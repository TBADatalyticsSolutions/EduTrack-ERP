from django.urls import path

from . import views_auth


urlpatterns = [

    path(
        "login/",
        views_auth.login_view,
        name="login",
    ),

    path(
        "logout/",
        views_auth.logout_view,
        name="logout",
    ),

    path(
        "password-change/",
        views_auth.password_change_view,
        name="password-change",
    ),

    path(
    "password-reset/",
    views_auth.CustomPasswordResetView.as_view(),
    name="password-reset",
    ),

    path(
        "password-reset/done/",
        views_auth.CustomPasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        views_auth.CustomPasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),

    path(
    "password-reset/complete/",
    views_auth.CustomPasswordResetCompleteView.as_view(),
    name="password-reset-complete",
    ),

]