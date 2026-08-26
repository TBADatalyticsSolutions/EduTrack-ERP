from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.schools.models import School
from apps.students.models import Student
from apps.academics.models import (
    AcademicSession,
    SchoolClass,
    Term,
)

from .models import (
    AttendanceSession,
    AttendanceRecord,
)

from .services import AttendanceService


def run():
    print("\n==========================================")
    print("       EDUTRACK ATTENDANCE TEST")
    print("==========================================\n")

    # ======================================================
    # DATABASE COUNTS
    # ======================================================

    print("Schools:", School.objects.count())
    print("Students:", Student.objects.count())
    print("Academic Sessions:", AcademicSession.objects.count())
    print("Classes:", SchoolClass.objects.count())
    print("Terms:", Term.objects.count())

    # ======================================================
    # TEST DATA
    # ======================================================

    school = School.objects.first()
    academic_session = AcademicSession.objects.first()
    term = Term.objects.first()
    school_class = SchoolClass.objects.first()

    if not school:
        print("\nERROR: No school exists.")
        return

    if not academic_session:
        print("\nERROR: No academic session exists.")
        return

    if not term:
        print("\nERROR: No term exists.")
        return

    if not school_class:
        print("\nERROR: No school class exists.")
        return

    print("\n------------------------------------------")
    print("SELECTED TEST DATA")
    print("------------------------------------------")

    print("School:", school)
    print("Academic Session:", academic_session)
    print("Term:", term)
    print("Class:", school_class)

    # ======================================================
    # STUDENTS
    # ======================================================

    students = AttendanceService.students_for_class(
        school_class
    )

    print("\nStudents in class:", students.count())

    for student in students[:10]:
        print(
            student.admission_number,
            "|",
            student.full_name(),
            "| School:",
            student.school_id,
            "| Class:",
            student.current_class_id,
            "| Status:",
            student.status,
        )

    if not students.exists():
        print(
            "\nWARNING: No students are currently assigned "
            "to this class."
        )
        return

    # ======================================================
    # CREATE / GET ATTENDANCE SESSION
    # ======================================================

    attendance_date = timezone.localdate()

    session, created = (
        AttendanceService.get_or_create_session(
            school=school,
            school_class=school_class,
            academic_session=academic_session,
            term=term,
            attendance_date=attendance_date,
            user=None,
        )
    )

    print("\n------------------------------------------")
    print("ATTENDANCE SESSION")
    print("------------------------------------------")

    print("Session:", session)
    print("Session ID:", session.pk)
    print("Created:", created)

    # ======================================================
    # VALIDATE SESSION
    # ======================================================

    try:
        AttendanceService.validate_session(session)
        print("Session validation: PASSED")

    except ValidationError as exc:
        print("Session validation: FAILED")
        print(exc)
        return

    # ======================================================
    # INITIAL SUMMARY
    # ======================================================

    summary = AttendanceService.session_summary(
        session
    )

    print("\nInitial summary:")
    print(summary)

    # ======================================================
    # MARK FIRST STUDENT PRESENT
    # ======================================================

    first_student = students.first()

    try:

        record = AttendanceService.mark_student(
            attendance_session=session,
            student=first_student,
            status=AttendanceRecord.PRESENT,
            user=None,
        )

        print(
            "\nFirst student:",
            first_student.full_name()
        )

        print(
            "Initial status:",
            record.get_status_display()
        )

    except ValidationError as exc:

        print("\nERROR marking first student:")
        print(exc)
        return

    # ======================================================
    # CHANGE PRESENT → LATE
    # ======================================================

    record = AttendanceService.mark_student(
        attendance_session=session,
        student=first_student,
        status=AttendanceRecord.LATE,
        user=None,
    )

    print(
        "Updated status:",
        record.get_status_display()
    )

    # ======================================================
    # MARK SECOND STUDENT ABSENT
    # ======================================================

    second_student = students[1] if students.count() > 1 else None

    if second_student:

        record = AttendanceService.mark_student(
            attendance_session=session,
            student=second_student,
            status=AttendanceRecord.ABSENT,
            user=None,
        )

        print(
            "Second student:",
            second_student.full_name()
        )

        print(
            "Status:",
            record.get_status_display()
        )

    # ======================================================
    # SESSION SUMMARY
    # ======================================================

    summary = AttendanceService.session_summary(
        session
    )

    print("\n------------------------------------------")
    print("FINAL SUMMARY")
    print("------------------------------------------")

    print("Total:", summary["total"])
    print("Present:", summary["present"])
    print("Absent:", summary["absent"])
    print("Late:", summary["late"])
    print("Excused:", summary["excused"])
    print(
        "Attendance %:",
        summary["attendance_percentage"]
    )

    # ======================================================
    # DATABASE VERIFICATION
    # ======================================================

    print("\n------------------------------------------")
    print("DATABASE VERIFICATION")
    print("------------------------------------------")

    print(
        "Attendance sessions:",
        AttendanceSession.objects.count()
    )

    print(
        "Attendance records:",
        AttendanceRecord.objects.count()
    )

    print("\n==========================================")
    print("           TEST COMPLETED")
    print("==========================================\n")
