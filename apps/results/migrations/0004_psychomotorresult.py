import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0003_studentresult_report_card_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="PsychomotorResult",
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
                    "area",
                    models.CharField(
                        choices=[
                            ("HANDWRITING", "Handwriting / Fine Motor Skills"),
                            ("PRACTICAL", "Practical / Manipulative Skills"),
                            ("COORDINATION", "Physical Coordination"),
                            ("NEATNESS", "Neatness / Personal Presentation"),
                            ("PARTICIPATION", "Participation in Physical Activities"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "rating",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("EXCELLENT", "Excellent"),
                            ("VERY_GOOD", "Very Good"),
                            ("GOOD", "Good"),
                            ("FAIR", "Fair"),
                            ("NEEDS_IMPROVEMENT", "Needs Improvement"),
                        ],
                        max_length=30,
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                (
                    "student_result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="psychomotor_results",
                        to="results.studentresult",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="psychomotorresult",
            constraint=models.UniqueConstraint(
                fields=("student_result", "area"),
                name="unique_psychomotor_area_per_result",
            ),
        ),
    ]
