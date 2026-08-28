from django.urls import path

from .views import settings_dashboard

app_name = "system_settings"

urlpatterns = [
    path("", settings_dashboard, name="dashboard"),
]
