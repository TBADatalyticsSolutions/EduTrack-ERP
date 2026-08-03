from django.urls import path

from .views import (
    student_list,
    promotion_index,
    promote_student,
    graduate_student_view,
    bulk_graduation,
)

from .views_alumni import (
    alumni_list,
)

from .views_bulk_transfer import (
    bulk_transfer_view,
)

from .views_transfer import (
    transfer_student_view,
    transfer_history,
    rollback_transfer,
)

from .views_withdrawal import (
    withdraw_student_view,
    withdrawal_history,
    reinstate_student,
)

from .views_discipline import (
    suspend_student_view,
    expel_student_view,
    suspension_history,
    expulsion_history,
    reinstate_suspended_student,
)
from .views_discipline_dashboard import (
    discipline_dashboard,
)

urlpatterns = [

    # =====================================================
    # Student Dashboard
    # =====================================================

    path(
        "",
        student_list,
        name="student-list",
    ),

    # =====================================================
    # Promotion
    # =====================================================

    path(
        "promotion/",
        promotion_index,
        name="promotion",
    ),

    path(
        "promote/<int:pk>/",
        promote_student,
        name="student-promote",
    ),

    # =====================================================
    # Graduation
    # =====================================================

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

    # =====================================================
    # Alumni
    # =====================================================

    path(
        "alumni/",
        alumni_list,
        name="alumni-list",
    ),

    # =====================================================
    # Student Transfer
    # =====================================================

    path(
        "transfer/<int:pk>/",
        transfer_student_view,
        name="transfer-student",
    ),

    path(
        "transfer/bulk/",
        bulk_transfer_view,
        name="bulk-transfer",
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

    # =====================================================
    # Student Withdrawal
    # =====================================================

    path(
        "withdraw/<int:pk>/",
        withdraw_student_view,
        name="withdraw-student",
    ),

    path(
        "withdrawals/",
        withdrawal_history,
        name="withdrawal-history",
    ),

    path(
        "withdrawals/<int:pk>/reinstate/",
        reinstate_student,
        name="reinstate-student",
    ),

    # =====================================================
    # Student Discipline
    # =====================================================

    path(
    "discipline/",
    discipline_dashboard,
    name="discipline-dashboard",
    ),

    path(
        "discipline/suspend/<int:pk>/",
        suspend_student_view,
        name="suspend-student",
    ),

    path(
        "discipline/expel/<int:pk>/",
        expel_student_view,
        name="expel-student",
    ),

    path(
        "discipline/suspensions/",
        suspension_history,
        name="suspension-history",
    ),

    path(
        "discipline/expulsions/",
        expulsion_history,
        name="expulsion-history",
    ),

    path(
        "discipline/suspensions/<int:pk>/reinstate/",
        reinstate_suspended_student,
        name="reinstate-suspended-student",
    ),

]