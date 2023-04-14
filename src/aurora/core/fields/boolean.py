from django import forms

from aurora.core.fields.widgets.mixins import SmartWidgetMixin


class CheckboxInput(SmartWidgetMixin, forms.CheckboxInput):
    input_type = "checkbox"
    template_name = "django/forms/widgets/boolean.html"
    default_class = ""


class BooleanField(forms.BooleanField):
    widget = CheckboxInput
