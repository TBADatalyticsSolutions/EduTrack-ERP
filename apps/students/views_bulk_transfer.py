from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.academics.models import AcademicSession, SchoolClass

from .models import Student, TransferHistory


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")
def bulk_transfer_view(request):
    """Bulk transfer active students between classes within a school."""
    profile = getattr(request.user, "profile", None)
    school = getattr(profile, "school", None)
    if school is None and request.user.is_superuser:
        from apps.schools.models import School

        school = School.objects.filter(is_active=True).order_by("id").first()
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    classes = SchoolClass.objects.filter(
        school=school,
        is_active=True,
    ).order_by("name")
    sessions = AcademicSession.objects.filter(
        school=school,
        is_active=True,
    ).order_by("-is_current", "-created_at")

    if request.method == "POST":
        from_id = request.POST.get("from_class")
        to_id = request.POST.get("to_class")
        session_id = request.POST.get("academic_session")

        if not all((from_id, to_id, session_id)):
            messages.error(
                request,
                "Please select the source class, destination class, and academic session.",
            )
            return redirect("bulk-transfer")

        source = get_object_or_404(classes, pk=from_id)
        destination = get_object_or_404(classes, pk=to_id)
        session = get_object_or_404(sessions, pk=session_id)

        if source.pk == destination.pk:
            messages.error(request, "Source and destination classes cannot be the same.")
            return redirect("bulk-transfer")

        students = list(
            Student.objects.filter(
                school=school,
                current_class=source,
                current_session=session,
                status="ACTIVE",
                is_graduated=False,
            )
        )
        if not students:
            messages.warning(request, "There are no eligible students to transfer.")
            return redirect("bulk-transfer")

        with transaction.atomic():
            for student in students:
                TransferHistory.objects.create(
                    student=student,
                    school=school,
                    from_class=student.current_class,
                    to_class=destination,
                    from_session=student.current_session,
                    to_session=session,
                    transferred_by=request.user,
                    reason="Bulk class transfer",
                )
                student.current_class = destination
                student.status = "ACTIVE"
                student.save(update_fields=["current_class", "status"])

        log_activity(
            request,
            action="BULK_STUDENT_TRANSFER",
            module="Students",
            description=(
                f"Transferred {len(students)} student(s) from "
                f"{source.name} to {destination.name}."
            ),
        )
        messages.success(
            request,
            f"{len(students)} student(s) successfully transferred from "
            f"{source.name} to {destination.name}.",
        )
        return redirect("bulk-transfer")

    return render(
        request,
        "students/bulk_transfer.html",
        {"classes": classes, "sessions": sessions, "school": school},
    )
