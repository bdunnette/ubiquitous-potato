import pytest
from django.urls import reverse

from demo.models import Item


@pytest.mark.django_db
def test_health_check_endpoint(client):
    """
    Test the health check endpoint returns 200 and expected JSON structure.
    """
    url = reverse("health_check")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.django_db
def test_home_page_renders(client):
    """
    Test the demo home page renders successfully.
    """
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 200
    assert b"Django Serverless Template" in response.content
    assert reverse("admin:index").encode() in response.content


@pytest.mark.django_db
def test_create_and_delete_item(client):
    """
    Test adding an item via POST and deleting it.
    """
    url = reverse("home")
    post_data = {"title": "Lambda Integration Test", "description": "Testing persistence"}
    response = client.post(url, post_data, follow=True)
    assert response.status_code == 200
    assert Item.objects.filter(title="Lambda Integration Test").exists()

    item = Item.objects.get(title="Lambda Integration Test")
    delete_url = reverse("delete_item", kwargs={"item_id": item.id})
    del_response = client.post(delete_url, follow=True)
    assert del_response.status_code == 200
    assert not Item.objects.filter(title="Lambda Integration Test").exists()


@pytest.mark.django_db
def test_admin_login_page_renders_without_manifest_error(client):
    """
    Verify that accessing /admin/login/ renders with HTTP 200 and does not raise
    a ValueError for missing staticfiles manifest entry.
    """
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    assert b"Django administration" in response.content
