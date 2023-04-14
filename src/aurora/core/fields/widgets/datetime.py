from django import forms

from .mixins import TailWindMixin


class SmartDateWidget(TailWindMixin, forms.DateInput):
    input_type = "date"


class SmartDateTimeWidget(TailWindMixin, forms.DateTimeInput):
    input_type = "datetime"


class SmarTimeWidget(TailWindMixin, forms.TimeInput):
    input_type = "time"

    #
    # def __init__(self, attrs=None, format=None):
    #     super().__init__(attrs=attrs, format=format)
    #     self.attrs["size"] = 10
    #
    # def build_attrs(self, base_attrs, extra_attrs=None):
    #     # base_attrs["class"] += " vDateField"
    #     return super().build_attrs(base_attrs, extra_attrs)

    # @property
    # def media(self):
    #     extra = "" if settings.DEBUG else ".min"
    #     base = super().media
    #     return base + VersionMedia(
    #         js=[
    #             "admin/js/vendor/jquery/jquery%s.js" % extra,
    #             "admin/js/jquery.init.js",
    #             "jquery.compat%s.js" % extra,
    #             "datetimepicker/datepicker%s.js" % extra,
    #             "datetimepicker/dt%s.js" % extra,
    #         ],
    #         css={"all": ["datetimepicker/datepicker.css"]},
    #     )
