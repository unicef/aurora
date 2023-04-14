from django import forms

from aurora.core.fields.widgets.mixins import SmartWidgetMixin


class MultiCheckboxWidget(SmartWidgetMixin, forms.CheckboxSelectMultiple):
    template_name = "django/forms/widgets/multi_checkbox.html"
    option_template_name = "django/forms/widgets/multi_checkbox_option.html"
    default_class = ""


class MultiCheckboxField(forms.MultipleChoiceField):
    widget = MultiCheckboxWidget
