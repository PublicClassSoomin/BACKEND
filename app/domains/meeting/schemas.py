# app\domains\meeting\schemas.py

"""
회의(meeting) 도메인에서 사용하는 요청/응답 스키마를 정의하는 파일입니다.현재는 회의 생성/조회 최소 기능을 먼저 구현하기 위해 필요한 스키마를 정의합니다.
"""

from datetime import datetime

from pydantic import BaseModel, Field

class MeetingCreateRequest(BaseModel):
    """
    회의 생성 요청 시 사용하는 스키마입니다.
    """

    title: str = Field(min_length=1, max_length=200)
    meeting_type: str = Field(min_length=1, max_length=50)
    scheduled_at: datetime
    room_name: str | None = Field(default=None, max_length=255)
    participant_ids: list[int] = Field(default_factory=list)


class MeetingResponse(BaseModel):
    """
    회의 단건 응답 시 사용하는 스키마입니다.
    """

    meeting_id: int
    workspace_id: int
    title: str
    meeting_type: str
    scheduled_at: datetime
    room_name: str | None
    participant_ids: list[int]
    status: str
    created_at: datetime


class MeetingListResponse(BaseModel):
    """
    회의 목록 응답 시 사용하는 스키마입니다.
    """

    meetings: list[MeetingResponse]


class MeetingHistoryResponse(BaseModel):
    """
    회의 히스토리 응답 시 사용하는 스키마입니다.
    """

    total: int
    page: int
    size: int
    meetings: list[MeetingResponse]


class MeetingNoteActionItem(BaseModel):
    """
    회의록에 포함되는 액션 아이템 응답 스키마입니다.
    """

    id: str
    text: str
    assignee: str | None = None
    due: str | None = None
    done: bool = False


class MeetingTranscriptItem(BaseModel):
    """
    회의록 전문 타임라인 1건 응답 스키마입니다.
    """

    id: str
    speaker_name: str
    speaker_color: str
    start_time: int
    text: str
    is_decision: bool = False
    is_action_item: bool = False


class MeetingNotesUpdateRequest(BaseModel):
    """
    회의록 편집 저장 요청 시 사용하는 스키마입니다.
    """

    summary: str = Field(min_length=1, max_length=1000)
    decisions: list[str] = Field(default_factory=list)
    open_issues: list[str] = Field(default_factory=list)
    action_items: list[MeetingNoteActionItem] = Field(default_factory=list)
    transcript: list[MeetingTranscriptItem] = Field(default_factory=list)


class MeetingNotesResponse(MeetingNotesUpdateRequest):
    """
    회의록 조회 응답 시 사용하는 스키마입니다.
    """

    meeting_id: int
    title: str
    generated_at: datetime


class MeetingWbsTaskResponse(BaseModel):
    """
    WBS 태스크 응답 스키마입니다.
    """

    id: str
    title: str
    assignee_name: str | None = None
    priority: str
    status: str
    due_date: str | None = None
    progress: int
    jira_key: str | None = None


class MeetingWbsTaskUpdateRequest(BaseModel):
    """
    WBS 태스크 상태/담당자/기한 수정 요청 스키마입니다.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    assignee_name: str | None = Field(default=None, max_length=100)
    priority: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=20)
    due_date: str | None = Field(default=None, max_length=50)
    progress: int | None = Field(default=None, ge=0, le=100)
    jira_key: str | None = Field(default=None, max_length=50)


class MeetingWbsEpicCreateRequest(BaseModel):
    """
    WBS 에픽 생성 요청 스키마입니다.
    """

    title: str = Field(min_length=1, max_length=255)


class MeetingWbsTaskCreateRequest(BaseModel):
    """
    WBS 태스크 생성 요청 스키마입니다.
    """

    title: str = Field(min_length=1, max_length=255)
    assignee_name: str | None = Field(default=None, max_length=100)
    priority: str = Field(default="medium", max_length=20)
    status: str = Field(default="todo", max_length=20)
    due_date: str | None = Field(default=None, max_length=50)
    progress: int = Field(default=0, ge=0, le=100)
    jira_key: str | None = Field(default=None, max_length=50)


class MeetingWbsEpicResponse(BaseModel):
    """
    WBS 에픽 응답 스키마입니다.
    """

    id: str
    title: str
    progress: int
    tasks: list[MeetingWbsTaskResponse]


class MeetingWbsResponse(BaseModel):
    """
    회의 기반 WBS 목록 응답 스키마입니다.
    """

    meeting_id: int
    title: str
    epics: list[MeetingWbsEpicResponse]


class MeetingReportResponse(BaseModel):
    """
    보고서 생성 응답 스키마입니다.
    """

    meeting_id: int
    title: str
    format: str
    content: str


class MeetingReportUpdateRequest(BaseModel):
    """
    보고서 편집 저장 요청 스키마입니다.
    """

    content: str = Field(min_length=1)


class MeetingExportRequest(BaseModel):
    """
    회의 산출물 내보내기 요청 스키마입니다.
    """

    target: str = Field(min_length=1, max_length=50)


class MeetingExportResponse(BaseModel):
    """
    회의 산출물 내보내기 결과 응답 스키마입니다.
    """

    meeting_id: int
    target: str
    exported: bool
    message: str
