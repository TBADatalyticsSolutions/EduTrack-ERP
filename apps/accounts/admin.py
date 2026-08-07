from django.contrib import admin

from .models import Role, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
    )

    search_fields = (
        "name",
        "code",
    )

    ordering = (
        "name",
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "role",
        "school",
        "phone",
        "employee_id",
        "is_school_admin",
    )

    list_filter = (
        "role",
        "school",
        "is_school_admin",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "employee_id",
    )