from django.urls import path

from .views import (
    bulk_graduation,
    graduate_student_view,
    promotion_index,
    student_list,
    transfer_student_view,
)
from .views_alumni import alumni_list
from .views_transfer import (
    rollback_transfer,
    transfer_history,
)

urlpatterns = [

    # ==========================
    # Students
    # ==========================

    path(
        "",
        student_list,
        name="student-list",
    ),

    # ==========================
    # Promotion
    # ==========================

    path(
        "promotion/",
        promotion_index,
        name="promotion",
    ),

    # ==========================
    # Graduation
    # ==========================

    path(
        "graduate/<int:pk>/",
        graduate_student_view,
        name="graduate-student",
    ),

    path(
        "graduation/bulk/",
        bulk_graduation,
        name="bulk-graduation",
    ),

    # ==========================
    # Alumni
    # ==========================

    path(
        "alumni/",
        alumni_list,
        name="alumni-list",
    ),

    # ==========================
    # Transfer
    # ==========================

    path(
        "transfer/<int:pk>/",
        transfer_student_view,
        name="transfer-student",
    ),

    path(
        "transfers/",
        transfer_history,
        name="transfer-history",
    ),

    path(
        "transfers/<int:pk>/rollback/",
        rollback_transfer,
        name="rollback-transfer",
    ),

]