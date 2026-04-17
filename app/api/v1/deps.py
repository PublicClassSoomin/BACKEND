# app/api/v1/deps.py
"""API v1 공통 의존성 (인증 완성 전 임시 스텁 등)."""


def get_current_user_id() -> int:
    """임시: 로그인 완성 전까지 고정 사용자 ID 반환."""
    return 1
