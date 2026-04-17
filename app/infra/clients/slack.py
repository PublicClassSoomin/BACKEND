# app/infra/clients/slack.py
import logging
from typing import Dict, Any, List, Optional
from .base import BaseClient

logger = logging.getLogger(__name__)

class SlackClient(BaseClient):
    """
    Slack API 직접 호출 클라이언트
    integrations 테이블의 access_token(bot_token) 사용
    """
    def __init__(self, bot_token: str):
        super().__init__(
            base_url="https://slack.com/api",
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
        )

    async def _check_slack_error(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Slack의 http 200 + ok : False 에러 확인
        """
        if not response_data.get("ok"):
            error_code = response_data.get("error", "unknown_error")
            logger.error(f"[Slack API Error] -> {error_code}")
            raise ValueError(f"Slack API Error -. {error_code}")
        return response_data
        
    async def get_public_channels(self) -> List[Dict[str, str]]:
        """
        드롭다운 용 공개 체널 목록 조회
        """
        result = await self._request(
            "GET", "/conversations.list",
            params = {
                "types": "public_channel",
                "exclude_archived": "true"
            }
        )

        result = await self._check_slack_error(result)

        channels = []
        for c in result.get('channels', []):
            channels.append({
                "id": c['id'],
                "name": c['name']
            })
        return channels

    async def send_message(
            self, 
            channel_id: str, 
            text: str, 
            blocks: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Slack 채널에 메세지 전송

        args:
            channel: 채널 ID
            text: 메시지 본문
            blocks: Block Kit 블록 리스트
        """
        payload: Dict[str, Any] = {
            "channel": channel_id,
            "text": text
        }
        if blocks:
            payload['blocks'] = blocks
        
        result = await self._request("POST", "/chat.postMessage", json=payload)
        return await self._check_slack_error(result)
    
    async def get_channel_members(self, channel_id: str) -> List[str]:
        """
        채널 내 멤버 user_id 목록 조회
        """
        result = await self._request(
            "GET", "/conversations.members",
            params={
                "channel": channel_id
            }
        )
        result = await self._check_slack_error(result)
        return result.get("members", [])
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        user_id로 유저 정보 조회
        """
        result = await self._request(
            "GET", "/users.info",
            params={
                "user": user_id
            }
        )
        result = await self._check_slack_error(result)
        return {
            "id": user_id,
            "name": result['user']['real_name'],
            "email": result['user']['profile'].get("email", "")
        }
    
    async def send_dm_to_workspace_member(
            self,
            channel_id: str,
            workb_email: str,
            text: str,
    ) -> Dict[str, Any]:
        """
        WorkB DB에 이메일 있으면 채널 멤버와 매핑 후 DM 전송.!
        채널에 없으면 ValueError 발생.

        args: 
            channel_id : 채널 ID
            workb_email : 워크비 DB에 있는 users.email
            text : 보낼 메세지
        """
        # 1. 채널 멤버 목록 조회
        member_ids = await self.get_channel_members(channel_id)

        # 2. 채널에 있는 모든 사용자 이메일 조회
        slack_user_id = None
        for uid in member_ids:
            info = await self.get_user_info(uid)
            if info['email'] == workb_email:
                slack_user_id = uid
                break

        if not slack_user_id:
            raise ValueError(f"채널에서 {workb_email} 유저를 찾을 수 없습니다.")
        
        # DM 전송
        dm_channel_id = await self.open_dm(slack_user_id)
        return await self.send_message(channel_id=dm_channel_id, text=text)

    async def open_dm(self, user_id: str) -> str:
        """
        DM 채널 만들고, 채널 ID 반환
        """
        result = await self._request(
            "POST", "/conversations.open", json={"users": user_id}
        )
        result = await self._check_slack_error(result)
        return result['channel']['id']
    
    
    async def send_minutes(
            self,
            channel_id: str,
            meeting_title: str,
            minutes_text: str,
            action_items: Optional[List[str]] = None,
            link_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        회의록을 Slack Block Kit 형식으로 전송.

        args:
            channel : 채널명
            meeting_title: 회의 제목
            minutes_text: 회의록 내용
            action_items: 액션 아이템 리스트 (선택)
            link_url: 서비스 내 회의록 링크 (선택)
        """
        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{meeting_title}",
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": minutes_text[:3000],
                },
            },
        ]

        if action_items:
            action_text = "\n".join(f"• {item}" for item in action_items)
            blocks += [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"액션 아이템\n{action_text}"
                    }
                }
            ]
        
        if link_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "회의록 보기"
                        },
                        "url": link_url,
                        "style": "primary",
                    }
                ],
            })
        
        return await self.send_message(
            channel_id=channel_id,
            text=f"[{meeting_title}] 회의록이 도착했습니다.",
            blocks=blocks
        )
    
    