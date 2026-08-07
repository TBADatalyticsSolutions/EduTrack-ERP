from django.contrib import admin
from apps.accounts.utils import log_activity

from .models import School
from apps.accounts.utils import log_activity


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "phone",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
    )
