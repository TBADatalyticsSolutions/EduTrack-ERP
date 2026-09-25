from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import Role
from apps.accounts.utils import log_activity

from .forms import SchoolForm, SchoolOnboardingForm, SchoolSubscriptionForm
from .models import School, SchoolSubscription

User = get_user_model()

MAX_SCHOOLS = 10


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def school_dashboard(request):
    """Display only the school tenant available to the current administrator."""
    if request.user.is_superuser:
        schools = School.objects.filter(is_active=True).select_related("subscription").order_by("name")
    else:
        profile = getattr(request.user, "profile", None)
        school = getattr(profile, "school", None)
        schools = (
            School.objects.filter(pk=school.pk, is_active=True).select_related("subscription")
            if school
            else School.objects.none()
        )

    return render(
        request,
        "schools/dashboard.html",
        {"schools": schools, "school_count": schools.count()},
    )


@login_required
@role_required("SUPER_ADMIN")
def school_create(request):
    """Create a school tenant and its first school administrator atomically."""
    if request.method == "POST":
        if School.objects.filter(is_active=True).count() >= MAX_SCHOOLS:
            messages.error(
                request,
                f"EduTrack ERP is currently configured for a maximum of {MAX_SCHOOLS} active schools.",
            )
            return redirect("school-dashboard")
        form = SchoolOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                school = form.save()
                SchoolSubscription.objects.create(
                    school=school,
                    plan="STANDARD",
                    status="ACTIVE",
                    started_at=timezone.now(),
                )

                role = Role.objects.get(code="SCHOOL_ADMIN")
                admin_user = User.objects.create_user(
                    username=form.cleaned_data["admin_username"],
                    first_name=form.cleaned_data["admin_first_name"],
                    last_name=form.cleaned_data["admin_last_name"],
                    email=form.cleaned_data["admin_email"],
                    password=form.cleaned_data["admin_password"],
                    is_active=True,
                )
                profile = admin_user.profile
                profile.school = school
                profile.role = role
                profile.is_school_admin = True
                profile.save(update_fields=["school", "role", "is_school_admin"])

                log_activity(
                    request,
                    action="CREATE",
                    module="Schools",
                    description=(
                        f"Created school tenant '{school.name}' and initial "
                        f"school administrator '{admin_user.username}'."
                    ),
                )

            messages.success(
                request,
                f"School '{school.name}' was created and the school administrator account was provisioned.",
            )
            return redirect("school-dashboard")
    else:
        form = SchoolOnboardingForm()

    return render(
        request,
        "schools/form.html",
        {"form": form, "page_heading": "Add School & School Administrator", "onboarding": True, "max_schools": MAX_SCHOOLS},
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def school_edit(request, pk):
    """Edit a school profile while enforcing tenant ownership."""
    school = get_object_or_404(School, pk=pk, is_active=True)

    if not request.user.is_superuser:
        profile_school = getattr(getattr(request.user, "profile", None), "school", None)
        if not profile_school or profile_school.pk != school.pk:
            messages.error(request, "You do not have permission to edit this school.")
            return redirect("school-dashboard")

    if request.method == "POST":
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            school = form.save()
            log_activity(
                request,
                action="UPDATE",
                module="Schools",
                description=f"Updated school: {school.name}",
            )
            messages.success(request, f"School '{school.name}' was updated successfully.")
            return redirect("school-dashboard")
    else:
        form = SchoolForm(instance=school)

    return render(
        request,
        "schools/form.html",
        {"form": form, "school": school, "page_heading": "Edit School"},
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def subscription_list(request):
    """Show all subscriptions to the platform admin and only the current tenant to school admins."""
    subscriptions = SchoolSubscription.objects.select_related("school").order_by("school__name")
    if not request.user.is_superuser:
        school = getattr(getattr(request.user, "profile", None), "school", None)
        subscriptions = subscriptions.filter(school=school) if school else subscriptions.none()

    return render(
        request,
        "schools/subscription_list.html",
        {"subscriptions": subscriptions},
    )


@login_required
@role_required("SUPER_ADMIN")
def subscription_edit(request, pk):
    """Allow only the platform administrator to change a tenant subscription."""
    subscription = get_object_or_404(
        SchoolSubscription.objects.select_related("school"),
        pk=pk,
    )

    if request.method == "POST":
        form = SchoolSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            subscription = form.save()
            log_activity(
                request,
                action="UPDATE",
                module="Schools",
                description=(
                    f"Updated subscription for '{subscription.school.name}' "
                    f"to {subscription.get_plan_display()} / {subscription.get_status_display()}."
                ),
            )
            messages.success(request, "Subscription updated successfully.")
            return redirect("subscription-list")
    else:
        form = SchoolSubscriptionForm(instance=subscription)

    return render(
        request,
        "schools/subscription_form.html",
        {
            "form": form,
            "subscription": subscription,
            "page_heading": f"Manage Subscription — {subscription.school.name}",
        },
    )
