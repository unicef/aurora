from django.forms import widgets
from django_regex.forms import RegexFormField
from typing import Dict, List, Any

from django import forms

from aurora.core.compat import StrategyFormField, JsRegexEditor
from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.fields.widgets.mixins import TailWindMixin
from aurora.core.models import Section
from aurora.core.registry import field_registry, form_registry


class CustomAttrsForm(forms.Form):
    pass
    # SECTIONS_MAP: Dict[Section, List] = dict(field=[], widget=[], smart=[], css=[], custom=[], data=[])


class AdvancendAttrsForm(forms.Form):
    title = None
    SECTIONS_MAP: Dict[Section, List] = dict(field=[], widget=[], smart=[], css=[], custom=[], data=[])

    def __init__(self, *args, **kwargs):
        self.field = kwargs.pop("field", None)
        self.prefix = kwargs.get("prefix")
        self.cleaned_data = {}
        self.title = self.title or self.__class__.__name__
        initial = self.extract_initials()
        # initial.update(**self.extract_custom())
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def get_section(self, section: Section):
        targets = self.SECTIONS_MAP.get(section, [])
        return {k: v for k, v in self.cleaned_data.items() if k in targets}

    def extract_initials(self):
        ret = {}
        for section, field_names in self.SECTIONS_MAP.items():
            if section == "field":
                for field_name in field_names:
                    ret[field_name] = getattr(self.field, field_name, "")
            else:
                for field_name in field_names:
                    ret[field_name] = self.field.advanced.get(section, {}).get(field_name, "")
        return ret


class AdvancedForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "widget": ["value", "placeholder"],
        "smart": ["description", "hint"],
    }
    value = forms.CharField(label="default", required=False, help_text="default value for the field")
    placeholder = forms.CharField(required=False, help_text="placeholder for the input")
    description = forms.CharField(required=False, widget=forms.Textarea, help_text="Text to display below the input")
    hint = forms.CharField(required=False, widget=forms.Textarea, help_text="Text to display above the input")

    class Meta:
        title = "Advanced"
        help = ""


class CustomForm(AdvancendAttrsForm):
    def __init__(self, *args, **kwargs):
        from aurora.core.editors.configs import fields_config

        super().__init__(*args, **kwargs)
        self.custom = None
        if extra := fields_config.get(self.field.field_type, None):
            self.custom = extra()
            for name, field in self.custom.fields.items():
                self.fields[name] = field
                self.SECTIONS_MAP["custom"].append(name)

    class Meta:
        title = "Custom"
        help = ""

    def get_section(self, section: Section):
        if section == "custom" and self.custom:
            # targets = self.custom.SECTIONS_MAP.get(section, [])
            return {k: v for k, v in self.cleaned_data.items()}
        return {}


class FlexFieldAttributesForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "field": ["field_type", "label", "required", "enabled"],
        "smart": ["visible"],
    }
    field_type = StrategyFormField(registry=field_registry)
    label = forms.CharField()
    required = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    visible = forms.BooleanField(required=False, help_text="Hide/Show field", initial=True)

    # choices = forms.JSONField(required=False, initial=[])
    # description = forms.CharField(required=False, help_text="Text to display below the input")
    # hint = forms.CharField(required=False, help_text="Text to display above the input")

    # def __init__(self, *args, **kwargs):
    # kwargs["instance"] = kwargs["field"]
    # super().__init__(*args, **kwargs)

    class Meta:
        # model = FlexFormField
        # fields = ("field_type", "label", "required", "enabled")
        title = "General"
        help = ""


class ValidationForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "widget": ["title", "pattern"],
    }
    title = forms.CharField(label="Tooltip", required=False, help_text="")
    pattern = RegexFormField(label="Regex", required=False, help_text="", widget=JsRegexEditor)

    # validation = RegexFormField(label="Regex", required=False, help_text="", widget=JsRegexEditor)
    #         if self.registration.unique_field_path and not kwargs.get("unique_field", None):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        # model = FlexFormField
        # fields = ("regex", "title", "validation")
        title = "Validation"
        help = ""


class CssForm(AdvancendAttrsForm):
    SECTIONS_MAP = {"css": ["input", "label", "fieldset", "description", "hint", "group", "group_title"]}
    input = forms.CharField(required=False, initial=TailWindMixin.default_class)
    label = forms.CharField(required=False, initial="block uppercase tracking-wide text-gray-700 font-bold mb-2")
    fieldset = forms.CharField(required=False, help_text="")
    description = forms.CharField(required=False, help_text="")
    hint = forms.CharField(required=False, help_text="")

    group = forms.CharField(required=False, help_text="", initial="default")
    group_title = forms.CharField(required=False, help_text="", initial="")

    class Meta:
        title = "Css"
        help = ""


class EventForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "field": [],
        "widget": ["onchange", "onblur", "onkeyup", "onfocus"],
        "data": ["onload", "validation"],
    }

    onchange = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onblur = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onkeyup = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onload = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onfocus = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    validation = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    # init = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    class Meta:
        title = "Events"
        help = ""


class AdvancedFlexFormAttrsForm(forms.Form):
    title = None
    SECTIONS_MAP: Dict[Section, List] = dict(form=[], smart=[], css=[], custom=[], data=[])

    def __init__(self, *args, **kwargs):
        self.form = kwargs.pop("form", None)
        self.prefix = kwargs.get("prefix")
        self.cleaned_data = {}
        self.title = self.title or self.__class__.__name__
        initial = self.extract_initials()
        # initial.update(**self.extract_custom())
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def get_section(self, section: Section):
        targets = self.SECTIONS_MAP.get(section, [])
        return {k: v for k, v in self.cleaned_data.items() if k in targets}

    def extract_initials(self):
        ret = {}
        for section, field_names in self.SECTIONS_MAP.items():
            if section == "form":
                for field_name in field_names:
                    ret[field_name] = getattr(self.form, field_name, "")
            else:
                for field_name in field_names:
                    ret[field_name] = self.form.advanced.get(section, {}).get(field_name, "")
        return ret


class FlexFormAttributesForm(AdvancedFlexFormAttrsForm):
    SECTIONS_MAP = {"form": ["name", "base_type"]}
    name = forms.CharField(label="name", required=False, help_text="default value for the field")
    base_type = StrategyFormField(registry=form_registry)

    class Meta:
        title = "Form"


class FlexFormEventForm(AdvancedFlexFormAttrsForm):
    onsubmit = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onload = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    validation = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    class Meta:
        title = "Events"


class FieldConfigWidget(widgets.MultiWidget):
    template_name = "django/forms/widgets/fieldconfigwidget.html"

    def __init__(self, attrs=None):
        _widgets = (
            widgets.TextInput(attrs={"required": "required"}),
            widgets.CheckboxInput(attrs={"class": "required", "title": "required"}),
            widgets.CheckboxInput(attrs={"class": "enabled", "title": "enabled"}),
            widgets.HiddenInput(attrs={"style": "width: 20px", "class": "ordering"}),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        return [None, None, None, None]

    def value_from_datadict(self, data, files, name):
        return [
            widget.value_from_datadict(data, files, name + widget_name)
            for widget_name, widget in zip(self.widgets_names, self.widgets)
        ]


class FieldConfigField(forms.Field):
    def clean(self, value: Any) -> Any:
        value[-1] = int(value[-1])
        return value


class FlexFormFieldsForm(AdvancedFlexFormAttrsForm):
    class Meta:
        title = "Fields"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.order_by("ordering"):
            self.fields[field.name] = FieldConfigField(widget=FieldConfigWidget, required=False)

    def extract_initials(self):
        ret = {}
        for field in self.form.fields.order_by("ordering"):
            ret[field.name] = [
                field.label,
                field.required,
                field.enabled,
                field.ordering,
            ]
        return ret
