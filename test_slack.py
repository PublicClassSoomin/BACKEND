# test_slack_all.py
import asyncio
from app.infra.clients.slack import SlackAsyncClient
from app.domains.action import agent_utils
from app.infra.clients.session_manager import ClientSessionManager

async def test_all_scenarios():
    slack_client = SlackAsyncClient()
    print("🧪 슬랙 시나리오 001~008 통합 테스트를 시작합니다...\n")

    try:
        # [SCN-SLK-001] 회의 시작 알림
        print("- SCN-SLK-001 전송 중...")
        blocks_001 = agent_utils.create_meeting_start_blocks("MEET-101", "주간 성과 공유 및 전략 회의")
        await slack_client.send_via_webhook("회의 시작 알림", blocks=blocks_001)

        # [SCN-SLK-002] 실시간 액션 아이템 알림
        print("- SCN-SLK-002 전송 중...")
        blocks_002 = agent_utils.create_action_item_blocks("마케팅 채널별 유입 분석 보고서 작성", "김철수 팀장")
        await slack_client.send_via_webhook("신규 할 일 알림", blocks=blocks_002)

        # [SCN-SLK-003] 상급자 검토 요청 (문서 포함)
        print("- SCN-SLK-003 전송 중...")
        blocks_003 = agent_utils.create_review_request_blocks(
            "주간 성과 공유 및 전략 회의", "회의록 초안 및 WBS", "https://example.com/wbs/101"
        )
        await slack_client.send_via_webhook("상급자 검토 요청", blocks=blocks_003)

        # [SCN-SLK-004] 회의 요약 및 결과 보고
        print("- SCN-SLK-004 전송 중...")
        summary = "1. 신규 마케팅 전략 수립 완료\n2. 다음 주까지 상세 분석 보고서 제출 예정\n3. 예산 증액안 승인됨"
        blocks_004 = agent_utils.create_summary_blocks(summary, "https://example.com/full-report/101")
        await slack_client.send_via_webhook("회의 결과 보고", blocks=blocks_004)

        # [SCN-SLK-005] Jira 이슈 생성 확인
        print("- SCN-SLK-005 전송 중...")
        issues = [
            {"key": "PROJ-101", "title": "시장 분석 보고서 작성", "url": "https://jira.com/PROJ-101"},
            {"key": "PROJ-102", "title": "예산 승인 프로세스 시작", "url": "https://jira.com/PROJ-102"}
        ]
        blocks_005 = agent_utils.create_jira_issue_blocks(issues)
        await slack_client.send_via_webhook("Jira 이슈 생성 완료", blocks=blocks_005)

        # [SCN-SLK-006] 문서 내보내기 완료 (PPT/엑셀 등)
        print("- SCN-SLK-006 전송 중...")
        files = [
            {"name": "회의록_보고서.pptx", "url": "https://s3.com/ppt/1"},
            {"name": "액션아이템_리스트.xlsx", "url": "https://s3.com/excel/1"}
        ]
        blocks_006 = agent_utils.create_export_completion_blocks(files)
        await slack_client.send_via_webhook("문서 내보내기 완료", blocks=blocks_006)

        # [SCN-SLK-007] 시스템 장애 알림
        print("- SCN-SLK-007 전송 중...")
        blocks_007 = agent_utils.create_error_notification_blocks("NotionClient", "API Rate Limit Exceeded (429)")
        await slack_client.send_via_webhook("시스템 에러 알림", blocks=blocks_007)

        # [SCN-SLK-008] 실시간 액션 묶음 배송
        print("- SCN-SLK-008 전송 중...")
        bundle_data = [
            {"task": "슬랙 테스트 완료하기", "assignee": "대중님"},
            {"task": "지라 시나리오 검토", "assignee": "해결사 에이전트"}
        ]
        blocks_008 = agent_utils.create_action_bundle_blocks(bundle_data)
        await slack_client.send_via_webhook("할 일 묶음 알림", blocks=blocks_008)

        print("\n✅ 모든 테스트가 완료되었습니다! 슬랙 채널을 확인해 보세요.")

    except Exception as e:
        print(f"\n❌ 테스트 중 에러 발생: {e}")
    finally:
        # 테스트 종료 후 공유 세션 안전하게 닫기
        await ClientSessionManager.close_client()

if __name__ == "__main__":
    asyncio.run(test_all_scenarios())