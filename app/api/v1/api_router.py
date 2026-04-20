# app\api\v1\api_router.py
from fastapi import APIRouter

from app.domains.integration.router import router as integration_router
from app.domains.meeting.router import router as meeting_router
from app.domains.user.router import router as user_router
from app.domains.workspace.router import router as workspace_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(workspace_router, prefix="/workspaces", tags=["Workspace"])
api_router.include_router(integration_router, prefix="/integrations", tags=["Integration"])
api_router.include_router(meeting_router, prefix="/meetings", tags=["Meetings"])
