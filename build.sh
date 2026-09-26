#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

echo "==> Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Running Django deployment checks"
python manage.py check --deploy

echo "==> Verifying migration files"
python manage.py makemigrations --check --dry-run

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

# ==========================================================
# TEMPORARY DEMO DATA SEEDING
# Disabled by default. Set EDUTRACK_SEED_DEMO_DATA=True in
# Render only for the controlled demo-database initialization.
# Remove/unset the variable immediately after the deploy.
# ==========================================================
if [ "${EDUTRACK_SEED_DEMO_DATA:-False}" = "True" ]; then
  echo "==> TEMPORARY: Seeding EduTrack demo data"

  python manage.py seed_demo_schools
  python manage.py seed_demo_academics
  python manage.py seed_demo_subjects_teaching
  python manage.py seed_demo_academic_config
  python manage.py seed_demo_students_portal
  python manage.py seed_demo_finance
  python manage.py seed_demo_attendance
  python manage.py seed_demo_results
  python manage.py seed_demo_notifications

  echo "==> TEMPORARY: Verifying seeded demo data"

  python manage.py shell -c '
from apps.schools.models import School, SchoolSubscription
from apps.academics.models import AcademicSession, Term, SchoolClass, ClassArm, Subject, ClassSubject
from apps.teachers.models import Department, Teacher, TeacherSubject
from apps.academics.models import AssessmentType, GradeSetting
from apps.students.models import Student
from apps.accounts.models import UserProfile, ParentPortalLink
from apps.finance.models import StudentInvoice, InvoiceItem, Payment
from apps.attendance.models import AttendanceSession, AttendanceRecord
from apps.results.models import StudentResult, SubjectResult
from apps.notifications.models import Notification

expected = {
    "schools": 10,
    "subscriptions": 10,
    "sessions": 20,
    "terms": 60,
    "classes": 140,
    "class_arms": 280,
    "subjects": 100,
    "class_subjects": 1400,
    "departments": 40,
    "teachers": 50,
    "teacher_subjects": 200,
    "assessment_types": 30,
    "grade_settings": 60,
    "students": 120,
    "student_profiles": 120,
    "parent_profiles": 60,
    "parent_portal_links": 60,
    "invoices": 120,
    "invoice_items": 600,
    "payments": 100,
    "attendance_sessions": 600,
    "attendance_records": 600,
    "student_results": 120,
    "subject_results": 1200,
    "notifications": 380,
}

actual = {
    "schools": School.objects.count(),
    "subscriptions": SchoolSubscription.objects.count(),
    "sessions": AcademicSession.objects.count(),
    "terms": Term.objects.count(),
    "classes": SchoolClass.objects.count(),
    "class_arms": ClassArm.objects.count(),
    "subjects": Subject.objects.count(),
    "class_subjects": ClassSubject.objects.count(),
    "departments": Department.objects.count(),
    "teachers": Teacher.objects.count(),
    "teacher_subjects": TeacherSubject.objects.count(),
    "assessment_types": AssessmentType.objects.count(),
    "grade_settings": GradeSetting.objects.count(),
    "students": Student.objects.count(),
    "student_profiles": UserProfile.objects.filter(student__isnull=False).count(),
    "parent_profiles": UserProfile.objects.filter(parent__isnull=False).count(),
    "parent_portal_links": ParentPortalLink.objects.count(),
    "invoices": StudentInvoice.objects.count(),
    "invoice_items": InvoiceItem.objects.count(),
    "payments": Payment.objects.count(),
    "attendance_sessions": AttendanceSession.objects.count(),
    "attendance_records": AttendanceRecord.objects.count(),
    "student_results": StudentResult.objects.count(),
    "subject_results": SubjectResult.objects.count(),
    "notifications": Notification.objects.count(),
}

failures = {
    key: (expected[key], actual[key])
    for key in expected
    if actual[key] != expected[key]
}

print("==> DEMO DATA COUNTS")
for key in expected:
    print(f"{key}: {actual[key]} / expected {expected[key]}")

if failures:
    print("==> DEMO DATA VERIFICATION FAILED")
    for key, (want, got) in failures.items():
        print(f"  {key}: expected {want}, got {got}")
    raise SystemExit(1)

afaab = School.objects.get(short_name="AFAAB")
student = Student.objects.get(student_number="AFAAB/2026/0001", school=afaab)

invoice = StudentInvoice.objects.get(student=student)
result = StudentResult.objects.get(student=student)

print("==> AFAAB DETERMINISTIC CHECK")
print(f"invoice_total: {invoice.total_amount} / expected 28500")
print(f"invoice_balance: {invoice.balance} / expected 18500")
print(f"invoice_status: {invoice.status} / expected PARTIAL")
print(f"result_total: {result.total_score} / expected 749")
print(f"result_average: {result.average} / expected 74.90")
print(f"result_position: {result.position} / expected 1")

if (
    invoice.total_amount != 28500
    or invoice.balance != 18500
    or invoice.status != "PARTIAL"
    or result.total_score != 749
    or result.average != 74.90
    or result.position != 1
):
    raise SystemExit("==> AFAAB deterministic verification failed")

mat = result.subject_results.get(subject__code__endswith="-MAT")
print(f"MAT total: {mat.total_score} / expected 68")
print(f"MAT grade: {mat.grade} / expected B")
print(f"MAT remark: {mat.remark} / expected Very Good")

if mat.total_score != 68 or mat.grade != "B" or mat.remark != "Very Good":
    raise SystemExit("==> AFAAB Mathematics verification failed")

attendance_count = AttendanceRecord.objects.filter(student=student).count()
print(f"attendance_records: {attendance_count} / expected 5")

if attendance_count != 5:
    raise SystemExit("==> AFAAB attendance verification failed")

print("==> TEMPORARY DEMO SEED AND VERIFICATION PASSED")
'
fi

echo "==> Build completed successfully"
