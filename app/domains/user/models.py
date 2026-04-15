"""
사용자 도메인의 데이터베이스 모델을 정의하는 파일입니다.

models.py는 인증 기능 구현 흐름에서 데이터베이스 테이블 구조를 정의하는 역할을 합니다.
이 파일의 User 모델은 회원가입 시 사용자 정보를 저장하고,
로그인 시 이메일 기준으로 사용자를 조회하기 위한 기본 데이터 구조로 사용됩니다.

인증 기능 구현 흐름은 아래와 같습니다.
1. schemas.py
   - 회원가입/로그인 요청 데이터 형식을 정의합니다.
   - 입력값 검증을 담당합니다.
2. router.py
   - 클라이언트의 요청을 받습니다.
   - 요청을 service 계층으로 전달합니다.
3. service.py
   - 회원가입, 로그인 등의 비즈니스 로직 흐름을 처리합니다.
   - 필요 시 repository를 호출합니다.
4. repository.py
   - 실제 데이터베이스 조회/저장 작업을 수행합니다.
5. models.py
   - 데이터베이스에 어떤 형태로 저장할지 테이블 구조를 정의합니다.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    """
    사용자 정보를 저장하는 테이블 모델입니다.

    현재 인증 기능에서 필요한 최소 정보만 먼저 정의합니다.
    이후 워크스페이스 참여, 프로필, 권한 확장 등이 필요해지면
    컬럼을 추가하는 방식으로 확장할 수 있습니다.
    """

    __tablename__ = "users"

    # 사용자 고유 번호입니다.
    # 각 사용자를 구분하는 기본 키이며, 내부 식별자로 사용합니다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 로그인에 사용할 이메일입니다.
    # 중복 회원가입을 막기 위해 unique=True를 설정합니다.
    # 로그인 시 자주 조회되므로 index도 함께 설정합니다.
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # 사용자의 원본 비밀번호 대신 해시된 비밀번호를 저장합니다.
    # 로그인 시에는 사용자가 입력한 비밀번호를 해시 비교하여 검증합니다.
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # 사용자 이름입니다.
    # 회원가입 후 응답 데이터나 사용자 표시 정보에 활용할 수 있습니다.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # 사용자 역할입니다.
    # 현재는 admin / member / viewer 값을 문자열로 저장하는 구조를 사용합니다.
    # 이후 권한 분기나 관리자 기능 접근 제어에 활용합니다.
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="member",
    )

    # 사용자가 속한 워크스페이스 ID입니다.
    # 관리자는 가입 시 생성된 워크스페이스와 연결되고,
    # 멤버는 초대코드 검증 후 해당 워크스페이스에 연결됩니다.
    workspace_id: Mapped[int | None] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=True,
    )

    # 계정 활성 상태입니다.
    # 추후 비활성화/정지/탈퇴 처리 시 사용할 수 있도록 추가합니다.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # 계정 생성 시각입니다.
    # 회원가입 시점을 기록하기 위해 현재 UTC 시간을 저장합니다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
