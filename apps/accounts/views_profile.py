from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.utils import log_activity
from .forms import ProfileForm
# ==========================================================
# MY PROFILE
# ==========================================================

@login_required
def profile_view(request):
    """
    Display the logged-in user's profile.
    """

    profile = request.user.profile

    context = {
        "profile": profile,
    }

    return render(
        request,
        "accounts/profile.html",
        context,
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

            log_activity(
                request,
                action="UPDATE",
                module="Accounts",
                description="Updated own profile",
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

            return redirect(
                "profile",
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