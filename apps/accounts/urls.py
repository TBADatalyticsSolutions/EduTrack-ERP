from django.urls import include, path

from . import views
from . import views_profile
from .portal_views import portal_dashboard, portal_result_detail

urlpatterns = [
    path("dashboard/", views.accounts_dashboard, name="accounts-dashboard"),
    path("portal/", portal_dashboard, name="portal-dashboard"),
    path("portal/results/<uuid:pk>/", portal_result_detail, name="portal-result-detail"),

    path("users/", views.user_list, name="user-list"),
    path("users/create/", views.user_create, name="user-create"),
    path("users/<int:pk>/", views.user_detail, name="user-detail"),
    path("users/<int:pk>/edit/", views.user_update, name="user-update"),
    path("users/<int:pk>/toggle/", views.user_toggle_status, name="user-toggle-status"),
    path("users/<int:pk>/delete/", views.user_delete, name="user-delete"),

    path("profile/", views_profile.profile_view, name="profile"),
    path("profile/edit/", views_profile.profile_edit, name="profile-edit"),

    path("", include("apps.accounts.urls_auth")),
]
