from django.db import transaction
from django.utils import timezone

from .models import GraduationHistory


@transaction.atomic
def graduate_student(student, reason="", graduated_by=None):
    """Graduate one student and create an auditable graduation record."""
    if student.is_graduated:
        return False
    if student.status == "WITHDRAWN":
        raise ValueError("Withdrawn students cannot be graduated.")
    if student.status == "EXPELLED":
        raise ValueError("Expelled students cannot be graduated.")

    graduation_date = timezone.now().date()
    academic_session = (
        student.current_session.name if student.current_session else ""
    )
    graduated_from = student.current_class

    student.is_graduated = True
    student.status = "GRADUATED"
    student.graduation_date = graduation_date
    student.graduation_session = academic_session
    student.graduation_reason = reason.strip()
    student.current_class = None
    student.current_session = None
    student.current_term = None
    student.save(
        update_fields=[
            "is_graduated",
            "status",
            "graduation_date",
            "graduation_session",
            "graduation_reason",
            "current_class",
            "current_session",
            "current_term",
        ]
    )

    GraduationHistory.objects.create(
        student=student,
        school=student.school,
        graduated_from=graduated_from,
        academic_session=academic_session,
        graduation_date=graduation_date,
        graduated_by=graduated_by,
        remarks=reason.strip(),
    )
    return True
