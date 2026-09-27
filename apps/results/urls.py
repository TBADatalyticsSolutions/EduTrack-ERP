from django.urls import path
from .views import dashboard, result_list, result_create, result_detail, result_publish, psychomotor_update, settings

app_name = "results"
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("list/", result_list, name="list"),
    path("add/", result_create, name="create"),
    path("<uuid:pk>/", result_detail, name="detail"),
    path("<uuid:pk>/publish/", result_publish, name="publish"),
    path("<uuid:pk>/psychomotor/", psychomotor_update, name="psychomotor_update"),
    path("settings/", settings, name="settings"),
]
