import logging
from smart_admin.mixins import LinkedObjectsMixin

from admin_extra_buttons.decorators import button, view
from admin_ordering.admin import OrderableAdmin
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.querystring import QueryStringFilter
from django import forms
from django.contrib import messages
from django.contrib.admin import TabularInline, register
from django.core.cache import caches
from smart_admin.modeladmin import SmartModelAdmin

from ...administration.mixin import LoadDumpMixin
from ..admin_sync import SyncMixin
from ..models import FlexForm, FlexFormField, FormSet
from ..utils import render
from .base import ConcurrencyVersionAdmin
from .filters import ProjectFilter, UsedByRegistration, UsedInRFormset
from ..editors.flex_form import FormEditor

logger = logging.getLogger(__name__)

cache = caches["default"]


class FormSetInline(OrderableAdmin, TabularInline):
    model = FormSet
    fk_name = "parent"
    extra = 0
    fields = ("name", "flex_form", "extra", "max_num", "min_num", "ordering")
    show_change_link = True
    ordering_field = "ordering"
    ordering_field_hide_input = True

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class FlexFormFieldFormInline(forms.ModelForm):
    class Meta:
        model = FlexFormField
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["name"].widget.attrs = {"readonly": True, "tyle": "background-color:#f8f8f8;border:none"}


class FlexFormFieldInline(LoadDumpMixin, OrderableAdmin, TabularInline):
    template = "admin/core/flexformfield/tabular.html"
    model = FlexFormField
    form = FlexFormFieldFormInline
    fields = ("ordering", "label", "name", "required", "enabled", "field_type")
    show_change_link = True
    extra = 0
    ordering_field = "ordering"
    ordering_field_hide_input = True

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        # if db_field.name == "field_type":
        #     kwargs["widget"] = Select2Widget()
        #     return db_field.formfield(**kwargs)
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@register(FlexForm)
class FlexFormAdmin(SyncMixin, ConcurrencyVersionAdmin, LinkedObjectsMixin, SmartModelAdmin):
    SYNC_COOKIE = "sync"
    inlines = [
        FlexFormFieldInline,
        FormSetInline,
    ]
    list_display = (
        "name",
        # "validator",
        "project",
        "is_main",
    )
    list_filter = (
        QueryStringFilter,
        ("project__organization", AutoCompleteFilter),
        ("project", ProjectFilter),
        ("registration", UsedByRegistration),
        ("formset", UsedInRFormset),
        ("formset__parent", UsedInRFormset),
    )
    search_fields = ("name",)
    readonly_fields = ("version", "last_update_date")
    autocomplete_fields = ("validator", "project")
    ordering = ("name",)
    save_as = True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("registration_set")
            .select_related(
                "project",
            )
        )

    def is_main(self, obj):
        return obj.registration_set.exists()

    is_main.boolean = True

    @button(html_attrs={"class": "aeb-danger"})
    def invalidate_cache(self, request):
        from ..cache import cache

        cache.clear()

    @button(label="invalidate cache", html_attrs={"class": "aeb-warn"})
    def invalidate_cache_single(self, request, pk):
        obj = self.get_object(request, pk)
        obj.save()

    @button()
    def inspect(self, request, pk):
        ctx = self.get_common_context(request, pk)
        ctx["title"] = str(ctx["original"])
        return render(request, "admin/core/flexform/inspect.html", ctx)

    @button(label="editor")
    def form_editor(self, request, pk):
        self.editor = FormEditor(self, request, pk)
        if request.method == "POST":
            ret = self.editor.post(request, pk)
            self.message_user(request, "Saved", messages.SUCCESS)
            return ret
        else:
            return self.editor.get(request, pk)

    @view()
    def widget_attrs(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.get_configuration()

    @view()
    def editor_sort(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.sort()

    @view()
    def editor_advanced(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.get_advanced()

    @view()
    def widget_refresh(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.refresh()

    @view()
    def widget_code(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.get_code()

    @view()
    def widget_display(self, request, pk):
        editor = FormEditor(self, request, pk)
        return editor.render()

    # @button()
    # def test(self, request, pk):
    #     ctx = self.get_common_context(request, pk)
    #     form_class = self.object.get_form_class()
    #     if request.method == "POST":
    #         form = form_class(request.POST, initial=self.object.get_initial())
    #         if form.is_valid():
    #             ctx["cleaned_data"] = form.cleaned_data
    #             self.message_user(request, "Form is valid")
    #     else:
    #         form = form_class(initial=self.object.get_initial())
    #     ctx["form"] = form
    #     return render(request, "admin/core/flexform/test.html", ctx)
    #
    # @view(http_basic_auth=True, permission=lambda request, obj: request.user.is_superuser)
    # def export(self, request):
    #     try:
    #         frm = SyncConfigForm(request.GET)
    #         if frm.is_valid():
    #             apps = frm.cleaned_data["apps"]
    #             buf = io.StringIO()
    #             call_command(
    #                 "dumpdata",
    #                 *apps,
    #                 stdout=buf,
    #                 exclude=["registration.Record"],
    #                 use_natural_foreign_keys=True,
    #                 use_natural_primary_keys=True,
    #             )
    #             return JsonResponse(json.loads(buf.getvalue()), safe=False)
    #         else:
    #             return JsonResponse(frm.errors, status=400)
    #     except Exception as e:
    #         logger.exception(e)
    #         return JsonResponse({}, status=400)

    # def _get_signed_cookie(self, request, form):
    #     signer = Signer(request.user.password)
    #     return signer.sign_object(form.cleaned_data)
    #
    # def _get_saved_credentials(self, request):
    #     try:
    #         signer = Signer(request.user.password)
    #         obj: dict = signer.unsign_object(request.COOKIES.get(self.SYNC_COOKIE, {}))
    #         return obj
    #     except BadSignature:
    #         return {}

    # @button(label="Import")
    # def _import(self, request):
    #     ctx = self.get_common_context(request, title="Import")
    #     cookies = {}
    #     if request.method == "POST":
    #         form = SyncForm(request.POST)
    #         if form.is_valid():
    #             try:
    #                 auth = HTTPBasicAuth(form.cleaned_data["username"], form.cleaned_data["password"])
    #                 if form.cleaned_data["remember"]:
    #                     cookies = {self.SYNC_COOKIE: self._get_signed_cookie(request, form)}
    #                 else:
    #                     cookies = {self.SYNC_COOKIE: ""}
    #                 url = f"{form.cleaned_data['host']}core/flexform/export/?"
    #                 for app in form.cleaned_data["apps"]:
    #                     url += f"apps={app}&"
    #                 if not url.startswith("http"):
    #                     url = f"https://{url}"
    #
    #                 workdir = Path(".").absolute()
    #                 out = io.StringIO()
    #                 with requests.get(url, stream=True, auth=auth) as res:
    #                     if res.status_code != 200:
    #                         raise Exception(str(res))
    #                     ctx["url"] = url
    #                     with tempfile.NamedTemporaryFile(
    #                         dir=workdir, prefix="~SYNC", suffix=".json", delete=not settings.DEBUG
    #                     ) as fdst:
    #                         fdst.write(res.content)
    #                         with disable_concurrency():
    #                             fixture = (workdir / fdst.name).absolute()
    #                             call_command("loaddata", fixture, stdout=out, verbosity=3)
    #
    #                         message = out.getvalue()
    #                         self.message_user(request, message)
    #                 ctx["res"] = res
    #             except (Exception, JSONDecodeError) as e:
    #                 logger.exception(e)
    #                 self.message_error_to_user(request, e)
    #     else:
    #         form = SyncForm(initial=self._get_saved_credentials(request))
    #     ctx["form"] = form
    #     return render(request, "admin/core/flexform/import.html", ctx, cookies=cookies)
