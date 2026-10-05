import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    payload = {
        "email": "admin@enterprise.com",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@enterprise.com"

def test_login_invalid_credentials():
    payload = {
        "email": "admin@enterprise.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_get_me_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_get_me_authorized():
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@enterprise.com", "password": "password123"})
    token = login_res.json()["access_token"]
    
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@enterprise.com"

def test_logout():
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@enterprise.com", "password": "password123"})
    token = login_res.json()["access_token"]
    
    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Subsequent request using invalidated token should fail with 401
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401
