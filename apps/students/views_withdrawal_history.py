from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .models import (
    Student,
    WithdrawalHistory,
)


def withdrawal_history(request):
    """
    Display withdrawal history dashboard.
    """

    withdrawals = (
        WithdrawalHistory.objects
        .select_related(
            "student",
            "from_class",
            "withdrawn_by",
        )
        .order_by("-withdrawal_date")
    )

    search = request.GET.get("search")

    if search:

        withdrawals = withdrawals.filter(

            Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
            | Q(student__admission_number__icontains=search)

        )

    today = timezone.now().date()

    total_withdrawals = WithdrawalHistory.objects.count()

    withdrawals_this_month = (
        WithdrawalHistory.objects.filter(
            withdrawal_date__month=today.month,
            withdrawal_date__year=today.year,
        ).count()
    )

    reinstated = (
        WithdrawalHistory.objects.filter(
            reinstated=True
        ).count()
    )

    context = {

        "withdrawals": withdrawals,

        "total_withdrawals": total_withdrawals,

        "withdrawals_this_month": withdrawals_this_month,

        "reinstated": reinstated,

    }

    return render(
        request,
        "students/withdrawal_history.html",
        context,
    )


@transaction.atomic
def reinstate_student(request, pk):
    """
    Reinstate a withdrawn student.
    """

    history = get_object_or_404(
        WithdrawalHistory,
        pk=pk,
    )

    if history.reinstated:

        messages.warning(
            request,
            "This student has already been reinstated.",
        )

        return redirect("withdrawal-history")

    student = history.student

    student.status = "ACTIVE"
    student.current_class = history.from_class
    student.current_session = history.from_session

    student.save()

    history.reinstated = True
    history.reinstated_date = timezone.now()
    history.save()

    messages.success(
        request,
        f"{student.full_name()} has been reinstated successfully.",
    )

    return redirect("withdrawal-history")