from django.contrib import admin

from .models import (
    AcademicSession,
    Term,
    SchoolClass,
    ClassArm,
)


admin.site.register(AcademicSession)
admin.site.register(Term)
admin.site.register(SchoolClass)
admin.site.register(ClassArm)