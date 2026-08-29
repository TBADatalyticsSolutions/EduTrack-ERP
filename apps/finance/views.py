from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import FeeCategoryForm, FeeStructureForm, StudentInvoiceForm, PaymentForm
from .models import FeeCategory, FeeStructure, StudentInvoice, InvoiceItem, Payment

ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)


@login_required
@role_required(*ROLES)
def dashboard(request):
    school = _school(request)
    if not school:
        return render(request, "finance/dashboard.html", {"school": None})
    invoices = StudentInvoice.objects.filter(school=school)
    payments = Payment.objects.filter(invoice__school=school)
    context = {
        "school": school,
        "invoice_count": invoices.count(),
        "unpaid": invoices.filter(status="UNPAID").count(),
        "partial": invoices.filter(status="PARTIAL").count(),
        "paid": invoices.filter(status="PAID").count(),
        "total_billed": invoices.aggregate(v=Sum("total_amount"))["v"] or Decimal("0"),
        "total_balance": invoices.aggregate(v=Sum("balance"))["v"] or Decimal("0"),
        "total_paid": payments.filter(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or Decimal("0"),
        "total_relief": payments.exclude(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or Decimal("0"),
    }
    return render(request, "finance/dashboard.html", context)


@login_required
@role_required(*ROLES)
def fee_categories(request):
    school = _school(request)
    categories = FeeCategory.objects.filter(school=school) if school else FeeCategory.objects.none()
    if request.method == "POST":
        form = FeeCategoryForm(request.POST)
        if form.is_valid() and school:
            obj = form.save(commit=False)
            obj.school = school
            obj.save()
            log_activity(request, "CREATE", "Finance", f"Created fee category: {obj.name}")
            messages.success(request, "Fee category created successfully.")
            return redirect("finance:fee-categories")
    else:
        form = FeeCategoryForm()
    return render(request, "finance/fee_categories.html", {"form": form, "categories": categories})


@login_required
@role_required(*ROLES)
def fee_structures(request):
    school = _school(request)
    structures = (
        FeeStructure.objects.filter(school=school)
        .select_related("session", "term", "school_class", "fee_category")
        if school
        else FeeStructure.objects.none()
    )
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid() and school:
            obj = form.save(commit=False)
            obj.school = school
            obj.save()
            log_activity(request, "CREATE", "Finance", f"Created fee structure: {obj}")
            messages.success(request, "Fee structure created successfully.")
            return redirect("finance:fee-structures")
    else:
        form = FeeStructureForm()
    return render(request, "finance/fee_structures.html", {"form": form, "structures": structures})


@login_required
@role_required(*ROLES)
def fee_structure_edit(request, pk):
    school = _school(request)
    structure = get_object_or_404(FeeStructure, pk=pk, school=school)
    form = FeeStructureForm(request.POST or None, instance=structure)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_activity(request, "UPDATE", "Finance", f"Updated fee structure: {structure}")
        messages.success(request, "Fee structure updated successfully.")
        return redirect("finance:fee-structures")
    return render(
        request,
        "finance/fee_structure_form.html",
        {"form": form, "title": "Edit Fee Structure", "object": structure},
    )


@login_required
@role_required(*ROLES)
def invoice_list(request):
    school = _school(request)
    invoices = (
        StudentInvoice.objects.filter(school=school)
        .select_related("student", "session", "term")
        if school
        else StudentInvoice.objects.none()
    )
    return render(request, "finance/invoices.html", {"invoices": invoices})


@login_required
@role_required(*ROLES)
def invoice_create(request):
    school = _school(request)
    form = StudentInvoiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and school:
        student = form.cleaned_data["student"]
        session = form.cleaned_data["session"]
        term = form.cleaned_data["term"]

        if student.school_id != school.id:
            form.add_error("student", "Select a student from this school.")
        elif session.school_id != school.id:
            form.add_error("session", "Select an academic session belonging to this school.")
        elif term.school_id != school.id:
            form.add_error("term", "Select a term belonging to this school.")
        elif term.session_id != session.id:
            form.add_error("term", "The selected term must belong to the selected academic session.")
        elif not student.current_class_id:
            form.add_error("student", "This student has no current class. Assign a class before generating an invoice.")
        else:
            existing = StudentInvoice.objects.filter(
                school=school, student=student, session=session, term=term
            ).first()
            if existing:
                messages.info(request, f"Invoice {existing.invoice_number} already exists for this student, session and term.")
                return redirect("finance:invoice-detail", pk=existing.pk)

            structures = list(
                FeeStructure.objects.filter(
                    school=school,
                    session=session,
                    term=term,
                    school_class=student.current_class,
                ).select_related("fee_category")
            )
            if not structures:
                form.add_error(
                    None,
                    "No fee structure is configured for this student's current class, session and term.",
                )
            else:
                with transaction.atomic():
                    total = sum((item.amount for item in structures), Decimal("0.00"))
                    invoice = form.save(commit=False)
                    invoice.school = school
                    invoice.total_amount = total
                    invoice.balance = total
                    invoice.status = "UNPAID"
                    invoice.save()
                    InvoiceItem.objects.bulk_create(
                        [
                            InvoiceItem(
                                invoice=invoice,
                                fee_category=item.fee_category,
                                description=item.fee_category.name,
                                amount=item.amount,
                                due_date=invoice.due_date,
                            )
                            for item in structures
                        ]
                    )
                    log_activity(
                        request,
                        "CREATE",
                        "Finance",
                        f"Generated invoice {invoice.invoice_number} from fee structure",
                    )
                messages.success(request, f"Invoice {invoice.invoice_number} generated successfully from the applicable fee structure.")
                return redirect("finance:invoice-detail", pk=invoice.pk)

    return render(
        request,
        "finance/invoice_form.html",
        {"form": form, "title": "Generate Student Invoice"},
    )


@login_required
@role_required(*ROLES)
def invoice_detail(request, pk):
    school = _school(request)
    invoice = get_object_or_404(
        StudentInvoice.objects.prefetch_related("items", "payments"),
        pk=pk,
        school=school,
    )
    return render(
        request,
        "finance/invoice_detail.html",
        {"invoice": invoice, "payment_form": PaymentForm(invoice=invoice)},
    )


@login_required
@role_required(*ROLES)
def record_payment(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice, pk=pk, school=school)

    if invoice.balance <= Decimal("0.00"):
        messages.info(request, "This invoice has no outstanding balance.")
        return redirect("finance:invoice-detail", pk=invoice.pk)

    if request.method == "POST":
        with transaction.atomic():
            invoice = StudentInvoice.objects.select_for_update().get(pk=pk, school=school)
            form = PaymentForm(request.POST, invoice=invoice)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.invoice = invoice
                if payment.amount > invoice.balance:
                    form.add_error("amount", "Settlement cannot exceed the outstanding balance.")
                else:
                    payment.save()
                    label = payment.get_settlement_type_display()
                    log_activity(request, "CREATE", "Finance", f"Recorded {label.lower()} for {invoice.invoice_number}")
                    messages.success(request, f"{label} recorded successfully for {invoice.invoice_number}.")
                    return redirect("finance:invoice-detail", pk=invoice.pk)
    else:
        form = PaymentForm(invoice=invoice)

    return render(request, "finance/payment_form.html", {"form": form, "invoice": invoice})
