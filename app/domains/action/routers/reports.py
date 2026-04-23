# app/domains/action/routers/reports/py
import io
import json
import markdown as md_lib
from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.infra.database.session import get_db
from app.domains.action import repository
from app.domains.action.models import ReportFormat
from app.domains.action.schemas import (
    ReportResponse, ReportGenerateRequest, ReportPatchRequest, ExportResponse
)
from app.domains.action.services import report_builder
from app.domains.user.dependencies import require_workspace_admin, require_workspace_member

router = APIRouter()

_GENERATORS = {
    "markdown": report_builder.generate_markdown,
    "html":     report_builder.generate_html,
    "excel":    report_builder.generate_excel,
    "wbs":      report_builder.generate_wbs,
}

@router.post("/reports/generate", response_model=ExportResponse)
async def generate_report(
    meeting_id: int,
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    workspace_id: int = Query(..., description="워크스페이스ID"),
    db: Session = Depends(get_db),
    _admin = Depends(require_workspace_admin),
):
    fmt = request.format.lower()
    if fmt not in _GENERATORS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 포맷: {fmt}")
    
    background_tasks.add_task(
        _GENERATORS[fmt],
        db=db,
        meeting_id=meeting_id,
        user_id=_admin.id
    )
    return ExportResponse(status="processing")

@router.get("/reports", response_model=list[ReportResponse])
def get_reports(
    meeting_id: int,
    workspace_id: int = Query(...),
    db: Session = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    return repository.get_reports(db, meeting_id)


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(
    meeting_id: int,
    report_id: int,
    workspace_id: int = Query(...),
    db: Session = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    report = repository.get_report(db, report_id)
    if not report or report.meeting_id != meeting_id:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    return report


@router.get("/reports/{report_id}/view", response_class=HTMLResponse)
def view_report(
    meeting_id: int,
    report_id: int,
    workspace_id: int = Query(...),
    db: Session = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    report = repository.get_report(db, report_id)
    if not report or report.meeting_id != meeting_id:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")

    if report.format in (ReportFormat.markdown, ReportFormat.html):
        content = report.content
        if not content:
            minute  = repository.get_meeting_minute(db, meeting_id)
            content = minute.content if minute else ""
        html_body = md_lib.markdown(content or "", extensions=["tables", "fenced_code"])
        return f"<html><body style='max-width:800px;margin:auto;padding:2rem'>{html_body}</body></html>"

    if report.format == ReportFormat.wbs:
        wbs  = json.loads(report.content or "{}")
        rows = []
        for epic in wbs.get("epics", []):
            rows.append(f"<h2>{epic['title']}</h2><ul>")
            for task in epic.get("tasks", []):
                rows.append(f"<li>[{task.get('assignee','')}] {task['title']}</li>")
            rows.append("</ul>")
        body = "".join(rows)
        return f"<html><body style='max-width:800px;margin:auto;padding:2rem'>{body}</body></html>"

    raise HTTPException(status_code=400, detail="이 포맷은 view를 지원하지 않습니다.")


@router.get("/reports/{report_id}/download")
def download_report(
    meeting_id: int,
    report_id: int,
    workspace_id: int = Query(...),
    db: Session = Depends(get_db),
    _member=Depends(require_workspace_member),
):
    report = repository.get_report(db, report_id)
    if not report or report.meeting_id != meeting_id:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")

    if report.format == ReportFormat.excel:
        if not report.file_url:
            raise HTTPException(status_code=404, detail="파일이 아직 생성되지 않았습니다.")
        return FileResponse(
            report.file_url,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{report.title}.xlsx",
        )

    if report.format == ReportFormat.html:
        minute   = repository.get_meeting_minute(db, meeting_id)
        content  = minute.content if minute else ""
        html_str = md_lib.markdown(content or "", extensions=["tables", "fenced_code"])
        html     = f"<html><body style='max-width:800px;margin:auto;padding:2rem'>{html_str}</body></html>"
        return StreamingResponse(
            io.BytesIO(html.encode("utf-8")),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.html"'},
        )

    if report.format == ReportFormat.markdown:
        return StreamingResponse(
            io.BytesIO((report.content or "").encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.md"'},
        )

    if report.format == ReportFormat.wbs:
        return StreamingResponse(
            io.BytesIO((report.content or "{}").encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.json"'},
        )

    raise HTTPException(status_code=400, detail="다운로드 불가 포맷입니다.")

@router.patch("/reports/{report_id}", response_model=ReportResponse)
def patch_report(
    meeting_id: int,
    report_id: int,
    body: ReportPatchRequest,
    workspace_id: int = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_workspace_admin),
):
    report = repository.get_report(db, report_id)
    if not report or report.meeting_id != meeting_id:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    if report.format == ReportFormat.excel:
        raise HTTPException(status_code=400, detail="Excel 보고서는 수정할 수 없습니다.")
    return repository.update_report(db, report_id, body.content)