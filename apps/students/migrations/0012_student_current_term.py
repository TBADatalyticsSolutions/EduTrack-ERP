from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0002_subject_classsubject"),
        ("students", "0011_student_discipline_reason_student_suspension_end_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="current_term",
            field=models.ForeignKey(
                blank=True,
                help_text="Current academic term for the student's enrolment.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="students",
                to="academics.term",
            ),
        ),
    ]
