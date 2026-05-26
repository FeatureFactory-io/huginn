"""Welcome page and /health/ JSON include Celery-related checks."""

import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_json_includes_celery_checks(commander_client):
    r = commander_client.get(reverse("health-json"))
    assert r.status_code == 200
    data = json.loads(r.content.decode())
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    names = {c["name"] for c in data["checks"]}
    assert "Celery workers" in names
    assert "Celery Beat (scheduler)" in names
    assert all("status" in c and "detail" in c for c in data["checks"])


@pytest.mark.django_db
def test_health_json_revision_from_env(commander_client, monkeypatch):
    monkeypatch.setenv("HUGINN_GIT_REVISION", "0.5.1")
    r = commander_client.get(reverse("health-json"))
    assert r.status_code == 200
    data = json.loads(r.content.decode())
    assert data["revision"] == "0.5.1"


@pytest.mark.django_db
def test_welcome_page_lists_celery_rows(commander_client):
    r = commander_client.get(reverse("welcome"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Celery workers" in body
    assert "Celery Beat (scheduler)" in body
    assert 'data-testid="welcome-status-healthy"' in body or "welcome-status-" in body
