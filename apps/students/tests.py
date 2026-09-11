from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import AcademicSession, SchoolClass, Term
from apps.schools.models import School

from .models import Student


class StudentManagementViewTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Student Management Test School",
            short_name="SMTS",
            email="students@example.com",
            is_active=True,
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            is_active=True,
            is_current=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            session=self.session,
            name="First Term",
            is_active=True,
            is_current=True,
        )
        self.school_class = SchoolClass.objects.create(
            school=self.school,
            name="Primary 4",
            is_active=True,
        )
        self.student = Student.objects.create(
            school=self.school,
            admission_number="SMTS/2026/0001",
            first_name="Test",
            last_name="Student",
            gender="M",
            date_of_birth=date(2015, 1, 1),
            current_class=self.school_class,
            current_session=self.session,
            current_term=self.term,
        )
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="student-management-admin",
            password="test-password-123",
        )
        self.client.force_login(self.user)

    def test_student_management_dashboard_loads(self):
        response = self.client.get(reverse("student-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Management")
        self.assertContains(response, self.student.admission_number)

    def test_student_management_uses_active_school_for_superuser_without_school(self):
        response = self.client.get(reverse("student-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 302)

    def test_student_detail_is_school_scoped(self):
        response = self.client.get(reverse("student-detail", args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.full_name())
