from django import forms
from django.contrib.auth import get_user_model

from .models import Notification


User = get_user_model()


class NotificationForm(forms.ModelForm):
    send_to_all_students = forms.BooleanField(
        required=False,
        label="Send as school notice to all students",
        help_text="Creates a notice for every active student portal account in this school.",
    )

    class Meta:
        model = Notification
        fields = [
            "recipient",
            "send_to_all_students",
            "title",
            "message",
            "notification_type",
        ]
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Write the notice or message..."}
            ),
            "title": forms.TextInput(
                attrs={"placeholder": "e.g. First Term Resumption Notice"}
            ),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school:
            self.fields["recipient"].queryset = User.objects.filter(
                is_active=True,
                profile__school=school,
            ).select_related("profile", "profile__role").order_by(
                "first_name", "last_name", "username"
            )
        self.fields["recipient"].required = False

    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get("recipient")
        broadcast = cleaned_data.get("send_to_all_students")
        if not recipient and not broadcast:
            self.add_error(
                "recipient",
                "Select a recipient or choose the school-wide student notice option.",
            )
        return cleaned_data
