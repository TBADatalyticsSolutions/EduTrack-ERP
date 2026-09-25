from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import ParentPortalLink, UserProfile
from apps.attendance.models import AttendanceSession
from apps.finance.models import StudentInvoice
from apps.notifications.models import Notification
from apps.results.models import StudentResult
from apps.schools.models import School
from apps.students.models import Parent, Student


class SeedDemoStudentsPortalCommandTests(TestCase):
    def setUp(self):
        call_command("seed_roles")
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")
        call_command("seed_demo_subjects_teaching")
        call_command("seed_demo_academic_config")

    def test_complete_student_parent_and_portal_configuration(self):
        call_command("seed_demo_students_portal")

        self.assertEqual(Student.objects.count(), 120)
        self.assertEqual(Parent.objects.count(), 60)
        self.assertEqual(ParentPortalLink.objects.count(), 60)

        self.assertEqual(
            UserProfile.objects.filter(role__code="STUDENT").count(),
            120,
        )
        self.assertEqual(
            UserProfile.objects.filter(role__code="PARENT").count(),
            60,
        )
        self.assertEqual(
            UserProfile.objects.filter(
                role__code="SCHOOL_ADMIN",
                is_school_admin=True,
            ).count(),
            10,
        )

        for school in School.objects.all():
            self.assertEqual(school.students.count(), 12)
            self.assertEqual(school.parent_set.count(), 6)
            self.assertEqual(
                ParentPortalLink.objects.filter(
                    parent__school=school
                ).count(),
                6,
            )
            self.assertEqual(
                UserProfile.objects.filter(
                    school=school,
                    role__code="STUDENT",
                ).count(),
                12,
            )
            self.assertEqual(
                UserProfile.objects.filter(
                    school=school,
                    role__code="PARENT",
                ).count(),
                6,
            )
            self.assertEqual(
                UserProfile.objects.filter(
                    school=school,
                    role__code="SCHOOL_ADMIN",
                    is_school_admin=True,
                ).count(),
                1,
            )

    def test_portal_ownership_and_school_isolation(self):
        call_command("seed_demo_students_portal")

        for link in ParentPortalLink.objects.select_related(
            "parent__school", "user__profile"
        ):
            self.assertEqual(
                link.parent.school_id,
                link.user.profile.school_id,
            )
            self.assertEqual(link.user.profile.role.code, "PARENT")
            self.assertTrue(
                link.user.username.startswith(
                    f"{link.parent.school.short_name}-P"
                )
            )

        for student in Student.objects.select_related("school"):
            user = get_user_model().objects.get(
                username=student.admission_number
            )
            self.assertEqual(user.profile.school_id, student.school_id)
            self.assertEqual(user.profile.role.code, "STUDENT")

    def test_idempotent(self):
        call_command("seed_demo_students_portal")
        call_command("seed_demo_students_portal")

        self.assertEqual(Student.objects.count(), 120)
        self.assertEqual(Parent.objects.count(), 60)
        self.assertEqual(ParentPortalLink.objects.count(), 60)
        self.assertEqual(
            UserProfile.objects.filter(role__code="STUDENT").count(),
            120,
        )
        self.assertEqual(
            UserProfile.objects.filter(role__code="PARENT").count(),
            60,
        )
        self.assertEqual(
            UserProfile.objects.filter(
                role__code="SCHOOL_ADMIN",
                is_school_admin=True,
            ).count(),
            10,
        )

    def test_no_operational_data_is_created(self):
        call_command("seed_demo_students_portal")

        self.assertEqual(StudentInvoice.objects.count(), 0)
        self.assertEqual(StudentResult.objects.count(), 0)
        self.assertEqual(AttendanceSession.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_student_and_parent_fields_are_deterministic(self):
        call_command("seed_demo_students_portal")

        student = Student.objects.get(
            admission_number="AFAAB/2026/0001"
        )
        self.assertEqual(student.first_name, "Zainab")
        self.assertEqual(student.last_name, "Adekunle")
        self.assertEqual(student.current_session.name, "2026/2027")
        self.assertEqual(student.current_term.name, "First Term")
        self.assertEqual(student.current_class.name, "Nursery 1")

        parent = Parent.objects.get(
            school__short_name="AFAAB",
            first_name="Kareem",
            last_name="DemoFamily1",
        )
        self.assertEqual(parent.students.count(), 2)
        self.assertEqual(
            parent.email,
            "parent1.afaab@edutrack-demo.test",
        )
        self.assertEqual(
            parent.portal_link.user.username,
            "AFAAB-P001",
        )
