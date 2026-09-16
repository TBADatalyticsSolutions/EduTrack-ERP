from django import forms
from django.contrib.auth.models import User

from .models import School, SchoolSubscription


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


class SchoolOnboardingForm(SchoolForm):
    """Create a school tenant together with its first school administrator."""

    admin_username = forms.CharField(
        max_length=150,
        label="School Admin Username",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
    )
    admin_first_name = forms.CharField(
        max_length=150,
        label="Admin First Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    admin_last_name = forms.CharField(
        max_length=150,
        label="Admin Last Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    admin_email = forms.EmailField(
        label="Admin Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    admin_password = forms.CharField(
        min_length=8,
        label="Temporary Admin Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    admin_password_confirm = forms.CharField(
        min_length=8,
        label="Confirm Admin Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def clean_admin_username(self):
        username = self.cleaned_data["admin_username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("admin_password") != cleaned.get("admin_password_confirm"):
            self.add_error("admin_password_confirm", "The passwords do not match.")
        return cleaned


class SchoolSubscriptionForm(forms.ModelForm):
    class Meta:
        model = SchoolSubscription
        fields = (
            "plan",
            "status",
            "started_at",
            "ends_at",
        )
        widgets = {
            "plan": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "started_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["started_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]
