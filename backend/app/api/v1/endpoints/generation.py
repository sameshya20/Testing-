from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User
from app.schemas.test_case import TestCaseGenerationRequest, TestCaseGenerationResponse
from app.services.devops_service import devops_service
from app.services.web_extractor import web_extractor
from app.services.test_generator import test_generator_engine
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/create", response_model=TestCaseGenerationResponse)
async def generate_test_cases(
    payload: TestCaseGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyzes application database rules, multiple Azure DevOps User Stories / Acceptance Criteria,
    and optional Application Link to synthesize Positive, Negative, and Edge test cases.
    """
    # 1. Validation: Application
    if not payload.application_id:
        raise HTTPException(status_code=400, detail="Select an application.")

    app = db.query(Application).filter(Application.id == payload.application_id).first()
    if not app:
        raise HTTPException(status_code=400, detail="Select an application.")

    # 1b. Normalize & validate services and area_ids
    services_list: List[str] = []
    if payload.services:
        services_list = [s.strip() for s in payload.services if s and s.strip()]
    elif payload.service and payload.service.strip():
        services_list = [payload.service.strip()]
    services_list = list(dict.fromkeys(services_list))

    area_ids_list: List[int] = []
    if payload.area_ids:
        area_ids_list = [a for a in payload.area_ids if isinstance(a, int)]
    elif payload.area_id is not None:
        area_ids_list = [payload.area_id]
    area_ids_list = list(dict.fromkeys(area_ids_list))

    from app.models.devops import Area
    if area_ids_list and not services_list:
        matched_areas = db.query(Area).filter(Area.id.in_(area_ids_list)).all()
        services_list = [a.name for a in matched_areas]
    elif services_list and not area_ids_list:
        matched_areas = db.query(Area).filter(Area.name.in_(services_list)).all()
        area_ids_list = [a.id for a in matched_areas]

    # 2. Validation: Requirement identifiers list
    req_ids: List[str] = payload.requirement_identifiers if payload.requirement_identifiers else []
    if not req_ids and payload.requirement_identifier:
        req_ids = [payload.requirement_identifier]

    # Filter out empty strings
    req_ids = [r.strip() for r in req_ids if r and r.strip()]
    if not req_ids:
        raise HTTPException(status_code=400, detail="Select at least one requirement.")

    # 3. Retrieve User Stories / Work Items from Azure DevOps
    stories = []
    selected_ac_filter = None

    if payload.requirement_source == "USER_STORY":
        combined_ids = []
        if payload.user_story_ids:
            for u in payload.user_story_ids:
                clean_u = u.strip().upper() if u else ""
                if clean_u and clean_u not in combined_ids:
                    combined_ids.append(clean_u)
        for r in req_ids:
            clean_r = r.strip().upper() if r else ""
            if clean_r and clean_r not in combined_ids:
                combined_ids.append(clean_r)
        for sid in combined_ids:
            try:
                story = await devops_service.get_work_item(sid, db=db)
                if story and story.id not in [s.id for s in stories]:
                    stories.append(story)
            except Exception:
                pass
    else:
        # ACCEPTANCE_CRITERIA selection mode
        selected_ac_filter = list(dict.fromkeys(req_ids))
        story_ids_order = []

        # 1. Use user_story_ids if explicitly provided
        if payload.user_story_ids:
            for us_id in payload.user_story_ids:
                clean_us = us_id.strip().upper() if us_id else ""
                if clean_us and clean_us not in story_ids_order:
                    story_ids_order.append(clean_us)

        # 2. Look up user_story_id in database for selected criteria
        from app.models.devops import AcceptanceCriteria
        matched_acs = db.query(AcceptanceCriteria).filter(AcceptanceCriteria.id.in_(req_ids)).all()
        for ac in matched_acs:
            if ac.user_story_id:
                clean_sid = ac.user_story_id.strip().upper()
                if clean_sid not in story_ids_order:
                    story_ids_order.append(clean_sid)

        # 3. Extract story prefix from criteria identifiers (e.g. US-101-AC-01 -> US-101)
        for ac_id in req_ids:
            extracted = None
            if "-AC-" in ac_id.upper():
                extracted = ac_id.split("-AC-")[0].strip().upper()
            elif " AC-" in ac_id.upper():
                extracted = ac_id.split(" AC-")[0].strip().upper()
            elif "_AC_" in ac_id.upper():
                extracted = ac_id.split("_AC_")[0].strip().upper()
            if extracted and extracted not in story_ids_order:
                story_ids_order.append(extracted)

        # Fetch work items for each resolved story ID
        for sid in story_ids_order:
            try:
                story = await devops_service.get_work_item(sid, db=db)
                if story and story.id.upper() not in [s.id.upper() for s in stories]:
                    stories.append(story)
            except Exception:
                pass

    if not stories:
        # Fallback to general mock story if none found
        story = await devops_service.get_work_item("US-101", db=db)
        stories = [story]

    # 4. Optional Application Links Extraction
    links_payload = payload.application_links if payload.application_links else []
    if not links_payload and payload.application_url:
        from app.schemas.test_case import ApplicationLinkPayload
        links_payload = [ApplicationLinkPayload(name="Application Page 1", url=payload.application_url)]

    url_analyzed, url_message, page_contexts = await web_extractor.extract_multi_context(links_payload)

    # 5. Generate Test Suite for all requirements and application links
    response = test_generator_engine.generate_multi_requirement_test_suite(
        app=app,
        stories=stories,
        selected_ac_filter=selected_ac_filter,
        url_metadata=page_contexts[0] if page_contexts else {},
        url_analyzed=url_analyzed,
        url_message=url_message,
        page_contexts=page_contexts
    )

    # 6. Persist generated test cases and maintain traceability in database
    try:
        from app.models.test_case import TestCaseRecord
        all_cases = response.positive_test_cases + response.negative_test_cases + response.edge_test_cases
        for tc in all_cases:
            rec = db.query(TestCaseRecord).filter(TestCaseRecord.id == tc.id).first()
            steps_str = "\n".join(tc.test_steps) if isinstance(tc.test_steps, list) else str(tc.test_steps)
            if not rec:
                rec = TestCaseRecord(
                    id=tc.id,
                    azure_work_item_id=str(tc.azure_work_item_id or tc.user_story or ""),
                    azure_test_case_id=tc.azure_test_case_id,
                    application_id=payload.application_id,
                    category=tc.category,
                    priority=tc.priority,
                    scenario=tc.scenario,
                    description=tc.description,
                    preconditions=tc.preconditions,
                    test_data=tc.test_data,
                    test_steps=steps_str,
                    expected_result=tc.expected_result,
                    requirement_ref=tc.requirement_ref,
                    application_page=tc.application_page,
                    application_link=tc.application_link,
                    sync_status="Not Synced",
                    sync_message=""
                )
                db.add(rec)
            else:
                if rec.azure_test_case_id:
                    tc.azure_test_case_id = rec.azure_test_case_id
                    tc.sync_status = rec.sync_status
                    tc.sync_message = rec.sync_message
                rec.azure_work_item_id = str(tc.azure_work_item_id or rec.azure_work_item_id or "")
                rec.category = tc.category
                rec.priority = tc.priority
                rec.scenario = tc.scenario
                rec.description = tc.description
                rec.preconditions = tc.preconditions
                rec.test_data = tc.test_data
                rec.test_steps = steps_str
                rec.expected_result = tc.expected_result
                rec.requirement_ref = tc.requirement_ref
                rec.application_page = tc.application_page
                rec.application_link = tc.application_link
        db.commit()
    except Exception as db_err:
        pass

    return response

