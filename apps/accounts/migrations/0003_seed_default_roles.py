# Seed the default roles required by EduTrack ERP.

from django.db import migrations


DEFAULT_ROLES = [
    ("SUPER_ADMIN", "Super Administrator"),
    ("SCHOOL_ADMIN", "School Administrator"),
    ("PRINCIPAL", "Principal"),
    ("VICE_PRINCIPAL", "Vice Principal"),
    ("REGISTRAR", "Registrar"),
    ("TEACHER", "Teacher"),
    ("ACCOUNTANT", "Accountant"),
    ("LIBRARIAN", "Librarian"),
    ("PARENT", "Parent"),
    ("STUDENT", "Student"),
]


def seed_default_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for code, name in DEFAULT_ROLES:
        Role.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": "",
            },
        )


def unseed_default_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(
        code__in=[code for code, _ in DEFAULT_ROLES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_userprofile_role_activitylog"),
    ]

    operations = [
        migrations.RunPython(
            seed_default_roles,
            reverse_code=unseed_default_roles,
        ),
    ]
