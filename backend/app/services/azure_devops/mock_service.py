import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.schemas.devops import (
    DevOpsWorkItem,
    AzureDevOpsProjectItem,
    AzureDevOpsAreaItem
)
from app.services.azure_devops.interface import AzureDevOpsService

logger = logging.getLogger(__name__)

# ============================================================================
# REALISTIC MOCK AZURE DEVOPS REPOSITORY
# ============================================================================

MOCK_PROJECTS: List[Dict[str, Any]] = [
    {
        "id": "proj-101",
        "name": "TestCaseDemoProject",
        "description": "Enterprise QA Application-Link-Aware Test Case Demonstration Project",
        "state": "wellFormed"
    },
    {
        "id": "proj-102",
        "name": "EnterpriseCommercePlatform",
        "description": "Global Retail, Shopping Cart, and Payment Gateway Platform",
        "state": "wellFormed"
    },
    {
        "id": "proj-103",
        "name": "HealthcareClaimsSystem",
        "description": "Medical Claims Submission, Adjudication, and Compliance Portal",
        "state": "wellFormed"
    }
]

# Areas structure:
# Application
# ├── Authentication
# ├── User Management
# ├── Dashboard
# ├── Payments
# └── Reports
MOCK_AREAS: List[Dict[str, Any]] = [
    {
        "id": 100,
        "name": "Application",
        "code": "AREA-APP-ROOT",
        "path_suffix": "Application",
        "parent_id": None
    },
    {
        "id": 101,
        "name": "Authentication",
        "code": "AREA-AUTH",
        "path_suffix": "Application\\Authentication",
        "parent_id": 100
    },
    {
        "id": 102,
        "name": "User Management",
        "code": "AREA-USER-MGT",
        "path_suffix": "Application\\User Management",
        "parent_id": 100
    },
    {
        "id": 103,
        "name": "Dashboard",
        "code": "AREA-DASHBOARD",
        "path_suffix": "Application\\Dashboard",
        "parent_id": 100
    },
    {
        "id": 104,
        "name": "Payments",
        "code": "AREA-PAYMENTS",
        "path_suffix": "Application\\Payments",
        "parent_id": 100
    },
    {
        "id": 105,
        "name": "Reports",
        "code": "AREA-REPORTS",
        "path_suffix": "Application\\Reports",
        "parent_id": 100
    }
]

# Realistic Mock User Stories / Work Items
MOCK_STORIES_DATA: List[Dict[str, Any]] = [
    {
        "id": "1001",
        "title": "User Login with Valid Credentials",
        "work_item_type": "User Story",
        "area_name": "Authentication",
        "area_suffix": "Application\\Authentication",
        "iteration_suffix": "Sprint 1",
        "description": "The user should be able to log in using valid credentials.",
        "acceptance_criteria": (
            "1. User enters registered email\n"
            "2. User enters correct password\n"
            "3. User is successfully authenticated\n"
            "4. User is redirected to dashboard"
        ),
        "state": "Active",
        "assigned_to": "Authentication Squad",
        "tags": ["Authentication", "Security", "Sprint 1"]
    },
    {
        "id": "1002",
        "title": "Password Reset via Email Verification",
        "work_item_type": "User Story",
        "area_name": "Authentication",
        "area_suffix": "Application\\Authentication",
        "iteration_suffix": "Sprint 1",
        "description": "As a registered user, I want to reset my forgotten password via a secure email verification link so that I can regain access to my account.",
        "acceptance_criteria": (
            "1. User submits registered email address on password reset form\n"
            "2. System dispatches single-use password reset link with 15-minute expiration\n"
            "3. Clicking expired link displays error and prompts new request\n"
            "4. New password must satisfy 12-character complexity rules"
        ),
        "state": "Active",
        "assigned_to": "Security Squad",
        "tags": ["Authentication", "Password", "Email"]
    },
    {
        "id": "1003",
        "title": "Account Lockout After Failed Attempts",
        "work_item_type": "User Story",
        "area_name": "Authentication",
        "area_suffix": "Application\\Authentication",
        "iteration_suffix": "Sprint 1",
        "description": "The system should protect against brute-force attacks by locking user accounts after repeated invalid password attempts.",
        "acceptance_criteria": (
            "1. System tracks consecutive failed login attempts per account\n"
            "2. Account locks for 30 minutes after 5 consecutive failures\n"
            "3. System displays security alert without disclosing password validity\n"
            "4. Support administrator can manually unlock verified accounts"
        ),
        "state": "Active",
        "assigned_to": "Security Squad",
        "tags": ["Security", "Lockout", "BruteForce"]
    },
    {
        "id": "1004",
        "title": "User Role & Permission Management",
        "work_item_type": "User Story",
        "area_name": "User Management",
        "area_suffix": "Application\\User Management",
        "iteration_suffix": "Sprint 2",
        "description": "Administrators should be able to manage user accounts, assign roles, and revoke permissions across the organization.",
        "acceptance_criteria": (
            "1. Administrator can view searchable table of active enterprise users\n"
            "2. Administrator can assign roles: SuperAdmin, QA Engineer, Operator, Viewer\n"
            "3. Permission modifications take effect upon next user API action\n"
            "4. Deactivating user immediately terminates all active web sessions"
        ),
        "state": "Active",
        "assigned_to": "User Admin Team",
        "tags": ["User Management", "RBAC", "Permissions"]
    },
    {
        "id": "1005",
        "title": "Personalized Executive Dashboard & KPIs",
        "work_item_type": "User Story",
        "area_name": "Dashboard",
        "area_suffix": "Application\\Dashboard",
        "iteration_suffix": "Sprint 2",
        "description": "Authenticated users should view personalized metrics, active test suites, and system health status cards.",
        "acceptance_criteria": (
            "1. Dashboard metrics render dynamically according to user role\n"
            "2. Live test execution counters refresh every 60 seconds\n"
            "3. Weekly test pass/fail trend charts render within 1.5 seconds\n"
            "4. Quick-action shortcuts allow one-click test case generation"
        ),
        "state": "Active",
        "assigned_to": "Core UI Squad",
        "tags": ["Dashboard", "Analytics", "KPI"]
    },
    {
        "id": "1006",
        "title": "Secure Multi-Factor Payment Processing",
        "work_item_type": "User Story",
        "area_name": "Payments",
        "area_suffix": "Application\\Payments",
        "iteration_suffix": "Sprint 3",
        "description": "Online banking customers should be able to transfer funds and process transactions with mandatory multi-factor verification for threshold limits.",
        "acceptance_criteria": (
            "1. Given active checking account, customer can initiate funds transfer\n"
            "2. Given transfer amount exceeding $10,000, secondary OTP verification is required\n"
            "3. Invalid OTP entered 3 times blocks the transaction and alerts fraud monitoring\n"
            "4. Successful payment debits account immediately and issues immutable reference number"
        ),
        "state": "Active",
        "assigned_to": "Payment Services Squad",
        "tags": ["Payments", "MFA", "Finance"]
    },
    {
        "id": "1007",
        "title": "Automated QA Test Execution Audit Report",
        "work_item_type": "User Story",
        "area_name": "Reports",
        "area_suffix": "Application\\Reports",
        "iteration_suffix": "Sprint 3",
        "description": "Generate compliance-ready test execution audit reports downloadable in formatted Excel workbooks with full traceability to requirements.",
        "acceptance_criteria": (
            "1. Report aggregates Positive, Negative, and Edge test case outcomes\n"
            "2. Full traceability links each test case to source User Story and Area Path\n"
            "3. Downloadable spreadsheet features freeze panes, headers, and priority coloring\n"
            "4. Filter audit reports by date range, priority, and application module"
        ),
        "state": "Active",
        "assigned_to": "Reporting Engine Squad",
        "tags": ["Reports", "Audit", "Excel", "Compliance"]
    }
]


class MockAzureDevOpsService(AzureDevOpsService):
    """
    Local Mock Azure DevOps Service implementing the full AzureDevOpsService contract.
    Behaves identically to an external Azure DevOps integration from the application's perspective,
    without requiring real Microsoft Azure credentials or subscriptions.
    """

    def __init__(self):
        self._org: str = settings.AZURE_DEVOPS_ORG or "DemoOrganization"
        self._project: str = settings.AZURE_DEVOPS_PROJECT or "TestCaseDemoProject"
        self._pat: str = ""
        # Default connected in mock mode for development convenience
        self._connected: bool = True
        
        # Local mock store for synced ADO test cases (persists during process lifetime)
        # Key: int ADO ID -> Dict test case data
        self._mock_ado_test_cases: Dict[int, Dict[str, Any]] = {}
        self._next_ado_id: int = 50001

    @property
    def mode(self) -> str:
        return "mock"

    @property
    def organization(self) -> str:
        return self._org

    @property
    def project(self) -> str:
        return self._project

    @property
    def pat(self) -> str:
        return ""  # Not needed in mock mode

    @property
    def is_connected(self) -> bool:
        return self._connected

    def configure(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> None:
        if organization is not None:
            clean_org = organization.strip()
            if "dev.azure.com/" in clean_org:
                clean_org = clean_org.split("dev.azure.com/")[-1].split("/")[0]
            self._org = clean_org or "DemoOrganization"
        if project is not None:
            self._project = project.strip() or "TestCaseDemoProject"
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def reload_from_env(self) -> None:
        import os
        from dotenv import load_dotenv
        backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
        if os.path.exists(backend_env):
            load_dotenv(dotenv_path=backend_env, override=False)
        self._org = os.getenv("AZURE_DEVOPS_ORG") or os.getenv("ADO_ORGANIZATION") or self._org or "DemoOrganization"
        self._project = os.getenv("AZURE_DEVOPS_PROJECT") or os.getenv("ADO_PROJECT") or self._project or "TestCaseDemoProject"

    async def test_connection(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> Tuple[bool, str, List[AzureDevOpsProjectItem]]:
        target_org = organization.strip() if organization else self._org
        target_proj = project.strip() if project else self._project

        if not target_org:
            target_org = "DemoOrganization"
        if not target_proj:
            target_proj = "TestCaseDemoProject"

        self._org = target_org
        self._project = target_proj
        self._connected = True

        projects = await self.get_projects()
        msg = f"Connected to Azure DevOps organization '{target_org}' and project '{target_proj}' (Development / Mock Mode)."
        return True, msg, projects

    async def get_projects(self) -> List[AzureDevOpsProjectItem]:
        projects: List[AzureDevOpsProjectItem] = []
        for p in MOCK_PROJECTS:
            projects.append(
                AzureDevOpsProjectItem(
                    id=p["id"],
                    name=p["name"],
                    description=p["description"],
                    state=p["state"]
                )
            )
        # Ensure active project is represented in list
        if self._project and not any(p.name.lower() == self._project.lower() for p in projects):
            projects.insert(
                0,
                AzureDevOpsProjectItem(
                    id=f"proj-{len(projects)+101}",
                    name=self._project,
                    description=f"Active Project: {self._project}",
                    state="wellFormed"
                )
            )
        return projects

    async def get_areas(self, project: Optional[str] = None) -> List[AzureDevOpsAreaItem]:
        target_proj = project or self._project or "TestCaseDemoProject"
        
        # Build tree representation
        root_children: List[AzureDevOpsAreaItem] = []
        for a in MOCK_AREAS:
            if a["parent_id"] == 100:
                root_children.append(
                    AzureDevOpsAreaItem(
                        id=a["id"],
                        name=a["name"],
                        path=f"{target_proj}\\{a['path_suffix']}",
                        has_children=False,
                        children=[]
                    )
                )

        root_area = AzureDevOpsAreaItem(
            id=100,
            name="Application",
            path=f"{target_proj}\\Application",
            has_children=True,
            children=root_children
        )
        return [root_area]

    async def get_flat_areas(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        target_proj = project or self._project or "TestCaseDemoProject"
        result: List[Dict[str, Any]] = []
        for a in MOCK_AREAS:
            full_path = f"{target_proj}\\{a['path_suffix']}"
            result.append({
                "id": a["id"],
                "name": a["name"],
                "code": a["code"],
                "path": full_path,
                "parent_id": a["parent_id"]
            })
        return result

    async def query_work_items(
        self,
        project: Optional[str] = None,
        area_path: Optional[str] = None,
        work_item_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[DevOpsWorkItem]:
        target_proj = project or self._project or "TestCaseDemoProject"
        items: List[DevOpsWorkItem] = []

        norm_area = area_path.lower().strip() if area_path else None
        norm_type = work_item_type.lower().strip() if work_item_type else None
        norm_search = search.lower().strip() if search else None

        for s in MOCK_STORIES_DATA:
            full_area = f"{target_proj}\\{s['area_suffix']}"
            full_iteration = f"{target_proj}\\{s['iteration_suffix']}"

            # Filter by work item type if specified
            if norm_type and s["work_item_type"].lower() != norm_type:
                continue

            # Filter by Area Path if specified
            if norm_area:
                # Match against area_name, suffix, or full path
                area_match = (
                    norm_area in full_area.lower() or
                    s["area_name"].lower() == norm_area or
                    norm_area in s["area_name"].lower() or
                    s["area_suffix"].lower() in norm_area or
                    norm_area in s["area_suffix"].lower()
                )
                if not area_match:
                    continue

            # Filter by search query if specified
            if norm_search:
                content_match = (
                    norm_search in s["id"].lower() or
                    norm_search in s["title"].lower() or
                    norm_search in s["description"].lower() or
                    norm_search in s["acceptance_criteria"].lower() or
                    any(norm_search in t.lower() for t in s.get("tags", []))
                )
                if not content_match:
                    continue

            items.append(
                DevOpsWorkItem(
                    id=s["id"],
                    title=s["title"],
                    work_item_type=s["work_item_type"],
                    description=s["description"],
                    acceptance_criteria=s["acceptance_criteria"],
                    state=s["state"],
                    assigned_to=s["assigned_to"],
                    area_path=full_area,
                    iteration_path=full_iteration,
                    tags=s.get("tags", [])
                )
            )

            if len(items) >= limit:
                break

        return items

    async def get_single_work_item(
        self,
        work_item_id: str,
        project: Optional[str] = None
    ) -> Optional[DevOpsWorkItem]:
        target_proj = project or self._project or "TestCaseDemoProject"
        clean_id = work_item_id.strip().replace("#", "").upper()
        # Also handle potential prefixes like US-1001 or US-101
        numeric_id = ''.join(filter(str.isdigit, clean_id))

        for s in MOCK_STORIES_DATA:
            if s["id"].upper() == clean_id or s["id"] == numeric_id or f"US-{s['id']}".upper() == clean_id:
                full_area = f"{target_proj}\\{s['area_suffix']}"
                full_iteration = f"{target_proj}\\{s['iteration_suffix']}"
                return DevOpsWorkItem(
                    id=s["id"],
                    title=s["title"],
                    work_item_type=s["work_item_type"],
                    description=s["description"],
                    acceptance_criteria=s["acceptance_criteria"],
                    state=s["state"],
                    assigned_to=s["assigned_to"],
                    area_path=full_area,
                    iteration_path=full_iteration,
                    tags=s.get("tags", [])
                )

        # Fallback dynamic mock item for unknown numeric IDs (e.g. #2001)
        if numeric_id:
            full_area = f"{target_proj}\\Application\\Authentication"
            full_iteration = f"{target_proj}\\Sprint 1"
            return DevOpsWorkItem(
                id=numeric_id,
                title=f"User Story #{numeric_id} - Functional Requirement",
                work_item_type="User Story",
                description=f"Specification for Work Item #{numeric_id}. Enforces validation, authorization, and data processing.",
                acceptance_criteria=(
                    f"1. System must validate user inputs for Story #{numeric_id}\n"
                    f"2. Authorized user role must execute transaction successfully\n"
                    f"3. Invalid data or boundary violations must present clear business error messages\n"
                    f"4. Successful transactions must persist audit records in database"
                ),
                state="Active",
                assigned_to="QA Team",
                area_path=full_area,
                iteration_path=full_iteration,
                tags=["User Story", "Mock"]
            )

        return None

    async def create_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        target_proj = project or self._project or "TestCaseDemoProject"
        resolved_parent = str(parent_work_item_id or tc_data.get("azure_work_item_id") or tc_data.get("user_story") or "1001")
        clean_parent = ''.join(filter(str.isdigit, resolved_parent)) or resolved_parent

        new_ado_id = self._next_ado_id
        self._next_ado_id += 1

        mock_record = {
            "id": new_ado_id,
            "title": f"[{tc_data.get('category', 'Positive')}] {tc_data.get('scenario', 'Test Case')}",
            "description": tc_data.get("description", ""),
            "priority": tc_data.get("priority", "Medium"),
            "steps": tc_data.get("test_steps", []),
            "expected_result": tc_data.get("expected_result", ""),
            "parent_work_item_id": clean_parent,
            "area_path": area_path or f"{target_proj}\\Application",
            "project": target_proj,
            "synced_at": datetime.utcnow().isoformat()
        }
        self._mock_ado_test_cases[new_ado_id] = mock_record

        updated_tc = {
            **tc_data,
            "azure_test_case_id": new_ado_id,
            "azure_work_item_id": clean_parent,
            "azure_project_id": target_proj,
            "azure_area_path": area_path or f"{target_proj}\\Application",
            "sync_status": "Synced",
            "sync_message": f"Successfully created in Mock Azure DevOps #{new_ado_id}"
        }

        # Persist to local database
        if db is not None:
            self._persist_to_db(updated_tc, db)

        return updated_tc

    async def update_test_case(
        self,
        existing_ado_id: int,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        target_proj = project or self._project or "TestCaseDemoProject"
        resolved_parent = str(parent_work_item_id or tc_data.get("azure_work_item_id") or tc_data.get("user_story") or "1001")
        clean_parent = ''.join(filter(str.isdigit, resolved_parent)) or resolved_parent

        # Update in memory mock store
        self._mock_ado_test_cases[existing_ado_id] = {
            "id": existing_ado_id,
            "title": f"[{tc_data.get('category', 'Positive')}] {tc_data.get('scenario', 'Test Case')}",
            "description": tc_data.get("description", ""),
            "priority": tc_data.get("priority", "Medium"),
            "steps": tc_data.get("test_steps", []),
            "expected_result": tc_data.get("expected_result", ""),
            "parent_work_item_id": clean_parent,
            "area_path": area_path or f"{target_proj}\\Application",
            "project": target_proj,
            "updated_at": datetime.utcnow().isoformat()
        }

        updated_tc = {
            **tc_data,
            "azure_test_case_id": existing_ado_id,
            "azure_work_item_id": clean_parent,
            "azure_project_id": target_proj,
            "azure_area_path": area_path or f"{target_proj}\\Application",
            "sync_status": "Updated",
            "sync_message": f"Successfully updated in Mock Azure DevOps #{existing_ado_id}"
        }

        # Persist to local database
        if db is not None:
            self._persist_to_db(updated_tc, db)

        return updated_tc

    async def sync_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        """
        Synchronizes a test case to Mock Azure DevOps.
        CRITICAL: Strictly checks for existing azure_test_case_id in payload or local DB.
        If found: UPDATES the existing test case (#50001) instead of creating a duplicate (#50002).
        If not found: CREATES a new mock test case work item.
        """
        existing_ado_id = tc_data.get("azure_test_case_id")

        # Check local DB for existing ADO ID to prevent duplicates
        if not existing_ado_id and db is not None:
            try:
                from app.models.test_case import TestCaseRecord
                tc_id = tc_data.get("id")
                if tc_id:
                    rec = db.query(TestCaseRecord).filter(TestCaseRecord.id == tc_id).first()
                    if rec and rec.azure_test_case_id:
                        existing_ado_id = rec.azure_test_case_id
            except Exception:
                pass

        if existing_ado_id:
            # Case 1: Already synchronized -> UPDATE existing test case
            return await self.update_test_case(
                existing_ado_id=int(existing_ado_id),
                tc_data=tc_data,
                parent_work_item_id=parent_work_item_id,
                area_path=area_path,
                project=project,
                db=db
            )
        else:
            # Case 2: New test case -> CREATE new test case work item
            return await self.create_test_case(
                tc_data=tc_data,
                parent_work_item_id=parent_work_item_id,
                area_path=area_path,
                project=project,
                db=db
            )

    async def sync_all_test_cases(
        self,
        test_cases: List[Dict[str, Any]],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        synced_count = 0
        updated_count = 0
        failed_count = 0
        result_cases: List[Dict[str, Any]] = []

        for tc in test_cases:
            res_tc = await self.sync_test_case(
                tc_data=tc,
                parent_work_item_id=parent_work_item_id,
                area_path=area_path,
                project=project,
                db=db
            )
            status = res_tc.get("sync_status")
            if status == "Synced":
                synced_count += 1
            elif status == "Updated":
                updated_count += 1
            else:
                failed_count += 1

            result_cases.append(res_tc)

        return result_cases, synced_count, updated_count, failed_count

    def _persist_to_db(self, tc_data: Dict[str, Any], db) -> None:
        """Stores or updates the test case and sync status in the local database."""
        try:
            from app.models.test_case import TestCaseRecord
            tc_id = tc_data.get("id")
            if not tc_id:
                return

            db_rec = db.query(TestCaseRecord).filter(TestCaseRecord.id == tc_id).first()
            steps_val = tc_data.get("test_steps", [])
            steps_str = "\n".join(steps_val) if isinstance(steps_val, list) else str(steps_val)

            if not db_rec:
                db_rec = TestCaseRecord(
                    id=tc_id,
                    azure_work_item_id=str(tc_data.get("azure_work_item_id") or ""),
                    azure_test_case_id=tc_data.get("azure_test_case_id"),
                    azure_project_id=tc_data.get("azure_project_id"),
                    azure_area_path=tc_data.get("azure_area_path"),
                    category=tc_data.get("category", "Positive"),
                    priority=tc_data.get("priority", "Medium"),
                    scenario=tc_data.get("scenario", ""),
                    description=tc_data.get("description", ""),
                    preconditions=tc_data.get("preconditions", ""),
                    test_data=tc_data.get("test_data", ""),
                    test_steps=steps_str,
                    expected_result=tc_data.get("expected_result", ""),
                    requirement_ref=tc_data.get("requirement_ref", ""),
                    application_page=tc_data.get("application_page", ""),
                    application_link=tc_data.get("application_link", ""),
                    sync_status=tc_data.get("sync_status", "Synced"),
                    sync_message=tc_data.get("sync_message", ""),
                    last_synced_at=datetime.utcnow()
                )
                db.add(db_rec)
            else:
                db_rec.azure_test_case_id = tc_data.get("azure_test_case_id")
                db_rec.azure_work_item_id = str(tc_data.get("azure_work_item_id") or db_rec.azure_work_item_id)
                db_rec.azure_project_id = tc_data.get("azure_project_id") or getattr(db_rec, "azure_project_id", None)
                db_rec.azure_area_path = tc_data.get("azure_area_path") or getattr(db_rec, "azure_area_path", None)
                db_rec.sync_status = tc_data.get("sync_status", "Synced")
                db_rec.sync_message = tc_data.get("sync_message", "")
                db_rec.last_synced_at = datetime.utcnow()

            db.commit()
        except Exception as e:
            logger.warning(f"Error persisting mock sync record to DB: {e}")
            try:
                db.rollback()
            except Exception:
                pass
