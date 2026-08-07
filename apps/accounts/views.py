from django.contrib import messages
from apps.accounts.utils import log_activity
from django.contrib.auth.decorators import login_required
from apps.accounts.utils import log_activity
from django.contrib.auth.hashers import make_password
from apps.accounts.utils import log_activity
from django.contrib.auth.models import User
from apps.accounts.utils import log_activity
from django.shortcuts import (
from apps.accounts.utils import log_activity
    get_object_or_404,
    redirect,
    render,
)

from apps.students.models import Student
from apps.accounts.utils import log_activity
from apps.teachers.models import Teacher
from apps.accounts.utils import log_activity

from .decorators import role_required
from apps.accounts.utils import log_activity
from .forms import UserForm, UserProfileForm
from apps.accounts.utils import log_activity


# ==========================================================
# Accounts Dashboard
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def accounts_dashboard(request):

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
# User List
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_list(request):

    users = (
        User.objects
        .select_related(
            "profile",
            "profile__role",
            "profile__school",
        )
        .order_by("username")
    )

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
        },
    )


# ==========================================================
# Create User
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_create(request):

    if request.method == "POST":

        user_form = UserForm(request.POST)

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
        )

        if user_form.is_valid() and profile_form.is_valid():

            user = user_form.save(commit=False)

            password = user_form.cleaned_data.get("password")

            if password:
                user.password = make_password(password)

            user.save()

            profile = user.profile

            profile_form = UserProfileForm(
                request.POST,
                request.FILES,
                instance=profile,
            )

            profile_form.save()

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

            messages.success(
                request,
                "User created successfully.",
            )

            return redirect("user-list")

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
# User Detail
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_detail(request, pk):

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
# Edit User
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
)
def user_update(request, pk):

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

        if user_form.is_valid() and profile_form.is_valid():

            user = user_form.save(commit=False)

            password = user_form.cleaned_data.get("password")

            if password:
                user.password = make_password(password)

            user.save()

            profile_form.save()

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

            messages.success(
                request,
                "User updated successfully.",
            )

            return redirect("user-list")

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
# Activate / Deactivate User
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
)
def user_toggle_status(request, pk):

    user = get_object_or_404(
        User,
        pk=pk,
    )

    user.is_active = not user.is_active

    user.save()

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

    messages.success(
        request,
        "User status updated successfully.",
    )

    return redirect("user-list")


# ==========================================================
# Delete User
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
)
def user_delete(request, pk):

    account = get_object_or_404(
        User,
        pk=pk,
    )

    if request.method == "POST":

        account.delete()

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

        messages.success(
            request,
            "User deleted successfully.",
        )

        return redirect("user-list")

    return render(
        request,
        "accounts/user_confirm_delete.html",
        {
            "account": account,
        },
    )