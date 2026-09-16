from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.schools.models import School, SchoolSubscription

from .models import Role


class TenantUserManagementTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="Tenant A",
            email="tenant-a@example.com",
        )
        self.school_b = School.objects.create(
            name="Tenant B",
            email="tenant-b@example.com",
        )
        for school in (self.school_a, self.school_b):
            SchoolSubscription.objects.create(
                school=school,
                plan="STANDARD",
                status="ACTIVE",
                started_at=timezone.now(),
            )

        role, _ = Role.objects.get_or_create(
            code="SCHOOL_ADMIN",
            defaults={"name": "School Administrator"},
        )
        teacher_role, _ = Role.objects.get_or_create(
            code="TEACHER",
            defaults={"name": "Teacher"},
        )

        self.admin_a = User.objects.create_user(
            username="tenant-admin-a",
            password="password123",
        )
        self.admin_a.profile.school = self.school_a
        self.admin_a.profile.role = role
        self.admin_a.profile.is_school_admin = True
        self.admin_a.profile.save()

        self.user_a = User.objects.create_user(
            username="tenant-user-a",
            password="password123",
        )
        self.user_a.profile.school = self.school_a
        self.user_a.profile.role = teacher_role
        self.user_a.profile.save()

        self.user_b = User.objects.create_user(
            username="tenant-user-b",
            password="password123",
        )
        self.user_b.profile.school = self.school_b
        self.user_b.profile.role = teacher_role
        self.user_b.profile.save()

    def test_school_admin_user_list_excludes_other_tenants(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_a.username)
        self.assertNotContains(response, self.user_b.username)

    def test_school_admin_cannot_open_other_tenant_user(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("user-detail", args=[self.user_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_cannot_edit_other_tenant_user(self):
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("user-update", args=[self.user_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_school_admin_created_user_is_forced_into_current_school(self):
        self.client.force_login(self.admin_a)
        teacher_role = Role.objects.get(code="TEACHER")
        response = self.client.post(
            reverse("user-create"),
            {
                "username": "new-teacher",
                "first_name": "New",
                "last_name": "Teacher",
                "email": "new-teacher@example.com",
                "password": "securepass123",
                "is_active": "on",
                "school": str(self.school_a.pk),
                "role": str(teacher_role.pk),
                "phone": "08000000000",
                "avatar": "",
                "employee_id": "T-100",
                "department": "Science",
                "is_school_admin": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="new-teacher")
        self.assertEqual(new_user.profile.school_id, self.school_a.pk)
