from django.contrib import messages
from django.shortcuts import render
from django.db import transaction

from apps.academics.models import (
    SchoolClass,
    AcademicSession,
)

from .models import Student
from .bulk_transfer import bulk_transfer_students


def bulk_transfer_view(request):
    """
    Bulk transfer active students from one class
    to another class and academic session.
    """

    classes = SchoolClass.objects.order_by("name")
    sessions = AcademicSession.objects.order_by("name")

    preview_students = None

    selected_from = None
    selected_to = None
    selected_session = None

    total_students = 0
    male_students = 0
    female_students = 0

    transferred = 0
    skipped = 0

    if request.method == "POST":

        from_class_id = request.POST.get("from_class")
        to_class_id = request.POST.get("to_class")
        session_id = request.POST.get("session")

        if from_class_id:

            selected_from = SchoolClass.objects.get(pk=from_class_id)

            preview_students = (
                Student.objects.filter(
                    current_class=selected_from,
                    status="ACTIVE",
                    is_graduated=False,
                )
                .order_by("last_name", "first_name")
            )

            total_students = preview_students.count()

            male_students = preview_students.filter(
                gender="M"
            ).count()

            female_students = preview_students.filter(
                gender="F"
            ).count()

        if "transfer" in request.POST:

            if not all([from_class_id, to_class_id, session_id]):

                messages.error(
                    request,
                    "Please complete all required fields.",
                )

            else:

                selected_to = SchoolClass.objects.get(
                    pk=to_class_id
                )

                selected_session = AcademicSession.objects.get(
                    pk=session_id
                )

                if selected_from == selected_to:

                    messages.error(
                        request,
                        "Source class and destination class cannot be the same.",
                    )

                elif total_students == 0:

                    messages.warning(
                        request,
                        "There are no eligible students to transfer.",
                    )

                else:

                    with transaction.atomic():

                        transferred, skipped = bulk_transfer_students(
                            from_class=selected_from,
                            to_class=selected_to,
                            to_session=selected_session,
                            transferred_by=request.user,
                            reason="Bulk Transfer",
                            remarks="Transferred via Bulk Transfer Module",
                        )

                    messages.success(
                        request,
                        f"Bulk transfer completed successfully. "
                        f"{transferred} student(s) transferred, "
                        f"{skipped} skipped."
                    )

                    preview_students = (
                        Student.objects.filter(
                            current_class=selected_from,
                            status="ACTIVE",
                            is_graduated=False,
                        )
                        .order_by("last_name", "first_name")
                    )

                    total_students = preview_students.count()

                    male_students = preview_students.filter(
                        gender="M"
                    ).count()

                    female_students = preview_students.filter(
                        gender="F"
                    ).count()

    return render(
        request,
        "students/bulk_transfer.html",
        {
            "classes": classes,
            "sessions": sessions,
            "preview_students": preview_students,
            "selected_from": selected_from,
            "selected_to": selected_to,
            "selected_session": selected_session,
            "total_students": total_students,
            "male_students": male_students,
            "female_students": female_students,
            "transferred": transferred,
            "skipped": skipped,
        },
    )