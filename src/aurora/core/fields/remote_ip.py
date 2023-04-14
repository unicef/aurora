from django import forms
from django.forms import HiddenInput

from aurora.state import state

from ..utils import get_client_ip


class RemoteIpField(forms.CharField):
    widget = HiddenInput

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(**kwargs)

    def to_python(self, value):
        return get_client_ip(state.request)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        try:
            attrs["value"] = get_client_ip(state.request)
        except AttributeError:
            pass
        return attrs
