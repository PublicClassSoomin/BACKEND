"""
워크스페이스 도메인의 데이터베이스 모델을 정의하는 파일입니다.

현재는 워크스페이스 기본 정보와 설정 필드, 그리고 부서 관리 기능에서
사용할 Department 모델까지 함께 정의합니다.
"""

from datetime import datetime, timezone
import enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

class MemberRole(str, enum.Enum):
    admin   = "admin"
    member  = "member"
    viewer  = "viewer"

class Workspace(Base):
    """
    워크스페이스 정보를 저장하는 테이블 모델입니다.

    현재는 워크스페이스 이름, 초대코드와 함께
    설정 페이지에서 사용할 기본 필드도 함께 저장합니다.
    """

    __tablename__ = "workspaces"

    # 워크스페이스 고유 ID입니다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 워크스페이스 이름입니다.
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 현재 사용 중인 기본 초대코드입니다.
    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    # 팀 업종입니다.
    # 아직 입력되지 않은 상태를 허용하기 위해 nullable=True로 둡니다.
    industry: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 워크스페이스 기본 언어입니다.
    # 예: ko, en
    default_language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # 회의 요약 스타일입니다.
    # 예: concise, detailed
    summary_style: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # 로고 이미지 URL입니다.
    logo_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 생성 시각입니다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Department(Base):
    """
    워크스페이스별 부서 정보를 저장하는 테이블 모델입니다.

    부서 관리 페이지에서 CRUD를 수행할 수 있도록 workspace_id 기준으로 부서를 분리해서 저장합니다.
    """

    __tablename__ = "departments"

    # 부서 고유 ID입니다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 어떤 워크스페이스의 부서인지 나타내는 외래 키입니다.
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    # 부서 이름입니다.
    # 같은 워크스페이스 안에서 의미를 가지는 값입니다.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # 생성 시각입니다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # 수정 시각입니다.
    # PATCH로 이름 변경 시 자동 갱신됩니다.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
