from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.accounts.utils import log_activity
from apps.schools.models import School

from .forms import AssessmentTypeForm, GradeSettingForm, StudentResultForm, SubjectResultForm
from .models import AssessmentType, GradeSetting, StudentResult
from .services import calculate_student_result


ROLES = ("SUPER_ADMIN", "SCHOOL_ADMIN", "PRINCIPAL", "REGISTRAR", "TEACHER")


def _school(request):
    if request.user.is_superuser:
        return School.objects.first()
    return getattr(getattr(request.user, "profile", None), "school", None)


@login_required
@role_required(*ROLES)
def dashboard(request):