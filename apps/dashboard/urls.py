from django.urls import path
from apps.accounts.utils import log_activity
from . import views
from apps.accounts.utils import log_activity

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="home"),
]