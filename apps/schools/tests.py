from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role

from .models import School, SchoolSubscription


class SchoolSaaSTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="School A",
            email="school-a@example.com",
        )
        self.school_b = School.objects.create(
            name="School B",
            email="school-b@example.com",
        )
        now = timezone.now()
        SchoolSubscription.objects.create(
            school=self.school_a,
            plan="STANDARD",
            status="ACTIVE",
            started_at=now,
        )
        SchoolSubscription.objects.create(
            school=self.school_b,
            plan="PREMIUM",
            status="ACTIVE",
            started_at=now,
        )

        school_admin_role, _ = Role.objects.get_or_create(
            code="SCHOOL_ADMIN",
            defaults={"name": "School Administrator"},
        )
        self.admin_a = User.objects.create_user(
            username="admin-a",
            password="password123",
        )
        self.admin_a.profile.school = self.school_a
        self.admin_a.profile.role = school_admin_role
        self.admin_a.profile.is_school_admin = True
        self.admin_a.profile.save()

        self.admin_b = User.objects.create_user(
            username="admin-b",
            password="password123",
        )
        self.admin_b.profile.school = self.school_b
        self.admin_b.profile.role = school_admin_role
        self.admin_b.profile.is_school_admin = True
        self.admin_b.profile.save()

        self.superuser = User.objects.create_superuser(
            username="platform-admin",
            password="password123",
        )

    def test_school_admin_sees_only_own_school(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("school-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school_a.name)
        self.assertNotContains(response, self.school_b.name)

    def test_school_admin_cannot_edit_another_school(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("school-edit", args=[self.school_b.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("school-dashboard"))

    def test_school_admin_sees_only_own_subscription(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("subscription-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school_a.name)
        self.assertNotContains(response, self.school_b.name)

    def test_platform_admin_can_create_school_and_initial_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("school-create"),
            {
                "name": "School C",
                "short_name": "SC",
                "motto": "Learn",
                "email": "school-c@example.com",
                "phone": "08000000000",
                "website": "",
                "address": "Abeokuta",
                "admin_username": "school-c-admin",
                "admin_first_name": "School",
                "admin_last_name": "Admin",
                "admin_email": "school-c-admin@example.com",
                "admin_password": "securepass123",
                "admin_password_confirm": "securepass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        school = School.objects.get(email="school-c@example.com")
        subscription = SchoolSubscription.objects.get(school=school)
        admin = User.objects.get(username="school-c-admin")
        self.assertEqual(subscription.status, "ACTIVE")
        self.assertEqual(admin.profile.school_id, school.pk)
        self.assertEqual(admin.profile.role.code, "SCHOOL_ADMIN")
        self.assertTrue(admin.check_password("securepass123"))


    def test_platform_admin_cannot_create_more_than_ten_active_schools(self):
        for index in range(8):
            School.objects.create(
                name=f"Additional School {index}",
                email=f"additional-{index}@example.com",
            )

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("school-create"),
            {
                "name": "School Eleven",
                "short_name": "S11",
                "motto": "Learn",
                "email": "school-eleven@example.com",
                "phone": "08000000000",
                "website": "",
                "address": "Abeokuta",
                "admin_username": "school-eleven-admin",
                "admin_first_name": "School",
                "admin_last_name": "Admin",
                "admin_email": "school-eleven-admin@example.com",
                "admin_password": "securepass123",
                "admin_password_confirm": "securepass123",
            },
        )
        self.assertRedirects(response, reverse("school-dashboard"))
        self.assertFalse(School.objects.filter(email="school-eleven@example.com").exists())
