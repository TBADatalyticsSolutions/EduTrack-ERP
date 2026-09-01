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
    """
    Resolve the active school for the current user.

    A superuser may still belong to a specific school. Prefer that explicit
    profile assignment so school-scoped data does not accidentally fall back
    to the first school in the database.
    """
    profile_school = getattr(
        getattr(request.user, "profile", None),
        "school",
        None,
    )
    if profile_school is not None:
        return profile_school

    if request.user.is_superuser:
        return School.objects.order_by("name").first()

    return None


def _recalculate_invoice(invoice):
    settled = invoice.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    invoice.total_amount = invoice.items.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    invoice.balance = max(invoice.total_amount - settled, Decimal("0.00"))
    if invoice.balance == Decimal("0.00"):
        invoice.status = "PAID"
    elif settled > Decimal("0.00"):
        invoice.status = "PARTIAL"
    else:
        invoice.status = "UNPAID"
    invoice.save(update_fields=["total_amount", "balance", "status"])


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
            obj = form.save(commit=False); obj.school = school; obj.save()
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
    structures = FeeStructure.objects.filter(school=school).select_related("session", "term", "school_class", "fee_category") if school else FeeStructure.objects.none()
    form = FeeStructureForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid() and school:
        obj = form.save(commit=False); obj.school = school; obj.save()
        messages.success(request, "Fee structure created successfully.")
        return redirect("finance:fee-structures")
    return render(request, "finance/fee_structures.html", {"form": form, "structures": structures})


@login_required
@role_required(*ROLES)
def fee_structure_edit(request, pk):
    school = _school(request)
    structure = get_object_or_404(FeeStructure, pk=pk, school=school)
    form = FeeStructureForm(request.POST or None, instance=structure, school=school)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_activity(request, "UPDATE", "Finance", f"Updated fee structure: {structure}")
        messages.success(request, "Fee structure updated successfully.")
        return redirect("finance:fee-structures")
    return render(request, "finance/fee_structure_form.html", {"form": form, "title": "Edit Fee Structure", "object": structure})


@login_required
@role_required(*ROLES)
def invoice_list(request):
    school = _school(request)
    invoices = StudentInvoice.objects.filter(school=school).select_related("student", "session", "term") if school else StudentInvoice.objects.none()
    return render(request, "finance/invoices.html", {"invoices": invoices})


@login_required
@role_required(*ROLES)
def invoice_create(request):
    school = _school(request)
    form = StudentInvoiceForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid() and school:
        student = form.cleaned_data["student"]
        session = form.cleaned_data["session"]
        term = form.cleaned_data["term"]
        if not student.current_class_id:
            form.add_error("student", "This student has no current class. Assign a class before generating an invoice.")
        else:
            existing = StudentInvoice.objects.filter(school=school, student=student, session=session, term=term).first()
            if existing:
                messages.info(request, f"Invoice {existing.invoice_number} already exists for this student, session and term.")
                return redirect("finance:invoice-detail", pk=existing.pk)
            structures = list(FeeStructure.objects.filter(school=school, session=session, term=term, school_class=student.current_class).select_related("fee_category"))
            if not structures:
                form.add_error(None, "No fee structure is configured for this student's current class, session and term.")
            else:
                with transaction.atomic():
                    total = sum((item.amount for item in structures), Decimal("0.00"))
                    invoice = form.save(commit=False); invoice.school = school; invoice.total_amount = total; invoice.balance = total; invoice.status = "UNPAID"; invoice.save()
                    InvoiceItem.objects.bulk_create([
                        InvoiceItem(invoice=invoice, fee_category=item.fee_category, description=item.fee_category.name, amount=item.amount, due_date=invoice.due_date)
                        for item in structures
                    ])
                    log_activity(request, "CREATE", "Finance", f"Generated invoice {invoice.invoice_number} from fee structure")
                messages.success(request, f"Invoice {invoice.invoice_number} generated successfully from the applicable fee structure.")
                return redirect("finance:invoice-detail", pk=invoice.pk)
    return render(request, "finance/invoice_form.html", {"form": form, "title": "Generate Student Invoice"})


@login_required
@role_required(*ROLES)
def invoice_edit(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice, pk=pk, school=school)
    if invoice.payments.exists():
        messages.warning(request, "This invoice has financial settlements and cannot be edited. Create an adjustment or waiver instead.")
        return redirect("finance:invoice-detail", pk=invoice.pk)
    form = StudentInvoiceForm(request.POST or None, instance=invoice, school=school, editable=True)
    if request.method == "POST" and form.is_valid():
        invoice.due_date = form.cleaned_data["due_date"]
        invoice.remarks = form.cleaned_data["remarks"]
        invoice.save(update_fields=["due_date", "remarks"])
        log_activity(request, "UPDATE", "Finance", f"Updated invoice {invoice.invoice_number}")
        messages.success(request, f"Invoice {invoice.invoice_number} updated successfully. The original fee snapshot was preserved.")
        return redirect("finance:invoice-detail", pk=invoice.pk)
    return render(request, "finance/invoice_form.html", {"form": form, "title": f"Edit Invoice {invoice.invoice_number}", "invoice": invoice})


@login_required
@role_required(*ROLES)
def invoice_delete(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice, pk=pk, school=school)
    if invoice.payments.exists():
        messages.error(request, "This invoice cannot be deleted because it has financial settlements. Reverse or adjust the settlements first.")
        return redirect("finance:invoice-detail", pk=invoice.pk)
    if request.method == "POST":
        number = invoice.invoice_number; invoice.delete()
        log_activity(request, "DELETE", "Finance", f"Deleted invoice {number}")
        messages.success(request, f"Invoice {number} deleted successfully.")
        return redirect("finance:invoice-list")
    return render(request, "finance/invoice_confirm_delete.html", {"invoice": invoice})


@login_required
@role_required(*ROLES)
def invoice_detail(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice.objects.prefetch_related("items", "payments"), pk=pk, school=school)
    return render(request, "finance/invoice_detail.html", {"invoice": invoice, "payment_form": PaymentForm(invoice=invoice)})


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
                payment = form.save(commit=False); payment.invoice = invoice
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
