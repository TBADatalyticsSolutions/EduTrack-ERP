from django.contrib import admin

from .models import School, SchoolSubscription


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


@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "plan",
        "status",
        "started_at",
        "ends_at",
    )
    list_filter = ("status", "plan")
    search_fields = ("school__name", "school__email")
    autocomplete_fields = ("school",)
