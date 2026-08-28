from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0002_remove_school_is_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="school",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
