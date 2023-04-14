import logging
from typing import Dict

from django.template import Library
from django.utils.safestring import mark_safe
from pygments import highlight, lexers
from pygments.formatters import HtmlFormatter

from aurora.core.utils import safe_json

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def pretty_json(json_object: Dict) -> str:
    json_str = safe_json(json_object)
    lex = lexers.get_lexer_by_name("json")
    return mark_safe(highlight(json_str, lex, HtmlFormatter()))
