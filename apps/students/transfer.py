from django.db import transaction

from .models import (
    Student,
    TransferHistory,
)


@transaction.atomic
def transfer_student(
    student,
    to_class,
    to_session,
    approved_by=None,
    reason="",
    remarks="",
):
    """
    Transfer a student to another class/session.

    Returns:
        (success, message)
    """

    if student.is_graduated:
        return (
            False,
            "Graduated students cannot be transferred.",
        )

    if student.current_class == to_class:
        return (
            False,
            "Student is already in the selected class.",
        )

    from_class = student.current_class
    from_session = student.current_session

    student.current_class = to_class
    student.current_session = to_session
    student.save()

    TransferHistory.objects.create(
        student=student,
        school=student.school,
        from_class=from_class,
        to_class=to_class,
        from_session=from_session,
        to_session=to_session,
        reason=reason,
        remarks=remarks,
        approved_by=approved_by,
    )

    return (
        True,
        "Student transferred successfully.",
    )