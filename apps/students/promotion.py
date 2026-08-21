from django.db import transaction
from django.utils import timezone

from .models import (
    Student,
    PromotionHistory,
)


# =====================================================
# BULK STUDENT PROMOTION
# =====================================================

@transaction.atomic
def promote_students(
    current_class,
    next_class,
    session,
    term,
    approved_by=None,
):
    """
    Promote all eligible students from one class to
    another class for a selected academic session and term.

    Promotion workflow:

        Academic Session
            ↓
        Term
            ↓
        Current Class
            ↓
        Next Class
            ↓
        Eligible Students
            ↓
        Student Update
            ↓
        Promotion History
            ↓
        Activity Log

    Parameters
    ----------
    current_class : SchoolClass
        Current class of the students.

    next_class : SchoolClass
        Destination class.

    session : AcademicSession
        Academic session into which students are being promoted.

    term : Term
        Term in which the promotion is approved.

    approved_by : User, optional
        User approving the promotion.

    Returns
    -------
    int
        Number of students promoted.

    Raises
    ------
    ValueError
        If current and next classes are the same.
    """

    # -------------------------------------------------
    # Prevent same-class promotion
    # -------------------------------------------------

    if current_class.pk == next_class.pk:
        raise ValueError(
            "The current class and next class cannot be the same."
        )

    # -------------------------------------------------
    # Identify eligible students
    #
    # Students must:
    #   - belong to current class
    #   - not be graduated
    #   - have ACTIVE status
    # -------------------------------------------------

    students = list(
        Student.objects.filter(
            current_class=current_class,
            is_graduated=False,
            status="ACTIVE",
        ).select_related(
            "school",
            "current_class",
            "current_session",
        )
    )

    if not students:
        return 0

    # -------------------------------------------------
    # Prepare promotion history records
    # -------------------------------------------------

    histories = []

    for student in students:

        histories.append(
            PromotionHistory(
                student=student,
                school=student.school,
                academic_session=session,
                term=term,
                from_class=current_class,
                to_class=next_class,
                action="PROMOTED",
                approved_by=approved_by,
                approved_at=timezone.now(),
                remarks=(
                    f"Bulk promotion from "
                    f"{current_class.name} to "
                    f"{next_class.name}."
                ),
            )
        )

    # -------------------------------------------------
    # Update students
    #
    # The selected academic session becomes the
    # student's new current session.
    # -------------------------------------------------

    Student.objects.filter(
        pk__in=[student.pk for student in students]
    ).update(
        current_class=next_class,
        current_session=session,
        status="ACTIVE",
        is_graduated=False,
    )

    # -------------------------------------------------
    # Save promotion history
    # -------------------------------------------------

    PromotionHistory.objects.bulk_create(
        histories
    )

    return len(students)


# =====================================================
# INDIVIDUAL STUDENT PROMOTION
# =====================================================

@transaction.atomic
def promote_student(
    student,
    next_class,
    session=None,
    term=None,
    approved_by=None,
):
    """
    Promote one student to another class.

    Supports both the older individual-promotion workflow
    and the new session-aware promotion workflow.
    """

    if student.is_graduated:
        raise ValueError(
            "A graduated student cannot be promoted."
        )

    if student.current_class_id == next_class.pk:
        raise ValueError(
            "Student is already in the selected class."
        )

    old_class = student.current_class

    # -------------------------------------------------
    # Update class
    # -------------------------------------------------

    student.current_class = next_class

    # -------------------------------------------------
    # Update academic session when supplied
    # -------------------------------------------------

    if session is not None:
        student.current_session = session

    student.status = "ACTIVE"

    student.save(
        update_fields=[
            "current_class",
            "current_session",
            "status",
        ]
    )

    # -------------------------------------------------
    # Create history when session + term are supplied
    # -------------------------------------------------

    if session is not None and term is not None:

        PromotionHistory.objects.create(
            student=student,
            school=student.school,
            academic_session=session,
            term=term,
            from_class=old_class,
            to_class=next_class,
            action="PROMOTED",
            approved_by=approved_by,
            approved_at=timezone.now(),
            remarks=(
                f"Individual promotion from "
                f"{old_class.name if old_class else 'Unassigned'} "
                f"to {next_class.name}."
            ),
        )

    return student