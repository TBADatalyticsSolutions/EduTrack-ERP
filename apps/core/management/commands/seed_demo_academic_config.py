from django.core.management.base import BaseCommand
from django.db import transaction

from apps.results.models import AssessmentType, GradeSetting
from apps.schools.models import School

DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

ASSESSMENT_TYPES = (
    ("CA 1", 20, 1),
    ("CA 2", 20, 2),
    ("Assignment", 10, 3),
    ("Project", 10, 4),
    ("Examination", 40, 5),
)

GRADE_SETTINGS = (
    ("A", 70, 100, "Excellent"),
    ("B", 60, 69, "Very Good"),
    ("C", 50, 59, "Good"),
    ("D", 45, 49, "Fair"),
    ("E", 40, 44, "Pass"),
    ("F", 0, 39, "Fail"),
)


class Command(BaseCommand):
    help = (
        "Seed only demo academic configuration: assessment types and "
        "grade settings."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES
        ).order_by("short_name")

        if schools.count() != len(DEMO_SCHOOL_CODES):
            raise RuntimeError(
                "Run seed_demo_schools first. Expected all 10 demo schools."
            )

        created_assessments = 0
        created_grades = 0

        for school in schools:
            for name, maximum_score, order in ASSESSMENT_TYPES:
                _, created = AssessmentType.objects.get_or_create(
                    school=school,
                    name=name,
                    defaults={
                        "maximum_score": maximum_score,
                        "order": order,
                    },
                )
                if created:
                    created_assessments += 1

            for grade, minimum_score, maximum_score, remark in GRADE_SETTINGS:
                _, created = GradeSetting.objects.get_or_create(
                    school=school,
                    grade=grade,
                    defaults={
                        "minimum_score": minimum_score,
                        "maximum_score": maximum_score,
                        "remark": remark,
                    },
                )
                if created:
                    created_grades += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Demo academic configuration stage complete: "
                f"{schools.count()} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{created_assessments} assessment types, "
            f"{created_grades} grade settings."
        )
        self.stdout.write(
            "Totals: "
            f"{AssessmentType.objects.count()} assessment types | "
            f"{GradeSetting.objects.count()} grade settings"
        )
