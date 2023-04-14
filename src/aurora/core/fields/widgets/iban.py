from django import forms
from django.conf import settings
from .mixins import SmartWidgetMixin


class IbanWidget(SmartWidgetMixin, forms.TextInput):
    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "iban/lib%s.js" % extra,
                "iban/handler%s.js" % extra,
            ],
        )
