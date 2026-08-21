from django.utils import timezone

from .models import ActivityLog


def log_activity(
    request,
    action,
    module,
    description,
):
    """
    Create a reusable audit/activity log entry.

    Parameters
    ----------
    request : HttpRequest
        Current Django request.

    action : str
        Examples:
        CREATE
        UPDATE
        DELETE
        LOGIN
        LOGOUT
        EXPORT
        IMPORT
        PASSWORD_CHANGE
        PASSWORD_RESET

    module : str
        Examples:
        Accounts
        Students
        Teachers
        Finance
        Results
        Attendance
        Reports
        Library

    description : str
        Human-readable description of the activity.
    """

    # ------------------------------------------------------
    # USER
    # ------------------------------------------------------

    user = None

    if request and request.user.is_authenticated:
        user = request.user

    # ------------------------------------------------------
    # IP ADDRESS
    # ------------------------------------------------------

    ip_address = None

    if request:

        forwarded = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded:
            ip_address = forwarded.split(",")[0].strip()

        else:
            ip_address = request.META.get(
                "REMOTE_ADDR"
            )

    # ------------------------------------------------------
    # USER AGENT
    # ------------------------------------------------------

    user_agent = None

    if request:
        user_agent = request.META.get(
            "HTTP_USER_AGENT"
        )

    # ------------------------------------------------------
    # SCHOOL
    # ------------------------------------------------------

    school = None

    if user and hasattr(user, "profile"):

        school = getattr(
            user.profile,
            "school",
            None,
        )

    # ------------------------------------------------------
    # CREATE ACTIVITY LOG
    # ------------------------------------------------------

    ActivityLog.objects.create(

        user=user,

        school=school,

        action=action,

        module=module,

        description=description,

        ip_address=ip_address,

        user_agent=user_agent,
    )