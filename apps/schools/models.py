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
