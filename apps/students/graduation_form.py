from django import forms
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