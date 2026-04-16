"""
Production settings for AWS Elastic Beanstalk.
All secrets must be set as EB environment properties.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# HTTPS termination is handled at the load balancer / CloudFront layer.
# Re-enable when ACM certificate is attached to the EB environment.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
