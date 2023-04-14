from django import forms
from django_regex.fields import RegexField as RegexField_
from django_regex.utils import Regex
from strategy_field.fields import StrategyClassField as StrategyClassField_
from strategy_field.fields import StrategyFormField as StrategyFormField_
from strategy_field.utils import fqn


class JsRegexEditor(forms.Textarea):
    template_name = "django/forms/widgets/jsregex.html"


class RegexField(RegexField_):
    pass


class JavascriptRegexField(RegexField_):
    widget = JsRegexEditor

    def value_from_object(self, obj):
        """Return the value of this field in the given model instance."""
        return getattr(obj, self.attname)

    def get_prep_value(self, value):
        if isinstance(value, Regex):
            return value.pattern
        return value


class StrategyFormField(StrategyFormField_):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = self.registry.as_choices()


class StrategyClassField(StrategyClassField_):
    form_class = StrategyFormField

    def value_to_string(self, obj):
        return fqn(self.value_from_object(obj))

    def _get_choices(self):
        if self.registry:
            return self.registry.as_choices()
        return []

    def _set_choices(self, value):
        pass

    choices = property(_get_choices, _set_choices)
