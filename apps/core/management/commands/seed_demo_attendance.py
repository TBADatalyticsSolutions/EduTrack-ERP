from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import UserProfile
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.schools.models import School


DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

ATTENDANCE_STATUSES = (
    AttendanceRecord.PRESENT,
    AttendanceRecord.PRESENT,
    AttendanceRecord.LATE,
    AttendanceRecord.ABSENT,
    AttendanceRecord.EXCUSED,
)


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Seed Stage 7 demo attendance for the current 2026/2027 First Term: "
        "five school days of class sessions and student attendance records."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES,
        ).order_by("short_name")

        if schools.count() != len(DEMO_SCHOOL_CODES):
            raise RuntimeError(
                "Run the Stage 1 demo school seed first. "
                "Expected all 10 demo schools."
            )

        created_sessions = 0
        created_records = 0

        for school in schools:
            session = school.sessions.filter(
                name="2026/2027",
            ).first()
            term = (
                school.terms.filter(
                    session=session,
                    name="First Term",
                ).first()
                if session
                else None
            )

            if session is None or term is None:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_academics first."
                )

            admin_username = f"admin_{school.short_name.lower()}"
            admin = User.objects.filter(
                username=admin_username,
                is_active=True,
            ).first()
            if admin is None:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_students_portal "
                    "first so the school administrator exists."
                )

            profile = UserProfile.objects.filter(
                user=admin,
                school=school,
                role__code="SCHOOL_ADMIN",
                is_school_admin=True,
            ).first()
            if profile is None:
                raise RuntimeError(
                    f"{school.short_name}: expected an active SCHOOL_ADMIN "
                    "profile for {admin_username}."
                )

            students = list(
                school.students.filter(
                    status="ACTIVE",
                    current_session=session,
                    current_term=term,
                ).select_related("current_class").order_by(
                    "admission_number"
                )
            )
            if not students:
                raise RuntimeError(
                    f"{school.short_name}: no active current-term students. "
                    "Run seed_demo_students_portal first."
                )

            for day_index in range(5):
                attendance_date = (
                    term.resumption_date + timedelta(days=day_index)
                )

                students_by_class = {}
                for student in students:
                    if student.current_class_id is None:
                        raise RuntimeError(
                            f"{student.admission_number}: current class is required."
                        )
                    students_by_class.setdefault(
                        student.current_class_id,
                        [],
                    ).append(student)

                for class_id, class_students in students_by_class.items():
                    attendance_session, created = (
                        AttendanceSession.objects.get_or_create(
                            school=school,
                            school_class_id=class_id,
                            academic_session=session,
                            term=term,
                            attendance_date=attendance_date,
                            defaults={
                                "created_by": admin,
                                "is_active": day_index < 4,
                            },
                        )
                    )
                    if created:
                        created_sessions += 1

                    session_updates = []
                    if attendance_session.created_by_id != admin.id:
                        attendance_session.created_by = admin
                        session_updates.append("created_by")
                    desired_active = day_index < 4
                    if attendance_session.is_active != desired_active:
                        attendance_session.is_active = desired_active
                        session_updates.append("is_active")
                    if session_updates:
                        attendance_session.save(
                            update_fields=session_updates
                        )

                    for student_index, student in enumerate(class_students):
                        status = ATTENDANCE_STATUSES[
                            (student_index + day_index) % len(ATTENDANCE_STATUSES)
                        ]
                        remark = (
                            "Demo late arrival."
                            if status == AttendanceRecord.LATE
                            else "Demo approved absence."
                            if status == AttendanceRecord.ABSENT
                            else "Demo excused absence."
                            if status == AttendanceRecord.EXCUSED
                            else ""
                        )

                        record, record_created = (
                            AttendanceRecord.objects.get_or_create(
                                attendance_session=attendance_session,
                                student=student,
                                defaults={
                                    "status": status,
                                    "remarks": remark,
                                    "marked_by": admin,
                                },
                            )
                        )
                        if record_created:
                            created_records += 1
                        else:
                            changed = []
                            if record.status != status:
                                record.status = status
                                changed.append("status")
                            if record.remarks != remark:
                                record.remarks = remark
                                changed.append("remarks")
                            if record.marked_by_id != admin.id:
                                record.marked_by = admin
                                changed.append("marked_by")
                            if changed:
                                record.save(update_fields=changed)

        self.stdout.write(
            self.style.SUCCESS(
                f"Stage 7 attendance complete: {schools.count()} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{created_sessions} attendance sessions, "
            f"{created_records} attendance records."
        )
        self.stdout.write(
            "Totals: "
            f"{AttendanceSession.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} attendance sessions | "
            f"{AttendanceRecord.objects.filter(attendance_session__school__short_name__in=DEMO_SCHOOL_CODES).count()} attendance records"
        )
