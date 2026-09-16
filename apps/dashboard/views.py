from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .services.dashboard_service import DashboardService

PLATFORM_ROLES = {"SUPER_ADMIN"}
TENANT_ROLES = {
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "VICE_PRINCIPAL",
    "REGISTRAR",
    "ACCOUNTANT",
    "LIBRARIAN",
}


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(getattr(profile, "role", None), "code", None)

    if role in {"STUDENT", "PARENT"}:
        return redirect("portal-dashboard")
    if role == "TEACHER":
        return redirect("results:dashboard")

    if request.user.is_superuser or role in PLATFORM_ROLES:
        context = DashboardService.get_platform_dashboard_data()
    elif role in TENANT_ROLES:
        school = getattr(profile, "school", None)
        if school is None:
            return render(
                request,
                "dashboard/index.html",
                {
                    "dashboard_scope": "school",
                    "school": None,
                    "tenant_error": "Your account is not assigned to a school. Contact the platform administrator.",
                },
                status=403,
            )
        context = DashboardService.get_dashboard_data(school=school)
    else:
        return redirect("profile")

    return render(request, "dashboard/index.html", context)
