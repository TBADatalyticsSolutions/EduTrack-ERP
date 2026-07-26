from django.db import models

from apps.core.models import BaseModel


class Role(BaseModel):
    """
    Defines the different roles available in the system.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.name
