from django.apps import AppConfig


class StudentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.students"

    def ready(self):
        # Register the supplemental student identity model with Django's app registry.
        from . import student_identity  # noqa: F401
