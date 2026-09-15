from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.access import role_code, teacher_class_ids
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .enrollment_forms import StudentEnrollmentForm
from .models import Student


ALLOWED_ROLES = (
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
    "TEACHER",
)


def get_user_school(request):
    school = getattr(getattr(request.user, "profile", None), "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School
        school = School.objects.filter(is_active=True).order_by("id").first()
    return school


def generate_admission_number(school):
    prefix = "EDU"
    if school.short_name:
        cleaned = "".join(ch for ch in school.short_name.upper() if ch.isalnum())
        prefix = cleaned[:8] or prefix
    year = timezone.now().year
    base = f"{prefix}/{year}/"
    last = Student.objects.filter(school=school, admission_number__startswith=base).order_by("-admission_number").values_list("admission_number", flat=True).first()
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


def _teacher_can_access(student, user):
    return role_code(user) != "TEACHER" or student.current_class_id in teacher_class_ids(user)


@login_required
@role_required(*ALLOWED_ROLES)
def student_enrol(request):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    if role_code(request.user) == "TEACHER":
        messages.error(request, "Teachers cannot enrol new students.")
        return redirect("student-list")
    if request.method == "POST":
        form = StudentEnrollmentForm(request.POST, request.FILES, school=school)
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
            log_activity(request, "CREATE", "Students", f"Enrolled student '{student.full_name()}' with admission number '{student.admission_number}'.")
            messages.success(request, f"{student.full_name()} enrolled successfully. Admission No.: {student.admission_number}")
            return redirect("student-detail", pk=student.pk)
    else:
        form = StudentEnrollmentForm(school=school)
    return render(request, "students/student_enrol.html", {"form": form, "school": school, "title": "Enrol New Student"})


@login_required
@role_required(*ALLOWED_ROLES)
def student_edit(request, pk):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(Student, pk=pk, school=school)
    if not _teacher_can_access(student, request.user):
        messages.error(request, "You can only edit students in classes assigned to you.")
        return redirect("student-list")
    if request.method == "POST":
        form = StudentEnrollmentForm(request.POST, request.FILES, school=school, instance=student)
        if role_code(request.user) == "TEACHER":
            form.fields["current_class"].queryset = form.fields["current_class"].queryset.filter(pk__in=teacher_class_ids(request.user))
        if form.is_valid():
            if role_code(request.user) == "TEACHER" and form.cleaned_data["current_class"].pk not in teacher_class_ids(request.user):
                form.add_error("current_class", "You can only assign a student to a class assigned to you.")
            else:
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
                log_activity(request, "UPDATE", "Students", f"Updated student '{student.full_name()}'.")
                messages.success(request, "Student record updated successfully.")
                return redirect("student-detail", pk=student.pk)
    else:
        form = StudentEnrollmentForm(school=school, instance=student)
        if role_code(request.user) == "TEACHER":
            form.fields["current_class"].queryset = form.fields["current_class"].queryset.filter(pk__in=teacher_class_ids(request.user))
    return render(request, "students/student_enrol.html", {"form": form, "school": school, "student": student, "title": "Edit Student"})


@login_required
@role_required(*ALLOWED_ROLES)
def student_detail(request, pk):
    school = get_user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(Student.objects.prefetch_related("parents"), pk=pk, school=school)
    if not _teacher_can_access(student, request.user):
        messages.error(request, "You can only view students in classes assigned to you.")
        return redirect("student-list")
    return render(request, "students/student_detail.html", {"student": student})
