# app\domains\user\service.py

from app.domains.user.schemas import (
    AdminSignupRequest,
    LoginRequest,
    MemberSignupRequest,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    TokenResponse,
    UserResponse,
    UserRole,
)


def signup_admin_service(payload: AdminSignupRequest) -> UserResponse:
    """
    관리자 회원가입 요청을 처리합니다.

    현재 단계에서는 실제 DB 저장 없이,
    요청으로 전달된 값을 기반으로 예시 사용자 정보를 생성하여 반환합니다.

    Args:
        payload: 관리자 회원가입 요청 데이터입니다.

    Returns:
        관리자 역할이 포함된 사용자 응답 데이터를 반환합니다.
    """
    return UserResponse(
        id=1,
        email=payload.email,
        name=payload.name,
        role=UserRole.ADMIN,
    )


def signup_member_service(payload: MemberSignupRequest) -> UserResponse:
    """
    멤버 회원가입 요청을 처리합니다.

    현재 단계에서는 초대코드의 실제 유효성 검사나 워크스페이스 참여 처리 없이,
    예시 멤버 사용자 정보를 생성하여 반환합니다.

    Args:
        payload: 멤버 회원가입 요청 데이터입니다.

    Returns:
        멤버 역할이 포함된 사용자 응답 데이터를 반환합니다.
    """
    return UserResponse(
        id=2,
        email=payload.email,
        name=payload.name,
        role=UserRole.MEMBER,
    )


def login_service(payload: LoginRequest) -> TokenResponse:
    """
    로그인 요청을 처리합니다.

    현재 단계에서는 실제 사용자 인증 없이,
    access token과 refresh token 형식의 예시 데이터를 반환합니다.

    Args:
        payload: 로그인 요청 데이터입니다.

    Returns:
        예시 토큰 응답 데이터를 반환합니다.
    """
    return TokenResponse(
        access_token=f"access-token-for-{payload.email}",
        refresh_token=f"refresh-token-for-{payload.email}",
    )


def request_password_reset_service(
    payload: PasswordResetRequest,
) -> MessageResponse:
    """
    비밀번호 재설정 메일 발송 요청을 처리합니다.

    현재 단계에서는 실제 메일 발송 없이,
    요청 접수 완료 메시지만 반환합니다.

    Args:
        payload: 비밀번호 재설정 메일 발송 요청 데이터입니다.

    Returns:
        재설정 메일 발송 안내 메시지를 반환합니다.
    """
    return MessageResponse(
        message=f"{payload.email} 주소로 비밀번호 재설정 안내를 전송했습니다."
    )


def change_password_service(payload: PasswordChangeRequest) -> MessageResponse:
    """
    비밀번호 변경 요청을 처리합니다.

    현재 단계에서는 실제 토큰 검증 및 비밀번호 저장 없이,
    변경 완료 메시지만 반환합니다.

    Args:
        payload: 비밀번호 변경 요청 데이터입니다.

    Returns:
        비밀번호 변경 완료 메시지를 반환합니다.
    """
    return MessageResponse(message="비밀번호가 성공적으로 변경되었습니다.")
