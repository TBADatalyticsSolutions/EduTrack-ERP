from django.db import models

from apps.core.models import BaseModel
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    Term,
    SchoolClass,
    Subject,
)
from apps.schools.models import School


class AssessmentType(BaseModel):
    """
    Assessment components.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="assessment_types",
    )

    name = models.CharField(
        max_length=50,
    )

    maximum_score = models.PositiveIntegerField(
        default=20,
    )

    order = models.PositiveIntegerField(
        default=1,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class GradeSetting(BaseModel):
    """
    School grading settings.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    grade = models.CharField(
        max_length=5,
    )

    minimum_score = models.PositiveIntegerField()

    maximum_score = models.PositiveIntegerField()

    remark = models.CharField(
        max_length=100,
    )

    class Meta:
        ordering = ["-minimum_score"]

    def __str__(self):
        return (
            f"{self.grade} "
            f"({self.minimum_score}-{self.maximum_score})"
        )


class StudentResult(BaseModel):
    """
    Overall student result.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="results",
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

    total_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
    )

    average = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    position = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    published = models.BooleanField(
        default=False,
    )

    class Meta:
        unique_together = (
            "student",
            "session",
            "term",
        )

    def __str__(self):
        return str(self.student)

    @property
    def position_display(self):
        """
        Display 1st, 2nd, 3rd...
        """

        if self.position is None:
            return "-"

        if 10 <= self.position % 100 <= 20:
            suffix = "th"
        else:
            suffix = {
                1: "st",
                2: "nd",
                3: "rd",
            }.get(self.position % 10, "th")

        return f"{self.position}{suffix}"


class SubjectResult(BaseModel):
    """
    Individual subject result.
    """

    student_result = models.ForeignKey(
        StudentResult,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    ca1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    ca2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    assignment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    project = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    examination = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    grade = models.CharField(
        max_length=5,
        blank=True,
    )

    remark = models.CharField(
        max_length=100,
        blank=True,
    )

    teacher_remark = models.TextField(
        blank=True,
    )

    class Meta:
        unique_together = (
            "student_result",
            "subject",
        )

    def __str__(self):
        return (
            f"{self.student_result.student} - {self.subject}"
        )