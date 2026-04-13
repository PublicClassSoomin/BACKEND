"""
공통 데이터베이스 세션 설정 파일입니다.

- engine: DB 연결 본체입니다.
- SessionLocal: DB 작업 시 사용할 세션 팩토리입니다.
- Base: SQLAlchemy 모델 클래스들이 상속받는 기준 클래스입니다.
- get_db(): FastAPI에서 DB 세션을 주입할 때 사용하는 함수입니다.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL or "sqlite:///./app.db"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 생성하고 요청이 끝나면 정리합니다.

    FastAPI의 Depends와 함께 사용하여 각 요청마다 독립적인 DB 세션을 주입할 수 있도록 합니다.

    Yields:
        SQLAlchemy 세션 객체를 반환합니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
