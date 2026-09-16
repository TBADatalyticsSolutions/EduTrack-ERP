from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

from apps.finance.models import Payment, StudentInvoice
from apps.results.models import StudentResult
from apps.schools.models import School, SchoolSubscription
from apps.students.models import Student
from apps.teachers.models import Teacher


class DashboardService:
    """Return either platform-level or tenant-scoped dashboard data."""

    @staticmethod
    def get_platform_dashboard_data():
        """Platform view: subscription metrics only, never school records."""
        active_subscriptions = SchoolSubscription.objects.filter(
            school__is_active=True,
            is_active=True,
            status="ACTIVE",
        )
        return {
            "dashboard_scope": "platform",
            "subscribed_school_count": active_subscriptions.count(),
            "active_school_count": School.objects.filter(is_active=True).count(),
            "past_due_school_count": SchoolSubscription.objects.filter(
                school__is_active=True,
                is_active=True,
                status="PAST_DUE",
            ).count(),
            "suspended_school_count": SchoolSubscription.objects.filter(
                school__is_active=True,
                is_active=True,
                status="SUSPENDED",
            ).count(),
        }

    @staticmethod
    def get_dashboard_data(school=None):
        """Return metrics restricted to one school tenant."""
        if school is None:
            return DashboardService.get_platform_dashboard_data()

        students = Student.objects.filter(school=school)
        teachers = Teacher.objects.filter(school=school)
        invoices = StudentInvoice.objects.filter(school=school)
        payments = Payment.objects.filter(invoice__school=school)
        results = StudentResult.objects.filter(school=school)

        monthly_revenue = (
            payments.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )
        monthly_students = (
            students.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        return {
            "dashboard_scope": "school",
            "school": school,
            "student_count": students.count(),
            "teacher_count": teachers.count(),
            "invoice_count": invoices.count(),
            "result_count": results.filter(published=True).count(),
            "total_revenue": payments.aggregate(total=Sum("amount"))["total"] or 0,
            "outstanding": invoices.aggregate(total=Sum("balance"))["total"] or 0,
            "male_students": students.filter(gender="M").count(),
            "female_students": students.filter(gender="F").count(),
            "monthly_revenue": monthly_revenue,
            "monthly_students": monthly_students,
            "paid": invoices.filter(status="PAID").count(),
            "partial": invoices.filter(status="PARTIAL").count(),
            "unpaid": invoices.filter(status="UNPAID").count(),
            "recent_students": students.order_by("-created_at")[:10],
            "recent_payments": payments.select_related(
                "invoice", "invoice__student"
            ).order_by("-created_at")[:10],
            "recent_results": results.select_related(
                "student"
            ).order_by("-created_at")[:10],
        }
