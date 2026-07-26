from django.contrib import admin

from .models import (
    FeeCategory,
    FeeStructure,
    StudentInvoice,
    InvoiceItem,
    Payment,
)
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "fee_category",
        "amount",
        "paid_amount",
        "balance",
    )

    list_filter = (
        "fee_category",
    )

admin.site.register(FeeCategory)
admin.site.register(FeeStructure)
admin.site.register(StudentInvoice)
admin.site.register(Payment)