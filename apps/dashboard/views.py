from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.finance.models import StudentInvoice
from apps.results.models import StudentResult


@login_required
def dashboard(request):

    recent_students = Student.objects.order_by("-created_at")[:5]

    recent_results = StudentResult.objects.order_by("-created_at")[:5]

    recent_invoices = StudentInvoice.objects.order_by("-created_at")[:5]

    context = {

        "student_count": Student.objects.count(),

        "teacher_count": Teacher.objects.count(),

        "invoice_count": StudentInvoice.objects.count(),

        "result_count": StudentResult.objects.count(),

        "recent_students": recent_students,

        "recent_results": recent_results,

        "recent_invoices": recent_invoices,

    }

    return render(
        request,
        "dashboard/index.html",
        context,
    )