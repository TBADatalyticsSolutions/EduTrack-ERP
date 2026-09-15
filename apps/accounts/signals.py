from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Role, UserProfile


DEFAULT_PORTAL_PASSWORD = "12345"


def provision_portal_account(
    *,
    username,
    first_name,
    last_name,
    email="",
    school=None,
    role_code,
    employee_id="",
    reset_password=False,
):
    """Create or synchronize a portal account for a school user."""
    username = str(username).strip()
    if not username:
        return None

    role = Role.objects.get(code=role_code)
    user = User.objects.filter(username=username).first()

    if user is not None:
        profile = getattr(user, "profile", None)
        if profile and profile.role and profile.role.code != role_code:
            return None
    else:
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email or "",
            is_active=True,
        )
        user.set_password(DEFAULT_PORTAL_PASSWORD)
        user.save()
        profile = user.profile

    if reset_password:
        user.set_password(DEFAULT_PORTAL_PASSWORD)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email or ""
    if school is not None:
        user.is_active = bool(getattr(school, "is_active", True)) and bool(
            getattr(user, "is_active", True)
        )
    user.save(update_fields=["first_name", "last_name", "email", "is_active", "password"])

    profile.school = school
    profile.role = role
    if employee_id:
        profile.employee_id = employee_id
    profile.save()
    return user


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile for every new Django user."""
    if created and not hasattr(instance, "profile"):
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender="students.Student")
def provision_student_account(sender, instance, created, **kwargs):
    """Give every student an ID-based portal login."""
    provision_portal_account(
        username=instance.admission_number,
        first_name=instance.first_name,
        last_name=instance.last_name,
        school=instance.school,
        role_code="STUDENT",
    )


@receiver(post_save, sender="students.Parent")
def provision_parent_account(sender, instance, created, **kwargs):
    """Give every parent an ID-based portal login."""
    provision_portal_account(
        username=instance.pk,
        first_name=instance.first_name,
        last_name=instance.last_name,
        email=instance.email,
        school=instance.school,
        role_code="PARENT",
    )


@receiver(post_save, sender="teachers.Teacher")
def provision_teacher_account(sender, instance, created, **kwargs):
    """Give every teacher an employee-ID-based portal login."""
    provision_portal_account(
        username=instance.employee_id,
        first_name=instance.first_name,
        last_name=instance.last_name,
        email=instance.email,
        school=instance.school,
        role_code="TEACHER",
        employee_id=instance.employee_id,
    )
