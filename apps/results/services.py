from decimal import Decimal

from .grading import calculate_grade
from .models import SubjectResult
from .position import calculate_positions


def calculate_subject_result(subject_result):
    """
    Calculate total, grade, and remark for a single subject.
    """

    total = (
        subject_result.ca1
        + subject_result.ca2
        + subject_result.assignment
        + subject_result.project
        + subject_result.examination
    )

    subject_result.total = total

    grade, remark = calculate_grade(
        subject_result.student_result.school,
        total,
    )

    subject_result.grade = grade
    subject_result.remark = remark

    subject_result.save(update_fields=[
        "total",
        "grade",
        "remark",
    ])

    return subject_result


def calculate_student_result(student_result):
    """
    Calculate overall student total and average.
    """

    subjects = SubjectResult.objects.filter(
        student_result=student_result
    )

    overall = Decimal("0.00")

    for subject in subjects:
        calculate_subject_result(subject)
        overall += subject.total

    subject_count = subjects.count()

    if subject_count > 0:
        student_result.total_score = overall
        student_result.average = overall / subject_count
    else:
        student_result.total_score = Decimal("0.00")
        student_result.average = Decimal("0.00")

    student_result.save(update_fields=[
        "total_score",
        "average",
    ])

    calculate_positions(
        student_result.school,
        student_result.session,
        student_result.term,
        student_result.school_class,
    )

    return student_result