from typing import Literal, Tuple

import copy

import json
import logging
import re
from datetime import date, datetime, time
from json import JSONDecodeError

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from pathlib import Path

import jsonpickle
from admin_ordering.models import OrderableModel
from concurrency.fields import AutoIncVersionField
from django import forms
from django.contrib.postgres.fields import CICharField
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.forms import formset_factory
from django.template.defaultfilters import pluralize, slugify
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from mptt.fields import TreeForeignKey
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from natural_keys import NaturalKeyModel, NaturalKeyModelManager
from py_mini_racer.py_mini_racer import MiniRacerBaseException
from sentry_sdk import set_tag
from strategy_field.utils import fqn

from ..i18n.gettext import gettext as _
from ..i18n.models import I18NModel
from ..state import state
from . import fields
from .compat import JavascriptRegexField, StrategyClassField
from .fields import WIDGET_FOR_FORMFIELD_DEFAULTS, SmartFieldMixin
from .forms import CustomFieldMixin, FlexFormBaseForm, SmartBaseFormSet
from .registry import field_registry, form_registry, import_custom_field
from .utils import JSONEncoder, dict_setdefault, jsonfy, namify, underscore_to_camelcase, oneline

logger = logging.getLogger(__name__)

cache = caches["default"]


class AdminReverseMixin:
    def get_admin_change_url(self):
        return reverse(admin_urlname(self._meta, "change"), args=[self.pk])

    def get_admin_changelist_url(self):
        return reverse(admin_urlname(self._meta, "changelist"))


class OrganizationManager(TreeManager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Organization(AdminReverseMixin, MPTTModel):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    name = CICharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    objects = OrganizationManager()

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProjectManager(TreeManager):
    def get_by_natural_key(self, slug, org_slug):
        return self.get(slug=slug, organization__slug=org_slug)


class Project(AdminReverseMixin, MPTTModel):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    name = CICharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    organization = models.ForeignKey(Organization, null=True, related_name="projects", on_delete=models.CASCADE)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    objects = ProjectManager()

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        unique_together = ("slug", "organization")

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.slug, self.organization.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Validator(AdminReverseMixin, NaturalKeyModel):
    STATUS_ERROR = "error"
    STATUS_EXCEPTION = "exc"
    STATUS_SUCCESS = "success"
    STATUS_SKIP = "skip"
    STATUS_UNKNOWN = "unknown"
    STATUS_INACTIVE = "inactive"

    FORM = "form"
    FIELD = "field"
    MODULE = "module"
    FORMSET = "formset"
    SCRIPT = "script"
    HANDLER = "handler"

    CONSOLE = mark_safe(
        """
    console = {log: function(d) {}};
    """
    )
    LIB = (Path(__file__).parent / "static" / "smart_validation.min.js").read_text()
    # LIB += (Path(__file__).parent / 'static' / 'validate_utils.min.js').read_text()
    LIB3 = mark_safe(
        """
TODAY = new Date();
dateutil = {today: TODAY};

function getAge(birthDate){
    return Math.floor((new Date() - new Date(birthDate).getTime()) / 3.15576e+10);
}


_ = {is_child: function(d) { return d && getAge(d) < 18 ? true: false},
     is_baby: function(d) { return d && getAge(d) <= 2 ? true: false},
     is_future: function(d) { return d  && Date.parse(d) > dateutil.today ? true: false},
};
_.is_adult = function(d) { return !_.is_child(d)};

"""
    )

    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    label = CICharField(max_length=255)
    name = CICharField(verbose_name=_("Function Name"), max_length=255, unique=True, blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    target = models.CharField(
        max_length=10,
        choices=(
            (FORM, "Form"),
            (FIELD, "Field"),
            (FORMSET, "Formset"),
            (MODULE, "Module"),
            (HANDLER, "Handler"),
            (SCRIPT, "Script"),
        ),
    )
    trace = models.BooleanField(
        default=False,
        help_text="Debug/Testing purposes: trace validator invocation on Sentry.",
    )
    count_errors = models.BooleanField(default=False, help_text="Count failures")
    active = models.BooleanField(default=False, blank=True, help_text="Enable/Disable validator.")
    draft = models.BooleanField(
        default=False, blank=True, help_text="Testing purposes: draft validator are enabled only for staff users."
    )
    _natural_key = ["name"]

    def __str__(self):
        return f"{self.label} ({self.target})"

    @staticmethod
    def js_type(value):
        if isinstance(value, (datetime, date, time)):
            return str(value)
        if isinstance(value, (dict,)):
            return jsonfy(value)
        return value

    def jspickle(self, value):
        return json.dumps(value, cls=JSONEncoder, skip_files=True)

    def monitor(self, status, value, exc: Exception = None):
        cache.set(f"validator-{state.request.user.pk}-{self.pk}-status", status)
        error = None
        if exc:
            if hasattr(exc, "error_dict"):
                error = self.jspickle(
                    exc.error_dict,
                )
            elif isinstance(exc, ValidationError):
                error = self.jspickle({"Error": exc.messages})
            else:
                error = self.jspickle({"Error": str(exc)})
        cache.set(f"validator-{state.request.user.pk}-{self.pk}-error", error)
        cache.set(f"validator-{state.request.user.pk}-{self.pk}-payload", self.jspickle(value))

    def validate(self, value, registration=None):
        from py_mini_racer import MiniRacer

        set_tag("validator", self.name)

        if self.active:
            self.monitor(self.STATUS_UNKNOWN, value)
        else:
            self.monitor(self.STATUS_INACTIVE, value)

        if self.active or (self.draft and state.request.user.is_staff):
            ctx = MiniRacer()
            try:
                pickled = self.jspickle(value or "")
                base = f"{self.CONSOLE};{self.LIB}; var value = {pickled};"

                ctx.eval(base)

                result = ctx.eval(self.code)

                if result is None:
                    ret = False
                else:
                    try:
                        ret = jsonpickle.decode(result)
                    except (JSONDecodeError, TypeError):
                        ret = result
                if isinstance(ret, str):
                    raise ValidationError(_(ret))
                elif isinstance(ret, (list, tuple)):
                    errors = [_(v) for v in ret]
                    raise ValidationError(errors)
                elif isinstance(ret, dict):
                    errors = {k: _(v) for (k, v) in ret.items()}
                    raise ValidationError(errors)
                elif isinstance(ret, bool) and not ret:
                    raise ValidationError(_("Please insert a valid value"))
            except ValidationError as e:
                import sentry_sdk

                if self.trace:
                    with sentry_sdk.push_scope() as scope:
                        scope.set_tag("validator", self.name)
                        scope.set_extra("registration", registration)
                        logger.exception(e)
                    self.monitor(self.STATUS_ERROR, value, e)
                elif self.count_errors:
                    with sentry_sdk.push_scope() as scope:
                        scope.set_tag("validator", self.name)
                        scope.set_extra("registration", registration)
                        sentry_sdk.capture_message(f"{self.name}", level="info")
                raise
            except MiniRacerBaseException as e:
                logger.exception(e)
                self.monitor(self.STATUS_EXCEPTION, value, e)
                return True
            except Exception as e:
                logger.exception(e)
                self.monitor(self.STATUS_EXCEPTION, value, e)
                raise
            self.monitor(self.STATUS_SUCCESS, value)

        elif self.trace:
            self.monitor(self.STATUS_SKIP, value)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name:
            self.name = namify(self.label)
        super().save(force_insert, force_update, using, update_fields)

    def get_script_url(self):
        return reverse("api:validator-script", args=[self.pk])


def get_validators(field):
    if field.validator:

        def inner(value):
            field.validator.validate(value)

        return [inner]
    return []


class FlexForm(AdminReverseMixin, I18NModel, NaturalKeyModel):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)
    name = CICharField(max_length=255, unique=True)
    base_type = StrategyClassField(registry=form_registry, default=FlexFormBaseForm)
    validator = models.ForeignKey(
        Validator, limit_choices_to={"target": Validator.FORM}, blank=True, null=True, on_delete=models.PROTECT
    )
    advanced = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Flex Form"
        verbose_name_plural = "Flex Forms"

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        self._initial = {}
        super().__init__(*args, **kwargs)

    # def add_field(
    #     self,
    #     label,
    #     field_type=forms.CharField,
    #     required=False,
    #     choices=None,
    #     regex=None,
    #     validator=None,
    #     name=None,
    #     **kwargs,
    # ):
    #     if isinstance(choices, (list, tuple)):
    #         kwargs["choices"] = choices
    #         choices = None
    #     return self.fields.update_or_create(
    #         label=label,
    #         defaults={
    #             "name": name,
    #             "field_type": field_type,
    #             "choices": choices,
    #             "regex": regex,
    #             "validator": validator,
    #             "advanced": kwargs,
    #             "required": required,
    #         },
    #     )[0]

    def get_initial(self):
        return self._initial

    def add_formset(self, form, **extra):
        defaults = {"extra": 0, "name": form.name.lower() + pluralize(0)}
        defaults.update(extra)
        return FormSet.objects.update_or_create(parent=self, flex_form=form, defaults=defaults)[0]

    # @cache_form
    def get_form_fields(self):
        fields = {}
        # base_order = self.advanced.get("field_order", [])

        for field in self.fields.filter(enabled=True).select_related("validator").order_by("ordering"):
            try:
                fld = field.get_instance()
                fields[field.name] = fld
                # if isinstance(fld, CompilationTimeField):
                #     fields["compilation_time_field_name"] = field.name
                self._initial[field.name] = field.get_default_value()
            except TypeError:
                pass
        return fields

    def get_indexed_fields(self, fields):
        indexes = FlexFormBaseForm.indexes.copy()
        for name, field in fields.items():
            if index := field.flex_field.advanced.get("smart", {}).get("index"):
                indexes[str(index)] = name
        return indexes

    def get_form_attrs(self):
        fields = self.get_form_fields()
        indexed = self.get_indexed_fields(fields)

        return {
            "flex_form": self,
            # "compilation_time_field": fields.pop("compilation_time_field_name", None),
            "indexes": indexed,
            "field_order": self.advanced.get("field_order"),
            **fields,
        }

    def get_form_class(self):
        flexForm = type(f"{self.name}FlexForm", (self.base_type,), self.get_form_attrs())
        return flexForm

    def get_formsets_classes(self):
        formsets = {}
        for fs in self.formsets.select_related("flex_form", "parent").filter(enabled=True):
            formsets[fs.name] = fs.get_formset()
        return formsets

    def get_formsets(self, attrs):
        formsets = {}
        for name, fs in self.get_formsets_classes().items():
            formsets[name] = fs(prefix=f"{name}", **attrs)
        return formsets

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

    def get_usage(self):
        ret = []

        for reg in self.registration_set.all():
            ret.append(
                {
                    "type": "Registration",
                    "obj": reg,
                    "editor_url": reverse("admin:registration_registration_change", args=[reg.pk]),
                    "change_url": reverse("admin:registration_registration_change", args=[reg.pk]),
                }
            )
        for fs in self.formsets.all():
            ret.append(
                {
                    "type": "Parend Of",
                    "obj": fs.flex_form,
                    "editor_url": reverse("admin:core_flexform_form_editor", args=[fs.flex_form.pk]),
                    "change_url": reverse("admin:core_flexform_change", args=[fs.flex_form.pk]),
                }
            )
        for fs in self.formset_set.all():
            ret.append(
                {
                    "type": "Child Of",
                    "obj": fs.parent,
                    "editor_url": reverse("admin:core_flexform_form_editor", args=[fs.parent.pk]),
                    "change_url": reverse("admin:core_flexform_change", args=[fs.parent.pk]),
                }
            )
        return ret


class FormSet(AdminReverseMixin, NaturalKeyModel, OrderableModel):
    FORMSET_DEFAULT_ATTRS = {
        "smart": {
            "title": {
                "class": "",
                "html_attrs": {},
            },
            "container": {
                "class": "",
                "html_attrs": {},
            },
            "widget": {
                "showCounter": False,
                "counterPrefix": "",
                "addText": "Add Another",
                "addCssClass": None,
                "deleteText": "Remove",
                "deleteCssClass": None,
                "keepFieldValues": False,
                "onAdd": None,
                "onRemove": None,
            },
        }
    }
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    name = CICharField(max_length=255)
    title = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(max_length=2000, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    parent = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name="formsets")
    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE)
    extra = models.IntegerField(default=0, blank=False, null=False)
    max_num = models.IntegerField(default=None, blank=True, null=True)
    min_num = models.IntegerField(default=0, blank=False, null=False)

    dynamic = models.BooleanField(default=True)
    validator = models.ForeignKey(
        Validator, blank=True, null=True, limit_choices_to={"target": Validator.FORMSET}, on_delete=models.SET_NULL
    )

    advanced = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "FormSet"
        verbose_name_plural = "FormSets"
        ordering = ["ordering"]
        unique_together = (("parent", "flex_form", "name"),)

    def __str__(self):
        return self.name

    def get_form(self):
        return self.flex_form.get_form_class()

    def save(self, *args, **kwargs):
        self.name = slugify(self.name)
        dict_setdefault(self.advanced, self.FORMSET_DEFAULT_ATTRS)
        super().save(*args, **kwargs)

    @cached_property
    def widget_attrs(self):
        dict_setdefault(self.advanced, self.FORMSET_DEFAULT_ATTRS)
        return self.advanced["smart"]["widget"]

    def get_formset(self) -> SmartBaseFormSet:
        formSet = formset_factory(
            self.get_form(),
            formset=SmartBaseFormSet,
            extra=self.extra,
            min_num=self.min_num,
            absolute_max=self.max_num,
            max_num=self.max_num,
        )
        formSet.fs = self
        formSet.required = self.min_num > 0
        return formSet


FIELD_KWARGS = {
    forms.CharField: {"min_length": None, "max_length": None, "empty_value": "", "initial": None},
    forms.IntegerField: {"min_value": None, "max_value": None, "initial": None},
    forms.DateField: {"initial": None},
    fields.LocationField: {},
    fields.RemoteIpField: {},
    fields.AjaxSelectField: {},
    fields.SmartFileField: {},
    fields.SelectField: {},
    fields.WebcamField: {},
}


@deconstructible
class RegexPatternValidator:
    def __call__(self, value):
        try:
            re.compile(value)
        except Exception as e:
            raise ValidationError(e)


@deconstructible
class ChoicesValidator:
    def __call__(self, value):
        try:
            list(dict(value).items())
        except ValueError:
            try:
                list(zip(map(str.lower, value), value))
            except Exception as e:
                raise ValidationError(e)


Section = Literal["field", "widget", "smart", "css", "custom", "data"]
Sections = Tuple[Section, ...]


class FlexFormField(AdminReverseMixin, NaturalKeyModel, I18NModel, OrderableModel):
    I18N_FIELDS = [
        "label",
    ]
    I18N_ADVANCED = ["smart.hint", "smart.question", "smart.description"]

    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=2000)
    name = CICharField(max_length=100, blank=True, validators=[RegexValidator("^[a-z_0-9]*$")])
    field_type = StrategyClassField(registry=field_registry, import_error=import_custom_field)
    choices = models.CharField(max_length=2000, blank=True, null=True, validators=[ChoicesValidator])
    required = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    validator = models.ForeignKey(
        Validator, blank=True, null=True, limit_choices_to={"target": Validator.FIELD}, on_delete=models.PROTECT
    )
    validation = models.TextField(blank=True, null=True)
    regex = JavascriptRegexField(blank=True, null=True, validators=[RegexPatternValidator()])
    advanced = models.JSONField(default=dict, blank=True, null=True)
    mapping = models.CharField(max_length=500, default="", blank=True, null=True)
    note = models.CharField(max_length=500, blank=True, null=True, help_text="Add here for the mapping")

    class Meta:
        unique_together = (("flex_form", "name"),)
        verbose_name = "Flex Field"
        verbose_name_plural = "Flex Fields"
        ordering = ["ordering"]

    def __str__(self):
        if self.field_type:
            return f"{self.name} {self.field_type.__name__}"
        return f"{self.name} <no type>"

    def type_name(self):
        return str(self.field_type.__name__)

    def fqn(self):
        return fqn(self.field_type)

    def get_default_value(self):
        return self.advanced.get("kwargs", {}).get("default_value", None)

    def get_choices(self):
        value = self.advanced.get("custom", {}).get("choices", "")
        try:
            choices = json.loads(value)
        except JSONDecodeError:
            try:
                choices = value.split(",")
            except (ValueError, KeyError):
                return []

        if isinstance(choices, (list, tuple)):
            return list(zip(choices, choices))
        elif isinstance(choices, dict):
            return list(dict(choices).items())
        return []

    def get_field_kwargs(self):
        field_kwargs = copy.deepcopy({**WIDGET_FOR_FORMFIELD_DEFAULTS.get(self.field_type, {})})
        field_kwargs.update(**self.advanced.get("field", {}))
        widget_kwargs = copy.deepcopy(self.advanced.get("widget", {}))
        custom_kwargs = copy.deepcopy(self.advanced.get("custom", {}))
        data = copy.deepcopy(self.advanced.get("data", {}))
        # smart_attrs = self.advanced.get("smart", {})
        # config = self.advanced.get("config", {})
        # events = self.advanced.get("events", {})
        # onload = events.pop("onload", "")
        data["flex-name"] = self.name

        if issubclass(self.field_type, CustomFieldMixin):
            raise NotImplementedError("")
        else:
            field_type = self.field_type
            field_kwargs.update(
                **{
                    "label": self.label,
                    "disabled": not self.enabled,
                    "required": self.required,
                }
            )
            if "choices" in custom_kwargs:
                field_kwargs["choices"] = self.get_choices()

            for k, v in data.items():
                if v:
                    widget_kwargs[f"data-{k}"] = oneline(v)

            if hasattr(field_type, "choices"):
                field_kwargs["choices"] = self.get_choices()
            #
            widget_kwargs["class"] = self.advanced.get("css", {}).get("input", "") or getattr(
                self.field_type.widget, "default_class", ""
            )
            # widget_kwargs["value"] = smart_attrs.get("default", "")
            # widget_kwargs["placeholder"] = smart_attrs.get("placeholder", "")
            # widget_kwargs.update(**config)
            #
            # widget_kwargs.update(**{k: oneline(v) for k, v in events.items()})
            #
            # widget_kwargs = {k: v for k, v in widget_kwargs.items() if v and str(v).strip()}
        field_kwargs.setdefault("validators", get_validators(self))
        widget_kwargs = {k: oneline(v) for k, v in widget_kwargs.items() if v and str(v).strip()}
        kwargs = {"field": field_kwargs, "widget": widget_kwargs}
        return kwargs

    def _get_field_kwargs(self):
        if issubclass(self.field_type, CustomFieldMixin):
            advanced = self.advanced.copy()
            smart_attrs = advanced.pop("smart", {}).copy()
            widget_kwargs = self.advanced.get("widget_kwargs", {}).copy()
            events = self.advanced.get("events", {}).copy()

            field_type = self.field_type.custom.base_type
            field_kwargs = self.field_type.custom.attrs.copy()
            if self.validator:
                field_kwargs.setdefault("validators", get_validators(self))
            elif self.field_type.custom.validator:
                field_kwargs["validators"] = get_validators(self.field_type.custom)
            else:
                field_kwargs["validators"] = []
            field_kwargs.setdefault("label", self.label)
            field_kwargs.setdefault("required", self.required)
            regex = self.regex or self.field_type.custom.regex
        else:
            # field_kwargs
            # widget_kwargs
            # widget_attrs
            # smart_attrs
            # data_attrs
            field_type = self.field_type
            advanced = self.advanced.copy()
            # backward compatibility code
            if "field" not in self.advanced:
                field_kwargs = self.advanced.get("field", {}).copy()
            else:
                field_kwargs = self.advanced.get("kwargs", {}).copy()
            if "widget" in self.advanced:
                widget_kwargs = self.advanced.get("widget", {}).copy()
            else:
                widget_kwargs = self.advanced.get("widget_kwargs", {}).copy()
            smart_attrs = advanced.pop("smart", {}).copy()
            events = self.advanced.get("events", {}).copy()

            field_kwargs["required"] = False
            regex = self.regex

            # data = kwargs.pop("data", {}).copy()
            smart_attrs["data-flex"] = self.name
            if self.required:
                smart_attrs["required_by_question"] = "required"
                if smart_attrs.get("question"):
                    field_kwargs["required"] = False
                else:
                    field_kwargs["required"] = True
            else:
                smart_attrs["required_by_question"] = ""
            # field_kwargs["required"] = False

            if not smart_attrs.get("visible", True):
                smart_attrs["data-visibility"] = "hidden"
            elif smart_attrs.get("question", ""):
                smart_attrs["data-visibility"] = "hidden"

            field_kwargs.setdefault("smart_attrs", smart_attrs.copy())
            field_kwargs.setdefault("label", self.label)
            #
            # if not smart_attrs.get("question"):
            #     kwargs.setdefault("required", self.required)

            field_kwargs.setdefault("validators", get_validators(self))

        if field_type in WIDGET_FOR_FORMFIELD_DEFAULTS:
            field_kwargs = {**WIDGET_FOR_FORMFIELD_DEFAULTS[field_type], **field_kwargs}
        if "datasource" in smart_attrs:
            field_kwargs["datasource"] = smart_attrs["datasource"]
        elif "datasource" in self.advanced:
            field_kwargs["datasource"] = self.advanced["datasource"]

        if hasattr(field_type, "choices"):
            if "choices" in smart_attrs:
                field_kwargs["choices"] = smart_attrs["choices"]
            elif "choices" in self.advanced:  # old deprecated
                field_kwargs["choices"] = self.advanced["choices"]
            elif self.choices:
                field_kwargs["choices"] = clean_choices(self.choices.split(","))
        if regex:
            field_kwargs["validators"].append(RegexValidator(regex))
        if css_class := widget_kwargs.pop("class", ""):
            widget_kwargs["class"] = css_class
        if smart_attrs.get("extra_classes"):
            widget_kwargs["extra_classes"] = smart_attrs.pop("extra_classes")

        field_kwargs["widget_kwargs"] = widget_kwargs
        field_kwargs["smart_attrs"] = smart_attrs
        field_kwargs.pop("default_value", "")
        field_kwargs["smart_events"] = events
        # these are for django FormField and handled by SmartFieldMixin
        return field_kwargs

    def get_instance(self):
        try:
            if issubclass(self.field_type, CustomFieldMixin):
                field_type = self.field_type.custom.base_type
            else:
                field_type = self.field_type
            kwargs = self.get_field_kwargs()
            kwargs.setdefault("flex_field", self)
            tt = type(field_type.__name__, (SmartFieldMixin, field_type), dict())
            fld = tt(
                **kwargs["field"],
                flex_field=self,
                # smart_attrs=kwargs["smart"],
                widget_kwargs=kwargs["widget"],
            )
        except Exception as e:
            logger.exception(e)
            raise
        return fld

    def clean(self):
        if self.field_type:
            try:
                self.get_instance()
            except Exception as e:
                logger.exception(e)
                raise ValidationError(e)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name.strip():
            self.name = namify(self.label)[:100]

        super().save(force_insert, force_update, using, update_fields)

    def get_usage(self):
        ret = []
        ret.append(
            {
                "type": "Form",
                "obj": self.flex_form,
                "editor_url": reverse("admin:core_flexform_change", args=[self.flex_form.pk]),
                "change_url": reverse("admin:core_flexform_change", args=[self.flex_form.pk]),
            }
        )
        return ret


class OptionSetManager(NaturalKeyModelManager):
    def get_from_cache(self, name):
        key = f"option-set-{name}"
        value = cache.get(key)
        if value is None:
            value = self.get(name=name)
            cache.set(key, value)
        return value


class OptionSet(AdminReverseMixin, NaturalKeyModel, models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    name = CICharField(max_length=100, unique=True, validators=[RegexValidator("[a-z0-9-_]")])
    description = models.CharField(max_length=1000, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    separator = models.CharField(max_length=1, default="", blank=True)
    comment = models.CharField(max_length=1, default="#", blank=True)
    columns = models.CharField(
        max_length=20, default="0,0,-1", blank=True, help_text="column order. Es: 'pk,parent,label' or 'pk,label'"
    )

    pk_col = models.IntegerField(default=0, help_text="ID column number")
    parent_col = models.IntegerField(default=-1, help_text="Column number of the indicating parent element")
    locale = models.CharField(max_length=5, default="en-us", help_text="default language code")
    languages = models.CharField(
        max_length=255, default="-;-;", blank=True, null=True, help_text="language code of each column."
    )
    _natural_key = ["name"]

    objects = OptionSetManager()

    def __str__(self):
        return self.name

    def clean(self):
        if self.locale not in self.languages:
            raise ValidationError("Default locale must be in the languages list")
        try:
            self.languages.split(",")
        except ValueError:
            raise ValidationError("Languages must be a comma separated list of locales")

    def get_cache_key(self, requested_language):
        return f"options-{self.pk}-{requested_language}-{self.version}"

    def get_api_url(self):
        return reverse("optionset", args=[self.name])

    def get_data(self, requested_language=None):
        if self.separator and requested_language:
            try:
                label_col = self.languages.split(",").index(requested_language)
            except ValueError:
                logger.error(f"Language {requested_language} not available for OptionSet {self.name}")
                label_col = self.languages.split(",").index(self.locale)
        else:
            label_col = 0

        key = self.get_cache_key(requested_language)
        value = cache.get(key, version=self.version)
        if not value:
            value = []
            for line in self.data.split("\r\n"):
                if not line.strip():
                    continue
                if line.startswith(self.comment):
                    continue
                parent = None
                if self.separator:
                    cols = line.split(self.separator)
                    pk = cols[self.pk_col]
                    label = cols[label_col]
                    if self.parent_col > 0:
                        parent = cols[self.parent_col]
                else:
                    label = line
                    pk = str(line).lower()

                values = {
                    "pk": pk,
                    "parent": parent,
                    "label": label,
                }
                value.append(values)
            cache.set(key, value)
        return value

    def as_choices(self, language=None):
        data = self.get_data(language or get_language())
        for entry in data:
            yield entry["pk"], entry["label"]

    def as_json(self, language=None):
        return self.get_data(language or get_language())


def clean_choices(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError("choices must be list or tuple")
    try:
        return list(dict(value).items())
    except ValueError:
        return list(zip(map(str.lower, value), value))


class CustomFieldType(AdminReverseMixin, NaturalKeyModel, models.Model):
    name = CICharField(max_length=100, unique=True, validators=[RegexValidator("[A-Z][a-zA-Z0-9_]*")])
    base_type = StrategyClassField(registry=field_registry, default=forms.CharField)
    attrs = models.JSONField(default=dict)
    regex = JavascriptRegexField(blank=True, null=True)
    # choices = models.CharField(max_length=2000, blank=True, null=True)
    # required = models.BooleanField(default=False)
    validator = models.ForeignKey(
        Validator, blank=True, null=True, limit_choices_to={"target": Validator.FIELD}, on_delete=models.PROTECT
    )

    @staticmethod
    def build(name, defaults):
        choices = defaults.get("attrs", {}).get("choices", {})
        if choices:
            defaults["attrs"]["choices"] = clean_choices(choices)
        return CustomFieldType.objects.update_or_create(name=name, defaults=defaults)[0]

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        cls = self.get_class()
        if fqn(cls) not in field_registry:
            field_registry.register(cls)

    def clean(self):
        if not self.base_type:
            raise ValidationError("base_type is mandatory")
        try:
            class_ = self.get_class()
        except Exception as e:
            raise ValidationError(f"Error instantiating class: {e}")

        try:
            kwargs = self.attrs.copy()
            class_(**kwargs)
        except Exception as e:
            raise ValidationError(f"Error instantiating {fqn(class_)}: {e}")

    def get_class(self):
        attrs = self.attrs.copy()
        attrs["custom"] = self
        return type(self.base_type)(underscore_to_camelcase(self.name), (CustomFieldMixin, self.base_type), attrs)
