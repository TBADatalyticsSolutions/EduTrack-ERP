from django.utils import timezone
from apps.accounts.utils import log_activity

from datetime import date
from apps.accounts.utils import log_activity
from .models import GraduationHistory
from apps.accounts.utils import log_activity

def graduate_student(student):
    """
    Graduate one student.
    """

    if student.is_graduated:
        return False

    student.is_graduated = True
    GraduationHistory.objects.create(
    student=student,
    school=student.school,
    graduated_from=student.current_class,
    graduation_date=date.today(),
    academic_session="2025/2026",
    )

    student.current_class = None

    student.graduation_date = timezone.now().date()

    student.save()

    return True