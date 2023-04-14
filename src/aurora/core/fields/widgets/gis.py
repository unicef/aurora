from django import forms
from django.conf import settings
from .mixins import SmartWidgetMixin


class LocationWidget(SmartWidgetMixin, forms.HiddenInput):
    template_name = "django/forms/widgets/location.html"

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "gis%s.js" % extra,
            ],
        )
