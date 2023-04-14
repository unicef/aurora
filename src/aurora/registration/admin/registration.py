import csv
import io
import json
import logging
from django.utils.module_loading import import_string
from hashlib import md5
from smart_admin.mixins import LinkedObjectsMixin

from admin_extra_buttons.decorators import button, choice, view
from admin_sync.mixin import SyncMixin
from dateutil.utils import today
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db.models import JSONField
from django.db.models.signals import post_delete, post_save
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import Template
from django.template.loader import select_template
from django.urls import reverse, translate_url
from django.utils.text import slugify
from django_redis import get_redis_connection
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from aurora.core.admin.base import ConcurrencyVersionAdmin
from aurora.core.forms import CSVOptionsForm, DateFormatsForm, VersionMedia
from aurora.core.models import FormSet, Validator, FlexForm, FlexFormField
from aurora.core.utils import (
    build_dict,
    build_form_fake_data,
    clone_model,
    get_system_cache_version,
    is_root,
    namify,
)
from aurora.i18n.forms import TemplateForm, TranslationForm
from aurora.i18n.translate import Translator
from aurora.registration.admin.filters import (
    OrganizationFilter,
    RegistrationProjectFilter,
)
from aurora.registration.admin.forms import DebugForm
from aurora.registration.admin.protocol import AuroraSyncRegistrationProtocol
from aurora.registration.forms import (
    CloneForm,
    JamesForm,
    RegistrationExportForm,
    RegistrationForm,
)
from aurora.registration.models import Record, Registration

logger = logging.getLogger(__name__)


def can_export_data(request, obj, handler=None):
    return (obj.export_allowed and request.user.has_perm("registration.export_data", obj)) or is_root(request)


class RegistrationAdmin(ConcurrencyVersionAdmin, LinkedObjectsMixin, SyncMixin, SmartModelAdmin):
    search_fields = ("name", "title", "slug")
    date_hierarchy = "start"
    list_filter = (
        "active",
        ("flex_form__project__organization", OrganizationFilter),
        ("flex_form__project", RegistrationProjectFilter),
        "archived",
        "protected",
        "show_in_homepage",
    )
    list_display = ("name", "slug", "project", "secure", "active", "archived", "protected", "show_in_homepage")
    exclude = ("public_key",)
    autocomplete_fields = ("flex_form",)
    save_as = True
    form = RegistrationForm
    readonly_fields = ("version", "last_update_date")
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    change_form_template = None
    change_list_template = None
    filter_horizontal = ("scripts",)
    fieldsets = [
        (None, {"fields": (("version", "last_update_date"),)}),
        (None, {"fields": ("name", "title", "slug")}),
        (
            "Unique",
            {
                "fields": (
                    "unique_field_path",
                    "unique_field_error",
                )
            },
        ),
        ("Config", {"fields": ("flex_form", "validator", "scripts")}),
        ("Validity", {"classes": ("collapse",), "fields": (("start", "end"), ("archived", "active"))}),
        ("Languages", {"classes": ("collapse",), "fields": ("locale", "locales")}),
        ("Security", {"classes": ("collapse",), "fields": ("protected",)}),
        ("Text", {"classes": ("collapse",), "fields": ("intro", "footer")}),
        ("Advanced", {"fields": ("advanced",)}),
        ("Others", {"fields": ("__others__",)}),
    ]
    protocol_class = AuroraSyncRegistrationProtocol

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ["unique_field_path", "unique_field_error"]:
            formfield.widget.attrs = {"style": "width:80%"}
        return formfield

    def get_readonly_fields(self, request, obj=None):
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk and not is_root(request):
            ro = list(ro) + ["slug", "export_allowed"]
        return ro

    def secure(self, obj):
        return bool(obj.public_key) or obj.encrypt_data

    secure.boolean = True

    def admin_sync_show_inspect(self):
        return True

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return (
            VersionMedia(
                js=[
                    "admin/js/vendor/jquery/jquery%s.js" % extra,
                    "admin/js/jquery.init.js",
                    "jquery.compat%s.js" % extra,
                    "clipboard%s.js" % extra,
                ]
            )
            + base
        )

    @view(permission=can_export_data)
    def export_as_csv(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Export")
        reg: Registration = ctx["original"]
        if request.method == "POST":
            form = RegistrationExportForm(request.POST, initial={"include": ".*"})
            opts_form = CSVOptionsForm(request.POST, prefix="csv", initial=CSVOptionsForm.defaults)
            fmt_form = DateFormatsForm(request.POST, prefix="fmt", initial=DateFormatsForm.defaults)
            try:
                if form.is_valid() and opts_form.is_valid() and fmt_form.is_valid():
                    filters, exclude = form.cleaned_data["filters"]
                    include_fields = form.cleaned_data["include"]
                    exclude_fields = form.cleaned_data["exclude"]
                    ctx["filters"] = filters
                    ctx["exclude"] = exclude
                    qs = (
                        Record.objects.filter(registration__id=pk)
                        .defer(
                            "storage",
                            "counters",
                            "files",
                        )
                        .filter(**filters)
                        .exclude(**exclude)
                        .values("fields", "id", "ignored", "timestamp", "registration_id")
                    )
                    if qs.count() >= 5000:
                        raise Exception("Too many records please change your filters. (max 5000)")
                    valid = fmt_form.cleaned_data
                    records = [build_dict(r, **valid) for r in qs]
                    if not records:
                        raise Exception("No records matching filtering criteria")
                    skipped = []
                    all_fields = []
                    for r in records:
                        for field_name in r.keys():
                            if field_name not in skipped and field_name in exclude_fields:
                                skipped.append(field_name)
                            elif field_name not in all_fields and field_name in include_fields:
                                all_fields.append(field_name)
                    if "export" in request.POST:
                        csv_options = opts_form.cleaned_data
                        add_header = csv_options.pop("header")
                        out = io.StringIO()
                        writer = csv.DictWriter(
                            out,
                            # dialect="excel",
                            fieldnames=all_fields,
                            restval="-",
                            extrasaction="ignore",
                            **csv_options,
                        )
                        if add_header:
                            writer.writeheader()
                        writer.writerows(records)
                        out.seek(0)
                        filename = f"Registration_{reg.slug}.csv"
                        response = HttpResponse(
                            out.read(),
                            headers={"Content-Disposition": 'attachment;filename="%s"' % filename},
                            content_type="text/csv",
                        )
                        return response
                    else:
                        ctx["all_fields"] = sorted(set(all_fields))
                        ctx["skipped"] = skipped
                        ctx["qs"] = records[:10]
            except Exception as e:
                logger.exception(e)
                self.message_error_to_user(request, e)
        else:
            form = RegistrationExportForm(initial={"include": ".*"})
            opts_form = CSVOptionsForm(prefix="csv", initial=CSVOptionsForm.defaults)
            fmt_form = DateFormatsForm(prefix="fmt", initial=DateFormatsForm.defaults)

        ctx["form"] = form
        ctx["opts_form"] = opts_form
        ctx["fmt_form"] = fmt_form
        return render(request, "admin/registration/registration/export.html", ctx)

    @view(label="invalidate cache", html_attrs={"class": "aeb-warn"})
    def invalidate_cache(self, request, pk):
        obj = self.get_object(request, pk)
        obj.save()

    @choice(order=900, visible=lambda c: [], change_list=False)
    def encryption(self, button):
        original = button.context["original"]
        colors = ["#DC6C6C", "white"]
        if original.public_key:
            colors = ["#dfd", "black"]
            button.choices = [self.removekey]
        elif original.encrypt_data:
            colors = ["#dfd", "black"]
            self.toggle_encryption.func._handler.config["label"] = "Disable Symmetric"
            button.choices = [self.toggle_encryption]
        else:
            self.toggle_encryption.func._handler.config["label"] = "Enable Symmetric"
            self.generate_keys.func._handler.config["label"] = "Enable RSA"
            button.choices = [self.generate_keys, self.toggle_encryption]
        button.config["html_attrs"] = {"style": f"background-color:{colors[0]};color:{colors[1]}"}
        return button

    @view(label="Symmetric Encryption")
    def toggle_encryption(self, request, pk):
        self.object = self.get_object(request, pk)
        self.object.encrypt_data = not self.object.encrypt_data
        self.object.save()

    @view()
    def removekey(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Remove Encryption Key")
        if request.method == "POST":
            self.object = self.get_object(request, pk)
            self.object.public_key = ""
            self.object.save()
            self.message_user(request, "Encryption key removed", messages.WARNING)
            self.log_change(request, self.object, "Encryption Key has been removed")
            return HttpResponseRedirect("..")
        else:
            return render(request, "admin/registration/registration/keys_remove.html", ctx)

    @view()
    def generate_keys(self, request, pk):
        ctx = self.get_common_context(
            request, pk, media=self.media, title="Generate Private/Public Key pair to encrypt this Registration data"
        )

        if request.method == "POST":
            ctx["title"] = "Key Pair Generated"
            private_pem, public_pem = self.object.setup_encryption_keys()
            ctx["private_key"] = private_pem
            ctx["public_key"] = public_pem
            self.log_change(request, self.object, "Encryption Keys have been generated")

        return render(request, "admin/registration/registration/keys.html", ctx)

    @choice(order=900, change_list=False)
    def admin(self, button):
        button.choices = [
            self.james_editor,
            self.inspect,
            self.clone,
            self.create_translation,
            self.prepare_translation,
            self.create_custom_template,
            self.debug,
        ]
        return button

    @view()
    def debug(self, request, pk):
        ctx = self.get_common_context(request, pk)
        if request.method == "POST":
            form = DebugForm(request.POST)
            if form.is_valid():
                target = form.cleaned_data["search"]
                v = Validator.objects.filter(code__icontains=target).defer("code")
                fss = FormSet.objects.filter(advanced__icontains=target).defer("advanced")
                frms = FlexForm.objects.filter(advanced__icontains=target).defer("advanced")
                flds = FlexFormField.objects.filter(advanced__icontains=target).defer("advanced")
                ctx["results"] = {
                    "validators": [(str(e), e.get_admin_change_url()) for e in v],
                    "forms": [(str(e), e.get_admin_change_url()) for e in frms],
                    "fields": [(str(e), e.get_admin_change_url()) for e in flds],
                    "formsets": [(str(e), e.get_admin_change_url()) for e in fss],
                }
            else:
                pass
        else:
            form = DebugForm()

        ctx["form"] = form
        return render(request, "admin/registration/registration/debug.html", ctx)

    @view()
    def inspect(self, request, pk):
        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Inspect Registration",
        )
        return render(request, "admin/registration/registration/inspect.html", ctx)

    @view()
    def clone(self, request, pk):
        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Clone Registration",
        )
        reg: Registration = ctx["original"]
        if request.method == "POST":
            form = CloneForm(request.POST)
            if form.is_valid():
                try:
                    for dip in [
                        "form_dip",
                        "field_dip",
                        "formset_dip",
                        "form_del_dip",
                        "field_del_dip",
                        "formset_del_dip",
                    ]:
                        post_save.disconnect(dispatch_uid=dip)
                        post_delete.disconnect(dispatch_uid=dip)

                    with atomic():
                        source = Registration.objects.get(id=reg.pk)
                        title = form.cleaned_data["title"]
                        reg, __ = clone_model(source, name=namify(title), title=title, version=1, slug=slugify(title))
                        if form.cleaned_data["deep"]:
                            main_form, __ = clone_model(
                                source.flex_form, name=f"{source.flex_form.name}-(clone: {reg.name})"
                            )
                            reg.flex_form = main_form
                            reg.save()
                            for fld in source.flex_form.fields.all():
                                clone_model(fld, flex_form=main_form)

                            formsets = FormSet.objects.filter(parent=source.flex_form)
                            forms = {}
                            for fs in formsets:
                                forms[fs.flex_form.pk] = fs.flex_form
                                forms[fs.parent.pk] = fs.parent

                            for frm in forms.values():
                                frm2, created = clone_model(frm, name=f"{frm.name}-(clone: {reg.name})")
                                forms[frm.pk] = frm2
                                for field in frm.fields.all():
                                    clone_model(field, name=field.name, flex_form=frm2)

                            for fs in formsets:
                                clone_model(fs, parent=forms[fs.parent.pk], flex_form=forms[fs.flex_form.pk])
                        return HttpResponseRedirect(reverse("admin:registration_registration_inspect", args=[reg.pk]))
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)

            else:
                ctx["form"] = form
        else:
            form = CloneForm()
            ctx["form"] = form
        return render(request, "admin/registration/registration/clone.html", ctx)

    @view()
    def create_custom_template(self, request, pk):
        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Create Custom Template",
        )
        if request.method == "POST":
            obj = ctx["original"]
            form = TemplateForm(request.POST)
            if form.is_valid():
                from dbtemplates.models import Template as DbTemplate

                lang = form.cleaned_data["locale"]
                source: Template = select_template(
                    [
                        f"registration/{obj.locale}/{obj.slug}.html",
                        f"registration/{obj.slug}.html",
                        "registration/register.html",
                    ]
                )
                if lang == "-":
                    name = f"registration/{obj.slug}.html"
                else:
                    name = f"registration/{lang}/{obj.slug}.html"
                if hasattr(source, "template"):
                    content = source.template.source
                    source_name = source.template.name
                else:
                    content = ""
                tpl, created = DbTemplate.objects.get_or_create(name=name, defaults={"content": content})
                ctx["custom_template"] = tpl
                ctx["created"] = created
                ctx["source"] = source_name

        else:
            ctx["form"] = TemplateForm()
        return render(request, "admin/registration/registration/create_template.html", ctx)

    @view()
    def prepare_translation(self, request, pk):
        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Prepare Translation File",
        )
        instance: Registration = ctx["original"]
        if request.method == "POST":
            if "create" in request.POST:
                form = TranslationForm(request.POST)
                if form.is_valid():
                    key = f"i18n_{request.user.pk}_{md5(request.session.session_key.encode()).hexdigest()}"
                    con = get_redis_connection("default")
                    con.delete(key)
                    locale = form.cleaned_data["locale"]
                    translate = form.cleaned_data["translate"]
                    if locale not in instance.locales:
                        self.message_user(request, "Language not enabled for this registration", messages.ERROR)
                        return HttpResponseRedirect(".")
                    self.create_translation(self, request, pk)
                    stored = con.lrange(key, 0, -1)
                    collected = sorted(set([c.decode() for c in stored]))
                    from aurora.i18n.models import Message

                    entries = list(Message.objects.filter(locale=locale).values_list("msgid", "msgstr"))
                    data = dict(entries)
                    if translate == "2":
                        t: Translator = import_string(settings.TRANSLATOR_SERVICE)()
                        func = lambda x: t.translate(locale, x)
                    elif translate == "1":
                        t: Translator = import_string(settings.TRANSLATOR_SERVICE)()
                        func = lambda x: x if data.get(x, "") == x else t.translate(locale, x)
                    else:
                        func = lambda x: data.get(x, "")
                    ctx["collected"] = {c: func(c) for c in collected}
                    ctx["language_code"] = locale
            elif "export" in request.POST:
                selection = request.POST.getlist("selection")
                language_code = request.POST.get("language_code")
                msgids = [request.POST.get(f"msgid_{i}") for i in selection]
                response = HttpResponse(
                    content_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{instance.name}_{language_code}.csv"'},
                )
                writer = csv.writer(response, dialect="excel")
                for i, msg in enumerate(msgids, 1):
                    writer.writerow([str(i), msg, ""])
                return response
                # language_code = request.POST.get("language_code")
                # for i, row in enumerate(data["messages"], 1):

        else:
            form = TranslationForm()
            ctx["form"] = form

        return render(request, "admin/registration/registration/translation.html", ctx)

    @view()
    def create_translation(self, request, pk):
        from aurora.i18n.forms import LanguageForm
        from aurora.i18n.models import Message

        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Generate Translation",
        )
        instance: Registration = ctx["original"]
        if request.method == "POST":
            form = LanguageForm(request.POST)
            if form.is_valid():
                locale = form.cleaned_data["locale"]
                existing = Message.objects.filter(locale=locale).count()
                uri = reverse("register", args=[instance.slug, instance.version])
                uri = translate_url(uri, locale)
                from django.test import Client

                key = f"i18n_{request.user.pk}_{md5(request.session.session_key.encode()).hexdigest()}"
                settings.ALLOWED_HOSTS.append("testserver")
                headers = {"HTTP_ACCEPT_LANGUAGE": "locale", "HTTP_I18N_SESSION": key, "HTTP_I18N": "true"}
                try:
                    client = Client(**headers)
                    r1 = client.get(uri)
                    if r1.status_code == 302:
                        raise Exception(f"GET: {uri} - {r1.status_code}: {r1.headers['location']}")
                    if r1.status_code != 200:
                        raise Exception(f"GET: {uri} - {r1.status_code}")
                    r2 = client.post(uri, {}, **headers)
                    if r2.status_code != 200:
                        raise Exception(f"POST: {uri} - {r2.status_code}")
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)

                updated = Message.objects.filter(locale=locale).count()
                added = Message.objects.filter(locale=locale, draft=True, timestamp__date=today())
                self.message_user(request, f"{updated - existing} messages created. {updated} available")
                ctx["uri"] = uri
                ctx["locale"] = locale
                ctx["added"] = added
            else:
                ctx["form"] = form
        else:
            form = LanguageForm()
            ctx["form"] = form
        return render(request, "admin/registration/registration/translation.html", ctx)

    @choice(order=900, change_list=False)
    def data(self, button):
        button.choices = [
            self.charts,
            self.inspect_data,
            self.view_collected_data,
        ]
        if can_export_data(button.context["request"], button.original):
            button.choices.append(self.export_as_csv)
        return button

    @view()
    def inspect_data(self, request, pk):
        obj = self.get_object(request, pk)
        return HttpResponseRedirect(reverse("register-data", args=[obj.slug]))

    @view(change_form=True, html_attrs={"target": "_new"})
    def charts(self, request, pk):
        return HttpResponseRedirect(reverse("charts:registration", args=[pk]))

    @view(permission=is_root, html_attrs={"class": "aeb-warn"})
    def view_collected_data(self, button, pk):
        base = reverse("admin:registration_record_changelist")
        url = f"{base}?registration__exact={pk}"
        return HttpResponseRedirect(url)

    @view()
    def james_fake_data(self, request, pk):
        reg = self.get_object(request, pk)
        data = cache.get(f"james_{pk}", version=get_system_cache_version())
        if not data:
            form_class = reg.flex_form.get_form_class()
            data = json.dumps(build_form_fake_data(form_class), indent=4)
            cache.set(f"james_{pk}", data, version=get_system_cache_version())

        return HttpResponse(data)

    @view()
    def james_editor(self, request, pk):
        ctx = self.get_common_context(request, pk, title="JAMESPath Editor")
        if request.method == "POST":
            form = JamesForm(request.POST, instance=ctx["original"])
            if form.is_valid():
                form.save()
                cache.set(f"james_{pk}", form.cleaned_data["data"], version=get_system_cache_version())
                return HttpResponseRedirect(".")
        else:
            data = cache.get(f"james_{pk}", version=get_system_cache_version())
            form = JamesForm(instance=ctx["original"], initial={"data": data})
        ctx["form"] = form
        return render(request, "admin/registration/registration/james_editor.html", ctx)

    @button(visible=False)
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Test")
        form = self.object.flex_form.get_form_class()
        ctx["registration"] = self.object
        ctx["form"] = form
        return render(request, "admin/registration/registration/test.html", ctx)

    def get_changeform_buttons(self, context):
        base = super().get_changeform_buttons(context)
        return sorted(
            [h for h in base if h.change_form in [True, None]],
            key=lambda item: item.config.get("order", 1),
        )

    def get_changelist_buttons(self, context):
        return sorted(
            [h for h in self.extra_button_handlers.values() if h.change_list in [True, None]],
            key=lambda item: item.config.get("order", 1),
        )


class DecryptForm(forms.Form):
    key = forms.CharField(widget=forms.Textarea)
