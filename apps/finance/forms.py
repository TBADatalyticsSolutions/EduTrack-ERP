from django import forms

from .models import FeeCategory, FeeStructure, StudentInvoice, InvoiceItem, Payment


class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ["name", "description"]


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["session", "term", "school_class", "fee_category", "amount"]


class StudentInvoiceForm(forms.ModelForm):
    class Meta:
        model = StudentInvoice
        fields = ["student", "session", "term", "due_date", "remarks"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["fee_category", "description", "amount", "due_date", "is_optional"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class PaymentForm(forms.ModelForm):
    """Record a payment or a documented scholarship/fee waiver."""

    class Meta:
        model = Payment
        fields = [
            "settlement_type",
            "amount",
            "payment_method",
            "reference",
            "notes",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"min": "0", "step": "0.01", "class": "form-control"}
            ),
            "settlement_type": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice = invoice
        self.fields["amount"].help_text = (
            "For a full scholarship/waiver, enter 0 and the outstanding balance "
            "will be settled automatically."
        )
        self.fields["reference"].help_text = (
            "Optional for scholarships/waivers; recommended for bank, POS or online payments."
        )

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        settlement_type = cleaned.get("settlement_type")
        payment_method = cleaned.get("payment_method")

        if amount is None:
            return cleaned

        if amount < 0:
            self.add_error("amount", "Amount cannot be negative.")
            return cleaned

        if settlement_type == "PAYMENT":
            if amount <= 0:
                self.add_error("amount", "Payment amount must be greater than zero.")
            if not payment_method:
                self.add_error("payment_method", "Select a payment method.")

        elif settlement_type in {"SCHOLARSHIP", "WAIVER"}:
            if not self.invoice:
                self.add_error("amount", "Invoice context is required for a scholarship or waiver.")
            elif amount == 0:
                cleaned["amount"] = self.invoice.balance
            elif amount > self.invoice.balance:
                self.add_error(
                    "amount",
                    "Settlement cannot exceed the outstanding balance.",
                )
            cleaned["payment_method"] = ""

        return cleaned
