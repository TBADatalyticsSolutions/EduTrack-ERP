from django import forms

from apps.academics.models import AcademicSession, SchoolClass, Term

from .models import Parent, Student


class StudentEnrollmentForm(forms.ModelForm):
    """Create or update a student with parent/guardian information."""

    parent_first_name = forms.CharField(
        label="Parent/Guardian First Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    parent_last_name = forms.CharField(
        label="Parent/Guardian Last Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    parent_phone = forms.CharField(
        label="Parent/Guardian Phone",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    parent_email = forms.EmailField(
        label="Parent/Guardian Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    parent_address = forms.CharField(
        label="Parent/Guardian Address",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "other_name",
            "gender",
            "date_of_birth",
            "admission_date",
            "current_session",
            "current_term",
            "current_class",
            "passport",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "other_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "admission_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "current_session": forms.Select(attrs={"class": "form-select"}),
            "current_term": forms.Select(attrs={"class": "form-select"}),
            "current_class": forms.Select(attrs={"class": "form-select"}),
            "passport": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, school=None, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.school = school

        # Session and class choices are always limited to the student's school.
        self.fields["current_session"].queryset = (
            AcademicSession.objects.filter(school=school, is_active=True)
            .order_by("-is_current", "-created_at")
            if school else AcademicSession.objects.none()
        )
        self.fields["current_class"].queryset = (
            SchoolClass.objects.filter(school=school, is_active=True)
            .order_by("name")
            if school else SchoolClass.objects.none()
        )

        # Enrolment must have an academic session, term and class.
        self.fields["current_session"].required = True
        self.fields["current_term"].required = True
        self.fields["current_class"].required = True

        selected_session_id = (
            self.data.get("current_session") if self.is_bound else None
        )
        if not selected_session_id and instance and instance.current_session_id:
            selected_session_id = instance.current_session_id

        # For a new enrolment, default to the school's current session so the
        # corresponding manually-created production terms are immediately
        # available when the form opens.
        if not selected_session_id and school:
            current_session = (
                AcademicSession.objects.filter(
                    school=school,
                    is_active=True,
                    is_current=True,
                )
                .order_by("-created_at")
                .first()
            )
            if current_session:
                selected_session_id = current_session.pk
                self.initial.setdefault("current_session", current_session.pk)

        # Terms are restricted to the same school and selected session. This
        # ensures production terms manually loaded for the current session are
        # shown instead of unrelated terms from another session.
        if school:
            term_queryset = Term.objects.filter(school=school)
            if selected_session_id:
                term_queryset = term_queryset.filter(session_id=selected_session_id)
            self.fields["current_term"].queryset = term_queryset.order_by(
                "-is_current", "name"
            )

            # If the selected session has a current term, preselect it for a
            # new enrolment. Existing student records keep their saved term.
            if not instance and selected_session_id and not self.is_bound:
                current_term = (
                    self.fields["current_term"].queryset.filter(
                        is_current=True
                    )
                    .order_by("-created_at")
                    .first()
                )
                if current_term:
                    self.initial.setdefault("current_term", current_term.pk)
        else:
            self.fields["current_term"].queryset = Term.objects.none()

        if instance and instance.pk:
            parent = instance.parents.filter(school=school).order_by("created_at").first()
            if parent:
                self.initial.update({
                    "parent_first_name": parent.first_name,
                    "parent_last_name": parent.last_name,
                    "parent_phone": parent.phone,
                    "parent_email": parent.email,
                    "parent_address": parent.address,
                })

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("current_session")
        term = cleaned.get("current_term")
        school_class = cleaned.get("current_class")

        if session and self.school and session.school_id != self.school.id:
            self.add_error("current_session", "Invalid academic session for this school.")

        if school_class and self.school and school_class.school_id != self.school.id:
            self.add_error("current_class", "Invalid class for this school.")

        if term and self.school:
            if term.school_id != self.school.id:
                self.add_error("current_term", "Invalid term for this school.")
            elif session and term.session_id != session.id:
                self.add_error(
                    "current_term",
                    "The selected term does not belong to the selected academic session.",
                )

        first = (cleaned.get("first_name") or "").strip()
        last = (cleaned.get("last_name") or "").strip()
        dob = cleaned.get("date_of_birth")

        if self.school and first and last and dob:
            duplicates = Student.objects.filter(
                school=self.school,
                first_name__iexact=first,
                last_name__iexact=last,
                date_of_birth=dob,
            )
            if self.instance and self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "A student with the same first name, last name and date of birth "
                    "already exists in this school. Please check the existing record."
                )

        return cleaned

    def save_with_parent(self, *, commit=True):
        student = super().save(commit=False)
        student.school = self.school
        student.status = "ACTIVE"
        student.is_graduated = False
        if commit:
            student.save()
            self.save_m2m()
            parent = student.parents.filter(school=self.school).order_by("created_at").first()
            parent_data = {
                "first_name": self.cleaned_data["parent_first_name"].strip(),
                "last_name": self.cleaned_data["parent_last_name"].strip(),
                "phone": self.cleaned_data["parent_phone"].strip(),
                "email": self.cleaned_data.get("parent_email", "").strip(),
                "address": self.cleaned_data.get("parent_address", "").strip(),
            }
            if parent:
                for field, value in parent_data.items():
                    setattr(parent, field, value)
                parent.save()
            else:
                parent = Parent.objects.create(school=self.school, **parent_data)
                parent.students.add(student)
        return student
