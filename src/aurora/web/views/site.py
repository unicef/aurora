import logging
import os

from constance import config
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.cache import get_conditional_response
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views import View
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from aurora.core.utils import get_etag, get_qrcode, render
from aurora.i18n.gettext import gettext as _
from aurora.registration.models import Registration

logger = logging.getLogger(__name__)


def error_csrf(request, reason=""):
    if reason:
        logger.error(reason)
    return TemplateResponse(request, "csrf.html", status=400)


def error_404(request, exception):
    return TemplateResponse(request, "404.html", status=404, headers={"Session-Token": settings.DJANGO_ADMIN_URL})


def offline(request):
    return render(request, "offline.html")


def get_active_registrations():
    registrations = Registration.objects.filter(active=True, show_in_homepage=True)
    return registrations


class PageView(TemplateView):
    template_name = "index.html"

    def get_template_names(self):
        return [f"{self.kwargs['page']}.html"]

    def get_context_data(self, **kwargs):

        return super().get_context_data(
            title="Title", registrations=get_active_registrations(), title2=_("Title2"), **kwargs
        )


@method_decorator(cache_control(public=True), name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_template_names(self):
        return [config.HOME_TEMPLATE, self.template_name]

    def get(self, request, *args, **kwargs):
        res_etag = get_etag(
            request,
            config.HOME_TEMPLATE,
            config.CACHE_VERSION,
            os.environ.get("BUILD_DATE", ""),
            get_language(),
            {True: "staff", False: ""}[request.user.is_staff],
        )
        response = get_conditional_response(request, str(res_etag))
        if response is None:
            response = super().get(request, *args, **kwargs)
            response.headers.setdefault("ETag", res_etag)
        return response

    def get_context_data(self, **kwargs):
        return super().get_context_data(registrations=get_active_registrations(), **kwargs)


class QRCodeView(TemplateView):
    template_name = "qrcode.html"

    def get_context_data(self, **kwargs):
        url = self.request.build_absolute_uri("/")
        qrcode = get_qrcode(url)
        return super().get_context_data(**kwargs, qrcode=qrcode, url=url)


class ProbeView(View):
    http_method_names = ["get", "head"]

    def head(self, request, *args, **kwargs):
        return HttpResponse("Ok")

    def get(self, request, *args, **kwargs):
        return HttpResponse("Ok")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class MaintenanceView(TemplateView):
    template_name = "maintenance.html"

    def get(self, request, *args, **kwargs):
        if not config.MAINTENANCE_MODE:
            return HttpResponseRedirect("/")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
