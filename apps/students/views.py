from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
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
from .promotion import (
    promote_students,
    promote_student as promote_single_student,
)
from .transfer import transfer_student


# =====================================================
# STUDENT LIST
# =====================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
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
        .order_by("admission_number")
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
# BULK STUDENT PROMOTION
# =====================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
def promotion_index(request):
    """
    Bulk promotion dashboard.

    Allows authorized staff to:

    1. Select a current class.
    2. Select a destination/next class.
    3. Preview the number of eligible students.
    4. Promote all eligible students.
    """

    form = PromotionForm()

    preview_count = None
    promoted = None
    selected_current_class = None
    selected_next_class = None

    if request.method == "POST":

        form = PromotionForm(request.POST)

        if form.is_valid():

            current_class = form.cleaned_data["current_class"]
            next_class = form.cleaned_data["next_class"]

            selected_current_class = current_class
            selected_next_class = next_class

            # -------------------------------------------------
            # PREVENT SAME CLASS PROMOTION
            # -------------------------------------------------

            if current_class.pk == next_class.pk:

                form.add_error(
                    "next_class",
                    "The Next Class must be different from the Current Class.",
                )

            else:

                # -------------------------------------------------
                # FIND ELIGIBLE STUDENTS
                # -------------------------------------------------

                eligible_students = Student.objects.filter(
                    current_class=current_class,
                    is_graduated=False,
                )

                preview_count = eligible_students.count()

                # -------------------------------------------------
                # PREVIEW
                # -------------------------------------------------

                if "preview" in request.POST:

                    if preview_count == 0:

                        messages.warning(
                            request,
                            (
                                f"There are no eligible students "
                                f"in {current_class.name} for promotion."
                            ),
                        )

                    else:

                        messages.info(
                            request,
                            (
                                f"{preview_count} eligible student(s) "
                                f"found in {current_class.name}."
                            ),
                        )

                # -------------------------------------------------
                # BULK PROMOTION
                # -------------------------------------------------

                elif "promote" in request.POST:

                    if preview_count == 0:

                        messages.warning(
                            request,
                            (
                                f"There are no eligible students "
                                f"in {current_class.name} to promote."
                            ),
                        )

                    else:

                        try:

                            with transaction.atomic():

                                promoted = promote_students(
                                    current_class,
                                    next_class,
                                )

                            # -----------------------------------------
                            # ACTIVITY LOG
                            # -----------------------------------------

                            log_activity(
                                request,
                                action="PROMOTION",
                                module="Students",
                                description=(
                                    f"Bulk promotion completed. "
                                    f"{promoted} student(s) promoted "
                                    f"from '{current_class.name}' "
                                    f"to '{next_class.name}'."
                                ),
                            )

                            # -----------------------------------------
                            # SUCCESS MESSAGE
                            # -----------------------------------------

                            messages.success(
                                request,
                                (
                                    f"{promoted} student(s) promoted "
                                    f"successfully from "
                                    f"{current_class.name} "
                                    f"to {next_class.name}."
                                ),
                            )

                            return redirect("promotion")

                        except Exception as exc:

                            messages.error(
                                request,
                                (
                                    "The promotion could not be completed. "
                                    f"Error: {exc}"
                                ),
                            )

    return render(
        request,
        "students/promotion.html",
        {
            "form": form,

            "preview_count": preview_count,

            "promoted": promoted,

            "selected_current_class": (
                selected_current_class
            ),

            "selected_next_class": (
                selected_next_class
            ),
        },
    )


# =====================================================
# INDIVIDUAL STUDENT TRANSFER
# =====================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
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

                log_activity(
                    request,
                    action="TRANSFER",
                    module="Students",
                    description=(
                        f"Student '{student.full_name()}' "
                        f"was transferred. "
                        f"Reason: "
                        f"{form.cleaned_data['reason']}"
                    ),
                )

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

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
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

            reason = form.cleaned_data["reason"]

            graduate_student(
                student,
                reason,
            )

            log_activity(
                request,
                action="GRADUATION",
                module="Students",
                description=(
                    f"Student '{student.full_name()}' "
                    f"was graduated. "
                    f"Reason: {reason}"
                ),
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

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
)
def bulk_graduation(request):
    """
    Graduate all eligible students in a selected class.
    """

    classes = (
        SchoolClass.objects
        .all()
        .order_by("name")
    )

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

            preview_students = (
                Student.objects
                .filter(
                    current_class=selected_class,
                    is_graduated=False,
                )
                .order_by(
                    "last_name",
                    "first_name",
                )
            )

            total_students = preview_students.count()

            male_students = preview_students.filter(
                gender="M"
            ).count()

            female_students = preview_students.filter(
                gender="F"
            ).count()

            # -------------------------------------------------
            # BULK GRADUATION
            # -------------------------------------------------

            if "graduate" in request.POST:

                if total_students == 0:

                    messages.warning(
                        request,
                        "There are no students to graduate.",
                    )

                    return redirect(
                        "bulk-graduation"
                    )

                graduated = 0

                with transaction.atomic():

                    for student in preview_students:

                        student.is_graduated = True
                        student.status = "GRADUATED"

                        student.graduation_date = (
                            timezone.now().date()
                        )

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
                            academic_session=(
                                student.graduation_session
                            ),
                            graduated_by=request.user,
                            remarks="Bulk graduation",
                        )

                        graduated += 1

                log_activity(
                    request,
                    action="GRADUATION",
                    module="Students",
                    description=(
                        f"Bulk graduation completed for "
                        f"class '{selected_class.name}'. "
                        f"{graduated} student(s) graduated."
                    ),
                )

                messages.success(
                    request,
                    (
                        f"{graduated} student(s) "
                        "graduated successfully."
                    ),
                )

                return redirect(
                    "bulk-graduation"
                )

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
# INDIVIDUAL STUDENT PROMOTION
# =====================================================

@login_required
@role_required(
    "SUPER_ADMIN",
    "SCHOOL_ADMIN",
    "PRINCIPAL",
    "REGISTRAR",
)
def promote_student_view(request, pk):
    """
    Promote an individual student to the selected next class.
    """

    student = get_object_or_404(
        Student.objects.select_related(
            "current_class",
            "current_session",
            "school",
        ),
        pk=pk,
    )

    if request.method == "POST":

        next_class_id = request.POST.get(
            "next_class"
        )

        if not next_class_id:

            messages.error(
                request,
                "Please select the next class.",
            )

            return redirect(
                "student-promote",
                pk=student.pk,
            )

        next_class = get_object_or_404(
            SchoolClass,
            pk=next_class_id,
        )

        # -------------------------------------------------
        # PREVENT SAME CLASS
        # -------------------------------------------------

        if student.current_class_id == next_class.id:

            messages.error(
                request,
                "The student is already in this class.",
            )

            return redirect(
                "student-promote",
                pk=student.pk,
            )

        # -------------------------------------------------
        # PREVENT GRADUATED STUDENT PROMOTION
        # -------------------------------------------------

        if student.is_graduated:

            messages.error(
                request,
                "A graduated student cannot be promoted.",
            )

            return redirect(
                "student-promote",
                pk=student.pk,
            )

        old_class = student.current_class

        try:

            promoted_student = promote_single_student(
                student=student,
                next_class=next_class,
            )

        except ValueError as exc:

            messages.error(
                request,
                str(exc),
            )

            return redirect(
                "student-promote",
                pk=student.pk,
            )

        log_activity(
            request,
            action="UPDATE",
            module="Students",
            description=(
                f"Student "
                f"'{promoted_student.full_name()}' "
                f"was promoted from "
                f"'{old_class.name if old_class else 'Unassigned'}' "
                f"to '{next_class.name}'."
            ),
        )

        messages.success(
            request,
            (
                f"{promoted_student.full_name()} "
                f"was promoted successfully to "
                f"{next_class.name}."
            ),
        )

        return redirect(
            "student-list"
        )

    # -------------------------------------------------
    # AVAILABLE NEXT CLASSES
    # -------------------------------------------------

    next_classes = (
        SchoolClass.objects
        .exclude(
            pk=student.current_class_id
        )
        .order_by("name")
    )

    return render(
        request,
        "students/promote_student.html",
        {
            "student": student,
            "next_classes": next_classes,
        },
    )