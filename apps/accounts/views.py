from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.accounts.utils import log_activity
from apps.students.models import Student
from apps.teachers.models import Teacher

from .decorators import role_required
from .forms import UserForm, UserProfileForm


# ==========================================================
# ACCOUNTS DASHBOARD
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def accounts_dashboard(request):
    """
    Display Accounts Management dashboard.
    """

    context = {
        "total_users": User.objects.count(),

        "active_users": User.objects.filter(
            is_active=True
        ).count(),

        "inactive_users": User.objects.filter(
            is_active=False
        ).count(),

        "teachers": Teacher.objects.count(),

        "students": Student.objects.count(),
    }

    return render(
        request,
        "accounts/dashboard.html",
        context,
    )


# ==========================================================
# USER LIST
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_list(request):
    """
    Display all user accounts.
    """

    users = (
        User.objects
        .select_related(
            "profile",
            "profile__role",
            "profile__school",
        )
        .order_by(
            "username",
        )
    )

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
        },
    )


# ==========================================================
# CREATE USER
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_create(request):
    """
    Create a new user account and associated profile.
    """

    if request.method == "POST":

        user_form = UserForm(
            request.POST,
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
        )

        if (
            user_form.is_valid()
            and profile_form.is_valid()
        ):

            with transaction.atomic():

                # ------------------------------------------
                # CREATE USER
                # ------------------------------------------

                user = user_form.save(
                    commit=False,
                )

                password = (
                    user_form.cleaned_data.get(
                        "password",
                    )
                )

                if password:
                    user.password = make_password(
                        password,
                    )

                user.save()

                # ------------------------------------------
                # UPDATE AUTOMATICALLY CREATED PROFILE
                # ------------------------------------------

                profile = user.profile

                profile_form = UserProfileForm(
                    request.POST,
                    request.FILES,
                    instance=profile,
                )

                profile_form.save()

                # ------------------------------------------
                # ACTIVITY LOG
                # ------------------------------------------

                log_activity(
                    request,
                    action="CREATE",
                    module="Accounts",
                    description=(
                        f"Created user account "
                        f"'{user.username}' "
                        f"(User ID: {user.pk})."
                    ),
                )

            messages.success(
                request,
                "User created successfully.",
            )

            return redirect(
                "user-list",
            )

    else:

        user_form = UserForm()

        profile_form = UserProfileForm()

    return render(
        request,
        "accounts/user_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "title": "Create User",
        },
    )


# ==========================================================
# USER DETAIL
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_detail(request, pk):
    """
    Display details of one user account.
    """

    account = get_object_or_404(
        User.objects.select_related(
            "profile",
            "profile__role",
            "profile__school",
        ),
        pk=pk,
    )

    return render(
        request,
        "accounts/user_detail.html",
        {
            "account": account,
        },
    )


# ==========================================================
# EDIT USER
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_update(request, pk):
    """
    Update a user's account and profile.
    """

    user = get_object_or_404(
        User,
        pk=pk,
    )

    profile = user.profile

    if request.method == "POST":

        user_form = UserForm(
            request.POST,
            instance=user,
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if (
            user_form.is_valid()
            and profile_form.is_valid()
        ):

            with transaction.atomic():

                # ------------------------------------------
                # UPDATE USER
                # ------------------------------------------

                user = user_form.save(
                    commit=False,
                )

                password = (
                    user_form.cleaned_data.get(
                        "password",
                    )
                )

                # Only replace the password when the
                # user supplied a new one.
                if password:
                    user.password = make_password(
                        password,
                    )

                user.save()

                # ------------------------------------------
                # UPDATE PROFILE
                # ------------------------------------------

                profile_form.save()

                # ------------------------------------------
                # ACTIVITY LOG
                # ------------------------------------------

                log_activity(
                    request,
                    action="UPDATE",
                    module="Accounts",
                    description=(
                        f"Updated user account "
                        f"'{user.username}' "
                        f"(User ID: {user.pk})."
                    ),
                )

            messages.success(
                request,
                "User updated successfully.",
            )

            return redirect(
                "user-list",
            )

    else:

        user_form = UserForm(
            instance=user,
        )

        profile_form = UserProfileForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/user_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "title": "Edit User",
        },
    )


# ==========================================================
# ACTIVATE / DEACTIVATE USER
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
)
def user_toggle_status(request, pk):
    """
    Activate or deactivate a user account.
    """

    user = get_object_or_404(
        User,
        pk=pk,
    )

    # ----------------------------------------------
    # PREVENT SELF-DEACTIVATION
    # ----------------------------------------------

    if user.pk == request.user.pk:

        messages.error(
            request,
            "You cannot deactivate your own account.",
        )

        return redirect(
            "user-detail",
            pk=user.pk,
        )

    with transaction.atomic():

        # ----------------------------------------------
        # TOGGLE STATUS
        # ----------------------------------------------

        user.is_active = not user.is_active

        user.save(
            update_fields=[
                "is_active",
            ],
        )

        # ----------------------------------------------
        # DETERMINE ACTION
        # ----------------------------------------------

        if user.is_active:

            action = "ACTIVATE"

            description = (
                f"Activated user account "
                f"'{user.username}' "
                f"(User ID: {user.pk})."
            )

            message = (
                "User activated successfully."
            )

        else:

            action = "DEACTIVATE"

            description = (
                f"Deactivated user account "
                f"'{user.username}' "
                f"(User ID: {user.pk})."
            )

            message = (
                "User deactivated successfully."
            )

        # ----------------------------------------------
        # ACTIVITY LOG
        # ----------------------------------------------

        log_activity(
            request,
            action=action,
            module="Accounts",
            description=description,
        )

    messages.success(
        request,
        message,
    )

    return redirect(
        "user-list",
    )


# ==========================================================
# DELETE USER
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
)
def user_delete(request, pk):
    """
    Permanently delete a user account.

    Only SUPER_ADMIN users are allowed to perform this action.
    """

    account = get_object_or_404(
        User.objects.select_related(
            "profile",
            "profile__role",
            "profile__school",
        ),
        pk=pk,
    )

    # ------------------------------------------------------
    # PROTECT CURRENTLY LOGGED-IN USER
    # ------------------------------------------------------

    if account.pk == request.user.pk:

        messages.error(
            request,
            "You cannot delete your own account.",
        )

        return redirect(
            "user-detail",
            pk=account.pk,
        )

    # ------------------------------------------------------
    # POST = DELETE
    # ------------------------------------------------------

    if request.method == "POST":

        username = account.username
        user_id = account.pk

        with transaction.atomic():

            # ----------------------------------------------
            # DELETE USER
            # ----------------------------------------------

            account.delete()

            # ----------------------------------------------
            # ACTIVITY LOG
            # ----------------------------------------------

            log_activity(
                request,
                action="DELETE",
                module="Accounts",
                description=(
                    f"Deleted user account "
                    f"'{username}' "
                    f"(User ID: {user_id})."
                ),
            )

        messages.success(
            request,
            (
                f"User '{username}' "
                "was deleted successfully."
            ),
        )

        return redirect(
            "user-list",
        )

    # ------------------------------------------------------
    # GET = CONFIRMATION PAGE
    # ------------------------------------------------------

    return render(
        request,
        "accounts/user_confirm_delete.html",
        {
            "account": account,
        },
    )