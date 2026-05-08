"""Explicit FRAGO audit writes — no signals."""

from __future__ import annotations

from django.http import HttpRequest

from sitrep.models.frago import Frago, FragoAuditEvent


def record_frago_audit(frago: Frago, request: HttpRequest | None, *, kind: str, message: str) -> None:
    actor = None
    if request is not None and getattr(request, "user", None) is not None and request.user.is_authenticated:
        actor = request.user
    FragoAuditEvent.objects.create(frago=frago, actor=actor, kind=kind, message=message[:512])
