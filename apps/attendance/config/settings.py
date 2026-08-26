INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "apps.core",
    "apps.accounts",
    "apps.schools",
    "apps.students",
    "apps.teachers",
    "apps.academics",

    # Attendance
    "apps.attendance",

    # Other apps
    "apps.finance",
    "apps.results",
    "apps.reports",
    "apps.notifications",
    "apps.api",
]
