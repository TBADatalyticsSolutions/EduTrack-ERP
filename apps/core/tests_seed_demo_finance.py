from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from apps.finance.models import FeeCategory, FeeStructure, InvoiceItem, Payment, StudentInvoice
from apps.schools.models import School
from apps.students.models import Student


class SeedDemoFinanceCommandTests(TestCase):
    def setUp(self):
        call_command("seed_roles")
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")
        call_command("seed_demo_subjects_teaching")
        call_command("seed_demo_academic_config")
        call_command("seed_demo_students_portal")

    def test_complete_finance_configuration(self):
        call_command("seed_demo_finance")

        self.assertEqual(FeeCategory.objects.count(), 50)
        self.assertEqual(FeeStructure.objects.count(), 700)
        self.assertEqual(StudentInvoice.objects.count(), 120)
        self.assertEqual(InvoiceItem.objects.count(), 600)
        self.assertEqual(Payment.objects.count(), 100)

        self.assertEqual(
            StudentInvoice.objects.filter(status="PAID").count(),
            20,
        )
        self.assertEqual(
            StudentInvoice.objects.filter(status="PARTIAL").count(),
            60,
        )
        self.assertEqual(
            StudentInvoice.objects.filter(status="UNPAID").count(),
            40,
        )

        for invoice in StudentInvoice.objects.all():
            self.assertEqual(
                invoice.total_amount,
                sum(invoice.items.values_list("amount", flat=True)),
            )
            self.assertGreaterEqual(invoice.balance, Decimal("0.00"))
            self.assertLessEqual(invoice.balance, invoice.total_amount)

    def test_finance_is_tenant_scoped(self):
        call_command("seed_demo_finance")

        for structure in FeeStructure.objects.select_related(
            "school", "session__school", "term__school",
            "school_class__school", "fee_category__school",
        ):
            self.assertEqual(structure.school_id, structure.session.school_id)
            self.assertEqual(structure.school_id, structure.term.school_id)
            self.assertEqual(
                structure.school_id,
                structure.school_class.school_id,
            )
            self.assertEqual(
                structure.school_id,
                structure.fee_category.school_id,
            )

        for invoice in StudentInvoice.objects.select_related(
            "school", "student", "session", "term"
        ):
            self.assertEqual(invoice.school_id, invoice.student.school_id)
            self.assertEqual(invoice.school_id, invoice.session.school_id)
            self.assertEqual(invoice.school_id, invoice.term.school_id)

        for item in InvoiceItem.objects.select_related(
            "invoice__school", "fee_category__school"
        ):
            self.assertEqual(
                item.invoice.school_id,
                item.fee_category.school_id,
            )

    def test_settlement_types_are_present(self):
        call_command("seed_demo_finance")

        self.assertGreater(
            Payment.objects.filter(settlement_type="PAYMENT").count(),
            0,
        )
        self.assertGreater(
            Payment.objects.filter(settlement_type="SCHOLARSHIP").count(),
            0,
        )
        self.assertGreater(
            Payment.objects.filter(settlement_type="WAIVER").count(),
            0,
        )

    def test_invoice_balance_and_status_reconcile(self):
        call_command("seed_demo_finance")

        for invoice in StudentInvoice.objects.all():
            settled = sum(
                invoice.payments.values_list("amount", flat=True),
                Decimal("0.00"),
            )
            expected_balance = max(
                invoice.total_amount - settled,
                Decimal("0.00"),
            )
            expected_status = (
                "PAID"
                if expected_balance == Decimal("0.00")
                else "PARTIAL"
                if settled > Decimal("0.00")
                else "UNPAID"
            )
            self.assertEqual(invoice.balance, expected_balance)
            self.assertEqual(invoice.status, expected_status)

    def test_idempotent(self):
        call_command("seed_demo_finance")
        call_command("seed_demo_finance")

        self.assertEqual(FeeCategory.objects.count(), 50)
        self.assertEqual(FeeStructure.objects.count(), 700)
        self.assertEqual(StudentInvoice.objects.count(), 120)
        self.assertEqual(InvoiceItem.objects.count(), 600)
        self.assertEqual(Payment.objects.count(), 100)

    def test_no_results_or_attendance_are_created(self):
        call_command("seed_demo_finance")

        from apps.attendance.models import AttendanceSession
        from apps.notifications.models import Notification
        from apps.results.models import StudentResult

        self.assertEqual(StudentResult.objects.count(), 0)
        self.assertEqual(AttendanceSession.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_deterministic_afaaB_invoice(self):
        call_command("seed_demo_finance")

        student = Student.objects.get(admission_number="AFAAB/2026/0001")
        invoice = StudentInvoice.objects.get(student=student)
        self.assertEqual(invoice.invoice_number, "INV-AFAAB-2627T1-0001")
        self.assertEqual(invoice.total_amount, Decimal("36500.00"))
        self.assertEqual(invoice.balance, Decimal("26500.00"))
        self.assertEqual(invoice.status, "PARTIAL")
        self.assertEqual(
            invoice.items.get(fee_category__name="Tuition").amount,
            Decimal("13000.00"),
        )
