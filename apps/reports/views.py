from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Min
from django.shortcuts import get_object_or_404, render

from apps.accounts.access import role_code, teacher_class_ids
from apps.accounts.decorators import role_required
from apps.academics.models import SchoolClass
from apps.attendance.models import AttendanceRecord
from apps.results.models import StudentResult, SubjectResult
from apps.schools.models import School
from apps.students.models import Student


REPORT_ROLES = (
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
    "TEACHER",
)


def _school(request):
    profile_school = getattr(getattr(request.user, "profile", None), "school", None)
    if profile_school is not None:
        return profile_school
    if request.user.is_superuser:
        return School.objects.first()
    return None


def _teacher_class_scope(request, queryset):
    if role_code(request.user) != "TEACHER":
        return queryset
    return queryset.filter(school_class_id__in=teacher_class_ids(request.user))


def _report_context(result):
    attendance = AttendanceRecord.objects.filter(
        attendance_session__school=result.school,
        attendance_session__school_class=result.school_class,
        attendance_session__academic_session=result.session,
        attendance_session__term=result.term,
        student=result.student,
    )

    attendance_summary = {
        "total": attendance.count(),
        "present": attendance.filter(status=AttendanceRecord.PRESENT).count(),
        "absent": attendance.filter(status=AttendanceRecord.ABSENT).count(),
        "late": attendance.filter(status=AttendanceRecord.LATE).count(),
        "excused": attendance.filter(status=AttendanceRecord.EXCUSED).count(),
    }

    # Official subject statistics for this student's class, session and term.
    # Only published results are included so an unpublished score cannot alter
    # the statistics printed on an official report sheet.
    class_subject_stats = {}
    class_results = StudentResult.objects.filter(
        school=result.school,
        school_class=result.school_class,
        session=result.session,
        term=result.term,
        published=True,
    )
    subject_stats = (
        SubjectResult.objects.filter(student_result__in=class_results)
        .values("subject_id")
        .annotate(
            lowest=Min("total"),
            average=Avg("total"),
            highest=Max("total"),
        )
    )
    for row in subject_stats:
        class_subject_stats[row["subject_id"]] = {
            "lowest": row["lowest"],
            "average": row["average"],
            "highest": row["highest"],
        }

    # Position is competition ranking (1st, 2nd, 2nd, 4th...). The stored
    # position is calculated across the student's class/session/term.
    class_result_count = StudentResult.objects.filter(
        school=result.school,
        school_class=result.school_class,
        session=result.session,
        term=result.term,
    ).count()

    subject_rows = []
    for subject_result in result.subjects.all():
        subject_rows.append({
            "item": subject_result,
            "stats": class_subject_stats.get(
                subject_result.subject_id,
                {"lowest": None, "average": None, "highest": None},
            ),
        })

    return {
        "result": result,
        "attendance_summary": attendance_summary,
        "subject_rows": subject_rows,
        "class_result_count": class_result_count,
    }


@login_required
@role_required(*REPORT_ROLES)
def dashboard(request):
    school = _school(request)
    students = Student.objects.filter(school=school) if school else Student.objects.none()
    classes = SchoolClass.objects.filter(school=school) if school else SchoolClass.objects.none()
    results = StudentResult.objects.filter(school=school) if school else StudentResult.objects.none()

    if role_code(request.user) == "TEACHER":
        class_ids = teacher_class_ids(request.user)
        students = students.filter(current_class_id__in=class_ids)
        classes = classes.filter(pk__in=class_ids)
        results = results.filter(school_class_id__in=class_ids)

    return render(
        request,
        "reports/dashboard.html",
        {
            "school": school,
            "student_count": students.count(),
            "class_count": classes.count(),
            "result_count": results.count(),
        },
    )


@login_required
@role_required(*REPORT_ROLES)
def student_report(request, pk):
    results = _teacher_class_scope(
        request,
        StudentResult.objects.select_related(
            "student", "session", "term", "school_class", "school"
        ).prefetch_related("subjects"),
    )
    result = get_object_or_404(
        results,
        pk=pk,
        school=_school(request),
        published=True,
    )
    return render(
        request,
        "reports/student_report.html",
        _report_context(result),
    )


@login_required
@role_required(*REPORT_ROLES)
def class_report(request, pk):
    school = _school(request)
    classes = SchoolClass.objects.filter(school=school)
    if role_code(request.user) == "TEACHER":
        classes = classes.filter(pk__in=teacher_class_ids(request.user))
    school_class = get_object_or_404(classes, pk=pk)

    results = (
        StudentResult.objects.filter(
            school=school,
            school_class=school_class,
            published=True,
        )
        .select_related("student", "session", "term")
        .order_by("student__last_name", "student__first_name")
    )
    return render(
        request,
        "reports/class_report.html",
        {"school_class": school_class, "results": results},
    )


@login_required
@role_required(*REPORT_ROLES)
def result_report(request, pk):
    results = _teacher_class_scope(
        request,
        StudentResult.objects.select_related(
            "student", "session", "term", "school_class", "school"
        ).prefetch_related("subjects"),
    )
    result = get_object_or_404(
        results,
        pk=pk,
        school=_school(request),
        published=True,
    )
    return render(
        request,
        "reports/student_report.html",
        _report_context(result),
    )
