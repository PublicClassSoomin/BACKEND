"""
외부 연동(integration) 도메인의 데이터베이스 접근 로직을 담당하는 파일입니다.

현재는 워크스페이스 생성 직후 기본 연동 상태 row를 자동으로 만들고,
워크스페이스별 연동 상태를 조회하는 기능부터 구현합니다.
"""

from sqlalchemy.orm import Session

from app.domains.integration.models import Integration


DEFAULT_INTEGRATION_SERVICES = [
    "jira",
    "slack",
    "notion",
    "google_calendar",
    "kakao",
]


def create_default_integrations(db: Session, workspace_id: int) -> list[Integration]:
    """
    워크스페이스 생성 직후 기본 integration row 5개를 생성합니다.

    현재는 각 서비스에 대해 연결 전 상태(False)로 기본 데이터를 넣습니다.
    이후 실제 OAuth 연결이 되면 is_connected를 True로 변경하는 흐름으로 확장할 수 있습니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 기본 integration row를 생성할 워크스페이스 ID입니다.

    Returns:
        저장된 Integration 객체 리스트를 반환합니다.
    """
    integrations = [
        Integration(
            workspace_id=workspace_id,
            service=service,
            is_connected=False,
        )
        for service in DEFAULT_INTEGRATION_SERVICES
    ]

    # 여러 row를 한 번에 DB 세션에 추가합니다.
    db.add_all(integrations)

    # INSERT 내용을 실제 DB에 반영합니다.
    db.commit()

    # 각 row의 id 등 최신 상태를 다시 반영합니다.
    for integration in integrations:
        db.refresh(integration)

    return integrations


def get_integrations_by_workspace_id(db: Session, workspace_id: int) -> list[Integration]:
    """
    특정 워크스페이스에 연결된 전체 integration row를 조회합니다.

    연동 관리 페이지에서 워크스페이스별 외부 서비스 연결 상태를 한 번에 보여줄 때 사용합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 조회할 워크스페이스 ID입니다.

    Returns:
        해당 워크스페이스에 속한 Integration 객체 리스트를 반환합니다.
    """
    return (
        db.query(Integration)
        .filter(Integration.workspace_id == workspace_id)
        .order_by(Integration.id.asc())
        .all()
    )