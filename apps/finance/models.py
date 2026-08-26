from decimal import Decimal
from datetime import date

from django.db import models

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    Term,
    SchoolClass,
)


class FeeCategory(BaseModel):
    """
    Types of fees charged by the school.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fee_categories",
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name


class FeeStructure(BaseModel):
    """
    Defines fees payable by a class for a session and term.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fee_structures",
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

    fee_category = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        unique_together = (
            "school",
            "session",
            "term",
            "school_class",
            "fee_category",
        )

    def __str__(self):
        return (
            f"{self.school_class} - "
            f"{self.fee_category.name}"
        )


class StudentInvoice(BaseModel):
    """
    One invoice per student per term.
    """

    STATUS = (
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="invoices",
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
    )

    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
    )

    due_date = models.DateField(
        default=date.today,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="UNPAID",
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.invoice_number:
            self.invoice_number = (
                f"INV-{date.today().year}-{str(self.id)[:8].upper()}"
            )

            super().save(update_fields=["invoice_number"])

    def __str__(self):
        return self.invoice_number


class InvoiceItem(BaseModel):
    """
    Individual fee items belonging to an invoice.
    """

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    fee_category = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    is_optional = models.BooleanField(
        default=False,
    )

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def __str__(self):
        return (
            f"{self.invoice.invoice_number} - "
            f"{self.fee_category.name}"
        )


class Payment(BaseModel):
    """
    Payments made toward an invoice.
    """

    PAYMENT_METHODS = (
        ("CASH", "Cash"),
        ("TRANSFER", "Bank Transfer"),
        ("POS", "POS"),
        ("ONLINE", "Online"),
    )

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    payment_date = models.DateField(
        auto_now_add=True,
    )

    notes = models.TextField(
        blank=True,
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        invoice = self.invoice

        total_paid = (
            invoice.payments.aggregate(
                models.Sum("amount")
            )["amount__sum"]
            or Decimal("0.00")
        )

        invoice.balance = invoice.total_amount - total_paid

        if invoice.balance <= Decimal("0.00"):
            invoice.status = "PAID"

        elif total_paid > Decimal("0.00"):
            invoice.status = "PARTIAL"

        else:
            invoice.status = "UNPAID"

        invoice.save(
            update_fields=[
                "balance",
                "status",
            ]
        )

    def __str__(self):
        return (
            f"{self.invoice.invoice_number} "
            f"- ₦{self.amount}"
        )
