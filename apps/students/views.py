from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from apps.academics.models import SchoolClass

from .forms import (
    GraduationForm,
    PromotionForm,
    TransferForm,
)
from .graduation import graduate_student
from .models import (
    GraduationHistory,
    Student,
    TransferHistory,
    WithdrawalHistory,
)
from .promotion import promote_students
from .transfer import transfer_student

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
# =====================================================
# STUDENT LIST
# =====================================================

def student_list(request):
    """
    Display Student Management dashboard.
    """

    students = (
        Student.objects
        .select_related(
            "current_class",
            "current_session",
        )
        .order_by(
            "admission_number"
        )
    )

    context = {

        "students": students,

        "total_students": students.count(),

        "active_students": students.filter(
            status="ACTIVE"
        ).count(),

        "transferred_students": TransferHistory.objects.count(),

        "graduated_students": students.filter(
            status="GRADUATED"
        ).count(),

        "withdrawn_students": students.filter(
            status="WITHDRAWN"
        ).count(),

    }

    return render(
        request,
        "students/student_list.html",
        context,
    )


# =====================================================
# PROMOTION DASHBOARD
# =====================================================

def promotion_index(request):
    """
    Student promotion dashboard.
    """

    form = PromotionForm()

    promoted = None
    preview_count = None

    if request.method == "POST":

        form = PromotionForm(request.POST)

        if form.is_valid():

            current_class = form.cleaned_data["current_class"]
            next_class = form.cleaned_data["next_class"]

            if "preview" in request.POST:

                preview_count = Student.objects.filter(
                    current_class=current_class,
                    is_graduated=False,
                ).count()

            elif "promote" in request.POST:

                promoted = promote_students(
                    current_class,
                    next_class,
                )

                messages.success(
                    request,
                    f"{promoted} student(s) promoted successfully.",
                )

    return render(
        request,
        "students/promotion.html",
        {
            "form": form,
            "preview_count": preview_count,
            "promoted": promoted,
        },
    )


# =====================================================
# INDIVIDUAL STUDENT TRANSFER
# =====================================================

def transfer_student_view(request, pk):
    """
    Transfer an individual student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

    if request.method == "POST":

        form = TransferForm(request.POST)

        if form.is_valid():

            success, message = transfer_student(
                student=student,
                to_class=form.cleaned_data["to_class"],
                to_session=form.cleaned_data["to_session"],
                transferred_by=request.user,
                reason=form.cleaned_data["reason"],
                remarks=form.cleaned_data["remarks"],
            )

            if success:

                messages.success(
                    request,
                    message,
                )

                return redirect("student-list")

            messages.error(
                request,
                message,
            )

    else:

        form = TransferForm()

    return render(
        request,
        "students/transfer_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# =====================================================
# SINGLE STUDENT GRADUATION
# =====================================================

def graduate_student_view(request, pk):
    """
    Graduate a single student.
    """

    student = get_object_or_404(
        Student,
        pk=pk,
    )

    if request.method == "POST":

        form = GraduationForm(request.POST)

        if form.is_valid():

            graduate_student(
                student,
                form.cleaned_data["reason"],
            )

            messages.success(
                request,
                f"{student.full_name()} graduated successfully.",
            )

            return redirect("student-list")

    else:

        form = GraduationForm()

    return render(
        request,
        "students/graduate_student.html",
        {
            "student": student,
            "form": form,
        },
    )


# =====================================================
# BULK GRADUATION
# =====================================================

def bulk_graduation(request):
    """
    Graduate all eligible students in a selected class.
    """

    classes = SchoolClass.objects.all().order_by("name")

    selected_class = None
    preview_students = None

    total_students = 0
    male_students = 0
    female_students = 0

    if request.method == "POST":

        class_id = request.POST.get("school_class")

        if class_id:

            selected_class = get_object_or_404(
                SchoolClass,
                pk=class_id,
            )

            preview_students = Student.objects.filter(
                current_class=selected_class,
                is_graduated=False,
            ).order_by(
                "last_name",
                "first_name",
            )

            total_students = preview_students.count()

            male_students = preview_students.filter(
                gender="M"
            ).count()

            female_students = preview_students.filter(
                gender="F"
            ).count()

            if "graduate" in request.POST:

                if total_students == 0:

                    messages.warning(
                        request,
                        "There are no students to graduate.",
                    )

                    return redirect("bulk-graduation")

                graduated = 0

                with transaction.atomic():

                    for student in preview_students:

                        student.is_graduated = True
                        student.status = "GRADUATED"
                        student.graduation_date = timezone.now().date()

                        student.graduation_session = (
                            student.current_session.name
                            if student.current_session
                            else ""
                        )

                        student.current_class = None

                        student.save()

                        GraduationHistory.objects.create(
                            student=student,
                            school=student.school,
                            graduated_from=selected_class,
                            academic_session=student.graduation_session,
                            graduated_by=request.user,
                            remarks="Bulk graduation",
                        )

                        graduated += 1

                messages.success(
                    request,
                    f"{graduated} student(s) graduated successfully.",
                )

                return redirect("bulk-graduation")

    return render(
        request,
        "students/bulk_graduation.html",
        {
            "classes": classes,
            "selected_class": selected_class,
            "preview_students": preview_students,
            "total_students": total_students,
            "male_students": male_students,
            "female_students": female_students,
        },
    )


# =====================================================
# PLACEHOLDER
# =====================================================

def promote_student(request):
    """
    Reserved for future individual student promotion.
    """

    return redirect("student-list")