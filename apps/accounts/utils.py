from django.utils import timezone

from .models import ActivityLog


def log_activity(
    request,
    action,
    module,
    description,
    target_object="",
):
    """
    Create an audit log entry.

    Parameters
    ----------
    request : HttpRequest

    action : str
        CREATE
        UPDATE
        DELETE
        LOGIN
        LOGOUT
        EXPORT
        IMPORT
        PASSWORD_CHANGE
        etc.

    module : str
        Students
        Teachers
        Finance
        Results
        Attendance
        Accounts
        etc.

    description : str
        Human-readable description.

    target_object : str
        Optional object name or ID.
    """

    user = None

    if request and request.user.is_authenticated:
        user = request.user

    ip_address = None

    if request:

        forwarded = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded:

            ip_address = forwarded.split(",")[0]

        else:

            ip_address = request.META.get(
                "REMOTE_ADDR"
            )

    ActivityLog.objects.create(

        user=user,

        action=action,

        module=module,

        description=description,

        target_object=target_object,

        ip_address=ip_address,

        timestamp=timezone.now(),

    )