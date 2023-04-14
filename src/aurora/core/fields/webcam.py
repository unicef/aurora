from django import forms

from .widgets import WebcamWidget


class WebcamField(forms.CharField):
    widget = WebcamWidget
