from django.db import models

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.academics.models import Subject, SchoolClass


class Department(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="departments",
    )

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.name


class Teacher(BaseModel):
    GENDER = (
        ("M", "Male"),
        ("F", "Female"),
    )

    EMPLOYMENT_STATUS = (
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("CONTRACT", "Contract"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teachers",
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    other_name = models.CharField(
        max_length=100,
        blank=True,
    )

    gender = models.CharField(
        max_length=1,
        choices=GENDER,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    qualification = models.CharField(
        max_length=200,
        blank=True,
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default="FULL_TIME",
    )

    passport = models.ImageField(
        upload_to="teachers/",
        blank=True,
        null=True,
    )

    date_employed = models.DateField(
        null=True,
        blank=True,
    )

    is_class_teacher = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"


class TeacherSubject(BaseModel):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = (
            "teacher",
            "subject",
            "school_class",
        )

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.subject} ({self.school_class})"
        )
