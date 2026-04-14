# app/infra/clients/slack.py
import logging
from typing import Dict, Any
from .n8n import N8nClient

logger = logging.getLogger(__name__)

class SlackClient:
    """
    Slack 연동 클라이언트
    직접 Slack API 호출하지 않고 n8n 웹훅으로 연동
    """
    def __init__(self):
        self.n8n = N8nClient()

    async def send_message(
            self, webhook_url: str, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Slack n8n으로 메세지 전송

        args:
            webhook_url: integrations.extra_config['webhook_url']
            message_data: {
                "chaneel_id": "C1234567",
                "message": "회의록 검토 요청",
                "link_url": "http://서비스URL/meetings/1/minutes"
            }
        """
        payload = {
            "action": "send_message",
            "data": message_data
        }
        return await self.n8n.trigger_webhook(webhook_url, payload)
    
    async def export_minutes(
            self, webhook_url: str, export_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        회의록을 Slack 채널로 내보내기 요청을 n8n에 위임

        args:
            webhook_url: integrations.extra_config['webhook_url']
            export_data: {
                "channel_id": "C1234567",
                "content": "회의록 전문",
                "include_action_items": true
            }
        """
        payload = {
            "action": "export_minutes",
            "data": export_data
        }

        return self.n8n.trigger_webhook(webhook_url, payload)

        