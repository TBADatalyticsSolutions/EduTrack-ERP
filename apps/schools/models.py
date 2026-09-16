from django.db import models

from apps.core.models import BaseModel


class School(BaseModel):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True)
    motto = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to="school_logos/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


class SchoolSubscription(BaseModel):
    """Tenant subscription record for the EduTrack SaaS platform."""

    PLAN_CHOICES = (
        ("STANDARD", "Standard"),
        ("PREMIUM", "Premium"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("PAST_DUE", "Past Due"),
        ("SUSPENDED", "Suspended"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    )

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default="STANDARD",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )
    started_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=("status", "school")),
        ]

    def __str__(self):
        return f"{self.school.name} - {self.get_plan_display()} ({self.get_status_display()})"

    @property
    def is_subscribed(self):
        return self.status == "ACTIVE"
