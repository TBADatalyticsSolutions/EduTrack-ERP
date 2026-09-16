from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from apps.schools.models import SchoolSubscription


PLATFORM_ROLES = {"SUPER_ADMIN"}


def role_required(*allowed_roles):
    """Restrict a view to a role and an active school tenant."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(request.user, "profile", None)
            if profile is None:
                messages.error(request, "Profile not found.")
                return redirect("dashboard:home")

            if profile.role is None:
                messages.error(request, "No role assigned.")
                return redirect("dashboard:home")

            role = profile.role.code
            if role not in allowed_roles:
                messages.error(request, "Permission denied.")
                return redirect("dashboard:home")

            if role not in PLATFORM_ROLES:
                school = getattr(profile, "school", None)
                if school is None:
                    messages.error(
                        request,
                        "Your account is not assigned to a school tenant.",
                    )
                    return redirect("profile")

                subscription = SchoolSubscription.objects.filter(
                    school=school,
                ).first()
                if not subscription or subscription.status != "ACTIVE":
                    messages.error(
                        request,
                        "Your school's EduTrack subscription is not active.",
                    )
                    return redirect("profile")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
