from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.utils import log_activity
from apps.students.models import Student
from apps.teachers.models import Teacher

from .access import role_code
from .decorators import role_required
from .forms import UserForm, UserProfileForm


PLATFORM_ROLES = {"SUPER_ADMIN"}
TENANT_ROLES = {
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "VICE_PRINCIPAL",
    "REGISTRAR",
    "TEACHER",
    "ACCOUNTANT",
    "LIBRARIAN",
    "PARENT",
    "STUDENT",
}


def _profile_school(request):
    return getattr(getattr(request.user, "profile", None), "school", None)


def _is_platform_admin(request):
    return request.user.is_superuser or role_code(request.user) in PLATFORM_ROLES


def _tenant_users(request):
    users = User.objects.select_related(
        "profile",
        "profile__role",
        "profile__school",
    ).order_by("username")

    if _is_platform_admin(request):
        return users

    school = _profile_school(request)
    return users.filter(profile__school=school) if school else users.none()


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def accounts_dashboard(request):
    """Display account metrics for the platform or current school tenant."""
    users = _tenant_users(request)
    school = _profile_school(request)

    if _is_platform_admin(request):
        teachers = Teacher.objects.count()
        students = Student.objects.count()
    else:
        teachers = Teacher.objects.filter(school=school).count()
        students = Student.objects.filter(school=school).count()

    context = {
        "total_users": users.count(),
        "active_users": users.filter(is_active=True).count(),
        "inactive_users": users.filter(is_active=False).count(),
        "teachers": teachers,
        "students": students,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def user_list(request):
    """Display only users belonging to the current tenant."""
    return render(request, "accounts/user_list.html", {"users": _tenant_users(request)})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def user_create(request):
    """Create a user while preventing school administrators from crossing tenants."""
    school = _profile_school(request)
    is_platform_admin = _is_platform_admin(request)

    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if not is_platform_admin:
            profile_form.fields["school"].queryset = profile_form.fields["school"].queryset.filter(pk=school.pk)
            profile_form.fields["school"].required = True
            profile_form.fields["role"].queryset = profile_form.fields["role"].queryset.filter(code__in=TENANT_ROLES)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
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
                if not is_platform_admin:
                    profile_form.fields["school"].queryset = profile_form.fields["school"].queryset.filter(pk=school.pk)
                    profile_form.fields["school"].required = True
                    profile_form.fields["role"].queryset = profile_form.fields["role"].queryset.filter(code__in=TENANT_ROLES)
                    if request.POST.get("school") != str(school.pk):
                        messages.error(request, "You can only create users for your own school.")
                        transaction.set_rollback(True)
                        return render(
                            request,
                            "accounts/user_form.html",
                            {"user_form": user_form, "profile_form": profile_form, "title": "Create User"},
                            status=403,
                        )

                profile_form.save()
                if not is_platform_admin:
                    profile.school = school
                    profile.save(update_fields=["school"])
                log_activity(
                    request,
                    action="CREATE",
                    module="Accounts",
                    description=f"Created user account '{user.username}' (User ID: {user.pk}).",
                )

            messages.success(request, "User created successfully.")
            return redirect("user-list")
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
        if not is_platform_admin:
            profile_form.fields["school"].queryset = profile_form.fields["school"].queryset.filter(pk=school.pk)
            profile_form.fields["school"].required = True
            profile_form.fields["role"].queryset = profile_form.fields["role"].queryset.filter(code__in=TENANT_ROLES)
            profile_form.initial["school"] = school

    return render(
        request,
        "accounts/user_form.html",
        {"user_form": user_form, "profile_form": profile_form, "title": "Create User"},
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def user_detail(request, pk):
    """Display a user only when they belong to the current tenant."""
    account = get_object_or_404(_tenant_users(request), pk=pk)
    return render(request, "accounts/user_detail.html", {"account": account})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def user_update(request, pk):
    """Update a user while enforcing tenant ownership."""
    user = get_object_or_404(_tenant_users(request), pk=pk)
    profile = user.profile
    school = _profile_school(request)
    is_platform_admin = _is_platform_admin(request)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if not is_platform_admin:
            profile_form.fields["school"].queryset = profile_form.fields["school"].queryset.filter(pk=school.pk)
            profile_form.fields["school"].required = True
            profile_form.fields["role"].queryset = profile_form.fields["role"].queryset.filter(code__in=TENANT_ROLES)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                password = user_form.cleaned_data.get("password")
                if password:
                    user.password = make_password(password)
                user.save()
                profile_form.save()
                if not is_platform_admin:
                    profile.school = school
                    profile.save(update_fields=["school"])
                log_activity(
                    request,
                    action="UPDATE",
                    module="Accounts",
                    description=f"Updated user account '{user.username}' (User ID: {user.pk}).",
                )

            messages.success(request, "User updated successfully.")
            return redirect("user-list")
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        if not is_platform_admin:
            profile_form.fields["school"].queryset = profile_form.fields["school"].queryset.filter(pk=school.pk)
            profile_form.fields["school"].required = True
            profile_form.fields["role"].queryset = profile_form.fields["role"].queryset.filter(code__in=TENANT_ROLES)

    return render(
        request,
        "accounts/user_form.html",
        {"user_form": user_form, "profile_form": profile_form, "title": "Edit User"},
    )


@login_required
@role_required("SUPER_ADMIN")
def user_toggle_status(request, pk):
    """Activate or deactivate a user account."""
    user = get_object_or_404(User, pk=pk)

    if user.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("user-detail", pk=user.pk)

    with transaction.atomic():
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        action = "ACTIVATE" if user.is_active else "DEACTIVATE"
        description = f"{'Activated' if user.is_active else 'Deactivated'} user account '{user.username}' (User ID: {user.pk})."
        log_activity(request, action=action, module="Accounts", description=description)

    messages.success(request, "User activated successfully." if user.is_active else "User deactivated successfully.")
    return redirect("user-list")


@login_required
@role_required("SUPER_ADMIN")
def user_delete(request, pk):
    """Permanently delete a user account."""
    account = get_object_or_404(User, pk=pk)

    if account.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user-detail", pk=account.pk)

    if request.method == "POST":
        username = account.username
        user_id = account.pk
        with transaction.atomic():
            account.delete()
            log_activity(
                request,
                action="DELETE",
                module="Accounts",
                description=f"Deleted user account '{username}' (User ID: {user_id}).",
            )
        messages.success(request, f"User '{username}' was deleted successfully.")
        return redirect("user-list")

    return render(request, "accounts/user_confirm_delete.html", {"account": account})
