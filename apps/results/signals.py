from django.db.models.signals import post_save
from apps.accounts.utils import log_activity
from django.dispatch import receiver
from apps.accounts.utils import log_activity

from .models import SubjectResult
from apps.accounts.utils import log_activity
from .services import calculate_student_result
from apps.accounts.utils import log_activity


@receiver(post_save, sender=SubjectResult)
def update_result(sender, instance, **kwargs):
    calculate_student_result(instance.student_result)