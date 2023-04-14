from django import forms

from .widgets import IbanWidget


class IbanField(forms.CharField):
    widget = IbanWidget
