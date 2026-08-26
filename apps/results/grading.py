from .models import GradeSetting


def calculate_grade(school, score):
    """
    Return grade and remark based on the school's grading system.
    """

    grade = GradeSetting.objects.filter(
        school=school,
        minimum_score__lte=score,
        maximum_score__gte=score,
    ).first()

    if grade:
        return grade.grade, grade.remark

    return "F", "No Grade"
