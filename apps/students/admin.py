from django.contrib import admin

from .models import (
    Student,
    Parent,
    TransferHistory,
    WithdrawalHistory,
    DisciplineHistory,
    PromotionHistory,
    GraduationHistory,
)


# ==========================================================
# STUDENT
# ==========================================================

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
        "other_name",
    )

    ordering = (
        "admission_number",
    )


# ==========================================================
# PARENT
# ==========================================================

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    ordering = (
        "first_name",
        "last_name",
    )


# ==========================================================
# TRANSFER HISTORY
# ==========================================================

@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "from_class",
        "to_class",
        "from_session",
        "to_session",
        "transfer_date",
        "transferred_by",
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

    ordering = (
        "-transfer_date",
    )


# ==========================================================
# WITHDRAWAL HISTORY
# ==========================================================

@admin.register(WithdrawalHistory)
class WithdrawalHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "from_class",
        "from_session",
        "reason",
        "withdrawn_by",
        "withdrawal_date",
        "reinstated",
    )

    list_filter = (
        "reason",
        "reinstated",
        "withdrawal_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "withdrawal_date",
        "reinstated_date",
    )

    ordering = (
        "-withdrawal_date",
    )


# ==========================================================
# DISCIPLINE HISTORY
# ==========================================================

@admin.register(DisciplineHistory)
class DisciplineHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "action",
        "from_class",
        "from_session",
        "start_date",
        "end_date",
        "reason",
        "disciplined_by",
        "revoked",
    )

    list_filter = (
        "action",
        "revoked",
        "start_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
        "reason",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "revoked_at",
    )

    ordering = (
        "-start_date",
    )


# ==========================================================
# PROMOTION HISTORY
# ==========================================================

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

    ordering = (
        "-approved_at",
    )


# ==========================================================
# GRADUATION HISTORY
# ==========================================================

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
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "graduation_date",
    )

    ordering = (
        "-graduation_date",
    )