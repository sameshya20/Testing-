import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer test-token-admin"}

def test_generate_test_cases_scenario_b_no_link():
    """Scenario B: Application Link is NULL / Empty. System must NOT break and must generate test cases cleanly."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    
    assert "positive_test_cases" in data
    assert "negative_test_cases" in data
    assert "edge_test_cases" in data
    assert len(data["positive_test_cases"]) > 0
    assert len(data["negative_test_cases"]) > 0
    assert len(data["edge_test_cases"]) > 0
    assert data["coverage_summary"]["total_count"] > 0
    assert data["url_context_analyzed"] is False

def test_generate_test_cases_scenario_a_with_link():
    """Scenario A: Application Link is provided."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_url": "https://example.com"
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["positive_test_cases"]) > 0
    assert len(data["negative_test_cases"]) > 0
    assert len(data["edge_test_cases"]) > 0

def test_generate_test_cases_multiple_links():
    """Test creating test cases with multiple application links (general and requirement specific)."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifiers": ["US-101", "US-102"],
        "application_links": [
            {
                "name": "Login Page",
                "url": "https://example.com/login",
                "requirement_ref": "US-101"
            },
            {
                "name": "Dashboard",
                "url": "https://example.com/dashboard",
                "requirement_ref": "US-101"
            },
            {
                "name": "Payments",
                "url": "https://example.com/payments",
                "requirement_ref": "US-102"
            }
        ]
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    
    assert "positive_test_cases" in data
    assert len(data["positive_test_cases"]) > 0
    assert "coverage_summary" in data
    assert data["coverage_summary"]["total_count"] > 0
    assert data["coverage_summary"]["user_stories_count"] == 2
def test_link_based_output_variance():
    """Verify that different application links produce distinct page-aware test cases and steps."""
    payload_a = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_links": [
            {
                "name": "SauceDemo Login",
                "url": "https://www.saucedemo.com",
                "requirement_ref": "US-101"
            }
        ]
    }
    resp_a = client.post("/api/v1/generation/create", json=payload_a, headers=AUTH_HEADERS)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    case_a = data_a["positive_test_cases"][0]

    payload_b = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_links": [
            {
                "name": "Custom Corporate Portal",
                "url": "https://portal.enterprise.internal/app",
                "requirement_ref": "US-101"
            }
        ]
    }
    resp_b = client.post("/api/v1/generation/create", json=payload_b, headers=AUTH_HEADERS)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    case_b = data_b["positive_test_cases"][0]

    # Output MUST reflect the different application link details
    assert case_a["application_page"] == "SauceDemo Login"
    assert case_b["application_page"] == "Custom Corporate Portal"
    assert case_a["application_link"] != case_b["application_link"]

def test_generate_test_cases_single_service():
    """Verify test case generation with single service and area_id (backward compatibility)."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "service": "Payments",
        "area_id": 3
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["positive_test_cases"]) > 0

def test_generate_test_cases_multiple_services():
    """Verify test case generation with multiple services and area_ids."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifiers": ["US-101", "US-002"],
        "services": ["Payments", "Recruitment"],
        "area_ids": [3, 6]
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["positive_test_cases"]) > 0
    assert data["coverage_summary"]["user_stories_count"] == 2

def test_generate_test_cases_duplicate_services():
    """Verify duplicate services in payload are safely handled and deduplicated without error."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "services": ["Payments", "Payments"],
        "area_ids": [3, 3]
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["positive_test_cases"]) > 0


def test_expected_results_are_unique_and_not_generic():
    """Verify that generated test cases do not use generic expected result phrases and have unique, scenario-specific expected results."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    all_cases = data["positive_test_cases"] + data["negative_test_cases"] + data["edge_test_cases"]
    assert len(all_cases) > 0

    # Ensure no test case has the old generic phrase
    for tc in all_cases:
        assert "System accepts compliant payload without warnings" not in tc["expected_result"], f"Generic expected result found in {tc['id']}: {tc['expected_result']}"
        assert len(tc["expected_result"].strip()) > 15
        assert tc["expected_result"] != tc["scenario"]

    # Verify meaningful distribution across Positive, Negative, and Edge
    assert len(data["positive_test_cases"]) > 0, "Positive cases must be > 0"
    assert len(data["negative_test_cases"]) > 0, "Negative cases must be > 0"
    assert len(data["edge_test_cases"]) > 0, "Edge cases must be > 0"


def test_acceptance_criteria_selection_generates_positive_negative_edge():
    """Verify selecting Acceptance Criteria (with leading zeros format e.g. US-101-AC-01) produces positive, negative, and edge cases."""
    payload = {
        "application_id": 1,
        "requirement_source": "ACCEPTANCE_CRITERIA",
        "requirement_identifiers": ["US-101-AC-01", "US-101-AC-02"],
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    # Negative and Edge tabs must NOT be 0
    assert len(data["positive_test_cases"]) > 0, "Positive count must be > 0"
    assert len(data["negative_test_cases"]) > 0, "Negative count must be > 0"
    assert len(data["edge_test_cases"]) > 0, "Edge count must be > 0"
    assert data["coverage_summary"]["positive_count"] > 0
    assert data["coverage_summary"]["negative_count"] > 0
    assert data["coverage_summary"]["edge_count"] > 0


def test_business_rule_threshold_and_boundary_generation():
    """Verify that numerical threshold rules generate Positive, Negative, exact Edge, and just-above Edge cases."""
    payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifier": "US-101",
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    scenarios = [tc["scenario"] for tc in data["positive_test_cases"] + data["negative_test_cases"] + data["edge_test_cases"]]
    expected_results = [tc["expected_result"] for tc in data["positive_test_cases"] + data["negative_test_cases"] + data["edge_test_cases"]]

    scenarios_text = " ".join(scenarios)
    results_text = " ".join(expected_results)

    # 1. $10,000 threshold rule coverage
    assert "$10,000" in scenarios_text or "$10,000" in results_text
    # 2. $50,000 daily limit rule coverage
    assert "$50,000" in scenarios_text or "$50,000" in results_text
    # 3. Account active/non-frozen rule coverage
    assert "Frozen" in scenarios_text or "frozen" in results_text
    # 4. Session timeout rule coverage
    assert "15 minutes" in scenarios_text or "15 minutes" in results_text or "timeout" in results_text


def test_multi_user_story_generation():
    """Verify generating test cases for multiple user stories together."""
    payload = {
        "application_id": 1,
        "requirement_source": "ACCEPTANCE_CRITERIA",
        "user_story_ids": ["US-101", "US-102"],
        "requirement_identifiers": ["US-101-AC-01", "US-101-AC-02", "US-102-AC-01", "US-102-AC-02"],
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    # Coverage summary should show 2 user stories
    summary = data["coverage_summary"]
    assert summary["user_stories_count"] == 2
    assert "US-101" in summary["requirements_covered"]
    assert "US-102" in summary["requirements_covered"]

    # Test cases should include cases for both US-101 and US-102
    all_cases = data["positive_test_cases"] + data["negative_test_cases"] + data["edge_test_cases"]
    user_stories_in_cases = {tc.get("user_story") for tc in all_cases if tc.get("user_story")}
    assert "US-101" in user_stories_in_cases
    assert "US-102" in user_stories_in_cases

    # Verify no duplicate test case IDs within each category
    for cat in ["positive_test_cases", "negative_test_cases", "edge_test_cases"]:
        cat_ids = [tc["id"] for tc in data[cat]]
        assert len(cat_ids) == len(set(cat_ids)), f"Duplicate IDs found in {cat}"


def test_single_user_story_preservation():
    """Verify single user story selection workflow continues to work exactly as before."""
    payload = {
        "application_id": 1,
        "requirement_source": "ACCEPTANCE_CRITERIA",
        "user_story_ids": ["US-101"],
        "requirement_identifiers": ["US-101-AC-01", "US-101-AC-02"],
        "application_url": None
    }
    response = client.post("/api/v1/generation/create", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    summary = data["coverage_summary"]
    assert summary["user_stories_count"] == 1
    assert "US-101" in summary["requirements_covered"]
    assert len(data["positive_test_cases"]) > 0





