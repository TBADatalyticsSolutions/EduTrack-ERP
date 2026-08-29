from django.urls import path

from .views import (
    dashboard,
    fee_categories,
    fee_structures,
    fee_structure_edit,
    invoice_list,
    invoice_create,
    invoice_edit,
    invoice_delete,
    invoice_detail,
    record_payment,
)

app_name = "finance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("categories/", fee_categories, name="fee-categories"),
    path("structures/", fee_structures, name="fee-structures"),
    path("structures/<uuid:pk>/edit/", fee_structure_edit, name="fee-structure-edit"),
    path("invoices/", invoice_list, name="invoice-list"),
    path("invoices/add/", invoice_create, name="invoice-create"),
    path("invoices/<uuid:pk>/edit/", invoice_edit, name="invoice-edit"),
    path("invoices/<uuid:pk>/delete/", invoice_delete, name="invoice-delete"),
    path("invoices/<uuid:pk>/", invoice_detail, name="invoice-detail"),
    path("invoices/<uuid:pk>/payment/", record_payment, name="record-payment"),
]
