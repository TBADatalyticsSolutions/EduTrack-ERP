from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from django.shortcuts import render

from .models import GraduationHistory

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)

def alumni_list(request):

    alumni = GraduationHistory.objects.select_related(
        "student",
        "graduated_from",
        "school"
    ).order_by("-graduation_date")

    return render(
        request,
        "students/alumni_list.html",
        {
            "alumni": alumni,
        },
    )