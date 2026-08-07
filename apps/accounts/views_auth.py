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
    Custom Login View
    Supports Remember Me.
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

            login(request, user)

            log_activity(
            request,
            action="LOGIN",
            module="Accounts",
            description="User logged into the system",
            )
            # ======================================
            # Remember Me
            # ======================================

            if form.cleaned_data.get("remember_me"):

                request.session.set_expiry(
                    60 * 60 * 24 * 30
                )

            else:

                request.session.set_expiry(0)

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

            messages.success(
                request,
                f"Welcome back, {user.get_full_name() or user.username}!",
            )

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
    Logout current user.
    """

    log_activity(
        request,
        action="LOGOUT",
        module="Accounts",
        description="User logged out",
    )

    logout(request)

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("login")


# ==========================================================
# PASSWORD RESET
# ==========================================================

class CustomPasswordResetView(PasswordResetView):

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

        response = super().form_valid(form)

        email = form.cleaned_data.get("email")

        if self.request.user.is_authenticated:

            log_activity(
                self.request,
                action="PASSWORD_RESET_REQUEST",
                module="Accounts",
                description=f"Requested password reset for {email}",
            )

        return response

class CustomPasswordResetDoneView(
    PasswordResetDoneView
):
    template_name = (
        "accounts/password_reset_done.html"
    )

class CustomPasswordResetConfirmView(
    PasswordResetConfirmView
):

    template_name = (
        "accounts/password_reset_confirm.html"
    )

    success_url = (
        "/accounts/password-reset/complete/"
    )

    def form_valid(self, form):

        response = super().form_valid(form)

        if self.request.user.is_authenticated:

            log_activity(
                self.request,
                action="PASSWORD_RESET",
                module="Accounts",
                description="Password reset completed",
            )

        return response

class CustomPasswordResetCompleteView(
    PasswordResetCompleteView
):
    template_name = (
        "accounts/password_reset_complete.html"
    )


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@login_required
def password_change_view(request):
    """
    Change Password.
    """

    if request.method == "POST":

        form = CustomPasswordChangeForm(
            request.user,
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user,
            )

            log_activity(
                request,
                action="PASSWORD_CHANGE",
                module="Accounts",
                description="Changed account password",
            )

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
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
    Display logged-in user's profile.
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
    Edit logged-in user's profile.
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

            log_activity(
                request,
                action="UPDATE",
                module="Accounts",
                description="Updated personal profile",
            )

        log_activity(
            request,
            action="UPDATE",
            module="Unknown",
            description="Operation completed",
        )

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect("profile")

    else:

        form = ProfileForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "form": form,
        },
    )