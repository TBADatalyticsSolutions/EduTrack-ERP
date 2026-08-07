from django.contrib import admin
from apps.accounts.utils import log_activity

from .models import (
from apps.accounts.utils import log_activity
    Department,
    Teacher,
    TeacherSubject,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school",
    )

    search_fields = (
        "name",
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "department",
        "employment_status",
    )

    search_fields = (
        "employee_id",
        "first_name",
        "last_name",
    )

    list_filter = (
        "department",
        "employment_status",
    )


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "subject",
        "school_class",
    )

    list_filter = (
        "school_class",
        "subject",
    )