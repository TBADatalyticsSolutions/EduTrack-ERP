from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)


# ============================================================
# ATTENDANCE SESSION
# ============================================================

class AttendanceSession(BaseModel):
    """
    Represents one daily attendance session for a class.

    One class can have only one attendance session per:
        School + Academic Session + Term + Date
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )

    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )

    attendance_date = models.DateField(
        default=timezone.localdate,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_attendance_sessions",
    )

    class Meta:
        ordering = [
            "-attendance_date",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_session",
                    "term",
                    "school_class",
                    "attendance_date",
                ],
                name="unique_class_attendance_per_day",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "academic_session",
                    "term",
                ]
            ),
            models.Index(
                fields=[
                    "school_class",
                    "attendance_date",
                ]
            ),
            models.Index(
                fields=[
                    "attendance_date",
                ]
            ),
        ]

    def clean(self):
        errors = {}

        # ----------------------------------------------------
        # SCHOOL ↔ CLASS
        # ----------------------------------------------------

        if (
            self.school_id
            and self.school_class_id
            and self.school_class.school_id != self.school_id
        ):
            errors["school_class"] = (
                "The selected class does not belong "
                "to the selected school."
            )

        # ----------------------------------------------------
        # SCHOOL ↔ ACADEMIC SESSION
        # ----------------------------------------------------

        if (
            self.school_id
            and self.academic_session_id
            and self.academic_session.school_id != self.school_id
        ):
            errors["academic_session"] = (
                "The selected academic session does not "
                "belong to the selected school."
            )

        # ----------------------------------------------------
        # SCHOOL ↔ TERM
        # ----------------------------------------------------

        if (
            self.school_id
            and self.term_id
            and self.term.school_id != self.school_id
        ):
            errors["term"] = (
                "The selected term does not belong "
                "to the selected school."
            )

        # ----------------------------------------------------
        # TERM ↔ ACADEMIC SESSION
        # ----------------------------------------------------

        if (
            self.academic_session_id
            and self.term_id
            and hasattr(self.term, "academic_session_id")
            and self.term.academic_session_id
            != self.academic_session_id
        ):
            errors["term"] = (
                "The selected term does not belong "
                "to the selected academic session."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.school_class} | "
            f"{self.attendance_date} | "
            f"{self.term}"
        )


# ============================================================
# ATTENDANCE RECORD
# ============================================================

class AttendanceRecord(BaseModel):
    """
    Attendance status for one student in one attendance session.
    """

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

    STATUS_CHOICES = (
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (LATE, "Late"),
        (EXCUSED, "Excused"),
    )

    attendance_session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PRESENT,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendance_records",
    )

    marked_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "student__last_name",
            "student__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "attendance_session",
                    "student",
                ],
                name="unique_student_attendance_per_session",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "student",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "attendance_session",
                    "status",
                ]
            ),
        ]

    def clean(self):
        errors = {}

        if not self.student_id or not self.attendance_session_id:
            return

        session = self.attendance_session
        student = self.student

        # ----------------------------------------------------
        # STUDENT ↔ SCHOOL
        # ----------------------------------------------------

        if student.school_id != session.school_id:
            errors["student"] = (
                "This student does not belong to "
                "the attendance session's school."
            )

        # ----------------------------------------------------
        # STUDENT ↔ CLASS
        # ----------------------------------------------------

        if (
            student.current_class_id
            and student.current_class_id
            != session.school_class_id
        ):
            errors["student"] = (
                "This student does not belong to "
                "the class selected for this attendance session."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.get_status_display()} - "
            f"{self.attendance_session.attendance_date}"
        )
