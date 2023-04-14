import json

from django import forms
from strategy_field.utils import fqn

from aurora.core.models import FlexForm
from aurora.core.utils import JSONEncoder


class AttrEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, FlexForm):
            return fqn(o)
        elif isinstance(o, forms.Field):
            return fqn(o)
        elif isinstance(o, forms.Form):
            return fqn(o)

        return super().default(o)


def attr_dumps(data, **kwargs):
    kwargs.setdefault("indent", 4)
    kwargs.setdefault("sort_keys", True)
    return json.dumps(data, cls=AttrEncoder, **kwargs)
