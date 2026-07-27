from django.urls import path

from .views import attendance_register

app_name = "attendance"

urlpatterns = [

    path(
        "",
        attendance_register,
        name="register",
    ),

]