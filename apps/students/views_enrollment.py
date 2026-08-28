from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .enrollment_forms import StudentEnrollmentForm
from .models import Student


ALLOWED_ROLES = (
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)


def get_user_school(request):
    if request.user.is_superuser:
        return getattr(getattr(request.user, "profile", None), "school", None)
    return getattr(getattr(request.user, "profile", None), "school", None)


def generate_admission_number(school):
    """Generate a unique school admission number."""
    prefix = "EDU"
    if school.short_name:
        cleaned = "".join(ch for ch in school.short_name.upper() if ch.isalnum())
        prefix = cleaned[:8] or prefix

    year = timezone.now().year
    base = f"{prefix}/{year}/"
    last = (
        Student.objects.filter(
            school=school,
            admission_number__startswith=base,
        )
        .order_by("-admission_number")
        .values_list("admission_number", flat=True)
        .first()
    )

    number = 1
    if last:
        try:
            number = int(last.rsplit("/", 1)[-1]) + 1
        except ValueError:
            number = Student.objects.filter(school=school).count() + 1

    candidate = f"{base}{number:04d}"
    while Student.objects.filter(admission_number=candidate).exists():
        number += 1
        candidate = f"{base}{number:04d}"
    return candidate


@login_required
@role_required(*ALLOWED_ROLES)
def student_enrol(request):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    if request.method == "POST":
        form = StudentEnrollmentForm(
            request.POST,
            request.FILES,
            school=school,
        )
        if form.is_valid():
            with transaction.atomic():
                student = form.save(commit=False)
                student.school = school
                student.admission_number = generate_admission_number(school)
                student.status = "ACTIVE"
                student.is_graduated = False
                student.save()

                parent_data = {
                    "first_name": form.cleaned_data["parent_first_name"].strip(),
                    "last_name": form.cleaned_data["parent_last_name"].strip(),
                    "phone": form.cleaned_data["parent_phone"].strip(),
                    "email": form.cleaned_data.get("parent_email", "").strip(),
                    "address": form.cleaned_data.get("parent_address", "").strip(),
                }
                from .models import Parent
                parent = Parent.objects.create(school=school, **parent_data)
                parent.students.add(student)

            log_activity(
                request,
                action="CREATE",
                module="Students",
                description=(
                    f"Enrolled student '{student.full_name()}' "
                    f"with admission number '{student.admission_number}'."
                ),
            )
            messages.success(
                request,
                f"{student.full_name()} enrolled successfully. "
                f"Admission No.: {student.admission_number}",
            )
            return redirect("student-detail", pk=student.pk)
    else:
        form = StudentEnrollmentForm(school=school)

    return render(
        request,
        "students/student_enrol.html",
        {"form": form, "school": school, "title": "Enrol New Student"},
    )


@login_required
@role_required(*ALLOWED_ROLES)
def student_edit(request, pk):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    student = get_object_or_404(Student, pk=pk, school=school)

    if request.method == "POST":
        form = StudentEnrollmentForm(
            request.POST,
            request.FILES,
            school=school,
            instance=student,
        )
        if form.is_valid():
            with transaction.atomic():
                student = form.save(commit=False)
                student.school = school
                student.save()

                parent_data = {
                    "first_name": form.cleaned_data["parent_first_name"].strip(),
                    "last_name": form.cleaned_data["parent_last_name"].strip(),
                    "phone": form.cleaned_data["parent_phone"].strip(),
                    "email": form.cleaned_data.get("parent_email", "").strip(),
                    "address": form.cleaned_data.get("parent_address", "").strip(),
                }
                from .models import Parent
                parent = student.parents.filter(school=school).order_by("created_at").first()
                if parent:
                    for field, value in parent_data.items():
                        setattr(parent, field, value)
                    parent.save()
                else:
                    parent = Parent.objects.create(school=school, **parent_data)
                    parent.students.add(student)

            log_activity(
                request,
                action="UPDATE",
                module="Students",
                description=f"Updated student '{student.full_name()}'.",
            )
            messages.success(request, "Student record updated successfully.")
            return redirect("student-detail", pk=student.pk)
    else:
        form = StudentEnrollmentForm(school=school, instance=student)

    return render(
        request,
        "students/student_enrol.html",
        {"form": form, "school": school, "student": student, "title": "Edit Student"},
    )


@login_required
@role_required(*ALLOWED_ROLES)
def student_detail(request, pk):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(
        Student.objects.prefetch_related("parents"),
        pk=pk,
        school=school,
    )
    return render(request, "students/student_detail.html", {"student": student})
