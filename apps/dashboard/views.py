from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services.dashboard_service import DashboardService


@login_required
def dashboard(request):

    context = DashboardService.get_dashboard_data()

    return render(
        request,
        "dashboard/index.html",
        context,
    )