import pytest

from ingestion.models import DataSource


@pytest.mark.django_db
def test_create_screen_renders(commander_client):
    r = commander_client.get("/datasources/create/")
    assert r.status_code == 200
    assert "Add Data Source" in r.content.decode()


@pytest.mark.django_db
def test_save_post_redirects_to_detail(commander_client):
    r = commander_client.post(
        "/datasources/create/",
        {
            "name": "gitlab-a",
            "base_url": "https://gitlab.example.com/",
            "token": "glpat-test",
            "action": "save",
        },
        follow=False,
    )
    assert r.status_code == 302
    assert DataSource.objects.filter(name="gitlab-a").exists()


@pytest.mark.django_db
def test_connection_test_post_feedback(commander_client):
    r = commander_client.post(
        "/datasources/create/",
        {
            "name": "gitlab-a",
            "base_url": "https://gitlab.example.com/",
            "token": "glpat-test",
            "action": "test-connection",
        },
    )
    assert r.status_code == 200
    body = r.content.decode()
    assert "create-datasource-feedback" in body
    assert ("Connection OK" in body) or ("Unable to reach GitLab" in body)
