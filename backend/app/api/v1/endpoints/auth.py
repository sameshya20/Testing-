from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserRead
from app.core.security import verify_password, create_access_token, revoke_token
from app.api.deps import get_current_user, security_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and return bearer access token."""
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated."
        )
    
    token = create_access_token(user.email)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user)
    )

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Get currently authenticated user details."""
    return current_user

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Invalidate current active session token."""
    if credentials and credentials.credentials:
        revoke_token(credentials.credentials)
    return {"status": "success", "message": "Signed out successfully."}
