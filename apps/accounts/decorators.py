from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Restrict a view to one or more roles.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.is_superuser:
                return view_func(
                    request,
                    *args,
                    **kwargs,
                )

            profile = getattr(
                request.user,
                "profile",
                None,
            )

            if profile is None:
                messages.error(
                    request,
                    "Profile not found.",
                )
                return redirect("dashboard")

            if profile.role is None:
                messages.error(
                    request,
                    "No role assigned.",
                )
                return redirect("dashboard")

            if profile.role.code not in allowed_roles:
                messages.error(
                    request,
                    "Permission denied.",
                )
                return redirect("dashboard")

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator