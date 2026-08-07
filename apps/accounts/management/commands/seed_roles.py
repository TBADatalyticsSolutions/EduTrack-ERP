from django.core.management.base import BaseCommand
from apps.accounts.utils import log_activity

from apps.accounts.models import Role
from apps.accounts.utils import log_activity


class Command(BaseCommand):

    help = "Create default system roles"

    ROLES = [

        (
            "SUPER_ADMIN",
            "Super Administrator",
        ),

        (
            "SCHOOL_ADMIN",
            "School Administrator",
        ),

        (
            "PRINCIPAL",
            "Principal",
        ),

        (
            "VICE_PRINCIPAL",
            "Vice Principal",
        ),

        (
            "REGISTRAR",
            "Registrar",
        ),

        (
            "TEACHER",
            "Teacher",
        ),

        (
            "ACCOUNTANT",
            "Accountant",
        ),

        (
            "LIBRARIAN",
            "Librarian",
        ),

        (
            "PARENT",
            "Parent",
        ),

        (
            "STUDENT",
            "Student",
        ),

    ]

    def handle(self, *args, **kwargs):

        for code, name in self.ROLES:

            role, created = Role.objects.get_or_create(

                code=code,

                defaults={

                    "name": name,

                },

            )

            if created:

                self.stdout.write(

                    self.style.SUCCESS(

                        f"Created {name}"

                    )

                )

            else:

                self.stdout.write(

                    f"{name} already exists"

                )

        self.stdout.write(

            self.style.SUCCESS(

                "Role seeding completed."

            )

        )