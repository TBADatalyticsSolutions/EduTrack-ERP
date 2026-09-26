import io

from django.core.management import call_command
from django.test import TestCase

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassSubject,
    SchoolClass,
    Subject,
    Term,
)
from apps.accounts.models import ParentPortalLink, UserProfile
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.finance.models import InvoiceItem, Payment, StudentInvoice
from apps.notifications.models import Notification
from apps.results.models import (
    AssessmentType,
    GradeSetting,
    StudentResult,
    SubjectResult,
)
from apps.schools.models import School, SchoolSubscription
from apps.students.models import Student
from apps.teachers.models import Department, Teacher, TeacherSubject


DEMO_SCHOOL_CODES = (
    "AFAAB",
    "GIA",
    "CHC",
    "RCS",
    "BFA",
    "LIS",
    "HMC",
    "OBS",
    "SSA",
    "PIC",
)


STAGES = (
    "seed_demo_schools",
    "seed_demo_academics",
    "seed_demo_subjects_teaching",
    "seed_demo_academic_config",
    "seed_demo_students_portal",
    "seed_demo_finance",
    "seed_demo_attendance",
    "seed_demo_results",
    "seed_demo_notifications",
)


class FinalDemoIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for command_name in STAGES:
            call_command(command_name, stdout=io.StringIO())

    def test_all_demo_stages_coexist_with_expected_totals(self):
        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES
        )

        self.assertEqual(schools.count(), 10)
        self.assertEqual(
            SchoolSubscription.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            10,
        )

        self.assertEqual(
            AcademicSession.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            20,
        )
        self.assertEqual(
            Term.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            60,
        )
        self.assertEqual(
            SchoolClass.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            140,
        )
        self.assertEqual(
            ClassArm.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            280,
        )

        self.assertEqual(
            Subject.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            100,
        )
        self.assertEqual(
            ClassSubject.objects.filter(
                school_class__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            1400,
        )
        self.assertEqual(
            AssessmentType.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            30,
        )
        self.assertEqual(
            GradeSetting.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            60,
        )

        self.assertEqual(
            Department.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            40,
        )
        self.assertEqual(
            Teacher.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            50,
        )
        self.assertEqual(
            TeacherSubject.objects.filter(
                teacher__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            200,
        )

        self.assertEqual(
            Student.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            120,
        )
        self.assertEqual(
            UserProfile.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                role__code="STUDENT",
            ).count(),
            120,
        )
        self.assertEqual(
            UserProfile.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                role__code="PARENT",
            ).count(),
            60,
        )
        self.assertEqual(
            ParentPortalLink.objects.filter(
                parent__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            60,
        )

        self.assertEqual(
            StudentInvoice.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            120,
        )
        self.assertEqual(
            InvoiceItem.objects.filter(
                invoice__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            600,
        )
        self.assertEqual(
            Payment.objects.filter(
                invoice__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            100,
        )

        self.assertEqual(
            AttendanceSession.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            600,
        )
        self.assertEqual(
            AttendanceRecord.objects.filter(
                attendance_session__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            600,
        )

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
            Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            380,
        )
        self.assertEqual(
            Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                is_read=True,
            ).count(),
            160,
        )
        self.assertEqual(
            Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES,
                is_read=False,
            ).count(),
            220,
        )

    def test_tenant_isolation_and_current_term_consistency(self):
        for school in School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES
        ):
            current_session = school.sessions.get(
                name="2026/2027",
                is_current=True,
            )
            current_term = school.terms.get(
                session=current_session,
                name="First Term",
                is_current=True,
            )

            students = Student.objects.filter(
                school=school,
                current_session=current_session,
                current_term=current_term,
                status="ACTIVE",
            )
            self.assertEqual(students.count(), 12)

            self.assertEqual(
                StudentInvoice.objects.filter(school=school).exclude(
                    student__school=school
                ).count(),
                0,
            )
            self.assertEqual(
                StudentResult.objects.filter(school=school).exclude(
                    student__school=school
                ).count(),
                0,
            )
            self.assertEqual(
                AttendanceSession.objects.filter(school=school).exclude(
                    school_class__school=school
                ).count(),
                0,
            )
            self.assertEqual(
                Notification.objects.filter(school=school).exclude(
                    recipient__profile__school=school
                ).count(),
                0,
            )

    def test_deterministic_afaaB_cross_module_records(self):
        student = Student.objects.get(
            admission_number="AFAAB/2026/0001"
        )

        invoice = StudentInvoice.objects.get(
            student=student,
            session__name="2026/2027",
            term__name="First Term",
        )
        self.assertEqual(invoice.total_amount, 28500)
        self.assertEqual(invoice.balance, 18500)
        self.assertEqual(invoice.status, "PARTIAL")

        result = StudentResult.objects.get(student=student)
        self.assertEqual(result.total_score, 749)
        self.assertEqual(result.average, 74.90)
        self.assertEqual(result.position, 1)

        mathematics = SubjectResult.objects.get(
            student_result=result,
            subject__code="AFAAB-MAT",
        )
        self.assertEqual(mathematics.total, 68)
        self.assertEqual(mathematics.grade, "B")
        self.assertEqual(mathematics.remark, "Very Good")

        student_profile = UserProfile.objects.filter(
            school=student.school,
            role__code="STUDENT",
            user__is_active=True,
        ).order_by("user__username").first()
        self.assertIsNotNone(student_profile)

        notifications = Notification.objects.filter(
            school=student.school,
            recipient=student_profile.user,
        )
        self.assertEqual(notifications.count(), 2)

        attendance = AttendanceRecord.objects.filter(
            student=student,
            attendance_session__school=student.school,
        )
        self.assertEqual(attendance.count(), 5)

    def test_stage_commands_are_idempotent(self):
        before = {
            "schools": School.objects.filter(
                short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "students": Student.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "invoices": StudentInvoice.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "results": StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "attendance": AttendanceRecord.objects.filter(
                attendance_session__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "notifications": Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
        }

        for command_name in STAGES:
            call_command(command_name, stdout=io.StringIO())

        after = {
            "schools": School.objects.filter(
                short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "students": Student.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "invoices": StudentInvoice.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "results": StudentResult.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "attendance": AttendanceRecord.objects.filter(
                attendance_session__school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            "notifications": Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
        }

        self.assertEqual(after, before)
