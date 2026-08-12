from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.models import User

from .models import UserProfile


# ==========================================================
# AUTHENTICATION FORMS
# ==========================================================

class LoginForm(AuthenticationForm):
    """
    Custom Login Form
    """

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autofocus": True,
                "autocomplete": "username",
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )

    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        label="Remember Me",
    )


# ==========================================================
# PASSWORD CHANGE
# ==========================================================

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Password Change Form
    """

    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
            }
        )
    )

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        )
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        )
    )


# ==========================================================
# PASSWORD RESET
# ==========================================================

class CustomPasswordResetForm(PasswordResetForm):
    """
    Password Reset Form
    """

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address",
                "autocomplete": "email",
            }
        )
    )


# ==========================================================
# SET NEW PASSWORD
# ==========================================================

class CustomSetPasswordForm(SetPasswordForm):
    """
    Set Password Form
    """

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New Password",
                "autocomplete": "new-password",
            }
        )
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
                "autocomplete": "new-password",
            }
        )
    )


# ==========================================================
# MY PROFILE FORM
# ==========================================================

class ProfileForm(forms.ModelForm):
    """
    Logged-in user's profile form.
    """

    class Meta:
        model = UserProfile

        fields = [
            "avatar",
            "phone",
            "department",
        ]

        widgets = {
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone Number",
                }
            ),
            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department",
                }
            ),
        }


# ==========================================================
# USER MANAGEMENT
# ==========================================================

class UserForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
        required=False,
    )

    class Meta:

        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_active",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class UserProfileForm(forms.ModelForm):

    class Meta:

        model = UserProfile

        fields = [
            "school",
            "role",
            "phone",
            "avatar",
            "employee_id",
            "department",
            "is_school_admin",
        ]

        widgets = {
            "school": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "employee_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "is_school_admin": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }