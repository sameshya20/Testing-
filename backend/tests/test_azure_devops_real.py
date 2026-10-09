import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import httpx
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.azure_devops_service import azure_devops_service

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token-admin"}


@pytest.fixture(autouse=True)
def set_real_mode(monkeypatch):
    monkeypatch.setenv("AZURE_DEVOPS_MODE", "real")
    from app.core.config import settings
    settings.AZURE_DEVOPS_MODE = "real"
    azure_devops_service.configure("realorg", "RealProject", "valid_pat")
    yield
    settings.AZURE_DEVOPS_MODE = "mock"


def test_azure_devops_config_endpoint():
    """Verify config endpoint returns status without exposing PAT."""
    response = client.get("/api/v1/devops/azure/config", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "organization" in data
    assert "project" in data
    assert "is_pat_configured" in data
    assert "connected" in data
    assert "pat" not in data  # PAT must never be exposed


def test_azure_devops_connect_invalid_pat():
    """Verify that connect with invalid PAT returns clear error message."""
    mock_resp = httpx.Response(
        status_code=401,
        request=httpx.Request("GET", "https://dev.azure.com/testorg/_apis/projects")
    )
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        payload = {
            "organization": "testorg",
            "project": "testproj",
            "pat": "invalid_token_123"
        }
        response = client.post("/api/v1/devops/azure/connect", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert "Invalid or expired Personal Access Token" in data["message"]


def test_azure_devops_connect_success():
    """Verify successful connection retrieves real projects and connects."""
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "value": [
                {"id": "p-1", "name": "RealProject", "description": "Main Project", "state": "wellFormed"},
                {"id": "p-2", "name": "SecondaryProject", "description": "Second Project", "state": "wellFormed"}
            ]
        },
        request=httpx.Request("GET", "https://dev.azure.com/realorg/_apis/projects")
    )
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        payload = {
            "organization": "https://dev.azure.com/realorg",
            "project": "RealProject",
            "pat": "valid_pat_secret"
        }
        response = client.post("/api/v1/devops/azure/connect", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["organization"] == "realorg"
        assert len(data["projects"]) == 2
        assert data["projects"][0]["name"] == "RealProject"


def test_azure_devops_get_areas():
    """Verify classification nodes (Areas) retrieval and flattening."""
    azure_devops_service.configure("realorg", "RealProject", "valid_pat")
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "id": 100,
            "name": "RealProject",
            "hasChildren": True,
            "children": [
                {
                    "id": 101,
                    "name": "Area A",
                    "hasChildren": False,
                    "children": []
                },
                {
                    "id": 102,
                    "name": "Area B",
                    "hasChildren": False,
                    "children": []
                }
            ]
        },
        request=httpx.Request("GET", "https://dev.azure.com/realorg/RealProject/_apis/wit/classificationnodes/Areas")
    )
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        response = client.get("/api/v1/devops/azure/areas?project=RealProject", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        area_names = [a["name"] for a in data]
        assert "RealProject" in area_names
        assert "Area A" in area_names
        assert "Area B" in area_names


def test_azure_devops_query_work_items():
    """Verify WIQL query and batch retrieval of user stories."""
    azure_devops_service.configure("realorg", "RealProject", "valid_pat")
    wiql_resp = httpx.Response(
        status_code=200,
        json={"workItems": [{"id": 1024}, {"id": 1025}]},
        request=httpx.Request("POST", "https://dev.azure.com/realorg/RealProject/_apis/wit/wiql")
    )
    batch_resp = httpx.Response(
        status_code=200,
        json={
            "value": [
                {
                    "id": 1024,
                    "fields": {
                        "System.Id": 1024,
                        "System.Title": "Login functionality",
                        "System.WorkItemType": "User Story",
                        "System.Description": "<p>User can log in with valid credentials.</p>",
                        "Microsoft.VSTS.Common.AcceptanceCriteria": "<p>1. Valid login redirects to dashboard.<br/>2. Invalid password shows error.</p>",
                        "System.State": "Active",
                        "System.AssignedTo": {"displayName": "Alice QA"},
                        "System.AreaPath": "RealProject\\Area A"
                    }
                },
                {
                    "id": 1025,
                    "fields": {
                        "System.Id": 1025,
                        "System.Title": "Password reset",
                        "System.WorkItemType": "User Story",
                        "System.Description": "User can request password reset token.",
                        "Microsoft.VSTS.Common.AcceptanceCriteria": "Reset link expires in 15 minutes.",
                        "System.State": "Active",
                        "System.AssignedTo": "Bob Dev",
                        "System.AreaPath": "RealProject\\Area A"
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://dev.azure.com/realorg/RealProject/_apis/wit/workitemsbatch")
    )

    with patch("httpx.AsyncClient.post", side_effect=[wiql_resp, batch_resp]):
        response = client.get("/api/v1/devops/azure/work-items?area_path=RealProject\\Area A", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "1024"
        assert data[0]["title"] == "Login functionality"
        assert "Valid login redirects to dashboard" in data[0]["acceptance_criteria"]
        assert data[0]["assigned_to"] == "Alice QA"


def test_azure_devops_sync_and_update_prevents_duplicate():
    """Verify that syncing test cases creates on first call and updates on subsequent calls without duplicates."""
    import uuid
    dynamic_id = f"TC-SYNC-{uuid.uuid4().hex[:6]}"
    azure_devops_service.configure("realorg", "RealProject", "valid_pat")
    test_case_payload = {
        "id": dynamic_id,
        "requirement_ref": "US-2048 AC-1",
        "category": "Positive",
        "priority": "High",
        "scenario": "Verify valid user authentication",
        "description": "User submits valid username and password",
        "preconditions": "User is registered",
        "test_data": "user@example.com / Pass123",
        "test_steps": ["1. Open login page", "2. Enter credentials", "3. Click Login"],
        "expected_result": "Dashboard is displayed",
        "azure_work_item_id": "2048"
    }

    # First sync: POST to create test case work item in Azure DevOps
    create_resp = httpx.Response(
        status_code=200,
        json={"id": 45872},
        request=httpx.Request("POST", "https://dev.azure.com/realorg/RealProject/_apis/wit/workitems/$Test%20Case")
    )
    with patch("httpx.AsyncClient.post", return_value=create_resp):
        sync_req = {
            "test_cases": [test_case_payload],
            "work_item_id": "2048",
            "area_path": "RealProject\\Area A"
        }
        response = client.post("/api/v1/devops/azure/sync", json=sync_req, headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["synced_count"] == 1
        assert data["updated_count"] == 0
        assert data["test_cases"][0]["azure_test_case_id"] == 45872
        assert data["test_cases"][0]["sync_status"] == "Synced"

    # Second sync (edited test case with existing azure_test_case_id): PATCH to update work item #45872
    test_case_payload["azure_test_case_id"] = 45872
    test_case_payload["scenario"] = "Verify valid user authentication (Updated)"

    patch_resp = httpx.Response(
        status_code=200,
        json={"id": 45872},
        request=httpx.Request("PATCH", "https://dev.azure.com/realorg/RealProject/_apis/wit/workitems/45872")
    )
    with patch("httpx.AsyncClient.patch", return_value=patch_resp):
        sync_req = {
            "test_cases": [test_case_payload],
            "work_item_id": "2048",
            "area_path": "RealProject\\Area A"
        }
        response = client.post("/api/v1/devops/azure/sync", json=sync_req, headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["synced_count"] == 0
        assert data["updated_count"] == 1
        assert data["test_cases"][0]["azure_test_case_id"] == 45872
        assert data["test_cases"][0]["sync_status"] == "Updated"


def test_traceability_format_in_generation():
    """Verify Requirement 8: Test cases retain Azure DevOps Work Item ID (e.g. TC-2048-01)."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "2048",
        "user_story_ids": ["2048"],
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    positive_cases = data["positive_test_cases"]
    assert len(positive_cases) > 0
    first_tc = positive_cases[0]
    # Check traceability ID and azure_work_item_id
    assert first_tc["azure_work_item_id"] == "2048"
    assert first_tc["id"].startswith("TC-2048-")
    assert first_tc["sync_status"] == "Not Synced"
