from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import role_required


@login_required
@role_required("SUPER_ADMIN")
def settings_dashboard(request):
    context = {
        "debug": settings.DEBUG,
        "secure_ssl_redirect": getattr(settings, "SECURE_SSL_REDIRECT", False),
        "session_cookie_secure": getattr(settings, "SESSION_COOKIE_SECURE", False),
        "csrf_cookie_secure": getattr(settings, "CSRF_COOKIE_SECURE", False),
        "hsts_seconds": getattr(settings, "SECURE_HSTS_SECONDS", 0),
        "timezone": settings.TIME_ZONE,
        "language": settings.LANGUAGE_CODE,
    }
    return render(request, "system_settings/dashboard.html", context)
