from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class AreaRead(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    application_id: Optional[int] = None
    parent_id: Optional[int] = None
    path: Optional[str] = None

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
    state: Optional[str] = "Active"
    assigned_to: Optional[str] = "QA Team"
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
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


class AzureDevOpsConnectRequest(BaseModel):
    organization: Optional[str] = None
    project: Optional[str] = None
    pat: Optional[str] = None


class AzureDevOpsProjectItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    state: Optional[str] = "wellFormed"


class AzureDevOpsConnectResponse(BaseModel):
    connected: bool
    organization: str
    project: Optional[str] = None
    message: str
    projects: List[AzureDevOpsProjectItem] = []
    mode: Optional[str] = "mock"


class AzureDevOpsConfigResponse(BaseModel):
    organization: str
    project: str
    is_pat_configured: bool
    connected: bool
    mode: Optional[str] = "mock"


class AzureDevOpsConfigUpdate(BaseModel):
    organization: str
    project: str
    pat: Optional[str] = None


class AzureDevOpsAreaItem(BaseModel):
    id: int
    name: str
    path: str
    has_children: bool = False
    children: List['AzureDevOpsAreaItem'] = []

    model_config = ConfigDict(from_attributes=True)


class AzureDevOpsSyncRequest(BaseModel):
    test_cases: List[dict]
    work_item_id: Optional[str] = None
    area_path: Optional[str] = None
    project: Optional[str] = None


class AzureDevOpsSyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int
    updated_count: int
    failed_count: int
    test_cases: List[dict]

