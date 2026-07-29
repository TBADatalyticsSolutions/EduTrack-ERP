from django.db import transaction
from django.utils import timezone

from .models import (
    Student,
    WithdrawalHistory,
)


# ==========================================================
# WITHDRAW STUDENT
# ==========================================================

@transaction.atomic
def withdraw_student(
    student,
    withdrawn_by=None,
    reason="",
    remarks="",
):
    """
    Withdraw a student from the school.
    """

    if student.status == "WITHDRAWN":
        return (
            False,
            "Student has already been withdrawn.",
        )

    if student.is_graduated:
        return (
            False,
            "Graduated students cannot be withdrawn.",
        )

    previous_class = student.current_class
    previous_session = student.current_session

    student.status = "WITHDRAWN"
    student.current_class = None
    student.current_session = None

    student.save(
        update_fields=[
            "status",
            "current_class",
            "current_session",
        ]
    )

    WithdrawalHistory.objects.create(
        school=student.school,
        student=student,
        from_class=previous_class,
        from_session=previous_session,
        reason=reason,
        remarks=remarks,
        withdrawn_by=withdrawn_by,
    )

    return (
        True,
        f"{student.full_name()} has been withdrawn successfully.",
    )


# ==========================================================
# REINSTATE STUDENT
# ==========================================================

@transaction.atomic
def reinstate_student_service(
    history,
    reinstated_by=None,
):
    """
    Reinstate a withdrawn student.
    """

    if history.reinstated:
        return (
            False,
            "This withdrawal has already been reinstated.",
        )

    student = history.student

    if student.status != "WITHDRAWN":
        return (
            False,
            "Student is not currently withdrawn.",
        )

    student.status = "ACTIVE"
    student.current_class = history.from_class
    student.current_session = history.from_session

    student.save(
        update_fields=[
            "status",
            "current_class",
            "current_session",
        ]
    )

    history.reinstated = True
    history.reinstated_by = reinstated_by
    history.reinstated_date = timezone.now()

    history.save(
        update_fields=[
            "reinstated",
            "reinstated_by",
            "reinstated_date",
        ]
    )

    return (
        True,
        f"{student.full_name()} has been reinstated successfully.",
    )