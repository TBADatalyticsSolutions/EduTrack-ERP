from apps.students.models import Student


class AttendanceService:

    @staticmethod
    def students_for_class(school_class):

        return Student.objects.filter(
            current_class=school_class
        ).order_by(
            "last_name",
            "first_name",
        )