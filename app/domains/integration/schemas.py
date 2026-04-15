"""
외부 연동(integration) 도메인에서 사용하는 요청 / 응답 스키마를 정의하는 파일입니다.

현재는 워크스페이스별 연동 상태 조회 기능부터 구현하기 위해
조회 응답에 필요한 스키마를 먼저 정의합니다.
향후 연동 설정 변경 기능이 추가되면 이 파일에 요청 스키마도 정의할 수 있습니다.
"""

from datetime import datetime

from pydantic import BaseModel


class IntegrationItemResponse(BaseModel):
    """
    외부 서비스 연동 상태 1건을 응답할 때 사용하는 스키마입니다.

    현재 단계에서는 서비스 이름, 연결 여부, 생성 시각만 먼저 반환합니다.
    이후 토큰 만료 시각이나 추가 설정값이 필요해지면 여기에 확장할 수 있습니다.
    """

    # 외부 서비스 이름입니다.
    # 예: jira, slack, notion, google_calendar, kakao
    service: str

    # 실제 연동이 완료되었는지 여부입니다.
    # 워크스페이스 생성 직후 기본 row는 False로 생성됩니다.
    is_connected: bool

    # 해당 연동 row 생성 시각입니다.
    created_at: datetime


class IntegrationListResponse(BaseModel):
    """
    워크스페이스별 전체 연동 상태 목록을 응답할 때 사용하는 스키마입니다.

    현재는 연동 상태 리스트만 반환하지만 이후에 워크스페이스 ID나 이름 같은 기본 정보도 함께 반환하도록 확장할 수 있습니다.
    """

    integrations: list[IntegrationItemResponse]
