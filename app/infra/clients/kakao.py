# app/infra/clients/kakao.py
import logging
from typing import Dict, Any
from .n8n import N8nClient

class KakaoClient:
    """
    카카오톡 알림 클라이언트.
    직접 카카오 API를 호출하지 않고 n8n 웹훅으로 함.
    """
    def __init__(self):
        self.n8n = N8nClient()

    async def send_message(
            self, webhook_url: str, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        카카오톡 알림 메시지 발송 요청을 웹훅으로 한다.

        args: webhook_url: integrations.extra_config['webhook_url']
        message_data: {
            "receiver_uuid": "카카오 유저 UUID",
            "message": "회의록 검토 요청이 도착했습니다.",
            "link_url": "http://서비스URL/meetings/1/minutes"
        }
        """
        payload = {
            "action": "send_message",
            "data": message_data
        }
        return await self.n8n.trigger_webhook(webhook_url, payload)