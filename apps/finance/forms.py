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
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0", "step": "0.01", "class": "form-control"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["session"].queryset = self.fields["session"].queryset.filter(school=school)
            self.fields["term"].queryset = self.fields["term"].queryset.filter(school=school)
            self.fields["school_class"].queryset = self.fields["school_class"].queryset.filter(school=school)
            self.fields["fee_category"].queryset = self.fields["fee_category"].queryset.filter(school=school)

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("session")
        term = cleaned.get("term")
        school_class = cleaned.get("school_class")
        amount = cleaned.get("amount")
        if session and term and term.session_id != session.id:
            self.add_error("term", "Select a term belonging to the selected academic session.")
        if amount is not None and amount < 0:
            self.add_error("amount", "Fee amount cannot be negative.")
        if session and school_class and school_class.school_id != session.school_id:
            self.add_error("school_class", "The selected class must belong to the selected school.")
        return cleaned


class StudentInvoiceForm(forms.ModelForm):
    class Meta:
        model = StudentInvoice
        fields = ["student", "session", "term", "due_date", "remarks"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"})}

    def __init__(self, *args, school=None, editable=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school is not None:
            self.fields["student"].queryset = self.fields["student"].queryset.filter(school=school)
            self.fields["session"].queryset = self.fields["session"].queryset.filter(school=school)
            self.fields["term"].queryset = self.fields["term"].queryset.filter(school=school)
        if editable:
            for name in ("student", "session", "term"):
                self.fields[name].disabled = True
                self.fields[name].help_text = "Locked after generation to preserve the invoice accounting record."

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get("student")
        session = cleaned.get("session")
        term = cleaned.get("term")
        if student and self.school and student.school_id != self.school.id:
            self.add_error("student", "Select a student belonging to this school.")
        if session and self.school and session.school_id != self.school.id:
            self.add_error("session", "Select an academic session belonging to this school.")
        if term and self.school and term.school_id != self.school.id:
            self.add_error("term", "Select a term belonging to this school.")
        if session and term and term.session_id != session.id:
            self.add_error("term", "The selected term must belong to the selected academic session.")
        return cleaned


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["fee_category", "description", "amount", "due_date", "is_optional"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class PaymentForm(forms.ModelForm):
    """Record an actual payment or documented scholarship/waiver."""

    class Meta:
        model = Payment
        fields = ["settlement_type", "amount", "payment_method", "reference", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0", "step": "0.01", "class": "form-control"}),
            "settlement_type": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice = invoice
        self.fields["amount"].help_text = "Enter 0 for a full scholarship/waiver; the outstanding balance will be applied automatically."
        self.fields["reference"].help_text = "Recommended for bank transfer, POS and online payments."

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        settlement_type = cleaned.get("settlement_type")
        payment_method = cleaned.get("payment_method")
        if amount is None:
            return cleaned
        if amount < 0:
            self.add_error("amount", "Amount cannot be negative.")
        elif settlement_type == "PAYMENT":
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
                self.add_error("amount", "Settlement cannot exceed the outstanding balance.")
            cleaned["payment_method"] = ""
        return cleaned
