from django.core.management import call_command
from django.test import TestCase

from apps.academics.models import AcademicSession, ClassArm, SchoolClass, Term
from apps.schools.models import School
from apps.students.models import Student
from apps.teachers.models import Teacher


class SeedDemoAcademicStructureCommandTests(TestCase):
    def test_seeds_complete_academic_structure_for_ten_demo_schools(self):
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")

        self.assertEqual(AcademicSession.objects.count(), 20)
        self.assertEqual(Term.objects.count(), 60)
        self.assertEqual(SchoolClass.objects.count(), 140)
        self.assertEqual(ClassArm.objects.count(), 280)

        for school in School.objects.all():
            self.assertEqual(
                school.sessions.filter(is_current=True).count(),
                1,
            )
            current_session = school.sessions.get(is_current=True)
            self.assertEqual(current_session.name, "2026/2027")

            self.assertEqual(
                school.terms.filter(is_current=True).count(),
                1,
            )
            current_term = school.terms.get(is_current=True)
            self.assertEqual(current_term.name, "First Term")
            self.assertEqual(
                current_term.session_id,
                current_session.id,
            )

            self.assertEqual(school.classes.count(), 14)
            self.assertEqual(
                ClassArm.objects.filter(school=school).count(),
                28,
            )

    def test_rerun_is_idempotent(self):
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")
        call_command("seed_demo_academics")

        self.assertEqual(AcademicSession.objects.count(), 20)
        self.assertEqual(Term.objects.count(), 60)
        self.assertEqual(SchoolClass.objects.count(), 140)
        self.assertEqual(ClassArm.objects.count(), 280)

    def test_academic_stage_does_not_create_operational_data(self):
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Teacher.objects.count(), 0)
