from django.contrib import messages
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .forms import TransferForm
from .models import (
    Student,
    TransferHistory,
)
from .transfer import transfer_student


# ==========================================================
# INDIVIDUAL STUDENT TRANSFER
# ==========================================================

def transfer_student_view(request, pk):
    """
    Transfer a single student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

    if request.method == "POST":

        form = TransferForm(request.POST)

        if form.is_valid():

            transfer_student(
                student=student,
                to_class=form.cleaned_data["to_class"],
                to_session=form.cleaned_data["to_session"],
                transferred_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )

            messages.success(
                request,
                f"{student.full_name()} transferred successfully.",
            )

            return redirect("student-list")

    else:

        form = TransferForm()

    return render(
        request,
        "students/transfer_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# ==========================================================
# TRANSFER HISTORY
# ==========================================================

def transfer_history(request):
    """
    Display transfer history dashboard.
    """

    transfers = (
        TransferHistory.objects.select_related(
            "student",
            "from_class",
            "to_class",
            "transferred_by",
        )
        .order_by("-transfer_date")
    )

    search = request.GET.get("search")

    if search:

        transfers = transfers.filter(
            Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
            | Q(student__admission_number__icontains=search)
        )

    today = timezone.now().date()

    total_transfers = TransferHistory.objects.count()

    transfers_this_month = TransferHistory.objects.filter(
        transfer_date__month=today.month,
        transfer_date__year=today.year,
    ).count()

    transfers_this_session = TransferHistory.objects.filter(
        to_session__isnull=False,
    ).count()

    rolled_back = TransferHistory.objects.filter(
        rolled_back=True,
    ).count()

    return render(
        request,
        "students/transfer_history.html",
        {
            "transfers": transfers,
            "total_transfers": total_transfers,
            "transfers_this_month": transfers_this_month,
            "transfers_this_session": transfers_this_session,
            "rolled_back": rolled_back,
        },
    )


# ==========================================================
# ROLLBACK TRANSFER
# ==========================================================

def rollback_transfer(request, pk):
    """
    Undo a student transfer.
    """

    history = get_object_or_404(
        TransferHistory,
        pk=pk,
    )

    if history.rolled_back:

        messages.warning(
            request,
            "This transfer has already been rolled back.",
        )

        return redirect("transfer-history")

    student = history.student

    student.current_class = history.from_class
    student.current_session = history.from_session
    student.status = "ACTIVE"

    student.save(
        update_fields=[
            "current_class",
            "current_session",
            "status",
        ]
    )

    history.rolled_back = True
    history.save(update_fields=["rolled_back"])

    messages.success(
        request,
        f"{student.full_name()} has been restored to "
        f"{history.from_class}.",
    )

    return redirect("transfer-history")