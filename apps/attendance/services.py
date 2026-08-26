from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.students.models import Student

from .models import (
    AttendanceRecord,
    AttendanceSession,
)


class AttendanceService:
    """
    Business logic for the EduTrack-ERP Attendance module.
    """

    # ==========================================================
    # STUDENTS FOR CLASS
    # ==========================================================

    @staticmethod
    def students_for_class(
        school_class,
        academic_session=None,
        school=None,
    ):
        """
        Return eligible students currently assigned to a class.

        Optional filters:
            academic_session
            school
        """

        students = (
            Student.objects
            .filter(
                current_class=school_class,
                status="ACTIVE",
                is_graduated=False,
            )
            .select_related(
                "school",
                "current_class",
                "current_session",
            )
            .order_by(
                "last_name",
                "first_name",
            )
        )

        if academic_session is not None:
            students = students.filter(
                current_session=academic_session,
            )

        if school is not None:
            students = students.filter(
                school=school,
            )

        return students

    # ==========================================================
    # CREATE / GET ATTENDANCE SESSION
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def get_or_create_session(
        *,
        school,
        school_class,
        academic_session,
        term,
        attendance_date=None,
        user=None,
    ):
        """
        Get an existing attendance session or create one.
        """

        if attendance_date is None:
            attendance_date = timezone.localdate()

        session, created = (
            AttendanceSession.objects
            .get_or_create(
                school=school,
                school_class=school_class,
                academic_session=academic_session,
                term=term,
                attendance_date=attendance_date,
                defaults={
                    "is_active": True,
                    "created_by": user,
                },
            )
        )

        return session, created

    # ==========================================================
    # VALIDATE SESSION
    # ==========================================================

    @staticmethod
    def validate_session(attendance_session):
        """
        Run model-level validation on an attendance session.
        """

        attendance_session.full_clean()

        return True

    # ==========================================================
    # MARK ONE STUDENT
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def mark_student(
        *,
        attendance_session,
        student,
        status,
        user=None,
        remarks="",
    ):
        """
        Create or update attendance for one student.
        """

        valid_statuses = {
            AttendanceRecord.PRESENT,
            AttendanceRecord.ABSENT,
            AttendanceRecord.LATE,
            AttendanceRecord.EXCUSED,
        }

        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid attendance status: {status}"
            )

        if not attendance_session.is_active:
            raise ValidationError(
                "This attendance session is closed."
            )

        # ------------------------------------------------------
        # Validate student against session
        # ------------------------------------------------------

        if student.school_id != attendance_session.school_id:
            raise ValidationError(
                "The student does not belong to "
                "the attendance session's school."
            )

        if (
            student.current_class_id
            and student.current_class_id
            != attendance_session.school_class_id
        ):
            raise ValidationError(
                "The student does not belong to "
                "the attendance session's class."
            )

        # ------------------------------------------------------
        # Create or update record
        # ------------------------------------------------------

        record, created = (
            AttendanceRecord.objects.get_or_create(
                attendance_session=attendance_session,
                student=student,
                defaults={
                    "status": status,
                    "remarks": remarks,
                    "marked_by": user,
                },
            )
        )

        if not created:
            record.status = status
            record.remarks = remarks
            record.marked_by = user

            record.save(
                update_fields=[
                    "status",
                    "remarks",
                    "marked_by",
                    "marked_at",
                    "updated_at",
                ]
            )

        record.full_clean()

        return record

    # ==========================================================
    # BULK MARK ATTENDANCE
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def mark_bulk(
        *,
        attendance_session,
        attendance_data,
        user=None,
    ):
        """
        Mark attendance for multiple students.

        Expected format:

        {
            student_id: {
                "status": "PRESENT",
                "remarks": ""
            }
        }
        """

        if not attendance_session.is_active:
            raise ValidationError(
                "This attendance session is closed."
            )

        records = []

        for student_id, data in attendance_data.items():

            student = Student.objects.filter(
                pk=student_id,
            ).first()

            if not student:
                raise ValidationError(
                    f"Student with ID {student_id} does not exist."
                )

            record = AttendanceService.mark_student(
                attendance_session=attendance_session,
                student=student,
                status=data.get(
                    "status",
                    AttendanceRecord.PRESENT,
                ),
                user=user,
                remarks=data.get(
                    "remarks",
                    "",
                ),
            )

            records.append(record)

        return records

    # ==========================================================
    # MARK ALL PRESENT
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def mark_all_present(
        *,
        attendance_session,
        user=None,
    ):
        """
        Mark all eligible students in the class as Present.
        """

        if not attendance_session.is_active:
            raise ValidationError(
                "This attendance session is closed."
            )

        students = AttendanceService.students_for_class(
            attendance_session.school_class,
            academic_session=attendance_session.academic_session,
            school=attendance_session.school,
        )

        records = []

        for student in students:

            record = AttendanceService.mark_student(
                attendance_session=attendance_session,
                student=student,
                status=AttendanceRecord.PRESENT,
                user=user,
            )

            records.append(record)

        return records

    # ==========================================================
    # SESSION SUMMARY
    # ==========================================================

    @staticmethod
    def session_summary(attendance_session):
        """
        Return attendance statistics for one session.
        """

        records = AttendanceRecord.objects.filter(
            attendance_session=attendance_session,
        )

        total = records.count()

        present = records.filter(
            status=AttendanceRecord.PRESENT,
        ).count()

        absent = records.filter(
            status=AttendanceRecord.ABSENT,
        ).count()

        late = records.filter(
            status=AttendanceRecord.LATE,
        ).count()

        excused = records.filter(
            status=AttendanceRecord.EXCUSED,
        ).count()

        attendance_percentage = (
            round(
                (
                    (present + late)
                    / total
                ) * 100,
                2,
            )
            if total
            else 0
        )

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendance_percentage": attendance_percentage,
        }

    # ==========================================================
    # STUDENT ATTENDANCE HISTORY
    # ==========================================================

    @staticmethod
    def student_history(student):
        """
        Return complete attendance history for a student.
        """

        return (
            AttendanceRecord.objects
            .filter(
                student=student,
            )
            .select_related(
                "attendance_session",
                "attendance_session__school",
                "attendance_session__school_class",
                "attendance_session__academic_session",
                "attendance_session__term",
            )
            .order_by(
                "-attendance_session__attendance_date",
            )
        )

    # ==========================================================
    # CLOSE SESSION
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def close_session(
        attendance_session,
        user=None,
    ):
        """
        Close an attendance session.

        The optional user parameter identifies the user
        performing the action. It is currently accepted for
        service/API consistency and future audit logging.
        """

        attendance_session.is_active = False

        attendance_session.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return attendance_session

    # ==========================================================
    # REOPEN SESSION
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def reopen_session(
        attendance_session,
        user=None,
    ):
        """
        Reopen an attendance session.

        The optional user parameter identifies the user
        performing the action. It is currently accepted for
        service/API consistency and future audit logging.
        """

        attendance_session.is_active = True

        attendance_session.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return attendance_session
