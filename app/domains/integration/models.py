# app\domains\integration\models.py
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.infra.database.base import Base

class Integration(Base):
    __tablename__ = "integrations"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id     = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    service          = Column(String(50), nullable=False)
    is_connected     = Column(Boolean, default=False, nullable=False)
    created_at       = Column(DateTime, default=func.now(), nullable=False)
