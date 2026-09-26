from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import ParentPortalLink, UserProfile
from apps.notifications.models import Notification
from apps.schools.models import School


DEMO_SCHOOL_CODES = {
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
}


class SeedDemoNotificationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_schools", stdout=StringIO())
        call_command("seed_demo_academics", stdout=StringIO())
        call_command("seed_demo_subjects_teaching", stdout=StringIO())
        call_command("seed_demo_academic_config", stdout=StringIO())
        call_command("seed_demo_students_portal", stdout=StringIO())
        call_command("seed_demo_finance", stdout=StringIO())
        call_command("seed_demo_attendance", stdout=StringIO())
        call_command("seed_demo_results", stdout=StringIO())
        call_command("seed_demo_notifications", stdout=StringIO())

    def test_complete_notification_configuration(self):
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

        for school in School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES
        ):
            self.assertEqual(
                Notification.objects.filter(school=school).count(),
                38,
            )

    def test_notification_recipients_and_school_scope_are_safe(self):
        for notification in Notification.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES
        ).select_related("school", "recipient__profile__role"):
            profile = notification.recipient.profile
            self.assertEqual(profile.school_id, notification.school_id)
            self.assertIn(
                profile.role.code,
                {"SCHOOL_ADMIN", "STUDENT", "PARENT"},
            )

        self.assertEqual(
            Notification.objects.filter(
                recipient__profile__role__code="STUDENT"
            ).count(),
            240,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient__profile__role__code="PARENT"
            ).count(),
            120,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient__profile__role__code="SCHOOL_ADMIN"
            ).count(),
            20,
        )

    def test_deterministic_afaaB_notifications(self):
        school = School.objects.get(short_name="AFAAB")
        student = UserProfile.objects.get(
            school=school,
            role__code="STUDENT",
            user__username="AFAAB/2026/0001",
        ).user

        notice = Notification.objects.get(
            school=school,
            recipient=student,
            title="First Term Resumption Notice",
        )
        self.assertEqual(
            notice.message,
            "First Term 2026/2027 is now active. Check your portal for attendance, academic results, and school updates.",
        )
        self.assertEqual(notice.notification_type, "INFO")
        self.assertFalse(notice.is_read)
        self.assertIsNone(notice.read_at)

        parent_link = ParentPortalLink.objects.get(
            parent__school=school,
            user__username="AFAAB-P001",
        )
        parent_notice = Notification.objects.get(
            school=school,
            recipient=parent_link.user,
            title="Parent Finance Update",
        )
        self.assertEqual(parent_notice.notification_type, "WARNING")
        self.assertFalse(parent_notice.is_read)
        self.assertIsNone(parent_notice.read_at)

        admin = UserProfile.objects.get(
            school=school,
            role__code="SCHOOL_ADMIN",
            is_school_admin=True,
        ).user
        admin_notice = Notification.objects.get(
            school=school,
            recipient=admin,
            title="Welcome to EduTrack ERP Demo",
        )
        self.assertTrue(admin_notice.is_read)
        self.assertIsNotNone(admin_notice.read_at)

    def test_idempotent(self):
        before = Notification.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES
        ).count()

        call_command("seed_demo_notifications", stdout=StringIO())

        self.assertEqual(
            Notification.objects.filter(
                school__short_name__in=DEMO_SCHOOL_CODES
            ).count(),
            before,
        )

    def test_no_cross_school_recipient_leakage(self):
        for notification in Notification.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES
        ):
            self.assertEqual(
                notification.school_id,
                notification.recipient.profile.school_id,
            )

        for school in School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES
        ):
            school_user_ids = set(
                UserProfile.objects.filter(
                    school=school,
                    role__code__in=("SCHOOL_ADMIN", "STUDENT", "PARENT"),
                ).values_list("user_id", flat=True)
            )
            notification_user_ids = set(
                Notification.objects.filter(
                    school=school
                ).values_list("recipient_id", flat=True)
            )
            self.assertTrue(notification_user_ids.issubset(school_user_ids))
