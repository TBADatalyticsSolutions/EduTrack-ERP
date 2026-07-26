from django.contrib import admin

from .models import (
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


@admin.register(GradeSetting)
class GradeSettingAdmin(admin.ModelAdmin):
    list_display = (
        "grade",
        "minimum_score",
        "maximum_score",
        "remark",
    )


class SubjectResultInline(admin.TabularInline):
    model = SubjectResult
    extra = 0


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "session",
        "term",
        "average",
        "position",
        "published",
    )

    list_filter = (
        "session",
        "term",
        "published",
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
    )