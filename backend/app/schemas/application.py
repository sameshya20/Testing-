from pydantic import BaseModel
from typing import List, Optional
from app.schemas.test_case import ApplicationLinkPayload

class ApplicationBase(BaseModel):
    name: str
    code: str
    domain: str
    description: Optional[str] = None
    default_url: Optional[str] = None
    business_rules: Optional[str] = None
    user_roles: Optional[str] = None
    key_modules: Optional[str] = None

class ApplicationRead(ApplicationBase):
    id: int
    available_links: List[ApplicationLinkPayload] = []

    class Config:
        from_attributes = True

