from django.db import models
from apps.accounts.utils import log_activity

from apps.core.models import BaseModel
from apps.accounts.utils import log_activity
from apps.schools.models import School
from apps.accounts.utils import log_activity


class AcademicSession(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    name = models.CharField(max_length=20)

    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Term(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="terms",
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="terms",
    )

    name = models.CharField(max_length=20)

    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class SchoolClass(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ClassArm(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="arms",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="arms",
    )

    name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.school_class.name} {self.name}"


class Subject(BaseModel):
    """
    School subjects.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    name = models.CharField(
        max_length=100,
    )

    code = models.CharField(
        max_length=20,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_core = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.name


class ClassSubject(BaseModel):
    """
    Assign subjects to classes.
    """

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    class Meta:
        unique_together = ("school_class", "subject")

    def __str__(self):
        return f"{self.school_class} - {self.subject}"
