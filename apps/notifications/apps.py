from django.apps import AppConfig
from apps.accounts.utils import log_activity


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
