from django.contrib.auth.decorators import login_required
from apps.accounts.utils import log_activity
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from django.contrib import messages
from apps.accounts.utils import log_activity
from django.shortcuts import (

    get_object_or_404,
    redirect,
    render,
)

from .forms import (

    SuspensionForm,
    ExpulsionForm,
)

from .models import (

    Student,
    DisciplineHistory,
)

from .discipline import (

    suspend_student,
    expel_student,
    reinstate_student_from_suspension,
)

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)

# =====================================================
# SUSPEND STUDENT
# =====================================================

def suspend_student_view(request, pk):
    """
    Suspend a student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

    if request.method == "POST":

        form = SuspensionForm(request.POST)

        if form.is_valid():

            success, message = suspend_student(
                student=student,
                disciplined_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
            )

            if success:
                messages.success(
                    request,
                    message,
                )
            else:
                messages.error(
                    request,
                    message,
                )

                messages.success(
                    request,
                    message,
                )
                return redirect("student-list")

            messages.error(
                request,
                message,
            )

    else:
        form = SuspensionForm()

    return render(
        request,
        "students/suspend_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# =====================================================
# EXPEL STUDENT
# =====================================================

def expel_student_view(request, pk):
    """
    Permanently expel a student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

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
                action="UPDATE",
                module="Unknown",
                description="Operation completed",
            )

                messages.success(
                    request,
                    message,
                )
                return redirect("student-list")

            messages.error(
                request,
                message,
            )

    else:
        form = ExpulsionForm()

    return render(
        request,
        "students/expel_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# =====================================================
# SUSPENSION HISTORY
# =====================================================

def suspension_history(request):
    """
    Display suspension history.
    """

    suspensions = (
        DisciplineHistory.objects.filter(
            action="SUSPENSION",
        )
        .select_related(
            "student",
            "disciplined_by",
        )
        .order_by(
            "-start_date",
        )
    )

    context = {
        "suspensions": suspensions,
        "total_suspensions": suspensions.count(),
        "active_suspensions": suspensions.filter(
            revoked=False,
        ).count(),
        "reinstated_count": suspensions.filter(
            revoked=True,
        ).count(),
    }

    return render(
        request,
        "students/suspension_history.html",
        context,
    )


# =====================================================
# EXPULSION HISTORY
# =====================================================

def expulsion_history(request):
    """
    Display expulsion history.
    """

    expulsions = (
        DisciplineHistory.objects.filter(
            action="EXPULSION",
        )
        .select_related(
            "student",
            "disciplined_by",
        )
        .order_by(
            "-start_date",
        )
    )

    context = {
        "expulsions": expulsions,
        "total_expulsions": expulsions.count(),
    }

    return render(
        request,
        "students/expulsion_history.html",
        context,
    )


# =====================================================
# REINSTATE SUSPENDED STUDENT
# =====================================================

def reinstate_suspended_student(request, pk):
    """
    Reinstate a suspended student.
    """

    history = get_object_or_404(
        DisciplineHistory,
        pk=pk,
        action="SUSPENSION",
    )

    success, message = reinstate_student_from_suspension(
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

        messages.success(
            request,
            message,
        )
    else:
        messages.error(
            request,
            message,
        )

    return redirect(
        "suspension-history",
    )