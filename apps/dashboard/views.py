from django.contrib.auth.decorators import login_required
from apps.accounts.utils import log_activity
from django.shortcuts import render
from apps.accounts.utils import log_activity

from .services.dashboard_service import DashboardService
from apps.accounts.utils import log_activity


@login_required
def dashboard(request):

    context = DashboardService.get_dashboard_data()

    return render(
        request,
        "dashboard/index.html",
        context,
    )