from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_remove_notification_is_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
