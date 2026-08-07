from django import forms
from apps.accounts.utils import log_activity


class GraduationForm(forms.Form):

    session = forms.CharField(
        max_length=20,
        label="Academic Session",
    )

    remark = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )