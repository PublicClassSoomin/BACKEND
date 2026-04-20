# app\domains\meeting\service.py

"""
회의(meeting) 도메인의 비즈니스 로직을 처리하는 파일입니다.

현재는 회의 생성/조회 최소 기능을 먼저 구현합니다.
이후 participant_ids 검증, 히스토리 조회, 검색 기능을 이 service에 확장할 예정입니다.
"""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.meeting.repository import (
    create_export_log,
    create_meeting_note,
    create_meeting,
    create_meeting_participants,
    create_wbs_epic,
    create_wbs_task,
    delete_meeting,
    get_meeting_report,
    get_meeting_by_id,
    get_meeting_history_by_workspace_id,
    get_meeting_note_by_meeting_id,
    get_meetings_by_workspace_id,
    get_meeting_participant_user_ids,
    get_wbs_epics_by_meeting_id,
    get_wbs_tasks_by_epic_id,
    replace_meeting_participants,
    update_meeting,
    update_meeting_note,
    update_meeting_status,
    update_wbs_epic_progress,
    update_wbs_task,
    upsert_meeting_report,
)
from app.domains.meeting.schemas import (
    MeetingExportRequest,
    MeetingExportResponse,
    MeetingCreateRequest,
    MeetingHistoryResponse,
    MeetingListResponse,
    MeetingNoteActionItem,
    MeetingNotesResponse,
    MeetingNotesUpdateRequest,
    MeetingReportResponse,
    MeetingReportUpdateRequest,
    MeetingResponse,
    MeetingTranscriptItem,
    MeetingWbsEpicCreateRequest,
    MeetingWbsEpicResponse,
    MeetingWbsResponse,
    MeetingWbsTaskCreateRequest,
    MeetingWbsTaskResponse,
    MeetingWbsTaskUpdateRequest,
)
from app.domains.integration.repository import get_integration_by_service
from app.domains.user.repository import get_users_by_ids
from app.domains.workspace.repository import get_workspace_by_id


def _validate_participant_ids(
    db: Session,
    workspace_id: int,
    participant_ids: list[int],
) -> list[int]:
    """
    participant_ids를 중복 제거하고 유효성을 검증합니다.

    Returns:
        중복 제거가 적용된 participant_ids 목록을 반환합니다.
    """
    unique_participant_ids = list(dict.fromkeys(participant_ids))

    users = get_users_by_ids(db, unique_participant_ids)
    found_user_ids = {user.id for user in users}
    invalid_user_ids = [
        user_id for user_id in unique_participant_ids
        if user_id not in found_user_ids
    ]
    if invalid_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PARTICIPANT_IDS",
                "message": "유효하지 않은 참석자 ID가 포함되어 있습니다.",
                "invalid_participant_ids": invalid_user_ids,
            },
        )

    wrong_workspace_user_ids = [
        user.id for user in users
        if user.workspace_id != workspace_id
    ]
    if wrong_workspace_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PARTICIPANT_WORKSPACE",
                "message": "같은 워크스페이스 소속이 아닌 참석자가 포함되어 있습니다.",
                "invalid_participant_ids": wrong_workspace_user_ids,
            },
        )

    return unique_participant_ids


def _to_meeting_response(db: Session, meeting) -> MeetingResponse:
    """
    Meeting ORM 객체를 공통 응답 스키마로 변환합니다.
    """
    return MeetingResponse(
        meeting_id=meeting.id,
        workspace_id=meeting.workspace_id,
        title=meeting.title,
        meeting_type=meeting.meeting_type,
        scheduled_at=meeting.scheduled_at,
        room_name=meeting.room_name,
        participant_ids=get_meeting_participant_user_ids(db, meeting.id),
        status=meeting.status,
        created_at=meeting.created_at,
    )


def _get_meeting_or_404(db: Session, meeting_id: int):
    """
    회의 존재 여부를 공통으로 확인합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    return meeting


def _build_default_note_payload(meeting) -> dict:
    """
    실제 AI 요약 API 연결 전까지 사용할 기본 회의록 데이터를 생성합니다.
    """
    room_label = meeting.room_name or "회의실 미지정"

    return {
        "summary": f"{meeting.title} 회의에서 주요 논의사항과 후속 작업을 정리했습니다. 회의 장소는 {room_label}입니다.",
        "decisions": [
            "회의 목적과 진행 방향을 확인했습니다.",
            "후속 작업은 담당자를 지정해 WBS로 관리하기로 했습니다.",
            "필요한 외부 연동은 설정 페이지에서 연결 상태를 확인하기로 했습니다.",
        ],
        "open_issues": [
            "세부 담당자와 완료 기한은 추가 검토가 필요합니다.",
            "외부 서비스 연동 범위는 팀 정책에 맞춰 확정해야 합니다.",
        ],
        "action_items": [
            {
                "id": "n1",
                "text": f"{meeting.title} 회의 내용 검토",
                "assignee": None,
                "due": "2일 후",
                "done": False,
            },
            {
                "id": "n2",
                "text": "후속 작업 WBS 정리",
                "assignee": None,
                "due": "3일 후",
                "done": False,
            },
        ],
        "transcript": [
            {
                "id": "t1",
                "speaker_name": "회의 진행자",
                "speaker_color": "#6b78f6",
                "start_time": 0,
                "text": f"{meeting.title} 회의를 시작하겠습니다.",
                "is_decision": False,
                "is_action_item": False,
            },
            {
                "id": "t2",
                "speaker_name": "참석자",
                "speaker_color": "#22c55e",
                "start_time": 120,
                "text": "논의된 내용을 바탕으로 후속 작업을 정리하겠습니다.",
                "is_decision": True,
                "is_action_item": True,
            },
        ],
    }


def _get_or_create_meeting_note(db: Session, meeting):
    """
    회의록이 없으면 기본 회의록을 생성하고, 있으면 기존 회의록을 반환합니다.
    """
    note = get_meeting_note_by_meeting_id(db, meeting.id)
    if note:
        return note

    payload = _build_default_note_payload(meeting)
    return create_meeting_note(
        db=db,
        meeting_id=meeting.id,
        summary=payload["summary"],
        decisions=payload["decisions"],
        open_issues=payload["open_issues"],
        action_items=payload["action_items"],
        transcript=payload["transcript"],
    )


def _to_notes_response(meeting, note) -> MeetingNotesResponse:
    """
    MeetingNote ORM 객체를 회의록 응답으로 변환합니다.
    """
    return MeetingNotesResponse(
        meeting_id=meeting.id,
        title=meeting.title,
        summary=note.summary,
        decisions=note.decisions,
        open_issues=note.open_issues,
        action_items=[
            MeetingNoteActionItem(**item)
            for item in note.action_items
        ],
        transcript=[
            MeetingTranscriptItem(**item)
            for item in note.transcript
        ],
        generated_at=note.updated_at,
    )


def _normalize_task_status(task_status: str | None, done: bool = False) -> str:
    """
    WBS 태스크 상태 문자열을 프론트 계약에 맞게 정규화합니다.
    """
    if task_status in {"todo", "inprogress", "done", "blocked"}:
        return task_status
    return "done" if done else "todo"


def _calculate_epic_progress(tasks) -> int:
    """
    하위 태스크 진행률 평균으로 에픽 진행률을 계산합니다.
    """
    if not tasks:
        return 0

    return round(sum(task.progress for task in tasks) / len(tasks))


def _to_wbs_task_response(task) -> MeetingWbsTaskResponse:
    """
    WBS 태스크 ORM 객체를 응답 스키마로 변환합니다.
    """
    return MeetingWbsTaskResponse(
        id=str(task.id),
        title=task.title,
        assignee_name=task.assignee_name,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        progress=task.progress,
        jira_key=task.jira_key,
    )


def _to_wbs_response(db: Session, meeting) -> MeetingWbsResponse:
    """
    저장된 WBS ORM 데이터를 응답 스키마로 변환합니다.
    """
    epics = get_wbs_epics_by_meeting_id(db, meeting.id)

    return MeetingWbsResponse(
        meeting_id=meeting.id,
        title=meeting.title,
        epics=[
            MeetingWbsEpicResponse(
                id=str(epic.id),
                title=epic.title,
                progress=epic.progress,
                tasks=[
                    _to_wbs_task_response(task)
                    for task in get_wbs_tasks_by_epic_id(db, epic.id)
                ],
            )
            for epic in epics
        ],
    )


def _get_or_create_meeting_wbs(db: Session, meeting):
    """
    저장된 WBS가 없으면 회의록 액션 아이템 기준으로 WBS를 생성합니다.
    """
    epics = get_wbs_epics_by_meeting_id(db, meeting.id)
    if epics:
        return epics

    note = _get_or_create_meeting_note(db, meeting)
    action_items = note.action_items or [
        {
            "text": f"{meeting.title} 후속 작업 정리",
            "assignee": None,
            "due": None,
            "done": False,
        }
    ]
    done_count = len([item for item in action_items if item.get("done")])
    progress = round((done_count / len(action_items)) * 100) if action_items else 0
    epic = create_wbs_epic(
        db=db,
        meeting_id=meeting.id,
        title=f"{meeting.title} 후속 작업",
        progress=progress,
    )

    for index, item in enumerate(action_items):
        done = bool(item.get("done"))
        create_wbs_task(
            db=db,
            meeting_id=meeting.id,
            epic_id=epic.id,
            title=item.get("text") or "후속 작업",
            assignee_name=item.get("assignee"),
            priority="high" if index == 0 else "medium",
            status=_normalize_task_status(None, done),
            due_date=item.get("due"),
            progress=100 if done else 0,
            jira_key=None,
        )

    return get_wbs_epics_by_meeting_id(db, meeting.id)


def _build_report_content(db: Session, meeting, note) -> str:
    """
    회의록과 WBS를 기반으로 보고서 본문을 생성합니다.
    """
    participant_ids = get_meeting_participant_user_ids(db, meeting.id)
    decisions = "\n".join(
        f"{index + 1}. {decision}"
        for index, decision in enumerate(note.decisions)
    )
    action_items = "\n".join(
        f"- {item.get('text')} / 담당자: {item.get('assignee') or '미정'} / 기한: {item.get('due') or '미정'}"
        for item in note.action_items
    )
    issues = "\n".join(f"- {issue}" for issue in note.open_issues)

    return f"""# {meeting.title} 회의 보고서

## 회의 개요
- 회의 ID: {meeting.id}
- 워크스페이스 ID: {meeting.workspace_id}
- 회의 유형: {meeting.meeting_type}
- 회의실: {meeting.room_name or "미지정"}
- 참석자 수: {len(participant_ids)}명

## 요약
{note.summary}

## 결정사항
{decisions or "- 아직 등록된 결정사항이 없습니다."}

## 액션 아이템
{action_items or "- 아직 등록된 액션 아이템이 없습니다."}

## 미결 이슈
{issues or "- 미결 이슈가 없습니다."}
"""


def create_meeting_service(
    db: Session,
    workspace_id: int,
    payload: MeetingCreateRequest,
) -> MeetingResponse:
    """
    회의 생성을 처리합니다.

    현재 단계에서는 workspace 존재 여부를 먼저 확인하고,
    participant_ids는 중복 제거만 수행합니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    unique_participant_ids = _validate_participant_ids(
        db=db,
        workspace_id=workspace_id,
        participant_ids=payload.participant_ids,
    )

    meeting = create_meeting(
        db=db,
        workspace_id=workspace_id,
        title=payload.title,
        meeting_type=payload.meeting_type,
        scheduled_at=payload.scheduled_at,
        room_name=payload.room_name,
    )

    create_meeting_participants(
        db=db,
        meeting_id=meeting.id,
        participant_ids=unique_participant_ids,
    )

    return MeetingResponse(
        meeting_id=meeting.id,
        workspace_id=meeting.workspace_id,
        title=meeting.title,
        meeting_type=meeting.meeting_type,
        scheduled_at=meeting.scheduled_at,
        room_name=meeting.room_name,
        participant_ids=unique_participant_ids,
        status=meeting.status,
        created_at=meeting.created_at,
    )


def update_meeting_service(
    db: Session,
    meeting_id: int,
    payload: MeetingCreateRequest,
) -> MeetingResponse:
    """
    회의 수정을 처리합니다.

    title, meeting_type, scheduled_at, room_name, participant_ids를 함께 수정합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    unique_participant_ids = _validate_participant_ids(
        db=db,
        workspace_id=meeting.workspace_id,
        participant_ids=payload.participant_ids,
    )

    updated_meeting = update_meeting(
        db=db,
        meeting_id=meeting_id,
        title=payload.title,
        meeting_type=payload.meeting_type,
        scheduled_at=payload.scheduled_at,
        room_name=payload.room_name,
    )
    if not updated_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    replace_meeting_participants(
        db=db,
        meeting_id=meeting_id,
        participant_ids=unique_participant_ids,
    )

    return MeetingResponse(
        meeting_id=updated_meeting.id,
        workspace_id=updated_meeting.workspace_id,
        title=updated_meeting.title,
        meeting_type=updated_meeting.meeting_type,
        scheduled_at=updated_meeting.scheduled_at,
        room_name=updated_meeting.room_name,
        participant_ids=unique_participant_ids,
        status=updated_meeting.status,
        created_at=updated_meeting.created_at,
    )


def get_meeting_service(db: Session, meeting_id: int) -> MeetingResponse:
    """
    회의 단건 조회를 처리합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    participant_ids = get_meeting_participant_user_ids(db, meeting_id)

    return MeetingResponse(
        meeting_id=meeting.id,
        workspace_id=meeting.workspace_id,
        title=meeting.title,
        meeting_type=meeting.meeting_type,
        scheduled_at=meeting.scheduled_at,
        room_name=meeting.room_name,
        participant_ids=participant_ids,
        status=meeting.status,
        created_at=meeting.created_at,
    )


def start_meeting_service(db: Session, meeting_id: int) -> MeetingResponse:
    """
    회의 시작 처리를 수행합니다.

    scheduled 상태의 회의만 in_progress로 변경합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    if meeting.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="시작 가능한 상태의 회의가 아닙니다.",
        )

    updated_meeting = update_meeting_status(
        db=db,
        meeting_id=meeting_id,
        status="in_progress",
    )
    if not updated_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    return _to_meeting_response(db, updated_meeting)


def end_meeting_service(db: Session, meeting_id: int) -> MeetingResponse:
    """
    회의 종료 처리를 수행합니다.

    in_progress 상태의 회의만 done으로 변경합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    if meeting.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료 가능한 상태의 회의가 아닙니다.",
        )

    updated_meeting = update_meeting_status(
        db=db,
        meeting_id=meeting_id,
        status="done",
    )
    if not updated_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    return _to_meeting_response(db, updated_meeting)


def delete_meeting_service(db: Session, meeting_id: int) -> None:
    """
    회의 삭제를 처리합니다.

    회의 참석자 연결 정보를 먼저 삭제한 뒤 회의를 삭제합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )

    deleted = delete_meeting(db, meeting_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의를 찾을 수 없습니다.",
        )


def get_meeting_notes_service(db: Session, meeting_id: int) -> MeetingNotesResponse:
    """
    회의록을 조회합니다.

    저장된 회의록이 없으면 기본 회의록을 생성한 뒤 반환합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    note = _get_or_create_meeting_note(db, meeting)

    return _to_notes_response(meeting, note)


def update_meeting_notes_service(
    db: Session,
    meeting_id: int,
    payload: MeetingNotesUpdateRequest,
) -> MeetingNotesResponse:
    """
    회의록 편집 내용을 저장합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    _get_or_create_meeting_note(db, meeting)

    note = update_meeting_note(
        db=db,
        meeting_id=meeting_id,
        summary=payload.summary,
        decisions=payload.decisions,
        open_issues=payload.open_issues,
        action_items=[item.model_dump() for item in payload.action_items],
        transcript=[item.model_dump() for item in payload.transcript],
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회의록을 찾을 수 없습니다.",
        )

    return _to_notes_response(meeting, note)


def get_meeting_wbs_service(db: Session, meeting_id: int) -> MeetingWbsResponse:
    """
    저장된 WBS 목록을 조회합니다.

    WBS가 아직 없으면 회의록 액션 아이템 기준으로 최초 1회 생성한 뒤 DB에 저장합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    _get_or_create_meeting_wbs(db, meeting)

    return _to_wbs_response(db, meeting)


def update_meeting_wbs_task_service(
    db: Session,
    meeting_id: int,
    task_id: int,
    payload: MeetingWbsTaskUpdateRequest,
) -> MeetingWbsTaskResponse:
    """
    WBS 태스크 수정 내용을 DB에 저장합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    _get_or_create_meeting_wbs(db, meeting)

    updated_task = update_wbs_task(
        db=db,
        meeting_id=meeting_id,
        task_id=task_id,
        title=payload.title,
        assignee_name=payload.assignee_name,
        priority=payload.priority,
        status=payload.status,
        due_date=payload.due_date,
        progress=payload.progress,
        jira_key=payload.jira_key,
    )
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WBS 태스크를 찾을 수 없습니다.",
        )

    epic_tasks = get_wbs_tasks_by_epic_id(db, updated_task.epic_id)
    update_wbs_epic_progress(
        db=db,
        epic_id=updated_task.epic_id,
        progress=_calculate_epic_progress(epic_tasks),
    )

    return _to_wbs_task_response(updated_task)


def create_meeting_wbs_epic_service(
    db: Session,
    meeting_id: int,
    payload: MeetingWbsEpicCreateRequest,
) -> MeetingWbsEpicResponse:
    """
    WBS 에픽을 새로 생성합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    _get_or_create_meeting_wbs(db, meeting)
    epic = create_wbs_epic(
        db=db,
        meeting_id=meeting_id,
        title=payload.title,
        progress=0,
    )

    return MeetingWbsEpicResponse(
        id=str(epic.id),
        title=epic.title,
        progress=epic.progress,
        tasks=[],
    )


def create_meeting_wbs_task_service(
    db: Session,
    meeting_id: int,
    epic_id: int,
    payload: MeetingWbsTaskCreateRequest,
) -> MeetingWbsTaskResponse:
    """
    WBS 에픽 아래에 태스크를 새로 생성합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    epics = _get_or_create_meeting_wbs(db, meeting)
    epic_ids = {epic.id for epic in epics}
    if epic_id not in epic_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WBS 에픽을 찾을 수 없습니다.",
        )

    task = create_wbs_task(
        db=db,
        meeting_id=meeting_id,
        epic_id=epic_id,
        title=payload.title,
        assignee_name=payload.assignee_name,
        priority=payload.priority,
        status=payload.status,
        due_date=payload.due_date,
        progress=payload.progress,
        jira_key=payload.jira_key,
    )
    epic_tasks = get_wbs_tasks_by_epic_id(db, epic_id)
    update_wbs_epic_progress(
        db=db,
        epic_id=epic_id,
        progress=_calculate_epic_progress(epic_tasks),
    )

    return _to_wbs_task_response(task)


def get_meeting_report_service(
    db: Session,
    meeting_id: int,
    report_format: str,
) -> MeetingReportResponse:
    """
    저장된 보고서를 조회합니다.

    해당 형식의 보고서가 아직 없으면 회의록과 WBS 기준으로 생성해 DB에 저장합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    note = _get_or_create_meeting_note(db, meeting)
    _get_or_create_meeting_wbs(db, meeting)

    report = get_meeting_report(db, meeting_id, report_format)
    if not report:
        report = upsert_meeting_report(
            db=db,
            meeting_id=meeting_id,
            report_format=report_format,
            content=_build_report_content(db, meeting, note),
        )

    return MeetingReportResponse(
        meeting_id=meeting.id,
        title=meeting.title,
        format=report.format,
        content=report.content,
    )


def update_meeting_report_service(
    db: Session,
    meeting_id: int,
    report_format: str,
    payload: MeetingReportUpdateRequest,
) -> MeetingReportResponse:
    """
    보고서 편집 내용을 DB에 저장합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    report = upsert_meeting_report(
        db=db,
        meeting_id=meeting_id,
        report_format=report_format,
        content=payload.content,
    )

    return MeetingReportResponse(
        meeting_id=meeting.id,
        title=meeting.title,
        format=report.format,
        content=report.content,
    )


def export_meeting_service(
    db: Session,
    meeting_id: int,
    payload: MeetingExportRequest,
) -> MeetingExportResponse:
    """
    외부 서비스 내보내기 요청을 처리합니다.

    외부 서비스 연동 상태를 검증하고, 내보내기 요청 이력을 DB에 저장합니다.
    실제 OAuth Provider API 호출은 서비스별 키/정책이 확정된 뒤 adapter 계층으로 추가합니다.
    """
    meeting = _get_meeting_or_404(db, meeting_id)
    _get_or_create_meeting_note(db, meeting)
    _get_or_create_meeting_wbs(db, meeting)
    target = payload.target.replace("-", "_")
    external_targets = {"jira", "slack", "notion", "google_calendar", "kakao"}

    if target in external_targets:
        integration = get_integration_by_service(
            db=db,
            workspace_id=meeting.workspace_id,
            service=target,
        )
        if not integration or not integration.is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{payload.target} 연동이 필요합니다.",
            )

    message = f"{payload.target} 내보내기 요청이 저장되었습니다."
    create_export_log(
        db=db,
        meeting_id=meeting.id,
        target=payload.target,
        exported=True,
        message=message,
    )

    return MeetingExportResponse(
        meeting_id=meeting.id,
        target=payload.target,
        exported=True,
        message=message,
    )


def get_meetings_service(
    db: Session,
    workspace_id: int,
    meeting_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    keyword: str | None = None,
) -> MeetingListResponse:
    """
    워크스페이스별 회의 목록 조회를 처리합니다.

    status, from, to, keyword 조건을 받아 목록을 필터링합니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None

    meetings = get_meetings_by_workspace_id(
        db=db,
        workspace_id=workspace_id,
        status=meeting_status,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        keyword=keyword,
    )

    return MeetingListResponse(
        meetings=[
            MeetingResponse(
                meeting_id=meeting.id,
                workspace_id=meeting.workspace_id,
                title=meeting.title,
                meeting_type=meeting.meeting_type,
                scheduled_at=meeting.scheduled_at,
                room_name=meeting.room_name,
                participant_ids=get_meeting_participant_user_ids(db, meeting.id),
                status=meeting.status,
                created_at=meeting.created_at,
            )
            for meeting in meetings
        ]
    )


def get_meeting_history_service(
    db: Session,
    workspace_id: int,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    participant_id: int | None = None,
    page: int = 1,
    size: int = 10,
) -> MeetingHistoryResponse:
    """
    워크스페이스별 회의 히스토리 조회를 처리합니다.
    """
    workspace = get_workspace_by_id(db, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크스페이스를 찾을 수 없습니다.",
        )

    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None

    total, meetings = get_meeting_history_by_workspace_id(
        db=db,
        workspace_id=workspace_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        keyword=keyword,
        participant_id=participant_id,
        page=page,
        size=size,
    )

    return MeetingHistoryResponse(
        total=total,
        page=page,
        size=size,
        meetings=[
            MeetingResponse(
                meeting_id=meeting.id,
                workspace_id=meeting.workspace_id,
                title=meeting.title,
                meeting_type=meeting.meeting_type,
                scheduled_at=meeting.scheduled_at,
                room_name=meeting.room_name,
                participant_ids=get_meeting_participant_user_ids(db, meeting.id),
                status=meeting.status,
                created_at=meeting.created_at,
            )
            for meeting in meetings
        ],
    )
