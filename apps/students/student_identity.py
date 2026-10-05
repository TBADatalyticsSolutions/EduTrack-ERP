from django.db import models

from apps.core.models import BaseModel

from .models import Student


class StudentIdentity(BaseModel):
    """Additional statutory/student identity data kept separate from admission numbering."""

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="identity",
    )
    lin = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Learner Identification Number (LIN).",
    )

    class Meta:
        verbose_name = "Student Identity"
        verbose_name_plural = "Student Identities"

    def __str__(self):
        return f"{self.student.full_name()} - {self.lin}"
