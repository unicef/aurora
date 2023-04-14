from django import forms

from aurora.core.fields.widgets.mixins import SmartWidgetMixin


class EmailInput(SmartWidgetMixin, forms.EmailInput):
    pass
