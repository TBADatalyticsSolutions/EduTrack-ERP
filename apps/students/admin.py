from django.contrib import admin

from .models import Student, Parent


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "first_name",
        "last_name",
        "current_class",
    )

    search_fields = (
        "admission_number",
        "first_name",
        "last_name",
    )


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone",
    )
