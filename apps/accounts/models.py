from django.conf import settings
from django.db import models

from apps.schools.models import School


# ==========================================================
# ROLE MODEL
# ==========================================================

class Role(models.Model):

    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Administrator"),
        ("SCHOOL_ADMIN", "School Administrator"),
        ("PRINCIPAL", "Principal"),
        ("VICE_PRINCIPAL", "Vice Principal"),
        ("REGISTRAR", "Registrar"),
        ("TEACHER", "Teacher"),
        ("ACCOUNTANT", "Accountant"),
        ("LIBRARIAN", "Librarian"),
        ("PARENT", "Parent"),
        ("STUDENT", "Student"),
    ]

    code = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        unique=True,
        default="TEACHER",
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.name


# ==========================================================
# USER PROFILE
# ==========================================================

class UserProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    avatar = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    employee_id = models.CharField(
        max_length=30,
        blank=True,
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    is_school_admin = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.user.username


# ==========================================================
# ACTIVITY LOG (AUDIT TRAIL)
# ==========================================================

class ActivityLog(models.Model):

    ACTION_CHOICES = [

        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),

        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),

        ("PROFILE_UPDATE", "Profile Update"),

        ("PASSWORD_CHANGE", "Password Change"),
        ("PASSWORD_RESET", "Password Reset"),

        ("IMPORT", "Import"),
        ("EXPORT", "Export"),

        ("OTHER", "Other"),

    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
    )

    module = models.CharField(
        max_length=100,
        help_text="Students, Finance, Attendance, Results, etc.",
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "-created_at",
        ]

        verbose_name = "Activity Log"

        verbose_name_plural = "Activity Logs"

    def __str__(self):

        username = (
            self.user.username
            if self.user
            else "Anonymous"
        )

        return f"{username} | {self.module} | {self.action}"
