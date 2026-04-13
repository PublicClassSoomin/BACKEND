# app\domains\user\models.py
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, func
from app.infra.database.base import Base
import enum

class SocialProvider(str, enum.Enum):
    """
    users 테이블의 social_provider의 값들 정리
    """
    none = "none"
    google = "google"
    kakao = "kakao"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    social_provider = Column(Enum(SocialProvider), default=SocialProvider.none)
    social_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)