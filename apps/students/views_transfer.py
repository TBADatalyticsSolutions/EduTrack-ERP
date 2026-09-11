from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .forms import TransferForm
from .models import Student, TransferHistory
from .transfer import transfer_student


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


def _school(request):
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "school", None)


@login_required
@role_required(*ROLES)
def transfer_student_view(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = TransferForm(request.POST, school=school)
        if form.is_valid():
            success, message = transfer_student(
                student=student,
                to_class=form.cleaned_data["to_class"],
                to_session=form.cleaned_data["to_session"],
                transferred_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )
            if success:
                log_activity(
                    request,
                    action="TRANSFER",
                    module="Students",
                    description=f"Transferred student '{student.full_name()}'.",
                )
                messages.success(request, message)
                return redirect("student-list")
            messages.error(request, message)
    else:
        form = TransferForm(school=school)

    return render(
        request,
        "students/transfer_student.html",
        {"student": student, "form": form},
    )


@login_required
@role_required(*ROLES)
def transfer_history(request):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    transfers = TransferHistory.objects.filter(school=school).select_related(
        "student",
        "from_class",
        "to_class",
        "from_session",
        "to_session",
        "transferred_by",
    )
    search = request.GET.get("search", "").strip()
    if search:
        transfers = transfers.filter(
            Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
            | Q(student__admission_number__icontains=search)
        )

    today = timezone.now().date()
    context = {
        "transfers": transfers.order_by("-transfer_date"),
        "total_transfers": transfers.count(),
        "transfers_this_month": transfers.filter(
            transfer_date__month=today.month,
            transfer_date__year=today.year,
        ).count(),
        "transfers_this_session": transfers.filter(to_session__isnull=False).count(),
        "rolled_back": transfers.filter(rolled_back=True).count(),
    }
    return render(request, "students/transfer_history.html", context)


@login_required
@role_required(*ROLES)
def rollback_transfer(request, pk):
    school = _school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    if request.method != "POST":
        messages.error(request, "Transfer rollback must be submitted using POST.")
        return redirect("transfer-history")

    history = get_object_or_404(TransferHistory, pk=pk, school=school)
    if history.rolled_back:
        messages.warning(request, "This transfer has already been rolled back.")
        return redirect("transfer-history")

    student = history.student
    with transaction.atomic():
        student.current_class = history.from_class
        student.current_session = history.from_session
        student.status = "ACTIVE"
        student.save(update_fields=["current_class", "current_session", "status"])
        history.rolled_back = True
        history.save(update_fields=["rolled_back"])

    log_activity(
        request,
        action="TRANSFER_ROLLBACK",
        module="Students",
        description=f"Rolled back transfer for '{student.full_name()}'.",
    )
    messages.success(
        request,
        f"{student.full_name()} has been restored to "
        f"{history.from_class or 'the previous class'}.",
    )
    return redirect("transfer-history")
