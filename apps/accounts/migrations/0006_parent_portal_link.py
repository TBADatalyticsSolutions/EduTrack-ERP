from django.db import migrations, models
import django.db.models.deletion


def link_existing_parent_accounts(apps, schema_editor):
    Parent = apps.get_model("students", "Parent")
    UserProfile = apps.get_model("accounts", "UserProfile")
    ParentPortalLink = apps.get_model("accounts", "ParentPortalLink")

    number = 1
    parents = Parent.objects.all().order_by("created_at", "id")

    for parent in parents:
        parent_id = f"PAR{number:04d}"
        profile = UserProfile.objects.filter(
            parent_id=parent_id,
            role__code="PARENT",
        ).select_related("user").first()
        if profile is None:
            continue

        ParentPortalLink.objects.get_or_create(
            parent_id=parent.pk,
            defaults={"user_id": profile.user_id},
        )
        number += 1


def unlink_existing_parent_accounts(apps, schema_editor):
    ParentPortalLink = apps.get_model("accounts", "ParentPortalLink")
    ParentPortalLink.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_parent_portal_id"),
        ("students", "0013_student_current_term"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParentPortalLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "parent",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="portal_link",
                        to="students.parent",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parent_portal_link",
                        to="auth.user",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            link_existing_parent_accounts,
            reverse_code=unlink_existing_parent_accounts,
        ),
    ]
