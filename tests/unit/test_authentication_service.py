"""Unit tests for ui.services.authentication_service.AuthenticationService."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from ui.services.authentication_service import AuthenticationService


def _request_with_session():
    factory = RequestFactory()
    request = factory.post("/")
    middleware = SessionMiddleware(lambda _req: None)
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


@pytest.mark.django_db
def test_authenticate_user_returns_user_on_valid_credentials():
    user_model = get_user_model()
    user_model.objects.create_user("a@b.com", "secret")
    request = _request_with_session()
    user, err = AuthenticationService().authenticate_user("a@b.com", "secret", request)
    assert err is None
    assert user is not None
    assert user.email == "a@b.com"
    assert request.user.is_authenticated


@pytest.mark.django_db
def test_authenticate_user_returns_none_with_message_on_wrong_password():
    user_model = get_user_model()
    user_model.objects.create_user("a@b.com", "secret")
    request = _request_with_session()
    user, err = AuthenticationService().authenticate_user("a@b.com", "wrong", request)
    assert user is None
    assert err == "Invalid email or password"


@pytest.mark.django_db
def test_authenticate_user_returns_none_with_message_on_unknown_email():
    request = _request_with_session()
    user, err = AuthenticationService().authenticate_user("nobody@example.com", "x", request)
    assert user is None
    assert err == "Invalid email or password"


@pytest.mark.django_db
def test_authenticate_user_treats_email_case_insensitively():
    user_model = get_user_model()
    user_model.objects.create_user("Mixed@Example.COM", "secret")
    request = _request_with_session()
    user, err = AuthenticationService().authenticate_user("mixed@example.com", "secret", request)
    assert err is None
    assert user is not None


@pytest.mark.django_db
def test_authenticate_user_rejects_blank_email_or_password_with_minimal_queries(django_assert_num_queries):
    request = _request_with_session()
    with django_assert_num_queries(0):
        u1, e1 = AuthenticationService().authenticate_user("", "pw", request)
        assert u1 is None and e1 is None
    with django_assert_num_queries(0):
        u2, e2 = AuthenticationService().authenticate_user("a@b.com", "", request)
        assert u2 is None and e2 is None


@pytest.mark.django_db
def test_authenticate_user_strips_whitespace_around_email():
    user_model = get_user_model()
    user_model.objects.create_user("trim@example.com", "secret")
    request = _request_with_session()
    user, err = AuthenticationService().authenticate_user("  trim@example.com  ", "secret", request)
    assert err is None
    assert user is not None


@pytest.mark.django_db
def test_logout_user_clears_authenticated_session():
    user_model = get_user_model()
    user_model.objects.create_user("x@y.com", "pw")
    request = _request_with_session()
    AuthenticationService().authenticate_user("x@y.com", "pw", request)
    assert request.user.is_authenticated
    AuthenticationService().logout_user(request)
    assert not request.user.is_authenticated
