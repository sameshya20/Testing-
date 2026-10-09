from pydantic import BaseModel, Field
from typing import List, Optional

class ApplicationLinkPayload(BaseModel):
    name: Optional[str] = Field(default=None, description="Optional user-friendly link name e.g. Login Page")
    url: str = Field(..., description="Application URL e.g. https://example.com/login")
    requirement_ref: Optional[str] = Field(default=None, description="Optional association with specific requirement e.g. US-101")

class TestCase(BaseModel):
    __test__ = False
    id: str = Field(..., description="Unique Test Case ID e.g., TC-POS-001 or TC-1024-01")
    azure_work_item_id: Optional[str] = Field(None, description="Associated Azure DevOps Work Item / User Story ID e.g. 1024")
    azure_test_case_id: Optional[int] = Field(None, description="Synced Azure DevOps Test Case ID e.g. 45872")
    sync_status: Optional[str] = Field("Not Synced", description="Not Synced, Synced, Updated, Sync Failed")
    sync_message: Optional[str] = Field(None, description="Synchronization message or error details")
    requirement_ref: str = Field(..., description="Traceability Reference e.g. US-101 AC-1")
    user_story: Optional[str] = Field("", description="Associated User Story ID e.g. US-101")
    acceptance_criteria: Optional[str] = Field("", description="Associated Acceptance Criteria ID / text")
    application_page: Optional[str] = Field("", description="Associated Application Page name e.g. Login Page")
    application_link: Optional[str] = Field("", description="Associated Application Page URL")
    category: str = Field(..., description="Positive, Negative, or Edge")
    priority: str = Field("Medium", description="High, Medium, or Low")
    scenario: str = Field(..., description="Short title of the test scenario")
    description: str = Field(..., description="Detailed objective of the test case")
    preconditions: str = Field("User logged in with appropriate permissions", description="Prerequisites")
    test_data: str = Field("N/A", description="Specific test input values")
    test_steps: List[str] = Field(..., description="Step-by-step instructions")
    expected_result: str = Field(..., description="Expected system behavior")

class TestCaseGenerationRequest(BaseModel):
    __test__ = False
    application_id: int
    requirement_source: str = Field(..., description="USER_STORY or ACCEPTANCE_CRITERIA")
    requirement_identifiers: Optional[List[str]] = Field(default=[], description="List of User Story IDs or AC IDs")
    requirement_identifier: Optional[str] = Field(default=None, description="Single User Story ID or AC ID (backward compatibility)")
    user_story_ids: Optional[List[str]] = Field(default=[], description="List of selected User Story IDs")
    custom_requirement_text: Optional[str] = None
    application_links: Optional[List[ApplicationLinkPayload]] = Field(default=[], description="Multiple application links")
    application_url: Optional[str] = Field(default=None, description="Single link for backward compatibility")
    area_ids: Optional[List[int]] = Field(default=[], description="List of selected Area / Service IDs")
    area_id: Optional[int] = Field(default=None, description="Single Area / Service ID (backward compatibility)")
    services: Optional[List[str]] = Field(default=[], description="List of selected Service names")
    service: Optional[str] = Field(default=None, description="Single Service name (backward compatibility)")

class CoverageSummary(BaseModel):
    __test__ = False
    total_count: int
    positive_count: int
    negative_count: int
    edge_count: int
    user_stories_count: int = 0
    acceptance_criteria_count: int = 0
    application_pages_count: int = 0
    application_links_analyzed: List[str] = []
    requirements_covered: List[str]
    coverage_quality: str

class TestCaseGenerationResponse(BaseModel):
    __test__ = False
    positive_test_cases: List[TestCase]
    negative_test_cases: List[TestCase]
    edge_test_cases: List[TestCase]
    coverage_summary: CoverageSummary
    analysis_summary: str
    url_context_analyzed: bool
    url_analysis_message: Optional[str] = None

class ExportExcelRequest(BaseModel):
    positive_test_cases: List[TestCase]
    negative_test_cases: List[TestCase]
    edge_test_cases: List[TestCase]
    application_name: str
    requirement_ref: str


