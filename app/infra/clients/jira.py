# app\infra\clients\jira.py
import logging
from typing import Dict, Any, List
from .n8n import N8nClient

logger = logging.getLogger(__name__)

class JiraClient:
    """
    JIRA 연동
    직접 JIRA API를 호출하지 않고, n8n 웹훅에게 위임
    """
    def __init__(self):
        self.n8n = N8nClient()

    async def create_issue(
            self, webhook_url: str, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        JIRA Issue 생성 요청을 n8n으로 한다.

        args:
            webhook_url: integrations.extra_config['webhook-url']

            이슈 에 들어갈 내용
            issue_data: {
                "summary": "이슈 제목",
                "description: "이슈 설명"
                "issue_type": "Task | Epic | Story"
                "priority": "LOW | Medium | High | Critical"
                "assignee": "담당자 이메일"
            }
        """
        payload = {
            "action": "create_issue",
            "data": issue_data
        }
        return await self.n8n.trigger_webhook(webhook_url, payload)
    
    async def create_issue_bulk(
            self, webhook_url: str, issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        WBS 태스크 목록을 JIRA issue 일괄 생성 요청

        args:
            webhook_url : integrations.extra_config['webhook_url']
            issues: create_issue의 issue_data 형태 리스트
        """
        payload = {
            "action": "create_issues_bulk",
            "data": {"issues": issues}
        }
        return await self.n8n.trigger_webhook(webhook_url, payload)