from django.contrib.auth.decorators import login_required
from apps.accounts.utils import log_activity
from apps.accounts.decorators import role_required
from django.contrib import messages

from django.shortcuts import (

    get_object_or_404,
    redirect,
    render,
)

from .forms import WithdrawalForm
from .models import (
    Student,
    WithdrawalHistory,
)
from .withdrawal import (

    withdraw_student,
    reinstate_student_service,
)


@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
# =====================================================
# WITHDRAW STUDENT
# =====================================================
def withdraw_student_view(request, pk):
    """
    Withdraw an individual student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

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
                    action="UPDATE",
                    module="Unknown",
                    description="Operation completed",
                )

                messages.success(request, message)
                return redirect("student-list")

            messages.error(request, message)

    else:

        form = WithdrawalForm()

    return render(
        request,
        "students/withdraw_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# =====================================================
# WITHDRAWAL HISTORY
# =====================================================

def withdrawal_history(request):
    """
    Display all withdrawal records.
    """

    withdrawals = (
        WithdrawalHistory.objects
        .select_related(
            "student",
            "from_class",
            "from_session",
            "withdrawn_by",
            "reinstated_by",
        )
        .order_by("-withdrawal_date")
    )

    context = {

        "withdrawals": withdrawals,

        "total_withdrawals": withdrawals.count(),

        "active_withdrawals": withdrawals.filter(
            reinstated=False,
        ).count(),

        "reinstated_count": withdrawals.filter(
            reinstated=True,
        ).count(),
    }

    return render(
        request,
        "students/withdrawal_history.html",
        context,
    )


# =====================================================
# REINSTATE STUDENT
# =====================================================

def reinstate_student(request, pk):
    """
    Reinstate a withdrawn student.
    """

    history = get_object_or_404(
        WithdrawalHistory,
        pk=pk,
    )

    success, message = reinstate_student_service(
        history=history,
        reinstated_by=request.user,
    )

    if success:
        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect("withdrawal-history")
