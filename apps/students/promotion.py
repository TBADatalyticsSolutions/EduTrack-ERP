from django.db import transaction
from django.utils import timezone

from .models import (
    Student,
    GraduationHistory,
)

def graduate_class(school_class):
    """
    Graduate every student in a class.
    """

    students = Student.objects.filter(
        current_class=school_class,
        is_graduated=False,
    )

    count = 0

    for student in students:

        student.is_graduated = True
        student.current_class = None
        student.graduation_date = timezone.now().date()
        student.graduation_year = timezone.now().year

        student.save()

        GraduationHistory.objects.create(
            student=student,
            school=student.school,
            graduation_year=student.graduation_year,
            final_class=school_class,
            remarks="Bulk Graduation",
        )

        count += 1

    return count

@transaction.atomic
def promote_students(current_class, next_class):
    """
    Promote all students from one class to another.
    """

    students = Student.objects.filter(
        current_class=current_class,
        is_graduated=False,
    )

    total = students.count()

    students.update(
        current_class=next_class
    )

    return total


@transaction.atomic
def promote_student(student, next_class):
    """
    Promote one student.
    """

    student.current_class = next_class
    student.save()

    return student

def graduate_student(student, reason=""):

    student.is_graduated = True
    student.graduation_date = timezone.now().date()
    student.graduation_reason = reason
    student.save()

    return student