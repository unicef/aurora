import pytest

from aurora.core.registry import forms
from aurora.core.models import FlexFormField
from testutils.factories import FlexFormFieldFactory

pytestmark = pytest.mark.django_db

ATTRS = {
    "smart": {
        "hint": "",
        "index": None,
        "choices": [],
        "visible": True,
        "fieldset": "",
        "onchange": "",
        "question": "",
        "description": "",
        "question_onchange": "",
        "datasource": "",
        "parent_datasource": "",
    },
    "kwargs": {"default_value": None},
    "widget": {
        "title": None,
        "pattern": None,
        "fieldset": "",
        "onchange": "",
        "css_class": "",
        "placeholder": None,
        "extra_classes": "",
    },
    "choices": [["female", "Female"], ["male", "Male"]],
    "css": {
        "input": "",
        "label": "block uppercase tracking-wide text-gray-700 font-bold mb-2",
        "fieldset": "",
        "question": "",
    },
    "events": {"onchange": "", "onblur": "", "onkeyup": "", "onload": "", "onfocus": "", "validation": "", "init": ""},
}


@pytest.mark.parametrize("attrs", [{"label": "Label", "required": True}])
def test_plain(attrs):
    f: FlexFormField = FlexFormFieldFactory(field_type=forms.CharField, **attrs)
    i: forms.Field = f.get_instance()
    assert isinstance(i, forms.CharField)
    for k, v in attrs.items():
        assert getattr(i, k) == v


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1,2", [("1", "1"), ("2", "2")]),
        ("[1,2]", [(1, 1), (2, 2)]),
        ('{"a":10,"b":20}', [("a", 10), ("b", 20)]),
        ('{"1":"a", "2":"b"}', [("1", "a"), ("2", "b")]),
    ],
)
def test_choices(value, expected):
    f: FlexFormField = FlexFormFieldFactory(field_type=forms.ChoiceField, advanced={"custom": {"choices": value}})
    i: forms.Field = f.get_instance()
    assert isinstance(i, forms.ChoiceField)
    assert i.choices == expected


@pytest.mark.parametrize("value", [True, False])
def test_enabled(value):
    f: FlexFormField = FlexFormFieldFactory(field_type=forms.CharField, enabled=value)
    i: forms.Field = f.get_instance()
    assert isinstance(i, forms.CharField)
    assert i.disabled is not value
