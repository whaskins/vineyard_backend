from fastapi import APIRouter

from app.api.api_v1.endpoints import issues, login, maintenance, users, vines

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vines.router, prefix="/vines", tags=["vines"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])