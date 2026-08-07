from django.urls import include, path
from apps.accounts.utils import log_activity

from . import views
from apps.accounts.utils import log_activity

from . import views_profile
from apps.accounts.utils import log_activity

urlpatterns = [

    # ==================================================
    # Dashboard
    # ==================================================

    path(
        "dashboard/",
        views.accounts_dashboard,
        name="accounts-dashboard",
    ),

    # ==================================================
    # User Management
    # ==================================================

    path(
        "users/",
        views.user_list,
        name="user-list",
    ),

    path(
        "users/create/",
        views.user_create,
        name="user-create",
    ),

    path(
        "users/<int:pk>/",
        views.user_detail,
        name="user-detail",
    ),

    path(
        "users/<int:pk>/edit/",
        views.user_update,
        name="user-update",
    ),

    path(
        "users/<int:pk>/toggle/",
        views.user_toggle_status,
        name="user-toggle-status",
    ),

    path(
        "users/<int:pk>/delete/",
        views.user_delete,
        name="user-delete",
    ),

    # ==================================================
    # MY PROFILE
    # ==================================================

    path(
        "profile/",
        views_profile.profile_view,
        name="profile",
    ),

    path(
        "profile/edit/",
        views_profile.profile_edit,
        name="profile-edit",
    ),

    # ==================================================
    # Authentication
    # ==================================================

    path(
        "",
        include("apps.accounts.urls_auth"),
    ),

]