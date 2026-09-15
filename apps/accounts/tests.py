from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import AcademicSession, ClassSubject, SchoolClass, Subject, Term
from apps.attendance.models import AttendanceSession
from apps.finance.models import FeeCategory, InvoiceItem, Payment, StudentInvoice
from apps.results.models import StudentResult
from apps.schools.models import School
from apps.students.models import Parent, Student
from apps.teachers.models import Teacher, TeacherSubject

from .access import (
    parent_for_user,
    parent_students,
    student_for_user,
    teacher_can_access_class,
    teacher_can_access_student,
    teacher_class_ids,
)
from .models import ParentPortalLink, Role, UserProfile


class AccessControlRegressionTests(TestCase):
    """Regression tests for student, parent, teacher, and school isolation."""

    def setUp(self):
        self.User = get_user_model()

        self.school = School.objects.create(
            name="Access Control School",
            short_name="ACS",
            email="access@example.com",
            is_active=True,
        )
        self.other_school = School.objects.create(
            name="Other School",
            short_name="OTS",
            email="other@example.com",
            is_active=True,
        )

        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            is_current=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            session=self.session,
            name="First Term",
            is_current=True,
        )
        self.other_session = AcademicSession.objects.create(
            school=self.other_school,
            name="2026/2027",
            is_current=True,
        )
        self.other_term = Term.objects.create(
            school=self.other_school,
            session=self.other_session,
            name="First Term",
            is_current=True,
        )

        self.class_a = SchoolClass.objects.create(
            school=self.school,
            name="Primary 4 Access",
        )
        self.class_b = SchoolClass.objects.create(
            school=self.school,
            name="Primary 5 Access",
        )
        self.other_class = SchoolClass.objects.create(
            school=self.other_school,
            name="Primary 4 Other",
        )

        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathematics Access",
            code="MATH-ACCESS",
        )
        ClassSubject.objects.create(
            school_class=self.class_a,
            subject=self.subject,
        )
        ClassSubject.objects.create(
            school_class=self.class_b,
            subject=self.subject,
        )

        self.student_a = Student.objects.create(
            school=self.school,
            admission_number="ACS/2026/0001",
            first_name="Own",
            last_name="Student",
            gender="M",
            date_of_birth=date(2014, 1, 1),
            current_class=self.class_a,
            current_session=self.session,
            current_term=self.term,
        )
        self.student_b = Student.objects.create(
            school=self.school,
            admission_number="ACS/2026/0002",
            first_name="Other",
            last_name="Student",
            gender="F",
            date_of_birth=date(2014, 2, 1),
            current_class=self.class_b,
            current_session=self.session,
            current_term=self.term,
        )
        self.other_school_student = Student.objects.create(
            school=self.other_school,
            admission_number="OTS/2026/0001",
            first_name="Outside",
            last_name="Student",
            gender="F",
            date_of_birth=date(2014, 3, 1),
            current_class=self.other_class,
            current_session=self.other_session,
            current_term=self.other_term,
        )

        self.student_user = self.User.objects.get(
            username=self.student_a.admission_number,
        )
        self.student_b_user = self.User.objects.get(
            username=self.student_b.admission_number,
        )
        self.other_school_student_user = self.User.objects.get(
            username=self.other_school_student.admission_number,
        )

        self.parent = Parent.objects.create(
            school=self.school,
            first_name="Own",
            last_name="Parent",
            phone="08000000001",
            email="own.parent@example.com",
        )
        self.parent.students.add(self.student_a)
        self.parent_user = ParentPortalLink.objects.get(
            parent=self.parent,
        ).user

        self.other_parent = Parent.objects.create(
            school=self.school,
            first_name="Other",
            last_name="Parent",
            phone="08000000002",
            email="other.parent@example.com",
        )
        self.other_parent.students.add(self.student_b)
        self.other_parent_user = ParentPortalLink.objects.get(
            parent=self.other_parent,
        ).user

        self.teacher = Teacher.objects.create(
            school=self.school,
            employee_id="TCH-ACCESS-01",
            first_name="Assigned",
            last_name="Teacher",
            gender="M",
            phone="08000000003",
        )
        self.teacher_user = self.User.objects.get(username=self.teacher.employee_id)
        TeacherSubject.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            school_class=self.class_a,
        )

        self.other_teacher = Teacher.objects.create(
            school=self.school,
            employee_id="TCH-ACCESS-02",
            first_name="Second",
            last_name="Teacher",
            gender="F",
            phone="08000000004",
        )
        self.other_teacher_user = self.User.objects.get(
            username=self.other_teacher.employee_id,
        )
        TeacherSubject.objects.create(
            teacher=self.other_teacher,
            subject=self.subject,
            school_class=self.class_b,
        )

        self._set_role(self.student_user, "STUDENT")
        self._set_role(self.student_b_user, "STUDENT")
        self._set_role(self.other_school_student_user, "STUDENT")
        self._set_role(self.parent_user, "PARENT")
        self._set_role(self.other_parent_user, "PARENT")
        self._set_role(
            self.teacher_user,
            "TEACHER",
            employee_id=self.teacher.employee_id,
        )
        self._set_role(
            self.other_teacher_user,
            "TEACHER",
            employee_id=self.other_teacher.employee_id,
        )

        self.result_a = StudentResult.objects.create(
            school=self.school,
            student=self.student_a,
            session=self.session,
            term=self.term,
            school_class=self.class_a,
            published=True,
        )
        self.result_b = StudentResult.objects.create(
            school=self.school,
            student=self.student_b,
            session=self.session,
            term=self.term,
            school_class=self.class_b,
            published=True,
        )

        self.attendance_a = AttendanceSession.objects.create(
            school=self.school,
            school_class=self.class_a,
            academic_session=self.session,
            term=self.term,
            attendance_date=date(2026, 9, 1),
        )
        self.attendance_b = AttendanceSession.objects.create(
            school=self.school,
            school_class=self.class_b,
            academic_session=self.session,
            term=self.term,
            attendance_date=date(2026, 9, 2),
        )

        self.fee_category = FeeCategory.objects.create(
            school=self.school,
            name="Tuition Access",
        )
        self.invoice_a = StudentInvoice.objects.create(
            school=self.school,
            student=self.student_a,
            session=self.session,
            term=self.term,
            total_amount=50000,
            balance=50000,
        )
        self.invoice_b = StudentInvoice.objects.create(
            school=self.school,
            student=self.student_b,
            session=self.session,
            term=self.term,
            total_amount=60000,
            balance=60000,
        )
        InvoiceItem.objects.create(
            invoice=self.invoice_a,
            fee_category=self.fee_category,
            description="Tuition",
            amount=50000,
        )
        InvoiceItem.objects.create(
            invoice=self.invoice_b,
            fee_category=self.fee_category,
            description="Tuition",
            amount=60000,
        )
        self.payment_a = Payment.objects.create(
            invoice=self.invoice_a,
            amount=10000,
            settlement_type="PAYMENT",
            payment_method="CASH",
        )

    def _set_role(self, user, code, employee_id=""):
        role, _ = Role.objects.get_or_create(
            code=code,
            defaults={"name": code.replace("_", " ").title()},
        )
        profile = UserProfile.objects.get(user=user)
        profile.school = self.school
        profile.role = role
        profile.employee_id = employee_id
        profile.save()

    def test_student_access_is_bound_to_authenticated_account(self):
        self.assertEqual(student_for_user(self.student_user), self.student_a)
        self.assertNotEqual(student_for_user(self.student_b_user), self.student_a)
        self.assertEqual(
            student_for_user(self.other_school_student_user),
            self.other_school_student,
        )

    def test_student_portal_shows_only_own_records(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("portal-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_a.admission_number)
        self.assertContains(response, self.invoice_a.invoice_number)
        self.assertContains(response, self.result_a.student.full_name())
        self.assertNotContains(response, self.student_b.admission_number)
        self.assertNotContains(response, self.invoice_b.invoice_number)
        self.assertNotContains(response, self.result_b.student.full_name())

    def test_parent_access_is_bound_to_explicit_portal_link(self):
        self.assertEqual(parent_for_user(self.parent_user), self.parent)
        self.assertQuerySetEqual(
            parent_students(self.parent_user),
            [self.student_a],
            transform=lambda student: student,
        )
        self.assertNotIn(self.student_b, parent_students(self.parent_user))

    def test_parent_portal_shows_only_linked_child_records(self):
        self.client.force_login(self.parent_user)
        response = self.client.get(reverse("portal-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_a.admission_number)
        self.assertContains(response, self.invoice_a.invoice_number)
        self.assertContains(response, self.result_a.student.full_name())
        self.assertNotContains(response, self.student_b.admission_number)
        self.assertNotContains(response, self.invoice_b.invoice_number)
        self.assertNotContains(response, self.result_b.student.full_name())

    def test_parent_cannot_claim_another_parent_by_matching_name(self):
        self.parent_user.first_name = self.other_parent.first_name
        self.parent_user.last_name = self.other_parent.last_name
        self.parent_user.email = self.other_parent.email
        self.parent_user.save(
            update_fields=["first_name", "last_name", "email"],
        )
        self.assertEqual(parent_for_user(self.parent_user), self.parent)
        self.assertNotIn(self.student_b, parent_students(self.parent_user))

    def test_teacher_class_scope_contains_only_assigned_class(self):
        self.assertEqual(teacher_class_ids(self.teacher_user), [self.class_a.pk])
        self.assertTrue(teacher_can_access_class(self.teacher_user, self.class_a))
        self.assertFalse(teacher_can_access_class(self.teacher_user, self.class_b))
        self.assertTrue(teacher_can_access_student(self.teacher_user, self.student_a))
        self.assertFalse(teacher_can_access_student(self.teacher_user, self.student_b))
        self.assertFalse(
            teacher_can_access_student(self.teacher_user, self.other_school_student)
        )

    def test_teacher_results_are_scoped_to_assigned_class(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("results:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_a.admission_number)
        self.assertNotContains(response, self.student_b.admission_number)

    def test_teacher_cannot_open_result_for_unassigned_class(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(
            reverse("results:detail", args=[self.result_b.pk]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("results:list"))

    def test_teacher_attendance_dashboard_is_scoped_to_assigned_class(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("attendance-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.attendance_a.school_class.name)
        self.assertNotContains(response, self.attendance_b.school_class.name)

    def test_teacher_cannot_open_attendance_for_unassigned_class(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(
            reverse("attendance-session", args=[self.attendance_b.pk]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("attendance-dashboard"))

    def test_teacher_cannot_use_student_management_mutation_routes(self):
        self.client.force_login(self.teacher_user)
        restricted_routes = (
            ("student-enrol", {}),
            ("student-promote", {"args": [self.student_a.pk]}),
            ("graduate-student", {"args": [self.student_a.pk]}),
            ("transfer-student", {"args": [self.student_a.pk]}),
        )

        for route_name, options in restricted_routes:
            response = self.client.get(reverse(route_name, **options))
            self.assertEqual(response.status_code, 302, route_name)

    def test_student_and_parent_roles_cannot_enter_staff_results(self):
        self.client.force_login(self.student_user)
        student_response = self.client.get(reverse("results:list"))
        self.assertEqual(student_response.status_code, 302)

        self.client.force_login(self.parent_user)
        parent_response = self.client.get(reverse("results:list"))
        self.assertEqual(parent_response.status_code, 302)

    def test_student_and_parent_roles_cannot_enter_staff_attendance(self):
        self.client.force_login(self.student_user)
        student_response = self.client.get(reverse("attendance-dashboard"))
        self.assertEqual(student_response.status_code, 302)

        self.client.force_login(self.parent_user)
        parent_response = self.client.get(reverse("attendance-dashboard"))
        self.assertEqual(parent_response.status_code, 302)

    def test_student_portal_payment_belongs_to_own_invoice(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("portal-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment_a.amount))
        self.assertNotContains(response, str(self.invoice_b.total_amount))
