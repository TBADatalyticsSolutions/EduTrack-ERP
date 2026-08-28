from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import TeacherForm
from .models import Teacher


TEACHER_ROLES = (
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)


def _user_school(request):
    if request.user.is_superuser:
        return School.objects.first()
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "school", None)


@login_required
@role_required(*TEACHER_ROLES)
def teacher_dashboard(request):
    school = _user_school(request)
    teachers = Teacher.objects.select_related("department", "school")
    if school:
        teachers = teachers.filter(school=school)

    context = {
        "teachers": teachers,
        "total_teachers": teachers.count(),
        "full_time": teachers.filter(employment_status="FULL_TIME").count(),
        "part_time": teachers.filter(employment_status="PART_TIME").count(),
        "contract": teachers.filter(employment_status="CONTRACT").count(),
        "class_teachers": teachers.filter(is_class_teacher=True).count(),
    }
    return render(request, "teachers/dashboard.html", context)


@login_required
@role_required(*TEACHER_ROLES)
def teacher_list(request):
    school = _user_school(request)
    teachers = Teacher.objects.select_related("department", "school")
    if school:
        teachers = teachers.filter(school=school)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        teachers = teachers.filter(
            Q(employee_id__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )
    if status:
        teachers = teachers.filter(employment_status=status)

    return render(
        request,
        "teachers/list.html",
        {"teachers": teachers, "query": query, "status": status},
    )


@login_required
@role_required(*TEACHER_ROLES)
def teacher_create(request):
    school = _user_school(request)
    if school is None:
        messages.error(request, "No school is assigned to your account.")
        return redirect("teachers:dashboard")

    if request.method == "POST":
        form = TeacherForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.school = school
            teacher.save()
            log_activity(
                request,
                action="CREATE",
                module="Teachers",
                description=f"Created teacher {teacher.employee_id} - {teacher.first_name} {teacher.last_name}",
            )
            messages.success(request, "Teacher added successfully.")
            return redirect("teachers:detail", pk=teacher.pk)
    else:
        form = TeacherForm(school=school)

    return render(
        request,
        "teachers/form.html",
        {"form": form, "title": "Add Teacher", "submit_label": "Add Teacher"},
    )


@login_required
@role_required(*TEACHER_ROLES)
def teacher_detail(request, pk):
    school = _user_school(request)
    filters = {"pk": pk}
    if school:
        filters["school"] = school
    teacher = get_object_or_404(
        Teacher.objects.select_related("school", "department"),
        **filters,
    )
    return render(request, "teachers/detail.html", {"teacher": teacher})


@login_required
@role_required(*TEACHER_ROLES)
def teacher_edit(request, pk):
    school = _user_school(request)
    filters = {"pk": pk}
    if school:
        filters["school"] = school
    teacher = get_object_or_404(Teacher, **filters)

    if request.method == "POST":
        form = TeacherForm(
            request.POST,
            request.FILES,
            instance=teacher,
            school=school,
        )
        if form.is_valid():
            teacher = form.save()
            log_activity(
                request,
                action="UPDATE",
                module="Teachers",
                description=f"Updated teacher {teacher.employee_id} - {teacher.first_name} {teacher.last_name}",
            )
            messages.success(request, "Teacher details updated successfully.")
            return redirect("teachers:detail", pk=teacher.pk)
    else:
        form = TeacherForm(instance=teacher, school=school)

    return render(
        request,
        "teachers/form.html",
        {"form": form, "title": "Edit Teacher", "submit_label": "Save Changes", "teacher": teacher},
    )
