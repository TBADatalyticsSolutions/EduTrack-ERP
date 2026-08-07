from django.conf import settings
from apps.accounts.utils import log_activity
from django.db import models
from apps.accounts.utils import log_activity

from apps.core.models import BaseModel
from apps.accounts.utils import log_activity
from apps.schools.models import School
from apps.accounts.utils import log_activity
from apps.students.models import Student
from apps.accounts.utils import log_activity
from apps.teachers.models import Teacher
from apps.accounts.utils import log_activity
from apps.academics.models import (
from apps.accounts.utils import log_activity
    AcademicSession,
    Term,
    SchoolClass,
)


class AttendanceSession(BaseModel):
    """
    Represents one attendance day for a class.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    attendance_date = models.DateField()

    class Meta:
        ordering = ["-attendance_date"]

        unique_together = (
            "school",
            "school_class",
            "attendance_date",
        )

    def __str__(self):
        return (
            f"{self.school_class}"
            f" - {self.attendance_date}"
        )


class StudentAttendance(BaseModel):

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

    STATUS = (
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (LATE, "Late"),
        (EXCUSED, "Excused"),
    )

    attendance_session = models.ForeignKey(
        AttendanceSession,
        related_name="students",
        on_delete=models.CASCADE,
    )

    student = models.ForeignKey(
        Student,
        related_name="attendance_records",
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default=PRESENT,
    )

    time_in = models.TimeField(
        null=True,
        blank=True,
    )

    time_out = models.TimeField(
        null=True,
        blank=True,
    )

    remark = models.CharField(
        max_length=200,
        blank=True,
    )

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["student"]

        unique_together = (
            "attendance_session",
            "student",
        )

    def __str__(self):
        return (
            f"{self.student}"
            f" - {self.status}"
        )


class TeacherAttendance(BaseModel):

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

    STATUS = (
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (LATE, "Late"),
        (EXCUSED, "Excused"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    teacher = models.ForeignKey(
        Teacher,
        related_name="attendance_records",
        on_delete=models.CASCADE,
    )

    attendance_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default=PRESENT,
    )

    time_in = models.TimeField(
        null=True,
        blank=True,
    )

    time_out = models.TimeField(
        null=True,
        blank=True,
    )

    remark = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ["-attendance_date"]

        unique_together = (
            "teacher",
            "attendance_date",
        )

    def __str__(self):
        return (
            f"{self.teacher}"
            f" - {self.attendance_date}"
        )


class AttendanceSummary(BaseModel):
    """
    Cached monthly attendance summary.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_summary",
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
    )

    present = models.PositiveIntegerField(
        default=0,
    )

    absent = models.PositiveIntegerField(
        default=0,
    )

    late = models.PositiveIntegerField(
        default=0,
    )

    excused = models.PositiveIntegerField(
        default=0,
    )

    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    class Meta:
        ordering = ["student"]

    def __str__(self):
        return str(self.student)