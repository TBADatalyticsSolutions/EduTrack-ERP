from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.models import Subject
from apps.results.models import StudentResult, SubjectResult
from apps.results.services import calculate_student_result
from apps.schools.models import School
from apps.students.models import Student


DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

SUBJECT_CODES = (
    "ENG", "MAT", "BSC", "BTE", "SST",
    "CIV", "CMP", "AGR", "BUS", "IRS",
)

SESSION_NAME = "2026/2027"
TERM_NAME = "First Term"

# Deterministic score range: 55-90 overall, using only the configured
# CA1 (15), CA2 (15), and Examination (70) components.
def score_components(student_number, subject_number):
    ca1 = Decimal(8 + ((student_number + subject_number) % 8))
    ca2 = Decimal(8 + ((student_number * 2 + subject_number * 2) % 8))
    target_total = Decimal(
        55 + ((student_number * 7 + subject_number * 3) % 36)
    )
    examination = target_total - ca1 - ca2
    return ca1, ca2, Decimal("0.00"), Decimal("0.00"), examination


class Command(BaseCommand):
    help = (
        "Seed only Stage 8 demo student results and subject results "
        "for the current 2026/2027 First Term."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES,
        ).order_by("short_name")

        if schools.count() != len(DEMO_SCHOOL_CODES):
            raise RuntimeError(
                "Run seed_demo_schools first. Expected all 10 demo schools."
            )

        created_results = 0
        created_subject_results = 0

        for school in schools:
            session = school.sessions.filter(name=SESSION_NAME).first()
            term = (
                school.terms.filter(
                    session=session,
                    name=TERM_NAME,
                ).first()
                if session
                else None
            )

            if session is None or term is None:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_academics first."
                )

            subjects = list(
                Subject.objects.filter(
                    school=school,
                    code__in=[
                        f"{school.short_name}-{code}"
                        for code in SUBJECT_CODES
                    ],
                ).order_by("code")
            )

            if len(subjects) != len(SUBJECT_CODES):
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_subjects_teaching first."
                )

            students = list(
                Student.objects.filter(
                    school=school,
                    status="ACTIVE",
                    current_session=session,
                    current_term=term,
                ).order_by("admission_number")
            )

            if len(students) != 12:
                raise RuntimeError(
                    f"{school.short_name}: expected 12 active current-term "
                    f"demo students, found {len(students)}."
                )

            for student_number, student in enumerate(students, start=1):
                if student.school_id != school.id:
                    raise ValueError(
                        f"Student {student.admission_number} belongs to another school."
                    )

                if student.current_class_id is None:
                    raise ValueError(
                        f"Student {student.admission_number} has no current class."
                    )

                result, created = StudentResult.objects.get_or_create(
                    student=student,
                    session=session,
                    term=term,
                    defaults={
                        "school": school,
                        "school_class": student.current_class,
                        "teacher_remark": "Consistent effort throughout the term.",
                        "principal_remark": "Keep up the good work.",
                        "promotion_status": "PENDING",
                        "next_term_resumption": term.resumption_date,
                        "published": student_number % 4 != 0,
                    },
                )
                created_results += int(created)

                if result.school_id != school.id:
                    raise ValueError(
                        f"Result for {student.admission_number} belongs to another school."
                    )

                updates = {}
                desired_values = {
                    "school_class": student.current_class,
                    "teacher_remark": "Consistent effort throughout the term.",
                    "principal_remark": "Keep up the good work.",
                    "promotion_status": "PENDING",
                    "next_term_resumption": term.resumption_date,
                    "published": student_number % 4 != 0,
                }
                for field, value in desired_values.items():
                    if getattr(result, field) != value:
                        updates[field] = value

                if updates:
                    for field, value in updates.items():
                        setattr(result, field, value)
                    result.save(update_fields=list(updates))

                for subject_number, subject in enumerate(subjects, start=1):
                    ca1, ca2, assignment, project, examination = (
                        score_components(student_number, subject_number)
                    )

                    subject_result, created = SubjectResult.objects.get_or_create(
                        student_result=result,
                        subject=subject,
                        defaults={
                            "ca1": ca1,
                            "ca2": ca2,
                            "assignment": assignment,
                            "project": project,
                            "examination": examination,
                            "teacher_remark": "Good effort.",
                        },
                    )
                    created_subject_results += int(created)

                    changed = []
                    desired_scores = {
                        "ca1": ca1,
                        "ca2": ca2,
                        "assignment": assignment,
                        "project": project,
                        "examination": examination,
                        "teacher_remark": "Good effort.",
                    }
                    for field, value in desired_scores.items():
                        if getattr(subject_result, field) != value:
                            setattr(subject_result, field, value)
                            changed.append(field)

                    if changed:
                        subject_result.save(update_fields=changed)

                # Recalculate after all ten subject rows exist. This also
                # recalculates class positions using the existing service.
                calculate_student_result(result)

        self.stdout.write(
            self.style.SUCCESS(
                "Stage 8 results demo stage complete: "
                f"{schools.count()} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{created_results} student results, "
            f"{created_subject_results} subject results."
        )
        self.stdout.write(
            "Totals: "
            f"{StudentResult.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} "
            f"student results | "
            f"{SubjectResult.objects.filter(student_result__school__short_name__in=DEMO_SCHOOL_CODES).count()} "
            "subject results"
        )
