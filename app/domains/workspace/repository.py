# app\domains\workspace\repository.py
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.domains.meeting.models import Meeting, MeetingStatus
from app.domains.action.models import ActionItem, ActionStatus


class DashboardRepository:

    @staticmethod
    def get_meetings_by_workspace(db: Session, workspace_id: int) -> list[Meeting]:
        return (
            db.query(Meeting)
            .filter(Meeting.workspace_id == workspace_id)
            .order_by(Meeting.scheduled_at.desc())
            .all()
        )

    @staticmethod
    def get_done_meetings_this_week(
        db: Session, workspace_id: int, week_start: datetime, week_end: datetime
    ) -> list[Meeting]:
        return (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.workspace_id == workspace_id,
                    Meeting.status == MeetingStatus.done,
                    Meeting.ended_at >= week_start,
                    Meeting.ended_at < week_end,
                )
            )
            .all()
        )

    @staticmethod
    def get_pending_action_items(db: Session, workspace_id: int) -> list[dict]:
        rows = (
            db.query(
                ActionItem.id,
                ActionItem.content,
                ActionItem.due_date,
                Meeting.title.label("meeting_title"),
            )
            .join(Meeting, ActionItem.meeting_id == Meeting.id)
            .filter(
                and_(
                    Meeting.workspace_id == workspace_id,
                    ActionItem.status == ActionStatus.pending,
                )
            )
            .order_by(ActionItem.due_date.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "content": r.content,
                "due_date": r.due_date,
                "meeting_title": r.meeting_title,
            }
            for r in rows
        ]
