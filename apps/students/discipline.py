from django.db import transaction
from django.utils import timezone

from .models import (
    DisciplineHistory,
)


# ==========================================================
# SUSPEND STUDENT
# ==========================================================

@transaction.atomic
def suspend_student(
    student,
    disciplined_by=None,
    reason="OTHER",
    remarks="",
    start_date=None,
    end_date=None,
):
    """
    Suspend a student.
    Returns:
        (success, message)
    """

    if student.status == "EXPELLED":
        return False, "Expelled students cannot be suspended."

    if student.status == "SUSPENDED":
        return False, "Student is already suspended."

    if student.status == "WITHDRAWN":
        return False, "Withdrawn students cannot be suspended."

    if student.is_graduated:
        return False, "Graduated students cannot be suspended."

    if start_date is None:
        start_date = timezone.now().date()

    student.status = "SUSPENDED"
    student.suspension_start = start_date
    student.suspension_end = end_date
    student.discipline_reason = reason

    student.save(
        update_fields=[
            "status",
            "suspension_start",
            "suspension_end",
            "discipline_reason",
        ]
    )

    DisciplineHistory.objects.create(
        school=student.school,
        student=student,
        action="SUSPENSION",
        from_class=student.current_class,
        from_session=student.current_session,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        remarks=remarks,
        disciplined_by=disciplined_by,
    )

    return (
        True,
        f"{student.full_name()} suspended successfully.",
    )


# ==========================================================
# REINSTATE STUDENT
# ==========================================================

@transaction.atomic
def reinstate_student_from_suspension(
    history,
    reinstated_by=None,
):
    """
    Reinstate a suspended student.
    """

    if history.action != "SUSPENSION":
        return (
            False,
            "This record is not a suspension.",
        )

    if history.revoked:
        return (
            False,
            "Student has already been reinstated.",
        )

    student = history.student

    if student.status != "SUSPENDED":
        return (
            False,
            "Student is not currently suspended.",
        )

    student.status = "ACTIVE"
    student.suspension_start = None
    student.suspension_end = None
    student.discipline_reason = ""

    student.save(
        update_fields=[
            "status",
            "suspension_start",
            "suspension_end",
            "discipline_reason",
        ]
    )

    history.revoked = True
    history.revoked_by = reinstated_by
    history.revoked_at = timezone.now()

    history.save(
        update_fields=[
            "revoked",
            "revoked_by",
            "revoked_at",
        ]
    )

    return (
        True,
        f"{student.full_name()} has been reinstated.",
    )


# ==========================================================
# EXPEL STUDENT
# ==========================================================

@transaction.atomic
def expel_student(
    student,
    disciplined_by=None,
    reason="OTHER",
    remarks="",
):
    """
    Permanently expel a student.
    """

    if student.status == "EXPELLED":
        return (
            False,
            "Student has already been expelled.",
        )

    if student.is_graduated:
        return (
            False,
            "Graduated students cannot be expelled.",
        )

    previous_class = student.current_class
    previous_session = student.current_session

    student.status = "EXPELLED"
    student.current_class = None
    student.current_session = None
    student.suspension_start = None
    student.suspension_end = None
    student.discipline_reason = reason

    student.save(
        update_fields=[
            "status",
            "current_class",
            "current_session",
            "suspension_start",
            "suspension_end",
            "discipline_reason",
        ]
    )

    DisciplineHistory.objects.create(
        school=student.school,
        student=student,
        action="EXPULSION",
        from_class=previous_class,
        from_session=previous_session,
        start_date=timezone.now().date(),
        reason=reason,
        remarks=remarks,
        disciplined_by=disciplined_by,
    )

    return (
        True,
        f"{student.full_name()} expelled successfully.",
    )
