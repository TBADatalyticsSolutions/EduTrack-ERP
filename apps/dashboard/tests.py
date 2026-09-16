from datetime import date

from django.test import TestCase
from django.utils import timezone

from apps.schools.models import School, SchoolSubscription
from apps.students.models import Student

from .services.dashboard_service import DashboardService


class DashboardTenantIsolationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="School A",
            email="school-a@example.com",
        )
        self.school_b = School.objects.create(
            name="School B",
            email="school-b@example.com",
        )
        for school in (self.school_a, self.school_b):
            SchoolSubscription.objects.create(
                school=school,
                plan="STANDARD",
                status="ACTIVE",
                started_at=timezone.now(),
            )

        self.student_a = Student.objects.create(
            school=self.school_a,
            admission_number="A-0001",
            first_name="Student",
            last_name="Alpha",
            gender="M",
            date_of_birth=date(2015, 1, 1),
        )
        self.student_b = Student.objects.create(
            school=self.school_b,
            admission_number="B-0001",
            first_name="Student",
            last_name="Beta",
            gender="F",
            date_of_birth=date(2015, 2, 1),
        )

    def test_school_dashboard_is_scoped_to_one_tenant(self):
        context = DashboardService.get_dashboard_data(school=self.school_a)

        self.assertEqual(context["student_count"], 1)
        self.assertEqual(list(context["recent_students"]), [self.student_a])
        self.assertNotIn(self.student_b, context["recent_students"])

    def test_platform_dashboard_exposes_subscription_metrics_only(self):
        context = DashboardService.get_platform_dashboard_data()

        self.assertEqual(context["subscribed_school_count"], 2)
        self.assertEqual(context["active_school_count"], 2)
        self.assertNotIn("recent_students", context)
        self.assertNotIn("total_revenue", context)
