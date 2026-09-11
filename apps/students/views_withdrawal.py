from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .forms import WithdrawalForm
from .models import Student, WithdrawalHistory
from .withdrawal import reinstate_student_service, withdraw_student


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


def _school(request):
    profile = getattr(request.user, "profile", None)
    school = getattr(profile, "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School

        school = School.objects.filter(is_active=True).order_by("id").first()
    return school


@login_required
@role_required(*ROLES)
def withdraw_student_view(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            success, message = withdraw_student(
                student=student,
                withdrawn_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )
            if success:
                log_activity(
                    request,
                    action="WITHDRAWAL",
                    module="Students",
                    description=f"Withdrew student '{student.full_name()}'.",
                )
                messages.success(request, message)
                return redirect("student-list")
            messages.error(request, message)
    else:
        form = WithdrawalForm()

    return render(
        request,
        "students/withdraw_student.html",
        {"student": student, "form": form},
    )


@login_required
@role_required(*ROLES)
def withdrawal_history(request):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    withdrawals = WithdrawalHistory.objects.filter(school=school).select_related(
        "student",
        "from_class",
        "from_session",
        "withdrawn_by",
        "reinstated_by",
    ).order_by("-withdrawal_date")

    return render(
        request,
        "students/withdrawal_history.html",
        {
            "withdrawals": withdrawals,
            "total_withdrawals": withdrawals.count(),
            "active_withdrawals": withdrawals.filter(reinstated=False).count(),
            "reinstated_count": withdrawals.filter(reinstated=True).count(),
        },
    )


@login_required
@role_required(*ROLES)
def reinstate_student(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    if request.method != "POST":
        messages.error(request, "Student reinstatement must be submitted using POST.")
        return redirect("withdrawal-history")

    history = get_object_or_404(WithdrawalHistory, pk=pk, school=school)
    success, message = reinstate_student_service(
        history=history,
        reinstated_by=request.user,
    )
    if success:
        log_activity(
            request,
            action="REINSTATEMENT",
            module="Students",
            description=f"Reinstated student '{history.student.full_name()}'.",
        )
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect("withdrawal-history")
