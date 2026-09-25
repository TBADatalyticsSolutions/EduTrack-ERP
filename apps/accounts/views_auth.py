import logging

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect, render

from apps.accounts.utils import log_activity
from apps.schools.models import SchoolSubscription

from .forms import (
    LoginForm,
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    ProfileForm,
)


PLATFORM_ROLES = {"SUPER_ADMIN"}

logger = logging.getLogger(__name__)


def redirect_by_role(user):
    profile = getattr(user, "profile", None)
    if not profile or not profile.role:
        return redirect("accounts-dashboard")
    role = profile.role.code
    role_redirects = {
        "SUPER_ADMIN": "accounts-dashboard",
        "SCHOOL_ADMIN": "accounts-dashboard",
        "PRINCIPAL": "accounts-dashboard",
        "VICE_PRINCIPAL": "accounts-dashboard",
        "REGISTRAR": "student-list",
        "TEACHER": "results:dashboard",
        "ACCOUNTANT": "accounts-dashboard",
        "LIBRARIAN": "accounts-dashboard",
        "PARENT": "portal-dashboard",
        "STUDENT": "portal-dashboard",
    }
    return redirect(role_redirects.get(role, "accounts-dashboard"))


def _school_login_allowed(user):
    """Require every non-platform account to belong to an active school tenant."""
    profile = getattr(user, "profile", None)
    role = getattr(getattr(profile, "role", None), "code", None)

    if user.is_superuser or role in PLATFORM_ROLES:
        return True, None
    if not profile or not profile.school:
        return False, "Your account is not assigned to a school. Contact the EduTrack platform administrator."

    subscription = SchoolSubscription.objects.filter(
        school=profile.school,
    ).first()
    if not subscription or subscription.status != "ACTIVE":
        return False, "Your school's EduTrack subscription is not active. Contact your school administrator."

    return True, None


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        try:
            logger.info("Login diagnostic: POST received.")
            if form.is_valid():
                logger.info("Login diagnostic: form validation succeeded.")
                user = form.get_user()
                logger.info("Login diagnostic: authenticated user resolved (username=%s).", user.username)

                allowed, reason = _school_login_allowed(user)
                logger.info("Login diagnostic: school access check completed (allowed=%s).", allowed)
                if not allowed:
                    messages.error(request, reason)
                    return render(request, "accounts/login.html", {"form": form})

                login(request, user)
                logger.info("Login diagnostic: django.contrib.auth.login completed.")

                if form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                logger.info("Login diagnostic: session expiry configured.")

                log_activity(
                    request,
                    action="LOGIN",
                    module="Accounts",
                    description=f"User '{user.username}' logged into EduTrack ERP.",
                )
                logger.info("Login diagnostic: activity log created.")

                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")

                profile = getattr(user, "profile", None)
                role = getattr(getattr(profile, "role", None), "code", None)
                next_url = request.POST.get("next") or request.GET.get("next")
                logger.info("Login diagnostic: redirect preparation completed (role=%s, has_next=%s).", role, bool(next_url))

                if role not in {"STUDENT", "PARENT", "TEACHER"} and next_url and next_url.startswith("/"):
                    return redirect(next_url)

                return redirect_by_role(user)

            logger.info("Login diagnostic: form validation failed.")
            messages.error(request, "Invalid username or password.")
        except Exception:
            logger.exception("Login diagnostic: unhandled exception during POST login.")
            raise
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    username = request.user.username
    log_activity(request, action="LOGOUT", module="Accounts", description=f"User '{username}' logged out of EduTrack ERP.")
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = CustomPasswordResetForm
    success_url = "/accounts/password-reset/done/"

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        response = super().form_valid(form)
        log_activity(self.request, action="PASSWORD_RESET_REQUEST", module="Accounts", description=f"Password reset requested for email '{email}'.")
        return response


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = "/accounts/password-reset/complete/"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request, action="PASSWORD_RESET", module="Accounts", description="Password reset completed successfully.")
        return response


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@login_required
def password_change_view(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(request, action="PASSWORD_CHANGE", module="Accounts", description="User changed their password successfully.")
            messages.success(request, "Password changed successfully.")
            return redirect_by_role(request.user)
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"profile": request.user.profile})


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request, action="PROFILE_UPDATE", module="Accounts", description="User updated their profile information.")
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile_edit.html", {"form": form, "profile": profile})
