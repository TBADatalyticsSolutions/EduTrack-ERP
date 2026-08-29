from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import role_required
from apps.schools.models import School

from .models import Payment, StudentInvoice

ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)


@login_required
@role_required(*ROLES)
def financial_report(request):
    school = _school(request)
    invoices = StudentInvoice.objects.filter(school=school) if school else StudentInvoice.objects.none()
    payments = Payment.objects.filter(invoice__school=school).select_related("invoice", "invoice__student") if school else Payment.objects.none()
    settlement_type = request.GET.get("type", "")
    if settlement_type in {"PAYMENT", "SCHOLARSHIP", "WAIVER"}:
        payments = payments.filter(settlement_type=settlement_type)
    context = {
        "school": school,
        "payments": payments,
        "filter_type": settlement_type,
        "total_billed": invoices.aggregate(v=Sum("total_amount"))["v"] or Decimal("0.00"),
        "total_outstanding": invoices.aggregate(v=Sum("balance"))["v"] or Decimal("0.00"),
        "total_collected": payments.filter(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or Decimal("0.00"),
        "total_scholarships": payments.filter(settlement_type="SCHOLARSHIP").aggregate(v=Sum("amount"))["v"] or Decimal("0.00"),
        "total_waivers": payments.filter(settlement_type="WAIVER").aggregate(v=Sum("amount"))["v"] or Decimal("0.00"),
    }
    return render(request, "finance/financial_report.html", context)


@login_required
@role_required(*ROLES)
def payment_receipt(request, pk):
    school = _school(request)
    payment = get_object_or_404(
        Payment.objects.select_related("invoice", "invoice__student", "invoice__school"),
        pk=pk,
        invoice__school=school,
    )
    receipt_number = f"REC-{payment.payment_date.year}-{str(payment.id)[:8].upper()}"
    return render(
        request,
        "finance/payment_receipt.html",
        {"payment": payment, "receipt_number": receipt_number, "school": school},
    )
