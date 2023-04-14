import logging

from django import forms
from django.conf import settings
from django.forms import BoundField
from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language

from .widgets.mixins import TailWindMixin
from ..version_media import VersionMedia

logger = logging.getLogger(__name__)


class SmartChoiceWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/smart_select.html"


class SmartSelectWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/smart_select.html"


class AjaxSelectWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/ajax_select.html"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
        self.attrs.setdefault("class", {})
        # self.attrs["class"] += " ajaxSelect"

    def build_attrs(self, base_attrs, extra_attrs=None):
        base_attrs["class"] += " ajaxSelect"
        return super().build_attrs(base_attrs, extra_attrs)

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js",
                "select2/ajax_select%s.js" % extra,
                "jquery.formset%s.js" % extra,
                "smart.formset%s.js" % extra,
            ],
            css={
                "all": [
                    "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css",
                ]
            },
        )


class SelectField(forms.ChoiceField):
    widget = SmartSelectWidget

    def __init__(self, **kwargs):
        self._choices = ()
        self.language = kwargs.pop("language", get_language())
        self.parent = kwargs.pop("parent_datasource", None)
        options = kwargs.pop("datasource", "")
        super().__init__(**kwargs)
        self.choices = options

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.parent:
            attrs["data-parent"] = self.parent
        return attrs

    def _get_options(self):
        return self._options

    def _set_options(self, value):
        if value:  # pragma: no branch
            try:
                from aurora.core.models import OptionSet

                optset = OptionSet.objects.get_from_cache(value)
                value = list(optset.as_choices(self.language))
            except OptionSet.DoesNotExist as e:
                logger.exception(e)
                value = []
        self._options = self.widget.choices = value

    choices = property(_get_options, _set_options)


class AjaxSelectField(forms.Field):
    widget = AjaxSelectWidget

    def widget_attrs(self, widget):
        from aurora.core.models import OptionSet

        attrs = super().widget_attrs(widget)
        try:
            if self.flex_field:
                self.datasource = self.flex_field.advanced.get("custom", {}).get("datasource", None)
                self.parent = self.flex_field.advanced.get("custom", {}).get("parent", None)
                attrs["data-source"] = self.datasource
                attrs["data-ajax--url"] = reverse("optionset", args=[self.datasource])
                if self.parent:
                    attrs["data-parent"] = self.parent
        except (OptionSet.DoesNotExist, NoReverseMatch, TypeError, AttributeError) as e:
            logger.exception(e)

        return attrs

    def get_bound_field(self, form, field_name):
        ret = BoundField(form, self, field_name)
        ret.field.widget.attrs["data-name"] = ret.name
        ret.field.widget.attrs["data-label"] = ret.label
        return ret
