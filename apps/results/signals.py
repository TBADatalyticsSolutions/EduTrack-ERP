from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SubjectResult
from .services import calculate_student_result


@receiver(post_save, sender=SubjectResult)
def update_result(sender, instance, **kwargs):
    calculate_student_result(instance.student_result)
