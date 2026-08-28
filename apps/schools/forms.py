from django import forms

from .models import School


class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = (
            "name",
            "short_name",
            "motto",
            "email",
            "phone",
            "website",
            "address",
            "logo",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "short_name": forms.TextInput(attrs={"class": "form-control"}),
            "motto": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
