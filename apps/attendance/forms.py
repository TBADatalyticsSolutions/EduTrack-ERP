from django import forms
from apps.accounts.utils import log_activity

from apps.academics.models import (
from apps.accounts.utils import log_activity
    AcademicSession,
    Term,
    SchoolClass,
)


class AttendanceRegisterForm(forms.Form):

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.all()
    )

    term = forms.ModelChoiceField(
        queryset=Term.objects.all()
    )

    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Class",
    )

    attendance_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        )
    )