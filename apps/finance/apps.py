from django.apps import AppConfig
from apps.accounts.utils import log_activity


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"
