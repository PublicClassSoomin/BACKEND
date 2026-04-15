# app\domains\workspace\router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infra.database.session import get_db
from app.domains.workspace.schemas import DashboardResponse
from app.domains.workspace.service import DashboardService

router = APIRouter()


@router.get("/{workspace_id}/dashboard", response_model=DashboardResponse)
def get_workspace_dashboard(workspace_id: int, db: Session = Depends(get_db)):
    """
    워크스페이스 홈 대시보드 데이터를 조회합니다.

    - 상태별 회의 목록 (in_progress / scheduled / done)
    - 이번 주 완료 회의 요약 (건수, 총 소요시간)
    - 미결 액션 아이템 (pending)
    - 다음 회의 제안 (추후 AI 연동 예정)
    """
    return DashboardService.get_dashboard(db, workspace_id)
