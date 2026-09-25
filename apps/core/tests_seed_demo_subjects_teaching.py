from django.core.management import call_command
from django.test import TestCase

from apps.academics.models import ClassSubject, SchoolClass, Subject
from apps.schools.models import School
from apps.students.models import Student
from apps.teachers.models import Department, Teacher, TeacherSubject


class SeedDemoSubjectsTeachingCommandTests(TestCase):
    def setUp(self):
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")

    def test_seeds_subjects_and_teaching_for_all_demo_schools(self):
        call_command("seed_demo_subjects_teaching")

        self.assertEqual(
            Subject.objects.filter(
                school__short_name__in=[
                    "AFAAB", "GIA", "CHC", "RCS", "BFA",
                    "LIS", "HMC", "OBS", "SSA", "PIC",
                ]
            ).count(),
            100,
        )
        self.assertEqual(ClassSubject.objects.count(), 1400)
        self.assertEqual(Department.objects.count(), 40)
        self.assertEqual(Teacher.objects.count(), 50)
        self.assertEqual(TeacherSubject.objects.count(), 200)

        for school in School.objects.all():
            self.assertEqual(school.subjects.count(), 10)
            self.assertEqual(school.departments.count(), 4)
            self.assertEqual(school.teachers.count(), 5)
            self.assertEqual(
                ClassSubject.objects.filter(
                    school_class__school=school,
                ).count(),
                140,
            )
            self.assertEqual(
                TeacherSubject.objects.filter(
                    teacher__school=school,
                ).count(),
                20,
            )

    def test_is_idempotent(self):
        call_command("seed_demo_subjects_teaching")
        call_command("seed_demo_subjects_teaching")

        self.assertEqual(Subject.objects.count(), 100)
        self.assertEqual(ClassSubject.objects.count(), 1400)
        self.assertEqual(Department.objects.count(), 40)
        self.assertEqual(Teacher.objects.count(), 50)
        self.assertEqual(TeacherSubject.objects.count(), 200)

    def test_does_not_create_students(self):
        call_command("seed_demo_subjects_teaching")
        self.assertEqual(Student.objects.count(), 0)
