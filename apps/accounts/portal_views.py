from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import Sum

from apps.accounts.access import parent_students, role_code, student_for_user
from apps.attendance.models import AttendanceRecord
from apps.finance.models import StudentInvoice, Payment
from apps.results.models import StudentResult


@login_required

def portal_dashboard(request):
    role = role_code(request.user)
    if role == "STUDENT":
        return _student_portal(request)
    if role == "PARENT":
        return _parent_portal(request)
    return redirect("profile")


def _student_portal(request):
    student = student_for_user(request.user)
    if not student:
        return render(request, "accounts/portal.html", {"error": "Your student portal account is not linked to a student record."})

    invoices = StudentInvoice.objects.filter(
        school=student.school,
        student=student,
    ).prefetch_related("payments", "items").order_by("-created_at")
    payments = Payment.objects.filter(invoice__in=invoices).order_by("-payment_date", "-created_at")
    results = StudentResult.objects.filter(
        school=student.school,
        student=student,
        published=True,
    ).prefetch_related("subjects__subject").select_related("session", "term", "school_class").order_by("-created_at")
    attendance = AttendanceRecord.objects.filter(
        student=student,
    ).select_related("attendance_session", "attendance_session__school_class").order_by("-attendance_session__attendance_date")

    return render(
        request,
        "accounts/portal.html",
        {
            "portal_role": "Student",
            "student": student,
            "students": [student],
            "results": results,
            "attendance": attendance,
            "invoices": invoices,
            "payments": payments,
            "total_billed": invoices.aggregate(v=Sum("total_amount"))["v"] or 0,
            "total_paid": payments.filter(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or 0,
            "total_balance": invoices.aggregate(v=Sum("balance"))["v"] or 0,
        },
    )


def _parent_portal(request):
    students = parent_students(request.user)
    invoices = StudentInvoice.objects.filter(
        student__in=students,
        school=getattr(getattr(request.user, "profile", None), "school", None),
    ).prefetch_related("payments", "items").select_related("student").order_by("student__last_name", "-created_at")
    payments = Payment.objects.filter(invoice__in=invoices).select_related("invoice", "invoice__student").order_by("-payment_date", "-created_at")
    results = StudentResult.objects.filter(
        student__in=students,
        school=getattr(getattr(request.user, "profile", None), "school", None),
        published=True,
    ).prefetch_related("subjects__subject").select_related("student", "session", "term", "school_class").order_by("student__last_name", "-created_at")
    attendance = AttendanceRecord.objects.filter(
        student__in=students,
    ).select_related("student", "attendance_session", "attendance_session__school_class").order_by("student__last_name", "-attendance_session__attendance_date")

    return render(
        request,
        "accounts/portal.html",
        {
            "portal_role": "Parent",
            "students": students,
            "results": results,
            "attendance": attendance,
            "invoices": invoices,
            "payments": payments,
            "total_billed": invoices.aggregate(v=Sum("total_amount"))["v"] or 0,
            "total_paid": payments.filter(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or 0,
            "total_balance": invoices.aggregate(v=Sum("balance"))["v"] or 0,
        },
    )
