from decimal import Decimal

from django.test import TestCase

from apps.academics.models import AcademicSession, SchoolClass, Subject, Term
from apps.schools.models import School
from apps.students.models import Student

from .models import GradeSetting, StudentResult, SubjectResult


class SubjectResultCalculationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Results Test School",
            short_name="RTS",
            email="results-test@example.com",
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            is_current=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            session=self.session,
            name="First Term",
            is_current=True,
        )
        self.school_class = SchoolClass.objects.create(
            school=self.school,
            name="Primary 4",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathematics",
            code="RTS-MAT",
            is_core=True,
        )
        self.student = Student.objects.create(
            school=self.school,
            admission_number="RTS/2026/0001",
            first_name="Test",
            last_name="Student",
            gender="M",
            date_of_birth="2014-01-01",
            current_class=self.school_class,
            current_session=self.session,
            current_term=self.term,
        )
        GradeSetting.objects.create(
            school=self.school,
            grade="A",
            minimum_score=70,
            maximum_score=100,
            remark="Excellent",
        )
        GradeSetting.objects.create(
            school=self.school,
            grade="F",
            minimum_score=0,
            maximum_score=69,
            remark="Needs improvement",
        )

    def test_subject_result_save_recalculates_without_recursive_signal(self):
        result = StudentResult.objects.create(
            school=self.school,
            student=self.student,
            session=self.session,
            term=self.term,
            school_class=self.school_class,
        )

        subject_result = SubjectResult.objects.create(
            student_result=result,
            subject=self.subject,
            ca1=Decimal("15"),
            ca2=Decimal("15"),
            assignment=Decimal("10"),
            project=Decimal("10"),
            examination=Decimal("30"),
        )

        subject_result.refresh_from_db()
        result.refresh_from_db()

        self.assertEqual(subject_result.total, Decimal("80.00"))
        self.assertEqual(subject_result.grade, "A")
        self.assertEqual(subject_result.remark, "Excellent")
        self.assertEqual(result.total_score, Decimal("80.00"))
        self.assertEqual(result.average, Decimal("80.00"))
