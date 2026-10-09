import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.azure_devops import get_azure_devops_service
from app.db.session import SessionLocal
from app.models.test_case import TestCaseRecord

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token-admin"}


@pytest.fixture(autouse=True)
def ensure_mock_mode(monkeypatch):
    """Ensures mock mode is active for all mock service tests."""
    monkeypatch.setenv("AZURE_DEVOPS_MODE", "mock")
    settings.AZURE_DEVOPS_MODE = "mock"
    ado_service = get_azure_devops_service()
    ado_service.configure("DemoOrganization", "TestCaseDemoProject", "")
    db = SessionLocal()
    try:
        db.query(TestCaseRecord).filter(TestCaseRecord.id.like("TC-1001-%")).delete()
        db.commit()
    finally:
        db.close()
    yield
    settings.AZURE_DEVOPS_MODE = "mock"


def test_mock_connection_flow():
    """Requirement 4: Verify mock connection returns successful response without PAT."""
    payload = {
        "organization": "DemoOrganization",
        "project": "TestCaseDemoProject"
    }
    response = client.post("/api/v1/devops/azure/connect", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["organization"] == "DemoOrganization"
    assert data["project"] == "TestCaseDemoProject"
    assert data["mode"] == "mock"
    assert len(data["projects"]) >= 3
    proj_names = [p["name"] for p in data["projects"]]
    assert "TestCaseDemoProject" in proj_names


def test_mock_config_endpoint():
    """Verify config endpoint reflects mock mode and never leaks PAT."""
    response = client.get("/api/v1/devops/azure/config", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["organization"] == "DemoOrganization"
    assert data["project"] == "TestCaseDemoProject"
    assert data["connected"] is True
    assert data["mode"] == "mock"
    assert "pat" not in data


def test_mock_projects_endpoint():
    """Requirement 5: Verify mock projects endpoint exposes realistic project data."""
    response = client.get("/api/v1/devops/azure/projects", headers=AUTH_HEADERS)
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 3
    names = [p["name"] for p in projects]
    assert "TestCaseDemoProject" in names
    assert "EnterpriseCommercePlatform" in names
    assert "HealthcareClaimsSystem" in names


def test_mock_areas_endpoint():
    """Requirement 6: Verify Select Area retrieves mock areas with ID, Name, and Path."""
    response = client.get("/api/v1/devops/azure/areas?project=TestCaseDemoProject", headers=AUTH_HEADERS)
    assert response.status_code == 200
    areas = response.json()
    assert len(areas) >= 5

    names = [a["name"] for a in areas]
    assert "Authentication" in names
    assert "User Management" in names
    assert "Dashboard" in names
    assert "Payments" in names
    assert "Reports" in names

    auth_area = next(a for a in areas if a["name"] == "Authentication")
    assert auth_area["id"] == 101
    assert "Application\\Authentication" in auth_area["path"]
    assert auth_area["parent_id"] == 100


def test_mock_query_work_items_filtering():
    """Requirement 7 & 8: Verify mock WIQL querying with area and search filtering."""
    # 1. Filter by Authentication Area
    res_area = client.get(
        "/api/v1/devops/azure/work-items?area_path=Application\\Authentication&project=TestCaseDemoProject",
        headers=AUTH_HEADERS
    )
    assert res_area.status_code == 200
    items = res_area.json()
    assert len(items) >= 3
    titles = [item["title"] for item in items]
    assert "User Login with Valid Credentials" in titles
    assert "Password Reset via Email Verification" in titles
    assert "Account Lockout After Failed Attempts" in titles

    # 2. Filter by search query
    res_search = client.get(
        "/api/v1/devops/azure/work-items?search=Lockout&project=TestCaseDemoProject",
        headers=AUTH_HEADERS
    )
    assert res_search.status_code == 200
    search_items = res_search.json()
    assert len(search_items) == 1
    assert search_items[0]["id"] == "1003"
    assert "Account Lockout After Failed Attempts" in search_items[0]["title"]


def test_mock_wiql_alias_endpoints():
    """Requirement 8: Verify GET and POST /api/v1/azure-devops/work-items endpoints."""
    # GET alias
    get_res = client.get(
        "/api/v1/azure-devops/work-items?area_path=Authentication",
        headers=AUTH_HEADERS
    )
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 3

    # POST alias
    post_res = client.post(
        "/api/v1/azure-devops/work-items",
        json={"area_path": "Authentication", "work_item_type": "User Story"},
        headers=AUTH_HEADERS
    )
    assert post_res.status_code == 200
    assert len(post_res.json()) >= 3


def test_mock_work_item_details():
    """Requirement 9: Retrieve complete details for mock User Story #1001."""
    response = client.get("/api/v1/devops/azure/work-items/1001?project=TestCaseDemoProject", headers=AUTH_HEADERS)
    assert response.status_code == 200
    story = response.json()
    assert story["id"] == "1001"
    assert story["title"] == "User Login with Valid Credentials"
    assert "The user should be able to log in using valid credentials" in story["description"]
    assert "User enters registered email" in story["acceptance_criteria"]
    assert "User enters correct password" in story["acceptance_criteria"]
    assert "User is successfully authenticated" in story["acceptance_criteria"]
    assert "User is redirected to dashboard" in story["acceptance_criteria"]
    assert story["state"] == "Active"
    assert "Application\\Authentication" in story["area_path"]


def test_mock_test_case_generation_and_traceability():
    """Requirement 10, 11, 12: Generate test cases from User Story #1001 maintaining traceability."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "user_story_ids": ["1001"],
        "requirement_identifiers": ["1001"]
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    pos_cases = data["positive_test_cases"]
    neg_cases = data["negative_test_cases"]
    edge_cases = data["edge_test_cases"]

    assert len(pos_cases) > 0
    assert len(neg_cases) > 0
    assert len(edge_cases) > 0

    all_cases = pos_cases + neg_cases + edge_cases
    # Verify ID format TC-1001-01, TC-1001-02...
    for tc in all_cases:
        assert tc["id"].startswith("TC-1001-")
        assert tc["azure_work_item_id"] == "1001"
        assert tc["sync_status"] == "Not Synced"


def test_mock_sync_and_duplicate_prevention():
    """Requirement 13, 14, 15: Verify Sync to Mock ADO, ID assignment, and duplicate prevention."""
    test_case_payload = {
        "id": "TC-1001-01",
        "requirement_ref": "1001-AC-01",
        "user_story": "1001",
        "azure_work_item_id": "1001",
        "category": "Positive",
        "priority": "High",
        "scenario": "Verify valid user authentication",
        "description": "User enters correct credentials",
        "preconditions": "User has active account",
        "test_data": "user=test@enterprise.com",
        "test_steps": ["1. Navigate to login", "2. Submit valid credentials"],
        "expected_result": "User lands on dashboard"
    }

    # 1. FIRST SYNC: Creates new mock test case in ADO
    sync_payload = {
        "test_cases": [test_case_payload],
        "work_item_id": "1001",
        "area_path": "TestCaseDemoProject\\Application\\Authentication",
        "project": "TestCaseDemoProject"
    }
    res_1 = client.post("/api/v1/devops/azure/sync", json=sync_payload, headers=AUTH_HEADERS)
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["success"] is True
    assert data_1["synced_count"] == 1
    assert data_1["updated_count"] == 0

    synced_tc = data_1["test_cases"][0]
    ado_id_1 = synced_tc["azure_test_case_id"]
    assert ado_id_1 >= 50001
    assert synced_tc["sync_status"] == "Synced"

    # Verify persisted in local DB
    db = SessionLocal()
    db_rec = db.query(TestCaseRecord).filter(TestCaseRecord.id == "TC-1001-01").first()
    assert db_rec is not None
    assert db_rec.azure_test_case_id == ado_id_1
    assert db_rec.sync_status == "Synced"
    db.close()

    # 2. SECOND SYNC: Must UPDATE existing test case without creating a duplicate!
    test_case_payload_update = {
        **test_case_payload,
        "azure_test_case_id": ado_id_1,  # Existing ADO ID
        "scenario": "Verify valid user authentication (Updated steps)"
    }
    sync_payload_2 = {
        "test_cases": [test_case_payload_update],
        "work_item_id": "1001",
        "area_path": "TestCaseDemoProject\\Application\\Authentication",
        "project": "TestCaseDemoProject"
    }
    res_2 = client.post("/api/v1/devops/azure/sync", json=sync_payload_2, headers=AUTH_HEADERS)
    assert res_2.status_code == 200
    data_2 = res_2.json()
    assert data_2["success"] is True
    assert data_2["synced_count"] == 0
    assert data_2["updated_count"] == 1  # Successfully updated existing!

    updated_tc = data_2["test_cases"][0]
    assert updated_tc["azure_test_case_id"] == ado_id_1  # Same ADO ID, NOT 50002!
    assert updated_tc["sync_status"] == "Updated"

    # 3. SYNC A SECOND NEW TEST CASE: Should get the NEXT ADO ID (50002)
    test_case_2 = {
        "id": "TC-1001-02",
        "requirement_ref": "1001-AC-02",
        "user_story": "1001",
        "azure_work_item_id": "1001",
        "category": "Negative",
        "priority": "Medium",
        "scenario": "Verify login rejection with incorrect password",
        "description": "User enters invalid password",
        "preconditions": "Account exists",
        "test_data": "user=test@enterprise.com, pass=wrong",
        "test_steps": ["1. Submit wrong password"],
        "expected_result": "System presents error message"
    }
    sync_payload_3 = {
        "test_cases": [test_case_2],
        "work_item_id": "1001",
        "area_path": "TestCaseDemoProject\\Application\\Authentication",
        "project": "TestCaseDemoProject"
    }
    res_3 = client.post("/api/v1/devops/azure/sync", json=sync_payload_3, headers=AUTH_HEADERS)
    assert res_3.status_code == 200
    data_3 = res_3.json()
    assert data_3["synced_count"] == 1
    ado_id_2 = data_3["test_cases"][0]["azure_test_case_id"]
    assert ado_id_2 != ado_id_1
    assert ado_id_2 > ado_id_1
