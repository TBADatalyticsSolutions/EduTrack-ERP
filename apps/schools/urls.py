from django.urls import path

from .views import (
    school_create,
    school_dashboard,
    school_edit,
    subscription_edit,
    subscription_list,
)


urlpatterns = [
    path("", school_dashboard, name="school-dashboard"),
    path("add/", school_create, name="school-create"),
    path("<uuid:pk>/edit/", school_edit, name="school-edit"),
    path("subscriptions/", subscription_list, name="subscription-list"),
    path("subscriptions/<uuid:pk>/edit/", subscription_edit, name="subscription-edit"),
]
