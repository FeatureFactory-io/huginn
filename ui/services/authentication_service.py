"""Authenticate users for the web shell (Acts 0–12)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model, login, logout


class AuthenticationService:
    """Authenticate credentials and rotate sessions."""

    def authenticate_user(self, email: str, password: str, request) -> tuple[Any, str | None]:
        """Validate email/password and bind an authenticated session on success."""
        email = (email or "").strip()
        if not email or not password:
            return None, None

        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None or not user.check_password(password):
            return None, "Invalid email or password"

        login(request, user)
        return user, None

    def logout_user(self, request) -> None:
        """Clear server-side session credentials."""
        logout(request)
