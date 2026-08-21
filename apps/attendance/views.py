from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import AttendanceSessionForm
from .models import (
    AttendanceRecord,
    AttendanceSession,
)
from .services import AttendanceService


# ==========================================================
# SCHOOL / ROLE HELPERS
# ==========================================================

def get_user_profile(request):
    """
    Safely return the logged-in user's profile.
    """

    return getattr(
        request.user,
        "profile",
        None,
    )


def get_user_role_code(request):
    """
    Return the user's role code when available.
    """

    profile = get_user_profile(request)

    if profile and profile.role:
        return profile.role.code

    return None


def get_attendance_school(request):
    """
    Determine the school the current user should work with.

    Rules
    -----
    SUPER_ADMIN:
        Can work without a school assigned to the profile.
        If no school is assigned, the first school is used.

    Other roles:
        Must have a school assigned to their profile.
    """

    profile = get_user_profile(request)

    role_code = get_user_role_code(request)

    # ------------------------------------------------------
    # Super Admin
    # ------------------------------------------------------

    if role_code == "SUPER_ADMIN":

        if profile and profile.school:
            return profile.school

        # Current EduTrack setup has one school.
        return (
            School.objects
            .order_by("name")
            .first()
        )

    # ------------------------------------------------------
    # Other roles
    # ------------------------------------------------------

    if profile and profile.school:
        return profile.school

    return None


def user_can_access_school(request, school):
    """
    Determine whether the current user can access
    the supplied school.
    """

    role_code = get_user_role_code(request)

    # Super Admin can access all schools.
    if role_code == "SUPER_ADMIN":
        return True

    profile = get_user_profile(request)

    if not profile or not profile.school:
        return False

    return profile.school_id == school.id


# ==========================================================
# ATTENDANCE DASHBOARD
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "TEACHER",
)
def attendance_dashboard(request):
    """
    Display attendance sessions accessible to the user.
    """

    school = get_attendance_school(request)

    sessions = (
        AttendanceSession.objects
        .select_related(
            "school",
            "school_class",
            "academic_session",
            "term",
            "created_by",
        )
        .order_by(
            "-attendance_date",
            "-created_at",
        )
    )

    # ------------------------------------------------------
    # School filtering
    # ------------------------------------------------------

    if get_user_role_code(request) != "SUPER_ADMIN":

        if not school:
            messages.error(
                request,
                "Your account is not assigned to a school.",
            )

            return redirect(
                "accounts-dashboard",
            )

        sessions = sessions.filter(
            school=school,
        )

    return render(
        request,
        "attendance/dashboard.html",
        {
            "sessions": sessions,
            "school": school,
        },
    )


# ==========================================================
# CREATE / OPEN ATTENDANCE SESSION
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "TEACHER",
)
def attendance_create(request):
    """
    Create or open an attendance session.

    SUPER_ADMIN:
        Can operate without profile.school.

    Other roles:
        Must have profile.school assigned.
    """

    school = get_attendance_school(request)

    # ------------------------------------------------------
    # SCHOOL VALIDATION
    # ------------------------------------------------------

    if not school:

        messages.error(
            request,
            "No school is available for this account.",
        )

        return redirect(
            "attendance-dashboard",
        )

    # ------------------------------------------------------
    # POST
    # ------------------------------------------------------

    if request.method == "POST":

        form = AttendanceSessionForm(
            request.POST,
        )

        if form.is_valid():

            school_class = form.cleaned_data[
                "school_class"
            ]

            academic_session = form.cleaned_data[
                "academic_session"
            ]

            term = form.cleaned_data[
                "term"
            ]

            attendance_date = form.cleaned_data[
                "attendance_date"
            ]

            # ------------------------------------------------
            # SCHOOL ↔ CLASS
            # ------------------------------------------------

            if (
                hasattr(
                    school_class,
                    "school_id",
                )
                and school_class.school_id
                != school.id
            ):

                form.add_error(
                    "school_class",
                    (
                        "The selected class does not "
                        "belong to the selected school."
                    ),
                )

            # ------------------------------------------------
            # SCHOOL ↔ ACADEMIC SESSION
            # ------------------------------------------------

            elif (
                hasattr(
                    academic_session,
                    "school_id",
                )
                and academic_session.school_id
                != school.id
            ):

                form.add_error(
                    "academic_session",
                    (
                        "The selected academic session "
                        "does not belong to the selected school."
                    ),
                )

            # ------------------------------------------------
            # SCHOOL ↔ TERM
            # ------------------------------------------------

            elif (
                hasattr(
                    term,
                    "school_id",
                )
                and term.school_id
                != school.id
            ):

                form.add_error(
                    "term",
                    (
                        "The selected term does not "
                        "belong to the selected school."
                    ),
                )

            else:

                try:

                    session, created = (
                        AttendanceService
                        .get_or_create_session(
                            school=school,
                            school_class=school_class,
                            academic_session=(
                                academic_session
                            ),
                            term=term,
                            attendance_date=(
                                attendance_date
                            ),
                            user=request.user,
                        )
                    )

                except Exception as exc:

                    messages.error(
                        request,
                        (
                            "The attendance session "
                            "could not be created: "
                            f"{exc}"
                        ),
                    )

                    return render(
                        request,
                        "attendance/create.html",
                        {
                            "form": form,
                            "school": school,
                        },
                    )

                # --------------------------------------------
                # CREATED
                # --------------------------------------------

                if created:

                    log_activity(
                        request,
                        action="CREATE",
                        module="Attendance",
                        description=(
                            "Created attendance session for "
                            f"{school_class.name} on "
                            f"{attendance_date}."
                        ),
                    )

                    messages.success(
                        request,
                        (
                            "Attendance session created "
                            "successfully."
                        ),
                    )

                # --------------------------------------------
                # ALREADY EXISTS
                # --------------------------------------------

                else:

                    messages.info(
                        request,
                        (
                            "An attendance session already "
                            "exists for this class and date."
                        ),
                    )

                return redirect(
                    "attendance-session",
                    pk=session.pk,
                )

    else:

        form = AttendanceSessionForm()

    return render(
        request,
        "attendance/create.html",
        {
            "form": form,
            "school": school,
        },
    )


# ==========================================================
# ATTENDANCE SESSION
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "TEACHER",
)
def attendance_session(request, pk):
    """
    Display and update attendance for one session.
    """

    session = get_object_or_404(
        AttendanceSession.objects.select_related(
            "school",
            "school_class",
            "academic_session",
            "term",
            "created_by",
        ),
        pk=pk,
    )

    # ------------------------------------------------------
    # SCHOOL ACCESS
    # ------------------------------------------------------

    if not user_can_access_school(
        request,
        session.school,
    ):

        messages.error(
            request,
            "You cannot access attendance for another school.",
        )

        return redirect(
            "attendance-dashboard",
        )

    # ------------------------------------------------------
    # ELIGIBLE STUDENTS
    # ------------------------------------------------------

    students = (
        AttendanceService.students_for_class(
            session.school_class,
            academic_session=(
                session.academic_session
            ),
            school=session.school,
        )
    )

    # ------------------------------------------------------
    # EXISTING RECORDS
    # ------------------------------------------------------

    records = {
        record.student_id: record
        for record in (
            AttendanceRecord.objects
            .filter(
                attendance_session=session,
            )
        )
    }

    # Attach record directly to each student
    # for template use.
    for student in students:

        student.attendance_record = (
            records.get(
                student.pk,
            )
        )

    # ------------------------------------------------------
    # SAVE ATTENDANCE
    # ------------------------------------------------------

    if request.method == "POST":

        if not session.is_active:

            messages.error(
                request,
                "This attendance session is closed.",
            )

            return redirect(
                "attendance-session",
                pk=session.pk,
            )

        attendance_data = {}

        for student in students:

            status = request.POST.get(
                f"status_{student.pk}",
                AttendanceRecord.PRESENT,
            )

            remarks = request.POST.get(
                f"remarks_{student.pk}",
                "",
            ).strip()

            attendance_data[
                student.pk
            ] = {
                "status": status,
                "remarks": remarks,
            }

        try:

            saved_records = (
                AttendanceService.mark_bulk(
                    attendance_session=session,
                    attendance_data=attendance_data,
                    user=request.user,
                )
            )

            log_activity(
                request,
                action="UPDATE",
                module="Attendance",
                description=(
                    "Updated attendance for "
                    f"{session.school_class.name} "
                    f"on {session.attendance_date}. "
                    f"{len(saved_records)} "
                    "attendance record(s) saved."
                ),
            )

            messages.success(
                request,
                "Attendance saved successfully.",
            )

        except Exception as exc:

            messages.error(
                request,
                (
                    "Attendance could not be saved: "
                    f"{exc}"
                ),
            )

        return redirect(
            "attendance-session",
            pk=session.pk,
        )

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    summary = (
        AttendanceService.session_summary(
            session,
        )
    )

    return render(
        request,
        "attendance/session.html",
        {
            "session": session,
            "students": students,
            "summary": summary,
        },
    )


# ==========================================================
# CLOSE ATTENDANCE SESSION
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
)
def attendance_close(request, pk):
    """
    Close an attendance session.
    """

    session = get_object_or_404(
        AttendanceSession.objects.select_related(
            "school",
            "school_class",
        ),
        pk=pk,
    )

    # ------------------------------------------------------
    # SCHOOL ACCESS
    # ------------------------------------------------------

    if not user_can_access_school(
        request,
        session.school,
    ):

        messages.error(
            request,
            "You cannot modify attendance for another school.",
        )

        return redirect(
            "attendance-dashboard",
        )

    # ------------------------------------------------------
    # CHECK ALREADY CLOSED
    # ------------------------------------------------------

    if not session.is_active:

        messages.info(
            request,
            "This attendance session is already closed.",
        )

        return redirect(
            "attendance-session",
            pk=session.pk,
        )

    # ------------------------------------------------------
    # CLOSE
    # ------------------------------------------------------

    AttendanceService.close_session(
        session,
    )

    log_activity(
        request,
        action="UPDATE",
        module="Attendance",
        description=(
            "Closed attendance session for "
            f"{session.school_class.name} "
            f"on {session.attendance_date}."
        ),
    )

    messages.success(
        request,
        "Attendance session closed successfully.",
    )

    return redirect(
        "attendance-session",
        pk=session.pk,
    )


# ==========================================================
# MARK ALL PRESENT
# ==========================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "TEACHER",
)
def attendance_mark_all_present(request, pk):
    """
    Mark all eligible students in an attendance session
    as Present.
    """

    session = get_object_or_404(
        AttendanceSession.objects.select_related(
            "school",
            "school_class",
            "academic_session",
            "term",
        ),
        pk=pk,
    )

    # ------------------------------------------------------
    # SCHOOL ACCESS
    # ------------------------------------------------------

    if not user_can_access_school(
        request,
        session.school,
    ):

        messages.error(
            request,
            "You cannot modify attendance for another school.",
        )

        return redirect(
            "attendance-dashboard",
        )

    # ------------------------------------------------------
    # SESSION STATUS
    # ------------------------------------------------------

    if not session.is_active:

        messages.error(
            request,
            "This attendance session is already closed.",
        )

        return redirect(
            "attendance-session",
            pk=session.pk,
        )

    # ------------------------------------------------------
    # MARK ALL PRESENT
    # ------------------------------------------------------

    try:

        records = (
            AttendanceService.mark_all_present(
                attendance_session=session,
                user=request.user,
            )
        )

        log_activity(
            request,
            action="UPDATE",
            module="Attendance",
            description=(
                "Marked all eligible students present "
                f"for {session.school_class.name} "
                f"on {session.attendance_date}. "
                f"{len(records)} student(s) updated."
            ),
        )

        messages.success(
            request,
            (
                f"{len(records)} student(s) have been "
                "marked Present."
            ),
        )

    except Exception as exc:

        messages.error(
            request,
            (
                "Attendance could not be updated: "
                f"{exc}"
            ),
        )

    return redirect(
        "attendance-session",
        pk=session.pk,
    )