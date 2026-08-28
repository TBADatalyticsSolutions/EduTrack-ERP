from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.permissions import has_role
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import AcademicSessionForm, ClassSubjectForm, SchoolClassForm, SubjectForm, TermForm
from .models import AcademicSession, ClassSubject, SchoolClass, Subject, Term

ACADEMIC_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
ADMIN_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")


def _user_school(request):
    if request.user.is_superuser:
        return School.objects.first()
    profile = getattr(request.user, "profile", None)
    return getattr(profile, "school", None)


def _schools_for_user(request):
    school = _user_school(request)
    return school


@login_required
@role_required(*ACADEMIC_ROLES)
def academic_dashboard(request):
    school = _schools_for_user(request)
    if not school:
        messages.error(request, "No school is assigned to your account.")
        return render(request, "academics/dashboard.html", {
            "school": None,
            "can_manage_academics": has_role(request.user, *ADMIN_ROLES),
        })
    sessions = AcademicSession.objects.filter(school=school).order_by("-name")
    terms = Term.objects.filter(school=school).select_related("session").order_by("-session__name", "name")
    classes = SchoolClass.objects.filter(school=school).prefetch_related("subjects").order_by("name")
    subjects = Subject.objects.filter(school=school).order_by("name")
    assignments = ClassSubject.objects.filter(school_class__school=school).select_related("school_class", "subject").order_by("school_class__name", "subject__name")
    return render(request, "academics/dashboard.html", {
        "school": school,
        "sessions": sessions,
        "terms": terms,
        "classes": classes,
        "subjects": subjects,
        "assignments": assignments,
        "session_count": sessions.count(),
        "term_count": terms.count(),
        "class_count": classes.count(),
        "subject_count": subjects.count(),
        "current_session": sessions.filter(is_current=True).first(),
        "current_term": terms.filter(is_current=True).first(),
        # The dashboard itself is already protected by ACADEMIC_ROLES.
        # Calculate management capability explicitly so the UI does not
        # depend on template context-processor state.
        "can_manage_academics": has_role(request.user, *ADMIN_ROLES),
    })


@login_required
@role_required(*ADMIN_ROLES)
def session_create(request):
    school = _user_school(request)
    if not school:
        messages.error(request, "No school is assigned to your account.")
        return redirect("academics:dashboard")
    form = AcademicSessionForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.school = school
        if session.is_current:
            AcademicSession.objects.filter(school=school).update(is_current=False)
        session.save()
        log_activity(request, action="CREATE", module="Academics", description=f"Created academic session: {session.name}")
        messages.success(request, "Academic session created successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Add Academic Session", "submit_label": "Save Session"})


@login_required
@role_required(*ADMIN_ROLES)
def session_edit(request, pk):
    school = _user_school(request)
    session = get_object_or_404(AcademicSession, pk=pk, school=school)
    form = AcademicSessionForm(request.POST or None, instance=session, school=school)
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        if session.is_current:
            AcademicSession.objects.filter(school=school).exclude(pk=session.pk).update(is_current=False)
        session.save()
        messages.success(request, "Academic session updated successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Academic Session", "submit_label": "Save Changes"})


@login_required
@role_required(*ADMIN_ROLES)
def term_create(request):
    school = _user_school(request)
    form = TermForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        term = form.save(commit=False)
        term.school = school
        if term.is_current:
            Term.objects.filter(school=school).update(is_current=False)
        term.save()
        log_activity(request, action="CREATE", module="Academics", description=f"Created term: {term.name}")
        messages.success(request, "Term created successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Add Academic Term", "submit_label": "Save Term"})


@login_required
@role_required(*ADMIN_ROLES)
def term_edit(request, pk):
    school = _user_school(request)
    term = get_object_or_404(Term, pk=pk, school=school)
    form = TermForm(request.POST or None, instance=term, school=school)
    if request.method == "POST" and form.is_valid():
        term = form.save(commit=False)
        if term.is_current:
            Term.objects.filter(school=school).exclude(pk=term.pk).update(is_current=False)
        term.school = school
        term.save()
        messages.success(request, "Term updated successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Academic Term", "submit_label": "Save Changes"})


@login_required
@role_required(*ADMIN_ROLES)
def class_create(request):
    school = _user_school(request)
    form = SchoolClassForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.school = school
        obj.save()
        log_activity(request, action="CREATE", module="Academics", description=f"Created class: {obj.name}")
        messages.success(request, "Class created successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Add Class", "submit_label": "Save Class"})


@login_required
@role_required(*ADMIN_ROLES)
def class_edit(request, pk):
    school = _user_school(request)
    obj = get_object_or_404(SchoolClass, pk=pk, school=school)
    form = SchoolClassForm(request.POST or None, instance=obj, school=school)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Class updated successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Class", "submit_label": "Save Changes"})


@login_required
@role_required(*ADMIN_ROLES)
def subject_create(request):
    school = _user_school(request)
    form = SubjectForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.school = school
        obj.save()
        log_activity(request, action="CREATE", module="Academics", description=f"Created subject: {obj.name}")
        messages.success(request, "Subject created successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Add Subject", "submit_label": "Save Subject"})


@login_required
@role_required(*ADMIN_ROLES)
def subject_edit(request, pk):
    school = _user_school(request)
    obj = get_object_or_404(Subject, pk=pk, school=school)
    form = SubjectForm(request.POST or None, instance=obj, school=school)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Subject", "submit_label": "Save Changes"})


@login_required
@role_required(*ADMIN_ROLES)
def assignment_create(request):
    school = _user_school(request)
    form = ClassSubjectForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        log_activity(request, action="CREATE", module="Academics", description=f"Assigned {obj.subject} to {obj.school_class}")
        messages.success(request, "Subject assigned to class successfully.")
        return redirect("academics:dashboard")
    return render(request, "academics/form.html", {"form": form, "title": "Assign Subject to Class", "submit_label": "Assign Subject"})


@login_required
@role_required(*ADMIN_ROLES)
def assignment_delete(request, pk):
    school = _user_school(request)
    obj = get_object_or_404(ClassSubject, pk=pk, school_class__school=school)
    if request.method == "POST":
        description = f"Removed {obj.subject} from {obj.school_class}"
        obj.delete()
        log_activity(request, action="DELETE", module="Academics", description=description)
        messages.success(request, "Subject removed from class.")
    return redirect("academics:dashboard")
