from .models import StudentResult


def calculate_positions(school, session, term, school_class):
    """
    Calculate class positions using competition ranking.
    Example:
        95 -> 1st
        90 -> 2nd
        90 -> 2nd
        85 -> 4th
    """

    results = (
        StudentResult.objects.filter(
            school=school,
            session=session,
            term=term,
            school_class=school_class,
        )
        .order_by("-average", "student__last_name")
    )

    previous_average = None
    current_position = 0

    for index, result in enumerate(results, start=1):

        if previous_average is None:
            current_position = 1

        elif result.average != previous_average:
            current_position = index

        result.position = current_position
        result.save(update_fields=["position"])

        previous_average = result.average