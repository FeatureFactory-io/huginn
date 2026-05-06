"""Authenticate users for the web shell (Acts 0–12)."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import authenticate, login, logout

logger = logging.getLogger("huginn.auth")

_INVALID_MESSAGE = "Invalid email or password"


class AuthenticationService:
    """Authenticate credentials and rotate sessions."""

    def authenticate_user(self, email: str, password: str, request) -> tuple[Any, str | None]:
        """Validate email/password and bind an authenticated session on success.

        :param email: Primary identifier (case-insensitive; normalized by ORM/User model).
        :param password: Plain-text password (never logged).
        :param request: Django HTTP request for session binding.
        :return: ``(user, None)`` on success, or ``(None, error_message)`` on credential failure.
            Blank email or password yields ``(None, None)`` so the view can rely on HTML5 validation.
        """
        email = (email or "").strip()
        if not email or not password:
            return None, None

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            logger.info(
                '"event":"auth_login_success","user_id":%s',
                user.pk,
            )
            return user, None

        logger.warning('"event":"auth_login_failure","reason":"invalid_credentials"')
        return None, _INVALID_MESSAGE

    def logout_user(self, request) -> None:
        """Clear server-side session credentials."""
        logout(request)
