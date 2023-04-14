from django import forms

from . import widgets


class DateField(forms.DateField):
    widget = widgets.SmartDateWidget

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        try:
            attrs["max"] = self.get_advanced("custom.max")
            attrs["min"] = self.get_advanced("custom.min", "") or ""
        except AttributeError:
            pass
        return attrs


class DateTimeField(forms.DateTimeField):
    widget = widgets.SmartDateTimeWidget


class TimeField(forms.TimeField):
    widget = widgets.SmarTimeWidget
