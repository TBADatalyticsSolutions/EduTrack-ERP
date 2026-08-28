from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import FeeCategoryForm, FeeStructureForm, StudentInvoiceForm, PaymentForm
from .models import FeeCategory, FeeStructure, StudentInvoice, Payment

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
        "total_paid": payments.aggregate(v=Sum("amount"))["v"] or Decimal("0"),
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
def invoice_list(request):
    school = _school(request)
    invoices = StudentInvoice.objects.filter(school=school).select_related("student", "session", "term") if school else StudentInvoice.objects.none()
    return render(request, "finance/invoices.html", {"invoices": invoices})


@login_required
@role_required(*ROLES)
def invoice_create(request):
    school = _school(request)
    form = StudentInvoiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and school:
        invoice = form.save(commit=False); invoice.school = school; invoice.total_amount = Decimal("0"); invoice.balance = Decimal("0"); invoice.save()
        log_activity(request, "CREATE", "Finance", f"Created invoice: {invoice.invoice_number}")
        messages.success(request, "Invoice created successfully.")
        return redirect("finance:invoice-list")
    return render(request, "finance/invoice_form.html", {"form": form, "title": "Create Invoice"})


@login_required
@role_required(*ROLES)
def invoice_detail(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice.objects.prefetch_related("items", "payments"), pk=pk, school=school)
    return render(request, "finance/invoice_detail.html", {"invoice": invoice, "payment_form": PaymentForm()})


@login_required
@role_required(*ROLES)
def record_payment(request, pk):
    school = _school(request)
    invoice = get_object_or_404(StudentInvoice, pk=pk, school=school)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False); payment.invoice = invoice
            if payment.amount > invoice.balance:
                form.add_error("amount", "Payment cannot exceed the outstanding balance.")
            else:
                payment.save(); log_activity(request, "CREATE", "Finance", f"Recorded payment for {invoice.invoice_number}")
                messages.success(request, "Payment recorded successfully.")
                return redirect("finance:invoice-detail", pk=invoice.pk)
    else:
        form = PaymentForm()
    return render(request, "finance/payment_form.html", {"form": form, "invoice": invoice})


@login_required
@role_required(*ROLES)
def fee_structures(request):
    school = _school(request)
    structures = FeeStructure.objects.filter(school=school).select_related("session", "term", "school_class", "fee_category") if school else FeeStructure.objects.none()
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid() and school:
            obj = form.save(commit=False); obj.school = school; obj.save()
            messages.success(request, "Fee structure created successfully.")
            return redirect("finance:fee-structures")
    else:
        form = FeeStructureForm()
    return render(request, "finance/fee_structures.html", {"form": form, "structures": structures})
