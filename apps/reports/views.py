from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from apps.accounts.decorators import role_required
from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import SchoolClass
from apps.results.models import StudentResult

REPORT_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")

def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)

@login_required
@role_required(*REPORT_ROLES)
def dashboard(request):
    school = _school(request)
    students = Student.objects.filter(school=school) if school else Student.objects.none()
    classes = SchoolClass.objects.filter(school=school) if school else SchoolClass.objects.none()
    results = StudentResult.objects.filter(school=school) if school else StudentResult.objects.none()
    return render(request, "reports/dashboard.html", {"school": school, "student_count": students.count(), "class_count": classes.count(), "result_count": results.count()})

@login_required
@role_required(*REPORT_ROLES)
def student_report(request, pk):
    result = get_object_or_404(StudentResult.objects.select_related("student", "session", "term", "school_class").prefetch_related("subjects"), pk=pk, school=_school(request))
    return render(request, "reports/student_report.html", {"result": result})

@login_required
@role_required(*REPORT_ROLES)
def class_report(request, pk):
    school = _school(request)
    school_class = get_object_or_404(SchoolClass, pk=pk, school=school)
    results = StudentResult.objects.filter(school=school, school_class=school_class).select_related("student", "session", "term").order_by("student__last_name", "student__first_name")
    return render(request, "reports/class_report.html", {"school_class": school_class, "results": results})

@login_required
@role_required(*REPORT_ROLES)
def result_report(request, pk):
    result = get_object_or_404(StudentResult.objects.select_related("student", "session", "term", "school_class").prefetch_related("subjects"), pk=pk, school=_school(request))
    return render(request, "reports/result_report.html", {"result": result})
