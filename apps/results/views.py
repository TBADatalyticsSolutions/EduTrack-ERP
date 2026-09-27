from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.access import role_code, teacher_can_access_class, teacher_class_ids
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.academics.models import SchoolClass, Subject
from apps.schools.models import School
from apps.students.models import Student

from .forms import (
    AssessmentTypeForm,
    GradeSettingForm,
    PsychomotorResultFormSet,
    StudentResultForm,
    SubjectResultForm,
)
from .models import AssessmentType, GradeSetting, PsychomotorResult, StudentResult, SubjectResult
from .services import calculate_student_result


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")


def _school(request):
    profile_school = getattr(getattr(request.user, "profile", None), "school", None)
    if profile_school is not None:
        return profile_school
    if request.user.is_superuser:
        return School.objects.order_by("name").first()
    return None


def _teacher_scope(request, queryset):
    if role_code(request.user) != "TEACHER":
        return queryset
    return queryset.filter(school_class_id__in=teacher_class_ids(request.user))


@login_required
@role_required(*ROLES)
def dashboard(request):
    school = _school(request)
    results = StudentResult.objects.filter(school=school).select_related(
        "student", "session", "term", "school_class"
    ) if school else StudentResult.objects.none()
    results = _teacher_scope(request, results)
    return render(
        request,
        "results/dashboard.html",
        {
            "school": school,
            "result_count": results.count(),
            "published_count": results.filter(published=True).count(),
            "pending_count": results.filter(published=False).count(),
            "recent_results": results.order_by("-created_at")[:10],
        },
    )


@login_required
@role_required(*ROLES)
def result_list(request):
    school = _school(request)
    results = StudentResult.objects.filter(school=school).select_related(
        "student", "session", "term", "school_class"
    ) if school else StudentResult.objects.none()
    results = _teacher_scope(request, results)
    return render(request, "results/list.html", {"results": results})


@login_required
@role_required(*ROLES)
def result_create(request):
    school = _school(request)
    form = StudentResultForm(request.POST or None)
    if role_code(request.user) == "TEACHER":
        class_ids = teacher_class_ids(request.user)
        form.fields["school_class"].queryset = SchoolClass.objects.filter(
            school=school, pk__in=class_ids
        ).order_by("name")
        form.fields["student"].queryset = Student.objects.filter(
            school=school, current_class_id__in=class_ids
        ).order_by("last_name", "first_name")
    if request.method == "POST" and form.is_valid() and school:
        result = form.save(commit=False)
        result.school = school
        if role_code(request.user) == "TEACHER" and not teacher_can_access_class(request.user, result.school_class):
            messages.error(request, "You can only create results for classes assigned to you.")
            return redirect("results:list")
        if result.student.school_id != school.id or result.student.current_class_id != result.school_class_id:
            form.add_error("student", "The student must belong to the selected class.")
        else:
            result.save()
            log_activity(request, "CREATE", "Results", f"Created result for {result.student}")
            messages.success(request, "Result record created successfully.")
            return redirect("results:detail", pk=result.pk)
    return render(request, "results/form.html", {"form": form, "title": "Create Result"})


@login_required
@role_required(*ROLES)
def psychomotor_update(request, pk):
    result = get_object_or_404(
        StudentResult,
        pk=pk,
        school=_school(request),
    )

    if result.published:
        messages.error(
            request,
            "Published results are locked. Unpublish the result before editing psychomotor assessment.",
        )
        return redirect("results:detail", pk=result.pk)

    if role_code(request.user) == "TEACHER" and not teacher_can_access_class(
        request.user, result.school_class
    ):
        messages.error(request, "You can only edit results for classes assigned to you.")
        return redirect("results:list")

    for area, _label in PsychomotorResult.AREA_CHOICES:
        PsychomotorResult.objects.get_or_create(
            student_result=result,
            area=area,
        )

    formset = PsychomotorResultFormSet(
        request.POST,
        queryset=PsychomotorResult.objects.filter(
            student_result=result
        ).order_by("id"),
    )

    if formset.is_valid():
        formset.save()
        messages.success(request, "Psychomotor assessment saved successfully.")
    else:
        messages.error(request, "Please correct the psychomotor assessment fields and try again.")

    return redirect("results:detail", pk=result.pk)


@login_required
@role_required(*ROLES)
def subject_edit(request, pk):
    subject_result = get_object_or_404(
        SubjectResult.objects.select_related("student_result", "student_result__school_class"),
        pk=pk,
        student_result__school=_school(request),
    )
    result = subject_result.student_result

    if role_code(request.user) not in ("SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"):
        messages.error(request, "You do not have permission to edit subject scores.")
        return redirect("results:detail", pk=result.pk)
    if role_code(request.user) == "TEACHER" and not teacher_can_access_class(
        request.user, result.school_class
    ):
        messages.error(request, "You can only edit results for classes assigned to you.")
        return redirect("results:list")
    if result.published:
        messages.error(request, "Published results are locked. Unpublish the result before editing.")
        return redirect("results:detail", pk=result.pk)

    form = SubjectResultForm(request.POST or None, instance=subject_result)
    if role_code(request.user) == "TEACHER":
        form.fields["subject"].queryset = Subject.objects.filter(
            school=result.school,
            classes__school_class_id=result.school_class_id,
        ).distinct().order_by("name")

    if request.method == "POST" and form.is_valid():
        form.save()
        calculate_student_result(result)
        log_activity(request, "UPDATE", "Results", f"Updated {result.student} - {subject_result.subject}")
        messages.success(request, "Subject score updated and result recalculated.")
        return redirect("results:detail", pk=result.pk)

    return render(
        request,
        "results/subject_form.html",
        {"form": form, "result": result, "subject_result": subject_result},
    )


@login_required
@role_required(*ROLES)
def result_edit(request, pk):
    result = get_object_or_404(
        StudentResult,
        pk=pk,
        school=_school(request),
    )
    if role_code(request.user) not in ("SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"):
        messages.error(request, "You do not have permission to edit results.")
        return redirect("results:detail", pk=result.pk)
    if role_code(request.user) == "TEACHER" and not teacher_can_access_class(
        request.user, result.school_class
    ):
        messages.error(request, "You can only edit results for classes assigned to you.")
        return redirect("results:list")
    if result.published:
        messages.error(request, "Published results are locked. Unpublish the result before editing.")
        return redirect("results:detail", pk=result.pk)

    form = StudentResultForm(request.POST or None, instance=result)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.school = result.school
        updated.student = result.student
        updated.session = result.session
        updated.term = result.term
        updated.school_class = result.school_class
        updated.save()
        messages.success(request, "Result details updated successfully.")
        return redirect("results:detail", pk=result.pk)

    return render(request, "results/form.html", {"form": form, "title": "Edit Result"})


@login_required
@role_required(*ROLES)
def result_detail(request, pk):
    result = get_object_or_404(
        StudentResult.objects.prefetch_related("subjects", "psychomotor_results"),
        pk=pk,
        school=_school(request),
    )
    if role_code(request.user) == "TEACHER" and not teacher_can_access_class(request.user, result.school_class):
        messages.error(request, "You can only access results for classes assigned to you.")
        return redirect("results:list")

    for area, _label in PsychomotorResult.AREA_CHOICES:
        PsychomotorResult.objects.get_or_create(
            student_result=result,
            area=area,
        )

    form = SubjectResultForm(request.POST or None)
    psychomotor_formset = PsychomotorResultFormSet(
        queryset=PsychomotorResult.objects.filter(
            student_result=result
        ).order_by("id"),
    )
    if role_code(request.user) == "TEACHER":
        form.fields["subject"].queryset = Subject.objects.filter(
            school=result.school,
            classes__school_class_id__in=teacher_class_ids(request.user),
        ).distinct().order_by("name")

    if request.method == "POST" and form.is_valid():
        subject = form.save(commit=False)
        if role_code(request.user) == "TEACHER" and not subject.subject.classes.filter(
            school_class=result.school_class
        ).exists():
            form.add_error("subject", "You can only edit subjects assigned to this class.")
        else:
            subject.student_result = result
            subject.save()
            calculate_student_result(result)
            messages.success(request, "Subject score saved and result recalculated.")
            return redirect("results:detail", pk=result.pk)
    return render(request, "results/detail.html", {"result": result, "form": form, "psychomotor_formset": psychomotor_formset})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")
def result_publish(request, pk):
    result = get_object_or_404(StudentResult, pk=pk, school=_school(request))
    result.published = True
    result.save(update_fields=["published"])
    log_activity(request, "UPDATE", "Results", f"Published result for {result.student}")
    messages.success(request, "Result published successfully.")
    return redirect("results:detail", pk=result.pk)


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")
def result_unpublish(request, pk):
    result = get_object_or_404(StudentResult, pk=pk, school=_school(request))

    if role_code(request.user) == "TEACHER" and not teacher_can_access_class(
        request.user, result.school_class
    ):
        messages.error(request, "You can only unpublish results for classes assigned to you.")
        return redirect("results:list")

    result.published = False
    result.save(update_fields=["published"])
    log_activity(request, "UPDATE", "Results", f"Unpublished result for {result.student}")
    messages.success(
        request,
        "Result unpublished. You can now edit the result before publishing it again.",
    )
    return redirect("results:detail", pk=result.pk)


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")
def settings(request):
    school = _school(request)
    assessment_types = AssessmentType.objects.filter(school=school) if school else AssessmentType.objects.none()
    grades = GradeSetting.objects.filter(school=school) if school else GradeSetting.objects.none()
    if request.method == "POST":
        if request.POST.get("form_type") == "assessment":
            form = AssessmentTypeForm(request.POST)
            if form.is_valid() and school:
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, "Assessment type saved.")
        else:
            form = GradeSettingForm(request.POST)
            if form.is_valid() and school:
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                messages.success(request, "Grade setting saved.")
        return redirect("results:settings")
    return render(
        request,
        "results/settings.html",
        {
            "assessment_form": AssessmentTypeForm(),
            "grade_form": GradeSettingForm(),
            "assessment_types": assessment_types,
            "grades": grades,
        },
    )
