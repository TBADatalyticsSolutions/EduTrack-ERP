from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.academics.models import AcademicSession, SchoolClass
from apps.students.models import Student, TransferHistory


@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
)
def bulk_transfer_view(request):
    """
    Bulk transfer students from one class to another.

    Students are transferred within the selected academic session.
    """

    school = getattr(request.user, "school", None)

    if not school:
        messages.error(
            request,
            "You are not associated with a school.",
        )
        return redirect("dashboard")

    classes = SchoolClass.objects.filter(
        school=school,
        is_active=True,
    ).order_by("name")

    sessions = AcademicSession.objects.filter(
        school=school,
        is_active=True,
    ).order_by("-start_date")

    if request.method == "POST":

        selected_from = request.POST.get("from_class")
        selected_to = request.POST.get("to_class")
        session_id = request.POST.get("academic_session")

        if not selected_from or not selected_to or not session_id:
            messages.error(
                request,
                (
                    "Please select the source class, destination class, "
                    "and academic session."
                ),
            )
            return redirect("students:bulk-transfer")

        try:
            selected_from = SchoolClass.objects.get(
                pk=selected_from,
                school=school,
            )

            selected_to = SchoolClass.objects.get(
                pk=selected_to,
                school=school,
            )

            selected_session = AcademicSession.objects.get(
                pk=session_id,
                school=school,
            )

        except (
            SchoolClass.DoesNotExist,
            AcademicSession.DoesNotExist,
        ):
            messages.error(
                request,
                "Invalid class or academic session selected.",
            )
            return redirect("students:bulk-transfer")

        if selected_from == selected_to:
            messages.error(
                request,
                (
                    "Source class and destination class "
                    "cannot be the same."
                ),
            )
            return redirect("students:bulk-transfer")

        students = Student.objects.filter(
            school=school,
            current_class=selected_from,
            current_session=selected_session,
            status="ACTIVE",
        )

        total_students = students.count()

        if total_students == 0:
            messages.warning(
                request,
                "There are no eligible students to transfer.",
            )
            return redirect("students:bulk-transfer")

        transferred_count = 0

        with transaction.atomic():

            for student in students:

                old_class = student.current_class

                TransferHistory.objects.create(
                    student=student,
                    school=school,
                    from_class=old_class,
                    to_class=selected_to,
                    from_session=selected_session,
                    to_session=selected_session,
                    transferred_by=request.user,
                )

                student.current_class = selected_to

                student.save(
                    update_fields=[
                        "current_class",
                        "updated_at",
                    ]
                )

                transferred_count += 1

            log_activity(
                user=request.user,
                action="BULK_STUDENT_TRANSFER",
                description=(
                    f"Transferred {transferred_count} "
                    f"student(s) from "
                    f"{selected_from} to {selected_to}."
                ),
            )

        messages.success(
            request,
            (
                f"{transferred_count} student(s) successfully "
                f"transferred from {selected_from} to "
                f"{selected_to}."
            ),
        )

        return redirect("students:bulk-transfer")

    context = {
        "classes": classes,
        "sessions": sessions,
        "school": school,
    }

    return render(
        request,
        "students/bulk_transfer.html",
        context,
    )
