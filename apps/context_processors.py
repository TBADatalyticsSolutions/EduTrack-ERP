def current_user_role(request):

    role = None

    if request.user.is_authenticated:

        profile = getattr(request.user, "userprofile", None)

        if profile:
            role = profile.role

    return {
        "current_role": role
    }
