from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ParentPortalLink, UserProfile
from apps.notifications.models import Notification
from apps.schools.models import School


User = get_user_model()

DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)


def sync_notification(*, school, recipient, title, message, notification_type, is_read):
    notification, created = Notification.objects.get_or_create(
        school=school,
        recipient=recipient,
        title=title,
        defaults={
            "message": message,
            "notification_type": notification_type,
            "is_read": is_read,
        },
    )

    changed = []
    desired = {
        "message": message,
        "notification_type": notification_type,
        "is_read": is_read,
    }
    for field, value in desired.items():
        if getattr(notification, field) != value:
            setattr(notification, field, value)
            changed.append(field)

    if is_read:
        if notification.read_at is None:
            from django.utils import timezone
            notification.read_at = timezone.now()
            changed.append("read_at")
    elif notification.read_at is not None:
        notification.read_at = None
        changed.append("read_at")

    if changed:
        notification.save(update_fields=changed)

    return notification, created


class Command(BaseCommand):
    help = (
        "Seed only Stage 9 demo notifications for school administrators, "
        "student portals, and parent portals."
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

        created_count = 0

        for school in schools:
            admin_profile = UserProfile.objects.select_related("user").filter(
                school=school,
                role__code="SCHOOL_ADMIN",
                is_school_admin=True,
                user__is_active=True,
            ).first()
            if admin_profile is None:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_students_portal first "
                    "so the school administrator exists."
                )

            admin = admin_profile.user

            _, created = sync_notification(
                school=school,
                recipient=admin,
                title="Welcome to EduTrack ERP Demo",
                message=(
                    "Your school demo environment is ready for academic, "
                    "attendance, results, and finance review."
                ),
                notification_type="INFO",
                is_read=True,
            )
            created_count += int(created)

            _, created = sync_notification(
                school=school,
                recipient=admin,
                title="Results Published for Review",
                message=(
                    "Stage 8 contains synthetic First Term academic results. "
                    "Review published and unpublished records before client demonstration."
                ),
                notification_type="SUCCESS",
                is_read=False,
            )
            created_count += int(created)

            student_profiles = list(
                UserProfile.objects.select_related("user").filter(
                    school=school,
                    role__code="STUDENT",
                    user__is_active=True,
                ).order_by("user__username")
            )
            if len(student_profiles) != 12:
                raise RuntimeError(
                    f"{school.short_name}: expected 12 student portal profiles, "
                    f"found {len(student_profiles)}."
                )

            for student_number, profile in enumerate(student_profiles, start=1):
                recipient = profile.user

                _, created = sync_notification(
                    school=school,
                    recipient=recipient,
                    title="First Term Resumption Notice",
                    message=(
                        "First Term 2026/2027 is now active. Check your portal "
                        "for attendance, academic results, and school updates."
                    ),
                    notification_type="INFO",
                    is_read=student_number % 2 == 0,
                )
                created_count += int(created)

                _, created = sync_notification(
                    school=school,
                    recipient=recipient,
                    title="Academic Performance Update",
                    message=(
                        "Your First Term academic performance record is available "
                        "in the portal when it has been published by the school."
                    ),
                    notification_type="SUCCESS",
                    is_read=student_number % 3 == 0,
                )
                created_count += int(created)

            parent_links = list(
                ParentPortalLink.objects.select_related(
                    "parent",
                    "user",
                ).filter(
                    parent__school=school,
                    user__is_active=True,
                ).order_by("user__username")
            )
            if len(parent_links) != 6:
                raise RuntimeError(
                    f"{school.short_name}: expected 6 parent portal links, "
                    f"found {len(parent_links)}."
                )

            for parent_number, link in enumerate(parent_links, start=1):
                recipient = link.user

                _, created = sync_notification(
                    school=school,
                    recipient=recipient,
                    title="Parent Finance Update",
                    message=(
                        "Your school finance records have been updated for "
                        "the current First Term. Review invoices and balances in the portal."
                    ),
                    notification_type="WARNING",
                    is_read=parent_number % 2 == 0,
                )
                created_count += int(created)

                _, created = sync_notification(
                    school=school,
                    recipient=recipient,
                    title="Parent Academic Update",
                    message=(
                        "First Term academic performance information is available "
                        "through the parent portal when results are published."
                    ),
                    notification_type="INFO",
                    is_read=parent_number % 3 == 0,
                )
                created_count += int(created)

        total = Notification.objects.filter(
            school__short_name__in=DEMO_SCHOOL_CODES,
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Stage 9 notifications complete: {schools.count()} schools processed."
            )
        )
        self.stdout.write(
            f"Created this run: {created_count} notifications."
        )
        self.stdout.write(
            f"Total demo notifications: {total}."
        )
