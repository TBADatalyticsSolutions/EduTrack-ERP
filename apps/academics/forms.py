from django import forms

from .models import AcademicSession, ClassSubject, SchoolClass, Subject, Term


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "is_current"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = AcademicSession.objects.filter(school=self.school, name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This academic session already exists for this school.")
        return name


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ["session", "name", "is_current"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields["session"].queryset = AcademicSession.objects.filter(school=school).order_by("-name") if school else AcademicSession.objects.none()

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("session")
        name = cleaned.get("name", "").strip()
        if session and self.school and session.school_id != self.school.pk:
            raise forms.ValidationError("Select a session belonging to your school.")
        if session and name:
            qs = Term.objects.filter(school=self.school, session=session, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This term already exists in the selected session.")
        cleaned["name"] = name
        return cleaned


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = SchoolClass.objects.filter(school=self.school, name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This class already exists for this school.")
        return name


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "description", "is_core"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ["school_class", "subject"]

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school).order_by("name") if school else SchoolClass.objects.none()
        self.fields["subject"].queryset = Subject.objects.filter(school=school).order_by("name") if school else Subject.objects.none()

    def clean(self):
        cleaned = super().clean()
        school_class = cleaned.get("school_class")
        subject = cleaned.get("subject")
        if school_class and subject:
            if school_class.school_id != self.school.pk or subject.school_id != self.school.pk:
                raise forms.ValidationError("Class and subject must belong to the same school.")
            qs = ClassSubject.objects.filter(school_class=school_class, subject=subject)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This subject is already assigned to the selected class.")
        return cleaned
