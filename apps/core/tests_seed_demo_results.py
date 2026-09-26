from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.academics.models import AcademicSession, Term
from apps.results.grading import calculate_grade
from apps.results.models import AssessmentType, GradeSetting, StudentResult, SubjectResult
from apps.schools.models import School, SchoolSubscription
from apps.students.models import Student


DEMO_SCHOOL_CODES = {
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
}


class SeedDemoResultsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_schools", stdout=StringIO())
        call_command("seed_demo_academics", stdout=StringIO())
        call_command("seed_demo_subjects_teaching", stdout=StringIO())
        call_command("seed_demo_academic_config", stdout=StringIO())
        call_command("seed_demo_students_portal", stdout=StringIO())
        call_command("seed_demo_results", stdout=StringIO())

    def test_complete_results_configuration(self):
        self.assertEqual(
            StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            120,
        )
        self.assertEqual(
            SubjectResult.objects.filter(
                student_result__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            1200,
        )

        self.assertEqual(
            StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                published=True,
            ).count(),
            90,
        )
        self.assertEqual(
            StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                published=False,
            ).count(),
            30,
        )
        self.assertEqual(
            StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                promotion_status="PENDING",
            ).count(),
            120,
        )

    def test_subject_totals_grades_and_overall_averages_are_consistent(self):
        for subject_result in SubjectResult.objects.select_related(
            "student_result__school"
        ).filter(student_result__school__short_name__in=DEMO_SCHOOL_CODES):
            expected_total = (
                subject_result.ca1
                + subject_result.ca2
                + subject_result.assignment
                + subject_result.project
                + subject_result.examination
            )
            self.assertEqual(subject_result.total, expected_total)

            expected_grade = calculate_grade(
                subject_result.student_result.school,
                expected_total,
            )
            self.assertEqual(
                (subject_result.grade, subject_result.remark),
                expected_grade,
            )

        for result in StudentResult.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES
        ):
            subject_totals = list(
                result.subjects.values_list("total", flat=True)
            )
            self.assertEqual(len(subject_totals), 10)
            self.assertEqual(
                result.total_score,
                sum(subject_totals, Decimal("0.00")),
            )
            self.assertEqual(
                result.average,
                result.total_score / Decimal("10"),
            )

    def test_results_are_tenant_and_academic_scope_safe(self):
        for result in StudentResult.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES
        ).select_related("student", "session", "term", "school_class"):
            self.assertEqual(result.school_id, result.student.school_id)
            self.assertEqual(result.school_id, result.session.school_id)
            self.assertEqual(result.school_id, result.term.school_id)
            self.assertEqual(result.school_id, result.school_class.school_id)
            self.assertEqual(result.session.name, "2026/2027")
            self.assertEqual(result.term.name, "First Term")
            self.assertEqual(result.term.session_id, result.session_id)
            self.assertEqual(
                result.school_class_id,
                result.student.current_class_id,
            )

            for subject_result in result.subjects.select_related("subject"):
                self.assertEqual(
                    subject_result.student_result.school_id,
                    subject_result.subject.school_id,
                )

    def test_deterministic_afaaB_result(self):
        result = StudentResult.objects.get(
            student__admission_number="AFAAB/2026/0001"
        )
        self.assertEqual(result.student.first_name, "Zainab")
        self.assertEqual(result.student.last_name, "Adekunle")
        self.assertEqual(result.school_class.name, "Nursery 1")
        self.assertEqual(result.session.name, "2026/2027")
        self.assertEqual(result.term.name, "First Term")
        self.assertEqual(result.total_score, Decimal("749.00"))
        self.assertEqual(result.average, Decimal("74.90"))
        self.assertEqual(result.position, 1)

        subject_result = SubjectResult.objects.get(
            student_result=result,
            subject__code="AFAAB-MAT",
        )
        self.assertEqual(subject_result.ca1, Decimal("11.00"))
        self.assertEqual(subject_result.ca2, Decimal("14.00"))
        self.assertEqual(subject_result.examination, Decimal("43.00"))
        self.assertEqual(subject_result.total, Decimal("68.00"))
        self.assertEqual(subject_result.grade, "A")
        self.assertEqual(subject_result.remark, "Excellent")

    def test_idempotent(self):
        before = (
            StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            SubjectResult.objects.filter(
                student_result__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
        )

        call_command("seed_demo_results", stdout=StringIO())

        self.assertEqual(
            (
                StudentResult.objects.filter(
                    school__short_name__in=DEMO_SCHOOL_CODES
                ).count(),
                SubjectResult.objects.filter(
                    student_result__school__short_name__in=DEMO_SCHOOL_CODES
                ).count(),
            ),
            before,
        )

    def test_stage_does_not_create_finance_or_academic_configuration_records(self):
        self.assertEqual(
            AssessmentType.objects.count(),
            30,
        )
        self.assertEqual(
            GradeSetting.objects.count(),
            60,
        )
        self.assertEqual(
            SchoolSubscription.objects.count(),
            School.objects.count(),
        )
        self.assertEqual(AcademicSession.objects.count(), 20)
        self.assertEqual(Term.objects.count(), 60)

        # Results are the only operational records introduced by this stage.
        self.assertEqual(Student.objects.count(), 120)
