from django.urls import path

from .views import (
    attendance_dashboard,
    attendance_create,
    attendance_session,
    attendance_close,
    attendance_mark_all_present,
)


urlpatterns = [

    # Attendance Dashboard
    path(
        "",
        attendance_dashboard,
        name="attendance-dashboard",
    ),

    # Create / Open Session
    path(
        "create/",
        attendance_create,
        name="attendance-create",
    ),

    # Mark Attendance
    path(
        "session/<uuid:pk>/",
        attendance_session,
        name="attendance-session",
    ),

    # Close Session
    path(
        "session/<uuid:pk>/close/",
        attendance_close,
        name="attendance-close",
    ),

    path(
    "session/<uuid:pk>/mark-all-present/",
    attendance_mark_all_present,
    name="attendance-mark-all-present",
),

]