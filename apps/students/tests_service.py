from datetime import date

from django.test import TestCase

from apps.academics.models import AcademicSession, SchoolClass, Term
from apps.schools.models import School

from .discipline import expel_student, reinstate_student_from_suspension, suspend_student
from .enrollment_forms import StudentEnrollmentForm
from .graduation import graduate_student
from .models import DisciplineHistory, GraduationHistory, PromotionHistory, Student
from .promotion import promote_student, promote_students
from .transfer import transfer_student
from .withdrawal import reinstate_student_service, withdraw_student


class StudentServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            short_name="TEST",
            email="test-school@example.com",
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
        self.other_session = AcademicSession.objects.create(
            school=self.school,
            name="2027/2028",
            is_active=True,
        )
        self.current_class = SchoolClass.objects.create(
            school=self.school,
            name="Primary 5",
            is_active=True,
        )
        self.next_class = SchoolClass.objects.create(
            school=self.school,
            name="Primary 6",
            is_active=True,
        )
        self.student = Student.objects.create(
            school=self.school,
            admission_number="TEST/2026/0001",
            first_name="Amina",
            last_name="Test",
            gender="F",
            date_of_birth=date(2014, 1, 1),
            current_class=self.current_class,
            current_session=self.session,
            current_term=self.term,
        )

    def test_bulk_promotion_updates_student_and_history(self):
        count = promote_students(
            self.current_class,
            self.next_class,
            self.session,
            self.term,
        )
        self.assertEqual(count, 1)
        self.student.refresh_from_db()
        self.assertEqual(self.student.current_class, self.next_class)
        self.assertEqual(self.student.current_term, self.term)
        self.assertEqual(PromotionHistory.objects.count(), 1)

    def test_individual_promotion_rejects_cross_school_class(self):
        other_school = School.objects.create(
            name="Other School",
            email="other-school@example.com",
        )
        other_class = SchoolClass.objects.create(
            school=other_school,
            name="Primary 6",
        )
        with self.assertRaises(ValueError):
            promote_student(self.student, other_class)

    def test_transfer_updates_class_and_creates_history(self):
        success, _ = transfer_student(
            self.student,
            self.next_class,
            self.other_session,
        )
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.current_class, self.next_class)
        self.assertEqual(self.student.current_session, self.other_session)
        self.assertEqual(self.student.status, "ACTIVE")

    def test_withdraw_and_reinstate(self):
        success, _ = withdraw_student(self.student, reason="Relocation")
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "WITHDRAWN")
        self.assertIsNone(self.student.current_class)

        history = self.student.withdrawal_history.first()
        success, _ = reinstate_student_service(history)
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "ACTIVE")
        self.assertEqual(self.student.current_class, self.current_class)

    def test_suspend_and_reinstate(self):
        success, _ = suspend_student(
            self.student,
            reason="MISCONDUCT",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
        )
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "SUSPENDED")

        history = DisciplineHistory.objects.get(student=self.student)
        success, _ = reinstate_student_from_suspension(history)
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "ACTIVE")

    def test_expel_clears_active_placement(self):
        success, _ = expel_student(self.student, reason="GROSS_MISCONDUCT")
        self.assertTrue(success)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "EXPELLED")
        self.assertIsNone(self.student.current_class)
        self.assertIsNone(self.student.current_session)

    def test_graduation_uses_actual_session_and_reason(self):
        graduate_student(self.student, "Completed Primary School")
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_graduated)
        self.assertEqual(self.student.status, "GRADUATED")
        self.assertEqual(self.student.graduation_session, "2026/2027")
        self.assertEqual(self.student.graduation_reason, "Completed Primary School")
        self.assertEqual(GraduationHistory.objects.count(), 1)


class StudentEnrollmentFormTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Enrollment School",
            email="enrollment-school@example.com",
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            is_active=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            session=self.session,
            name="First Term",
            is_active=True,
        )
        self.school_class = SchoolClass.objects.create(
            school=self.school,
            name="Primary 1",
            is_active=True,
        )

    def test_enrollment_form_only_exposes_school_records(self):
        other_school = School.objects.create(
            name="Other Enrollment School",
            email="other-enrollment@example.com",
        )
        other_class = SchoolClass.objects.create(
            school=other_school,
            name="Primary 1",
            is_active=True,
        )
        form = StudentEnrollmentForm(school=self.school)
        self.assertIn(self.school_class, form.fields["current_class"].queryset)
        self.assertNotIn(other_class, form.fields["current_class"].queryset)
