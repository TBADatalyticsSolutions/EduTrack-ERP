"""
URL configuration for EduTrack ERP.

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [

    # ==================================================
    # Django Admin
    # ==================================================

    path(
        "admin/",
        admin.site.urls,
    ),

    # ==================================================
    # Dashboard
    # ==================================================

    path(
        "",
        include("apps.dashboard.urls"),
    ),

    # ==================================================
    # Accounts
    # ==================================================

    path(
        "accounts/",
        include("apps.accounts.urls"),
    ),

    # ==================================================
    # Students
    # ==================================================

    path(
        "students/",
        include("apps.students.urls"),
    ),

    # ==================================================
    # Attendance
    # ==================================================

    path(
        "attendance/",
        include("apps.attendance.urls"),
    ),

]

# ==================================================
# Serve Media Files (Development Only)
# ==================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )