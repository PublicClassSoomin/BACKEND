# app\domains\meeting\router.py

"""
회의(meeting) 도메인의 API 엔드포인트를 정의하는 파일입니다.

현재는 회의 생성과 단건 조회 기능부터 구현합니다.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domains.meeting.schemas import (
    MeetingExportRequest,
    MeetingExportResponse,
    MeetingCreateRequest,
    MeetingHistoryResponse,
    MeetingListResponse,
    MeetingNotesResponse,
    MeetingNotesUpdateRequest,
    MeetingReportResponse,
    MeetingReportUpdateRequest,
    MeetingResponse,
    MeetingWbsEpicCreateRequest,
    MeetingWbsEpicResponse,
    MeetingWbsResponse,
    MeetingWbsTaskCreateRequest,
    MeetingWbsTaskResponse,
    MeetingWbsTaskUpdateRequest,
)
from app.domains.meeting.service import (
    create_meeting_wbs_epic_service,
    create_meeting_wbs_task_service,
    create_meeting_service,
    delete_meeting_service,
    end_meeting_service,
    export_meeting_service,
    get_meeting_history_service,
    get_meeting_notes_service,
    get_meeting_report_service,
    get_meeting_service,
    get_meeting_wbs_service,
    get_meetings_service,
    start_meeting_service,
    update_meeting_service,
    update_meeting_notes_service,
    update_meeting_report_service,
    update_meeting_wbs_task_service,
)


router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting(
    workspace_id: int,
    payload: MeetingCreateRequest,
    db: Session = Depends(get_db),
) -> MeetingResponse:
    """
    특정 워크스페이스에 새 회의를 생성하는 API 엔드포인트입니다.
    """
    return create_meeting_service(db, workspace_id, payload)


@router.get(
    "/{meeting_id}",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingResponse:
    """
    특정 회의 상세 정보를 조회하는 API 엔드포인트입니다.
    """
    return get_meeting_service(db, meeting_id)


@router.get(
    "/workspaces/{workspace_id}",
    response_model=MeetingListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meetings(
    workspace_id: int,
    meeting_status: str | None = Query(default=None, alias="status"),
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    keyword: str | None = None,
    db: Session = Depends(get_db),
) -> MeetingListResponse:
    """
    특정 워크스페이스의 회의 목록을 조회하는 API 엔드포인트입니다.
    """
    return get_meetings_service(
        db=db,
        workspace_id=workspace_id,
        meeting_status=meeting_status,
        date_from=date_from,
        date_to=date_to,
        keyword=keyword,
    )


@router.get(
    "/workspaces/{workspace_id}/history",
    response_model=MeetingHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meeting_history(
    workspace_id: int,
    keyword: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    participant_id: int | None = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
) -> MeetingHistoryResponse:
    """
    특정 워크스페이스의 회의 히스토리를 조회하는 API 엔드포인트입니다.
    """
    return get_meeting_history_service(
        db=db,
        workspace_id=workspace_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        participant_id=participant_id,
        page=page,
        size=size,
    )


@router.patch(
    "/{meeting_id}",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
async def update_meeting(
    meeting_id: int,
    payload: MeetingCreateRequest,
    db: Session = Depends(get_db),
) -> MeetingResponse:
    """
    특정 회의 정보를 수정하는 API 엔드포인트입니다.
    """
    return update_meeting_service(db, meeting_id, payload)


@router.patch(
    "/{meeting_id}/start",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
async def start_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingResponse:
    """
    특정 회의를 시작 상태로 변경하는 API 엔드포인트입니다.
    """
    return start_meeting_service(db, meeting_id)


@router.patch(
    "/{meeting_id}/end",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
async def end_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingResponse:
    """
    특정 회의를 종료 상태로 변경하는 API 엔드포인트입니다.
    """
    return end_meeting_service(db, meeting_id)


@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    특정 회의를 삭제하는 API 엔드포인트입니다.
    """
    delete_meeting_service(db, meeting_id)


@router.get(
    "/{meeting_id}/notes",
    response_model=MeetingNotesResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meeting_notes(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingNotesResponse:
    """
    특정 회의의 회의록을 조회하는 API 엔드포인트입니다.
    """
    return get_meeting_notes_service(db, meeting_id)


@router.patch(
    "/{meeting_id}/notes",
    response_model=MeetingNotesResponse,
    status_code=status.HTTP_200_OK,
)
async def update_meeting_notes(
    meeting_id: int,
    payload: MeetingNotesUpdateRequest,
    db: Session = Depends(get_db),
) -> MeetingNotesResponse:
    """
    특정 회의의 회의록 편집 내용을 저장하는 API 엔드포인트입니다.
    """
    return update_meeting_notes_service(db, meeting_id, payload)


@router.get(
    "/{meeting_id}/wbs",
    response_model=MeetingWbsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meeting_wbs(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> MeetingWbsResponse:
    """
    특정 회의의 WBS 목록을 조회하는 API 엔드포인트입니다.
    """
    return get_meeting_wbs_service(db, meeting_id)


@router.post(
    "/{meeting_id}/wbs/epics",
    response_model=MeetingWbsEpicResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting_wbs_epic(
    meeting_id: int,
    payload: MeetingWbsEpicCreateRequest,
    db: Session = Depends(get_db),
) -> MeetingWbsEpicResponse:
    """
    특정 회의의 WBS 에픽을 생성하는 API 엔드포인트입니다.
    """
    return create_meeting_wbs_epic_service(
        db=db,
        meeting_id=meeting_id,
        payload=payload,
    )


@router.post(
    "/{meeting_id}/wbs/epics/{epic_id}/tasks",
    response_model=MeetingWbsTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting_wbs_task(
    meeting_id: int,
    epic_id: int,
    payload: MeetingWbsTaskCreateRequest,
    db: Session = Depends(get_db),
) -> MeetingWbsTaskResponse:
    """
    특정 WBS 에픽 아래에 태스크를 생성하는 API 엔드포인트입니다.
    """
    return create_meeting_wbs_task_service(
        db=db,
        meeting_id=meeting_id,
        epic_id=epic_id,
        payload=payload,
    )


@router.patch(
    "/{meeting_id}/wbs/tasks/{task_id}",
    response_model=MeetingWbsTaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_meeting_wbs_task(
    meeting_id: int,
    task_id: int,
    payload: MeetingWbsTaskUpdateRequest,
    db: Session = Depends(get_db),
) -> MeetingWbsTaskResponse:
    """
    특정 회의의 WBS 태스크를 수정하는 API 엔드포인트입니다.
    """
    return update_meeting_wbs_task_service(
        db=db,
        meeting_id=meeting_id,
        task_id=task_id,
        payload=payload,
    )


@router.get(
    "/{meeting_id}/reports",
    response_model=MeetingReportResponse,
    status_code=status.HTTP_200_OK,
)
async def get_meeting_report(
    meeting_id: int,
    format: str = "html",
    db: Session = Depends(get_db),
) -> MeetingReportResponse:
    """
    특정 회의의 보고서 초안을 생성하는 API 엔드포인트입니다.
    """
    return get_meeting_report_service(db, meeting_id, format)


@router.patch(
    "/{meeting_id}/reports/{report_format}",
    response_model=MeetingReportResponse,
    status_code=status.HTTP_200_OK,
)
async def update_meeting_report(
    meeting_id: int,
    report_format: str,
    payload: MeetingReportUpdateRequest,
    db: Session = Depends(get_db),
) -> MeetingReportResponse:
    """
    특정 회의의 보고서 편집 내용을 저장하는 API 엔드포인트입니다.
    """
    return update_meeting_report_service(
        db=db,
        meeting_id=meeting_id,
        report_format=report_format,
        payload=payload,
    )


@router.post(
    "/{meeting_id}/exports",
    response_model=MeetingExportResponse,
    status_code=status.HTTP_200_OK,
)
async def export_meeting(
    meeting_id: int,
    payload: MeetingExportRequest,
    db: Session = Depends(get_db),
) -> MeetingExportResponse:
    """
    특정 회의 산출물을 외부 서비스로 내보내는 API 엔드포인트입니다.
    """
    return export_meeting_service(db, meeting_id, payload)
