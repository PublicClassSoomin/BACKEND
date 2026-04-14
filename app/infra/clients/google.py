# app\infra\clients\google.py
import logging
from typing import Dict, Any
from .n8n import N8nClient

logger = logging.getLogger(__name__)

class GoogleCalenderClient:
    """
    Google Calendar 연동 클라이언트.
    직접 Google API를 호출하지 않고 n8n 웹혹으로 함.
    """
    def __init__(self):
        self.n8n = N8nClient()

    async def create_event(
            self, webhook_url: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Google Calender 일정 생성 요청을 n8n 웹훅으로 함.

        args:
            webhook_url: integrations.extra_config['webhook_url']
            event_data: {
                "title": "2차 스프린트 회의",
                "start_datetime": "2025-04-20T10:00:00",
                "end_datetime": "2025-04-20T12:00:00",
                "attendess": ["@a@n.com", "b@g.com"],
                "description": "회의 안건 및 참고사항"
            }
        """
        payload = {
            "action": "create_event",
            "data": event_data,
        }

        return await self.n8n.trigger_webhook(webhook_url, payload)