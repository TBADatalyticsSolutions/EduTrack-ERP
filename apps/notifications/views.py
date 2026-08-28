from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.decorators import role_required
from apps.schools.models import School
from .forms import NotificationForm
from .models import Notification

ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR")

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
    return render(request, "notifications/dashboard.html", {"notifications": qs, "unread_count": qs.filter(is_read=False).count()})

@login_required
@role_required(*ROLES)
def notification_create(request):
    school = _school(request)
    if not school:
        messages.error(request, "No school is assigned to your account.")
        return redirect("notifications:dashboard")
    form = NotificationForm(request.POST or None)
    if form.is_valid():
        notification = form.save(commit=False)
        notification.school = school
        notification.save()
        messages.success(request, "Notification sent successfully.")
        return redirect("notifications:dashboard")
    return render(request, "notifications/form.html", {"form": form})

@login_required
@role_required(*ROLES)
def notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return redirect("notifications:dashboard")
