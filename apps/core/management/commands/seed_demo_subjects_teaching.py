from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.models import ClassSubject, SchoolClass, Subject
from apps.schools.models import School
from apps.teachers.models import Department, Teacher, TeacherSubject


DEMO_SCHOOL_CODES = (
    "AFAAB", "GIA", "CHC", "RCS", "BFA",
    "LIS", "HMC", "OBS", "SSA", "PIC",
)

SUBJECT_SPECS = (
    ("English Language", "ENG", True),
    ("Mathematics", "MAT", True),
    ("Basic Science", "BSC", True),
    ("Basic Technology", "BTE", False),
    ("Social Studies", "SST", True),
    ("Civic Education", "CIV", True),
    ("Computer Studies", "CMP", False),
    ("Agricultural Science", "AGR", False),
    ("Business Studies", "BUS", False),
    ("Islamic Religious Studies", "IRS", False),
)

DEPARTMENT_NAMES = (
    "Sciences",
    "Humanities",
    "Languages",
    "Administration",
)

TEACHER_FIRST_NAMES = (
    "Amina", "David", "Fatima", "Michael", "Zainab",
)
TEACHER_LAST_NAMES = (
    "Adeyemi", "Okafor", "Ibrahim", "Johnson", "Balogun",
)


class Command(BaseCommand):
    help = (
        "Seed only demo subjects, departments, teachers, class-subject "
        "links, and teacher-subject assignments."
    )

    def add_arguments(self, parser):
        parser.add_argument("--teachers-per-school", type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        teachers_per_school = max(2, min(options["teachers_per_school"], 30))

        schools = School.objects.filter(
            short_name__in=DEMO_SCHOOL_CODES,
        ).order_by("short_name")

        processed = 0
        subjects_created = 0
        class_subjects_created = 0
        departments_created = 0
        teachers_created = 0
        teacher_subjects_created = 0

        for school in schools:
            processed += 1

            classes = list(
                SchoolClass.objects.filter(school=school).order_by("id")
            )
            if len(classes) != 14:
                self.stdout.write(
                    self.style.ERROR(
                        f"{school.short_name}: expected 14 classes; "
                        f"found {len(classes)}. Run seed_demo_academics first."
                    )
                )
                raise SystemExit(1)

            subjects = []
            for name, code, is_core in SUBJECT_SPECS:
                subject, created = Subject.objects.get_or_create(
                    code=f"{school.short_name}-{code}",
                    defaults={
                        "school": school,
                        "name": name,
                        "is_core": is_core,
                    },
                )
                if subject.school_id != school.id:
                    raise ValueError(
                        f"Subject {subject.code} belongs to another school."
                    )

                changed = []
                if subject.name != name:
                    subject.name = name
                    changed.append("name")
                if subject.is_core != is_core:
                    subject.is_core = is_core
                    changed.append("is_core")
                if changed:
                    subject.save(update_fields=changed)

                subjects.append(subject)
                subjects_created += int(created)

            for school_class in classes:
                for subject in subjects:
                    _, created = ClassSubject.objects.get_or_create(
                        school_class=school_class,
                        subject=subject,
                    )
                    class_subjects_created += int(created)

            departments = []
            for department_name in DEPARTMENT_NAMES:
                name = f"{school.short_name} {department_name}"
                department, created = Department.objects.get_or_create(
                    school=school,
                    name=name,
                )
                departments.append(department)
                departments_created += int(created)

            teachers = []
            for teacher_no in range(1, teachers_per_school + 1):
                teacher, created = Teacher.objects.get_or_create(
                    employee_id=f"{school.short_name}-T{teacher_no:03d}",
                    defaults={
                        "school": school,
                        "first_name": TEACHER_FIRST_NAMES[
                            (teacher_no - 1) % len(TEACHER_FIRST_NAMES)
                        ],
                        "last_name": TEACHER_LAST_NAMES[
                            (teacher_no - 1) % len(TEACHER_LAST_NAMES)
                        ],
                        "gender": "F" if teacher_no % 2 else "M",
                        "phone": f"081800{teacher_no:03d}",
                        "email": (
                            f"teacher{teacher_no}."
                            f"{school.short_name.lower()}@edutrack-demo.test"
                        ),
                        "qualification": "B.Ed. Education",
                        "department": departments[
                            (teacher_no - 1) % len(departments)
                        ],
                        "employment_status": "FULL_TIME",
                        "date_employed": date(2023, 9, 1),
                        "is_class_teacher": teacher_no <= 3,
                    },
                )

                if teacher.school_id != school.id:
                    raise ValueError(
                        f"Teacher {teacher.employee_id} belongs to another school."
                    )

                teachers.append(teacher)
                teachers_created += int(created)

            # Reconcile demo teacher metadata without overwriting a real
            # school's unrelated records.
            for teacher_no, teacher in enumerate(teachers, start=1):
                desired_department = departments[
                    (teacher_no - 1) % len(departments)
                ]
                updates = {}
                if teacher.department_id != desired_department.id:
                    updates["department"] = desired_department
                if teacher.is_class_teacher != (teacher_no <= 3):
                    updates["is_class_teacher"] = teacher_no <= 3
                if teacher.employment_status != "FULL_TIME":
                    updates["employment_status"] = "FULL_TIME"
                if updates:
                    for field, value in updates.items():
                        setattr(teacher, field, value)
                    teacher.save(update_fields=list(updates))

            # Give each demo teacher four subjects on one class. This keeps
            # the dataset useful without creating an unnecessarily huge
            # teaching allocation matrix.
            for teacher_no, teacher in enumerate(teachers):
                school_class = classes[teacher_no % len(classes)]
                for subject in subjects[:4]:
                    _, created = TeacherSubject.objects.get_or_create(
                        teacher=teacher,
                        subject=subject,
                        school_class=school_class,
                    )
                    teacher_subjects_created += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo subjects & teaching stage complete: "
                f"{processed} schools processed."
            )
        )
        self.stdout.write(
            "Created this run: "
            f"{subjects_created} subjects, "
            f"{class_subjects_created} class-subject links, "
            f"{departments_created} departments, "
            f"{teachers_created} teachers, "
            f"{teacher_subjects_created} teacher-subject assignments."
        )
        self.stdout.write(
            "Totals: "
            f"{Subject.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} subjects | "
            f"{ClassSubject.objects.filter(school_class__school__short_name__in=DEMO_SCHOOL_CODES).count()} class-subject links | "
            f"{Teacher.objects.filter(school__short_name__in=DEMO_SCHOOL_CODES).count()} teachers | "
            f"{TeacherSubject.objects.filter(teacher__school__short_name__in=DEMO_SCHOOL_CODES).count()} teaching assignments"
        )
