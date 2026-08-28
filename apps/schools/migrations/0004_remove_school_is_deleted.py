from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0003_restore_school_is_deleted"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="school",
            name="is_deleted",
        ),
    ]
