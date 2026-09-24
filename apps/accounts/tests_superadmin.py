from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import CommandError
from django.test import TestCase

from .models import Role, UserProfile


class SuperAdminProvisioningCommandTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_creates_platform_superadmin_idempotently(self):
        with patch.dict("os.environ", {"DJANGO_SUPERADMIN_PASSWORD": "Strong-Test-Password-123!"}):
            management.call_command(
                "provision_superadmin",
                username="platform-admin",
                email="admin@example.com",
                first_name="Platform",
                last_name="Admin",
                noinput=True,
            )
            management.call_command(
                "provision_superadmin",
                username="platform-admin",
                noinput=True,
            )

        user = self.User.objects.get(username="platform-admin")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.check_password("Strong-Test-Password-123!"))

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role.code, "SUPER_ADMIN")
        self.assertIsNone(profile.school)
        self.assertFalse(profile.is_school_admin)

        self.assertEqual(
            self.User.objects.filter(username="platform-admin").count(),
            1,
        )

    def test_refuses_to_promote_existing_non_superuser_without_explicit_flag(self):
        user = self.User.objects.create_user(
            username="existing-user",
            password="Existing-Password-123!",
        )

        with self.assertRaises(CommandError):
            management.call_command(
                "provision_superadmin",
                username=user.username,
                noinput=True,
            )

        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_explicit_promotion_and_password_reset_are_repeatable(self):
        user = self.User.objects.create_user(
            username="existing-user",
            password="Old-Password-123!",
        )

        with patch.dict("os.environ", {"DJANGO_SUPERADMIN_PASSWORD": "New-Password-123!"}):
            management.call_command(
                "provision_superadmin",
                username=user.username,
                promote_existing=True,
                reset_password=True,
                noinput=True,
            )

        user.refresh_from_db()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("New-Password-123!"))

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role.code, "SUPER_ADMIN")
        self.assertIsNone(profile.school)
