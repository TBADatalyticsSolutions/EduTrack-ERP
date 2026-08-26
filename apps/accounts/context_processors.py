from .permissions import has_role


def role_context(request):

    return {
        "is_super_admin": has_role(
            request.user,
            "SUPER_ADMIN",
        ),

        "is_school_admin": has_role(
            request.user,
            "SCHOOL_ADMIN",
        ),

        "is_principal": has_role(
            request.user,
            "PRINCIPAL",
        ),

        "is_teacher": has_role(
            request.user,
            "TEACHER",
        ),

        "is_accountant": has_role(
            request.user,
            "ACCOUNTANT",
        ),

        "is_parent": has_role(
            request.user,
            "PARENT",
        ),

        "is_student": has_role(
            request.user,
            "STUDENT",
        ),
    }
