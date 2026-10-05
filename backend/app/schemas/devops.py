from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class AreaRead(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    application_id: Optional[int] = None
    parent_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserStoryRead(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    state: Optional[str] = "Active"
    assigned_to: Optional[str] = "QA Team"
    area_id: int

    model_config = ConfigDict(from_attributes=True)


class AcceptanceCriteriaRead(BaseModel):
    id: str
    user_story_id: str
    criteria_number: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class DevOpsWorkItem(BaseModel):
    id: str
    title: str
    work_item_type: str
    description: Optional[str] = ""
    acceptance_criteria: Optional[str] = ""
    state: Optional[str] = "Approved"
    assigned_to: Optional[str] = "QA Team"
    tags: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)


class AcceptanceCriteriaItem(BaseModel):
    id: str
    work_item_id: str
    user_story_title: str
    criteria_number: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class DevOpsSearchResponse(BaseModel):
    items: List[DevOpsWorkItem]
