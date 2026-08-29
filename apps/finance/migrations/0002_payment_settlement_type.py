from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="settlement_type",
            field=models.CharField(
                choices=[
                    ("PAYMENT", "Payment"),
                    ("SCHOLARSHIP", "Scholarship / Full Waiver"),
                    ("WAIVER", "Fee Waiver / Adjustment"),
                ],
                default="PAYMENT",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CASH", "Cash"),
                    ("TRANSFER", "Bank Transfer"),
                    ("POS", "POS"),
                    ("ONLINE", "Online"),
                ],
                max_length=20,
            ),
        ),
    ]
