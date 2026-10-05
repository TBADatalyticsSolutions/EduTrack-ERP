from base64 import b64encode
from io import BytesIO

import barcode
from barcode.writer import SVGWriter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.decorators import role_required

from .models import Student, StudentIdentity


ALLOWED_ROLES = ("SCHOOL_ADMIN", "PRINCIPAL")


def _school(request):
    return getattr(getattr(request.user, "profile", None), "school", None)


def _barcode_data(value):
    output = BytesIO()
    barcode.get("code128", value, writer=SVGWriter()).write(
        output,
        options={
            "module_width": 0.25,
            "module_height": 12,
            "font_size": 8,
            "text_distance": 2,
            "quiet_zone": 2,
        },
    )
    return b64encode(output.getvalue()).decode("ascii")


def _prepare_students(queryset):
    students = list(queryset)
    identity_map = {
        identity.student_id: identity.lin
        for identity in StudentIdentity.objects.filter(
            student_id__in=[student.pk for student in students]
        )
    }

    for student in students:
        student.student_lin = identity_map.get(student.pk)
        student.barcode_svg = _barcode_data(student.admission_number)

    return students


@login_required
@role_required(*ALLOWED_ROLES)
def bulk_student_id_cards(request):
    school = _school(request)
    if school is None:
        messages.error(request, "Your account is not linked to a school.")
        return redirect("student-list")

    base_qs = (
        Student.objects.filter(school=school)
        .select_related("current_class", "current_session")
        .order_by("current_class__name", "last_name", "first_name", "other_name")
    )

    if request.method == "POST":
        selected_ids = request.POST.getlist("student_ids")
        if not selected_ids:
            messages.error(request, "Select at least one student to print ID cards.")
            return redirect("bulk-student-id-cards")

        students = _prepare_students(base_qs.filter(pk__in=selected_ids))
        if not students:
            messages.error(request, "No valid students were selected.")
            return redirect("bulk-student-id-cards")

        return render(
            request,
            "students/bulk_student_id_cards.html",
            {
                "students": students,
                "school": school,
                "print_mode": True,
            },
        )

    students = list(base_qs)
    return render(
        request,
        "students/bulk_student_id_cards.html",
        {
            "students": students,
            "school": school,
            "print_mode": False,
        },
    )
