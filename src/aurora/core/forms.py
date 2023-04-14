import csv

from adminactions.api import delimiters, quotes
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet
from django.utils import formats
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from .fields.widgets import JavascriptEditor
from .version_media import VersionMedia


class ValidatorForm(forms.ModelForm):
    code = forms.CharField(widget=JavascriptEditor)


class Select2Widget(forms.Select):
    template_name = "django/forms/widgets/select2.html"


class CustomFieldMixin:
    custom = None


class FlexFormBaseForm(forms.Form):
    flex_form = None
    # compilation_time_field = None
    indexes = {"1": None, "2": None, "3": None}
    field_order = None

    @cached_property
    def compilation_time_field(self) -> str:
        from aurora.core.fields import CompilationTimeField

        for name, fld in self.fields.items():
            if isinstance(fld, CompilationTimeField):
                return name

    def get_counters(self, data):
        if self.compilation_time_field:
            return data.pop(self.compilation_time_field, {})
        return {}

    def is_valid(self):
        return super().is_valid()

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return (
            VersionMedia(
                js=[
                    "admin/js/vendor/jquery/jquery%s.js" % extra,
                    "admin/js/jquery.init.js",
                    "jquery.compat%s.js" % extra,
                    "smart_validation%s.js" % extra,
                    "smart%s.js" % extra,
                    "smart_field%s.js" % extra,
                ]
            )
            + base
        )

    def get_storage_mapping(self):
        return {name: field.storage for name, field in self.fields.items()}

    def _clean_fields(self):
        super()._clean_fields()
        for name, field in self.fields.items():
            if not field.is_stored():
                del self.cleaned_data[name]

    def full_clean(self):
        return super().full_clean()

    def clean(self):
        cleaned_data = self.cleaned_data
        # if self.is_valid() and self.flex_form and self.flex_form.validator:
        if self.flex_form.validator:
            try:
                self.flex_form.validator.validate(cleaned_data)
            except ValidationError as e:
                raise ValidationError(e)
        return cleaned_data


class SmartBaseFormSet(BaseFormSet):
    def non_form_errors(self):
        return super().non_form_errors()

    def clean(self):
        if self.fs.validator:
            data = {
                "total_form_count": self.total_form_count(),
                "errors": self._errors,
                "non_form_errors": self._non_form_errors,
                "cleaned_data": getattr(self, "cleaned_data", []),
            }
            try:
                self.fs.validator.validate(data)
            except ValidationError as e:
                raise ValidationError([e])

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return (
            VersionMedia(
                js=[
                    "admin/js/vendor/jquery/jquery%s.js" % extra,
                    "admin/js/jquery.init.js",
                    "jquery.compat%s.js" % extra,
                    "jquery.formset%s.js" % extra,
                    "smart.formset%s.js" % extra,
                ]
            )
            + base
        )


class DateFormatsForm(forms.Form):
    defaults = {
        "date_format": formats.get_format("DATE_FORMAT"),
        "datetime_format": formats.get_format("DATETIME_FORMAT"),
        "time_format": formats.get_format("TIME_FORMAT"),
    }
    datetime_format = forms.CharField(label=_("Datetime format"))
    date_format = forms.CharField(label=_("Date format"))
    time_format = forms.CharField(label=_("Time format"))


class CSVOptionsForm(forms.Form):
    defaults = {
        "date_format": "d/m/Y",
        "datetime_format": "N j, Y, P",
        "time_format": "P",
        "doublequote": True,
        "header": False,
        "skipinitialspace": True,
        "quotechar": '"',
        "quoting": csv.QUOTE_MINIMAL,
        "delimiter": ";",
        "escapechar": "\\",
    }

    header = forms.BooleanField(label=_("Header"), required=False)
    doublequote = forms.BooleanField(
        label=_("Doublequote"),
        required=False,
        help_text=_(
            "Controls how instances of quotechar appearing inside a field should "
            "themselves be quoted. When True, the character is doubled. "
            "When False, the escapechar is used as a prefix to the quotechar"
        ),
    )
    skipinitialspace = forms.BooleanField(
        label=_("Skip Initial Space"),
        required=False,
        help_text=_("When True, whitespace immediately following the delimiter is ignored"),
    )
    delimiter = forms.ChoiceField(
        label=_("Delimiter"),
        choices=list(zip(delimiters, delimiters)),
        help_text=_("A one-character string used to separate fields"),
    )
    quotechar = forms.ChoiceField(
        label=_("Quotechar"),
        choices=list(zip(quotes, quotes)),
        help_text=_(
            "A one-character string used to quote fields containing special characters, "
            "such as the delimiter or quotechar, or which contain new-line characters"
        ),
    )
    quoting = forms.TypedChoiceField(
        coerce=int,
        label=_("Quoting"),
        choices=(
            (csv.QUOTE_ALL, _("All")),
            (csv.QUOTE_MINIMAL, _("Minimal")),
            (csv.QUOTE_NONE, _("None")),
            (csv.QUOTE_NONNUMERIC, _("Non Numeric")),
        ),
        help_text=_("Controls when quotes should be generated by the writer and recognised by the reader"),
    )

    escapechar = forms.ChoiceField(
        label=_("Escapechar"),
        choices=(("", ""), ("\\", "\\")),
        required=False,
        help_text=_(
            "A one-character string used by the writer to escape the delimiter "
            "if quoting is set to QUOTE_NONE and the quotechar if doublequote is False. "
            "On reading, the escapechar removes any special meaning from the following character"
        ),
    )
