from django.urls import path
from .views import dashboard, student_report, class_report, result_report

app_name = "reports"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("student/<uuid:pk>/", student_report, name="student"),
    path("class/<uuid:pk>/", class_report, name="class"),
    path("result/<uuid:pk>/", result_report, name="result"),
]
