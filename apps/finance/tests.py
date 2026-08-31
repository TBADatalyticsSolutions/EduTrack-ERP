from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.academics.models import AcademicSession, SchoolClass, Term
from apps.schools.models import School
from apps.students.models import Student

from .models import FeeCategory, FeeStructure, InvoiceItem, Payment, StudentInvoice


class FinanceIntegrityTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            email="finance-tests@example.com",
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            is_current=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            session=self.session,
            name="First Term",
            is_current=True,
        )
        self.school_class = SchoolClass.objects.create(
            school=self.school,
            name="JSS 1",
        )
        self.category = FeeCategory.objects.create(
            school=self.school,
            name="Tuition",
        )
        self.student = Student.objects.create(
            school=self.school,
            admission_number="ADM-TEST-001",
            first_name="Test",
            last_name="Student",
            gender="M",
            date_of_birth=date(2013, 1, 1),
            admission_date=date(2026, 9, 1),
            current_class=self.school_class,
            current_session=self.session,
            current_term=self.term,
        )

    def test_fee_structure_requires_matching_school_and_session_term(self):
        structure = FeeStructure(
            school=self.school,
            session=self.session,
            term=self.term,
            school_class=self.school_class,
            fee_category=self.category,
            amount=Decimal("50000.00"),
        )
        structure.full_clean()
        structure.save()

        duplicate = FeeStructure(
            school=self.school,
            session=self.session,
            term=self.term,
            school_class=self.school_class,
            fee_category=self.category,
            amount=Decimal("60000.00"),
        )
        duplicate.full_clean()
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_invoice_scope_is_unique(self):
        invoice = StudentInvoice.objects.create(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            total_amount=Decimal("50000.00"),
            balance=Decimal("50000.00"),
            status="UNPAID",
        )
        self.assertTrue(invoice.invoice_number.startswith("INV-"))

        duplicate = StudentInvoice(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            total_amount=Decimal("50000.00"),
            balance=Decimal("50000.00"),
            status="UNPAID",
        )
        duplicate.full_clean()
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_payment_updates_invoice_and_delete_recalculates_balance(self):
        invoice = StudentInvoice.objects.create(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            total_amount=Decimal("50000.00"),
            balance=Decimal("50000.00"),
            status="UNPAID",
        )

        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal("20000.00"),
            settlement_type="PAYMENT",
            payment_method="TRANSFER",
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.balance, Decimal("30000.00"))
        self.assertEqual(invoice.status, "PARTIAL")

        payment.delete()
        invoice.refresh_from_db()
        self.assertEqual(invoice.balance, Decimal("50000.00"))
        self.assertEqual(invoice.status, "UNPAID")

    def test_negative_payment_is_rejected(self):
        invoice = StudentInvoice.objects.create(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            total_amount=Decimal("50000.00"),
            balance=Decimal("50000.00"),
            status="UNPAID",
        )
        payment = Payment(
            invoice=invoice,
            amount=Decimal("-1.00"),
            settlement_type="PAYMENT",
            payment_method="CASH",
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_invoice_item_cannot_use_another_school_fee_category(self):
        other_school = School.objects.create(
            name="Other School",
            email="other-finance-tests@example.com",
        )
        other_category = FeeCategory.objects.create(
            school=other_school,
            name="Tuition",
        )
        invoice = StudentInvoice.objects.create(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            total_amount=Decimal("50000.00"),
            balance=Decimal("50000.00"),
            status="UNPAID",
        )
        item = InvoiceItem(
            invoice=invoice,
            fee_category=other_category,
            description="Invalid cross-school item",
            amount=Decimal("50000.00"),
        )
        with self.assertRaises(ValidationError):
            item.full_clean()
