from django.urls import path

from .views import (
    teacher_dashboard,
    teacher_list,
    teacher_create,
    teacher_detail,
    teacher_edit,
)
from .views_assignments import teacher_assignments, teacher_remove_assignment

app_name = "teachers"

urlpatterns = [
    path("", teacher_dashboard, name="dashboard"),
    path("list/", teacher_list, name="list"),
    path("add/", teacher_create, name="create"),
    path("<uuid:pk>/assignments/", teacher_assignments, name="assignments"),
    path("assignments/<uuid:pk>/remove/", teacher_remove_assignment, name="remove-assignment"),
    path("<uuid:pk>/", teacher_detail, name="detail"),
    path("<uuid:pk>/edit/", teacher_edit, name="edit"),
]
