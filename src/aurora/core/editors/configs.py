from django import forms

from aurora.core import fields
from .forms import CustomAttrsForm
from ..models import OptionSet


def get_datasources():
    v = OptionSet.objects.order_by("name").values_list("name", flat=True)
    return [("", "")] + list(zip(v, v))


class BooleanFieldExtra(CustomAttrsForm):
    captions = forms.CharField(required=False)
    position = forms.ChoiceField(choices=(["l", "Left"], ["r", "right"]))


class CharFieldExtra(CustomAttrsForm):
    max_length = forms.IntegerField(required=True, initial=200)


class ChoiceFieldExtra(CustomAttrsForm):
    choices = forms.CharField(required=False)


class YesNoFieldExtra(CustomAttrsForm):
    choices = forms.CharField(required=False, initial='{"y": "Yes", "n": "No"}')


class AjaxSelectFieldExtra(CustomAttrsForm):
    datasource = forms.ChoiceField(choices=get_datasources, required=False)
    parent = forms.ChoiceField(choices=get_datasources, required=False)


class ImageFieldExtra(CustomAttrsForm):
    max_size = forms.CharField(required=False, initial="3M")
    accept = forms.CharField(label="File types", required=False, initial="*/*")


class CameraExtra(CustomAttrsForm):
    snap_label = forms.CharField(required=False, initial="Take photo")
    cancel_label = forms.CharField(required=False, initial="Clear photo")


class DateExtra(CustomAttrsForm):
    max = forms.CharField(required=False)
    min = forms.CharField(required=False)


fields_config = {
    fields.AjaxSelectField: AjaxSelectFieldExtra,
    fields.BooleanField: BooleanFieldExtra,
    fields.DateField: DateExtra,
    fields.IbanField: DateExtra,
    fields.MultiCheckboxField: ChoiceFieldExtra,
    fields.SmartFileField: ImageFieldExtra,
    fields.WebcamField: CameraExtra,
    fields.YesNoChoice: YesNoFieldExtra,
    fields.YesNoRadio: YesNoFieldExtra,
    fields.RadioField: ChoiceFieldExtra,
    forms.CharField: CharFieldExtra,
    forms.ChoiceField: ChoiceFieldExtra,
    forms.RadioSelect: ChoiceFieldExtra,
}
