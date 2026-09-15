from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.access import role_code
from apps.accounts.decorators import role_required
from apps.schools.models import School

from .forms import NotificationForm
from .models import Notification


User = get_user_model()
ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")
PORTAL_ROLES = ("STUDENT", "PARENT")


def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)


@login_required
@role_required(*ROLES)
def notification_dashboard(request):
    school = _school(request)
    qs = Notification.objects.filter(recipient=request.user)
    if school:
        qs = qs.filter(school=school)
    return render(
        request,
        "notifications/dashboard.html",
        {"notifications": qs, "unread_count": qs.filter(is_read=False).count()},
    )


@login_required
@role_required(*ROLES)
def notification_create(request):
    school = _school(request)
    if not school:
        messages.error(request, "No school is assigned to your account.")
        return redirect("notifications:dashboard")

    form = NotificationForm(request.POST or None, school=school)
    if form.is_valid():
        send_to_all_students = form.cleaned_data["send_to_all_students"]
        title = form.cleaned_data["title"]
        message = form.cleaned_data["message"]
        notification_type = form.cleaned_data["notification_type"]

        if send_to_all_students:
            recipients = list(
                User.objects.filter(
                    is_active=True,
                    profile__school=school,
                    profile__role__code="STUDENT",
                )
            )
            Notification.objects.bulk_create(
                [
                    Notification(
                        school=school,
                        recipient=recipient,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                    )
                    for recipient in recipients
                ]
            )
            messages.success(
                request,
                f"School notice sent to {len(recipients)} student portal account(s).",
            )
        else:
            notification = form.save(commit=False)
            notification.school = school
            notification.save()
            messages.success(request, "Notification sent successfully.")

        return redirect("notifications:dashboard")

    return render(request, "notifications/form.html", {"form": form})


@login_required
@role_required(*ROLES)
def notification_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return redirect("notifications:dashboard")


@login_required
def portal_notification_read(request, pk):
    if role_code(request.user) not in PORTAL_ROLES:
        return redirect("profile")

    school = getattr(getattr(request.user, "profile", None), "school", None)
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
        school=school,
    )
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return redirect("portal-dashboard")
