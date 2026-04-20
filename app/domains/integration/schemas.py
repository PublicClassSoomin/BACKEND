# app\domains\integration\schemas.py

from datetime import datetime

from pydantic import BaseModel


class IntegrationItemResponse(BaseModel):
    service: str
    is_connected: bool
    created_at: datetime | None = None


class IntegrationListResponse(BaseModel):
    integrations: list[IntegrationItemResponse]
