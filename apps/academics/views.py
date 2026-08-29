from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.permissions import has_role
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import AcademicSessionForm, ClassSubjectForm, SchoolClassForm, SubjectForm, TermForm
from .models import AcademicSession, ClassSubject, SchoolClass, Subject, Term

ACADEMIC_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
ADMIN_ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")

DEFAULT_CLASSES = [
    "KG 1", "KG 2", "Nursery 1", "Nursery 2",
    "Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5", "Primary 6",
    "JSS 1", "JSS 2", "JSS 3",
    "SS 1", "SS 2", "SS 3",
]

DEFAULT_SUBJECTS = [
    ("English Language", "ENG", True),
    ("Mathematics", "MTH", True),
    ("Basic Science", "BSC", True),
    ("Basic Technology", "BTE", True),
    ("Social Studies", "SOS", True),
    ("Civic Education", "CIV", True),
    ("Computer Studies", "CMP", True),
    ("Agricultural Science", "AGR", False),
    ("Physical and Health Education", "PHE", False),
    ("Creative and Cultural Arts", "CCA", False),
    ("Islamic Religious Studies", "IRS", False),
    ("Christian Religious Studies", "CRS", False),
    ("Yoruba Language", "YOR", False),
    ("French", "FRE", False),
    ("Economics", "ECO", False),
    ("Commerce", "COM", False),
    ("Financial Accounting", "ACC", False),
    ("Government", "GOV", False),
    ("Geography", "GEO", False),
    ("Biology", "BIO", False),
    ("Chemistry", "CHE", False),
    ("Physics", "PHY", False),
    ("Literature in English", "LIT", False),
    ("Further Mathematics", "FMA", False),
]


def _user_school(request):
    profile = getattr(request.user, "profile", None)
    profile_school = getattr(profile, "school", None)
    if profile_school:
        return profile_school
    if request.user.is_superuser:
        return School.objects.first()
    return None


def _schools_for_user(request):
    return _user_school(request)


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
        "can_manage_academics": has_role(request.user, *ADMIN_ROLES),
    })


@login_required
@role_required(*ADMIN_ROLES)
def initialize_academic_data(request):
    school = _user_school(request)
    if not school:
        messages.error(request, "No school is assigned to your account.")
        return redirect("academics:dashboard")

    if request.method != "POST":
        return redirect("academics:dashboard")

    classes_created = 0
    subjects_created = 0

    for name in DEFAULT_CLASSES:
        _, created = SchoolClass.objects.get_or_create(school=school, name=name)
        classes_created += int(created)

    for name, code, is_core in DEFAULT_SUBJECTS:
        subject = Subject.objects.filter(school=school, code=code).first()
        if not subject:
            Subject.objects.create(
                school=school,
                name=name,
                code=code,
                is_core=is_core,
            )
            subjects_created += 1

    log_activity(
        request,
        action="CREATE",
        module="Academics",
        description=f"Initialized default academic data: {classes_created} classes and {subjects_created} subjects.",
    )
    messages.success(
        request,
        f"Academic structure initialized successfully: {classes_created} new classes and {subjects_created} new subjects added.",
    )
    return redirect("academics:dashboard")


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
        form.save()
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
        form.save()
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
