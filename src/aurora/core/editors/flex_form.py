from typing import Dict

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.functional import cached_property

from aurora.core.editors.forms import (
    FlexFormAttributesForm,
    FlexFormEventForm,
    AdvancedFlexFormAttrsForm,
    FlexFormFieldsForm,
)
from aurora.core.editors.utils import attr_dumps
from aurora.core.models import FlexForm
from aurora.core.utils import merge_data
from aurora.core.version_media import VersionMedia

cache = caches["default"]


class FlexFormWrapper:
    def __init__(self, form: FlexForm, *args, **kwargs):
        self.form = form
        self.overrides = {}
        self._get_form_fields = self.form.get_form_fields
        self.form.get_form_fields = self.get_form_fields
        self.override = {}

    @property
    def advanced(self):
        return self.form.advanced

    @advanced.setter
    def advanced(self, value):
        self.form.advanced = value

    def get_form_class(self):
        return self.form.get_form_class()

    def get_form_attrs(self):
        return self.form.get_form_attrs()

    def get_form_fields(self):
        fields = {}
        for field in self.form.fields.order_by("ordering"):
            try:
                field.required = self.overrides[field.name]["required"]
                field.label = self.overrides[field.name]["label"]
                field.enabled = self.overrides[field.name]["enabled"]
                fld = field.get_instance()
                if field.enabled:
                    fields[field.name] = fld
                    # if isinstance(fld, CompilationTimeField):
                    #     fields["compilation_time_field_name"] = field.name
                    self.form._initial[field.name] = field.get_default_value()
            except TypeError:
                pass
        return fields
        #
        # original = self._get_form_fields()
        # fields = {}
        # for field_name, field in original.items():
        #     if self.overrides[field_name]["enabled"]:
        #         fields[field_name] = field
        #         fields[field_name].required = self.overrides[field_name]["required"]
        #         fields[field_name].label = self.overrides[field_name]["label"]
        # return fields

    @atomic()
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        for field in self.form.fields.order_by("ordering"):
            field.required = self.overrides[field.name]["required"]
            field.label = self.overrides[field.name]["label"]
            field.enabled = self.overrides[field.name]["enabled"]
            field.save()
        return self.form.save()


class FormEditor:
    FORMS = {
        "form": FlexFormAttributesForm,
        "fields": FlexFormFieldsForm,
        # "widget": WidgetAttributesForm,
        # "smart": SmartAttributesForm,
        # "css": CssForm,
        "events": FlexFormEventForm,
    }

    def __init__(self, modeladmin, request, pk):
        self.modeladmin = modeladmin
        self.request = request
        self.pk = pk
        self.cache_key = f"/editor/form/{self.request.user.pk}/{self.pk}/"

    @cached_property
    def flex_form(self):
        return FlexForm.objects.get(pk=self.pk)

    @cached_property
    def patched_form(self) -> FlexForm:
        form: FlexForm = FlexFormWrapper(self.flex_form)
        form.advanced = {}

        if config := cache.get(self.cache_key, None):
            merged = {}
            _forms: Dict[str, AdvancedFlexFormAttrsForm] = self.get_forms(config)
            for prefix, frm in _forms.items():
                if frm.is_valid():
                    if prefix == "fields":
                        ordered = [x[0] for x in sorted(frm.cleaned_data.items(), key=lambda x: x[1][-1])]
                        merged["field_order"] = ordered
                        for fname in ordered:
                            form.overrides[fname] = {
                                "label": frm.cleaned_data[fname][0],
                                "required": frm.cleaned_data[fname][1],
                                "enabled": frm.cleaned_data[fname][2],
                            }
                    else:
                        processed = []
                        for sect in AdvancedFlexFormAttrsForm.SECTIONS_MAP.keys():
                            values = {k: v for k, v in frm.get_section(sect).items() if v and str(v).strip()}
                            processed.extend(values.keys())
                            if sect == "field":
                                for k, v in values.items():
                                    setattr(frm, k, v)
                            else:
                                merged = merge_data(merged, {**{sect: values}})
                else:
                    raise ValidationError(frm.errors)
            form.advanced = merged
        return form

    def get_advanced(self):
        frm: FlexForm = self.patched_form
        rendered = attr_dumps(frm.advanced, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_configuration(self):
        frm: FlexForm = self.patched_form
        attrs = frm.get_form_attrs()
        rendered = attr_dumps(attrs, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_code(self):
        from bs4 import BeautifulSoup as bs
        from bs4 import formatter
        from pygments import highlight
        from pygments.formatters.html import HtmlFormatter
        from pygments.lexers import HtmlLexer

        ctx = self.get_context(self.request)
        ctx["form"] = self.patched_form.get_form_class()
        code = get_template("smart/_form.html").render(ctx)
        formatter = formatter.HTMLFormatter(indent=2)
        soup = bs(code)
        prettyHTML = soup.prettify(formatter=formatter)

        formatter = HtmlFormatter(style="default", full=True)
        ctx["code"] = highlight(prettyHTML, HtmlLexer(), formatter)
        return render(self.request, "admin/core/flexformfield/field_editor/code.html", ctx, content_type="text/html")

    def render(self):
        instance = self.patched_form
        form_class = self.flex_form.get_form_class()
        ctx = self.get_context(self.request)
        if self.request.method == "POST":
            form = form_class(self.request.POST)
            ctx["valid"] = form.is_valid()
        else:
            form = form_class()
            ctx["valid"] = None

        ctx["form"] = form
        ctx["instance"] = instance

        return render(self.request, "admin/core/flexform/form_editor/preview.html", ctx)

    def get_forms(self, data=None) -> Dict:
        if data:
            return {prefix: Form(data, prefix=prefix, form=self.flex_form) for prefix, Form in self.FORMS.items()}
        if self.request.method == "POST":
            return {
                prefix: Form(self.request.POST, prefix=prefix, form=self.flex_form)
                for prefix, Form in self.FORMS.items()
            }
        return {prefix: Form(prefix=prefix, form=self.flex_form) for prefix, Form in self.FORMS.items()}

    def refresh(self):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            data = self.request.POST.dict()
            data.pop("csrfmiddlewaretoken")
            cache.set(self.cache_key, data)
        else:
            return JsonResponse({prefix: frm.errors for prefix, frm in forms.items()}, status=400)
        return JsonResponse(data)

    def get_context(self, request, pk=None, **kwargs):
        return {
            **self.modeladmin.get_common_context(request, pk),
            **kwargs,
        }

    def sort(self):
        print("aurora/core/editors/flex_form.py: 136", self.request.body)

    def get(self, request, pk):
        ctx = self.get_context(request, pk)
        ctx["forms"] = {}
        extra = "" if settings.DEBUG else ".min"
        media = VersionMedia()
        for prefix, frm in self.get_forms().items():
            # ctx[f"form_{prefix}"] = frm
            ctx["forms"][prefix] = frm
            media += frm.media

        media += VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                # "admin/resizer%s.js" % extra,
                "smart_validation%s.js" % extra,
                "smart%s.js" % extra,
                "smart_field%s.js" % extra,
                "https://cdn.jsdelivr.net/npm/dragsort@1.0.6/dist/js/jquery.dragsort.min.js",
            ],
            css={"all": ["admin/form_editor/form_editor.css"]},
        )
        ctx["media"] = media
        # + VersionMedia(js=["admin/field_editor/field_editor%s.js" % extra])
        return render(request, "admin/core/flexform/form_editor/main.html", ctx)

    def post(self, request, pk):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            self.patched_form.save()
            return HttpResponseRedirect(".")
