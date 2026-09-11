from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .discipline import (
    expel_student,
    reinstate_student_from_suspension,
    suspend_student,
)
from .forms import ExpulsionForm, SuspensionForm
from .models import DisciplineHistory, Student


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


def _school(request):
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "school", None)


@login_required
@role_required(*ROLES)
def suspend_student_view(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = SuspensionForm(request.POST)
        if form.is_valid():
            success, message = suspend_student(
                student=student,
                disciplined_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
                start_date=form.cleaned_data["suspension_start"],
                end_date=form.cleaned_data["suspension_end"],
            )
            if success:
                log_activity(
                    request,
                    action="SUSPENSION",
                    module="Students",
                    description=f"Suspended student '{student.full_name()}'.",
                )
                messages.success(request, message)
                return redirect("student-list")
            messages.error(request, message)
    else:
        form = SuspensionForm()

    return render(
        request,
        "students/suspend_student.html",
        {"student": student, "form": form},
    )


@login_required
@role_required(*ROLES)
def expel_student_view(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = ExpulsionForm(request.POST)
        if form.is_valid():
            success, message = expel_student(
                student=student,
                disciplined_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )
            if success:
                log_activity(
                    request,
                    action="EXPULSION",
                    module="Students",
                    description=f"Expelled student '{student.full_name()}'.",
                )
                messages.success(request, message)
                return redirect("student-list")
            messages.error(request, message)
    else:
        form = ExpulsionForm()

    return render(
        request,
        "students/expel_student.html",
        {"student": student, "form": form},
    )


@login_required
@role_required(*ROLES)
def suspension_history(request):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    suspensions = DisciplineHistory.objects.filter(
        school=school,
        action="SUSPENSION",
    ).select_related("student", "disciplined_by").order_by("-start_date")

    return render(
        request,
        "students/suspension_history.html",
        {
            "suspensions": suspensions,
            "total_suspensions": suspensions.count(),
            "active_suspensions": suspensions.filter(revoked=False).count(),
            "reinstated_count": suspensions.filter(revoked=True).count(),
        },
    )


@login_required
@role_required(*ROLES)
def expulsion_history(request):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    expulsions = DisciplineHistory.objects.filter(
        school=school,
        action="EXPULSION",
    ).select_related("student", "disciplined_by").order_by("-start_date")

    return render(
        request,
        "students/expulsion_history.html",
        {"expulsions": expulsions, "total_expulsions": expulsions.count()},
    )


@login_required
@role_required(*ROLES)
def reinstate_suspended_student(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    if request.method != "POST":
        messages.error(request, "Suspension reinstatement must be submitted using POST.")
        return redirect("suspension-history")

    history = get_object_or_404(
        DisciplineHistory,
        pk=pk,
        school=school,
        action="SUSPENSION",
    )
    success, message = reinstate_student_from_suspension(
        history=history,
        reinstated_by=request.user,
    )
    if success:
        log_activity(
            request,
            action="REINSTATEMENT",
            module="Students",
            description=f"Reinstated suspended student '{history.student.full_name()}'.",
        )
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect("suspension-history")


@login_required
@role_required(*ROLES)
def discipline_dashboard(request):
    """Display the school-scoped student discipline dashboard."""
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    students = Student.objects.filter(school=school)
    records = DisciplineHistory.objects.filter(school=school).select_related(
        "student", "disciplined_by"
    )
    suspensions = records.filter(action="SUSPENSION")
    expulsions = records.filter(action="EXPULSION")

    return render(
        request,
        "students/discipline_dashboard.html",
        {
            "total_students": students.count(),
            "active_students": students.filter(status="ACTIVE").count(),
            "suspended_students": students.filter(status="SUSPENDED").count(),
            "expelled_students": students.filter(status="EXPELLED").count(),
            "total_suspensions": suspensions.count(),
            "active_suspensions": suspensions.filter(revoked=False).count(),
            "reinstated_students": suspensions.filter(revoked=True).count(),
            "total_expulsions": expulsions.count(),
            "recent_cases": records.order_by("-start_date")[:10],
        },
    )
