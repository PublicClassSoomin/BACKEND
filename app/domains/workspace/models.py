"""
워크스페이스 도메인의 데이터베이스 모델을 정의하는 파일입니다.

현재는 인증 흐름과 연결하기 위해 최소한의 Workspace 모델만 먼저 정의합니다.
관리자 회원가입 시 기본 워크스페이스를 생성하고,
멤버 회원가입 시 invite_code를 기준으로 워크스페이스를 찾는 데 사용합니다.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Workspace(Base):
    """
    워크스페이스 정보를 저장하는 테이블 모델입니다. 재는 워크스페이스 이름과 초대코드를 저장하는 최소 구조만 사용합니다.
    """

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
