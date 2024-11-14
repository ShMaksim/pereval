import pytest
from fastapi.testclient import TestClient
from main import app
import json
import base64


test_data = {
    "beauty_title": "test_beauty_title",
    "title": "test_title",
    "other_titles": "test_other_titles",
    "connect": "test_connect",
    "add_time": "2023-11-21T12:00:00Z",
    "user": {
        "email": "test@example.com",
        "fam": "test_fam",
        "name": "test_name",
        "otc": "test_otc",
        "phone": "+7 123 456 78 90"
    },
    "coords": {
        "latitude": 45.0,
        "longitude": 7.0,
        "height": 1200
    },
    "level": {
        "winter": "1A",
        "summer": "1B",
        "autumn": "1A",
        "spring": "2A"
    },
    "images": [
        {"data": base64.b64encode(b"test image data").decode(), "title": "test_image_1"},
        {"data": base64.b64encode(b"test image data 2").decode(), "title": "test_image_2"}
    ]
}

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_submit_data(client):
    response = client.post("/submitData", json=test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    pereval_id = response.json()["id"]
    return pereval_id


def test_get_pereval_data(client):
    pereval_id = test_submit_data(client)
    response = client.get(f"/submitData/{pereval_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pereval_id



def test_update_pereval_data(client):
    pereval_id = test_submit_data(client)
    updated_data = test_data.copy()
    updated_data["title"] = "updated_title"
    del updated_data["user"]

    response = client.patch(f"/submitData/{pereval_id}", json=updated_data)

    assert response.status_code == 200
    assert response.json()["state"] == 1

    response = client.get(f"/submitData/{pereval_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "updated_title"



def test_get_perevals_by_user_email(client):
    pereval_id = test_submit_data(client)

    response = client.get(f"/submitData/?user__email={test_data['user']['email']}")
    assert response.status_code == 200
    perevals = response.json()
    assert isinstance(perevals, list)
    assert len(perevals) >= 1


def test_get_pereval_data_not_found(client):
    response = client.get("/submitData/9999999")
    assert response.status_code == 404


def test_update_pereval_data_not_found(client):
    response = client.patch("/submitData/9999999", json=test_data)
    assert response.status_code == 404 or response.status_code == 400



def test_get_perevals_by_user_email_not_found(client):
    response = client.get("/submitData/?user__email=nonexistent@example.com")
    assert response.status_code == 404