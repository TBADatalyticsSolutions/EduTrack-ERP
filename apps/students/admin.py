from django.contrib import admin

from .models import (
    Student,
    Parent,
    PromotionHistory,
    GraduationHistory,
    TransferHistory,
)
@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "from_class",
        "to_class",
        "transfer_date",
        "approved_by",
        "rolled_back",
    )

    list_filter = (
        "transfer_date",
        "rolled_back",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "transfer_date",
    )
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "full_name",
        "current_class",
        "current_session",
        "status",
    )

    list_filter = (
        "status",
        "current_class",
        "current_session",
        "gender",
    )

    search_fields = (
        "admission_number",
        "first_name",
        "last_name",
    )


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
    )


@admin.register(PromotionHistory)
class PromotionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "academic_session",
        "from_class",
        "to_class",
        "action",
        "average_score",
        "approved_by",
        "approved_at",
    )

    list_filter = (
        "academic_session",
        "action",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "approved_at",
    )


@admin.register(GraduationHistory)
class GraduationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "graduated_from",
        "academic_session",
        "graduation_date",
        "graduated_by",
        "rolled_back",
    )

    list_filter = (
        "academic_session",
        "rolled_back",
        "graduation_date",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )