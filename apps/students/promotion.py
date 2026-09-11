from django.db import transaction
from django.utils import timezone

from .models import PromotionHistory, Student


@transaction.atomic
def promote_students(
    current_class,
    next_class,
    session,
    term,
    approved_by=None,
):
    """Promote all eligible students from one class to another."""
    if current_class.pk == next_class.pk:
        raise ValueError("The current class and next class cannot be the same.")

    if current_class.school_id != next_class.school_id:
        raise ValueError("The current and next classes must belong to the same school.")

    if session.school_id != current_class.school_id:
        raise ValueError("The academic session must belong to the selected school.")

    if term.school_id != current_class.school_id or term.session_id != session.pk:
        raise ValueError("The selected term does not belong to the selected academic session.")

    students = list(
        Student.objects.filter(
            school=current_class.school,
            current_class=current_class,
            current_session=session,
            is_graduated=False,
            status="ACTIVE",
        ).select_related("school", "current_class", "current_session")
    )

    if not students:
        return 0

    now = timezone.now()
    histories = [
        PromotionHistory(
            student=student,
            school=student.school,
            academic_session=session,
            term=term,
            from_class=current_class,
            to_class=next_class,
            action="PROMOTED",
            approved_by=approved_by,
            approved_at=now,
            remarks=(
                f"Bulk promotion from {current_class.name} "
                f"to {next_class.name}."
            ),
        )
        for student in students
    ]

    Student.objects.filter(pk__in=[student.pk for student in students]).update(
        current_class=next_class,
        current_session=session,
        current_term=term,
        status="ACTIVE",
        is_graduated=False,
    )
    PromotionHistory.objects.bulk_create(histories)
    return len(students)


@transaction.atomic
def promote_student(
    student,
    next_class,
    session=None,
    term=None,
    approved_by=None,
):
    """Promote one student and optionally record session-aware history."""
    if student.is_graduated:
        raise ValueError("A graduated student cannot be promoted.")
    if student.status != "ACTIVE":
        raise ValueError("Only active students can be promoted.")
    if student.current_class_id == next_class.pk:
        raise ValueError("Student is already in the selected class.")
    if student.school_id != next_class.school_id:
        raise ValueError("The destination class must belong to the student's school.")

    if session is not None:
        if session.school_id != student.school_id:
            raise ValueError("The academic session must belong to the student's school.")
        if term is None:
            raise ValueError("A term is required when an academic session is supplied.")
        if term.school_id != student.school_id or term.session_id != session.pk:
            raise ValueError("The selected term does not belong to the academic session.")

    old_class = student.current_class
    student.current_class = next_class
    if session is not None:
        student.current_session = session
        student.current_term = term

    student.status = "ACTIVE"
    student.save(
        update_fields=[
            "current_class",
            "current_session",
            "current_term",
            "status",
        ]
    )

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
