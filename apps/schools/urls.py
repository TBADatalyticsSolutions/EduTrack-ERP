from django.urls import path

from .views import school_create, school_dashboard, school_edit


urlpatterns = [
    path("", school_dashboard, name="school-dashboard"),
    path("add/", school_create, name="school-create"),
    path("<uuid:pk>/edit/", school_edit, name="school-edit"),
]
