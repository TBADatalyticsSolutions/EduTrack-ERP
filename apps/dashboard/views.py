from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.finance.models import StudentInvoice
from apps.results.models import StudentResult


@login_required
def dashboard(request):
    context = {
        "student_count": Student.objects.count(),
        "teacher_count": Teacher.objects.count(),
        "invoice_count": StudentInvoice.objects.count(),
        "result_count": StudentResult.objects.count(),
    }

    return render(
        request,
        "dashboard/index.html",
        context,
    )