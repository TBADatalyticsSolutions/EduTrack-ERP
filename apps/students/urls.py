from django.urls import path

from .views import (
    student_list,
    promotion_index,
    promote_student_view,
    graduate_student_view,
    bulk_graduation,
)
from .views_alumni import alumni_list
from .views_bulk_transfer import bulk_transfer_view
from .views_discipline import (
    discipline_dashboard,
    expel_student_view,
    expulsion_history,
    reinstate_suspended_student,
    suspend_student_view,
    suspension_history,
)
from .views_enrollment import (
    student_detail,
    student_edit,
    student_enrol,
)
from .views_transfer import (
    rollback_transfer,
    transfer_history,
    transfer_student_view,
)
from .views_withdrawal import (
    reinstate_student,
    withdrawal_history,
    withdraw_student_view,
)

urlpatterns = [
    path("", student_list, name="student-list"),
    path("enrol/", student_enrol, name="student-enrol"),
    path("add/", student_enrol, name="student-add"),
    path("<uuid:pk>/", student_detail, name="student-detail"),
    path("<uuid:pk>/edit/", student_edit, name="student-edit"),

    path("promotion/", promotion_index, name="promotion"),
    path("promote/<uuid:pk>/", promote_student_view, name="student-promote"),

    path("graduate/<uuid:pk>/", graduate_student_view, name="graduate-student"),
    path("graduation/bulk/", bulk_graduation, name="bulk-graduation"),

    path("alumni/", alumni_list, name="alumni-list"),

    path("transfer/<uuid:pk>/", transfer_student_view, name="transfer-student"),
    path("transfer/bulk/", bulk_transfer_view, name="bulk-transfer"),
    path("transfers/", transfer_history, name="transfer-history"),
    path("transfers/<uuid:pk>/rollback/", rollback_transfer, name="rollback-transfer"),

    path("withdraw/<uuid:pk>/", withdraw_student_view, name="withdraw-student"),
    path("withdrawals/", withdrawal_history, name="withdrawal-history"),
    path("withdrawals/<uuid:pk>/reinstate/", reinstate_student, name="reinstate-student"),

    path("discipline/", discipline_dashboard, name="discipline-dashboard"),
    path("discipline/suspend/<uuid:pk>/", suspend_student_view, name="suspend-student"),
    path("discipline/expel/<uuid:pk>/", expel_student_view, name="expel-student"),
    path("discipline/suspensions/", suspension_history, name="suspension-history"),
    path("discipline/expulsions/", expulsion_history, name="expulsion-history"),
    path(
        "discipline/suspensions/<uuid:pk>/reinstate/",
        reinstate_suspended_student,
        name="reinstate-suspended-student",
    ),
]
