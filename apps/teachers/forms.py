from django import forms

from .models import Department, Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "employee_id",
            "first_name",
            "last_name",
            "other_name",
            "gender",
            "date_of_birth",
            "phone",
            "email",
            "address",
            "qualification",
            "department",
            "employment_status",
            "passport",
            "date_employed",
            "is_class_teacher",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "date_employed": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school is not None:
            self.fields["department"].queryset = Department.objects.filter(
                school=school
            ).order_by("name")

    def clean_employee_id(self):
        value = self.cleaned_data["employee_id"].strip()
        qs = Teacher.objects.filter(employee_id__iexact=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This employee ID is already in use.")
        return value
