from admin_extra_buttons.decorators import button, view
from admin_sync.mixin import SyncMixin
from django.conf import settings
from django.shortcuts import render
from smart_admin.modeladmin import SmartModelAdmin

from .forms import FlatPageForm

INITIAL_CONTENT = """

"""


class FlatPageAdmin(SyncMixin, SmartModelAdmin):
    form = FlatPageForm
    list_display = (
        "title",
        "url",
        "registration_required",
    )
    list_filter = ("sites", "registration_required")
    filter_horizontal = ("sites",)
    search_fields = ("url", "title")
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("url", "title", "content", "sites")}),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": (
                    "enable_comments",
                    "registration_required",
                    "template_name",
                ),
            },
        ),
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial["content"] = INITIAL_CONTENT
        initial["sites"] = settings.SITE_ID
        return initial

    @view()
    def xrender(self, request, pk):
        obj = self.get_object(request, pk)
        from aurora.flatpages.views import render_flatpage

        return render_flatpage(request, obj)

    @button()
    def preview(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Preview")
        return render(request, "admin/flatpages/flatpage/preview.html", ctx)
