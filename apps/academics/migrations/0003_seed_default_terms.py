from django.db import migrations


DEFAULT_TERMS = (
    ("First Term", True),
    ("Second Term", False),
    ("Third Term", False),
)


def seed_default_terms(apps, schema_editor):
    AcademicSession = apps.get_model("academics", "AcademicSession")
    Term = apps.get_model("academics", "Term")

    for session in AcademicSession.objects.filter(is_deleted=False):
        existing_terms = Term.objects.filter(
            school_id=session.school_id,
            session_id=session.pk,
            is_deleted=False,
        )

        for name, is_current in DEFAULT_TERMS:
            if not existing_terms.filter(name__iexact=name).exists():
                Term.objects.create(
                    school_id=session.school_id,
                    session_id=session.pk,
                    name=name,
                    is_current=False,
                    is_active=True,
                )

        # Do not overwrite an existing current term. If the session had no
        # current term, make First Term the current term for a usable default.
        if not existing_terms.filter(is_current=True).exists():
            first_term = Term.objects.filter(
                school_id=session.school_id,
                session_id=session.pk,
                name__iexact="First Term",
                is_deleted=False,
            ).first()
            if first_term:
                first_term.is_current = True
                first_term.save(update_fields=["is_current", "updated_at"])


def remove_seeded_terms(apps, schema_editor):
    Term = apps.get_model("academics", "Term")
    Term.objects.filter(name__in=[name for name, _ in DEFAULT_TERMS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0002_subject_classsubject"),
    ]

    operations = [
        migrations.RunPython(seed_default_terms, remove_seeded_terms),
    ]
