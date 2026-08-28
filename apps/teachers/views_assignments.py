from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .assignment_forms import TeacherSubjectForm
from .models import Teacher, TeacherSubject


TEACHER_ROLES = (
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)


def _user_school(request):
    if request.user.is_superuser:
        return None
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "school", None)


@login_required
@role_required(*TEACHER_ROLES)
def teacher_assignments(request, pk):
    school = _user_school(request)
    filters = {"pk": pk}
    if school:
        filters["school"] = school
    teacher = get_object_or_404(Teacher, **filters)

    assignments = TeacherSubject.objects.filter(teacher=teacher).select_related(
        "subject", "school_class"
    ).order_by("school_class__name", "subject__name")

    if request.method == "POST":
        form = TeacherSubjectForm(request.POST, teacher=teacher)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = teacher
            assignment.save()
            log_activity(
                request,
                action="CREATE",
                module="Teachers",
                description=(
                    f"Assigned {assignment.subject} to {teacher.first_name} "
                    f"{teacher.last_name} for {assignment.school_class}"
                ),
            )
            messages.success(request, "Subject and class assigned successfully.")
            return redirect("teachers:assignments", pk=teacher.pk)
    else:
        form = TeacherSubjectForm(teacher=teacher)

    return render(
        request,
        "teachers/assignments.html",
        {"teacher": teacher, "assignments": assignments, "form": form},
    )


@login_required
@role_required(*TEACHER_ROLES)
def teacher_remove_assignment(request, pk):
    school = _user_school(request)
    filters = {"pk": pk}
    if school:
        filters["teacher__school"] = school
    assignment = get_object_or_404(
        TeacherSubject.objects.select_related("teacher", "subject", "school_class"),
        **filters,
    )
    teacher_pk = assignment.teacher.pk

    if request.method == "POST":
        description = (
            f"Removed {assignment.subject} from {assignment.teacher.first_name} "
            f"{assignment.teacher.last_name} for {assignment.school_class}"
        )
        assignment.delete()
        log_activity(
            request,
            action="DELETE",
            module="Teachers",
            description=description,
        )
        messages.success(request, "Teacher assignment removed successfully.")
        return redirect("teachers:assignments", pk=teacher_pk)

    return render(
        request,
        "teachers/remove_assignment.html",
        {"assignment": assignment},
    )
