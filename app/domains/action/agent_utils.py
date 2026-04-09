# app\domains\action\agent_utils.py
from typing import List, Dict, Any

def create_meeting_start_blocks(meeting_id: str, title: str) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-001] 회의 시작 알림을 슬랙 Block Kit 레이아웃을 생성합니다.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 새로운 회의가 시작되었습니다!",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*회의 제목:*\n{title}"},
                {"type": "mrkdwn", "text": f"*회의 ID:*\n{meeting_id}"}
            ]
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "💡 에이전트가 지금부터 실시간으로 회의를 기록하고 분석합니다."}
            ]
        }
    ]

def create_action_item_blocks(task_name: str, assignee: str) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-002] 실시간 액션 아이템 알림용 디자인
    회의 중 할 일이 결정되었을 때 담당자와 태스크를 보여줍니다.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📍 *새로운 액션 아이템이 등록되었습니다:*\n>{task_name}"
            }
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"👤 *담당자:* {assignee}"}
            ]
        }
    ]

def create_review_request_blocks(meeting_title: str, file_type: str, file_url: str) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-003] 상급자 검토 요청용 디자인
    PPT, 엑셀 등 생성된 문서를 상급자에게 보고할 때 사용합니다.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🔔 *상급자 검토 요청*\n지난 *<{meeting_title}>* 회의의 결과 문서가 생성되었습니다. 검토를 부탁드립니다."
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*문서 종류:*\n{file_type}"},
                {"type": "mrkdwn", "text": f"*상태:*\n초안 작성 완료"}
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📄 문서 확인하기"},
                    "url": file_url,
                    "style": "primary"
                }
            ]
        }
    ]

def create_summary_blocks(summary_text: str, wbs_link: str) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-004] 회의 요약 및 WBS 공유용 디자인
    회의가 끝나고 결과를 한눈에 보여줄 때 사용합니다.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📝 회의 요약 및 결과 보고",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*핵심 요약:*\n{summary_text}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🔗 *상세 WBS 및 결과 문서 보기*"
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "문서 바로가기"},
                "url": wbs_link,
                "action_id": "button-action"
            }
        }
    ]

def create_jira_issue_blocks(issues: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-005] Jira 이슈 생성 완료 알림용 디자인입니다.
    생성된 모든 티켓의 키(Key)와 제목을 리스트 형태로 출력합니다.
    """
    # 1. 이슈 목록을 불렛 포인트 형태의 마크다운 텍스트로 만듭니다.
    issue_links = "\n".join([f"• *<{i['url']}|{i['key']}>*: {i['title']}" for i in issues])

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🎫 Jira 이슈 생성 완료",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"회의 결과가 Jira 시스템에 등록되었습니다. 아래 링크를 통해 확인해 보세요.\n\n{issue_links}"
            }
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "ℹ️ 각 티켓 번호를 클릭하면 바로 Jira로 이동합니다."}
            ]
        }
    ]

def create_export_completion_blocks(files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-006] 여러 문서 내보내기 완료 알림
    노션, 엑셀, PPT가 한꺼번에 생성되었을 때 리스트 형태로 보여줍니다.
    """
    file_links = "\n".join([f"• <{f['url']}|{f['name']}>" for f in files])
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *모든 문서 내보내기가 완료되었습니다!*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*생성된 문서 리스트:*\n{file_links}"
            }
        }
    ]


def create_error_notification_blocks(node_name: str, error_msg: str) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-007] 시스템 에어 알림용 디자인 (Quality 도메인 협업)
    문제가 생겼을 때 관리자에게 긴급하게 알립니다.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *에이전트 실행 중 오류가 발생했습니다!*"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*발생 위치:*\n{node_name}"},
                {"type": "mrkdwn", "text": f"*오류 내용:*\n`{error_msg}`"}
            ]
        }
    ]

def create_action_bundle_blocks(actions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    [SCN-SLK-008] 실시간 액션 아이템 묶음 배송 디자인
    여러 개의 할 일을 불렛 포인트로 묶어서 한 번에 보여줍니다.
    """
    # 리스트를 예쁜 마크다운 문자열로 변환합니다.
    action_list = "\n".join([f"• *{a['task']}* (담당: {a['assignee']})" for a in actions])
    
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📌 *실시간으로 결정된 할 일 목록입니다:*\n{action_list}"
            }
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "💡 회의 흐름을 방해하지 않도록 결정된 사항들을 모아서 알려드립니다."}
            ]
        }
    ]
