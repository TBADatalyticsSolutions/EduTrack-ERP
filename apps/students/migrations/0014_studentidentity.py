import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0013_student_current_term"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentIdentity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("lin", models.CharField(db_index=True, help_text="Learner Identification Number (LIN).", max_length=50, unique=True)),
                (
                    "student",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="identity",
                        to="students.student",
                    ),
                ),
            ],
            options={
                "verbose_name": "Student Identity",
                "verbose_name_plural": "Student Identities",
            },
        ),
    ]
