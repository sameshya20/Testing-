from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.devops import (
    DevOpsWorkItem,
    AcceptanceCriteriaItem,
    AreaRead,
    UserStoryRead,
    AcceptanceCriteriaRead
)
from app.models.devops import Area, UserStory, AcceptanceCriteria
from app.services.devops_service import devops_service
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

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
def get_acceptance_criteria_by_multiple_user_stories(
    story_ids: Optional[List[str]] = Query(None, description="List of User Story IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all Acceptance Criteria belonging to selected User Stories from database (requires login)."""
    if not story_ids:
        return []

    # Clean and normalize story IDs
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

    # Query database for criteria
    from sqlalchemy import func
    criteria = db.query(AcceptanceCriteria).filter(
        func.upper(AcceptanceCriteria.user_story_id).in_(normalized_ids)
    ).order_by(AcceptanceCriteria.user_story_id, AcceptanceCriteria.criteria_number).all()

    # Deduplicate criteria by ID while preserving order
    unique_criteria: List[AcceptanceCriteriaRead] = []
    seen_ids = set()
    for c in criteria:
        clean_cid = c.id.strip().upper()
        if clean_cid not in seen_ids:
            seen_ids.add(clean_cid)
            unique_criteria.append(c)

    # Check for any stories not found in DB, search mock data
    found_story_ids = {c.user_story_id.upper() for c in unique_criteria}
    from app.services.devops_service import MOCK_WORK_ITEMS
    for sid in story_ids:
        clean = sid.strip().upper()
        if clean not in found_story_ids and f"US-{clean}" not in found_story_ids:
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
def get_acceptance_criteria_by_user_story(
    story_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all Acceptance Criteria belonging to selected User Story from database (requires login)."""
    clean_id = story_id.strip().upper()
    story = db.query(UserStory).filter(UserStory.id.ilike(clean_id)).first()
    if not story and not clean_id.startswith("US-"):
        story = db.query(UserStory).filter(UserStory.id.ilike(f"US-{clean_id}")).first()

    if not story:
        # Fallback query if criteria exist directly
        criteria = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id.ilike(clean_id)).all()
        return criteria

    criteria = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.user_story_id == story.id).order_by(AcceptanceCriteria.criteria_number).all()
    return criteria

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
