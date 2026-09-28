"""Integration tests for the consent-gated Huginn product analytics contract."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

_MEASUREMENT_ID = "G-0M33216B65"
_FEATURE_IDS = (
    "sitrep",
    "frago",
    "variables",
    "chat",
    "decisions",
    "contributors",
    "action-stations",
    "situational-awareness",
)


def test_guest_landing_with_analytics_contract_is_consent_gated(client):
    response = client.get("/")
    body = response.content.decode()

    assert response.status_code == 200
    assert f'data-analytics-measurement-id="{_MEASUREMENT_ID}"' in body
    assert 'data-analytics-enabled="true"' in body
    assert "data-analytics-consent" in body
    assert "data-analytics-settings" in body
    assert "js/product_analytics.js" in body
    assert "googletagmanager.com/gtag/js" not in body


@pytest.mark.django_db
def test_authenticated_page_with_analytics_contract_is_disabled(client):
    user = User.objects.create_user(email="analytics-user@example.com", password="pass")
    client.force_login(user)

    body = client.get("/").content.decode()

    assert 'data-analytics-enabled="true"' not in body
    assert "data-analytics-settings" not in body


def test_landing_with_analytics_contract_marks_ctas_features_and_registration(client):
    body = client.get("/").content.decode()

    assert 'data-analytics-registration="beta"' in body
    assert 'data-analytics-target="beta_registration"' in body
    for feature_id in _FEATURE_IDS:
        assert f'data-analytics-feature="{feature_id}"' in body


def test_product_analytics_source_with_privacy_contract_never_reads_form_values():
    source = Path("static/js/product_analytics.js").read_text(encoding="utf-8")

    assert "FormData" not in source
    assert "email" not in source.lower()
    assert "pageUrl.search" not in source
    assert "ga-disable-" in source
    assert 'analytics_storage: "denied"' in source


def test_landing_beta_with_confirmed_outcome_dispatches_analytics_event():
    source = Path("static/js/landing_beta.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("ff:registration-outcome"' in source
    assert "detail: { outcome: outcome }" in source
