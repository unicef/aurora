import base64
import json

from django import forms
from .widgets import LocationWidget


class LocationField(forms.CharField):
    widget = LocationWidget

    def __init__(self, *, max_length=None, min_length=None, strip=True, empty_value="", **kwargs):
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(max_length=None, min_length=None, strip=strip, empty_value=empty_value, **kwargs)

    def to_python(self, value):
        decoded = base64.decodebytes(value.encode())
        # as_json = json.loads(decoded)
        return json.loads(decoded)
