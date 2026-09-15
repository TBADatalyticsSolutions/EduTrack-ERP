from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.access import role_code, teacher_can_access_class, teacher_class_ids
from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import AttendanceSessionForm
from .models import AttendanceRecord, AttendanceSession
from .services import AttendanceService


def get_user_profile(request):
    return getattr(request.user, "profile", None)


def get_user_role_code(request):
    profile = get_user_profile(request)
    if profile and profile.role:
        return profile.role.code
    return None


def get_attendance_school(request):
    profile = get_user_profile(request)
    if profile and profile.school:
        return profile.school
    if request.user.is_superuser:
        return School.objects.order_by("name").first()
    return None


def user_can_access_school(request, school):
    role = get_user_role_code(request)
    if role == "SUPER_ADMIN":
        return True
    profile = get_user_profile(request)
    return bool(profile and profile.school_id == school.id)


def _teacher_session_allowed(request, school_class):
    return role_code(request.user) != "TEACHER" or teacher_can_access_class(
        request.user, school_class
    )


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
def attendance_dashboard(request):
    school = get_attendance_school(request)
    if not school:
        messages.error(request, "Your account is not assigned to a school.")
        return redirect("accounts-dashboard")

    sessions = AttendanceSession.objects.select_related(
        "school", "school_class", "academic_session", "term", "created_by"
    ).filter(school=school)
    if role_code(request.user) == "TEACHER":
        sessions = sessions.filter(school_class_id__in=teacher_class_ids(request.user))
    sessions = sessions.order_by("-attendance_date", "-created_at")

    return render(request, "attendance/dashboard.html", {"sessions": sessions, "school": school})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
def attendance_create(request):
    school = get_attendance_school(request)
    if not school:
        messages.error(request, "No school is available for this account.")
        return redirect("attendance-dashboard")

    form = AttendanceSessionForm(request.POST or None)
    if role_code(request.user) == "TEACHER":
        form.fields["school_class"].queryset = form.fields["school_class"].queryset.filter(
            school=school, pk__in=teacher_class_ids(request.user)
        )

    if request.method == "POST" and form.is_valid():
        school_class = form.cleaned_data["school_class"]
        academic_session = form.cleaned_data["academic_session"]
        term = form.cleaned_data["term"]
        attendance_date = form.cleaned_data["attendance_date"]

        if school_class.school_id != school.id:
            form.add_error("school_class", "The selected class does not belong to your school.")
        elif not _teacher_session_allowed(request, school_class):
            form.add_error("school_class", "You can only create attendance for classes assigned to you.")
        elif academic_session.school_id != school.id:
            form.add_error("academic_session", "The selected academic session does not belong to your school.")
        elif term.school_id != school.id:
            form.add_error("term", "The selected term does not belong to your school.")
        else:
            try:
                session, created = AttendanceService.get_or_create_session(
                    school=school,
                    school_class=school_class,
                    academic_session=academic_session,
                    term=term,
                    attendance_date=attendance_date,
                    user=request.user,
                )
            except Exception as exc:
                messages.error(request, f"The attendance session could not be created: {exc}")
            else:
                if created:
                    log_activity(request, "CREATE", "Attendance", f"Created attendance session for {school_class.name} on {attendance_date}.")
                    messages.success(request, "Attendance session created successfully.")
                else:
                    messages.info(request, "An attendance session already exists for this class and date.")
                return redirect("attendance-session", pk=session.pk)

    return render(request, "attendance/create.html", {"form": form, "school": school})


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
def attendance_session(request, pk):
    session = get_object_or_404(
        AttendanceSession.objects.select_related("school", "school_class", "academic_session", "term", "created_by"),
        pk=pk,
    )
    if not user_can_access_school(request, session.school):
        messages.error(request, "You cannot access attendance for another school.")
        return redirect("attendance-dashboard")
    if not _teacher_session_allowed(request, session.school_class):
        messages.error(request, "You can only access attendance for classes assigned to you.")
        return redirect("attendance-dashboard")

    students = AttendanceService.students_for_class(
        session.school_class,
        academic_session=session.academic_session,
        school=session.school,
    )
    records = {record.student_id: record for record in AttendanceRecord.objects.filter(attendance_session=session)}
    for student in students:
        student.attendance_record = records.get(student.pk)

    if request.method == "POST":
        if not session.is_active:
            messages.error(request, "This attendance session is closed.")
            return redirect("attendance-session", pk=session.pk)
        attendance_data = {}
        for student in students:
            attendance_data[student.pk] = {
                "status": request.POST.get(f"status_{student.pk}", AttendanceRecord.PRESENT),
                "remarks": request.POST.get(f"remarks_{student.pk}", "").strip(),
            }
        try:
            saved_records = AttendanceService.mark_bulk(
                attendance_session=session,
                attendance_data=attendance_data,
                user=request.user,
            )
            log_activity(request, "UPDATE", "Attendance", f"Updated attendance for {session.school_class.name} on {session.attendance_date}. {len(saved_records)} attendance record(s) saved.")
            messages.success(request, "Attendance saved successfully.")
        except Exception as exc:
            messages.error(request, f"Attendance could not be saved: {exc}")
        return redirect("attendance-session", pk=session.pk)

    return render(request, "attendance/session.html", {
        "session": session,
        "students": students,
        "summary": AttendanceService.session_summary(session),
    })


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL")
def attendance_close(request, pk):
    session = get_object_or_404(AttendanceSession.objects.select_related("school", "school_class"), pk=pk)
    if not user_can_access_school(request, session.school):
        messages.error(request, "You cannot modify attendance for another school.")
        return redirect("attendance-dashboard")
    if not session.is_active:
        messages.info(request, "This attendance session is already closed.")
        return redirect("attendance-session", pk=session.pk)
    AttendanceService.close_session(session)
    log_activity(request, "UPDATE", "Attendance", f"Closed attendance session for {session.school_class.name} on {session.attendance_date}.")
    messages.success(request, "Attendance session closed successfully.")
    return redirect("attendance-session", pk=session.pk)


@login_required
@role_required("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "TEACHER")
def attendance_mark_all_present(request, pk):
    session = get_object_or_404(
        AttendanceSession.objects.select_related("school", "school_class", "academic_session", "term"),
        pk=pk,
    )
    if not user_can_access_school(request, session.school):
        messages.error(request, "You cannot modify attendance for another school.")
        return redirect("attendance-dashboard")
    if not _teacher_session_allowed(request, session.school_class):
        messages.error(request, "You can only modify attendance for classes assigned to you.")
        return redirect("attendance-dashboard")
    if not session.is_active:
        messages.error(request, "This attendance session is already closed.")
        return redirect("attendance-session", pk=session.pk)
    try:
        records = AttendanceService.mark_all_present(attendance_session=session, user=request.user)
        log_activity(request, "UPDATE", "Attendance", f"Marked all eligible students present for {session.school_class.name} on {session.attendance_date}. {len(records)} student(s) updated.")
        messages.success(request, f"{len(records)} student(s) have been marked Present.")
    except Exception as exc:
        messages.error(request, f"Attendance could not be updated: {exc}")
    return redirect("attendance-session", pk=session.pk)
