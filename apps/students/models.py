from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.academics.models import (
    SchoolClass,
    AcademicSession,
)


# ===========================================================
# STUDENT
# ===========================================================

class Student(BaseModel):

    GENDER = (
        ("M", "Male"),
        ("F", "Female"),
    )

    STATUS = (
        ("ACTIVE", "Active"),
        ("GRADUATED", "Graduated"),
        ("WITHDRAWN", "Withdrawn"),
        ("TRANSFERRED", "Transferred"),
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

    admission_date = models.DateField(
        default=timezone.now,
    )

    current_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    current_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    passport = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="ACTIVE",
    )

    is_graduated = models.BooleanField(
        default=False,
    )

    graduation_date = models.DateField(
        null=True,
        blank=True,
    )

    graduation_session = models.CharField(
        max_length=20,
        blank=True,
    )

    graduation_reason = models.CharField(
        max_length=150,
        blank=True,
    )

    graduation_remark = models.CharField(
        max_length=255,
        blank=True,
    )

    def full_name(self):
        return (
            f"{self.first_name} "
            f"{self.other_name} "
            f"{self.last_name}"
        ).replace("  ", " ").strip()

    def __str__(self):
        return f"{self.admission_number} - {self.full_name()}"


# ===========================================================
# PARENT
# ===========================================================

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


# ===========================================================
# TRANSFER HISTORY
# ===========================================================

class TransferHistory(BaseModel):
    """
    Stores every student transfer for audit purposes.
    """

    student = models.ForeignKey(
    Student,
    on_delete=models.CASCADE,
    related_name="transfer_history",
)

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="transfer_history",
    )

    from_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transferred_from",
    )

    to_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transferred_to",
    )

    from_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfer_from_session",
    )

    to_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfer_to_session",
    )

    transfer_date = models.DateField(
        auto_now_add=True,
    )

    reason = models.CharField(
        max_length=200,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    rolled_back = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = [
            "-transfer_date",
        ]

    def __str__(self):
        return (
            f"{self.student} "
            f"{self.from_class} → "
            f"{self.to_class}"
        )
# ===========================================================
# PROMOTION HISTORY
# ===========================================================

class PromotionHistory(BaseModel):

    ACTIONS = (
        ("PROMOTED", "Promoted"),
        ("REPEATED", "Repeated"),
        ("GRADUATED", "Graduated"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="promotion_history",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="promotion_history",
    )

    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
    )

    from_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="promoted_from",
    )

    to_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_to",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
        default="PROMOTED",
    )

    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    approved_at = models.DateTimeField(
        auto_now_add=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-approved_at",
        ]

    def __str__(self):
        return f"{self.student} - {self.action}"


# ===========================================================
# GRADUATION HISTORY
# ===========================================================

class GraduationHistory(BaseModel):
    """
    Stores graduation records for audit purposes.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="graduation_records",
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    graduated_from = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    academic_session = models.CharField(
        max_length=20,
    )

    graduation_date = models.DateField(
        auto_now_add=True,
    )

    graduated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    rolled_back = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = [
            "-graduation_date",
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.academic_session}"
        )