from django.urls import path
from apps.accounts.utils import log_activity

from .views import attendance_register
from apps.accounts.utils import log_activity

app_name = "attendance"

urlpatterns = [

    path(
        "",
        attendance_register,
        name="register",
    ),

]