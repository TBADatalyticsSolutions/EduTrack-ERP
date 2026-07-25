from django.db import models

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.academics.models import SchoolClass


class Student(BaseModel):
    GENDER = (
        ("M", "Male"),
        ("F", "Female"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="students",
    )

    admission_number = models.CharField(
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

    date_of_birth = models.DateField()

    current_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    passport = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True,
    )

    is_graduated = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"


class Parent(BaseModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
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

    students = models.ManyToManyField(
        Student,
        related_name="parents",
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"