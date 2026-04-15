
"""
외부 연동(integration) 도메인의 데이터베이스 모델을 정의하는 파일입니다.

워크스페이스가 생성되면 기본적으로 JIRA, Slack, Notion, Google Calendar,
카카오톡 연동 상태를 저장할 수 있어야 하므로 integrations 테이블을 먼저 정의합니다.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Integration(Base):
    """
    워크스페이스별 외부 서비스 연동 상태를 저장하는 테이블 모델입니다.

    현재 단계에서는 각 서비스가 연결되었는지 여부만 먼저 저장합니다.
    이후 OAuth 토큰, 만료 시각, 설정값 등이 필요해지면 컬럼을 추가해서 확장할 수 있습니다.
    """

    __tablename__ = "integrations"

    # integration row 자체의 고유 ID입니다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 어떤 워크스페이스의 연동 정보인지 연결하는 외래 키입니다.
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    # 외부 서비스 이름입니다.
    # 현재는 jira, slack, notion, google_calendar, kakao 다섯 가지를 사용합니다.
    service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # 실제 연동이 완료되었는지 여부입니다.
    # 워크스페이스 생성 직후에는 기본 row만 만들고 아직 연결되지 않은 상태이므로 False로 시작합니다.
    is_connected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # row 생성 시각입니다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
