from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.access import role_code
from apps.accounts.decorators import role_required

from .models import Student


ALLOWED_ROLES = ("SCHOOL_ADMIN", "PRINCIPAL")


def _school(request):
    return getattr(getattr(request.user, "profile", None), "school", None)


@login_required
@role_required(*ALLOWED_ROLES)
def bulk_student_id_cards(request):
    school = _school(request)
    if school is None:
        messages.error(request, "Your account is not linked to a school.")
        return redirect("student-list")

    base_qs = Student.objects.filter(school=school).select_related(
        "current_class", "current_session", "identity"
    ).order_by("current_class__name", "last_name", "first_name", "other_names")

    if request.method == "POST":
        selected_ids = request.POST.getlist("student_ids")
        if not selected_ids:
            messages.error(request, "Select at least one student to print ID cards.")
            return redirect("bulk-student-id-cards")

        students = list(base_qs.filter(pk__in=selected_ids))
        if not students:
            messages.error(request, "No valid students were selected.")
            return redirect("bulk-student-id-cards")

        return render(
            request,
            "students/bulk_student_id_cards.html",
            {"students": students, "school": school, "print_mode": True},
        )

    students = base_qs
    return render(
        request,
        "students/bulk_student_id_cards.html",
        {"students": students, "school": school, "print_mode": False},
    )
