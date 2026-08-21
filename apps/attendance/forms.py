from django import forms

from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)

from .models import AttendanceRecord


# ==========================================================
# ATTENDANCE SESSION FORM
# ==========================================================

class AttendanceSessionForm(forms.Form):
    """
    Form used to create or open an attendance session.
    """

    academic_session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.order_by("-name"),
        empty_label="Select Academic Session",
        label="Academic Session",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    term = forms.ModelChoiceField(
        queryset=Term.objects.order_by("name"),
        empty_label="Select Term",
        label="Term",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.order_by("name"),
        empty_label="Select Class",
        label="Class",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    attendance_date = forms.DateField(
        label="Attendance Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )


# ==========================================================
# ATTENDANCE RECORD FORM
# ==========================================================

class AttendanceRecordForm(forms.ModelForm):
    """
    Form for editing an individual attendance record.
    """

    class Meta:
        model = AttendanceRecord

        fields = [
            "status",
            "remarks",
        ]

        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "remarks": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional remark",
                }
            ),
        }