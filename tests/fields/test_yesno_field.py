import pytest
from django import forms

from aurora.core import fields
from aurora.core.fields import YesNoRadio
from aurora.core.models import FlexFormField
from testutils.factories import FlexFormFieldFactory


def test_yesno():
    fld = YesNoRadio()
    assert fld.choices == [("y", "Yes"), ("n", "No")]


def test_custom():
    fld = YesNoRadio(choices=[("y", "Si"), ("n", "No")])
    assert fld.choices == [("y", "Si"), ("n", "No")]


def test_error1():
    with pytest.raises(ValueError):
        YesNoRadio(choices=["Si", "No"])


def test_error2():
    with pytest.raises(ValueError):
        YesNoRadio(choices=["Yes", "No", "Maybe"])


@pytest.mark.parametrize(
    "value,expected",
    [
        ("y,n", [("y", "y"), ("n", "n")]),
        ('{"y":"Yes", "n":"No"}', [("y", "Yes"), ("n", "No")]),
    ],
)
def test_build(db, value, expected):
    f: FlexFormField = FlexFormFieldFactory(field_type=fields.YesNoRadio, advanced={"custom": {"choices": value}})
    i: forms.Field = f.get_instance()
    assert isinstance(i, fields.YesNoRadio)
    assert i.choices == expected
