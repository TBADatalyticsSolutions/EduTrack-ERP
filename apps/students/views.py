from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.access import role_code, teacher_class_ids
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.academics.models import SchoolClass

from .forms import GraduationForm, PromotionForm, TransferForm
from .graduation import graduate_student
from .models import Student
from .promotion import promote_student as promote_single_student
from .promotion import promote_students
from .transfer import transfer_student


ALLOWED_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")


def _user_school(request):
    profile = getattr(request.user, "profile", None)
    school = getattr(profile, "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School
        school = School.objects.filter(is_active=True).order_by("id").first()
    return school


def _student_scope(request, queryset):
    if role_code(request.user) != "TEACHER":
        return queryset
    return queryset.filter(current_class_id__in=teacher_class_ids(request.user))


@login_required
@role_required(*ALLOWED_ROLES)
def student_list(request):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    school_students = _student_scope(request, Student.objects.filter(school=school))
    students = school_students.select_related("current_class", "current_session", "current_term")
    query = request.GET.get("q", "").strip()
    if query:
        students = students.filter(
            Q(admission_number__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(other_name__icontains=query)
            | Q(current_class__name__icontains=query)
        )
    students = students.order_by("admission_number")
    context = {
        "students": students,
        "search_query": query,
        "total_students": school_students.count(),
        "active_students": school_students.filter(status="ACTIVE").count(),
        "transferred_students": school_students.filter(status="TRANSFERRED").count(),
        "graduated_students": school_students.filter(status="GRADUATED").count(),
        "withdrawn_students": school_students.filter(status="WITHDRAWN").count(),
    }
    return render(request, "students/student_list.html", context)


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")
def promotion_index(request):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    form = PromotionForm(school=school)
    preview_students = None
    preview_count = 0
    promoted = None
    selected_session = selected_term = selected_current_class = selected_next_class = None
    if request.method == "POST":
        form = PromotionForm(request.POST, school=school)
        if form.is_valid():
            selected_session = form.cleaned_data["session"]
            selected_term = form.cleaned_data["term"]
            selected_current_class = form.cleaned_data["current_class"]
            selected_next_class = form.cleaned_data["next_class"]
            eligible_students = Student.objects.filter(
                school=school,
                current_class=selected_current_class,
                current_session=selected_session,
                is_graduated=False,
                status="ACTIVE",
            ).select_related("current_class", "current_session")
            preview_students = eligible_students.order_by("last_name", "first_name")
            preview_count = preview_students.count()
            if "preview" in request.POST:
                if preview_count:
                    messages.info(request, f"{preview_count} eligible student(s) found for promotion.")
                else:
                    messages.warning(request, "There are no eligible students for the selected criteria.")
            elif "promote" in request.POST:
                if preview_count == 0:
                    messages.warning(request, "There are no eligible students to promote.")
                else:
                    try:
                        with transaction.atomic():
                            promoted = promote_students(
                                selected_current_class,
                                selected_next_class,
                                selected_session,
                                selected_term,
                                approved_by=request.user,
                            )
                        log_activity(
                            request,
                            "PROMOTION",
                            "Students",
                            f"Bulk promotion completed. {promoted} student(s) promoted from '{selected_current_class.name}' to '{selected_next_class.name}'.",
                        )
                        messages.success(request, f"{promoted} student(s) promoted successfully.")
                        return redirect("promotion")
                    except ValueError as exc:
                        messages.error(request, str(exc))
    return render(request, "students/promotion.html", {
        "form": form,
        "preview_count": preview_count,
        "preview_students": preview_students,
        "promoted": promoted,
        "selected_session": selected_session,
        "selected_term": selected_term,
        "selected_current_class": selected_current_class,
        "selected_next_class": selected_next_class,
    })


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")
def transfer_student_view(request, pk):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = TransferForm(request.POST, school=school)
        if form.is_valid():
            success, message = transfer_student(
                student=student,
                to_class=form.cleaned_data["to_class"],
                to_session=form.cleaned_data["to_session"],
                transferred_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )
            if success:
                log_activity(request, "TRANSFER", "Students", f"Transferred student '{student.full_name()}'.")
                messages.success(request, message)
                return redirect("student-list")
            messages.error(request, message)
    else:
        form = TransferForm(school=school)
    return render(request, "students/transfer_student.html", {"student": student, "form": form})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")
def graduate_student_view(request, pk):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == "POST":
        form = GraduationForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data["reason"]
            try:
                graduate_student(student, reason, graduated_by=request.user)
            except TypeError:
                graduate_student(student, reason)
            log_activity(request, "GRADUATION", "Students", f"Graduated student '{student.full_name()}'.")
            messages.success(request, "Student graduated successfully.")
            return redirect("student-list")
    else:
        form = GraduationForm()
    return render(request, "students/graduation.html", {"student": student, "form": form})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")
def bulk_graduation(request):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    form = GraduationForm()
    if request.method == "POST":
        form = GraduationForm(request.POST)
        if form.is_valid():
            try:
                count = Student.objects.filter(
                    school=school,
                    status="ACTIVE",
                    is_graduated=False,
                ).count()
                messages.info(request, f"Graduation workflow is available for {count} active student(s).")
            except Exception as exc:
                messages.error(request, f"Graduation workflow could not be prepared: {exc}")
    return render(request, "students/graduation.html", {"form": form})


@login_required
@role_required(*ALLOWED_ROLES)
def promote_student_view(request, pk):
    school = _user_school(request)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")
    student = get_object_or_404(
        Student.objects.select_related("current_class", "current_session", "school"),
        pk=pk,
        school=school,
    )
    if role_code(request.user) == "TEACHER":
        messages.error(request, "Teachers cannot promote students.")
        return redirect("student-list")
    if request.method == "POST":
        next_class_id = request.POST.get("next_class")
        if not next_class_id:
            messages.error(request, "Please select the next class.")
            return redirect("student-promote", pk=student.pk)
        next_class = get_object_or_404(SchoolClass, pk=next_class_id, school=school, is_active=True)
        if student.current_class_id == next_class.id:
            messages.error(request, "The student is already in this class.")
            return redirect("student-promote", pk=student.pk)
        try:
            promoted_student = promote_single_student(student=student, next_class=next_class, approved_by=request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("student-promote", pk=student.pk)
        log_activity(
            request,
            "PROMOTION",
            "Students",
            f"Student '{promoted_student.full_name()}' was promoted from '{student.current_class.name if student.current_class else 'Unassigned'}' to '{next_class.name}'.",
        )
        messages.success(request, f"{promoted_student.full_name()} was promoted successfully to {next_class.name}.")
        return redirect("student-list")
    next_classes = SchoolClass.objects.filter(
        school=school,
        is_active=True,
    ).exclude(pk=student.current_class_id).order_by("name")
    return render(request, "students/promote_student.html", {"student": student, "next_classes": next_classes})
