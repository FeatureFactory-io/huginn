"""Custom manager for email-based User model."""

from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Create users with email as the canonical identifier."""

    use_in_migrations = True

    def get_by_natural_key(self, username: str):
        """Case-insensitive lookup for session / ModelBackend."""
        return self.get(email__iexact=username)

    def _normalize_email_value(self, email: str) -> str:
        if not email or not str(email).strip():
            msg = "The Email field must be set"
            raise ValueError(msg)
        cleaned = str(email).strip().lower()
        return self.normalize_email(cleaned)

    def _create_user(self, email, password, **extra_fields):
        email = self._normalize_email_value(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)
        return self._create_user(email, password, **extra_fields)
