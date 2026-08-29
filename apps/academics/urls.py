from django.urls import path

from .views import (
    academic_dashboard,
    assignment_create,
    assignment_delete,
    class_create,
    class_edit,
    initialize_academic_data,
    session_create,
    session_edit,
    subject_create,
    subject_edit,
    term_create,
    term_edit,
)

app_name = "academics"

urlpatterns = [
    path("", academic_dashboard, name="dashboard"),
    path("initialize/", initialize_academic_data, name="initialize"),
    path("sessions/add/", session_create, name="session-create"),
    path("sessions/<uuid:pk>/edit/", session_edit, name="session-edit"),
    path("terms/add/", term_create, name="term-create"),
    path("terms/<uuid:pk>/edit/", term_edit, name="term-edit"),
    path("classes/add/", class_create, name="class-create"),
    path("classes/<uuid:pk>/edit/", class_edit, name="class-edit"),
    path("subjects/add/", subject_create, name="subject-create"),
    path("subjects/<uuid:pk>/edit/", subject_edit, name="subject-edit"),
    path("assignments/add/", assignment_create, name="assignment-create"),
    path("assignments/<uuid:pk>/delete/", assignment_delete, name="assignment-delete"),
]
