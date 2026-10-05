import pytest
from app.models.application import Application
from app.schemas.devops import DevOpsWorkItem
from app.schemas.test_case import ApplicationLinkPayload
from app.services.test_generator import test_generator_engine
from app.services.web_extractor import web_extractor

@pytest.fixture
def sample_app():
    return Application(
        id=1,
        name="Enterprise QA Portal",
        description="Core enterprise application under test",
        user_roles="Standard User, Administrator",
        business_rules="All transactions must require valid authorization.\nAudit trail must log user actions."
    )

@pytest.fixture
def login_story():
    return DevOpsWorkItem(
        id="US-201",
        title="User Login Authentication",
        description="User should be able to log into the application using valid credentials.",
        acceptance_criteria="1. User inputs valid credentials.\n2. System authenticates user and redirects to dashboard.",
        work_item_type="User Story"
    )

def test_link_changes_output_differently(sample_app, login_story):
    """
    Req 14, 15, 23: Verify that providing different application links produces 
    meaningfully different test cases for the exact same User Story requirement.
    """
    # Application Link 1 Context (SauceDemo Login)
    sauce_ctx = {
        "name": "SauceDemo Login",
        "url": "https://www.saucedemo.com",
        "status": "success",
        "page_title": "Swag Labs Login",
        "detected_inputs": ["user-name", "password"],
        "detected_actions": ["Login"],
        "observed_errors": ["Epic sadface: Username is required"]
    }

    # Application Link 2 Context (CRM Portal Login)
    crm_ctx = {
        "name": "CRM Portal Login",
        "url": "https://crm.enterprise.com/login",
        "status": "success",
        "page_title": "CRM Enterprise Sign In",
        "detected_inputs": ["email_address", "security_pin"],
        "detected_actions": ["Sign In"],
        "observed_errors": ["Email address is required"]
    }

    # Generate test cases with Link 1
    res1 = test_generator_engine.generate_multi_requirement_test_suite(
        app=sample_app,
        stories=[login_story],
        selected_ac_filter=None,
        url_analyzed=True,
        page_contexts=[sauce_ctx]
    )

    # Generate test cases with Link 2
    res2 = test_generator_engine.generate_multi_requirement_test_suite(
        app=sample_app,
        stories=[login_story],
        selected_ac_filter=None,
        url_analyzed=True,
        page_contexts=[crm_ctx]
    )

    # Verify Link 1 test cases reflect SauceDemo context
    pos1_steps = " ".join(res1.positive_test_cases[0].test_steps)
    assert "user-name" in pos1_steps or "SauceDemo" in pos1_steps
    assert res1.positive_test_cases[0].application_link == "https://www.saucedemo.com"

    # Verify Link 2 test cases reflect CRM context
    pos2_steps = " ".join(res2.positive_test_cases[0].test_steps)
    assert "email_address" in pos2_steps or "CRM" in pos2_steps
    assert res2.positive_test_cases[0].application_link == "https://crm.enterprise.com/login"

    # Verify outputs are DIFFERENT (Requirement 15 & 23)
    assert pos1_steps != pos2_steps
    assert res1.positive_test_cases[0].scenario != res2.positive_test_cases[0].scenario


def test_multiple_application_links_workflow(sample_app, login_story):
    """
    Req 18: Multiple links provided across pages (Product -> Cart -> Checkout)
    should generate end-to-end multi-page workflow cases.
    """
    multi_contexts = [
        {
            "name": "Product Page",
            "url": "https://www.saucedemo.com/inventory.html",
            "status": "success",
            "page_title": "Products",
            "detected_inputs": ["add-to-cart-sauce-labs-backpack"],
            "detected_actions": ["Add to cart"]
        },
        {
            "name": "Cart Page",
            "url": "https://www.saucedemo.com/cart.html",
            "status": "success",
            "page_title": "Your Cart",
            "detected_inputs": ["cart-contents"],
            "detected_actions": ["Checkout"]
        },
        {
            "name": "Checkout Page",
            "url": "https://www.saucedemo.com/checkout-step-one.html",
            "status": "success",
            "page_title": "Checkout: Your Information",
            "detected_inputs": ["firstName", "lastName", "postalCode"],
            "detected_actions": ["Continue"]
        }
    ]

    res = test_generator_engine.generate_multi_requirement_test_suite(
        app=sample_app,
        stories=[login_story],
        selected_ac_filter=None,
        url_analyzed=True,
        page_contexts=multi_contexts
    )

    # Check for E2E multi-page workflow case
    e2e_cases = [tc for tc in res.positive_test_cases if "Multi-Page" in tc.scenario or "Journey" in tc.scenario]
    assert len(e2e_cases) > 0
    e2e = e2e_cases[0]
    assert "Product Page" in e2e.application_page
    assert "Cart Page" in e2e.application_page


def test_inaccessible_link_failure_handling(sample_app, login_story):
    """
    Req 20: Inaccessible link handling. System must not crash or invent false UI elements.
    Context should be marked unverified, and test generation proceeds safely.
    """
    failed_ctx = {
        "name": "Unreachable Page",
        "url": "https://invalid-host-9999.xyz/page",
        "status": "failed",
        "error": "HTTP status 404",
        "detected_inputs": [],
        "detected_actions": [],
        "page_title": "Unreachable Page"
    }

    res = test_generator_engine.generate_multi_requirement_test_suite(
        app=sample_app,
        stories=[login_story],
        selected_ac_filter=None,
        url_analyzed=False,
        url_message="Application links could not be accessed.",
        page_contexts=[failed_ctx]
    )

    assert len(res.positive_test_cases) > 0
    pos = res.positive_test_cases[0]
    # Check that preconditions state link could not be accessed
    assert "could not be accessed" in pos.preconditions or "unverified" in pos.preconditions


def test_traceability_fields_present(sample_app, login_story):
    """
    Req 21: Every generated test case must include complete traceability attributes.
    """
    res = test_generator_engine.generate_multi_requirement_test_suite(
        app=sample_app,
        stories=[login_story],
        selected_ac_filter=None,
        url_analyzed=True,
        page_contexts=[{
            "name": "SauceDemo Login",
            "url": "https://www.saucedemo.com",
            "status": "success",
            "page_title": "Swag Labs",
            "detected_inputs": ["user-name", "password"],
            "detected_actions": ["Login"]
        }]
    )

    all_cases = res.positive_test_cases + res.negative_test_cases + res.edge_test_cases
    assert len(all_cases) > 0

    for tc in all_cases:
        assert tc.id
        assert tc.user_story == login_story.id
        assert tc.acceptance_criteria
        assert tc.category in ("Positive", "Negative", "Edge")
        assert tc.priority in ("High", "Medium", "Low")
        assert tc.scenario
        assert tc.description
        assert tc.preconditions
        assert tc.test_data
        assert len(tc.test_steps) > 0
        assert tc.expected_result
