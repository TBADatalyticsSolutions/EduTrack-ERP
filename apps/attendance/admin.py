from django.contrib import admin

from .models import (
    AttendanceRecord,
    AttendanceSession,
)


# ==========================================================
# ATTENDANCE RECORD INLINE
# ==========================================================

class AttendanceRecordInline(admin.TabularInline):

    model = AttendanceRecord

    extra = 0

    fields = (
        "student",
        "status",
        "remarks",
        "marked_by",
        "marked_at",
    )

    readonly_fields = (
        "marked_by",
        "marked_at",
    )

    ordering = (
        "student__last_name",
        "student__first_name",
    )


# ==========================================================
# ATTENDANCE SESSION ADMIN
# ==========================================================

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):

    list_display = (
        "attendance_date",
        "school",
        "school_class",
        "academic_session",
        "term",
        "is_active",
        "created_by",
        "created_at",
    )

    list_filter = (
        "school",
        "academic_session",
        "term",
        "school_class",
        "attendance_date",
        "is_active",
    )

    search_fields = (
        "school__name",
        "school_class__name",
        "academic_session__name",
        "created_by__username",
    )

    ordering = (
        "-attendance_date",
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "school",
        "school_class",
        "created_by",
    )

    inlines = (
        AttendanceRecordInline,
    )


# ==========================================================
# ATTENDANCE RECORD ADMIN
# ==========================================================

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "attendance_session",
        "status",
        "remarks",
        "marked_by",
        "marked_at",
    )

    list_filter = (
        "status",
        "attendance_session__school",
        "attendance_session__academic_session",
        "attendance_session__term",
        "attendance_session__school_class",
        "attendance_session__attendance_date",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
        "attendance_session__school_class__name",
    )

    readonly_fields = (
        "marked_at",
    )

    autocomplete_fields = (
        "student",
        "attendance_session",
        "marked_by",
    )

    ordering = (
        "-marked_at",
    )
