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
    parent_id = getattr(profile, "parent_id", None)
    if not parent_id:
        return None

    number = None
    if parent_id.startswith("PAR"):
        try:
            number = int(parent_id[3:])
        except ValueError:
            return None

    if number is None:
        return None

    parents = Parent.objects.all().order_by("created_at", "id")
    return parents[number - 1] if number <= parents.count() else None


def parent_students(user):
    parent = parent_for_user(user)
    if not parent:
        return Student.objects.none()
    return parent.students.select_related(
        "school", "current_class", "current_session", "current_term"
    ).filter(school=getattr(getattr(user, "profile", None), "school", None))


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
        TeacherSubject.objects.filter(teacher=teacher)
        .values_list("school_class_id", flat=True)
        .distinct()
    )


def teacher_can_access_class(user, school_class):
    if role_code(user) != "TEACHER":
        return False
    return school_class is not None and school_class.pk in teacher_class_ids(user)


def teacher_can_access_student(user, student):
    if not student or not student.current_class_id:
        return False
    return student.current_class_id in teacher_class_ids(user)
