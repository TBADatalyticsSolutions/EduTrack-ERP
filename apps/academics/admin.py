from django.contrib import admin
from apps.accounts.utils import log_activity

from .models import (
from apps.accounts.utils import log_activity
    AcademicSession,
    Term,
    SchoolClass,
    ClassArm,
    Subject,
    ClassSubject,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "is_current")
    list_filter = ("school", "is_current")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "session", "is_current")
    list_filter = ("session", "is_current")


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "school")
    search_fields = ("name",)


@admin.register(ClassArm)
class ClassArmAdmin(admin.ModelAdmin):
    list_display = ("school_class", "name")
    list_filter = ("school_class",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "school",
        "is_core",
    )

    search_fields = (
        "code",
        "name",
    )

    list_filter = (
        "school",
        "is_core",
    )


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "school_class",
        "subject",
    )

    list_filter = ("school_class",)
