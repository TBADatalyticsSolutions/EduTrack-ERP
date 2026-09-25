from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.schools.models import School, SchoolSubscription


DEMO_SCHOOLS = (
    ("AFAAB Digital Schools", "AFAAB", "Pinnacle of Reliability"),
    ("Greenfield International Academy", "GIA", "Learning Without Limits"),
    ("Cedar Heights College", "CHC", "Knowledge Builds Leaders"),
    ("Royal Crest Schools", "RCS", "Character, Knowledge, Excellence"),
    ("Bright Future Academy", "BFA", "Discover. Learn. Lead."),
    ("Lighthouse International School", "LIS", "Guiding Minds, Shaping Futures"),
    ("Heritage Model College", "HMC", "Tradition Meets Innovation"),
    ("Oakbridge Schools", "OBS", "Growing Great Minds"),
    ("Sunrise Scholars Academy", "SSA", "Learn Today, Lead Tomorrow"),
    ("Pacesetters International College", "PIC", "Excellence in Every Learner"),
)

STARTED_AT = timezone.make_aware(datetime(2026, 1, 5))


class Command(BaseCommand):
    help = "Seed only the demo schools and their active subscriptions."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        reused = 0

        for index, (name, short_name, motto) in enumerate(DEMO_SCHOOLS, start=1):
            school = School.objects.filter(short_name=short_name).first()

            if school is None:
                school = School.objects.create(
                    name=name,
                    short_name=short_name,
                    motto=motto,
                    email=f"demo{index}@edutrack-demo.test",
                    phone=f"0809000{index:04d}",
                    address=f"{index} Demo Education Avenue, Abeokuta, Ogun State",
                    website=f"https://{short_name.lower()}.demo.edutrack.test",
                )
                created += 1
            else:
                # Reconcile only the demo profile fields. Preserve existing
                # contact details and logos on an already-created school.
                changed = False
                for field, value in (
                    ("name", name),
                    ("short_name", short_name),
                    ("motto", motto),
                ):
                    if getattr(school, field) != value:
                        setattr(school, field, value)
                        changed = True

                if changed:
                    school.save(update_fields=["name", "short_name", "motto"])
                reused += 1

            SchoolSubscription.objects.get_or_create(
                school=school,
                defaults={
                    "plan": "PREMIUM" if index % 3 == 0 else "STANDARD",
                    "status": "ACTIVE",
                    "started_at": STARTED_AT,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo school stage complete: {len(DEMO_SCHOOLS)} schools "
                f"processed ({created} created, {reused} reused)."
            )
        )
        self.stdout.write(
            f"Schools: {School.objects.count()} | "
            f"Subscriptions: {SchoolSubscription.objects.count()}"
        )
