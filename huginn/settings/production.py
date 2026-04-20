"""
Production settings for AWS Elastic Beanstalk.
All secrets must be set as EB environment properties.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# HTTPS is terminated at CloudFront. CloudFront forwards X-Forwarded-Proto: https
# and the original Host header (via AllViewer origin request policy).
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Explicitly trust the public domain for CSRF on HTMX POST requests.
CSRF_TRUSTED_ORIGINS = ["https://huginn.featurefactory.io"]

# Exempt /health/ from the SSL redirect so the CI smoke test can reach the EB
# CNAME directly over HTTP (bypassing CloudFront) without hitting a 301 loop.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]

# HSTS — start at 1 hour; bump SECURE_HSTS_SECONDS to 31536000 after a week
# of stable HTTPS operation.
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
