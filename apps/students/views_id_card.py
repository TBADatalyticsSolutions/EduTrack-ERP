from base64 import b64encode
from io import BytesIO

import barcode
from barcode.writer import SVGWriter
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from apps.accounts.access import role_code, teacher_class_ids
from apps.accounts.decorators import role_required

from .models import Student, StudentIdentity


ALLOWED_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")


def _school(request):
    school = getattr(getattr(request.user, "profile", None), "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School
        school = School.objects.filter(is_active=True).order_by("id").first()
    return school


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


@login_required
@role_required(*ALLOWED_ROLES)
def student_id_card(request, pk):
    school = _school(request)
    student = get_object_or_404(
        Student.objects.select_related("school", "current_class", "current_session"),
        pk=pk,
        school=school,
    )

    if role_code(request.user) == "TEACHER" and student.current_class_id not in teacher_class_ids(request.user):
        from django.contrib import messages
        messages.error(request, "You can only view ID cards for students in your assigned classes.")
        return redirect("student-list")

    identity = StudentIdentity.objects.filter(student_id=student.pk).only("lin").first()

    return render(
        request,
        "students/student_id_card.html",
        {
            "student": student,
            "school": school,
            "student_lin": identity.lin if identity else None,
            "barcode_svg": _barcode_data(student.admission_number),
        },
    )
