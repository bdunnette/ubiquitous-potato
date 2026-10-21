import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient

from demo.models import Item


@pytest.fixture
def api_client():
    return APIClient()


def test_rest_framework_installed():
    """
    Verify rest_framework is included in INSTALLED_APPS and configured.
    """
    assert "rest_framework" in settings.INSTALLED_APPS
    assert hasattr(settings, "REST_FRAMEWORK")
    assert settings.REST_FRAMEWORK.get("PAGE_SIZE") == 10


@pytest.mark.django_db
def test_api_root(api_client):
    """
    Test that the browsable API root (/api/) responds with 200
    and lists discoverable endpoint links.
    """
    response = api_client.get("/api/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "info" in data


@pytest.mark.django_db
def test_api_info_endpoint(api_client):
    """
    Test the /api/info/ diagnostics endpoint returns runtime details.
    """
    response = api_client.get("/api/info/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "python_version" in data
    assert "django_version" in data
    assert "drf_version" in data
    assert "environment" in data
    assert "database" in data
    assert "stats" in data
    assert data["stats"]["item_count"] == 0


@pytest.mark.django_db
def test_api_items_list_empty(api_client):
    """
    Test GET /api/items/ on an empty database returns a paginated empty response.
    """
    response = api_client.get("/api/items/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []


@pytest.mark.django_db
def test_api_items_create(api_client):
    """
    Test POST /api/items/ successfully creates a new record.
    """
    payload = {
        "title": "API Test Item",
        "description": "Created via Django REST Framework",
    }
    response = api_client.post("/api/items/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "API Test Item"
    assert data["description"] == "Created via Django REST Framework"
    assert "id" in data
    assert "created_at" in data

    # Verify item persisted in the database
    assert Item.objects.filter(id=data["id"]).exists()


@pytest.mark.django_db
def test_api_items_create_validation_error(api_client):
    """
    Test POST /api/items/ with invalid data returns HTTP 400 Bad Request.
    """
    payload = {"title": "", "description": "Missing title"}
    response = api_client.post("/api/items/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "title" in data


@pytest.mark.django_db
def test_api_items_retrieve(api_client):
    """
    Test GET /api/items/<id>/ retrieves item details.
    """
    item = Item.objects.create(title="Retrieve Me", description="Detail view test")
    response = api_client.get(f"/api/items/{item.id}/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == item.id
    assert data["title"] == "Retrieve Me"
    assert data["description"] == "Detail view test"


@pytest.mark.django_db
def test_api_items_retrieve_not_found(api_client):
    """
    Test GET /api/items/<id>/ with nonexistent ID returns 404.
    """
    response = api_client.get("/api/items/99999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_api_items_update(api_client):
    """
    Test PUT /api/items/<id>/ fully updates an existing item.
    """
    item = Item.objects.create(title="Original Title", description="Original Desc")
    payload = {
        "title": "Updated Title",
        "description": "Updated Desc",
    }
    response = api_client.put(f"/api/items/{item.id}/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    item.refresh_from_db()
    assert item.title == "Updated Title"
    assert item.description == "Updated Desc"


@pytest.mark.django_db
def test_api_items_partial_update(api_client):
    """
    Test PATCH /api/items/<id>/ partially updates an item.
    """
    item = Item.objects.create(title="Keep Title", description="Before Patch")
    payload = {"description": "After Patch"}
    response = api_client.patch(f"/api/items/{item.id}/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    item.refresh_from_db()
    assert item.title == "Keep Title"
    assert item.description == "After Patch"


@pytest.mark.django_db
def test_api_items_delete(api_client):
    """
    Test DELETE /api/items/<id>/ removes an item.
    """
    item = Item.objects.create(title="Delete Me", description="To be deleted")
    response = api_client.delete(f"/api/items/{item.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Item.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_api_items_pagination(api_client):
    """
    Test that items list endpoint paginates according to PAGE_SIZE (10).
    """
    items = [Item(title=f"Item {i}", description=f"Desc {i}") for i in range(15)]
    Item.objects.bulk_create(items)

    # First page
    response = api_client.get("/api/items/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 15
    assert len(data["results"]) == 10
    assert data["next"] is not None
    assert data["previous"] is None

    # Second page
    response_p2 = api_client.get(data["next"])
    assert response_p2.status_code == status.HTTP_200_OK
    data_p2 = response_p2.json()
    assert len(data_p2["results"]) == 5
    assert data_p2["next"] is None
    assert data_p2["previous"] is not None


@pytest.mark.django_db
def test_api_urls_with_zappa_stage_environment(monkeypatch, api_client):
    """
    Ensure API URLs are correctly prefixed with stage (e.g. /dev/api/)
    when running inside a Zappa environment with API Gateway.
    """
    from django.urls import set_script_prefix

    monkeypatch.setattr(settings, "FORCE_SCRIPT_NAME", "/dev")
    set_script_prefix("/dev")
    try:
        response = api_client.get("/api/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == "http://testserver/dev/api/items/"
        assert data["info"] == "http://testserver/dev/api/info/"
    finally:
        set_script_prefix("/")


@pytest.mark.django_db
def test_home_page_renders_with_zappa_stage_prefix(monkeypatch, client):
    """
    Verify that in a Zappa environment with stage prefix (e.g. /dev/),
    all API links in the web dashboard are prefixed with /dev/.
    """
    from django.urls import set_script_prefix

    monkeypatch.setattr(settings, "FORCE_SCRIPT_NAME", "/dev")
    set_script_prefix("/dev")
    try:
        response = client.get("/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'href="/dev/api/"' in content
        assert 'href="/dev/api/items/"' in content
        assert 'href="/dev/api/info/"' in content
        assert 'href="/dev/health/"' in content
        assert 'href="/dev/admin/"' in content
    finally:
        set_script_prefix("/")
