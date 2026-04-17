# app\api\v1\api_router.py
from fastapi import APIRouter

from app.api.v1.routers.workspaces import router as workspaces_router
from app.api.v1.routers.meetings import router as meetings_router
from app.api.v1.routers.knowledge import router as knowledge_router

api_router = APIRouter()

# Workspaces: 홈 대시보드 등
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])

# Meetings: 생성, 히스토리
api_router.include_router(meetings_router, prefix="/meetings", tags=["Meetings"])

# Knowledge: 과거 회의 검색
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
