from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ParentPortalLink, UserProfile
from apps.accounts.signals import provision_portal_account
from apps.academics.models import SchoolClass
from apps.schools.models import School
from apps.students.models import Parent, Student


User = get_user_model()

DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

STUDENT_FIRST_NAMES = (
    "Zainab", "Zaynul", "Aisha", "Abdullah",
    "Maryam", "Ibrahim", "Hannah", "Samuel",
    "Fatimah", "Yusuf", "Daniel", "Safiyyah",
)

STUDENT_LAST_NAMES = (
    "Adekunle", "Balogun", "Ibrahim", "Okafor",
    "Yusuf", "Adebayo",
)

PARENT_FIRST_NAMES = (
    "Kareem", "Mariam", "Abdul", "Aisha", "Hassan", "Safiya",
)

PARENT_LAST_NAMES = (
    "DemoFamily", "DemoHouse", "DemoParent", "DemoGuardian",
    "DemoHome", "DemoFamily",
)


class Command(BaseCommand):
    help = (
        "Seed only demo students, parents, portal ownership links, "
        "student/parent portal profiles, and school administrator accounts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--students-per-school",
            type=int,
            default=12,
            help="Number of synthetic students to seed per demo school (4-60, even).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        students_per_school = max(
            4,
            min(options["students_per_school"], 60),
        )
        if students_per_school % 2:
            students_per_school += 1

        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES,
        ).order_by("short_name")

        if schools.count() != len(DEMO_SCHOOL_CODES):
            raise RuntimeError(
                "Run seed_demo_schools first. Expected all 10 demo schools."
            )

        created_students = 0
        created_parents = 0
        created_school_admins = 0

        for school in schools:
            session = school.academic_sessions.filter(
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
            classes = list(
                SchoolClass.objects.filter(school=school).order_by("id")
            )

            if session is None or term is None or len(classes) != 14:
                raise RuntimeError(
                    f"{school.short_name}: run seed_demo_academics first."
                )

            students = []
            for student_no in range(1, students_per_school + 1):
                admission_number = (
                    f"{school.short_name}/2026/{student_no:04d}"
                )
                student, created = Student.objects.get_or_create(
                    admission_number=admission_number,
                    defaults={
                        "school": school,
                        "first_name": STUDENT_FIRST_NAMES[
                            (student_no - 1) % len(STUDENT_FIRST_NAMES)
                        ],
                        "last_name": STUDENT_LAST_NAMES[
                            (student_no - 1) % len(STUDENT_LAST_NAMES)
                        ],
                        "other_name": "Demo",
                        "gender": "F" if student_no % 2 else "M",
                        "date_of_birth": date(
                            2012 + (student_no % 5),
                            2 + (student_no % 10),
                            5 + (student_no % 20),
                        ),
                        "admission_date": date(2026, 9, 1),
                        "current_class": classes[
                            (student_no - 1) % len(classes)
                        ],
                        "current_session": session,
                        "current_term": term,
                        "status": "ACTIVE",
                    },
                )

                if student.school_id != school.id:
                    raise ValueError(
                        f"Student {student.admission_number} belongs to "
                        "another school."
                    )

                desired_class = classes[
                    (student_no - 1) % len(classes)
                ]
                updates = {}
                if student.current_class_id != desired_class.id:
                    updates["current_class"] = desired_class
                if student.current_session_id != session.id:
                    updates["current_session"] = session
                if student.current_term_id != term.id:
                    updates["current_term"] = term
                if student.status != "ACTIVE":
                    updates["status"] = "ACTIVE"

                if updates:
                    for field, value in updates.items():
                        setattr(student, field, value)
                    student.save(update_fields=list(updates))

                students.append(student)
                created_students += int(created)

            for parent_no in range(1, (students_per_school // 2) + 1):
                first_name = PARENT_FIRST_NAMES[
                    (parent_no - 1) % len(PARENT_FIRST_NAMES)
                ]
                last_name = (
                    f"{PARENT_LAST_NAMES[(parent_no - 1) % len(PARENT_LAST_NAMES)]}"
                    f"{parent_no}"
                )
                email = (
                    f"parent{parent_no}."
                    f"{school.short_name.lower()}@edutrack-demo.test"
                )
                phone = (
                    f"080700"
                    f"{DEMO_SCHOOL_CODES.index(school.short_name) + 1:02d}"
                    f"{parent_no:02d}"
                )

                parent, created = Parent.objects.get_or_create(
                    school=school,
                    first_name=first_name,
                    last_name=last_name,
                    defaults={
                        "phone": phone,
                        "email": email,
                        "address": f"Demo Estate, {school.short_name}",
                    },
                )

                if parent.school_id != school.id:
                    raise ValueError(
                        f"Parent {parent} belongs to another school."
                    )

                changed = []
                desired_values = {
                    "phone": phone,
                    "email": email,
                    "address": f"Demo Estate, {school.short_name}",
                }
                for field, value in desired_values.items():
                    if getattr(parent, field) != value:
                        setattr(parent, field, value)
                        changed.append(field)

                if changed:
                    parent.save(update_fields=changed)

                parent.students.set(
                    students[(parent_no - 1) * 2: parent_no * 2]
                )
                created_parents += int(created)

                portal_link = (
                    ParentPortalLink.objects
                    .select_related("user")
                    .filter(parent=parent)
                    .first()
                )
                if portal_link is None:
                    raise RuntimeError(
                        f"{school.short_name}: parent portal account was "
                        f"not provisioned for {parent}."
                    )

                user = portal_link.user
                desired_username = f"{school.short_name}-P{parent_no:03d}"
                conflicting_user = (
                    User.objects
                    .filter(username=desired_username)
                    .exclude(pk=user.pk)
                    .first()
                )
                if conflicting_user is not None:
                    raise ValueError(
                        f"Portal username {desired_username} is already in use."
                    )

                user.username = desired_username
                user.first_name = parent.first_name
                user.last_name = parent.last_name
                user.email = parent.email
                user.is_active = True
                user.save(
                    update_fields=[
                        "username",
                        "first_name",
                        "last_name",
                        "email",
                        "is_active",
                    ]
                )

                profile = user.profile
                if profile.role is None or profile.role.code != "PARENT":
                    raise RuntimeError(
                        f"{desired_username} is not assigned the PARENT role."
                    )
                profile.school = school
                profile.parent_id = desired_username
                profile.save(update_fields=["school", "parent_id"])

            admin_username = f"admin_{school.short_name.lower()}"
            admin_exists = User.objects.filter(
                username=admin_username,
            ).exists()
            admin = provision_portal_account(
                username=admin_username,
                first_name="Demo",
                last_name="Administrator",
                email=(
                    f"admin.{school.short_name.lower()}"
                    "@edutrack-demo.test"
                ),
                school=school,
                role_code="SCHOOL_ADMIN",
            )
            if admin is None:
                raise RuntimeError(
                    f"Could not provision school administrator for "
                    f"{school.short_name}."
                )

            profile = UserProfile.objects.get(user=admin)
            profile.school = school
            profile.is_school_admin = True
            profile.save(update_fields=["school", "is_school_admin"])

            created_school_admins += int(not admin_exists)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo students & portal stage complete: "
                f"{schools.count()} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{created_students} students, "
            f"{created_parents} parents, "
            f"{created_school_admins} school administrators."
        )
        self.stdout.write(
            "Totals: "
            f"{Student.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} students | "
            f"{Parent.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} parents | "
            f"{UserProfile.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES, role__code='STUDENT').count()} student portal profiles | "
            f"{UserProfile.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES, role__code='PARENT').count()} parent portal profiles | "
            f"{UserProfile.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES, role__code='SCHOOL_ADMIN').count()} school admin profiles"
        )
