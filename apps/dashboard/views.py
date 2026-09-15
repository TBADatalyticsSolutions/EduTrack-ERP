from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .services.dashboard_service import DashboardService


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(getattr(profile, "role", None), "code", None)

    if role in {"STUDENT", "PARENT"}:
        return redirect("portal-dashboard")
    if role == "TEACHER":
        return redirect("results:dashboard")

    context = DashboardService.get_dashboard_data()
    return render(request, "dashboard/index.html", context)
