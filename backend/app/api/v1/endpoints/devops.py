import re
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.devops import (
    DevOpsWorkItem,
    AcceptanceCriteriaItem,
    AreaRead,
    UserStoryRead,
    AcceptanceCriteriaRead,
    AzureDevOpsConnectRequest,
    AzureDevOpsConnectResponse,
    AzureDevOpsConfigResponse,
    AzureDevOpsProjectItem,
    AzureDevOpsSyncRequest,
    AzureDevOpsSyncResponse
)
from app.models.devops import Area, UserStory, AcceptanceCriteria
from app.services.devops_service import devops_service, MOCK_WORK_ITEMS
from app.services.azure_devops_service import azure_devops_service, normalize_organization
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


def extract_criteria_from_ado_item(item: DevOpsWorkItem) -> List[AcceptanceCriteriaRead]:
    """Parses Acceptance Criteria lines from an Azure DevOps Work Item."""
    criteria: List[AcceptanceCriteriaRead] = []
    text_source = (item.acceptance_criteria or item.description or "").strip()
    if text_source:
        lines = [l.strip() for l in text_source.split("\n") if l.strip()]
        for idx, line in enumerate(lines, start=1):
            clean_text = re.sub(r'^(?:[0-9]+[\.\)]\s*|[-*]\s*)+', '', line).strip()
            if clean_text:
                criteria.append(
                    AcceptanceCriteriaRead(
                        id=f"{item.id}-AC-{idx:02d}",
                        user_story_id=item.id,
                        criteria_number=idx,
                        text=clean_text
                    )
                )
    if not criteria:
        criteria.append(
            AcceptanceCriteriaRead(
                id=f"{item.id}-AC-01",
                user_story_id=item.id,
                criteria_number=1,
                text=f"Verify {item.title} meets specified functional and acceptance requirements."
            )
        )
    return criteria


# ============================================================================
# AZURE DEVOPS INTEGRATION ENDPOINTS (MOCK & REAL ABSTRACTION)
# ============================================================================

@router.post("/azure/connect", response_model=AzureDevOpsConnectResponse)
async def connect_azure_devops(
    payload: Optional[AzureDevOpsConnectRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Connects to Azure DevOps (Local Mock Service or Microsoft REST API).
    In Mock Mode: connects successfully with Organization and Project without requiring real PAT/signup.
    In Real Mode: connects with credentials configured in .env or payload.
    """
    azure_devops_service.reload_from_env()
    current_mode = getattr(azure_devops_service, "mode", "mock")

    raw_org = payload.organization if (payload and payload.organization) else azure_devops_service.organization
    raw_proj = (payload.project.strip() if (payload and payload.project) else None) or azure_devops_service.project
    raw_pat = (payload.pat.strip() if (payload and payload.pat) else None) or azure_devops_service.pat

    target_org = normalize_organization(raw_org) if raw_org else ("DemoOrganization" if current_mode == "mock" else "")
    target_proj = raw_proj or ("TestCaseDemoProject" if current_mode == "mock" else "")
    target_pat = raw_pat or ""

    if current_mode == "real":
        if not target_org:
            return AzureDevOpsConnectResponse(
                connected=False,
                organization="",
                project=target_proj or "",
                message="Azure DevOps Organization is missing. Please configure ADO_ORGANIZATION in backend/.env.",
                projects=[],
                mode="real"
            )
        if not target_pat:
            return AzureDevOpsConnectResponse(
                connected=False,
                organization=target_org,
                project=target_proj or "",
                message="Personal Access Token (PAT) is missing. Please configure ADO_PAT in backend/.env.",
                projects=[],
                mode="real"
            )

    success, message, projects = await azure_devops_service.test_connection(
        organization=target_org,
        project=target_proj,
        pat=target_pat
    )

    if success:
        azure_devops_service.configure(organization=target_org, project=target_proj, pat=target_pat)

    return AzureDevOpsConnectResponse(
        connected=success,
        organization=target_org or "",
        project=target_proj or "",
        message=message,
        projects=projects,
        mode=current_mode
    )


@router.get("/azure/config", response_model=AzureDevOpsConfigResponse)
def get_azure_devops_config(current_user: User = Depends(get_current_user)):
    """
    Returns current Azure DevOps configuration status from backend.
    Never exposes technical secrets like PAT.
    """
    azure_devops_service.reload_from_env()
    current_mode = getattr(azure_devops_service, "mode", "mock")
    return AzureDevOpsConfigResponse(
        organization=azure_devops_service.organization,
        project=azure_devops_service.project,
        is_pat_configured=bool(azure_devops_service.pat),
        connected=azure_devops_service.is_connected,
        mode=current_mode
    )


@router.post("/azure/disconnect")
def disconnect_azure_devops(current_user: User = Depends(get_current_user)):
    """Switches Azure DevOps integration to offline / local database mode."""
    azure_devops_service.disconnect()
    return {"connected": False, "message": "Azure DevOps disconnected. Operating in offline/local mode."}


@router.get("/azure/projects", response_model=List[AzureDevOpsProjectItem])
async def get_azure_devops_projects(current_user: User = Depends(get_current_user)):
    """Retrieves projects from the active Azure DevOps service (mock or real)."""
    return await azure_devops_service.get_projects()


@router.get("/azure/areas")
async def get_azure_devops_areas(
    project: Optional[str] = Query(None, description="Azure DevOps Project name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves classification nodes (Areas) from Azure DevOps service (mock or real).
    If Azure DevOps service is offline, falls back gracefully to local database areas.
    """
    target_proj = project or azure_devops_service.project
    current_mode = getattr(azure_devops_service, "mode", "mock")

    if current_mode == "mock" or (azure_devops_service.pat and azure_devops_service.organization and target_proj):
        try:
            areas = await azure_devops_service.get_flat_areas(project=target_proj)
            if areas:
                return areas
        except Exception:
            pass

    # Graceful fallback to local database areas
    db_areas = db.query(Area).order_by(Area.id).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "code": a.code,
            "path": a.name,
            "parent_id": a.parent_id
        }
        for a in db_areas
    ]


@router.get("/azure/work-items", response_model=List[DevOpsWorkItem])
async def get_azure_devops_work_items(
    area_path: Optional[str] = Query(None, description="Azure DevOps Area Path to filter by"),
    project: Optional[str] = Query(None, description="Azure DevOps Project name"),
    work_item_type: Optional[str] = Query(None, description="Filter by Work Item Type (e.g. User Story)"),
    search: Optional[str] = Query(None, description="Search text in title, description, or tags"),
    limit: int = Query(50, description="Max work items to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Queries User Stories and Work Items from Azure DevOps service via mock/real WIQL engine.
    Supports filtering by project, area_path, work_item_type, and search text.
    """
    target_proj = project or azure_devops_service.project
    current_mode = getattr(azure_devops_service, "mode", "mock")

    if current_mode == "mock" or (azure_devops_service.pat and azure_devops_service.organization and target_proj):
        try:
            items = await azure_devops_service.query_work_items(
                project=target_proj,
                area_path=area_path,
                work_item_type=work_item_type,
                search=search,
                limit=limit
            )
            if items:
                return items
        except Exception:
            pass

    # Fallback to local database user stories
    stories = db.query(UserStory).all()
    result = []
    for s in stories:
        acs = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id == s.id).order_by(AcceptanceCriteria.criteria_number).all()
        ac_text = "\n".join([ac.text for ac in acs]) if acs else (s.description or "")
        area_obj = db.query(Area).filter(Area.id == s.area_id).first()
        result.append(
            DevOpsWorkItem(
                id=s.id,
                title=s.title,
                work_item_type="User Story",
                description=s.description or "",
                acceptance_criteria=ac_text,
                state=s.state or "Active",
                assigned_to=s.assigned_to or "QA Team",
                area_path=area_obj.name if area_obj else None
            )
        )
    return result


# ============================================================================
# WIQL QUERY ALIAS ENDPOINTS (REQUIREMENT 8)
# ============================================================================

@router.get("/work-items", response_model=List[DevOpsWorkItem])
async def get_work_items_alias(
    area_path: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    work_item_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct alias for querying Azure DevOps work items with WIQL-style filtering."""
    effective_area = area_path or area
    return await get_azure_devops_work_items(
        area_path=effective_area,
        project=project,
        work_item_type=work_item_type,
        search=search,
        limit=limit,
        db=db,
        current_user=current_user
    )


@router.post("/work-items", response_model=List[DevOpsWorkItem])
async def post_work_items_alias(
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """POST alias for WIQL query filter payload (project, area, work_item_type, search, limit)."""
    payload = payload or {}
    return await get_azure_devops_work_items(
        area_path=payload.get("area_path") or payload.get("area"),
        project=payload.get("project"),
        work_item_type=payload.get("work_item_type"),
        search=payload.get("search") or payload.get("query"),
        limit=int(payload.get("limit", 50)),
        db=db,
        current_user=current_user
    )


@router.get("/azure/work-items/{work_item_id}", response_model=DevOpsWorkItem)
async def get_azure_devops_single_work_item(
    work_item_id: str,
    project: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves complete details for a single work item from active Azure DevOps service:
    ID, Title, Description, Acceptance Criteria, State, Assigned To, Area Path, Iteration Path, Tags.
    """
    target_proj = project or azure_devops_service.project
    current_mode = getattr(azure_devops_service, "mode", "mock")

    if current_mode == "mock" or (azure_devops_service.pat and azure_devops_service.organization):
        try:
            item = await azure_devops_service.get_single_work_item(work_item_id=work_item_id, project=target_proj)
            if item:
                return item
        except Exception:
            pass

    # Fallback to local database or devops_service
    return await devops_service.get_work_item(work_item_id, db=db)


@router.post("/azure/sync", response_model=AzureDevOpsSyncResponse)
async def sync_test_cases_to_azure(
    payload: AzureDevOpsSyncRequest,
    project: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronizes generated test cases to Azure DevOps (Mock or Real Service).
    - Prevents duplicates: updates existing Azure DevOps test cases if already synced.
    - Creates new Test Case work items if not yet synced.
    - Stores resulting Azure DevOps IDs in the local SQLite database.
    - Returns sync status for each test case.
    """
    target_proj = payload.project or project or azure_devops_service.project
    current_mode = getattr(azure_devops_service, "mode", "mock")

    if current_mode == "real" and (not azure_devops_service.pat or not azure_devops_service.organization):
        raise HTTPException(
            status_code=400,
            detail="Azure DevOps is not connected. Please configure Organization, Project, and PAT first."
        )

    result_cases, synced_count, updated_count, failed_count = await azure_devops_service.sync_all_test_cases(
        test_cases=payload.test_cases,
        parent_work_item_id=payload.work_item_id,
        area_path=payload.area_path,
        project=target_proj,
        db=db
    )

    success = (synced_count > 0 or updated_count > 0) or (failed_count == 0 and len(result_cases) > 0)
    message = (
        f"Azure DevOps sync finished: {synced_count} created, {updated_count} updated, "
        f"{failed_count} failed."
    )

    return AzureDevOpsSyncResponse(
        success=success,
        message=message,
        synced_count=synced_count,
        updated_count=updated_count,
        failed_count=failed_count,
        test_cases=result_cases
    )


# ============================================================================
# EXISTING LOCAL / OFFLINE DATABASE ROUTES (MAINTAIN 100% COMPATIBILITY)
# ============================================================================

@router.get("/areas", response_model=List[AreaRead])
def get_areas(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all available Area / Parts from database (requires login)."""
    areas = db.query(Area).order_by(Area.id).all()
    return areas


@router.get("/areas/multi/user-stories", response_model=List[UserStoryRead])
def get_user_stories_by_multiple_areas(
    area_ids: Optional[List[int]] = Query(None, description="List of Area / Service IDs"),
    services: Optional[List[str]] = Query(None, description="List of Service names"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all User Stories belonging to selected Areas / Services (requires login)."""
    target_area_ids = set()
    if area_ids:
        target_area_ids.update(area_ids)
    if services:
        matched = db.query(Area.id).filter(Area.name.in_(services)).all()
        for (a_id,) in matched:
            target_area_ids.add(a_id)

    if not target_area_ids:
        return []

    all_area_ids = set()
    for a_id in target_area_ids:
        area = db.query(Area).filter(Area.id == a_id).first()
        if not area:
            continue
        all_area_ids.add(a_id)
        def get_child_ids(p_id: int):
            children = db.query(Area.id).filter(Area.parent_id == p_id).all()
            for (c_id,) in children:
                all_area_ids.add(c_id)
                get_child_ids(c_id)
        get_child_ids(a_id)

    if not all_area_ids:
        return []

    stories = db.query(UserStory).filter(UserStory.area_id.in_(list(all_area_ids))).all()
    return stories


@router.get("/areas/{area_id}/user-stories", response_model=List[UserStoryRead])
def get_user_stories_by_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all User Stories belonging to selected Area / Part or its child areas from database (requires login)."""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area / Part not found.")

    area_ids = [area_id]
    def get_child_ids(p_id: int):
        children = db.query(Area.id).filter(Area.parent_id == p_id).all()
        for (c_id,) in children:
            area_ids.append(c_id)
            get_child_ids(c_id)
    get_child_ids(area_id)

    stories = db.query(UserStory).filter(UserStory.area_id.in_(area_ids)).all()
    return stories


@router.get("/user-stories/multi/acceptance-criteria", response_model=List[AcceptanceCriteriaRead])
async def get_acceptance_criteria_by_multiple_user_stories(
    story_ids: Optional[List[str]] = Query(None, description="List of User Story IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all Acceptance Criteria belonging to selected User Stories from database or live Azure DevOps (requires login)."""
    if not story_ids:
        return []

    normalized_ids = []
    for sid in story_ids:
        if not sid:
            continue
        clean = sid.strip().upper()
        if clean not in normalized_ids:
            normalized_ids.append(clean)
        if not clean.startswith("US-"):
            prefixed = f"US-{clean}"
            if prefixed not in normalized_ids:
                normalized_ids.append(prefixed)

    from sqlalchemy import func
    criteria = db.query(AcceptanceCriteria).filter(
        func.upper(AcceptanceCriteria.user_story_id).in_(normalized_ids)
    ).order_by(AcceptanceCriteria.user_story_id, AcceptanceCriteria.criteria_number).all()

    unique_criteria: List[AcceptanceCriteriaRead] = []
    seen_ids = set()
    for c in criteria:
        clean_cid = c.id.strip().upper()
        if clean_cid not in seen_ids:
            seen_ids.add(clean_cid)
            unique_criteria.append(c)

    found_story_ids = {c.user_story_id.upper() for c in unique_criteria}

    # For any stories not in local DB: check live Azure DevOps first, then mock fallback
    for sid in story_ids:
        clean = sid.strip().upper()
        if clean not in found_story_ids and f"US-{clean}" not in found_story_ids:
            # Check live Azure DevOps
            if azure_devops_service.pat and azure_devops_service.organization:
                try:
                    live_story = await azure_devops_service.get_single_work_item(sid)
                    if live_story:
                        parsed_crits = extract_criteria_from_ado_item(live_story)
                        for ac in parsed_crits:
                            if ac.id.upper() not in seen_ids:
                                seen_ids.add(ac.id.upper())
                                unique_criteria.append(ac)
                        continue
                except Exception:
                    pass

            # Mock fallback
            for mock_item in MOCK_WORK_ITEMS:
                if mock_item.id.upper() in (clean, f"US-{clean}"):
                    ac_lines = [l.strip() for l in (mock_item.acceptance_criteria or "").split("\n") if l.strip()]
                    for idx, line in enumerate(ac_lines, start=1):
                        cid = f"{mock_item.id}-AC-{idx:02d}"
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            unique_criteria.append(
                                AcceptanceCriteriaRead(
                                    id=cid,
                                    user_story_id=mock_item.id,
                                    criteria_number=idx,
                                    text=line
                                )
                            )

    return unique_criteria


@router.get("/user-stories/{story_id}/acceptance-criteria", response_model=List[AcceptanceCriteriaRead])
async def get_acceptance_criteria_by_user_story(
    story_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all Acceptance Criteria belonging to selected User Story from database or live Azure DevOps (requires login)."""
    clean_id = story_id.strip().upper()
    story = db.query(UserStory).filter(UserStory.id.ilike(clean_id)).first()
    if not story and not clean_id.startswith("US-"):
        story = db.query(UserStory).filter(UserStory.id.ilike(f"US-{clean_id}")).first()

    if story:
        return db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id == story.id).order_by(AcceptanceCriteria.criteria_number).all()

    # Fallback to direct criteria query in DB
    criteria = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id.ilike(clean_id)).all()
    if criteria:
        return criteria

    # Check live Azure DevOps
    if azure_devops_service.pat and azure_devops_service.organization:
        try:
            live_story = await azure_devops_service.get_single_work_item(clean_id)
            if live_story:
                return extract_criteria_from_ado_item(live_story)
        except Exception:
            pass

    # Check mock fallback
    for mock_item in MOCK_WORK_ITEMS:
        if mock_item.id.upper() in (clean_id, f"US-{clean_id}"):
            lines = [l.strip() for l in (mock_item.acceptance_criteria or "").split("\n") if l.strip()]
            return [
                AcceptanceCriteriaRead(
                    id=f"{mock_item.id}-AC-{idx:02d}",
                    user_story_id=mock_item.id,
                    criteria_number=idx,
                    text=line
                )
                for idx, line in enumerate(lines, start=1)
            ]

    return []


@router.get("/work-items/{work_item_id}", response_model=DevOpsWorkItem)
async def get_work_item(
    work_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve User Story or Work Item directly from database or Azure DevOps API."""
    try:
        item = await devops_service.get_work_item(work_item_id, db=db)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Azure DevOps API: {str(e)}")


@router.get("/acceptance-criteria", response_model=List[AcceptanceCriteriaItem])
async def get_acceptance_criteria(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve available Acceptance Criteria across database and Azure DevOps work items."""
    try:
        db_criteria = db.query(AcceptanceCriteria).all()
        if db_criteria:
            result = []
            for ac in db_criteria:
                story = db.query(UserStory).filter(UserStory.id == ac.user_story_id).first()
                result.append(
                    AcceptanceCriteriaItem(
                        id=ac.id,
                        work_item_id=ac.user_story_id,
                        user_story_title=story.title if story else ac.user_story_id,
                        criteria_number=ac.criteria_number,
                        text=ac.text
                    )
                )
            return result
        criteria = await devops_service.get_acceptance_criteria_list()
        return criteria
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Acceptance Criteria: {str(e)}")


@router.get("/search", response_model=List[DevOpsWorkItem])
async def search_work_items(
    q: str = Query("", description="Query text to search Azure DevOps Work Items"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search Azure DevOps work items by ID or keywords."""
    db_stories = db.query(UserStory).all()
    if db_stories:
        items = []
        for s in db_stories:
            if not q or q.lower() in s.id.lower() or q.lower() in s.title.lower() or q.lower() in (s.description or "").lower():
                acs = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id == s.id).all()
                ac_text = "\n".join([ac.text for ac in acs]) if acs else s.description
                items.append(
                    DevOpsWorkItem(
                        id=s.id,
                        title=s.title,
                        work_item_type="User Story",
                        description=s.description or "",
                        acceptance_criteria=ac_text,
                        state=s.state or "Active",
                        assigned_to=s.assigned_to or "QA Team"
                    )
                )
        if items:
            return items

    items = await devops_service.search_work_items(q)
    return items
