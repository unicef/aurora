from django import forms

from . import widgets
from .boolean import BooleanField
from .captcha import CaptchaField
from .compilation_time import CompilationTimeField
from .date import DateField, DateTimeField, TimeField
from .document import DocumentField
from .file import SmartFileField
from .gis import LocationField
from .hidden import HiddenField
from .iban import IbanField
from .label import LabelOnlyField
from .mixins import SmartFieldMixin
from .multi_checkbox import MultiCheckboxField
from .radio import RadioField, YesNoChoice, YesNoRadio
from .remote_ip import RemoteIpField
from .select import AjaxSelectField, SelectField, SmartSelectWidget
from .webcam import WebcamField

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    forms.EmailField: {"widget": widgets.EmailInput},
    forms.CharField: {"widget": widgets.SmartTextWidget, "max_length": 200, "strip": True},
    forms.IntegerField: {"widget": widgets.NumberWidget},
    forms.FloatField: {"widget": widgets.NumberWidget},
    forms.ChoiceField: {"widget": SmartSelectWidget},
    forms.ImageField: {"widget": widgets.ImageWidget},
    SmartFileField: {"widget": widgets.UploadFileWidget},
    # SelectField: {"widget": SmartSelectWidget},
    # RadioField: {"widget": widgets.RadioWidget},
    # YesNoRadio: {"widget": widgets.YesNoRadioWidget},
    # YesNoChoice: {"widget": SmartSelectWidget},
    # MultiCheckboxField: {"widget": widgets.MultiCheckboxWidget},
}
