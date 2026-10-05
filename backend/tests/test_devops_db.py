import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer test-token-admin"}

def test_get_areas():
    response = client.get("/api/v1/devops/areas", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "code" in data[0]

def test_get_user_stories_by_area():
    # Get first area
    areas_resp = client.get("/api/v1/devops/areas", headers=AUTH_HEADERS)
    area_id = areas_resp.json()[0]["id"]
    
    response = client.get(f"/api/v1/devops/areas/{area_id}/user-stories", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "title" in data[0]
    assert "area_id" in data[0]

def test_get_acceptance_criteria_by_user_story():
    # Get user stories for area 1
    areas_resp = client.get("/api/v1/devops/areas", headers=AUTH_HEADERS)
    area_id = areas_resp.json()[0]["id"]
    stories_resp = client.get(f"/api/v1/devops/areas/{area_id}/user-stories", headers=AUTH_HEADERS)
    story_id = stories_resp.json()[0]["id"]

    response = client.get(f"/api/v1/devops/user-stories/{story_id}/acceptance-criteria", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "text" in data[0]
    assert "criteria_number" in data[0]

def test_unauthorized_access():
    response = client.get("/api/v1/devops/areas")
    assert response.status_code == 401

def test_get_user_stories_by_multiple_area_ids():
    response = client.get("/api/v1/devops/areas/multi/user-stories?area_ids=3&area_ids=6", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_user_stories_by_services_query():
    response = client.get("/api/v1/devops/areas/multi/user-stories?services=Payments&services=Recruitment", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_multi_user_stories_acceptance_criteria():
    response = client.get(
        "/api/v1/devops/user-stories/multi/acceptance-criteria?story_ids=US-101&story_ids=US-102",
        headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    # Check criteria belong to both US-101 and US-102
    story_ids_in_data = {c["user_story_id"] for c in data}
    assert "US-101" in story_ids_in_data
    assert "US-102" in story_ids_in_data

    # Check for no duplicate criteria IDs
    ids_in_data = [c["id"] for c in data]
    assert len(ids_in_data) == len(set(ids_in_data)), "No duplicate criteria IDs allowed"

def test_full_flow_multiple_user_stories_generation_and_export():
    """Verify complete flow: Area -> Multiple User Stories -> Grouped Acceptance Criteria -> Generate -> Excel Export."""
    # 1. Fetch User Stories for Payments Area (id=3 or code=AREA-BANK-PAYMENTS)
    areas_resp = client.get("/api/v1/devops/areas", headers=AUTH_HEADERS)
    assert areas_resp.status_code == 200
    payments_area = next((a for a in areas_resp.json() if "PAYMENT" in a["code"].upper() or a["name"] == "Payments"), None)
    assert payments_area is not None

    stories_resp = client.get(f"/api/v1/devops/areas/{payments_area['id']}/user-stories", headers=AUTH_HEADERS)
    assert stories_resp.status_code == 200
    stories = stories_resp.json()
    assert len(stories) >= 2, "Expected at least 2 stories in Payments area"

    # Select multiple User Stories: US-101 and US-102
    selected_story_ids = ["US-101", "US-102"]
    
    # 2. Fetch grouped Acceptance Criteria for the selected stories
    query_str = "&".join(f"story_ids={sid}" for sid in selected_story_ids)
    criteria_resp = client.get(f"/api/v1/devops/user-stories/multi/acceptance-criteria?{query_str}", headers=AUTH_HEADERS)
    assert criteria_resp.status_code == 200
    criteria_list = criteria_resp.json()
    assert len(criteria_list) >= 4, "Expected criteria for both stories"

    # Verify criteria belong to both stories and have no duplicate IDs
    crits_by_story = {}
    for crit in criteria_list:
        sid = crit["user_story_id"].upper()
        crits_by_story.setdefault(sid, []).append(crit)
    assert "US-101" in crits_by_story
    assert "US-102" in crits_by_story
    all_crit_ids = [c["id"] for c in criteria_list]
    assert len(all_crit_ids) == len(set(all_crit_ids)), "Duplicate criteria detected!"

    # 3. Generate Test Cases with selected User Stories and Acceptance Criteria from both stories
    selected_crit_ids = [
        crits_by_story["US-101"][0]["id"],
        crits_by_story["US-101"][1]["id"],
        crits_by_story["US-102"][0]["id"],
        crits_by_story["US-102"][1]["id"]
    ]
    gen_payload = {
        "application_id": 1,
        "requirement_source": "ACCEPTANCE_CRITERIA",
        "user_story_ids": selected_story_ids,
        "requirement_identifiers": selected_crit_ids,
        "area_ids": [payments_area["id"]]
    }
    gen_resp = client.post("/api/v1/generation/create", json=gen_payload, headers=AUTH_HEADERS)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()

    # Check coverage summary
    summary = gen_data["coverage_summary"]
    assert summary["user_stories_count"] == 2
    assert "US-101" in summary["requirements_covered"]
    assert "US-102" in summary["requirements_covered"]
    assert summary["positive_count"] > 0
    assert summary["negative_count"] > 0
    assert summary["edge_count"] > 0

    # Verify test cases exist for both stories without duplicate IDs
    all_test_cases = gen_data["positive_test_cases"] + gen_data["negative_test_cases"] + gen_data["edge_test_cases"]
    stories_represented = {tc.get("user_story") for tc in all_test_cases if tc.get("user_story")}
    assert "US-101" in stories_represented
    assert "US-102" in stories_represented

    # Ensure no duplicate test case IDs within categories
    for cat in ["positive_test_cases", "negative_test_cases", "edge_test_cases"]:
        c_ids = [tc["id"] for tc in gen_data[cat]]
        assert len(c_ids) == len(set(c_ids)), f"Duplicate IDs in {cat}"

    # 4. Excel Export
    export_payload = {
        "positive_test_cases": gen_data["positive_test_cases"],
        "negative_test_cases": gen_data["negative_test_cases"],
        "edge_test_cases": gen_data["edge_test_cases"],
        "application_name": "Enterprise Banking Portal",
        "requirement_ref": "US-101, US-102"
    }
    export_resp = client.post("/api/v1/export/excel", json=export_payload, headers=AUTH_HEADERS)
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Test_Suite_US-101_US-102.xlsx" in export_resp.headers.get("content-disposition", "")
    assert len(export_resp.content) > 1000, "Excel binary content must be non-empty"

def test_full_flow_single_user_story_preservation():
    """Verify that selecting only a single user story continues to work exactly as before."""
    gen_payload = {
        "application_id": 1,
        "requirement_source": "ACCEPTANCE_CRITERIA",
        "user_story_ids": ["US-101"],
        "requirement_identifiers": ["US-101-AC-01", "US-101-AC-02"]
    }
    gen_resp = client.post("/api/v1/generation/create", json=gen_payload, headers=AUTH_HEADERS)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()

    summary = gen_data["coverage_summary"]
    assert summary["user_stories_count"] == 1
    assert "US-101" in summary["requirements_covered"]
    assert summary["positive_count"] > 0


