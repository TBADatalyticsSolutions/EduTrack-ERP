from django.db import migrations

DEFAULT_TERM_NAMES = ("First Term", "Second Term", "Third Term")


def seed_default_terms(apps, schema_editor):
    AcademicSession = apps.get_model("academics", "AcademicSession")
    Term = apps.get_model("academics", "Term")
    for session in AcademicSession.objects.filter(is_deleted=False):
        existing_terms = Term.objects.filter(school_id=session.school_id, session_id=session.pk, is_deleted=False)
        for name in DEFAULT_TERM_NAMES:
            if not existing_terms.filter(name__iexact=name).exists():
                Term.objects.create(school_id=session.school_id, session_id=session.pk, name=name, is_current=False, is_active=True)
        if not existing_terms.filter(is_current=True).exists():
            first_term = Term.objects.filter(school_id=session.school_id, session_id=session.pk, name__iexact="First Term", is_deleted=False).first()
            if first_term:
                first_term.is_current = True
                first_term.save(update_fields=["is_current", "updated_at"])


def preserve_seeded_terms(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("academics", "0002_subject_classsubject")]
    operations = [migrations.RunPython(seed_default_terms, preserve_seeded_terms)]
