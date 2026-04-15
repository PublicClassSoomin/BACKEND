"""
워크스페이스 도메인의 비즈니스 로직을 처리하는 파일입니다.

현재는 워크스페이스 조회 기능과 초대코드 검증 기능부터 구현하며,
이후 초대코드 발급/조회 기능과 워크스페이스 설정/멤버/연동 기능이 추가되면
이 파일에 비즈니스 로직을 확장해 나가야 합니다.
"""

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.user.repository import (
    get_user_by_id,
    get_users_by_workspace_id,
    update_user_role,
)
from app.domains.workspace.repository import (
    get_workspace_by_id,
    get_workspace_by_invite_code,
    update_workspace_invite_code,
)
from app.domains.workspace.schemas import (
    InviteCodeIssueResponse,
    InviteCodeValidateResponse,
    WorkspaceMemberListResponse,
    WorkspaceMemberRoleUpdateResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)


def _generate_invite_code() -> str:
    """
    워크스페이스 초대코드를 생성합니다.

    현재는 대문자 기반 8자리 문자열을 사용합니다.
    워크스페이스 기능에서 초대코드를 재발급할 때 같은 규칙을 사용하기 위해
    service 계층 내부에 별도 함수로 둡니다.
    """
    return secrets.token_hex(4).upper()


def get_workspace_service(db: Session, workspace_id: int) -> WorkspaceResponse:
    """
    워크스페이스 상세 조회를 처리하는 비즈니스 로직입니다.

    처리 순서는 다음과 같습니다.
    1. workspace_id를 기준으로 워크스페이스가 존재하는지 조회합니다.
    2. 워크스페이스가 존재하는지 확인하고, 존재하지 않으면 404 Not Found 예외를 발생시킵니다.
    3. 응답 스키마 형식으로 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 조회할 워크스페이스 ID입니다.

    Returns:
        조회된 워크스페이스 정보를 반환합니다.

    Raises:
        HTTPException: 워크스페이스가 존재하지 않을 경우 404 Not Found 예외를 발생시킵니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    return WorkspaceResponse(
        workspace_id=workspace.id,
        name=workspace.name,
        invite_code=workspace.invite_code,
    )


def validate_invite_code_service(
    db: Session,
    invite_code: str,
) -> InviteCodeValidateResponse:
    """
    초대코드 유효성 검증을 처리합니다.

    처리 순서는 다음과 같습니다.
    1. invite_code 기준으로 워크스페이스를 조회합니다.
    2. 코드가 유효한지 확인합니다.
    3. 유효하면 워크스페이스 정보를 포함해 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        invite_code: 검증할 초대코드입니다.

    Returns:
        초대코드 검증 결과와 연결된 워크스페이스 정보를 반환합니다.

    Raises:
        HTTPException: 초대코드가 유효하지 않을 경우 400 Bad Request 예외를 발생시킵니다.
    """
    workspace = get_workspace_by_invite_code(db, invite_code)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 초대코드입니다.",
        )

    return InviteCodeValidateResponse(
        valid=True,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
    )


def get_workspace_members_service(
    db: Session,
    workspace_id: int,
) -> WorkspaceMemberListResponse:
    """
    워크스페이스 소속 멤버 목록 조회를 처리합니다.

    처리 순서는 다음과 같습니다.
    1. workspace_id 기준으로 워크스페이스가 존재하는지 확인합니다.
    2. 해당 워크스페이스 소속 사용자 목록을 조회합니다.
    3. 응답 스키마 형식으로 변환하여 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 조회할 워크스페이스 ID입니다.

    Returns:
        해당 워크스페이스 소속 멤버 목록을 반환합니다.

    Raises:
        HTTPException: 워크스페이스가 존재하지 않을 경우 404 에러를 발생시킵니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    users = get_users_by_workspace_id(db, workspace_id)

    return WorkspaceMemberListResponse(
        members=[
            WorkspaceMemberResponse(
                user_id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
            )
            for user in users
        ]
    )


def update_workspace_member_role_service(
    db: Session,
    workspace_id: int,
    user_id: int,
    role: str,
) -> WorkspaceMemberRoleUpdateResponse:
    """
    워크스페이스 소속 멤버의 역할 변경을 처리합니다.

    처리 순서는 다음과 같습니다.
    1. workspace_id 기준으로 워크스페이스가 존재하는지 확인합니다.
    2. user_id 기준으로 사용자가 존재하는지 확인합니다.
    3. 해당 사용자가 요청한 워크스페이스 소속인지 확인합니다.
    4. 역할을 변경하고 저장한 뒤 응답 형식으로 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 사용자가 속한 워크스페이스 ID입니다.
        user_id: 역할을 변경할 사용자 ID입니다.
        role: 새로 저장할 역할 문자열입니다.

    Returns:
        역할이 변경된 사용자 정보를 반환합니다.

    Raises:
        HTTPException: 워크스페이스나 사용자가 존재하지 않거나, 사용자가 해당 워크스페이스 소속이 아닐 경우 예외를 발생시킵니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    if user.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 워크스페이스 소속 사용자가 아닙니다.",
        )

    updated_user = update_user_role(db, user_id, role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return WorkspaceMemberRoleUpdateResponse(
        user_id=updated_user.id,
        role=updated_user.role,
    )


def issue_workspace_invite_code_service(
    db: Session,
    workspace_id: int,
) -> InviteCodeIssueResponse:
    """
    워크스페이스 초대코드 발급(재발급)을 처리합니다.

    처리 순서는 다음과 같습니다.
    1. workspace_id 기준으로 워크스페이스가 존재하는지 확인합니다.
    2. 새 초대코드를 생성합니다.
    3. 워크스페이스의 기본 초대코드를 새 값으로 갱신합니다.
    4. 갱신 결과를 응답 형식으로 반환합니다.

    Args:
        db: 데이터베이스 세션입니다.
        workspace_id: 초대코드를 발급할 워크스페이스 ID입니다.

    Returns:
        새로 발급된 초대코드 정보를 반환합니다.

    Raises:
        HTTPException: 워크스페이스가 존재하지 않을 경우 404 에러를 발생시킵니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    new_invite_code = _generate_invite_code()

    # 현재 구조에서는 기본 초대코드 1개만 유지하므로,
    # 새 코드를 발급하면 기존 코드를 새 값으로 덮어씁니다.
    updated_workspace = update_workspace_invite_code(
        db=db,
        workspace_id=workspace_id,
        invite_code=new_invite_code,
    )

    if not updated_workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    return InviteCodeIssueResponse(
        workspace_id=updated_workspace.id,
        invite_code=updated_workspace.invite_code,
    )
