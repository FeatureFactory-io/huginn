import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture()
def commander_user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email="donland@example.com",
        password="s3cr3t",
        full_name="Commander Donland",
    )


@pytest.fixture()
def commander_client(db, commander_user):
    client = Client()
    client.force_login(commander_user)
    return client
