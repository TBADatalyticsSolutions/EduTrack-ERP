from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity

from .forms import SchoolForm
from .models import School


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def school_dashboard(request):
    """Display the schools available to the current administrator."""
    if request.user.is_superuser:
        schools = School.objects.filter(is_deleted=False).order_by("name")
    else:
        profile = getattr(request.user, "profile", None)
        school = getattr(profile, "school", None)
        schools = (
            School.objects.filter(pk=school.pk, is_deleted=False)
            if school
            else School.objects.none()
        )

    return render(
        request,
        "schools/dashboard.html",
        {"schools": schools, "school_count": schools.count()},
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def school_create(request):
    """Create a school. Super administrators can create additional schools."""
    profile = getattr(request.user, "profile", None)
    if not request.user.is_superuser and getattr(profile, "school", None):
        messages.error(
            request,
            "Your account is already assigned to a school. "
            "Contact a Super Administrator to create another school.",
        )
        return redirect("school-dashboard")

    if request.method == "POST":
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            log_activity(
                request,
                action="CREATE",
                module="Schools",
                description=f"Created school: {school.name}",
            )
            messages.success(
                request,
                f"School '{school.name}' was created successfully.",
            )
            return redirect("school-dashboard")
    else:
        form = SchoolForm()

    return render(
        request,
        "schools/form.html",
        {"form": form, "page_heading": "Add School"},
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN")
def school_edit(request, pk):
    """Edit a school profile."""
    school = get_object_or_404(School, pk=pk, is_deleted=False)

    if not request.user.is_superuser:
        profile = getattr(request.user, "profile", None)
        profile_school = getattr(profile, "school", None)
        if not profile_school or profile_school.pk != school.pk:
            messages.error(
                request,
                "You do not have permission to edit this school.",
            )
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
            messages.success(
                request,
                f"School '{school.name}' was updated successfully.",
            )
            return redirect("school-dashboard")
    else:
        form = SchoolForm(instance=school)

    return render(
        request,
        "schools/form.html",
        {
            "form": form,
            "school": school,
            "page_heading": "Edit School",
        },
    )
