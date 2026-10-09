import os
import re
import html
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx
from app.core.config import settings
from app.schemas.devops import (
    DevOpsWorkItem,
    AzureDevOpsProjectItem,
    AzureDevOpsAreaItem
)
from app.services.azure_devops.interface import AzureDevOpsService

logger = logging.getLogger(__name__)


def strip_html_tags(text: Optional[str]) -> str:
    """Utility to clean HTML tags and entities from Azure DevOps text fields."""
    if not text:
        return ""
    text = re.sub(r'<(?:br|/li|/p|/div)[^>]*>', '\n', text, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', '', text)
    clean = html.unescape(clean)
    lines = [line.strip() for line in clean.split('\n')]
    return '\n'.join([line for line in lines if line])


def normalize_organization(org_input: str) -> str:
    """
    Extracts the clean organization name from user input or URL.
    Examples:
      - 'https://dev.azure.com/myorg' -> 'myorg'
      - 'https://dev.azure.com/myorg/' -> 'myorg'
      - 'https://myorg.visualstudio.com' -> 'myorg'
      - 'myorg' -> 'myorg'
    """
    if not org_input:
        return ""
    org = org_input.strip().rstrip('/')
    if "dev.azure.com/" in org:
        parts = org.split("dev.azure.com/")
        if len(parts) > 1:
            org = parts[1].split('/')[0]
    elif ".visualstudio.com" in org:
        parts = org.replace("https://", "").replace("http://", "").split(".visualstudio.com")
        if len(parts) > 0:
            org = parts[0]
    return org.strip('/')


class RealAzureDevOpsService(AzureDevOpsService):
    """
    Production-grade service communicating with real Microsoft Azure DevOps REST APIs (v7.0).
    Implements the AzureDevOpsService contract.
    """

    def __init__(self):
        self._org: str = normalize_organization(settings.AZURE_DEVOPS_ORG)
        self._project: str = settings.AZURE_DEVOPS_PROJECT.strip()
        self._pat: str = settings.AZURE_DEVOPS_PAT.strip()
        self._connected: bool = bool(self._org and self._pat)

    @property
    def mode(self) -> str:
        return "real"

    @property
    def organization(self) -> str:
        return self._org

    @property
    def project(self) -> str:
        return self._project

    @property
    def pat(self) -> str:
        return self._pat

    @property
    def is_connected(self) -> bool:
        return self._connected and bool(self._org) and bool(self._pat)

    def configure(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> None:
        """Update runtime Azure DevOps credentials safely in memory."""
        if organization is not None:
            self._org = normalize_organization(organization)
        if project is not None:
            self._project = project.strip()
        if pat is not None:
            self._pat = pat.strip()
        self._connected = bool(self._org and self._pat)

    def disconnect(self) -> None:
        """Reset connection state to disconnected / offline mode."""
        self._connected = False

    def reload_from_env(self) -> None:
        """Dynamically reload credentials from backend .env file."""
        from dotenv import load_dotenv
        backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
        root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
        if os.path.exists(backend_env):
            load_dotenv(dotenv_path=backend_env, override=False)
        elif os.path.exists(root_env):
            load_dotenv(dotenv_path=root_env, override=False)
        else:
            load_dotenv(override=False)

        raw_org = os.getenv("AZURE_DEVOPS_ORG") or os.getenv("ADO_ORGANIZATION") or ""
        self._org = normalize_organization(raw_org)
        self._project = (os.getenv("AZURE_DEVOPS_PROJECT") or os.getenv("ADO_PROJECT") or "").strip()
        self._pat = (os.getenv("AZURE_DEVOPS_PAT") or os.getenv("ADO_PAT") or "").strip()
        self._connected = bool(self._org and self._pat)

    def get_base_url(self, org: Optional[str] = None, project: Optional[str] = None) -> str:
        target_org = normalize_organization(org) if org else self._org
        target_proj = project if project is not None else self._project
        if target_proj:
            return f"https://dev.azure.com/{target_org}/{target_proj}/_apis"
        return f"https://dev.azure.com/{target_org}/_apis"

    def get_headers(self, pat: Optional[str] = None, content_type: str = "application/json") -> Dict[str, str]:
        target_pat = pat.strip() if pat else self._pat
        if not target_pat:
            return {"Content-Type": content_type}
        encoded = base64.b64encode(f":{target_pat}".encode("utf-8")).decode("ascii")
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": content_type,
            "Accept": "application/json"
        }

    async def test_connection(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> Tuple[bool, str, List[AzureDevOpsProjectItem]]:
        """Tests connection to Microsoft Azure DevOps using official REST API."""
        target_org = normalize_organization(organization) if organization else self._org
        target_pat = pat.strip() if pat else self._pat
        target_proj = project.strip() if project else self._project

        if not target_org:
            return False, "Azure DevOps Organization is required.", []
        if not target_pat:
            return False, "Personal Access Token (PAT) is required.", []

        headers = self.get_headers(pat=target_pat)
        url = f"https://dev.azure.com/{target_org}/_apis/projects?api-version=7.0"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code in (401, 203) or "signin" in str(res.url).lower():
                    return False, "Invalid or expired Personal Access Token (PAT). Please verify credentials.", []
                if res.status_code == 403:
                    return False, "Access denied. The PAT does not have required permissions for this organization.", []
                if res.status_code == 404:
                    return False, f"Azure DevOps organization '{target_org}' not found. Please verify the URL or organization name.", []
                if res.status_code != 200:
                    return False, f"Azure DevOps returned HTTP {res.status_code}: {res.text[:200]}", []

                data = res.json()
                raw_projects = data.get("value", [])
                projects: List[AzureDevOpsProjectItem] = []
                for p in raw_projects:
                    projects.append(
                        AzureDevOpsProjectItem(
                            id=p.get("id", ""),
                            name=p.get("name", ""),
                            description=p.get("description", "") or "",
                            state=p.get("state", "wellFormed")
                        )
                    )

                if target_proj:
                    proj_match = next((p for p in projects if p.name.lower() == target_proj.lower()), None)
                    if not proj_match:
                        self._connected = True
                        return True, f"Connected to organization '{target_org}', but project '{target_proj}' was not found among available projects.", projects
                    self._connected = True
                    self._project = proj_match.name
                    return True, f"Connected to Azure DevOps organization '{target_org}' and project '{proj_match.name}'.", projects

                self._connected = True
                return True, f"Connected to Azure DevOps organization '{target_org}'. Found {len(projects)} projects.", projects

        except httpx.ConnectError:
            self._connected = False
            return False, "Network error: Unable to connect to dev.azure.com. Check internet connection.", []
        except httpx.TimeoutException:
            self._connected = False
            return False, "Connection timed out while contacting Azure DevOps REST API.", []
        except Exception as e:
            self._connected = False
            return False, f"Unable to connect to Azure DevOps: {str(e)}", []

    async def get_projects(self) -> List[AzureDevOpsProjectItem]:
        if not self._org or not self._pat:
            return []
        success, _, projects = await self.test_connection(self._org, self._project, self._pat)
        return projects if success else []

    async def get_areas(self, project: Optional[str] = None) -> List[AzureDevOpsAreaItem]:
        target_proj = project or self._project
        if not self._org or not target_proj or not self._pat:
            return []

        url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/classificationnodes/Areas?$depth=5&api-version=7.0"
        headers = self.get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"Failed to fetch classification nodes: HTTP {res.status_code} {res.text}")
                    return []

                data = res.json()

                def parse_node(node: dict, current_path: str) -> AzureDevOpsAreaItem:
                    node_name = node.get("name", "")
                    node_id = int(node.get("id", 0))
                    child_path = f"{current_path}\\{node_name}" if current_path else node_name
                    raw_children = node.get("children", [])
                    has_children = node.get("hasChildren", False) or len(raw_children) > 0
                    parsed_children = [parse_node(c, child_path) for c in raw_children]

                    return AzureDevOpsAreaItem(
                        id=node_id,
                        name=node_name,
                        path=child_path.lstrip('\\'),
                        has_children=has_children,
                        children=parsed_children
                    )

                root_item = parse_node(data, "")
                if root_item.children:
                    return [root_item] + root_item.children
                return [root_item]

        except Exception as e:
            logger.error(f"Error fetching areas from Azure DevOps: {e}")
            return []

    async def get_flat_areas(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        target_proj = project or self._project
        if not self._org or not target_proj or not self._pat:
            return []

        url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/classificationnodes/Areas?$depth=5&api-version=7.0"
        headers = self.get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"Failed to fetch classification nodes: HTTP {res.status_code} {res.text}")
                    return []

                data = res.json()
                flat_list: List[Dict[str, Any]] = []

                def flatten_node(node: dict, current_path: str, parent_id: Optional[int]):
                    node_name = node.get("name", "")
                    node_id = int(node.get("id", 0))
                    child_path = f"{current_path}\\{node_name}" if current_path else node_name

                    flat_list.append({
                        "id": node_id,
                        "name": node_name,
                        "code": child_path,
                        "path": child_path,
                        "parent_id": parent_id
                    })

                    for child in node.get("children", []):
                        flatten_node(child, child_path, node_id)

                flatten_node(data, "", None)
                return flat_list
        except Exception as e:
            logger.error(f"Error fetching flat areas from Azure DevOps: {e}")
            return []

    async def query_work_items(
        self,
        project: Optional[str] = None,
        area_path: Optional[str] = None,
        work_item_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[DevOpsWorkItem]:
        """
        Executes WIQL query to retrieve real Work Items.
        Supports filtering by project, area_path, work_item_type, and search text.
        """
        target_proj = project or self._project
        if not self._org or not target_proj or not self._pat:
            return []

        conditions = []
        if target_proj:
            conditions.append(f"[System.TeamProject] = '{target_proj}'")

        if work_item_type:
            clean_type = work_item_type.replace("'", "''")
            conditions.append(f"[System.WorkItemType] = '{clean_type}'")
        else:
            conditions.append("[System.WorkItemType] IN ('User Story', 'Product Backlog Item', 'Requirement', 'Issue', 'Bug', 'Task', 'Feature')")

        if area_path:
            clean_area = area_path.replace("'", "''")
            conditions.append(f"[System.AreaPath] UNDER '{clean_area}'")

        if search:
            clean_search = search.replace("'", "''")
            conditions.append(f"([System.Title] CONTAINS '{clean_search}' OR [System.Description] CONTAINS '{clean_search}')")

        where_clause = " AND ".join(conditions)
        query_str = (
            f"SELECT [System.Id] FROM WorkItems "
            f"WHERE {where_clause} "
            f"ORDER BY [System.Id] DESC"
        )

        url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/wiql?api-version=7.0"
        headers = self.get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.post(url, headers=headers, json={"query": query_str})
                if res.status_code != 200:
                    logger.warning(f"WIQL query failed: HTTP {res.status_code} {res.text}")
                    return []

                data = res.json()
                work_item_refs = data.get("workItems", [])
                if not work_item_refs:
                    return []

                ids = [w["id"] for w in work_item_refs[:limit]]
                return await self.get_work_items_batch(ids, target_proj)

        except Exception as e:
            logger.error(f"Error querying work items via WIQL: {e}")
            return []

    async def get_work_items_batch(self, ids: List[int], project: Optional[str] = None) -> List[DevOpsWorkItem]:
        if not ids or not self._org or not self._pat:
            return []

        target_proj = project or self._project
        url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workitemsbatch?api-version=7.0"
        headers = self.get_headers()

        payload = {
            "ids": ids,
            "fields": [
                "System.Id",
                "System.Title",
                "System.WorkItemType",
                "System.Description",
                "Microsoft.VSTS.Common.AcceptanceCriteria",
                "System.State",
                "System.AssignedTo",
                "System.AreaPath",
                "System.IterationPath",
                "System.Tags"
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    logger.warning(f"Batch work item retrieval failed: HTTP {res.status_code} {res.text}")
                    return []

                data = res.json()
                items: List[DevOpsWorkItem] = []
                for raw in data.get("value", []):
                    fields = raw.get("fields", {})
                    raw_desc = fields.get("System.Description", "")
                    clean_desc = strip_html_tags(raw_desc)

                    raw_ac = fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
                    clean_ac = strip_html_tags(raw_ac)
                    if not clean_ac and clean_desc:
                        clean_ac = clean_desc

                    assigned_to = fields.get("System.AssignedTo")
                    assigned_name = "Unassigned"
                    if isinstance(assigned_to, dict):
                        assigned_name = assigned_to.get("displayName", "Unassigned")
                    elif isinstance(assigned_to, str):
                        assigned_name = assigned_to

                    raw_tags = fields.get("System.Tags", "")
                    tags_list = [t.strip() for t in raw_tags.split(';') if t.strip()] if raw_tags else []

                    items.append(
                        DevOpsWorkItem(
                            id=str(raw.get("id")),
                            title=fields.get("System.Title", "Untitled Work Item"),
                            work_item_type=fields.get("System.WorkItemType", "User Story"),
                            description=clean_desc,
                            acceptance_criteria=clean_ac,
                            state=fields.get("System.State", "Active"),
                            assigned_to=assigned_name,
                            area_path=fields.get("System.AreaPath"),
                            iteration_path=fields.get("System.IterationPath"),
                            tags=tags_list
                        )
                    )
                return items

        except Exception as e:
            logger.error(f"Error fetching work items batch: {e}")
            return []

    async def get_single_work_item(self, work_item_id: str, project: Optional[str] = None) -> Optional[DevOpsWorkItem]:
        numeric_id = ''.join(filter(str.isdigit, work_item_id))
        if not numeric_id:
            return None

        target_proj = project or self._project
        if not self._org or not self._pat:
            return None

        url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workitems/{numeric_id}?api-version=7.0&$expand=all"
        headers = self.get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    return None

                data = res.json()
                fields = data.get("fields", {})

                raw_desc = fields.get("System.Description", "")
                clean_desc = strip_html_tags(raw_desc)

                raw_ac = fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
                clean_ac = strip_html_tags(raw_ac)
                if not clean_ac and clean_desc:
                    clean_ac = clean_desc

                assigned_to = fields.get("System.AssignedTo")
                assigned_name = "Unassigned"
                if isinstance(assigned_to, dict):
                    assigned_name = assigned_to.get("displayName", "Unassigned")
                elif isinstance(assigned_to, str):
                    assigned_name = assigned_to

                raw_tags = fields.get("System.Tags", "")
                tags_list = [t.strip() for t in raw_tags.split(';') if t.strip()] if raw_tags else []

                return DevOpsWorkItem(
                    id=str(data.get("id")),
                    title=fields.get("System.Title", f"Work Item #{numeric_id}"),
                    work_item_type=fields.get("System.WorkItemType", "User Story"),
                    description=clean_desc,
                    acceptance_criteria=clean_ac,
                    state=fields.get("System.State", "Active"),
                    assigned_to=assigned_name,
                    area_path=fields.get("System.AreaPath"),
                    iteration_path=fields.get("System.IterationPath"),
                    tags=tags_list
                )

        except Exception as e:
            logger.error(f"Error fetching single work item #{numeric_id}: {e}")
            return None

    def _build_tcm_steps_xml(self, steps: List[str], expected_result: str) -> str:
        xml_steps = [f'<steps id="0" last="{len(steps) + 1}">']
        for idx, step_text in enumerate(steps, start=2):
            is_last = (idx == len(steps) + 1)
            step_expected = html.escape(expected_result) if is_last else ""
            xml_steps.append(
                f'<step id="{idx}" type="ValidateStep">'
                f'<parameterizedString isformatted="true">{html.escape(step_text)}</parameterizedString>'
                f'<parameterizedString isformatted="true">{step_expected}</parameterizedString>'
                f'<description/>'
                f'</step>'
            )
        xml_steps.append('</steps>')
        return "".join(xml_steps)

    def _map_priority(self, priority_str: str) -> int:
        p = (priority_str or "").strip().upper()
        if p == "HIGH":
            return 1
        elif p == "LOW":
            return 3
        return 2

    async def create_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        target_proj = project or self._project
        if not self._org or not target_proj or not self._pat:
            return {
                **tc_data,
                "sync_status": "Sync Failed",
                "sync_message": "Azure DevOps is not configured or PAT is missing."
            }

        headers = self.get_headers(content_type="application/json-patch+json")
        title = f"[{tc_data.get('category', 'Positive')}] {tc_data.get('scenario', 'Test Case')}"
        description = (
            f"<p><strong>Objective:</strong> {html.escape(tc_data.get('description', ''))}</p>"
            f"<p><strong>Preconditions:</strong> {html.escape(tc_data.get('preconditions', ''))}</p>"
            f"<p><strong>Test Data:</strong> {html.escape(tc_data.get('test_data', ''))}</p>"
            f"<p><strong>Expected Result:</strong> {html.escape(tc_data.get('expected_result', ''))}</p>"
        )

        steps_list = tc_data.get("test_steps", [])
        if isinstance(steps_list, str):
            steps_list = [s.strip() for s in steps_list.split("\n") if s.strip()]

        steps_xml = self._build_tcm_steps_xml(steps_list, tc_data.get("expected_result", ""))
        priority_val = self._map_priority(tc_data.get("priority", "Medium"))
        resolved_parent_id = parent_work_item_id or tc_data.get("azure_work_item_id") or tc_data.get("user_story")
        clean_parent_numeric = ''.join(filter(str.isdigit, str(resolved_parent_id))) if resolved_parent_id else None

        create_patch = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority_val},
            {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": steps_xml}
        ]

        if area_path:
            create_patch.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})

        if clean_parent_numeric:
            create_patch.append({
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
                    "url": f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workItems/{clean_parent_numeric}",
                    "attributes": {
                        "comment": f"Generated Test Case linked to User Story #{clean_parent_numeric}"
                    }
                }
            })

        create_url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workitems/$Test%20Case?api-version=7.0"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.post(create_url, headers=headers, json=create_patch)
                if res.status_code != 200 and clean_parent_numeric:
                    fallback_patch = [op for op in create_patch if op.get("path") != "/relations/-"]
                    fallback_patch.append({
                        "op": "add",
                        "path": "/relations/-",
                        "value": {
                            "rel": "System.LinkTypes.Related",
                            "url": f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workItems/{clean_parent_numeric}",
                            "attributes": {
                                "comment": f"Generated Test Case linked to #{clean_parent_numeric}"
                            }
                        }
                    })
                    res = await client.post(create_url, headers=headers, json=fallback_patch)

                if res.status_code != 200:
                    clean_patch = [op for op in create_patch if op.get("path") != "/relations/-"]
                    res = await client.post(create_url, headers=headers, json=clean_patch)

                if res.status_code in (200, 201):
                    res_data = res.json()
                    new_ado_id = res_data.get("id")
                    updated_tc = {
                        **tc_data,
                        "azure_test_case_id": int(new_ado_id),
                        "azure_work_item_id": clean_parent_numeric or tc_data.get("azure_work_item_id"),
                        "azure_project_id": target_proj,
                        "azure_area_path": area_path,
                        "sync_status": "Synced",
                        "sync_message": f"Successfully created in Azure DevOps #{new_ado_id}"
                    }
                    if db is not None:
                        self._persist_to_db(updated_tc, db)
                    return updated_tc
                else:
                    return {
                        **tc_data,
                        "sync_status": "Sync Failed",
                        "sync_message": f"Azure DevOps creation failed: HTTP {res.status_code} {res.text[:100]}"
                    }

        except Exception as e:
            return {
                **tc_data,
                "sync_status": "Sync Failed",
                "sync_message": f"Network error during sync: {str(e)}"
            }

    async def update_test_case(
        self,
        existing_ado_id: int,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        target_proj = project or self._project
        if not self._org or not target_proj or not self._pat:
            return {
                **tc_data,
                "sync_status": "Sync Failed",
                "sync_message": "Azure DevOps is not configured or PAT is missing."
            }

        headers = self.get_headers(content_type="application/json-patch+json")
        title = f"[{tc_data.get('category', 'Positive')}] {tc_data.get('scenario', 'Test Case')}"
        description = (
            f"<p><strong>Objective:</strong> {html.escape(tc_data.get('description', ''))}</p>"
            f"<p><strong>Preconditions:</strong> {html.escape(tc_data.get('preconditions', ''))}</p>"
            f"<p><strong>Test Data:</strong> {html.escape(tc_data.get('test_data', ''))}</p>"
            f"<p><strong>Expected Result:</strong> {html.escape(tc_data.get('expected_result', ''))}</p>"
        )

        steps_list = tc_data.get("test_steps", [])
        if isinstance(steps_list, str):
            steps_list = [s.strip() for s in steps_list.split("\n") if s.strip()]

        steps_xml = self._build_tcm_steps_xml(steps_list, tc_data.get("expected_result", ""))
        priority_val = self._map_priority(tc_data.get("priority", "Medium"))
        resolved_parent_id = parent_work_item_id or tc_data.get("azure_work_item_id") or tc_data.get("user_story")
        clean_parent_numeric = ''.join(filter(str.isdigit, str(resolved_parent_id))) if resolved_parent_id else None

        update_patch = [
            {"op": "replace", "path": "/fields/System.Title", "value": title},
            {"op": "replace", "path": "/fields/System.Description", "value": description},
            {"op": "replace", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority_val},
            {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": steps_xml}
        ]
        if area_path:
            update_patch.append({"op": "replace", "path": "/fields/System.AreaPath", "value": area_path})

        patch_url = f"https://dev.azure.com/{self._org}/{target_proj}/_apis/wit/workitems/{existing_ado_id}?api-version=7.0"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.patch(patch_url, headers=headers, json=update_patch)
                if res.status_code in (200, 201):
                    updated_tc = {
                        **tc_data,
                        "azure_test_case_id": int(existing_ado_id),
                        "azure_work_item_id": clean_parent_numeric or tc_data.get("azure_work_item_id"),
                        "azure_project_id": target_proj,
                        "azure_area_path": area_path,
                        "sync_status": "Updated",
                        "sync_message": f"Successfully updated in Azure DevOps #{existing_ado_id}"
                    }
                    if db is not None:
                        self._persist_to_db(updated_tc, db)
                    return updated_tc
                else:
                    return {
                        **tc_data,
                        "sync_status": "Sync Failed",
                        "sync_message": f"Azure DevOps update failed: HTTP {res.status_code} {res.text[:100]}"
                    }
        except Exception as e:
            return {
                **tc_data,
                "sync_status": "Sync Failed",
                "sync_message": f"Network error during update: {str(e)}"
            }

    async def sync_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        existing_ado_id = tc_data.get("azure_test_case_id")
        if not existing_ado_id and db is not None:
            try:
                from app.models.test_case import TestCaseRecord
                tc_id = tc_data.get("id")
                if tc_id:
                    db_rec = db.query(TestCaseRecord).filter(TestCaseRecord.id == tc_id).first()
                    if db_rec and db_rec.azure_test_case_id:
                        existing_ado_id = db_rec.azure_test_case_id
            except Exception:
                pass

        if existing_ado_id:
            return await self.update_test_case(
                existing_ado_id=int(existing_ado_id),
                tc_data=tc_data,
                parent_work_item_id=parent_work_item_id,
                area_path=area_path,
                project=project,
                db=db
            )
        else:
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
            logger.warning(f"Error persisting real sync record to DB: {e}")
            try:
                db.rollback()
            except Exception:
                pass
