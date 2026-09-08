from django import forms

from .models import FeeCategory, FeeStructure, StudentInvoice, InvoiceItem, Payment


class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["session", "term", "school_class", "fee_category", "amount"]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "fee_category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"min": "0", "step": "0.01", "class": "form-control"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school is not None:
            self.fields["session"].queryset = self.fields["session"].queryset.filter(school=school).order_by("-name")
            self.fields["school_class"].queryset = self.fields["school_class"].queryset.filter(school=school).order_by("name")
            self.fields["fee_category"].queryset = self.fields["fee_category"].queryset.filter(school=school).order_by("name")

        selected_session_id = None
        if self.is_bound:
            selected_session_id = self.data.get(self.add_prefix("session"))
        elif self.instance.pk:
            selected_session_id = self.instance.session_id

        if school is not None:
            term_qs = self.fields["term"].queryset.filter(school=school)
            if selected_session_id:
                term_qs = term_qs.filter(session_id=selected_session_id)
            self.fields["term"].queryset = term_qs.order_by("session__name", "name")
        else:
            self.fields["term"].queryset = self.fields["term"].queryset.none()

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("session")
        term = cleaned.get("term")
        school_class = cleaned.get("school_class")
        fee_category = cleaned.get("fee_category")
        amount = cleaned.get("amount")

        if session and term and term.session_id != session.id:
            self.add_error("term", "Select a term belonging to the selected academic session.")
        if session and self.school and session.school_id != self.school.id:
            self.add_error("session", "The selected academic session must belong to this school.")
        if term and self.school and term.school_id != self.school.id:
            self.add_error("term", "The selected term must belong to this school.")
        if school_class and self.school and school_class.school_id != self.school.id:
            self.add_error("school_class", "The selected class must belong to this school.")
        if fee_category and self.school and fee_category.school_id != self.school.id:
            self.add_error("fee_category", "The selected fee category must belong to this school.")
        if amount is not None and amount < 0:
            self.add_error("amount", "Fee amount cannot be negative.")
        return cleaned


class StudentInvoiceForm(forms.ModelForm):
    class Meta:
        model = StudentInvoice
        fields = ["student", "session", "term", "due_date", "remarks"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, school=None, editable=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school is not None:
            self.fields["student"].queryset = self.fields["student"].queryset.filter(school=school).order_by("first_name", "last_name")
            self.fields["session"].queryset = self.fields["session"].queryset.filter(school=school).order_by("-name")

            selected_session_id = None
            if self.is_bound:
                selected_session_id = self.data.get(self.add_prefix("session"))
            elif self.instance.pk:
                selected_session_id = self.instance.session_id

            term_qs = self.fields["term"].queryset.filter(school=school)
            if selected_session_id:
                term_qs = term_qs.filter(session_id=selected_session_id)
            self.fields["term"].queryset = term_qs.order_by("session__name", "name")
        else:
            self.fields["student"].queryset = self.fields["session"].queryset = self.fields["term"].queryset.none()

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
        widgets = {"due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"})}


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
            if self.invoice and amount > self.invoice.balance:
                self.add_error("amount", "Payment cannot exceed the outstanding balance.")
        elif settlement_type in {"SCHOLARSHIP", "WAIVER"}:
            if not self.invoice:
                self.add_error("amount", "Invoice context is required for a scholarship or waiver.")
            elif amount == 0:
                cleaned["amount"] = self.invoice.balance
            elif amount > self.invoice.balance:
                self.add_error("amount", "Settlement cannot exceed the outstanding balance.")
            cleaned["payment_method"] = ""
        return cleaned
