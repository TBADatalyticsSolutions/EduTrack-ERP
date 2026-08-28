from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School
from .forms import AssessmentTypeForm, GradeSettingForm, StudentResultForm, SubjectResultForm
from .models import AssessmentType, GradeSetting, StudentResult, SubjectResult
from .services import calculate_student_result

ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")

def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)

@login_required
@role_required(*ROLES)
def dashboard(request):
    school = _school(request)
    results = StudentResult.objects.filter(school=school).select_related("student", "session", "term", "school_class") if school else StudentResult.objects.none()
    return render(request, "results/dashboard.html", {"school": school, "result_count": results.count(), "published_count": results.filter(published=True).count(), "pending_count": results.filter(published=False).count(), "recent_results": results.order_by("-created_at")[:10]})

@login_required
@role_required(*ROLES)
def result_list(request):
    school = _school(request)
    results = StudentResult.objects.filter(school=school).select_related("student", "session", "term", "school_class") if school else StudentResult.objects.none()
    return render(request, "results/list.html", {"results": results})

@login_required
@role_required(*ROLES)
def result_create(request):
    school = _school(request)
    form = StudentResultForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and school:
        result = form.save(commit=False); result.school = school; result.save()
        log_activity(request, "CREATE", "Results", f"Created result for {result.student}")
        messages.success(request, "Result record created successfully.")
        return redirect("results:detail", pk=result.pk)
    return render(request, "results/form.html", {"form": form, "title": "Create Result"})

@login_required
@role_required(*ROLES)
def result_detail(request, pk):
    result = get_object_or_404(StudentResult.objects.prefetch_related("subjects"), pk=pk, school=_school(request))
    form = SubjectResultForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subject = form.save(commit=False); subject.student_result = result; subject.save()
        calculate_student_result(result)
        messages.success(request, "Subject score saved and result recalculated.")
        return redirect("results:detail", pk=result.pk)
    return render(request, "results/detail.html", {"result": result, "form": form})

@login_required
@role_required(*ROLES)
def result_publish(request, pk):
    result = get_object_or_404(StudentResult, pk=pk, school=_school(request))
    result.published = True; result.save(update_fields=["published"])
    log_activity(request, "UPDATE", "Results", f"Published result for {result.student}")
    messages.success(request, "Result published successfully.")
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
                obj = form.save(commit=False); obj.school = school; obj.save(); messages.success(request, "Assessment type saved.")
        else:
            form = GradeSettingForm(request.POST)
            if form.is_valid() and school:
                obj = form.save(commit=False); obj.school = school; obj.save(); messages.success(request, "Grade setting saved.")
        return redirect("results:settings")
    return render(request, "results/settings.html", {"assessment_form": AssessmentTypeForm(), "grade_form": GradeSettingForm(), "assessment_types": assessment_types, "grades": grades})
