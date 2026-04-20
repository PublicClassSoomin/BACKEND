# app\domains\meeting\repository.py

"""
회의(meeting) 도메인의 데이터베이스 접근 로직을 담당하는 파일입니다. repository 계층은 service 계층과 데이터베이스 사이에서 실제 조회 및 저장 작업을 수행합니다. 즉, service 계층은 처리 흐름을 결정하고, repository 계층은 DB에서 어떻게 조회하고 저장할지를 담당합니다.
현재는 회의 생성과 상세 조회에 필요한 최소한의 repository 함수만 정의합니다. 향후 회의 업데이트, 삭제, 목록 조회 등의 기능이 추가되면 해당 기능에 필요한 repository 함수도 함께 추가할 예정입니다.
"""


from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domains.meeting.models import (
    Meeting,
    MeetingExportLog,
    MeetingNote,
    MeetingParticipant,
    MeetingReport,
    MeetingWbsEpic,
    MeetingWbsTask,
)


def create_meeting(
    db: Session,
    workspace_id: int,
    title: str,
    meeting_type: str,
    scheduled_at: datetime,
    room_name: str | None,
) -> Meeting:
    """
    새 회의를 생성하고 저장합니다.
    """
    meeting = Meeting(
        workspace_id=workspace_id,
        title=title,
        meeting_type=meeting_type,
        scheduled_at=scheduled_at,
        room_name=room_name,
        status="scheduled",
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


def get_meeting_by_id(db: Session, meeting_id: int) -> Meeting | None:
    """
    회의 ID를 기준으로 회의를 조회합니다.
    """
    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def update_meeting(
    db: Session,
    meeting_id: int,
    title: str,
    meeting_type: str,
    scheduled_at: datetime,
    room_name: str | None,
) -> Meeting | None:
    """
    기존 회의 정보를 수정합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        return None

    meeting.title = title
    meeting.meeting_type = meeting_type
    meeting.scheduled_at = scheduled_at
    meeting.room_name = room_name

    db.commit()
    db.refresh(meeting)

    return meeting


def update_meeting_status(
    db: Session,
    meeting_id: int,
    status: str,
) -> Meeting | None:
    """
    특정 회의의 상태를 변경합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        return None

    meeting.status = status
    db.commit()
    db.refresh(meeting)

    return meeting


def delete_meeting(db: Session, meeting_id: int) -> bool:
    """
    특정 회의와 참석자 연결 정보를 삭제합니다.

    참석자 연결 row를 먼저 삭제한 뒤 회의를 삭제합니다.
    """
    meeting = get_meeting_by_id(db, meeting_id)
    if not meeting:
        return False

    db.query(MeetingExportLog).filter(
        MeetingExportLog.meeting_id == meeting_id
    ).delete()
    db.query(MeetingReport).filter(
        MeetingReport.meeting_id == meeting_id
    ).delete()
    db.query(MeetingWbsTask).filter(
        MeetingWbsTask.meeting_id == meeting_id
    ).delete()
    db.query(MeetingWbsEpic).filter(
        MeetingWbsEpic.meeting_id == meeting_id
    ).delete()
    db.query(MeetingNote).filter(
        MeetingNote.meeting_id == meeting_id
    ).delete()
    db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).delete()
    db.delete(meeting)
    db.commit()

    return True


def create_meeting_participants(
    db: Session,
    meeting_id: int,
    participant_ids: list[int],
) -> list[MeetingParticipant]:
    """
    특정 회의의 참석자 연결 row를 생성합니다.
    """
    participants = [
        MeetingParticipant(
            meeting_id=meeting_id,
            user_id=user_id,
        )
        for user_id in participant_ids
    ]

    if not participants:
        return []

    db.add_all(participants)
    db.commit()

    for participant in participants:
        db.refresh(participant)

    return participants


def get_meeting_participant_user_ids(db: Session, meeting_id: int) -> list[int]:
    """
    특정 회의에 연결된 참석자 user_id 목록을 조회합니다.
    """
    participants = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.meeting_id == meeting_id)
        .order_by(MeetingParticipant.id.asc())
        .all()
    )

    return [participant.user_id for participant in participants]


def replace_meeting_participants(
    db: Session,
    meeting_id: int,
    participant_ids: list[int],
) -> list[MeetingParticipant]:
    """
    특정 회의의 참석자 연결 정보를 새 목록으로 교체합니다.

    기존 row를 모두 삭제한 뒤 새 row를 다시 생성합니다.
    """
    db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).delete()
    db.commit()

    return create_meeting_participants(db, meeting_id, participant_ids)


def get_meetings_by_workspace_id(
    db: Session,
    workspace_id: int,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    keyword: str | None = None,
) -> list[Meeting]:
    """
    특정 워크스페이스의 회의 목록을 조회합니다.

    status, from, to, keyword 조건이 있으면 함께 필터링합니다.
    keyword는 제목과 회의실 이름(room_name)에 대해 검색합니다.
    """
    query = db.query(Meeting).filter(Meeting.workspace_id == workspace_id)

    if status is not None:
        query = query.filter(Meeting.status == status)

    if date_from is not None:
        query = query.filter(Meeting.scheduled_at >= date_from)

    if date_to is not None:
        query = query.filter(Meeting.scheduled_at <= date_to)

    if keyword is not None and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Meeting.title.like(pattern),
                Meeting.room_name.like(pattern),
            )
        )

    return query.order_by(Meeting.scheduled_at.desc()).all()


def get_meeting_ids_by_participant_id(
    db: Session,
    participant_id: int,
) -> list[int]:
    """
    특정 사용자가 참석자로 연결된 meeting_id 목록을 조회합니다.
    """
    participants = (
        db.query(MeetingParticipant)
        .filter(MeetingParticipant.user_id == participant_id)
        .all()
    )

    return [participant.meeting_id for participant in participants]


def get_meeting_history_by_workspace_id(
    db: Session,
    workspace_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    keyword: str | None = None,
    participant_id: int | None = None,
    page: int = 1,
    size: int = 10,
) -> tuple[int, list[Meeting]]:
    """
    워크스페이스 기준 회의 히스토리 목록을 조회합니다.

    keyword는 title, room_name에 대해 검색합니다.
    participant_id가 전달되면 해당 참석자가 포함된 회의만 조회합니다.
    """
    query = db.query(Meeting).filter(Meeting.workspace_id == workspace_id)

    if date_from is not None:
        query = query.filter(Meeting.scheduled_at >= date_from)

    if date_to is not None:
        query = query.filter(Meeting.scheduled_at <= date_to)

    if keyword is not None and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Meeting.title.like(pattern),
                Meeting.room_name.like(pattern),
            )
        )

    if participant_id is not None:
        meeting_ids = get_meeting_ids_by_participant_id(db, participant_id)
        if not meeting_ids:
            return 0, []
        query = query.filter(Meeting.id.in_(meeting_ids))

    total = query.count()
    meetings = (
        query.order_by(Meeting.scheduled_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return total, meetings


def get_meeting_note_by_meeting_id(db: Session, meeting_id: int) -> MeetingNote | None:
    """
    meeting_id 기준으로 저장된 회의록을 조회합니다.
    """
    return db.query(MeetingNote).filter(MeetingNote.meeting_id == meeting_id).first()


def create_meeting_note(
    db: Session,
    meeting_id: int,
    summary: str,
    decisions: list[str],
    open_issues: list[str],
    action_items: list[dict],
    transcript: list[dict],
) -> MeetingNote:
    """
    회의록 row를 생성합니다.
    """
    note = MeetingNote(
        meeting_id=meeting_id,
        summary=summary,
        decisions=decisions,
        open_issues=open_issues,
        action_items=action_items,
        transcript=transcript,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def get_wbs_epics_by_meeting_id(db: Session, meeting_id: int) -> list[MeetingWbsEpic]:
    """
    회의 ID 기준으로 저장된 WBS 에픽 목록을 조회합니다.
    """
    return (
        db.query(MeetingWbsEpic)
        .filter(MeetingWbsEpic.meeting_id == meeting_id)
        .order_by(MeetingWbsEpic.id.asc())
        .all()
    )


def get_wbs_tasks_by_epic_id(db: Session, epic_id: int) -> list[MeetingWbsTask]:
    """
    에픽 ID 기준으로 저장된 WBS 태스크 목록을 조회합니다.
    """
    return (
        db.query(MeetingWbsTask)
        .filter(MeetingWbsTask.epic_id == epic_id)
        .order_by(MeetingWbsTask.id.asc())
        .all()
    )


def get_wbs_task_by_id(
    db: Session,
    meeting_id: int,
    task_id: int,
) -> MeetingWbsTask | None:
    """
    회의 ID와 태스크 ID 기준으로 WBS 태스크를 조회합니다.
    """
    return (
        db.query(MeetingWbsTask)
        .filter(
            MeetingWbsTask.meeting_id == meeting_id,
            MeetingWbsTask.id == task_id,
        )
        .first()
    )


def create_wbs_epic(
    db: Session,
    meeting_id: int,
    title: str,
    progress: int,
) -> MeetingWbsEpic:
    """
    WBS 에픽을 생성합니다.
    """
    epic = MeetingWbsEpic(
        meeting_id=meeting_id,
        title=title,
        progress=progress,
    )

    db.add(epic)
    db.commit()
    db.refresh(epic)

    return epic


def create_wbs_task(
    db: Session,
    meeting_id: int,
    epic_id: int,
    title: str,
    assignee_name: str | None,
    priority: str,
    status: str,
    due_date: str | None,
    progress: int,
    jira_key: str | None = None,
) -> MeetingWbsTask:
    """
    WBS 태스크를 생성합니다.
    """
    task = MeetingWbsTask(
        meeting_id=meeting_id,
        epic_id=epic_id,
        title=title,
        assignee_name=assignee_name,
        priority=priority,
        status=status,
        due_date=due_date,
        progress=progress,
        jira_key=jira_key,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def update_wbs_task(
    db: Session,
    meeting_id: int,
    task_id: int,
    title: str | None = None,
    assignee_name: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    due_date: str | None = None,
    progress: int | None = None,
    jira_key: str | None = None,
) -> MeetingWbsTask | None:
    """
    WBS 태스크 정보를 수정합니다.
    """
    task = get_wbs_task_by_id(db, meeting_id, task_id)
    if not task:
        return None

    if title is not None:
        task.title = title
    if assignee_name is not None:
        task.assignee_name = assignee_name
    if priority is not None:
        task.priority = priority
    if status is not None:
        task.status = status
    if due_date is not None:
        task.due_date = due_date
    if progress is not None:
        task.progress = progress
    if jira_key is not None:
        task.jira_key = jira_key

    db.commit()
    db.refresh(task)

    return task


def update_wbs_epic_progress(
    db: Session,
    epic_id: int,
    progress: int,
) -> MeetingWbsEpic | None:
    """
    WBS 에픽 진행률을 수정합니다.
    """
    epic = db.query(MeetingWbsEpic).filter(MeetingWbsEpic.id == epic_id).first()
    if not epic:
        return None

    epic.progress = progress
    db.commit()
    db.refresh(epic)

    return epic


def get_meeting_report(
    db: Session,
    meeting_id: int,
    report_format: str,
) -> MeetingReport | None:
    """
    회의 ID와 보고서 형식 기준으로 저장된 보고서를 조회합니다.
    """
    return (
        db.query(MeetingReport)
        .filter(
            MeetingReport.meeting_id == meeting_id,
            MeetingReport.format == report_format,
        )
        .first()
    )


def upsert_meeting_report(
    db: Session,
    meeting_id: int,
    report_format: str,
    content: str,
) -> MeetingReport:
    """
    회의 보고서를 생성하거나 기존 보고서를 수정합니다.
    """
    report = get_meeting_report(db, meeting_id, report_format)
    if report:
        report.content = content
    else:
        report = MeetingReport(
            meeting_id=meeting_id,
            format=report_format,
            content=content,
        )
        db.add(report)

    db.commit()
    db.refresh(report)

    return report


def create_export_log(
    db: Session,
    meeting_id: int,
    target: str,
    exported: bool,
    message: str,
) -> MeetingExportLog:
    """
    회의 산출물 내보내기 이력을 저장합니다.
    """
    log = MeetingExportLog(
        meeting_id=meeting_id,
        target=target,
        exported=exported,
        message=message,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def update_meeting_note(
    db: Session,
    meeting_id: int,
    summary: str,
    decisions: list[str],
    open_issues: list[str],
    action_items: list[dict],
    transcript: list[dict],
) -> MeetingNote | None:
    """
    저장된 회의록 row를 수정합니다.
    """
    note = get_meeting_note_by_meeting_id(db, meeting_id)
    if not note:
        return None

    note.summary = summary
    note.decisions = decisions
    note.open_issues = open_issues
    note.action_items = action_items
    note.transcript = transcript

    db.commit()
    db.refresh(note)

    return note
