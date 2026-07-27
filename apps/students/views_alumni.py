from django.shortcuts import render

from .models import GraduationHistory


def alumni_list(request):

    alumni = GraduationHistory.objects.select_related(
        "student",
        "graduated_class",
    ).order_by("-graduation_date")

    return render(
        request,
        "students/alumni_list.html",
        {
            "alumni": alumni,
        },
    )