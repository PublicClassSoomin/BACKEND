# app\domains\integration\service.py
import logging
from sqlalchemy.orm import Session
from typing import List

from app.core.graph.state import SharedState
from app.domains.integration.models import Integration, ServiceType
from app.domains.integration import repository
from app.infra.clients.n8n import N8nClient

logger= logging.getLogger(__name__)

# --- LangGraph Node ---

async def load_integration_settings(state: SharedState, db: Session):
    """
    DB에서 워크스페이스 연동 설정을 읽어 SharedSate에 올린다.
    회의 시작 시 supervisor가 이노드를 호출한다.
    """
    workspace_id = int(state['workspace_id'])
    integrations = repository.get_integrations(db, workspace_id)

    integration_settings = {}
    for item in integrations:
        webhook_url = None
        if item.extra_config:
            webhook_url = item.extra_config.get("webhook_url")

        integration_settings[item.service.value] = {
            "is_connected": item.is_connected,
            "webhook_url": webhook_url
        }
    return {"integration_settings": integration_settings}

# --- 비즈니스 로직 ---
def get_integrations(db: Session, workspace_id: int) -> List[Integration]:
    return repository.get_integrations(db, workspace_id)

def connect_integration(
        db: Session, workspace_id: int, service: ServiceType, webhook_url: str
) -> Integration:
    """
    서비스 연동 등록
    webhook_url 을 extra_config에 저장하고 is_connected=True로 변경.
    """
    return repository.upsert_integration(db, workspace_id, service, webhook_url)

def disconnect_integration(
        db: Session,
        workspace_id: int,
        service: ServiceType
) -> Integration:
    """
    연동 해제
    is_connected=False, webhook_url 삭제
    """
    return repository.disconnect_integration(db, workspace_id, service)

async def test_webhook(webhook_url: str) -> bool:
    """
    webhook_url이 실제로 동작하는지 테스트.
    n8n에 ping payload를 보내고 응답 확인.
    """
    n8n = N8nClient()
    try:
        await n8n.trigger_webhook(webhook_url, payload={"action": "ping"})
        return True
    except Exception as e:
        logger.error(f"테스트 실패 : {str(e)}")
        return False

