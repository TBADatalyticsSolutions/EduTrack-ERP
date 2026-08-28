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
    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "reference", "notes"]

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount
