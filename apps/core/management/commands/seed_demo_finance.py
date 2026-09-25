from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.finance.models import FeeCategory, FeeStructure, InvoiceItem, Payment, StudentInvoice
from apps.schools.models import School
from apps.students.models import Student


DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

FEE_SPECS = (
    ("Tuition", "Core tuition fee."),
    ("Development Levy", "School development contribution."),
    ("ICT/Technology", "Technology and digital learning fee."),
    ("Activities", "Academic and extracurricular activities."),
    ("Examination", "Assessment and examination fee."),
)

TUITION_BY_CLASS = {
    "Nursery 1": Decimal("13000.00"),
    "Nursery 2": Decimal("16000.00"),
    "Primary 1": Decimal("16000.00"),
    "Primary 2": Decimal("16000.00"),
    "Primary 3": Decimal("21000.00"),
    "Primary 4": Decimal("21000.00"),
    "Primary 5": Decimal("21000.00"),
    "Primary 6": Decimal("21000.00"),
    "JSS 1": Decimal("27000.00"),
    "JSS 2": Decimal("27000.00"),
    "JSS 3": Decimal("27000.00"),
    "SS 1": Decimal("32000.00"),
    "SS 2": Decimal("32000.00"),
    "SS 3": Decimal("32000.00"),
}

NON_TUITION_AMOUNTS = {
    "Development Levy": Decimal("5000.00"),
    "ICT/Technology": Decimal("3000.00"),
    "Activities": Decimal("5000.00"),
    "Examination": Decimal("2500.00"),
}


class Command(BaseCommand):
    help = (
        "Seed the Stage 6 demo finance layer: fee categories, fee structures, "
        "student invoices, invoice items, payments, scholarships, and waivers."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES,
        ).order_by("short_name")

        if schools.count() != len(DEMO_SCHOOL_CODES):
            raise RuntimeError(
                "Run seed_demo_schools first. Expected all 10 demo schools."
            )

        created_categories = 0
        created_structures = 0
        created_invoices = 0
        created_items = 0
        created_payments = 0

        for school in schools:
            session = school.sessions.filter(
                name="2026/2027",
            ).first()
            term = (
                school.terms.filter(
                    session=session,
                    name="First Term",
                ).first()
                if session
                else None
            )

            if session is None or term is None:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_academics first."
                )

            classes = list(
                school.classes.order_by("name")
            )
            if len(classes) != 14:
                raise RuntimeError(
                    f"{school.short_name}: expected 14 school classes. "
                    "Run seed_demo_academics first."
                )

            categories = {}
            for name, description in FEE_SPECS:
                category, created = FeeCategory.objects.get_or_create(
                    school=school,
                    name=name,
                    defaults={"description": description},
                )
                if created:
                    created_categories += 1
                if category.description != description:
                    category.description = description
                    category.save(update_fields=["description"])
                categories[name] = category

            for school_class in classes:
                for category_name, _ in FEE_SPECS:
                    amount = (
                        TUITION_BY_CLASS[school_class.name]
                        if category_name == "Tuition"
                        else NON_TUITION_AMOUNTS[category_name]
                    )
                    structure, created = FeeStructure.objects.get_or_create(
                        school=school,
                        session=session,
                        term=term,
                        school_class=school_class,
                        fee_category=categories[category_name],
                        defaults={"amount": amount},
                    )
                    if created:
                        created_structures += 1
                    elif structure.amount != amount:
                        structure.amount = amount
                        structure.save(update_fields=["amount"])

            students = list(
                school.students.filter(
                    status="ACTIVE",
                    current_session=session,
                    current_term=term,
                ).select_related("current_class").order_by("admission_number")
            )

            for student_index, student in enumerate(students):
                if student.current_class_id is None:
                    raise RuntimeError(
                        f"{student.admission_number}: current class is required."
                    )

                invoice_number = (
                    f"INV-{school.short_name}-2627T1-{student_index + 1:04d}"
                )
                invoice, created = StudentInvoice.objects.get_or_create(
                    school=school,
                    student=student,
                    session=session,
                    term=term,
                    defaults={
                        "invoice_number": invoice_number,
                        "due_date": term.resumption_date,
                        "remarks": "Synthetic Stage 6 demo invoice.",
                    },
                )
                if created:
                    created_invoices += 1

                if invoice.invoice_number != invoice_number:
                    raise RuntimeError(
                        f"{student.admission_number}: unexpected invoice number "
                        f"{invoice.invoice_number}."
                    )

                structures = FeeStructure.objects.filter(
                    school=school,
                    session=session,
                    term=term,
                    school_class=student.current_class,
                ).select_related("fee_category").order_by(
                    "fee_category__name"
                )

                total = Decimal("0.00")
                for structure in structures:
                    item, item_created = InvoiceItem.objects.get_or_create(
                        invoice=invoice,
                        fee_category=structure.fee_category,
                        defaults={
                            "description": structure.fee_category.name,
                            "amount": structure.amount,
                            "due_date": term.resumption_date,
                        },
                    )
                    if item_created:
                        created_items += 1

                    changed = []
                    if item.description != structure.fee_category.name:
                        item.description = structure.fee_category.name
                        changed.append("description")
                    if item.amount != structure.amount:
                        item.amount = structure.amount
                        changed.append("amount")
                    if item.due_date != term.resumption_date:
                        item.due_date = term.resumption_date
                        changed.append("due_date")
                    if item.paid_amount > item.amount:
                        raise RuntimeError(
                            f"{invoice_number}: existing item payment exceeds "
                            "the current item amount."
                        )
                    if changed:
                        item.save(update_fields=changed)
                    total += structure.amount

                invoice.due_date = term.resumption_date
                invoice.total_amount = total
                invoice.remarks = "Synthetic Stage 6 demo invoice."
                invoice.save(
                    update_fields=["due_date", "total_amount", "remarks"]
                )

                settlement_type = None
                settlement_amount = Decimal("0.00")
                payment_method = ""
                if student_index % 6 == 0:
                    settlement_type = "PAYMENT"
                    settlement_amount = min(total, Decimal("10000.00"))
                    payment_method = "TRANSFER"
                elif student_index % 6 == 1:
                    settlement_type = "SCHOLARSHIP"
                    settlement_amount = min(total, Decimal("15000.00"))
                elif student_index % 6 == 2:
                    settlement_type = "WAIVER"
                    settlement_amount = min(total, Decimal("5000.00"))
                elif student_index % 6 == 3:
                    settlement_type = "PAYMENT"
                    settlement_amount = total
                    payment_method = "POS"
                elif student_index % 6 == 4:
                    settlement_type = "SCHOLARSHIP"
                    settlement_amount = min(total, Decimal("5000.00"))

                if settlement_type and settlement_amount > Decimal("0.00"):
                    reference = (
                        f"DEMO-{settlement_type[:3]}-"
                        f"{school.short_name}-{student_index + 1:04d}"
                    )
                    payment, payment_created = Payment.objects.get_or_create(
                        invoice=invoice,
                        reference=reference,
                        defaults={
                            "amount": settlement_amount,
                            "settlement_type": settlement_type,
                            "payment_method": payment_method,
                            "notes": "Synthetic Stage 6 demo settlement.",
                        },
                    )
                    if payment_created:
                        created_payments += 1
                    elif (
                        payment.amount != settlement_amount
                        or payment.settlement_type != settlement_type
                        or payment.payment_method != payment_method
                    ):
                        payment.amount = settlement_amount
                        payment.settlement_type = settlement_type
                        payment.payment_method = payment_method
                        payment.notes = "Synthetic Stage 6 demo settlement."
                        payment.save(
                            update_fields=[
                                "amount",
                                "settlement_type",
                                "payment_method",
                                "notes",
                            ]
                        )

                Payment._recalculate_invoice(invoice)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo finance stage complete: {schools.count()} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{created_categories} fee categories, "
            f"{created_structures} fee structures, "
            f"{created_invoices} invoices, "
            f"{created_items} invoice items, "
            f"{created_payments} settlements."
        )
        self.stdout.write(
            "Totals: "
            f"{FeeCategory.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} fee categories | "
            f"{FeeStructure.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} fee structures | "
            f"{StudentInvoice.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} invoices | "
            f"{InvoiceItem.objects.filter(invoice__school__short_name__in=DEMO_SCHOOL_CODES).count()} invoice items | "
            f"{Payment.objects.filter(invoice__school__short_name__in=DEMO_SCHOOL_CODES).count()} settlements"
        )
