# app\infra\clients\slack.py
import logging
from typing import Dict, Any, Optional, List
from .base import BaseClient
from .session_manager import ClientSessionManager
from app.core.config import settings

logger = logging.getLogger(__name__)

class SlackAsyncClient(BaseClient):
    """
    슬랙 메시지 발송을 담당하는 비동기 클라이언트
    """
    def __init__(self):
        # 슬랙 API 기본주소를 설정하지만, 웹훅 사용 시에는 호출 시 주소를 직접 전달받음.
        super().__init__(base_url="https://slack.com/api")

    async def send_via_webhook(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        .env에 설정된 Webhook으로 메시지(또는 블록)를 보냅니다.
        """
        webhook_url = settings.SLACK_WEBHOOK_URL
        if not webhook_url:
            return False

        # 블록이 있으면 블록을 우선해서 보냅니다.
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            client = await ClientSessionManager.get_client()
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"슬랙 전송 실패: {e}")
            raise e