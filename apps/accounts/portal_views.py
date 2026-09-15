from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from apps.accounts.access import parent_students, role_code, student_for_user
from apps.attendance.models import AttendanceRecord
from apps.finance.models import Payment, StudentInvoice
from apps.notifications.models import Notification
from apps.results.models import StudentResult


def _prepare_invoices(invoices):
    for invoice in invoices:
        invoice.settled_amount = sum(
            (payment.amount for payment in invoice.payments.all()),
            0,
        )
    return invoices


def _attendance_summary(records):
    summary = {
        "total": 0,
        "present": 0,
        "absent": 0,
        "late": 0,
        "excused": 0,
    }
    for record in records:
        summary["total"] += 1
        key = record.status.lower()
        if key in summary:
            summary[key] += 1
    total = summary["total"]
    summary["rate"] = round(
        ((summary["present"] + summary["excused"]) / total) * 100,
        1,
    ) if total else 0
    return summary


def _portal_context(request, *, role_label, students, school, invoices, payments, results, attendance):
    notifications = Notification.objects.filter(
        recipient=request.user,
        school=school,
    ).order_by("-created_at")[:8]
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        school=school,
        is_read=False,
    ).count()
    attendance_list = list(attendance)

    return {
        "portal_role": role_label,
        "students": students,
        "results": results,
        "attendance": attendance_list,
        "attendance_summary": _attendance_summary(attendance_list),
        "invoices": invoices,
        "payments": payments,
        "notifications": notifications,
        "unread_notifications": unread_notifications,
        "total_billed": sum((invoice.total_amount for invoice in invoices), 0),
        "total_paid": payments.filter(settlement_type="PAYMENT").aggregate(v=Sum("amount"))["v"] or 0,
        "total_balance": sum((invoice.balance for invoice in invoices), 0),
    }


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
        return render(
            request,
            "accounts/portal.html",
            {"error": "Your student portal account is not linked to a student record."},
        )

    invoices = _prepare_invoices(list(
        StudentInvoice.objects.filter(
            school=student.school,
            student=student,
        ).prefetch_related("payments", "items").order_by("-created_at")
    ))
    payments = Payment.objects.filter(
        invoice__in=invoices,
    ).select_related("invoice", "invoice__student").order_by(
        "-payment_date", "-created_at"
    )
    results = StudentResult.objects.filter(
        school=student.school,
        student=student,
        published=True,
    ).prefetch_related("subjects__subject").select_related(
        "session", "term", "school_class"
    ).order_by("-created_at")
    attendance = AttendanceRecord.objects.filter(
        student=student,
        attendance_session__school=student.school,
    ).select_related(
        "attendance_session", "attendance_session__school_class"
    ).order_by("-attendance_session__attendance_date")

    context = _portal_context(
        request,
        role_label="Student",
        students=[student],
        school=student.school,
        invoices=invoices,
        payments=payments,
        results=results,
        attendance=attendance,
    )
    context["student"] = student
    return render(request, "accounts/portal.html", context)


def _parent_portal(request):
    school = getattr(getattr(request.user, "profile", None), "school", None)
    students = parent_students(request.user)
    invoices = _prepare_invoices(list(
        StudentInvoice.objects.filter(
            student__in=students,
            school=school,
        ).prefetch_related("payments", "items").select_related("student").order_by(
            "student__last_name", "-created_at"
        )
    ))
    payments = Payment.objects.filter(
        invoice__in=invoices,
    ).select_related("invoice", "invoice__student").order_by(
        "-payment_date", "-created_at"
    )
    results = StudentResult.objects.filter(
        student__in=students,
        school=school,
        published=True,
    ).prefetch_related("subjects__subject").select_related(
        "student", "session", "term", "school_class"
    ).order_by("student__last_name", "-created_at")
    attendance = AttendanceRecord.objects.filter(
        student__in=students,
        attendance_session__school=school,
    ).select_related(
        "student", "attendance_session", "attendance_session__school_class"
    ).order_by("student__last_name", "-attendance_session__attendance_date")

    return render(
        request,
        "accounts/portal.html",
        _portal_context(
            request,
            role_label="Parent",
            students=students,
            school=school,
            invoices=invoices,
            payments=payments,
            results=results,
            attendance=attendance,
        ),
    )
