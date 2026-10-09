from fastapi import APIRouter
from app.api.v1.endpoints import auth, applications, devops, generation, export

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(devops.router, prefix="/devops", tags=["Azure DevOps"])
api_router.include_router(devops.router, prefix="/azure-devops", tags=["Azure DevOps Alias"])
api_router.include_router(generation.router, prefix="/generation", tags=["Test Generation"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
