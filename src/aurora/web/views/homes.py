import logging
from django.shortcuts import get_object_or_404
from django.http import Http404
from aurora.core.models import Organization, Project
from aurora.core.utils import render

logger = logging.getLogger(__name__)


def org_index(request, org):
    ctx = {}
    organization = get_object_or_404(Organization, slug=org)
    ctx["organization"] = organization

    return render(request, "homes/org_index.html", ctx)


def prj_index(request, org, prj):
    ctx = {}
    try:
        project = Project.objects.select_related("organization").get(organization__slug=org, slug=prj)
    except Project.DoesNotExist:
        raise Http404("No Project matches the given query.")
    ctx["organization"] = project.organization
    ctx["project"] = project

    return render(request, "homes/prj_index.html", ctx)
