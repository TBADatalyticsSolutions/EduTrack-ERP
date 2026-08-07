from django.contrib.auth.decorators import login_required
from apps.accounts.utils import log_activity
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from django.shortcuts import render
from apps.accounts.utils import log_activity

from .models import GraduationHistory
from apps.accounts.utils import log_activity

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