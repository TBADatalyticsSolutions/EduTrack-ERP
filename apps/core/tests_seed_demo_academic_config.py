from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.academics.models import AcademicSession, Term
from apps.results.grading import calculate_grade
from apps.results.models import AssessmentType, GradeSetting, StudentResult, SubjectResult
from apps.schools.models import School, SchoolSubscription


class SeedDemoAcademicConfigTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_schools", stdout=StringIO())
        call_command("seed_demo_academics", stdout=StringIO())
        call_command("seed_demo_subjects_teaching", stdout=StringIO())

    def test_complete_configuration_is_seeded(self):
        self.assertEqual(AssessmentType.objects.count(), 50)
        self.assertEqual(GradeSetting.objects.count(), 60)

        for school in School.objects.filter(short_name__in={
            "AFAAB", "GIA", "CHC", "RCS", "BFA",
            "LIS", "HMC", "OBS", "SSA", "PIC",
        }):
            assessments = AssessmentType.objects.filter(school=school)
            grades = GradeSetting.objects.filter(school=school)

            self.assertEqual(assessments.count(), 3)
            self.assertEqual(grades.count(), 6)
            self.assertEqual(
                list(assessments.values_list("name", "maximum_score", "order")),
                [
                    ("CA 1", 15, 1),
                    ("CA 2", 15, 2),
                    ("Examination", 70, 3),
                ],
            )
            self.assertEqual(
                list(
                    grades.values_list(
                        "grade", "minimum_score", "maximum_score", "remark"
                    )
                ),
                [
                    ("A", 70, 100, "Excellent"),
                    ("B", 60, 69, "Very Good"),
                    ("C", 50, 59, "Good"),
                    ("D", 45, 49, "Fair"),
                    ("E", 40, 44, "Pass"),
                    ("F", 0, 39, "Fail"),
                ],
            )

    def test_grade_boundaries_are_complete_and_non_overlapping(self):
        school = School.objects.get(short_name="AFAAB")

        expected = {
            0: ("F", "Fail"),
            39: ("F", "Fail"),
            40: ("E", "Pass"),
            44: ("E", "Pass"),
            45: ("D", "Fair"),
            49: ("D", "Fair"),
            50: ("C", "Good"),
            59: ("C", "Good"),
            60: ("B", "Very Good"),
            69: ("B", "Very Good"),
            70: ("A", "Excellent"),
            100: ("A", "Excellent"),
        }

        for score, expected_result in expected.items():
            self.assertEqual(calculate_grade(school, score), expected_result)

    def test_idempotent(self):
        before = (
            AssessmentType.objects.count(),
            GradeSetting.objects.count(),
        )
        call_command("seed_demo_academic_config", stdout=StringIO())
        self.assertEqual(
            (
                AssessmentType.objects.count(),
                GradeSetting.objects.count(),
            ),
            before,
        )

    def test_stage_does_not_create_operational_records(self):
        self.assertEqual(StudentResult.objects.count(), 0)
        self.assertEqual(SubjectResult.objects.count(), 0)
        self.assertEqual(
            SchoolSubscription.objects.count(),
            School.objects.count(),
        )
        self.assertEqual(AcademicSession.objects.count(), 20)
        self.assertEqual(Term.objects.count(), 60)
