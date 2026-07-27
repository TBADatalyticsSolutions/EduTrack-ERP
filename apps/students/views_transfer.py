from django.contrib import messages
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .models import (
    Student,
    TransferHistory,
)


def transfer_history(request):
    """
    Display transfer history dashboard.
    """

    transfers = (
        TransferHistory.objects
        .select_related(
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

    transfers_this_month = (
        TransferHistory.objects.filter(
            transfer_date__month=today.month,
            transfer_date__year=today.year,
        ).count()
    )

    transfers_this_session = (
        TransferHistory.objects.filter(
            to_session__isnull=False
        ).count()
    )

    rolled_back = (
        TransferHistory.objects.filter(
            rolled_back=True
        ).count()
    )

    context = {

        "transfers": transfers,

        "total_transfers": total_transfers,

        "transfers_this_month": transfers_this_month,

        "transfers_this_session": transfers_this_session,

        "rolled_back": rolled_back,

    }

    return render(
        request,
        "students/transfer_history.html",
        context,
    )


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

    student.save()

    history.rolled_back = True
    history.save()

    messages.success(
        request,
        f"{student.full_name()} has been restored to "
        f"{history.from_class}.",
    )

    return redirect("transfer-history")