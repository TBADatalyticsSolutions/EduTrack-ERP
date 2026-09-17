from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0002_alter_studentresult_total_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentresult",
            name="next_term_resumption",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="studentresult",
            name="principal_remark",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="studentresult",
            name="promotion_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("PROMOTED", "Promoted"),
                    ("REPEATED", "Repeated"),
                    ("GRADUATED", "Graduated"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="studentresult",
            name="teacher_remark",
            field=models.TextField(blank=True),
        ),
    ]
