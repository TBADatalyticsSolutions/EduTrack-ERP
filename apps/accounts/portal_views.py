from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.accounts.access import parent_students, role_code, student_for_user
from apps.attendance.models import AttendanceRecord
from apps.finance.models import Payment, StudentInvoice
from apps.notifications.models import Notification
from apps.results.models import GradeSetting, StudentResult
from apps.schools.models import SchoolSubscription


def _prepare_invoices(invoices):
    for invoice in invoices:
        invoice.settled_amount = sum(
            (payment.amount for payment in invoice.payments.all()),
            0,
        )
    return invoices


def _attendance_summary(records):
    summary = {"total": 0, "present": 0, "absent": 0, "late": 0, "excused": 0}
    for record in records:
        summary["total"] += 1
        key = record.status.lower()
        if key in summary:
            summary[key] += 1
    total = summary["total"]
    summary["rate"] = round(((summary["present"] + summary["excused"]) / total) * 100, 1) if total else 0
    return summary


def _portal_context(request, *, role_label, students, school, invoices, payments, results, attendance):
    notifications = Notification.objects.filter(recipient=request.user, school=school).order_by("-created_at")[:8]
    unread_notifications = Notification.objects.filter(recipient=request.user, school=school, is_read=False).count()
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


def _published_result_queryset():
    return StudentResult.objects.filter(published=True).prefetch_related("subjects__subject").select_related(
        "student", "session", "term", "school_class", "school"
    )


def _scoped_portal_result(request, pk):
    role = role_code(request.user)
    if role not in {"STUDENT", "PARENT"}:
        return None, role, None
    school = getattr(getattr(request.user, "profile", None), "school", None)
    if not school:
        return None, role, None
    result_qs = _published_result_queryset().filter(school=school, pk=pk)
    if role == "STUDENT":
        student = student_for_user(request.user)
        if not student:
            return None, role, school
        result_qs = result_qs.filter(student=student)
    else:
        result_qs = result_qs.filter(student__in=parent_students(request.user))
    return get_object_or_404(result_qs), role, school


def _result_report_context(result, role):
    attendance = AttendanceRecord.objects.filter(
        student=result.student,
        attendance_session__school=result.school,
        attendance_session__school_class=result.school_class,
    ).select_related("attendance_session").order_by("-attendance_session__attendance_date")
    attendance_list = list(attendance)
    return {
        "result": result,
        "portal_role": "Student" if role == "STUDENT" else "Parent",
        "grades": GradeSetting.objects.filter(school=result.school).order_by("-minimum_score"),
        "attendance": attendance_list,
        "attendance_summary": _attendance_summary(attendance_list),
        "school_logo_uri": (
            Path(result.school.logo.path).resolve().as_uri()
            if result.school.logo and result.school.logo.name
            else ""
        ),
    }


@login_required
def portal_dashboard(request):
    role = role_code(request.user)
    if role not in {"STUDENT", "PARENT"}:
        return redirect("profile")
    school = getattr(getattr(request.user, "profile", None), "school", None)
    subscription = SchoolSubscription.objects.filter(school=school).first() if school else None
    if not school or not subscription or subscription.status != "ACTIVE":
        return render(request, "accounts/portal.html", {"error": "Your school's EduTrack subscription is not active. Please contact your school administrator."}, status=403)
    if role == "STUDENT":
        return _student_portal(request)
    return _parent_portal(request)


@login_required
def portal_result_detail(request, pk):
    if role_code(request.user) not in {"STUDENT", "PARENT"}:
        return redirect("profile")
    result, role, school = _scoped_portal_result(request, pk)
    if not school:
        return render(request, "accounts/portal_result_detail.html", {"error": "Your portal account is not assigned to a school tenant."}, status=403)
    if not result:
        return render(request, "accounts/portal_result_detail.html", {"error": "Your portal account is not linked to an eligible student record."}, status=403)
    return render(request, "accounts/portal_result_detail.html", _result_report_context(result, role))


@login_required
def portal_result_pdf(request, pk):
    if role_code(request.user) not in {"STUDENT", "PARENT"}:
        return redirect("profile")
    result, role, school = _scoped_portal_result(request, pk)
    if not school:
        return HttpResponse("Your portal account is not assigned to a school tenant.", status=403)
    if not result:
        return HttpResponse("Result not found.", status=404)
    context = _result_report_context(result, role)
    html = render_to_string("accounts/portal_result_pdf.html", context, request=request)
    pdf = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    filename = f"{result.student.admission_number}-{result.session}-{result.term}-result.pdf".replace("/", "-")
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _student_portal(request):
    student = student_for_user(request.user)
    if not student:
        return render(request, "accounts/portal.html", {"error": "Your student portal account is not linked to a student record."})
    invoices = _prepare_invoices(list(StudentInvoice.objects.filter(school=student.school, student=student).prefetch_related("payments", "items").order_by("-created_at")))
    payments = Payment.objects.filter(invoice__in=invoices).select_related("invoice", "invoice__student").order_by("-payment_date", "-created_at")
    results = _published_result_queryset().filter(school=student.school, student=student).order_by("-created_at")
    attendance = AttendanceRecord.objects.filter(student=student, attendance_session__school=student.school).select_related("attendance_session", "attendance_session__school_class").order_by("-attendance_session__attendance_date")
    context = _portal_context(request, role_label="Student", students=[student], school=student.school, invoices=invoices, payments=payments, results=results, attendance=attendance)
    context["student"] = student
    return render(request, "accounts/portal.html", context)


def _parent_portal(request):
    school = getattr(getattr(request.user, "profile", None), "school", None)
    students = parent_students(request.user)
    invoices = _prepare_invoices(list(StudentInvoice.objects.filter(student__in=students, school=school).prefetch_related("payments", "items").select_related("student").order_by("student__last_name", "-created_at")))
    payments = Payment.objects.filter(invoice__in=invoices).select_related("invoice", "invoice__student").order_by("-payment_date", "-created_at")
    results = _published_result_queryset().filter(student__in=students, school=school).order_by("student__last_name", "-created_at")
    attendance = AttendanceRecord.objects.filter(student__in=students, attendance_session__school=school).select_related("student", "attendance_session", "attendance_session__school_class").order_by("student__last_name", "-attendance_session__attendance_date")
    return render(request, "accounts/portal.html", _portal_context(request, role_label="Parent", students=students, school=school, invoices=invoices, payments=payments, results=results, attendance=attendance))
