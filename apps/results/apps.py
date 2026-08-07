from django.apps import AppConfig
from apps.accounts.utils import log_activity


class ResultsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.results"

    def ready(self):
        import apps.results.signals