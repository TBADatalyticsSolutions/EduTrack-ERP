from django import forms

from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)


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