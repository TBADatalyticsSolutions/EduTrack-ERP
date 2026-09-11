from django import forms

from apps.academics.models import AcademicSession, SchoolClass, Term


class PromotionForm(forms.Form):
    """Validate school-scoped, session-aware student promotion."""

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.none(),
        label="Academic Session",
        empty_label="Select Academic Session",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.none(),
        label="Term",
        empty_label="Select Term",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    current_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        label="Current Class",
        empty_label="Select Current Class",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    next_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        label="Next Class",
        empty_label="Select Next Class",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school:
            self.fields["session"].queryset = AcademicSession.objects.filter(
                school=school,
                is_active=True,
            ).order_by("-is_current", "-created_at")
            self.fields["current_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("name")
            self.fields["next_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("name")

            session_id = self.data.get("session") if self.is_bound else None
            if session_id:
                self.fields["term"].queryset = Term.objects.filter(
                    school=school,
                    session_id=session_id,
                    is_active=True,
                ).order_by("-is_current", "name")
            else:
                self.fields["term"].queryset = Term.objects.filter(
                    school=school,
                    is_active=True,
                ).order_by("-is_current", "name")

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("session")
        term = cleaned.get("term")
        current_class = cleaned.get("current_class")
        next_class = cleaned.get("next_class")

        if not self.school:
            raise forms.ValidationError("A school context is required.")
        if current_class and current_class.school_id != self.school.id:
            self.add_error("current_class", "Invalid class for this school.")
        if next_class and next_class.school_id != self.school.id:
            self.add_error("next_class", "Invalid class for this school.")
        if current_class and next_class and current_class.pk == next_class.pk:
            self.add_error(
                "next_class",
                "The Next Class must be different from the Current Class.",
            )
        if session and session.school_id != self.school.id:
            self.add_error("session", "Invalid academic session for this school.")
        if term:
            if term.school_id != self.school.id:
                self.add_error("term", "Invalid term for this school.")
            elif session and term.session_id != session.pk:
                self.add_error(
                    "term",
                    "The selected term does not belong to the selected academic session.",
                )
        return cleaned


class GraduationForm(forms.Form):
    """Form for graduating an individual student."""

    reason = forms.CharField(
        label="Graduation Reason",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Completed SS3"}
        ),
    )


class WithdrawalForm(forms.Form):
    """Form for withdrawing a student."""

    reason = forms.CharField(
        label="Withdrawal Reason",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Relocated, Financial Reasons",
            }
        ),
    )
    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional remarks...",
            }
        ),
    )


class TransferForm(forms.Form):
    """Form for transferring a student to another class/session."""

    to_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        label="Transfer To Class",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    to_session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.none(),
        label="Transfer To Session",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.CharField(
        label="Transfer Reason",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Reason for transfer...",
            }
        ),
    )
    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Additional remarks...",
            }
        ),
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school:
            self.fields["to_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("name")
            self.fields["to_session"].queryset = AcademicSession.objects.filter(
                school=school,
                is_active=True,
            ).order_by("-is_current", "-created_at")

    def clean(self):
        cleaned = super().clean()
        to_class = cleaned.get("to_class")
        to_session = cleaned.get("to_session")
        if not self.school:
            raise forms.ValidationError("A school context is required.")
        if to_class and to_class.school_id != self.school.id:
            self.add_error("to_class", "Invalid destination class for this school.")
        if to_session and to_session.school_id != self.school.id:
            self.add_error("to_session", "Invalid academic session for this school.")
        return cleaned


class SuspensionForm(forms.Form):
    """Form for suspending a student."""

    REASONS = (
        ("MISCONDUCT", "Misconduct"),
        ("EXAM_MALPRACTICE", "Examination Malpractice"),
        ("FIGHTING", "Fighting"),
        ("BULLYING", "Bullying"),
        ("ABSENTEEISM", "Persistent Absenteeism"),
        ("UNPAID_FEES", "Outstanding School Fees"),
        ("VANDALISM", "Damage to School Property"),
        ("OTHER", "Other"),
    )

    reason = forms.ChoiceField(
        choices=REASONS,
        label="Suspension Reason",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    suspension_start = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    suspension_end = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Reason for suspension...",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("suspension_start")
        end = cleaned.get("suspension_end")
        if start and end and end < start:
            raise forms.ValidationError(
                "Suspension end date cannot be earlier than the start date."
            )
        return cleaned


class ExpulsionForm(forms.Form):
    """Form for permanently expelling a student."""

    REASONS = (
        ("GROSS_MISCONDUCT", "Gross Misconduct"),
        ("CULTISM", "Cultism"),
        ("DRUG_ABUSE", "Drug Abuse"),
        ("VIOLENCE", "Violence"),
        ("THEFT", "Theft"),
        ("SEXUAL_MISCONDUCT", "Sexual Misconduct"),
        ("CRIMINAL_OFFENCE", "Criminal Offence"),
        ("OTHER", "Other"),
    )

    reason = forms.ChoiceField(
        choices=REASONS,
        label="Expulsion Reason",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Reason for expulsion...",
            }
        ),
    )
