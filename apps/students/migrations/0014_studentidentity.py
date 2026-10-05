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
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
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
