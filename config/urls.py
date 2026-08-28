"""
URL configuration for EduTrack ERP.

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("schools/", include("apps.schools.urls")),
    path("students/", include("apps.students.urls")),
    path("teachers/", include("apps.teachers.urls")),
    path("attendance/", include("apps.attendance.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
