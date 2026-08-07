from django.contrib.auth.models import User
from apps.accounts.utils import log_activity
from django.db.models.signals import post_save
from apps.accounts.utils import log_activity
from django.dispatch import receiver
from apps.accounts.utils import log_activity

from .models import Role, UserProfile
from apps.accounts.utils import log_activity


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_superuser:
        role, _ = Role.objects.get_or_create(
            code="SUPER_ADMIN",
            defaults={
                "name": "Super Administrator",
                "description": "",
            },
        )
    else:
        role, _ = Role.objects.get_or_create(
            code="TEACHER",
            defaults={
                "name": "Teacher",
                "description": "",
            },
        )

    UserProfile.objects.create(
        user=instance,
        role=role,
    )