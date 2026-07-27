from django.shortcuts import render

from .forms import AttendanceRegisterForm
from .services import AttendanceService


def attendance_register(request):

    form = AttendanceRegisterForm()

    students = None

    if request.GET:

        form = AttendanceRegisterForm(request.GET)

        if form.is_valid():

            school_class = form.cleaned_data["school_class"]

            students = AttendanceService.students_for_class(
                school_class
            )

    return render(
        request,
        "attendance/attendance_register.html",
        {
            "form": form,
            "students": students,
        },
    )