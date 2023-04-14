from django import forms
from django.conf import settings

from aurora.core.fields.widgets.mixins import SmartWidgetMixin


class WebcamWidget(SmartWidgetMixin, forms.Textarea):
    template_name = "django/forms/widgets/webcam.html"

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "webcam/webcam%s.js" % extra,
            ],
            css={
                "all": [
                    "webcam/webcam.css",
                ]
            },
        )
