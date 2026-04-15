"""
워크스페이스 도메인의 API 엔드포인트를 정의하는 파일입니다.

현재는 워크스페이스 조회 기능과 초대코드 검증 기능부터 먼저 구현합니다.
이후 초대코드 발급, 초대코드 목록 조회, 설정 수정 기능을
이 router에 이어서 추가할 수 있습니다.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.workspace.schemas import (
    InviteCodeIssueResponse,
    InviteCodeValidateRequest,
    InviteCodeValidateResponse,
    WorkspaceMemberListResponse,
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceMemberRoleUpdateResponse,
    WorkspaceResponse,
)
from app.domains.workspace.service import (
    get_workspace_members_service,
    get_workspace_service,
    issue_workspace_invite_code_service,
    update_workspace_member_role_service,
    validate_invite_code_service,
)


router = APIRouter()


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    """
    워크스페이스 정보를 조회하는 API 엔드포인트입니다.

    Args:
        workspace_id: 조회할 워크스페이스 ID입니다.
        db: 요청에 사용되는 데이터베이스 세션입니다.

    Returns:
        조회된 워크스페이스 정보를 반환합니다.
    """
    return get_workspace_service(db, workspace_id)


@router.post(
    "/invite-codes/validate",
    response_model=InviteCodeValidateResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_invite_code(
    payload: InviteCodeValidateRequest,
    db: Session = Depends(get_db),
) -> InviteCodeValidateResponse:
    """
    초대코드 유효성 검증을 처리하는 API 엔드포인트입니다.

    Args:
        payload: 검증할 초대코드 요청 데이터입니다.
        db: 요청에 사용되는 데이터베이스 세션입니다.

    Returns:
        초대코드 검증 결과와 연결된 워크스페이스 정보를 반환합니다.
    """
    return validate_invite_code_service(db, payload.invite_code)


@router.post(
    "/{workspace_id}/invite-codes",
    response_model=InviteCodeIssueResponse,
    status_code=status.HTTP_200_OK,
)
async def issue_workspace_invite_code(
    workspace_id: int,
    db: Session = Depends(get_db),
) -> InviteCodeIssueResponse:
    """
    특정 워크스페이스의 새 초대코드를 발급하는 API 엔드포인트입니다.

    현재 구조에서는 별도 초대코드 테이블 없이 workspaces 테이블의 invite_code를
    갱신하는 방식으로 재발급을 처리합니다.

    Args:
        workspace_id: 초대코드를 발급할 워크스페이스 ID입니다.
        db: 요청에 사용되는 데이터베이스 세션입니다.

    Returns:
        새로 발급된 초대코드 정보를 반환합니다.
    """
    return issue_workspace_invite_code_service(db, workspace_id)


@router.get(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_workspace_members(
    workspace_id: int,
    db: Session = Depends(get_db),
) -> WorkspaceMemberListResponse:
    """
    특정 워크스페이스의 멤버 목록을 조회하는 API 엔드포인트입니다.

    Args:
        workspace_id: 조회할 워크스페이스 ID입니다.
        db: 요청에 사용되는 데이터베이스 세션입니다.

    Returns:
        해당 워크스페이스 소속 멤버 목록을 반환합니다.
    """
    return get_workspace_members_service(db, workspace_id)


@router.patch(
    "/{workspace_id}/members/{user_id}/role",
    response_model=WorkspaceMemberRoleUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_workspace_member_role(
    workspace_id: int,
    user_id: int,
    payload: WorkspaceMemberRoleUpdateRequest,
    db: Session = Depends(get_db),
) -> WorkspaceMemberRoleUpdateResponse:
    """
    특정 워크스페이스 소속 멤버의 역할을 변경하는 API 엔드포인트입니다.

    Args:
        workspace_id: 사용자가 속한 워크스페이스 ID입니다.
        user_id: 역할을 변경할 사용자 ID입니다.
        payload: 새 역할 요청 데이터입니다.
        db: 요청에 사용되는 데이터베이스 세션입니다.

    Returns:
        역할 변경 결과를 반환합니다.
    """
    return update_workspace_member_role_service(
        db=db,
        workspace_id=workspace_id,
        user_id=user_id,
        role=payload.role,
    )
