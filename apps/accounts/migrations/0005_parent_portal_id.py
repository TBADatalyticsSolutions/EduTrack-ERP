from django.db import migrations, models


PARENT_ID_PREFIX = "PAR"


def migrate_parent_portal_ids(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")
    Parent = apps.get_model("students", "Parent")

    number = 1
    parents = Parent.objects.all().order_by("created_at", "id")

    for parent in parents:
        profile = UserProfile.objects.filter(
            user__username=str(parent.pk),
            role__code="PARENT",
        ).first()
        if profile is None:
            continue

        parent_id = f"{PARENT_ID_PREFIX}{number:04d}"
        while UserProfile.objects.filter(parent_id=parent_id).exclude(pk=profile.pk).exists():
            number += 1
            parent_id = f"{PARENT_ID_PREFIX}{number:04d}"

        profile.parent_id = parent_id
        profile.save(update_fields=["parent_id"])

        user = profile.user
        user.username = parent_id
        user.save(update_fields=["username"])
        number += 1


def reverse_parent_portal_ids(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")

    for profile in UserProfile.objects.filter(
        role__code="PARENT",
    ).exclude(parent_id=""):
        user = profile.user
        # Parent UUIDs are not recoverable from the new username alone.
        # Leave the username unchanged on rollback and only clear the mapping.
        profile.parent_id = None
        profile.save(update_fields=["parent_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_provision_portal_accounts"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="parent_id",
            field=models.CharField(
                blank=True,
                help_text="Human-readable portal ID for parent accounts.",
                max_length=30,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(
            migrate_parent_portal_ids,
            reverse_code=reverse_parent_portal_ids,
        ),
    ]
