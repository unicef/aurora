from django.forms import widgets

from .mixins import SmartWidgetMixin


class RadioWidget(SmartWidgetMixin, widgets.RadioSelect):
    template_name = "django/forms/widgets/radio.html"
    option_template_name = "django/forms/widgets/radio_option.html"
    default_class = ""


class YesNoRadioWidget(SmartWidgetMixin, widgets.RadioSelect):
    template_name = "django/forms/widgets/yesnoradio.html"
    option_template_name = "django/forms/widgets/radio_option.html"
    default_class = ""
