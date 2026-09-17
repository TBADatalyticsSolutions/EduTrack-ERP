from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0003_seed_default_terms"),
    ]

    operations = [
        migrations.AddField(
            model_name="term",
            name="resumption_date",
            field=models.DateField(
                blank=True,
                help_text="Date students resume for this term.",
                null=True,
            ),
        ),
    ]
