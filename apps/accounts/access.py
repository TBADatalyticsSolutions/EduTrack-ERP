from apps.students.models import Parent, Student
from apps.teachers.models import Teacher, TeacherSubject


def role_code(user):
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None)
    return getattr(role, "code", None)


def student_for_user(user):
    if role_code(user) != "STUDENT":
        return None
    return (
        Student.objects.select_related(
            "school", "current_class", "current_session", "current_term"
        )
        .filter(admission_number=user.username)
        .first()
    )


def parent_for_user(user):
    if role_code(user) != "PARENT":
        return None
    profile = getattr(user, "profile", None)
    school = getattr(profile, "school", None)
    if not school:
        return None

    candidates = Parent.objects.filter(school=school)
    email = (getattr(user, "email", "") or "").strip()
    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()

    if email:
        parent = candidates.filter(email__iexact=email).order_by("created_at", "id").first()
        if parent:
            return parent

    return candidates.filter(
        first_name__iexact=first_name,
        last_name__iexact=last_name,
    ).order_by("created_at", "id").first()


def parent_students(user):
    parent = parent_for_user(user)
    if not parent:
        return Student.objects.none()
    return parent.students.select_related(
        "school", "current_class", "current_session", "current_term"
    ).filter(school=parent.school)


def teacher_for_user(user):
    if role_code(user) != "TEACHER":
        return None
    profile = getattr(user, "profile", None)
    employee_id = getattr(profile, "employee_id", "") or user.username
    return Teacher.objects.filter(
        employee_id=employee_id,
        school=getattr(profile, "school", None),
    ).first()


def teacher_class_ids(user):
    teacher = teacher_for_user(user)
    if not teacher:
        return []
    return list(
        TeacherSubject.objects.filter(
            teacher=teacher,
            school_class__school=teacher.school,
        ).values_list("school_class_id", flat=True).distinct()
    )


def teacher_can_access_class(user, school_class):
    if role_code(user) != "TEACHER":
        return False
    return (
        school_class is not None
        and school_class.school_id == getattr(getattr(user, "profile", None), "school_id", None)
        and school_class.pk in teacher_class_ids(user)
    )


def teacher_can_access_student(user, student):
    if not student or not student.current_class_id:
        return False
    return (
        student.school_id == getattr(getattr(user, "profile", None), "school_id", None)
        and student.current_class_id in teacher_class_ids(user)
    )
