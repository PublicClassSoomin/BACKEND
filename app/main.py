# app\main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 각 도메인에서 router 만들어서 연결해주세요.
# from app.api.v1.api_router import api_router
from app.core.lifespan import lifespan
from app.domains.integration.models import Integration
from app.domains.user.models import User
from app.domains.user.router import router as user_router
from app.domains.workspace.models import Department, Workspace
from app.domains.workspace.router import router as workspace_router
from app.domains.integration.router import router as integration_router
from app.domains.meeting.models import Meeting
from app.domains.meeting.router import router as meeting_router


app = FastAPI(title="Meeting Assistant Agent API", lifespan=lifespan)

# 웹 프론트엔드 통신 허용 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 경로
@app.get("/")
async def root():
    return {"message": "Meeting Assistant Agent API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 사용자 인증 관련 라우터를 연결합니다. 
app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])

# 워크스페이스 조회 관련 라우터를 연결합니다. 
app.include_router(workspace_router, prefix="/api/v1/workspaces", tags=["Workspaces"])

app.include_router(
    integration_router,
    prefix="/api/v1/integrations",
    tags=["Integrations"],
)
app.include_router(meeting_router, prefix="/api/v1/meetings", tags=["Meetings"])
