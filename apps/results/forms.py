from django import forms

from .models import AssessmentType, GradeSetting, StudentResult, SubjectResult


class AssessmentTypeForm(forms.ModelForm):
    class Meta:
        model = AssessmentType
        fields = ["name", "maximum_score", "order"]


class GradeSettingForm(forms.ModelForm):
    class Meta:
        model = GradeSetting
        fields = ["grade", "minimum_score", "maximum_score", "remark"]


class StudentResultForm(forms.ModelForm):
    class Meta:
        model = StudentResult
        fields = [
            "student",
            "session",
            "term",
            "school_class",
            "teacher_remark",
            "principal_remark",
            "promotion_status",
            "next_term_resumption",
        ]
        widgets = {
            "teacher_remark": forms.Textarea(attrs={"rows": 3}),
            "principal_remark": forms.Textarea(attrs={"rows": 3}),
            "next_term_resumption": forms.DateInput(attrs={"type": "date"}),
        }


class SubjectResultForm(forms.ModelForm):
    class Meta:
        model = SubjectResult
        fields = [
            "subject",
            "ca1",
            "ca2",
            "assignment",
            "project",
            "examination",
            "teacher_remark",
        ]

    def clean(self):
        cleaned = super().clean()
        for field in ["ca1", "ca2", "assignment", "project", "examination"]:
            value = cleaned.get(field)
            if value is not None and value < 0:
                self.add_error(field, "Score cannot be negative.")
        return cleaned
