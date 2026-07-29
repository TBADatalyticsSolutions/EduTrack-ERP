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
        ("SUSPENDED", "Suspended"),
        ("EXPELLED", "Expelled"),
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
    # ===========================================
    # DISCIPLINE
    # =========================================
    suspension_start = models.DateField(
    null=True,
    blank=True,
    )
    suspension_end = models.DateField(
    null=True,
    blank=True,
    )
    discipline_reason = models.CharField(
    max_length=200,
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

    # UPDATED: renamed from approved_by
    transferred_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="student_transfers",
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
            f"{self.student} | "
            f"{self.from_class} → {self.to_class}"
        )
# ===========================================================
# WITHDRAWAL HISTORY
# ===========================================================

class WithdrawalHistory(BaseModel):
    """
    Stores student withdrawal records for audit purposes.
    """

    WITHDRAWAL_REASONS = (
        ("TRANSFER", "Transferred to Another School"),
        ("FINANCIAL", "Financial Reasons"),
        ("ILLNESS", "Illness"),
        ("DISCIPLINE", "Disciplinary Action"),
        ("GRADUATED", "Graduated"),
        ("DECEASED", "Deceased"),
        ("PARENT_REQUEST", "Parent Request"),
        ("VOLUNTARY", "Voluntary Withdrawal"),
        ("OTHER", "Other"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="withdrawal_history",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="withdrawal_history",
    )

    from_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="withdrawals_from",
    )

    from_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="withdrawals_from_session",
    )

    reason = models.CharField(
        max_length=30,
        choices=WITHDRAWAL_REASONS,
        default="OTHER",
    )

    remarks = models.TextField(
        blank=True,
    )

    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_withdrawals",
    )

    withdrawal_date = models.DateTimeField(
        auto_now_add=True,
    )

    reinstated = models.BooleanField(
        default=False,
    )

    reinstated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_reinstatements",
    )

    reinstated_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-withdrawal_date",
        ]
        verbose_name = "Withdrawal History"
        verbose_name_plural = "Withdrawal History"

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.get_reason_display()}"
        )
# ===========================================================
# DISCIPLINE HISTORY
# ===========================================================

class DisciplineHistory(BaseModel):
    """
    Stores student suspension and expulsion records.
    """

    ACTIONS = (
        ("SUSPENSION", "Suspension"),
        ("EXPULSION", "Expulsion"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="discipline_history",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="discipline_history",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
    )

    from_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    from_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    start_date = models.DateField(
        default=timezone.now,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    reason = models.CharField(
        max_length=200,
    )

    remarks = models.TextField(
        blank=True,
    )

    disciplined_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_discipline",
    )

    revoked = models.BooleanField(
        default=False,
    )

    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discipline_revocations",
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-start_date",
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.get_action_display()}"
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