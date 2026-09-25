from datetime import date

from django.core.management import call_command
from django.test import TestCase

from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.notifications.models import Notification
from apps.results.models import StudentResult
from apps.schools.models import School
from apps.students.models import Student


class SeedDemoAttendanceCommandTests(TestCase):
    def setUp(self):
        call_command("seed_roles")
        call_command("seed_demo_schools")
        call_command("seed_demo_academics")
        call_command("seed_demo_subjects_teaching")
        call_command("seed_demo_academic_config")
        call_command("seed_demo_students_portal")

    def test_complete_attendance_configuration(self):
        call_command("seed_demo_attendance")

        self.assertEqual(AttendanceSession.objects.count(), 600)
        self.assertEqual(AttendanceRecord.objects.count(), 600)

        self.assertEqual(
            AttendanceRecord.objects.filter(status=AttendanceRecord.PRESENT).count(),
            240,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(status=AttendanceRecord.LATE).count(),
            120,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(status=AttendanceRecord.ABSENT).count(),
            120,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(status=AttendanceRecord.EXCUSED).count(),
            120,
        )

    def test_attendance_is_tenant_and_academic_scope_safe(self):
        call_command("seed_demo_attendance")

        for attendance_session in AttendanceSession.objects.select_related(
            "school",
            "school_class__school",
            "academic_session__school",
            "term__school",
        ):
            self.assertEqual(
                attendance_session.school_id,
                attendance_session.school_class.school_id,
            )
            self.assertEqual(
                attendance_session.school_id,
                attendance_session.academic_session.school_id,
            )
            self.assertEqual(
                attendance_session.school_id,
                attendance_session.term.school_id,
            )
            self.assertEqual(
                attendance_session.term.session_id,
                attendance_session.academic_session_id,
            )

        for record in AttendanceRecord.objects.select_related(
            "attendance_session__school",
            "student__school",
        ):
            self.assertEqual(
                record.student.school_id,
                record.attendance_session.school_id,
            )
            self.assertEqual(
                record.student.current_class_id,
                record.attendance_session.school_class_id,
            )

    def test_five_school_days_per_populated_class(self):
        call_command("seed_demo_attendance")

        for school in School.objects.all():
            sessions = AttendanceSession.objects.filter(school=school)
            self.assertEqual(sessions.count(), 60)

            dates = list(
                sessions.values_list("attendance_date", flat=True).distinct()
            )
            self.assertEqual(
                dates,
                [
                    date(2026, 9, 18),
                    date(2026, 9, 17),
                    date(2026, 9, 16),
                    date(2026, 9, 15),
                    date(2026, 9, 14),
                ],
            )

            self.assertEqual(
                sessions.values("school_class_id").distinct().count(),
                12,
            )

    def test_deterministic_afaaB_attendance(self):
        call_command("seed_demo_attendance")

        student = Student.objects.get(
            admission_number="AFAAB/2026/0001"
        )
        records = AttendanceRecord.objects.filter(
            student=student,
        ).select_related("attendance_session").order_by(
            "attendance_session__attendance_date"
        )

        self.assertEqual(records.count(), 5)
        self.assertEqual(
            student.current_class.name,
            "Nursery 1",
        )
        self.assertEqual(
            [
                record.status
                for record in records
            ],
            [
                AttendanceRecord.PRESENT,
                AttendanceRecord.PRESENT,
                AttendanceRecord.LATE,
                AttendanceRecord.ABSENT,
                AttendanceRecord.EXCUSED,
            ],
        )
        self.assertEqual(
            records.first().attendance_session.attendance_date,
            date(2026, 9, 14),
        )

    def test_idempotent(self):
        call_command("seed_demo_attendance")
        call_command("seed_demo_attendance")

        self.assertEqual(AttendanceSession.objects.count(), 600)
        self.assertEqual(AttendanceRecord.objects.count(), 600)

    def test_does_not_seed_results_or_notifications(self):
        call_command("seed_demo_attendance")

        self.assertEqual(StudentResult.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
