from django.db.models import Count
from django.shortcuts import render

from .models import (

    Student,
    DisciplineHistory,
)


def discipline_dashboard(request):
    """
    Discipline Dashboard
    """

    students = Student.objects.all()

    suspensions = DisciplineHistory.objects.filter(
        action="SUSPENSION"
    )

    expulsions = DisciplineHistory.objects.filter(
        action="EXPULSION"
    )

    context = {

        # Student Statistics

        "total_students": students.count(),

        "active_students": students.filter(
            status="ACTIVE"
        ).count(),

        "suspended_students": students.filter(
            status="SUSPENDED"
        ).count(),

        "expelled_students": students.filter(
            status="EXPELLED"
        ).count(),

        # Discipline Records

        "total_suspensions": suspensions.count(),

        "active_suspensions": suspensions.filter(
            revoked=False
        ).count(),

        "reinstated_students": suspensions.filter(
            revoked=True
        ).count(),

        "total_expulsions": expulsions.count(),

        # Recent Activities

        "recent_cases": DisciplineHistory.objects.select_related(
            "student",
            "disciplined_by",
        ).order_by(
            "-created_at"
        )[:10],

        # Suspension Reasons

        "reason_summary": (
            DisciplineHistory.objects
            .values("reason")
            .annotate(total=Count("id"))
            .order_by("-total")
        ),

    }

    return render(
        request,
        "students/discipline_dashboard.html",
        context,
    )
