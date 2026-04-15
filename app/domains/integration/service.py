"""
외부 연동(integration) 도메인의 비즈니스 로직을 처리하는 파일입니다.

현재는 워크스페이스별 연동 상태 조회 기능부터 구현합니다.
이후 connect, disconnect, refresh 같은 연동 제어 기능도
이 service 계층을 기준으로 확장할 예정입니다.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.integration.repository import get_integrations_by_workspace_id
from app.domains.integration.schemas import (
    IntegrationItemResponse,
    IntegrationListResponse,
)


def get_integrations_service(db: Session, workspace_id: int) -> IntegrationListResponse:
    """
    워크스페이스별 전체 연동 상태 조회를 처리합니다.

    처리 순서는 다음과 같습니다.
    1. workspace_id 기준으로 integration row 목록을 조회합니다.
    2. 데이터가 존재하는지 확인합니다.
    3. 응답 스키마 형식으로 변환하여 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 조회할 워크스페이스 ID입니다.

    Returns:
        해당 워크스페이스의 연동 상태 목록을 반환합니다.

    Raises:
        HTTPException: 해당 워크스페이스의 integration 데이터가 없을 경우 404 에러를 발생시킵니다.
    """
    integrations = get_integrations_by_workspace_id(db, workspace_id)

    # 현재 구조에서는 워크스페이스 생성 시 기본 integration 5개가 함께 생성되므로,
    # 목록이 비어 있으면 잘못된 workspace_id이거나 데이터 생성이 누락된 상태로 판단합니다.
    if not integrations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연동 정보를 찾을 수 없습니다.",
        )

    return IntegrationListResponse(
        integrations=[
            IntegrationItemResponse(
                service=integration.service,
                is_connected=integration.is_connected,
                created_at=integration.created_at,
            )
            for integration in integrations
        ]
    )
