from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.models import BaseModel
from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    Term,
    SchoolClass,
)


class FeeCategory(BaseModel):
    """Types of fees charged by the school."""

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
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="finance_fee_category_school_name_uniq",
            ),
        ]

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Fee category name cannot be empty."})
        if self.school_id and self.name:
            qs = FeeCategory.objects.filter(school_id=self.school_id, name__iexact=self.name)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"name": "This fee category already exists for this school."})

    def __str__(self):
        return self.name


class FeeStructure(BaseModel):
    """Defines fees payable by a class for a session and term."""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="fee_structures")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "session", "term", "school_class", "fee_category"],
                name="finance_fee_structure_scope_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="finance_fee_structure_amount_gte_0",
            ),
        ]

    def clean(self):
        errors = {}
        if self.session_id and self.school_id and self.session.school_id != self.school_id:
            errors["session"] = "The selected academic session must belong to the same school."
        if self.term_id and self.school_id and self.term.school_id != self.school_id:
            errors["term"] = "The selected term must belong to the same school."
        if self.school_class_id and self.school_id and self.school_class.school_id != self.school_id:
            errors["school_class"] = "The selected class must belong to the same school."
        if self.fee_category_id and self.school_id and self.fee_category.school_id != self.school_id:
            errors["fee_category"] = "The selected fee category must belong to the same school."
        if self.session_id and self.term_id and self.term.session_id != self.session_id:
            errors["term"] = "The selected term must belong to the selected academic session."
        if self.amount is not None and self.amount < 0:
            errors["amount"] = "Fee amount cannot be negative."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.school_class} - {self.fee_category.name}"


class StudentInvoice(BaseModel):
    """One invoice per student per school, session and term."""

    STATUS = (
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=30, unique=True, blank=True)
    due_date = models.DateField(default=date.today)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="UNPAID")
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "student", "session", "term"],
                name="finance_invoice_student_session_term_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="finance_invoice_total_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(balance__gte=0),
                name="finance_invoice_balance_gte_0",
            ),
        ]

    def clean(self):
        errors = {}
        if self.student_id and self.school_id and self.student.school_id != self.school_id:
            errors["student"] = "The student must belong to the same school as the invoice."
        if self.session_id and self.school_id and self.session.school_id != self.school_id:
            errors["session"] = "The academic session must belong to the same school as the invoice."
        if self.term_id and self.school_id and self.term.school_id != self.school_id:
            errors["term"] = "The term must belong to the same school as the invoice."
        if self.session_id and self.term_id and self.term.session_id != self.session_id:
            errors["term"] = "The term must belong to the selected academic session."
        if self.total_amount is not None and self.total_amount < 0:
            errors["total_amount"] = "Invoice total cannot be negative."
        if self.balance is not None and self.balance < 0:
            errors["balance"] = "Invoice balance cannot be negative."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{date.today().year}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(BaseModel):
    """Individual fee items belonging to an invoice."""

    invoice = models.ForeignKey(StudentInvoice, on_delete=models.CASCADE, related_name="items")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    is_optional = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="finance_invoice_item_amount_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(paid_amount__gte=0),
                name="finance_invoice_item_paid_gte_0",
            ),
        ]

    def clean(self):
        errors = {}
        if self.invoice_id and self.fee_category_id:
            if self.invoice.school_id != self.fee_category.school_id:
                errors["fee_category"] = "The fee category must belong to the invoice's school."
        if self.amount is not None and self.amount < 0:
            errors["amount"] = "Invoice item amount cannot be negative."
        if self.paid_amount is not None and self.paid_amount < 0:
            errors["paid_amount"] = "Paid amount cannot be negative."
        if self.paid_amount is not None and self.amount is not None and self.paid_amount > self.amount:
            errors["paid_amount"] = "Paid amount cannot exceed the item amount."
        if errors:
            raise ValidationError(errors)

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.fee_category.name}"


class Payment(BaseModel):
    """Financial settlement against an invoice."""

    SETTLEMENT_TYPES = (
        ("PAYMENT", "Payment"),
        ("SCHOLARSHIP", "Scholarship / Full Waiver"),
        ("WAIVER", "Fee Waiver / Adjustment"),
    )

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
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    settlement_type = models.CharField(
        max_length=20,
        choices=SETTLEMENT_TYPES,
        default="PAYMENT",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        blank=True,
    )
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="finance_payment_amount_gte_0",
            ),
        ]

    def clean(self):
        if self.amount is not None and self.amount < 0:
            raise ValidationError({"amount": "Settlement amount cannot be negative."})

    def save(self, *args, **kwargs):
        old_invoice_id = None
        if self.pk:
            old_invoice_id = Payment.objects.filter(pk=self.pk).values_list("invoice_id", flat=True).first()

        super().save(*args, **kwargs)
        self._recalculate_invoice(self.invoice)

        if old_invoice_id and old_invoice_id != self.invoice_id:
            old_invoice = StudentInvoice.objects.filter(pk=old_invoice_id).first()
            if old_invoice:
                self._recalculate_invoice(old_invoice)

    @staticmethod
    def _recalculate_invoice(invoice):
        total_settled = (
            invoice.payments.aggregate(models.Sum("amount"))["amount__sum"]
            or Decimal("0.00")
        )
        invoice.balance = max(
            invoice.total_amount - total_settled,
            Decimal("0.00"),
        )
        if invoice.balance == Decimal("0.00"):
            invoice.status = "PAID"
        elif total_settled > Decimal("0.00"):
            invoice.status = "PARTIAL"
        else:
            invoice.status = "UNPAID"
        invoice.save(update_fields=["balance", "status"])

    def __str__(self):
        return f"{self.invoice.invoice_number} - ₦{self.amount}"


@receiver(post_delete, sender=Payment)
def recalculate_invoice_after_payment_delete(sender, instance, **kwargs):
    if instance.invoice_id:
        invoice = StudentInvoice.objects.filter(pk=instance.invoice_id).first()
        if invoice:
            Payment._recalculate_invoice(invoice)
