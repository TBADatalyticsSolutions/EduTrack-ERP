from django.apps import AppConfig
from apps.accounts.utils import log_activity


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
