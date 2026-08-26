from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.finance.models import StudentInvoice, Payment
from apps.results.models import StudentResult


class DashboardService:

    @staticmethod
    def get_dashboard_data():

        # ==============================
        # KPI COUNTS
        # ==============================

        student_count = Student.objects.count()

        teacher_count = Teacher.objects.count()

        invoice_count = StudentInvoice.objects.count()

        result_count = StudentResult.objects.filter(
            published=True
        ).count()

        # ==============================
        # FINANCIALS
        # ==============================

        total_revenue = (
            Payment.objects.aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        outstanding = (
            StudentInvoice.objects.aggregate(
                total=Sum("balance")
            )["total"] or 0
        )

        # ==============================
        # GENDER DISTRIBUTION
        # ==============================

        male_students = Student.objects.filter(
            gender="M"
        ).count()

        female_students = Student.objects.filter(
            gender="F"
        ).count()

        # ==============================
        # MONTHLY REVENUE
        # ==============================

        monthly_revenue = (
            Payment.objects
            .annotate(
                month=TruncMonth("created_at")
            )
            .values("month")
            .annotate(
                total=Sum("amount")
            )
            .order_by("month")
        )

        # ==============================
        # MONTHLY STUDENT ADMISSION
        # ==============================

        monthly_students = (
            Student.objects
            .annotate(
                month=TruncMonth("created_at")
            )
            .values("month")
            .annotate(
                total=Count("id")
            )
            .order_by("month")
        )

        # ==============================
        # INVOICE STATUS
        # ==============================

        paid = StudentInvoice.objects.filter(
            status="PAID"
        ).count()

        partial = StudentInvoice.objects.filter(
            status="PARTIAL"
        ).count()

        unpaid = StudentInvoice.objects.filter(
            status="UNPAID"
        ).count()

        # ==============================
        # RECENT RECORDS
        # ==============================

        recent_students = (
            Student.objects
            .order_by("-created_at")[:10]
        )

        recent_payments = (
            Payment.objects
            .select_related(
                "invoice",
                "invoice__student"
            )
            .order_by("-created_at")[:10]
        )

        recent_results = (
            StudentResult.objects
            .select_related("student")
            .order_by("-created_at")[:10]
        )

        return {

            "student_count": student_count,

            "teacher_count": teacher_count,

            "invoice_count": invoice_count,

            "result_count": result_count,

            "total_revenue": total_revenue,

            "outstanding": outstanding,

            "male_students": male_students,

            "female_students": female_students,

            "monthly_revenue": monthly_revenue,

            "monthly_students": monthly_students,

            "paid": paid,

            "partial": partial,

            "unpaid": unpaid,

            "recent_students": recent_students,

            "recent_payments": recent_payments,

            "recent_results": recent_results,

        }
