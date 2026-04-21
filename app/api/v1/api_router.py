# app\api\v1\api_router.py
from fastapi import APIRouter

from app.domains.action.router import router as action_router
from app.domains.integration.router import router as integration_router
from app.domains.knowledge.router import router as knowledge_router
from app.domains.user.router import router as user_router
from app.domains.vision.router import router as vision_router
from app.domains.workspace.router import router as workspace_router

# (과거 구조에서 사용한 경우만 아래에서 임포트 해제/대체!)
# from app.api.v1.routers.workspaces import router as workspaces_router
# from app.api.v1.routers.meetings import router as meetings_router

api_router = APIRouter()

<<<<<<< HEAD
# 1. 사용자 및 인증 도메인 (회원가입, 로그인, 음성 특징 등록)
# api_router.include_router(user_router, prefix="/users", tags=["Users"])

# 2. 회의 도메인 (실시간 회의 시작, 음성 스트림 처리, 과거 기록/스크립트 조회)
# api_router.include_router(meeting_router, prefix="/meetings", tags=["Meetings"])
# (아래 줄은 이전 v1 구조에서 사용)
# api_router.include_router(meetings_router, prefix="/meetings", tags=["Meetings"])

# 3. 인텔리전스 도메인 (회의 요약본 조회, 결정사항 리스트 확인)
# api_router.include_router(intelligence_router, prefix="/intelligences", tags=["Intelligence"])

# 4. 지식 베이스 도메인 (과거 자료 검색, 챗봇 대화 엔드포인트)
api_router.include_router(knowledge_router, prefix="/knowledges", tags=["Knowledge"])

# 5. 액션 도메인 (생성된 WBS 조회, 외부 툴 연동 상태 확인)
api_router.include_router(action_router, prefix="/actions", tags=["Actions"])

# 6. 비전 도메인 (스크린샷 분석 결과 조회)
api_router.include_router(vision_router, prefix="/visions", tags=["Vision"])

# 7. 워크스페이스 도메인
# api_router.include_router(workspace_router, prefix="/workspaces", tags=["Workspace"])
# (아래 줄은 이전 v1 구조에서 사용)
# api_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])

# 8. API 연동 통합 도메인
=======
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(workspace_router, prefix="/workspaces", tags=["Workspace"])
>>>>>>> main
api_router.include_router(integration_router, prefix="/integrations", tags=["Integration"])
api_router.include_router(knowledge_router, prefix="/knowledges", tags=["Knowledge"])
api_router.include_router(action_router, prefix="/actions", tags=["Actions"])
api_router.include_router(vision_router, prefix="/visions", tags=["Vision"])
