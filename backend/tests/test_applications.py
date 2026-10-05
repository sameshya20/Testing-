import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer test-token-admin"}

def test_get_applications():
    response = client.get("/api/v1/applications", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "code" in data[0]

def test_get_single_application():
    response = client.get("/api/v1/applications/1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

