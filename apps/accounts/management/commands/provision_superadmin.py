from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role, UserProfile


class Command(BaseCommand):
    help = (
        "Create or safely synchronize a platform super-admin account. "
        "Existing non-superuser accounts are never promoted unless "
        "--promote-existing is explicitly supplied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="Username for the platform super-admin account.",
        )
        parser.add_argument(
            "--email",
            default="",
            help="Optional email address. Existing email is preserved when omitted.",
        )
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")
        parser.add_argument(
            "--promote-existing",
            action="store_true",
            help=(
                "Allow an existing non-superuser account to be promoted. "
                "Without this flag the command fails safely."
            ),
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Interactively reset the password of an existing account.",
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            help=(
                "Do not prompt. For a new account, "
                "DJANGO_SUPERADMIN_PASSWORD must be set."
            ),
        )

    def _password(self, *, noinput, reset):
        if noinput:
            import os

            password = os.getenv("DJANGO_SUPERADMIN_PASSWORD", "")
            if not password:
                raise CommandError(
                    "DJANGO_SUPERADMIN_PASSWORD must be set when using --noinput."
                )
            return password

        prompt = "Enter super-admin password: " if reset else "Enter password: "
        password = getpass(prompt)
        if not password:
            raise CommandError("Password cannot be empty.")

        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise CommandError("Passwords do not match.")
        return password

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"].strip()
        if not username:
            raise CommandError("Username cannot be empty.")

        User = get_user_model()
        role, _ = Role.objects.get_or_create(
            code="SUPER_ADMIN",
            defaults={
                "name": "Super Administrator",
                "description": "Platform-level EduTrack administrator.",
            },
        )

        user = User.objects.filter(username=username).first()
        created = user is None

        if user is not None and not user.is_superuser:
            if not options["promote_existing"]:
                raise CommandError(
                    f"User '{username}' already exists and is not a superuser. "
                    "Refusing to change its privilege level. "
                    "Use --promote-existing only after verifying this is the "
                    "intended platform administrator account."
                )

        if created:
            user = User(
                username=username,
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            user.set_password(
                self._password(
                    noinput=options["noinput"],
                    reset=False,
                )
            )
        else:
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True

            if options["reset_password"]:
                user.set_password(
                    self._password(
                        noinput=options["noinput"],
                        reset=True,
                    )
                )

        if options["email"]:
            user.email = options["email"].strip()
        if options["first_name"]:
            user.first_name = options["first_name"].strip()
        if options["last_name"]:
            user.last_name = options["last_name"].strip()

        if created:
            user.save()
        else:
            user.save(
                update_fields=[
                    "email",
                    "first_name",
                    "last_name",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    *(
                        ["password"]
                        if options["reset_password"]
                        else []
                    ),
                ]
            )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.school = None
        profile.is_school_admin = False
        profile.save(update_fields=["role", "school", "is_school_admin"])

        action = "Created" if created else "Synchronized"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} platform super-admin '{user.username}' successfully."
            )
        )
        self.stdout.write(
            "The account is platform-scoped (no school) and has SUPER_ADMIN role."
        )
