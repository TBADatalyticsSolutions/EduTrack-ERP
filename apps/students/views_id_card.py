from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.accounts.access import role_code, teacher_class_ids
from apps.accounts.decorators import role_required

from .models import Student


ALLOWED_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")


def _school(request):
    school = getattr(getattr(request.user, "profile", None), "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School
        school = School.objects.filter(is_active=True).order_by("id").first()
    return school


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
        from django.shortcuts import redirect
        return redirect("student-list")
    return render(request, "students/student_id_card.html", {"student": student, "school": school})
