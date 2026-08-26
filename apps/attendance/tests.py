from datetime import date

from django.test import TestCase
from django.utils import timezone

from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)

from .models import (
    AttendanceSession,
    AttendanceRecord,
)

from .services import AttendanceService


# ===========================================================
# TEST DATA MIXIN
# ===========================================================

class AttendanceTestDataMixin:

    def create_test_data(self):

        # ---------------------------------------------------
        # SCHOOL
        # ---------------------------------------------------

        self.school = School.objects.create(
            name="Test School",
        )

        # ---------------------------------------------------
        # ACADEMIC SESSION
        # ---------------------------------------------------

        self.academic_session = AcademicSession.objects.create(
            school=self.school,
            name="2025/2026",
            is_current=True,
        )

        # ---------------------------------------------------
        # TERM
        # IMPORTANT:
        # Term model uses "session", NOT "academic_session"
        # ---------------------------------------------------

        self.term = Term.objects.create(
            school=self.school,
            session=self.academic_session,
            name="First Term",
            is_current=True,
        )

        # ---------------------------------------------------
        # CLASS
        # ---------------------------------------------------

        self.school_class = SchoolClass.objects.create(
            school=self.school,
            name="JSS 1",
        )

        # ---------------------------------------------------
        # STUDENTS
        # ---------------------------------------------------

        self.student1 = Student.objects.create(
            school=self.school,
            admission_number="TEST001",
            first_name="John",
            last_name="Doe",
            gender="M",
            date_of_birth=date(2012, 1, 1),
            current_class=self.school_class,
            current_session=self.academic_session,
            status="ACTIVE",
            is_graduated=False,
        )

        self.student2 = Student.objects.create(
            school=self.school,
            admission_number="TEST002",
            first_name="Jane",
            last_name="Doe",
            gender="F",
            date_of_birth=date(2012, 2, 1),
            current_class=self.school_class,
            current_session=self.academic_session,
            status="ACTIVE",
            is_graduated=False,
        )

        # ---------------------------------------------------
        # ATTENDANCE DATE
        # ---------------------------------------------------

        self.attendance_date = timezone.localdate()


# ===========================================================
# ATTENDANCE SESSION MODEL TESTS
# ===========================================================

class AttendanceSessionModelTests(
    AttendanceTestDataMixin,
    TestCase,
):

    def setUp(self):

        self.create_test_data()

    # -------------------------------------------------------
    # CREATE ATTENDANCE SESSION
    # -------------------------------------------------------

    def test_attendance_session_can_be_created(self):

        session = AttendanceSession.objects.create(
            school=self.school,
            school_class=self.school_class,
            academic_session=self.academic_session,
            term=self.term,
            attendance_date=self.attendance_date,
        )

        self.assertIsNotNone(session.pk)

        self.assertEqual(
            session.school,
            self.school,
        )

        self.assertEqual(
            session.school_class,
            self.school_class,
        )

        self.assertEqual(
            session.academic_session,
            self.academic_session,
        )

        self.assertEqual(
            session.term,
            self.term,
        )

        self.assertEqual(
            session.attendance_date,
            self.attendance_date,
        )

    # -------------------------------------------------------
    # DUPLICATE SESSION
    # -------------------------------------------------------

    def test_duplicate_attendance_session_is_not_allowed(self):

        AttendanceSession.objects.create(
            school=self.school,
            school_class=self.school_class,
            academic_session=self.academic_session,
            term=self.term,
            attendance_date=self.attendance_date,
        )

        with self.assertRaises(Exception):

            AttendanceSession.objects.create(
                school=self.school,
                school_class=self.school_class,
                academic_session=self.academic_session,
                term=self.term,
                attendance_date=self.attendance_date,
            )


# ===========================================================
# ATTENDANCE SERVICE TESTS
# ===========================================================

class AttendanceServiceTests(
    AttendanceTestDataMixin,
    TestCase,
):

    def setUp(self):

        self.create_test_data()

        self.session, self.created = (
            AttendanceService.get_or_create_session(
                school=self.school,
                school_class=self.school_class,
                academic_session=self.academic_session,
                term=self.term,
                attendance_date=self.attendance_date,
                user=None,
            )
        )

    # -------------------------------------------------------
    # GET OR CREATE SESSION
    # -------------------------------------------------------

    def test_get_or_create_session_returns_existing_session(
        self,
    ):

        session, created = (
            AttendanceService.get_or_create_session(
                school=self.school,
                school_class=self.school_class,
                academic_session=self.academic_session,
                term=self.term,
                attendance_date=self.attendance_date,
                user=None,
            )
        )

        self.assertEqual(
            session.pk,
            self.session.pk,
        )

        self.assertFalse(created)

        self.assertEqual(
            AttendanceSession.objects.count(),
            1,
        )

    # -------------------------------------------------------
    # CLOSE SESSION
    # -------------------------------------------------------

    def test_session_can_be_closed(self):

        self.assertTrue(
            self.session.is_active
        )

        AttendanceService.close_session(
            self.session,
            user=None,
        )

        self.session.refresh_from_db()

        self.assertFalse(
            self.session.is_active
        )

    # -------------------------------------------------------
    # REOPEN SESSION
    # -------------------------------------------------------

    def test_session_can_be_reopened(self):

        AttendanceService.close_session(
            self.session,
            user=None,
        )

        self.session.refresh_from_db()

        self.assertFalse(
            self.session.is_active
        )

        AttendanceService.reopen_session(
            self.session,
            user=None,
        )

        self.session.refresh_from_db()

        self.assertTrue(
            self.session.is_active
        )


# ===========================================================
# ATTENDANCE RECORD TESTS
# ===========================================================

class AttendanceRecordTests(
    AttendanceTestDataMixin,
    TestCase,
):

    def setUp(self):

        self.create_test_data()

        self.session, self.created = (
            AttendanceService.get_or_create_session(
                school=self.school,
                school_class=self.school_class,
                academic_session=self.academic_session,
                term=self.term,
                attendance_date=self.attendance_date,
                user=None,
            )
        )

    # -------------------------------------------------------
    # STATUS CHOICES
    # -------------------------------------------------------

    def test_attendance_record_status_choices_exist(self):

        statuses = dict(
            AttendanceRecord.STATUS_CHOICES
        )

        self.assertIn(
            AttendanceRecord.PRESENT,
            statuses,
        )

        self.assertIn(
            AttendanceRecord.ABSENT,
            statuses,
        )

        self.assertIn(
            AttendanceRecord.LATE,
            statuses,
        )

        self.assertIn(
            AttendanceRecord.EXCUSED,
            statuses,
        )

    # -------------------------------------------------------
    # MARK STUDENT PRESENT
    # -------------------------------------------------------

    def test_student_can_be_marked_present(self):

        record = AttendanceService.mark_student(
            attendance_session=self.session,
            student=self.student1,
            status=AttendanceRecord.PRESENT,
            user=None,
        )

        self.assertIsNotNone(
            record.pk
        )

        self.assertEqual(
            record.student,
            self.student1,
        )

        self.assertEqual(
            record.attendance_session,
            self.session,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.PRESENT,
        )

    # -------------------------------------------------------
    # CHANGE ATTENDANCE STATUS
    # -------------------------------------------------------

    def test_student_attendance_status_can_be_updated(self):

        record = AttendanceService.mark_student(
            attendance_session=self.session,
            student=self.student1,
            status=AttendanceRecord.PRESENT,
            user=None,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.PRESENT,
        )

        record = AttendanceService.mark_student(
            attendance_session=self.session,
            student=self.student1,
            status=AttendanceRecord.LATE,
            user=None,
        )

        record.refresh_from_db()

        self.assertEqual(
            record.status,
            AttendanceRecord.LATE,
        )

        self.assertEqual(
            AttendanceRecord.objects.filter(
                attendance_session=self.session,
                student=self.student1,
            ).count(),
            1,
        )
