"""Register and auto-login a new account (DEBUG-only sprint)."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

logger = logging.getLogger("huginn.registration")

User = get_user_model()


class RegistrationService:
    """Create a new active account and bind the session."""

    def register(self, email: str, full_name: str, password: str, request) -> tuple[Any, str | None]:
        """Create user and log in on success.

        Returns ``(user, None)``      on successful create + login.
        Returns ``(None, None)``      on duplicate email — enumeration protection
                                      (caller must redirect the same as success).
        Returns ``(None, error_msg)`` on password-validator failure or blank input.
        """
        email = (email or "").strip().lower()
        full_name = (full_name or "").strip()

        if not email or not password:
            return None, "Please complete all required fields."

        try:
            validate_password(password, user=None)
        except ValidationError as exc:
            return None, exc.messages[0]

        if User.objects.filter(email__iexact=email).exists():
            logger.info('"event":"register_duplicate_silent"')
            return None, None

        user = User.objects.create_user(email=email, password=password, full_name=full_name)
        login(request, user)
        logger.info('"event":"register_success","user_id":%s', user.pk)
        return user, None
