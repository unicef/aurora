from django import forms

from .mixins import SmartWidgetMixin


class SmartTextWidget(SmartWidgetMixin, forms.TextInput):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
