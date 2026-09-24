from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from apps.accounts.access import parent_students, role_code, student_for_user
from apps.results.models import StudentResult
from apps.schools.models import SchoolSubscription


def _student_scope(request):
    role = role_code(request.user)
    if role == "STUDENT":
        return student_for_user(request.user), role
    if role == "PARENT":
        students = parent_students(request.user)
        requested_id = request.GET.get("student")
        if requested_id:
            return students.filter(pk=requested_id).first(), role
        return students.first(), role
    return None, role


def _transcript_results(student):
    return list(
        StudentResult.objects.filter(
            school=student.school,
            student=student,
            published=True,
        )
        .select_related("session", "term", "school_class")
        .prefetch_related("subjects__subject")
        .order_by("session__name", "term__name", "created_at")
    )


def _transcript_context(request, student, role):
    results = _transcript_results(student)
    overall_average = (
        sum((result.average for result in results), Decimal("0")) / len(results)
        if results
        else Decimal("0")
    )
    return {
        "portal_role": "Student" if role == "STUDENT" else "Parent",
        "student": student,
        "students": parent_students(request.user) if role == "PARENT" else [student],
        "results": results,
        "published_count": len(results),
        "subject_count": sum(result.subjects.count() for result in results),
        "overall_average": overall_average,
    }


@login_required
def portal_transcript(request):
    role = role_code(request.user)
    if role not in {"STUDENT", "PARENT"}:
        return redirect("profile")

    school = getattr(getattr(request.user, "profile", None), "school", None)
    subscription = SchoolSubscription.objects.filter(school=school).first() if school else None
    if not school or not subscription or subscription.status != "ACTIVE":
        return render(
            request,
            "accounts/portal_transcript.html",
            {"error": "Your school's EduTrack subscription is not active."},
            status=403,
        )

    student, role = _student_scope(request)
    if not student or student.school_id != school.id:
        return render(
            request,
            "accounts/portal_transcript.html",
            {"error": "Your portal account is not linked to an eligible student record."},
            status=403,
        )

    return render(
        request,
        "accounts/portal_transcript.html",
        _transcript_context(request, student, role),
    )


@login_required
def portal_transcript_pdf(request):
    from apps.accounts.pdf import render_pdf

    role = role_code(request.user)
    if role not in {"STUDENT", "PARENT"}:
        return redirect("profile")

    school = getattr(getattr(request.user, "profile", None), "school", None)
    subscription = SchoolSubscription.objects.filter(school=school).first() if school else None
    if not school or not subscription or subscription.status != "ACTIVE":
        return HttpResponse("Your school's EduTrack subscription is not active.", status=403)

    student, role = _student_scope(request)
    if not student or student.school_id != school.id:
        return HttpResponse("Transcript student not found.", status=404)

    context = _transcript_context(request, student, role)
    html = render_to_string("accounts/portal_transcript_pdf.html", context, request=request)
    pdf = render_pdf(html, base_url=settings.BASE_DIR)
    filename = f"{student.admission_number}-academic-transcript.pdf".replace("/", "-")
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
