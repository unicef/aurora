import logging

from admin_extra_buttons.decorators import button, view
from admin_ordering.admin import OrderableAdmin
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.querystring import QueryStringFilter
from django import forms
from django.contrib import messages
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from ...administration.mixin import LoadDumpMixin
from ..admin_sync import SyncMixin
from ..forms import Select2Widget
from ..models import FlexFormField
from ..utils import is_root
from .base import ConcurrencyVersionAdmin
from ..editors.field import FieldEditor
from .filters import Select2FieldComboFilter

logger = logging.getLogger(__name__)

cache = caches["default"]


class FlexFormFieldForm(forms.ModelForm):
    class Meta:
        model = FlexFormField
        exclude = ()


@register(FlexFormField)
class FlexFormFieldAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, OrderableAdmin, SmartModelAdmin):
    search_fields = ("name", "label")
    list_display = ("label", "name", "flex_form", "field_type", "required", "enabled")
    list_editable = ["required", "enabled"]
    list_filter = (
        ("flex_form", AutoCompleteFilter),
        ("field_type", Select2FieldComboFilter),
        QueryStringFilter,
    )
    autocomplete_fields = ("flex_form", "validator")
    save_as = True
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    form = FlexFormFieldForm
    ordering_field = "ordering"
    order = "ordering"
    readonly_fields = ("version", "last_update_date")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("flex_form")

    # change_list_template = "reversion/change_list.html"
    def get_readonly_fields(self, request, obj=None):
        if is_root(request):
            return []
        else:
            return super().get_readonly_fields(request, obj)

    def field_type(self, obj):
        if obj.field_type:
            return obj.field_type.__name__
        else:
            return "[[ removed ]]"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "advanced":
            kwargs["widget"] = JSONEditor()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "field_type":
            kwargs["widget"] = Select2Widget()
            return db_field.formfield(**kwargs)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("advanced", FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
        return initial

    @button(label="editor")
    def field_editor(self, request, pk):
        self.editor = FieldEditor(self, request, pk)
        if request.method == "POST":
            ret = self.editor.post(request, pk)
            self.message_user(request, "Saved", messages.SUCCESS)
            return ret
        else:
            return self.editor.get(request, pk)

    @view()
    def widget_refresh(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.refresh()

    @view()
    def widget_code(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.get_html()

    @view()
    def widget_advanced(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.get_advanced()

    @view()
    def widget_kwargs(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.get_kwargs()

    @view()
    def widget_display(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.render()

    # @button()
    # def test(self, request, pk):
    #     ctx = self.get_common_context(request, pk)
    #     try:
    #         fld = ctx["original"]
    #         instance = fld.get_instance()
    #         ctx["debug_info"] = {
    #             # "widget": getattr(instance, "widget", None),
    #             "field_kwargs": fld.get_field_kwargs(),
    #             # "options": getattr(instance, "options", None),
    #             # "choices": getattr(instance, "choices", None),
    #             # "widget_attrs": instance.widget_attrs(instance.widget),
    #         }
    #         form_class_attrs = {
    #             "sample": instance,
    #         }
    #         form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)
    #
    #         if request.method == "POST":
    #             form = form_class(request.POST)
    #
    #             if form.is_valid():
    #                 ctx["debug_info"]["cleaned_data"] = form.cleaned_data
    #                 self.message_user(
    #                     request, f"Form validation success. You have selected: {form.cleaned_data['sample']}"
    #                 )
    #         else:
    #             form = form_class()
    #         ctx["form"] = form
    #         ctx["instance"] = instance
    #     except Exception as e:
    #         logger.exception(e)
    #         ctx["error"] = e
    #         raise
    #
    #     return render(request, "admin/core/flexformfield/test.html", ctx)
