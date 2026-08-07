def has_role(user, *roles):

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    profile = getattr(
        user,
        "profile",
        None,
    )

    if not profile:
        return False

    if not profile.role:
        return False

    return profile.role.code in roles