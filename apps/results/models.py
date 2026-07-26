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
    Defines the assessment components.
    Example:
        CA1
        CA2
        Assignment
        Project
        Examination
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
    School grading system.
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
        return f"{self.grade} ({self.minimum_score}-{self.maximum_score})"


class StudentResult(BaseModel):
    """
    Header record for one student's result.
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
        max_digits=6,
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


class SubjectResult(BaseModel):
    """
    One subject score.
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
        return f"{self.student_result.student} - {self.subject}"