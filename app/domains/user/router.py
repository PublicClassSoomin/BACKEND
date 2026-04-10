# app\domains\user\router.py

from fastapi import APIRouter, status

from app.domains.user.schemas import (
    AdminSignupRequest,
    LoginRequest,
    MemberSignupRequest,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    TokenResponse,
    UserResponse,
)
from app.domains.user.service import (
    change_password_service,
    login_service,
    request_password_reset_service,
    signup_admin_service,
    signup_member_service,
)


router = APIRouter()


@router.post(
    "/signup/admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup_admin(payload: AdminSignupRequest) -> UserResponse:
    """
    관리자 회원가입 요청을 처리하는 API 엔드포인트입니다.

    요청 데이터 검증은 Pydantic 스키마가 담당하고,
    실제 처리 로직은 service 계층에 위임합니다.

    Args:
        payload: 관리자 회원가입 요청 데이터입니다.

    Returns:
        회원가입 처리 결과 사용자 정보를 반환합니다.
    """
    return signup_admin_service(payload)


@router.post(
    "/signup/member",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup_member(payload: MemberSignupRequest) -> UserResponse:
    """
    멤버 회원가입 요청을 처리하는 API 엔드포인트입니다.

    Args:
        payload: 멤버 회원가입 요청 데이터입니다.

    Returns:
        회원가입 처리 결과 사용자 정보를 반환합니다.
    """
    return signup_member_service(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(payload: LoginRequest) -> TokenResponse:
    """
    로그인 요청을 처리하는 API 엔드포인트입니다.

    Args:
        payload: 로그인 요청 데이터입니다.

    Returns:
        로그인 처리 결과 토큰 정보를 반환합니다.
    """
    return login_service(payload)


@router.post(
    "/password-reset",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(payload: PasswordResetRequest) -> MessageResponse:
    """
    비밀번호 재설정 메일 발송 요청을 처리하는 API 엔드포인트입니다.

    Args:
        payload: 비밀번호 재설정 메일 발송 요청 데이터입니다.

    Returns:
        요청 처리 결과 메시지를 반환합니다.
    """
    return request_password_reset_service(payload)


@router.post(
    "/password-change",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(payload: PasswordChangeRequest) -> MessageResponse:
    """
    비밀번호 변경 요청을 처리하는 API 엔드포인트입니다.

    Args:
        payload: 비밀번호 변경 요청 데이터입니다.

    Returns:
        요청 처리 결과 메시지를 반환합니다.
    """
    return change_password_service(payload)
