from django import template

register = template.Library()


@register.filter
def has_role(user, role):

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

    return profile.role.code == role