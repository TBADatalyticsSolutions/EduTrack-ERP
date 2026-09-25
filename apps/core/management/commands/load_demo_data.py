from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ParentPortalLink, Role
from apps.academics.models import AcademicSession, ClassArm, ClassSubject, SchoolClass, Subject, Term
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.finance.models import FeeCategory, FeeStructure, InvoiceItem, Payment, StudentInvoice
from apps.notifications.models import Notification
from apps.results.models import AssessmentType, GradeSetting, StudentResult, SubjectResult
from apps.schools.models import School, SchoolSubscription
from apps.students.models import Parent, Student, PromotionHistory, TransferHistory
from apps.teachers.models import Department, Teacher, TeacherSubject


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Load deterministic synthetic demo data for client testing. "
        "Creates AFAAB plus nine additional demo schools by default."
    )

    def add_arguments(self, parser):
        parser.add_argument("--schools", type=int, default=10)
        parser.add_argument("--students-per-school", type=int, default=12)
        parser.add_argument("--teachers-per-school", type=int, default=5)
        parser.add_argument("--reset", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        school_count = max(1, min(options["schools"], 50))
        students_per_school = max(2, min(options["students_per_school"], 100))
        teachers_per_school = max(2, min(options["teachers_per_school"], 30))

        self._ensure_roles()

        if options["reset"]:
            self._reset_demo_data()

        schools = self._schools(school_count)
        for index, school_data in enumerate(schools, start=1):
            school = self._school(school_data, index)
            self._populate_school(
                school,
                index,
                students_per_school,
                teachers_per_school,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data loaded: {len(schools)} schools, "
                f"{students_per_school} students/school, "
                f"{teachers_per_school} teachers/school."
            )
        )
        self.stdout.write(
            "Synthetic demo credentials use password: Demo@2026!"
        )

    def _ensure_roles(self):
        for code, name in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": name})

    def _schools(self, count):
        names = [
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
        ]
        return names[:count]

    def _school(self, data, index):
        name, short_name, motto = data
        school = School.objects.filter(short_name=short_name).first()
        if school is None:
            school, _ = School.objects.get_or_create(
                email=f"demo{index}@edutrack-demo.test",
                defaults={
                    "name": name,
                    "short_name": short_name,
                    "motto": motto,
                    "phone": f"0809000{index:04d}",
                    "address": f"{index} Demo Education Avenue, Abeokuta, Ogun State",
                    "website": f"https://{short_name.lower()}.demo.edutrack.test",
                },
            )
        changed = False
        for field, value in {
            "name": name,
            "short_name": short_name,
            "motto": motto,
        }.items():
            if getattr(school, field) != value:
                setattr(school, field, value)
                changed = True
        if changed:
            school.save(update_fields=["name", "short_name", "motto"])

        SchoolSubscription.objects.get_or_create(
            school=school,
            defaults={
                "plan": "PREMIUM" if index % 3 == 0 else "STANDARD",
                "status": "ACTIVE",
                "started_at": date(2026, 1, 5),
            },
        )
        return school

    def _populate_school(self, school, index, students_per_school, teachers_per_school):
        session_2526, _ = AcademicSession.objects.get_or_create(
            school=school, name="2025/2026",
            defaults={"is_current": False},
        )
        session_2627, _ = AcademicSession.objects.get_or_create(
            school=school, name="2026/2027",
            defaults={"is_current": True},
        )
        AcademicSession.objects.filter(school=school).exclude(pk=session_2627.pk).update(is_current=False)
        session_2627.is_current = True
        session_2627.save(update_fields=["is_current"])

        terms = {}
        for session in (session_2526, session_2627):
            for term_name, month in (("First Term", 9), ("Second Term", 1), ("Third Term", 4)):
                term, _ = Term.objects.get_or_create(
                    school=school,
                    session=session,
                    name=term_name,
                    defaults={
                        "is_current": session == session_2627 and term_name == "First Term",
                        "resumption_date": date(
                            2026 if session == session_2627 and month >= 9 else 2027 if session == session_2627 and month < 9 else 2025 if month >= 9 else 2026,
                            month,
                            8,
                        ),
                    },
                )
                terms[(session.pk, term_name)] = term
        Term.objects.filter(school=school).update(is_current=False)
        terms[(session_2627.pk, "First Term")].is_current = True
        terms[(session_2627.pk, "First Term")].save(update_fields=["is_current"])

        classes = []
        for class_name in ["Nursery 1", "Nursery 2", "Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5", "Primary 6", "JSS 1", "JSS 2", "JSS 3", "SS 1", "SS 2", "SS 3"]:
            school_class, _ = SchoolClass.objects.get_or_create(school=school, name=class_name)
            classes.append(school_class)
            for arm in ["A", "B"]:
                ClassArm.objects.get_or_create(school=school, school_class=school_class, name=arm)

        subject_specs = [
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
        ]
        subjects = []
        for name, code, core in subject_specs:
            subject, _ = Subject.objects.get_or_create(
                code=f"{school.short_name}-{code}",
                defaults={"school": school, "name": name, "is_core": core},
            )
            subjects.append(subject)
            for school_class in classes:
                ClassSubject.objects.get_or_create(school_class=school_class, subject=subject)

        departments = []
        for department_name in ["Sciences", "Humanities", "Languages", "Administration"]:
            department, _ = Department.objects.get_or_create(
                school=school,
                name=f"{school.short_name} {department_name}",
            )
            departments.append(department)

        teachers = []
        for teacher_no in range(1, teachers_per_school + 1):
            teacher, _ = Teacher.objects.get_or_create(
                employee_id=f"{school.short_name}-T{teacher_no:03d}",
                defaults={
                    "school": school,
                    "first_name": ["Amina", "David", "Fatima", "Michael", "Zainab", "Daniel"][teacher_no % 6],
                    "last_name": ["Adeyemi", "Okafor", "Ibrahim", "Johnson", "Balogun", "Yusuf"][teacher_no % 6],
                    "gender": "F" if teacher_no % 2 else "M",
                    "phone": f"081800{index:02d}{teacher_no:03d}",
                    "email": f"teacher{teacher_no}.{school.short_name.lower()}@edutrack-demo.test",
                    "qualification": "B.Ed. Education",
                    "department": departments[(teacher_no - 1) % len(departments)],
                    "employment_status": "FULL_TIME",
                    "date_employed": date(2023, 9, 1),
                    "is_class_teacher": teacher_no <= 3,
                },
            )
            teachers.append(teacher)

        for teacher_no, teacher in enumerate(teachers):
            for subject in subjects[:4]:
                TeacherSubject.objects.get_or_create(
                    teacher=teacher,
                    subject=subject,
                    school_class=classes[teacher_no % len(classes)],
                )

        assessment_specs = [("CA 1", 20, 1), ("CA 2", 20, 2), ("Assignment", 10, 3), ("Project", 10, 4), ("Examination", 40, 5)]
        for name, maximum, order in assessment_specs:
            AssessmentType.objects.get_or_create(
                school=school,
                name=name,
                defaults={"maximum_score": maximum, "order": order},
            )
        for grade, minimum, maximum, remark in [
            ("A", 70, 100, "Excellent"),
            ("B", 60, 69, "Very Good"),
            ("C", 50, 59, "Good"),
            ("D", 45, 49, "Fair"),
            ("E", 40, 44, "Pass"),
            ("F", 0, 39, "Fail"),
        ]:
            GradeSetting.objects.get_or_create(
                school=school,
                grade=grade,
                defaults={"minimum_score": minimum, "maximum_score": maximum, "remark": remark},
            )

        fee_specs = [
            ("Tuition", Decimal("21000.00")),
            ("Development Levy", Decimal("5000.00")),
            ("ICT/Technology", Decimal("3000.00")),
            ("Activities", Decimal("5000.00")),
            ("Examination", Decimal("2500.00")),
        ]
        fee_categories = []
        for name, amount in fee_specs:
            category, _ = FeeCategory.objects.get_or_create(school=school, name=name)
            fee_categories.append((category, amount))

        current_term = terms[(session_2627.pk, "First Term")]
        for school_class in classes:
            for category, amount in fee_categories:
                FeeStructure.objects.get_or_create(
                    school=school,
                    session=session_2627,
                    term=current_term,
                    school_class=school_class,
                    fee_category=category,
                    defaults={"amount": amount},
                )

        students = []
        first_names = ["Zainab", "Zaynul", "Aisha", "Abdullah", "Maryam", "Ibrahim", "Hannah", "Samuel", "Fatimah", "Yusuf", "Daniel", "Safiyyah"]
        last_names = ["Adekunle", "Balogun", "Ibrahim", "Okafor", "Yusuf", "Adebayo"]
        for student_no in range(1, students_per_school + 1):
            student, _ = Student.objects.get_or_create(
                admission_number=f"{school.short_name}/2026/{student_no:04d}",
                defaults={
                    "school": school,
                    "first_name": first_names[(student_no - 1) % len(first_names)],
                    "last_name": last_names[(student_no - 1) % len(last_names)],
                    "other_name": "Demo",
                    "gender": "F" if student_no % 2 else "M",
                    "date_of_birth": date(2012 + (student_no % 5), 2 + (student_no % 10), 5 + (student_no % 20)),
                    "admission_date": date(2026, 9, 1),
                    "current_class": classes[student_no % len(classes)],
                    "current_session": session_2627,
                    "current_term": current_term,
                    "status": "ACTIVE",
                },
            )
            students.append(student)

        parents = []
        for parent_no in range(0, students_per_school, 2):
            parent, _ = Parent.objects.get_or_create(
                school=school,
                first_name=["Kareem", "Mariam", "Abdul", "Aisha"][parent_no % 4],
                last_name=f"DemoFamily{parent_no // 2 + 1}",
                defaults={
                    "phone": f"080700{index:02d}{parent_no:02d}",
                    "email": f"parent{parent_no // 2 + 1}.{school.short_name.lower()}@edutrack-demo.test",
                    "address": f"Demo Estate, {school.short_name}",
                },
            )
            parent.students.add(*students[parent_no:parent_no + 2])
            parents.append(parent)
            username = f"parent{index}_{parent_no // 2 + 1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": parent.first_name, "last_name": parent.last_name, "email": parent.email, "is_active": True},
            )
            user.set_password("Demo@2026!")
            user.save(update_fields=["password"])
            profile = user.profile
            profile.school = school
            profile.role = Role.objects.get(code="PARENT")
            profile.parent_id = f"{school.short_name}-P{parent_no // 2 + 1:03d}"
            profile.save(update_fields=["school", "role", "parent_id"])
            ParentPortalLink.objects.get_or_create(parent=parent, user=user)

        for student_no, student in enumerate(students):
            if student_no % 3 == 0:
                Student.objects.filter(pk=student.pk).update(status="ACTIVE")
            invoice, _ = StudentInvoice.objects.get_or_create(
                school=school,
                student=student,
                session=session_2627,
                term=current_term,
                defaults={
                    "invoice_number": f"INV-{index:02d}-2026-{student_no + 1:04d}",
                    "due_date": date(2026, 10, 15),
                    "total_amount": Decimal("0.00"),
                    "balance": Decimal("0.00"),
                },
            )
            total = Decimal("0.00")
            for category, amount in fee_categories:
                InvoiceItem.objects.get_or_create(
                    invoice=invoice,
                    fee_category=category,
                    defaults={
                        "description": category.name,
                        "amount": amount,
                        "due_date": invoice.due_date,
                    },
                )
                total += amount
            invoice.total_amount = total
            invoice.balance = total
            invoice.status = "UNPAID"
            invoice.save(update_fields=["total_amount", "balance", "status"])

            if student_no % 4 == 0:
                Payment.objects.get_or_create(
                    invoice=invoice,
                    reference=f"DEMO-{index:02d}-{student_no + 1:04d}",
                    defaults={
                        "amount": Decimal("25000.00"),
                        "settlement_type": "PAYMENT",
                        "payment_method": "TRANSFER",
                        "notes": "Synthetic demo payment.",
                    },
                )
            elif student_no % 4 == 1:
                Payment.objects.get_or_create(
                    invoice=invoice,
                    reference=f"DEMO-SCH-{index:02d}-{student_no + 1:04d}",
                    defaults={
                        "amount": Decimal("15000.00"),
                        "settlement_type": "SCHOLARSHIP",
                        "payment_method": "",
                        "notes": "Synthetic demo scholarship.",
                    },
                )

            result, _ = StudentResult.objects.get_or_create(
                school=school,
                student=student,
                session=session_2627,
                term=current_term,
                defaults={
                    "school_class": student.current_class,
                    "total_score": Decimal("0"),
                    "average": Decimal("0"),
                    "position": student_no + 1,
                    "teacher_remark": "Good progress.",
                    "principal_remark": "Keep improving.",
                    "promotion_status": "PROMOTED",
                    "next_term_resumption": date(2027, 1, 8),
                    "published": True,
                },
            )
            totals = []
            for subject_no, subject in enumerate(subjects[:6]):
                ca1 = Decimal(10 + ((student_no + subject_no) % 10))
                ca2 = Decimal(10 + ((student_no * 2 + subject_no) % 10))
                assignment = Decimal(5 + ((student_no + subject_no) % 6))
                project = Decimal(5 + ((student_no + subject_no * 2) % 6))
                examination = Decimal(25 + ((student_no * 3 + subject_no) % 16))
                total_score = ca1 + ca2 + assignment + project + examination
                grade = "A" if total_score >= 70 else "B" if total_score >= 60 else "C" if total_score >= 50 else "D" if total_score >= 45 else "E" if total_score >= 40 else "F"
                SubjectResult.objects.update_or_create(
                    student_result=result,
                    subject=subject,
                    defaults={
                        "ca1": ca1,
                        "ca2": ca2,
                        "assignment": assignment,
                        "project": project,
                        "examination": examination,
                        "total": total_score,
                        "grade": grade,
                        "remark": "Good",
                        "teacher_remark": "Synthetic demo result.",
                    },
                )
                totals.append(total_score)
            average = sum(totals) / len(totals)
            result.total_score = sum(totals)
            result.average = average
            result.save(update_fields=["total_score", "average"])

        attendance_date = date(2026, 9, 21)
        attendance_class = classes[2]
        attendance_session, _ = AttendanceSession.objects.get_or_create(
            school=school,
            school_class=attendance_class,
            academic_session=session_2627,
            term=current_term,
            attendance_date=attendance_date,
            defaults={"created_by": teachers[0].user if hasattr(teachers[0], "user") else None},
        )
        class_students = [s for s in students if s.current_class_id == attendance_class.pk]
        if not class_students:
            class_students = students[:4]
        for student_no, student in enumerate(class_students):
            AttendanceRecord.objects.get_or_create(
                attendance_session=attendance_session,
                student=student,
                defaults={
                    "status": ["PRESENT", "PRESENT", "LATE", "ABSENT"][student_no % 4],
                    "remarks": "Synthetic demo attendance.",
                },
            )

        if students:
            PromotionHistory.objects.get_or_create(
                student=students[0],
                school=school,
                academic_session=session_2526,
                term=terms[(session_2526.pk, "Third Term")],
                defaults={
                    "from_class": students[0].current_class,
                    "to_class": classes[min(classes.index(students[0].current_class) + 1, len(classes) - 1)],
                    "action": "PROMOTED",
                    "average_score": Decimal("72.50"),
                    "remarks": "Synthetic demo promotion.",
                },
            )
            TransferHistory.objects.get_or_create(
                student=students[1],
                school=school,
                from_class=students[1].current_class,
                to_class=students[1].current_class,
                from_session=session_2526,
                to_session=session_2627,
                defaults={"reason": "Academic progression", "remarks": "Synthetic demo transfer history."},
            )

        school_admin_role = Role.objects.get(code="SCHOOL_ADMIN")
        admin, _ = User.objects.get_or_create(
            username=f"admin_{school.short_name.lower()}",
            defaults={
                "first_name": "Demo",
                "last_name": "Administrator",
                "email": f"admin.{school.short_name.lower()}@edutrack-demo.test",
                "is_active": True,
            },
        )
        admin.set_password("Demo@2026!")
        admin.save(update_fields=["password"])
        profile = admin.profile
        profile.school = school
        profile.role = school_admin_role
        profile.is_school_admin = True
        profile.save(update_fields=["school", "role", "is_school_admin"])

        Notification.objects.get_or_create(
            school=school,
            recipient=admin,
            title="Welcome to EduTrack ERP Demo",
            defaults={
                "message": "This school contains synthetic data for client demonstration and testing.",
                "notification_type": "INFO",
            },
        )

        Notification.objects.get_or_create(
            school=school,
            recipient=admin,
            title="Finance Demo Ready",
            defaults={
                "message": "Sample invoices, payments, scholarships and balances are available.",
                "notification_type": "SUCCESS",
            },
        )
