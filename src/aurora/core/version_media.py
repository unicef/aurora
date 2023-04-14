import os

from itertools import chain

from django import forms
from django.utils.html import html_safe, format_html


@html_safe
class VersionMedia(forms.Media):
    def __str__(self):
        return self.render()

    def render_js(self):
        version = os.environ.get("VERSION", "<dev>")
        return [format_html('<script src="{}?{}"></script>', self.absolute_path(path), version) for path in self._js]

    def render_css(self):
        # To keep rendering order consistent, we can't just iterate over items().
        # We need to sort the keys, and iterate over the sorted list.
        media = sorted(self._css)
        version = os.environ.get("VERSION", "dev")
        return chain.from_iterable(
            [
                format_html(
                    '<link href="{}?{}" type="text/css" media="{}" rel="stylesheet">',
                    self.absolute_path(path),
                    version,
                    medium,
                )
                for path in self._css[medium]
            ]
            for medium in media
        )

    def __add__(self, other):
        combined = VersionMedia()
        combined._css_lists = self._css_lists[:]
        combined._js_lists = self._js_lists[:]
        for item in other._css_lists:
            if item and item not in self._css_lists:
                combined._css_lists.append(item)
        for item in other._js_lists:
            if item and item not in self._js_lists:
                combined._js_lists.append(item)
        return combined
