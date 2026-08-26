from django.contrib import messages
from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import (
    redirect,
    render,
)

from apps.accounts.utils import log_activity

from .forms import (
    LoginForm,
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    ProfileForm,
)


# ==========================================================
# ROLE-BASED REDIRECT HELPER
# ==========================================================

def redirect_by_role(user):
    """
    Redirect users based on their assigned role.
    """

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
        "TEACHER": "student-list",
        "ACCOUNTANT": "accounts-dashboard",
        "LIBRARIAN": "accounts-dashboard",
        "PARENT": "accounts-dashboard",
        "STUDENT": "student-list",
    }

    return redirect(
        role_redirects.get(
            role,
            "accounts-dashboard",
        )
    )


# ==========================================================
# LOGIN
# ==========================================================

def login_view(request):
    """
    Custom Login View.

    Supports:
    - Remember Me
    - Role-based redirection
    - Safe next URL handling
    - Activity logging
    """

    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    form = LoginForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST":

        if form.is_valid():

            user = form.get_user()

            # ------------------------------------------
            # Authenticate user
            # ------------------------------------------

            login(request, user)

            # ------------------------------------------
            # Remember Me
            # ------------------------------------------

            if form.cleaned_data.get("remember_me"):

                request.session.set_expiry(
                    60 * 60 * 24 * 30
                )

            else:

                request.session.set_expiry(0)

            # ------------------------------------------
            # Activity Log
            # ------------------------------------------

            log_activity(
                request,
                action="LOGIN",
                module="Accounts",
                description=(
                    f"User '{user.username}' "
                    f"logged into EduTrack ERP."
                ),
            )

            messages.success(
                request,
                (
                    f"Welcome back, "
                    f"{user.get_full_name() or user.username}!"
                ),
            )

            # ------------------------------------------
            # Safe Redirect
            # ------------------------------------------

            next_url = (
                request.POST.get("next")
                or request.GET.get("next")
            )

            # Prevent Open Redirect vulnerability
            if next_url and next_url.startswith("/"):

                return redirect(next_url)

            return redirect_by_role(user)

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


# ==========================================================
# LOGOUT
# ==========================================================

@login_required
def logout_view(request):
    """
    Logout current user and record the activity.
    """

    username = request.user.username

    log_activity(
        request,
        action="LOGOUT",
        module="Accounts",
        description=(
            f"User '{username}' "
            f"logged out of EduTrack ERP."
        ),
    )

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("login")


# ==========================================================
# PASSWORD RESET
# ==========================================================

class CustomPasswordResetView(PasswordResetView):
    """
    Request a password reset email.
    """

    template_name = "accounts/password_reset.html"

    email_template_name = (
        "accounts/password_reset_email.html"
    )

    subject_template_name = (
        "accounts/password_reset_subject.txt"
    )

    form_class = CustomPasswordResetForm

    success_url = "/accounts/password-reset/done/"

    def form_valid(self, form):

        email = form.cleaned_data.get("email")

        response = super().form_valid(form)

        # ------------------------------------------
        # Password reset request
        #
        # This may be an anonymous user.
        # Therefore do NOT require
        # request.user.is_authenticated here.
        # ------------------------------------------

        log_activity(
            self.request,
            action="PASSWORD_RESET_REQUEST",
            module="Accounts",
            description=(
                f"Password reset requested "
                f"for email '{email}'."
            ),
        )

        return response


# ==========================================================
# PASSWORD RESET DONE
# ==========================================================

class CustomPasswordResetDoneView(
    PasswordResetDoneView
):
    """
    Display password reset email confirmation.
    """

    template_name = (
        "accounts/password_reset_done.html"
    )


# ==========================================================
# PASSWORD RESET CONFIRM
# ==========================================================

class CustomPasswordResetConfirmView(
    PasswordResetConfirmView
):
    """
    Confirm and set a new password.
    """

    template_name = (
        "accounts/password_reset_confirm.html"
    )

    success_url = (
        "/accounts/password-reset/complete/"
    )

    def form_valid(self, form):

        response = super().form_valid(form)

        # ------------------------------------------
        # Password reset completed.
        #
        # User may still be anonymous here.
        # ------------------------------------------

        log_activity(
            self.request,
            action="PASSWORD_RESET",
            module="Accounts",
            description=(
                "Password reset completed successfully."
            ),
        )

        return response


# ==========================================================
# PASSWORD RESET COMPLETE
# ==========================================================

class CustomPasswordResetCompleteView(
    PasswordResetCompleteView
):
    """
    Display password reset completion message.
    """

    template_name = (
        "accounts/password_reset_complete.html"
    )


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@login_required
def password_change_view(request):
    """
    Allow a logged-in user to change their password.
    """

    if request.method == "POST":

        form = CustomPasswordChangeForm(
            request.user,
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            # ------------------------------------------
            # Keep user logged in after password change
            # ------------------------------------------

            update_session_auth_hash(
                request,
                user,
            )

            # ------------------------------------------
            # Activity Log
            # ------------------------------------------

            log_activity(
                request,
                action="PASSWORD_CHANGE",
                module="Accounts",
                description=(
                    "User changed their password "
                    "successfully."
                ),
            )

            messages.success(
                request,
                "Password changed successfully.",
            )

            return redirect(
                "accounts-dashboard"
            )

    else:

        form = CustomPasswordChangeForm(
            request.user,
        )

    return render(
        request,
        "accounts/password_change.html",
        {
            "form": form,
        },
    )


# ==========================================================
# MY PROFILE
# ==========================================================

@login_required
def profile_view(request):
    """
    Display the logged-in user's profile.

    No activity log is created here because simply
    viewing a profile is not an important audit event.
    """

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": request.user.profile,
        },
    )


# ==========================================================
# EDIT PROFILE
# ==========================================================

@login_required
def profile_edit(request):
    """
    Allow users to edit their own profile.
    """

    profile = request.user.profile

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():

            form.save()

            # ------------------------------------------
            # Activity Log
            # ------------------------------------------

            log_activity(
                request,
                action="PROFILE_UPDATE",
                module="Accounts",
                description=(
                    "User updated their profile "
                    "information."
                ),
            )

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect(
                "profile"
            )

    else:

        form = ProfileForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "form": form,
            "profile": profile,
        },
    )
