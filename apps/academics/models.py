from django.db import models

from apps.core.models import BaseModel
from apps.schools.models import School


# ===========================================================
# ACADEMIC SESSION
# ===========================================================

class AcademicSession(BaseModel):
    """
    Represents an academic session for a school.

    Example:
        2025/2026
        2026/2027
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    name = models.CharField(
        max_length=20,
    )

    is_current = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.name


# ===========================================================
# TERM
# ===========================================================

class Term(BaseModel):
    """
    Represents an academic term within an academic session.
    """

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

    name = models.CharField(
        max_length=20,
    )

    is_current = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.name


# ===========================================================
# SCHOOL CLASS
# ===========================================================

class SchoolClass(BaseModel):
    """
    Represents a class in the school.

    Examples:
        Nursery 1
        Primary 1
        JSS 1
        SS 1
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    name = models.CharField(
        max_length=50,
    )

    def __str__(self):
        return self.name


# ===========================================================
# CLASS ARM
# ===========================================================

class ClassArm(BaseModel):
    """
    Represents an arm of a school class.

    Examples:
        JSS 1 A
        JSS 1 B
        SS 2 Science
    """

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

    name = models.CharField(
        max_length=20,
    )

    def __str__(self):
        return (
            f"{self.school_class.name} "
            f"{self.name}"
        )


# ===========================================================
# SUBJECT
# ===========================================================

class Subject(BaseModel):
    """
    Represents a school subject.
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


# ===========================================================
# CLASS SUBJECT
# ===========================================================

class ClassSubject(BaseModel):
    """
    Assigns subjects to school classes.
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
        unique_together = (
            "school_class",
            "subject",
        )

    def __str__(self):
        return (
            f"{self.school_class} - "
            f"{self.subject}"
        )