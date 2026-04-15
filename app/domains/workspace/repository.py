"""
워크스페이스 도메인의 데이터베이스 접근 로직을 담당하는 파일입니다.

현재는 인증 흐름과 워크스페이스 조회 기능에 필요한
최소 조회/생성 기능만 먼저 구현합니다.
"""

from sqlalchemy.orm import Session

from app.domains.workspace.models import Workspace


def get_workspace_by_invite_code(db: Session, invite_code: str) -> Workspace | None:
    """
    초대코드를 기준으로 워크스페이스를 조회합니다.

    Args:
        db: 데이터베이스 세션입니다.
        invite_code: 조회할 초대코드입니다.

    Returns:
        워크스페이스가 존재하면 Workspace 객체를 반환하고,
        존재하지 않으면 None을 반환합니다.
    """
    return db.query(Workspace).filter(Workspace.invite_code == invite_code).first()


def get_workspace_by_id(db: Session, workspace_id: int) -> Workspace | None:
    """
    워크스페이스 ID를 기준으로 워크스페이스를 조회합니다.

    워크스페이스 상세 조회나 이후 설정/멤버/연동 기능에서
    공통으로 사용할 수 있는 기본 조회 함수입니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 조회할 워크스페이스 ID입니다.

    Returns:
        워크스페이스가 존재하면 Workspace 객체를 반환하고,
        존재하지 않으면 None을 반환합니다.
    """
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def create_workspace(db: Session, name: str, invite_code: str) -> Workspace:
    """
    새로운 워크스페이스를 생성하고 데이터베이스에 저장합니다.

    Args:
        db: 데이터베이스 세션입니다.
        name: 워크스페이스 이름입니다.
        invite_code: 초대코드입니다.

    Returns:
        저장이 완료된 Workspace 객체를 반환합니다.
    """
    workspace = Workspace(
        name=name,
        invite_code=invite_code,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


def update_workspace_invite_code(
    db: Session,
    workspace_id: int,
    invite_code: str,
) -> Workspace | None:
    """
    특정 워크스페이스의 초대코드를 새 값으로 갱신합니다.

    현재 구조에서는 워크스페이스별 기본 초대코드 1개만 저장하므로,
    초대코드 발급 API는 새 코드를 생성해서 기존 값을 교체하는 방식으로 처리합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 초대코드를 갱신할 워크스페이스 ID입니다.
        invite_code: 새로 저장할 초대코드입니다.

    Returns:
        갱신된 Workspace 객체를 반환하고, 워크스페이스가 존재하지 않으면 None을 반환합니다.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        return None

    # 현재 저장된 기본 초대코드를 새 코드로 교체합니다.
    workspace.invite_code = invite_code

    db.commit()
    db.refresh(workspace)

    return workspace
