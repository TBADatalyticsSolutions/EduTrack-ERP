from datetime import date, datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.academics.models import AcademicSession, ClassArm, SchoolClass, Term
from apps.schools.models import School


SESSION_NAMES = ("2025/2026", "2026/2027")
TERM_NAMES = ("First Term", "Second Term", "Third Term")
CLASS_NAMES = (
    "Nursery 1",
    "Nursery 2",
    "Primary 1",
    "Primary 2",
    "Primary 3",
    "Primary 4",
    "Primary 5",
    "Primary 6",
    "JSS 1",
    "JSS 2",
    "JSS 3",
    "SS 1",
    "SS 2",
    "SS 3",
)
ARM_NAMES = ("A", "B")

RESUMPTION_DATES = {
    "2025/2026": {
        "First Term": date(2025, 9, 8),
        "Second Term": date(2026, 1, 12),
        "Third Term": date(2026, 4, 20),
    },
    "2026/2027": {
        "First Term": date(2026, 9, 14),
        "Second Term": date(2027, 1, 11),
        "Third Term": date(2027, 4, 26),
    },
}


class Command(BaseCommand):
    help = (
        "Seed only the demo academic structure: sessions, terms, classes, "
        "and class arms."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = School.objects.filter(short_name__in=[
            "AFAAB",
            "GIA",
            "CHC",
            "RCS",
            "BFA",
            "LIS",
            "HMC",
            "OBS",
            "SSA",
            "PIC",
        ]).order_by("short_name")

        processed_schools = 0
        sessions_created = 0
        terms_created = 0
        classes_created = 0
        arms_created = 0

        for school in schools:
            processed_schools += 1

            sessions = {}
            for session_name in SESSION_NAMES:
                session, created = AcademicSession.objects.get_or_create(
                    school=school,
                    name=session_name,
                    defaults={"is_current": session_name == "2026/2027"},
                )
                if created:
                    sessions_created += 1

                desired_current = session_name == "2026/2027"
                if session.is_current != desired_current:
                    session.is_current = desired_current
                    session.save(update_fields=["is_current"])

                sessions[session_name] = session

            for session_name, session in sessions.items():
                for term_name in TERM_NAMES:
                    term, created = Term.objects.get_or_create(
                        school=school,
                        session=session,
                        name=term_name,
                        defaults={
                            "is_current": (
                                session_name == "2026/2027"
                                and term_name == "First Term"
                            ),
                            "resumption_date": RESUMPTION_DATES[
                                session_name
                            ][term_name],
                        },
                    )
                    if created:
                        terms_created += 1

                    desired_current = (
                        session_name == "2026/2027"
                        and term_name == "First Term"
                    )
                    desired_resumption = RESUMPTION_DATES[
                        session_name
                    ][term_name]

                    changed_fields = []
                    if term.is_current != desired_current:
                        term.is_current = desired_current
                        changed_fields.append("is_current")
                    if term.resumption_date != desired_resumption:
                        term.resumption_date = desired_resumption
                        changed_fields.append("resumption_date")

                    if changed_fields:
                        term.save(update_fields=changed_fields)

            for class_name in CLASS_NAMES:
                school_class, created = SchoolClass.objects.get_or_create(
                    school=school,
                    name=class_name,
                )
                if created:
                    classes_created += 1

                for arm_name in ARM_NAMES:
                    _, created = ClassArm.objects.get_or_create(
                        school=school,
                        school_class=school_class,
                        name=arm_name,
                    )
                    if created:
                        arms_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Demo academic structure stage complete: "
                f"{processed_schools} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{sessions_created} sessions, "
            f"{terms_created} terms, "
            f"{classes_created} classes, "
            f"{arms_created} arms."
        )
        self.stdout.write(
            "Totals: "
            f"{AcademicSession.objects.count()} sessions | "
            f"{Term.objects.count()} terms | "
            f"{SchoolClass.objects.count()} classes | "
            f"{ClassArm.objects.count()} arms"
        )
