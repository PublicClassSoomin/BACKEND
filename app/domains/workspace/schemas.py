"""
워크스페이스 도메인에서 사용하는 요청/응답 스키마를 정의하는 파일입니다.

현재는 워크스페이스 조회 기능과 초대코드 검증 기능에 필요한
요청/응답 스키마를 먼저 정의합니다.
"""

from pydantic import BaseModel

from app.domains.user.schemas import UserRole


class WorkspaceResponse(BaseModel):
    """
    워크스페이스 조회 시 사용하는 응답 스키마입니다.

    현재는 워크스페이스 기본 정보와 초대코드까지만 반환합니다.
    이후 industry, default_language, summary_style 같은 설정 값이 추가되면
    이 스키마에 확장할 수 있습니다.
    """

    workspace_id: int
    name: str
    invite_code: str


class InviteCodeValidateRequest(BaseModel):
    """
    초대코드 유효성 검증 요청 시 사용하는 스키마입니다.
    """

    invite_code: str


class InviteCodeValidateResponse(BaseModel):
    """
    초대코드 유효성 검증 응답 시 사용하는 스키마입니다.

    코드가 유효하면 어떤 워크스페이스의 코드인지 함께 반환합니다.
    """

    valid: bool
    workspace_id: int
    workspace_name: str


class InviteCodeIssueResponse(BaseModel):
    """
    초대코드 발급(재발급) 응답 시 사용하는 스키마입니다.

    현재 구조에서는 워크스페이스별 기본 초대코드 1개만 유지하므로,
    발급 API는 새 초대코드를 생성해 반환합니다.
    """

    workspace_id: int
    invite_code: str


class WorkspaceMemberResponse(BaseModel):
    """
    워크스페이스 소속 멤버 1명을 응답할 때 사용하는 스키마입니다.
    """

    user_id: int
    name: str
    email: str
    role: UserRole


class WorkspaceMemberListResponse(BaseModel):
    """
    워크스페이스 소속 멤버 목록 전체를 응답할 때 사용하는 스키마입니다.
    """

    members: list[WorkspaceMemberResponse]


class WorkspaceMemberRoleUpdateRequest(BaseModel):
    """
    워크스페이스 멤버 역할 변경 요청 시 사용하는 스키마입니다.
    """

    # 허용 가능한 역할은 admin, member, viewer 세 가지로 제한합니다.
    # 이 값을 벗어나면 FastAPI가 422 Validation Error를 반환합니다.
    role: UserRole


class WorkspaceMemberRoleUpdateResponse(BaseModel):
    """
    워크스페이스 멤버 역할 변경 응답 시 사용하는 스키마입니다.
    """

    user_id: int
    role: UserRole
