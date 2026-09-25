from django.core.management import call_command
from django.test import TestCase

from apps.schools.models import School, SchoolSubscription


class SeedDemoSchoolsCommandTests(TestCase):
    def test_seeds_ten_schools_and_subscriptions(self):
        call_command("seed_demo_schools")

        self.assertEqual(School.objects.count(), 10)
        self.assertEqual(SchoolSubscription.objects.count(), 10)
        self.assertEqual(
            School.objects.get(short_name="AFAAB").name,
            "AFAAB Digital Schools",
        )

    def test_rerun_is_idempotent_and_preserves_existing_contact_details(self):
        school = School.objects.create(
            name="AFAAB Digital Schools",
            short_name="AFAAB",
            motto="Old Motto",
            email="afaab-existing@example.com",
            phone="08000000000",
            address="Existing Address",
            website="https://existing.example.com",
        )

        call_command("seed_demo_schools")
        call_command("seed_demo_schools")

        self.assertEqual(School.objects.count(), 10)
        self.assertEqual(SchoolSubscription.objects.count(), 10)

        school.refresh_from_db()
        self.assertEqual(school.motto, "Pinnacle of Reliability")
        self.assertEqual(school.email, "afaab-existing@example.com")
        self.assertEqual(school.phone, "08000000000")
        self.assertEqual(school.address, "Existing Address")
        self.assertEqual(school.website, "https://existing.example.com")

    def test_school_stage_does_not_create_operational_data(self):
        call_command("seed_demo_schools")

        school = School.objects.get(short_name="AFAAB")

        self.assertFalse(hasattr(school, "students"))
        self.assertEqual(SchoolSubscription.objects.filter(school=school).count(), 1)
