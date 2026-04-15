"""
외부 연동(integration) 도메인의 API 엔드포인트를 정의하는 파일입니다.

현재는 워크스페이스별 전체 연동 상태 조회 기능부터 구현합니다.
이후 서비스 연결, 해제, 토큰 갱신 API를 이 router에 이어서 추가할 수 있습니다.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.integration.schemas import IntegrationListResponse
from app.domains.integration.service import get_integrations_service


router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}",
    response_model=IntegrationListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_integrations(
    workspace_id: int,
    db: Session = Depends(get_db),
) -> IntegrationListResponse:
    """
    특정 워크스페이스의 전체 연동 상태를 조회하는 API 엔드포인트입니다.

    Args:
        workspace_id: 조회할 워크스페이스 ID입니다.
        db: 데이터베이스 세션입니다.

    Returns:
        해당 워크스페이스의 연동 상태 목록을 반환합니다.
    """
    return get_integrations_service(db, workspace_id)
