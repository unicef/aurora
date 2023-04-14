import logging
from inspect import isclass

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from strategy_field.exceptions import StrategyAttributeError
from strategy_field.registry import Registry
from strategy_field.utils import fqn, import_by_name

from . import fields
from .forms import FlexFormBaseForm

logger = logging.getLogger(__name__)


def clean_classname(value):
    if value.startswith("smart_register."):
        value = value.replace("smart_register.", "aurora.")
    return value


def classloader(value):
    if not value:
        return value
    elif isinstance(value, str):
        value = clean_classname(value)
        return import_by_name(value)
    elif isclass(value):
        return value
    else:
        return type(value)


def get_custom_field(value):
    from .models import CustomFieldType

    *path, name = value.split(".")
    return CustomFieldType.objects.get(name=name)


def import_custom_field(value, exc):
    value = clean_classname(value)
    try:
        return import_by_name(value)
    except ModuleNotFoundError:
        return None
    except StrategyAttributeError:
        try:
            return get_custom_field(value).get_class()
        except ObjectDoesNotExist:
            return None


class FieldRegistry(Registry):
    def get_name(self, entry):
        return entry.__name__

    def as_choices(self):
        if not self._choices:
            self._choices = sorted([(fqn(klass), self.get_name(klass)) for klass in self], key=lambda e: e[1])
        return self._choices

    def __contains__(self, y):
        if isinstance(y, str):
            return y in [fqn(s) for s in self]
        try:
            return super().__contains__(y)
        except StrategyAttributeError:
            return get_custom_field(y)


field_registry = FieldRegistry(forms.Field)

# field_registry.register(forms.BooleanField)
field_registry.register(forms.CharField)
field_registry.register(forms.ChoiceField)
field_registry.register(forms.DurationField)
field_registry.register(forms.EmailField)
field_registry.register(forms.FileField)
# field_registry.register(forms.FloatField)
field_registry.register(forms.GenericIPAddressField)
# field_registry.register(forms.ImageField)
field_registry.register(forms.IntegerField)
field_registry.register(forms.MultipleChoiceField)
field_registry.register(forms.NullBooleanField)
field_registry.register(forms.TimeField)
field_registry.register(forms.URLField)


# field_registry.register(MathCaptchaField)
# field_registry.register(fields.DocumentField)
field_registry.register(fields.AjaxSelectField)
field_registry.register(fields.BooleanField)
field_registry.register(fields.CaptchaField)
field_registry.register(fields.CompilationTimeField)
field_registry.register(fields.DateField)
field_registry.register(fields.DateTimeField)
field_registry.register(fields.HiddenField)
field_registry.register(fields.IbanField)
field_registry.register(fields.LabelOnlyField)
field_registry.register(fields.LocationField)
field_registry.register(fields.MultiCheckboxField)
field_registry.register(fields.RadioField)
field_registry.register(fields.RemoteIpField)
field_registry.register(fields.SelectField)
field_registry.register(fields.SmartFileField)
field_registry.register(fields.SmartFileField)
field_registry.register(fields.WebcamField)
field_registry.register(fields.YesNoChoice)
field_registry.register(fields.YesNoRadio)

form_registry = Registry(forms.BaseForm)

form_registry.register(FlexFormBaseForm)
