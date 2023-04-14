from django.urls import path

from . import views

urlpatterns = [
    path("org/<slug:org>/prj/<slug:prj>/reg/<slug:reg>/", views.flatpage, name="flatpage1"),
    path("org/<slug:org>/prj/<slug:prj>/", views.flatpage, name="flatpage2"),
    path("org/<slug:org>/", views.flatpage, name="flatpage3"),
    # path("/org/<slug:slug>/", views.org_page, name="flatpage"),
    # path("<path:url>", views.flatpage, name="flatpage"),
]
