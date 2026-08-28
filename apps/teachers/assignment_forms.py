from django import forms

from apps.academics.models import SchoolClass, Subject

from .models import Teacher, TeacherSubject


class TeacherSubjectForm(forms.ModelForm):
    class Meta:
        model = TeacherSubject
        fields = ["subject", "school_class"]
        widgets = {
            "subject": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        if teacher is not None:
            self.fields["subject"].queryset = Subject.objects.filter(
                school=teacher.school
            ).order_by("name")
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=teacher.school
            ).order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get("subject")
        school_class = cleaned_data.get("school_class")
        if self.teacher and subject and school_class:
            existing = TeacherSubject.objects.filter(
                teacher=self.teacher,
                subject=subject,
                school_class=school_class,
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    "This subject and class are already assigned to this teacher."
                )
        return cleaned_data
