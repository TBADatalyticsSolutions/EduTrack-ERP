from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0002_payment_settlement_type"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="feecategory",
            constraint=models.UniqueConstraint(
                fields=("school", "name"),
                name="finance_fee_category_school_name_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="feestructure",
            constraint=models.UniqueConstraint(
                fields=("school", "session", "term", "school_class", "fee_category"),
                name="finance_fee_structure_scope_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="feestructure",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount__gte", 0)),
                name="finance_fee_structure_amount_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentinvoice",
            constraint=models.UniqueConstraint(
                fields=("school", "student", "session", "term"),
                name="finance_invoice_student_session_term_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentinvoice",
            constraint=models.CheckConstraint(
                condition=models.Q(("total_amount__gte", 0)),
                name="finance_invoice_total_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentinvoice",
            constraint=models.CheckConstraint(
                condition=models.Q(("balance__gte", 0)),
                name="finance_invoice_balance_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoiceitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount__gte", 0)),
                name="finance_invoice_item_amount_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoiceitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("paid_amount__gte", 0)),
                name="finance_invoice_item_paid_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount__gte", 0)),
                name="finance_payment_amount_gte_0",
            ),
        ),
    ]
