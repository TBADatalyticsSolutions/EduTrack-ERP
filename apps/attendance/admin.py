from django.contrib import admin

from .models import (
    AttendanceSession,
    StudentAttendance,
    TeacherAttendance,
    AttendanceSummary,
)


# ==========================================================
# Student Attendance Inline
# ==========================================================

class StudentAttendanceInline(admin.TabularInline):
    model = StudentAttendance
    extra = 0

    fields = (
        "student",
        "status",
        "time_in",
        "time_out",
        "remark",
        "marked_by",
    )

    autocomplete_fields = (
        "student",
        "marked_by",
    )


# ==========================================================
# Attendance Session
# ==========================================================

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):

    list_display = (
        "attendance_date",
        "school",
        "school_class",
        "session",
        "term",
    )

    list_filter = (
        "school",
        "session",
        "term",
        "school_class",
        "attendance_date",
    )

    search_fields = (
        "school_class__name",
        "school__name",
    )

    ordering = (
        "-attendance_date",
    )

    date_hierarchy = "attendance_date"

    inlines = [
        StudentAttendanceInline,
    ]


# ==========================================================
# Student Attendance
# ==========================================================

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "attendance_session",
        "status",
        "time_in",
        "time_out",
        "marked_by",
    )

    list_filter = (
        "status",
        "attendance_session__attendance_date",
        "attendance_session__school_class",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )

    autocomplete_fields = (
        "student",
        "attendance_session",
        "marked_by",
    )

    ordering = (
        "-attendance_session__attendance_date",
    )

    actions = (
        "mark_present",
        "mark_absent",
    )

    @admin.action(description="Mark selected students as Present")
    def mark_present(self, request, queryset):
        queryset.update(status="PRESENT")

    @admin.action(description="Mark selected students as Absent")
    def mark_absent(self, request, queryset):
        queryset.update(status="ABSENT")


# ==========================================================
# Teacher Attendance
# ==========================================================

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "teacher",
        "attendance_date",
        "status",
        "time_in",
        "time_out",
    )

    list_filter = (
        "attendance_date",
        "status",
    )

    search_fields = (
        "teacher__first_name",
        "teacher__last_name",
        "teacher__staff_id",
    )

    autocomplete_fields = (
        "teacher",
    )

    ordering = (
        "-attendance_date",
    )

    actions = (
        "mark_present",
        "mark_absent",
    )

    @admin.action(description="Mark selected teachers as Present")
    def mark_present(self, request, queryset):
        queryset.update(status="PRESENT")

    @admin.action(description="Mark selected teachers as Absent")
    def mark_absent(self, request, queryset):
        queryset.update(status="ABSENT")


# ==========================================================
# Attendance Summary
# ==========================================================

@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "session",
        "term",
        "present",
        "absent",
        "late",
        "excused",
        "attendance_percentage",
    )

    list_filter = (
        "session",
        "term",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__admission_number",
    )

    autocomplete_fields = (
        "student",
    )

    ordering = (
        "student",
    )