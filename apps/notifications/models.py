from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.schools.models import School

class Notification(BaseModel):
    TYPE_CHOICES = (("INFO", "Information"), ("SUCCESS", "Success"), ("WARNING", "Warning"), ("DANGER", "Important"))
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="notifications")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INFO")
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient}"
