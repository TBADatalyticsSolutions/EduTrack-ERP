from django.urls import reverse

from apps.notifications.forms import NotificationForm
from apps.notifications.models import Notification

from .tests import AccessControlRegressionTests


class PortalFeatureTests(AccessControlRegressionTests):
    """Regression coverage for portal notices and receipt access."""

    def test_student_can_view_own_payment_receipt(self):
        self.client.force_login(self.student_user)
        response = self.client.get(
            reverse("finance:payment-receipt", args=[self.payment_a.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Official Payment Receipt")
        self.assertContains(response, self.invoice_a.invoice_number)
        self.assertContains(response, "Back to Portal")

    def test_student_cannot_view_another_students_receipt(self):
        self.client.force_login(self.student_user)
        payment_b = self.payment_a.__class__.objects.create(
            invoice=self.invoice_b,
            amount=5000,
            settlement_type="PAYMENT",
            payment_method="CASH",
        )

        response = self.client.get(
            reverse("finance:payment-receipt", args=[payment_b.pk]),
        )

        self.assertEqual(response.status_code, 404)

    def test_student_portal_displays_and_reads_notice(self):
        notice = Notification.objects.create(
            school=self.school,
            recipient=self.student_user,
            title="Resumption Notice",
            message="School resumes on Monday.",
            notification_type="INFO",
        )
        self.client.force_login(self.student_user)

        response = self.client.get(reverse("portal-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumption Notice")
        self.assertContains(response, "School resumes on Monday.")
        self.assertContains(response, "Notices & Notifications")

        read_response = self.client.get(
            reverse("notifications:portal-read", args=[notice.pk]),
        )
        self.assertEqual(read_response.status_code, 302)
        notice.refresh_from_db()
        self.assertTrue(notice.is_read)
        self.assertIsNotNone(notice.read_at)

    def test_school_notice_form_allows_student_broadcast_without_recipient(self):
        form = NotificationForm(
            data={
                "recipient": "",
                "send_to_all_students": "on",
                "title": "School Notice",
                "message": "Important school announcement.",
                "notification_type": "WARNING",
            },
            school=self.school,
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
