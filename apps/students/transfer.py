from django.db import transaction

from .models import TransferHistory


@transaction.atomic
def transfer_student(
    student,
    to_class,
    to_session,
    transferred_by=None,
    reason="",
    remarks="",
):
    """Transfer a student to another class/session with an audit record."""
    if student.is_graduated:
        return False, "Graduated students cannot be transferred."
    if student.status in {"WITHDRAWN", "EXPELLED"}:
        return False, "This student is not eligible for transfer."
    if to_class.school_id != student.school_id:
        return False, "The destination class must belong to the student's school."
    if to_session.school_id != student.school_id:
        return False, "The destination session must belong to the student's school."
    if student.current_class_id == to_class.pk and student.current_session_id == to_session.pk:
        return False, "Student is already in the selected class and session."

    from_class = student.current_class
    from_session = student.current_session
    student.current_class = to_class
    student.current_session = to_session
    student.status = "ACTIVE"

    destination_term = to_session.terms.filter(is_active=True, is_current=True).order_by(
        "-created_at"
    ).first()
    if destination_term:
        student.current_term = destination_term

    student.save(update_fields=["current_class", "current_session", "current_term", "status"])

    TransferHistory.objects.create(
        student=student,
        school=student.school,
        from_class=from_class,
        to_class=to_class,
        from_session=from_session,
        to_session=to_session,
        reason=reason.strip(),
        remarks=remarks.strip(),
        transferred_by=transferred_by,
    )
    return True, "Student transferred successfully."
