from django.contrib import admin

from .models import School


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