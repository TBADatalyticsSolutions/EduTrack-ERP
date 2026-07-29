from django import forms

from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)


# =====================================================
# PROMOTION FORM
# =====================================================

class PromotionForm(forms.Form):
    """
    Form for promoting students to the next class.
    """

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.order_by("-name"),
        label="Academic Session",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    term = forms.ModelChoiceField(
        queryset=Term.objects.order_by("name"),
        label="Term",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    current_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.order_by("name"),
        label="Current Class",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    next_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.order_by("name"),
        label="Next Class",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )


# =====================================================
# GRADUATION FORM
# =====================================================

class GraduationForm(forms.Form):
    """
    Form for graduating an individual student.
    """

    reason = forms.CharField(
        label="Graduation Reason",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Completed SS3",
            }
        ),
    )


# =====================================================
# WITHDRAWAL FORM
# =====================================================

class WithdrawalForm(forms.Form):
    """
    Form for withdrawing a student.
    """

    reason = forms.CharField(
        label="Withdrawal Reason",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Relocated, Financial Reasons",
            }
        ),
    )

    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional remarks...",
            }
        ),
    )


# =====================================================
# TRANSFER FORM
# =====================================================

class TransferForm(forms.Form):
    """
    Form for transferring a student to another class and/or session.
    """

    to_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.order_by("name"),
        label="Transfer To Class",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    to_session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.order_by("-name"),
        label="Transfer To Session",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    reason = forms.CharField(
        label="Transfer Reason",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Reason for transfer...",
            }
        ),
    )

    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Additional remarks...",
            }
        ),
    )


# =====================================================
# SUSPENSION FORM
# =====================================================

class SuspensionForm(forms.Form):
    """
    Form for suspending a student.
    """

    REASONS = (
        ("MISCONDUCT", "Misconduct"),
        ("EXAM_MALPRACTICE", "Examination Malpractice"),
        ("FIGHTING", "Fighting"),
        ("BULLYING", "Bullying"),
        ("ABSENTEEISM", "Persistent Absenteeism"),
        ("UNPAID_FEES", "Outstanding School Fees"),
        ("VANDALISM", "Damage to School Property"),
        ("OTHER", "Other"),
    )

    reason = forms.ChoiceField(
        choices=REASONS,
        label="Suspension Reason",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    suspension_start = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    suspension_end = forms.DateField(
        label="End Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Reason for suspension...",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("suspension_start")
        end = cleaned_data.get("suspension_end")

        if start and end and end < start:
            raise forms.ValidationError(
                "Suspension end date cannot be earlier than the start date."
            )

        return cleaned_data


# =====================================================
# EXPULSION FORM
# =====================================================

class ExpulsionForm(forms.Form):
    """
    Form for permanently expelling a student.
    """

    REASONS = (
        ("GROSS_MISCONDUCT", "Gross Misconduct"),
        ("CULTISM", "Cultism"),
        ("DRUG_ABUSE", "Drug Abuse"),
        ("VIOLENCE", "Violence"),
        ("THEFT", "Theft"),
        ("SEXUAL_MISCONDUCT", "Sexual Misconduct"),
        ("CRIMINAL_OFFENCE", "Criminal Offence"),
        ("OTHER", "Other"),
    )

    reason = forms.ChoiceField(
        choices=REASONS,
        label="Expulsion Reason",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Reason for expulsion...",
            }
        ),
    )