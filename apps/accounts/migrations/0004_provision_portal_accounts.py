from django.contrib.auth.hashers import make_password
from django.db import migrations


DEFAULT_PASSWORD = "12345"


def provision_account(User, UserProfile, Role, *, username, first_name, last_name, email, school, role_code, is_active, employee_id=""):
    user = User.objects.filter(username=str(username)).first()

    if user is not None:
        profile = UserProfile.objects.filter(user=user).select_related("role").first()
        if profile and profile.role and profile.role.code != role_code:
            return False
    else:
        user = User(
            username=str(username),
            first_name=first_name,
            last_name=last_name,
            email=email or "",
            is_active=is_active,
            password=make_password(DEFAULT_PASSWORD),
        )
        user.save()
        profile = UserProfile.objects.get(user=user)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email or ""
    user.is_active = is_active
    user.password = make_password(DEFAULT_PASSWORD)
    user.save(update_fields=["first_name", "last_name", "email", "is_active", "password"])

    profile.school = school
    profile.role = Role.objects.get(code=role_code)
    if employee_id:
        profile.employee_id = employee_id
    profile.save()
    return True


def provision_portal_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")
    Role = apps.get_model("accounts", "Role")
    Student = apps.get_model("students", "Student")
    Parent = apps.get_model("students", "Parent")
    Teacher = apps.get_model("teachers", "Teacher")

    for student in Student.objects.select_related("school"):
        provision_account(
            User,
            UserProfile,
            Role,
            username=student.admission_number,
            first_name=student.first_name,
            last_name=student.last_name,
            email="",
            school=student.school,
            role_code="STUDENT",
            is_active=student.is_active and student.status == "ACTIVE",
        )

    for parent in Parent.objects.select_related("school"):
        provision_account(
            User,
            UserProfile,
            Role,
            username=parent.pk,
            first_name=parent.first_name,
            last_name=parent.last_name,
            email=parent.email,
            school=parent.school,
            role_code="PARENT",
            is_active=parent.is_active,
        )

    for teacher in Teacher.objects.select_related("school"):
        provision_account(
            User,
            UserProfile,
            Role,
            username=teacher.employee_id,
            first_name=teacher.first_name,
            last_name=teacher.last_name,
            email=teacher.email,
            school=teacher.school,
            role_code="TEACHER",
            is_active=teacher.is_active,
            employee_id=teacher.employee_id,
        )


def reverse_provision_portal_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")

    portal_roles = {"STUDENT", "PARENT", "TEACHER"}
    usernames = set()
    for profile in UserProfile.objects.select_related("role"):
        if profile.role and profile.role.code in portal_roles:
            usernames.add(profile.user.username)

    User.objects.filter(username__in=usernames).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_seed_default_roles"),
        ("students", "0013_student_current_term"),
        ("teachers", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            provision_portal_accounts,
            reverse_code=reverse_provision_portal_accounts,
        ),
    ]
