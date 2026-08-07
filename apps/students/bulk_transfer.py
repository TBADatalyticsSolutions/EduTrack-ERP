from django.db import transaction
from apps.accounts.utils import log_activity

from .models import (
from apps.accounts.utils import log_activity
    Student,
    TransferHistory,
)


def bulk_transfer_students(
    from_class,
    to_class,
    to_session,
    transferred_by,
    reason="Bulk Transfer",
    remarks="",
):
    """
    Transfer all active students from one class
    to another class and academic session.

    Returns:
        tuple:
            transferred (int)
            skipped (int)
    """

    students = Student.objects.filter(
        current_class=from_class,
        status="ACTIVE",
        is_graduated=False,
    ).select_related(
        "school",
        "current_class",
        "current_session",
    )

    transferred = 0
    skipped = 0

    with transaction.atomic():

        for student in students:

            # Skip students already in the destination
            if (
                student.current_class == to_class
                and student.current_session == to_session
            ):
                skipped += 1
                continue

            previous_class = student.current_class
            previous_session = student.current_session

            # Update student record
            student.current_class = to_class
            student.current_session = to_session
            student.status = "ACTIVE"

            student.save(
                update_fields=[
                    "current_class",
                    "current_session",
                    "status",
                ]
            )

            # Create audit history
            TransferHistory.objects.create(
                school=student.school,
                student=student,
                from_class=previous_class,
                to_class=to_class,
                from_session=previous_session,
                to_session=to_session,
                transferred_by=transferred_by,
                reason=reason,
                remarks=remarks,
            )

            transferred += 1

    return transferred, skipped