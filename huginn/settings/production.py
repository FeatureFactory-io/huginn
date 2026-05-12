"""
Production settings for AWS Elastic Beanstalk.
All secrets must be set as EB environment properties.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# HTTPS is enforced by CloudFront (Viewer Protocol Policy: Redirect HTTP -> HTTPS).
# Origin (EB nginx -> gunicorn) is reached over HTTP and does NOT receive a
# trustworthy X-Forwarded-Proto header in this distribution, so Django's own
# SECURE_SSL_REDIRECT would loop on every non-/health/ path. Cookies are still
# marked Secure because viewers always speak HTTPS at the edge.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"
CSRF_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

# Explicitly trust the public domain for CSRF on HTMX POST requests.
# EXTRA_CSRF_ORIGINS may be set as a comma-separated EB env var for staging.
_extra_csrf = [o for o in os.environ.get("EXTRA_CSRF_ORIGINS", "").split(",") if o]
CSRF_TRUSTED_ORIGINS = ["https://huginn.featurefactory.io"] + _extra_csrf

# HSTS — start at 1 hour; bump SECURE_HSTS_SECONDS to 31536000 after a week
# of stable HTTPS operation.
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
