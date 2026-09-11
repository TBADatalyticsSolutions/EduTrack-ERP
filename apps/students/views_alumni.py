from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.decorators import role_required

from .models import GraduationHistory


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")


@login_required
@role_required(*ROLES)
def alumni_list(request):
    """Display graduated students belonging to the user's school."""
    profile = getattr(request.user, "profile", None)
    school = getattr(profile, "school", None)
    if not school:
        messages.error(request, "You are not associated with a school.")
        return redirect("dashboard:home")

    alumni = GraduationHistory.objects.filter(school=school).select_related(
        "student",
        "graduated_from",
    ).order_by("-graduation_date")

    return render(request, "students/alumni_list.html", {"alumni": alumni})
