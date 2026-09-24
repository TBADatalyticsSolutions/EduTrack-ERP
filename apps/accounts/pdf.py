"""Shared PDF rendering helpers for portal reports.

The application uses xhtml2pdf because it is a pure-Python HTML-to-PDF
renderer and does not require the native GTK/Pango libraries required by
WeasyPrint on Windows.
"""

from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from xhtml2pdf import pisa
from xhtml2pdf.config.resources import ResourceAccessPolicy


def _resource_path(uri, rel=None):
    """Resolve trusted local static/media resources for xhtml2pdf."""
    if not uri:
        return None

    parsed = urlparse(str(uri))

    if parsed.scheme == "file":
        path = Path(unquote(parsed.path))
        if parsed.netloc:
            path = Path(f"//{parsed.netloc}{unquote(parsed.path)}")
        return str(path.resolve())

    static_match = str(uri).startswith(settings.STATIC_URL)
    if static_match:
        relative = str(uri)[len(settings.STATIC_URL):].lstrip("/")
        found = finders.find(relative)
        if isinstance(found, (list, tuple)):
            found = found[0] if found else None
        if found:
            return str(Path(found).resolve())

    media_match = str(uri).startswith(settings.MEDIA_URL)
    if media_match:
        relative = str(uri)[len(settings.MEDIA_URL):].lstrip("/")
        path = (Path(settings.MEDIA_ROOT) / relative).resolve()
        if path.exists():
            return str(path)

    if parsed.scheme in {"http", "https"}:
        return str(uri)

    candidate = Path(str(uri))
    if not candidate.is_absolute() and rel:
        candidate = Path(rel).parent / candidate
    if candidate.exists():
        return str(candidate.resolve())

    return None


def render_pdf(html, *, base_url=None):
    """Render trusted application HTML to PDF bytes."""
    output = __import__("io").BytesIO()
    base_dir = Path(base_url or settings.BASE_DIR).resolve()

    policy = ResourceAccessPolicy(
        base_dir=base_dir,
        extra_roots=(
            Path(settings.STATIC_ROOT).resolve(),
            Path(settings.MEDIA_ROOT).resolve(),
        ),
        allow_private_networks=False,
    )

    status = pisa.CreatePDF(
        html,
        dest=output,
        path=str(base_dir),
        link_callback=_resource_path,
        resource_policy=policy,
        raise_exception=True,
    )

    if status.err:
        raise RuntimeError("Unable to generate PDF.")

    return output.getvalue()
