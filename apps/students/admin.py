from django.contrib import admin, messages
from apps.accounts.utils import log_activity
from django.db.models import Count
from apps.accounts.utils import log_activity
from django.utils import timezone
from apps.accounts.utils import log_activity

from .models import (
from apps.accounts.utils import log_activity
    Student,
    Parent,
    PromotionHistory,
    GraduationHistory,
    TransferHistory,
    WithdrawalHistory,
    DisciplineHistory,
)

from .discipline import (
from apps.accounts.utils import log_activity
    suspend_student,
    expel_student,
    reinstate_student_from_suspension,
)


# ==========================================================
# STUDENT ADMIN
# ==========================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "admission_number",
        "full_name",
        "gender",
        "current_class",
        "current_session",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "status",
        "gender",
        "current_class",
        "current_session",
        "is_graduated",
    )

    search_fields = (
        "admission_number",
        "first_name",
        "last_name",
        "other_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "admission_number",
    )

    actions = (
        "bulk_suspend_students",
        "bulk_expel_students",
    )

    # -------------------------------------
    # BULK SUSPEND
    # -------------------------------------

    @admin.action(description="Suspend selected students")
    def bulk_suspend_students(
        self,
        request,
        queryset,
    ):

        success = 0

        for student in queryset:

            ok, _ = suspend_student(
                student=student,
                disciplined_by=request.user,
                reason="OTHER",
                remarks="Bulk suspension via admin.",
            )

            if ok:
                success += 1

        self.message_user(
            request,
            f"{success} student(s) suspended.",
            messages.SUCCESS,
        )

    # -------------------------------------
    # BULK EXPEL
    # -------------------------------------

    @admin.action(description="Expel selected students")
    def bulk_expel_students(
        self,
        request,
        queryset,
    ):

        success = 0

        for student in queryset:

            ok, _ = expel_student(
                student=student,
                disciplined_by=request.user,
                reason="OTHER",
                remarks="Bulk expulsion via admin.",
            )

            if ok:
                success += 1

        self.message_user(
            request,
            f"{success} student(s) expelled.",
            messages.SUCCESS,
        )


# ==========================================================
# PARENT ADMIN
# ==========================================================

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "phone",
        "school",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
    )

    filter_horizontal = (
        "students",
    )


# ==========================================================
# PROMOTION HISTORY
# ==========================================================

@admin.register(PromotionHistory)
class PromotionHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "action",
        "from_class",
        "to_class",
        "academic_session",
        "approved_at",
    )

    list_filter = (
        "action",
        "academic_session",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "approved_at",
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
        "transfer_date",
        "transferred_by",
        "rolled_back",
    )

    list_filter = (
        "rolled_back",
        "transfer_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "transfer_date",
    )


# ==========================================================
# WITHDRAWAL HISTORY
# ==========================================================

@admin.register(WithdrawalHistory)
class WithdrawalHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "reason",
        "withdrawal_date",
        "withdrawn_by",
        "reinstated",
    )

    list_filter = (
        "reason",
        "reinstated",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "withdrawal_date",
    )


# ==========================================================
# GRADUATION HISTORY
# ==========================================================

@admin.register(GraduationHistory)
class GraduationHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "academic_session",
        "graduation_date",
        "graduated_by",
    )

    list_filter = (
        "academic_session",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "graduation_date",
    )


# ==========================================================
# DISCIPLINE HISTORY
# ==========================================================

@admin.register(DisciplineHistory)
class DisciplineHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "action",
        "reason",
        "start_date",
        "end_date",
        "revoked",
        "disciplined_by",
    )

    list_filter = (
        "action",
        "revoked",
        "reason",
        "start_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

    readonly_fields = (
        "start_date",
        "revoked_at",
    )

    ordering = (
        "-start_date",
    )

    actions = (
        "bulk_reinstate_students",
    )

    # -------------------------------------
    # BULK REINSTATE
    # -------------------------------------

    @admin.action(description="Reinstate selected suspended students")
    def bulk_reinstate_students(
        self,
        request,
        queryset,
    ):

        success = 0

        queryset = queryset.filter(
            action="SUSPENSION",
            revoked=False,
        )

        for history in queryset:

            ok, _ = reinstate_student_from_suspension(
                history=history,
                reinstated_by=request.user,
            )

            if ok:
                success += 1

        self.message_user(
            request,
            f"{success} suspension(s) reinstated.",
            messages.SUCCESS,
        )

    # -------------------------------------
    # DASHBOARD STATISTICS
    # -------------------------------------

    def changelist_view(
        self,
        request,
        extra_context=None,
    ):

        extra_context = extra_context or {}

        extra_context["discipline_statistics"] = {

            "total_cases":
                DisciplineHistory.objects.count(),

            "active_suspensions":
                DisciplineHistory.objects.filter(
                    action="SUSPENSION",
                    revoked=False,
                ).count(),

            "reinstated":
                DisciplineHistory.objects.filter(
                    action="SUSPENSION",
                    revoked=True,
                ).count(),

            "expulsions":
                DisciplineHistory.objects.filter(
                    action="EXPULSION",
                ).count(),

            "cases_by_reason":
                DisciplineHistory.objects.values(
                    "reason",
                ).annotate(
                    total=Count("id"),
                ).order_by(
                    "-total",
                )[:10],
        }

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )