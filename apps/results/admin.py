from django.contrib import admin
from apps.accounts.utils import log_activity

from .models import (
from apps.accounts.utils import log_activity
    AssessmentType,
    GradeSetting,
    StudentResult,
    SubjectResult,
)


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "maximum_score",
        "order",
    )

    ordering = (
        "order",
    )


@admin.register(GradeSetting)
class GradeSettingAdmin(admin.ModelAdmin):

    list_display = (
        "grade",
        "minimum_score",
        "maximum_score",
        "remark",
    )

    ordering = (
        "-minimum_score",
    )


class SubjectResultInline(admin.TabularInline):

    model = SubjectResult

    extra = 0


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "school_class",
        "session",
        "term",
        "average",
        "position_display",
        "published",
    )

    list_filter = (
        "school_class",
        "session",
        "term",
        "published",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    inlines = [
        SubjectResultInline,
    ]


@admin.register(SubjectResult)
class SubjectResultAdmin(admin.ModelAdmin):

    list_display = (
        "student_result",
        "subject",
        "total",
        "grade",
        "remark",
    )

    list_filter = (
        "subject",
    )

    search_fields = (
        "student_result__student__admission_number",
        "student_result__student__first_name",
        "student_result__student__last_name",
    )