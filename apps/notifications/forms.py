from django import forms
from .models import Notification

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["recipient", "title", "message", "notification_type"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}
