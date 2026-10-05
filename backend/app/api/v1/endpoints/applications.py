from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User
from app.schemas.application import ApplicationRead
from app.schemas.test_case import ApplicationLinkPayload
from app.api.deps import get_current_user

router = APIRouter()

def build_available_links(app: Application) -> List[ApplicationLinkPayload]:
    """Derives standard available application page links based on default_url and key_modules."""
    base_url = (app.default_url or "https://application.com").rstrip("/")
    if base_url.endswith("/app"):
        base_url = base_url[:-4]
        
    links = [
        ApplicationLinkPayload(name="Login", url=f"{base_url}/login"),
        ApplicationLinkPayload(name="Dashboard", url=f"{base_url}/dashboard"),
    ]
    
    if app.key_modules:
        modules = [m.strip() for m in app.key_modules.split(",") if m.strip()]
        for mod in modules:
            slug = mod.lower().replace(" ", "-").replace("&", "and")
            links.append(ApplicationLinkPayload(name=mod, url=f"{base_url}/{slug}"))
    else:
        links.extend([
            ApplicationLinkPayload(name="Accounts", url=f"{base_url}/accounts"),
            ApplicationLinkPayload(name="Payments", url=f"{base_url}/payments"),
            ApplicationLinkPayload(name="Reports", url=f"{base_url}/reports"),
        ])
    
    return links

@router.get("", response_model=List[ApplicationRead])
def get_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all registered enterprise applications from the database with available links."""
    apps = db.query(Application).all()
    result = []
    for app in apps:
        app_read = ApplicationRead.model_validate(app)
        app_read.available_links = build_available_links(app)
        result.append(app_read)
    return result

@router.get("/{app_id}", response_model=ApplicationRead)
def get_application(app_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve single application details by ID."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application with ID {app_id} not found in database.")
    app_read = ApplicationRead.model_validate(app)
    app_read.available_links = build_available_links(app)
    return app_read


