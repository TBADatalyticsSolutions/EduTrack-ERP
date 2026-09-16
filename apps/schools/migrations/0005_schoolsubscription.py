from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
import uuid


def create_initial_subscriptions(apps, schema_editor):
    School = apps.get_model("schools", "School")
    SchoolSubscription = apps.get_model("schools", "SchoolSubscription")
    now = timezone.now()
    for school in School.objects.filter(is_active=True):
        SchoolSubscription.objects.get_or_create(
            school=school,
            defaults={
                "id": uuid.uuid4(),
                "plan": "STANDARD",
                "status": "ACTIVE",
                "started_at": now,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0004_remove_school_is_deleted"),
    ]

    operations = [
        migrations.CreateModel(
            name="SchoolSubscription",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "plan",
                    models.CharField(
                        choices=[
                            ("STANDARD", "Standard"),
                            ("PREMIUM", "Premium"),
                        ],
                        default="STANDARD",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("PAST_DUE", "Past Due"),
                            ("SUSPENDED", "Suspended"),
                            ("CANCELLED", "Cancelled"),
                            ("EXPIRED", "Expired"),
                        ],
                        default="ACTIVE",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                (
                    "school",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription",
                        to="schools.school",
                    ),
                ),
            ],
            options={
                "ordering": ("-started_at",),
                "indexes": [
                    models.Index(fields=["status", "school"], name="schools_sch_status_8930c9_idx"),
                ],
            },
        ),
        migrations.RunPython(create_initial_subscriptions, migrations.RunPython.noop),
    ]
