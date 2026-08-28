from django.urls import path
from .views import notification_dashboard, notification_create, notification_read

app_name = "notifications"

urlpatterns = [
    path("", notification_dashboard, name="dashboard"),
    path("send/", notification_create, name="create"),
    path("<uuid:pk>/read/", notification_read, name="read"),
]
