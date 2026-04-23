# app/domains/action/services/wbs_builder.py
from sqlalchemy.orm import Session
from app.domains.action import repository
from app.domains.action.mongo_repository import get_meeting_summary

async def build_wbs_template(db: Session, meeting_id: int) -> dict:
    epics = repository.get_wbs_epics(db, meeting_id)
    if epics:
        return _from_wbs_table(db, epics)
    
    summary = get_meeting_summary(meeting_id)
    return _persist_and_build(db, meeting_id, summary)

def _from_wbs_table(db: Session, epics: list) -> dict:
    result = []
    for epic in epics:
        tasks = repository.get_wbs_tasks_by_epic(db, epic.id)
        task_list = []
        for t in tasks:
            user = repository.get_user(db, t.assignee_id) if t.assignee_id else None
            task_list.append({
                "id":       t.id,
                "title":    t.title,
                "assignee": user.name if user else "",
                "due_date": str(t.due_date) if t.due_date else None,
                "priority": t.priority.value,
                "urgency": "normal",
            })
        result.append({
            "id": epic.id,
            "title": epic.title,
            "tasks": task_list
        })
    return {
        "epics": result
    }

def _persist_and_build(
        db: Session, 
        meeting_id: int, 
        summary: dict
) -> dict:
    overview = summary.get("overview", {})
    epic_title = overview.get("purpose", "주요 실행 과제")
    action_items = summary.get("action_items", [])

    epic = repository.save_wbs_epic(db, meeting_id, epic_title, order_index=0)

    task_list = []
    for a in action_items:
        task = repository.save_wbs_task(
            db=db,
            epic_id=epic.id,
            title=a.get("content", ""),
            priority=a.get("priority", "medium"),
        )
        task_list.append({
            "id":       task.id,
            "title":    task.title,
            "assignee": a.get("assignee", ""),
            "due_date": a.get("deadline"),
            "priority": a.get("priority", "normal"),
            "urgency":  a.get("urgency", "normal"),
        })
    
    return {
        "epics": [
            {
                "id": epic.id,
                "title": epic_title,
                "tasks": task_list
            }
        ]
    }