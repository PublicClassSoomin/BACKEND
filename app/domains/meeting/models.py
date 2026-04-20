# app\domains\meeting\models.py
from sqlalchemy import Column, String, Enum, DateTime, Boolean, ForeignKey, Integer, JSON, Text, func
from app.infra.database.base import Base
import enum

class MeetingStatus(str, enum.Enum):
    scheduled   = "scheduled"
    in_progress = "in_progress"
    done        = "done"

class DiarizationMethod(str, enum.Enum):
    stereo      = "stereo"
    diarization = "diarization"

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(200), nullable=False)
    meeting_type = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    room_name = Column(String(255), nullable=True)
    status = Column(String(20), default=MeetingStatus.scheduled.value, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class MeetingNote(Base):
    __tablename__ = "meeting_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    summary = Column(Text, nullable=False)
    decisions = Column(JSON, nullable=False, default=list)
    open_issues = Column(JSON, nullable=False, default=list)
    action_items = Column(JSON, nullable=False, default=list)
    transcript = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class MeetingWbsEpic(Base):
    __tablename__ = "meeting_wbs_epics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    title = Column(String(255), nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class MeetingWbsTask(Base):
    __tablename__ = "meeting_wbs_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    epic_id = Column(Integer, ForeignKey("meeting_wbs_epics.id"), nullable=False)
    title = Column(String(255), nullable=False)
    assignee_name = Column(String(100), nullable=True)
    priority = Column(String(20), default="medium", nullable=False)
    status = Column(String(20), default="todo", nullable=False)
    due_date = Column(String(50), nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    jira_key = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class MeetingReport(Base):
    __tablename__ = "meeting_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    format = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class MeetingExportLog(Base):
    __tablename__ = "meeting_export_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    target = Column(String(50), nullable=False)
    exported = Column(Boolean, default=False, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

class Agenda(Base):
    __tablename__ = "agendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

class AgendaItem(Base):
    __tablename__ = "agenda_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agenda_id = Column(Integer, ForeignKey("agendas.id"), nullable=False)
    title = Column(String(200), nullable=False)
    presenter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    estimated_minutes = Column(Integer, nullable=True)
    reference_url = Column(String(500), nullable=True)
    order_index = Column(Integer, nullable=False)

class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    voice_model_path = Column(String(500), nullable=True)
    diarization_method = Column(Enum(DiarizationMethod), nullable=False)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
