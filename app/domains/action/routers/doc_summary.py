# app/domains/action/routers/doc_summary.py
import io
import logging
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.domains.action.services.doc_summary_builder import EXT_MAP, process_document

logger = logging.getLogger(__name__)
router = APIRouter()

_SUPPORTED_EXTS = set(EXT_MAP.keys())


@router.post(
    "/doc-summary/generate",
    summary="문서 → 회의 요약 PDF 생성",
    description=(
        "업로드된 문서(PDF/DOCX/PPTX/HTML/MD/XLSX/TXT)에서 회의 관련 정보를 AI로 추출해 "
        "표준화된 회의 요약 PDF를 반환합니다. 파일명: meeting_summary_YYYYMMDD_HHMM.pdf"
    ),
    response_class=StreamingResponse,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "회의 요약 PDF"},
        400: {"description": "빈 파일"},
        415: {"description": "지원하지 않는 파일 형식"},
        422: {"description": "텍스트 추출 또는 AI 처리 실패"},
        500: {"description": "서버 오류"},
    },
)
async def generate_doc_summary(
    file: UploadFile = File(..., description="분석할 문서 파일"),
):
    filename = file.filename or "document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in _SUPPORTED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"지원하지 않는 파일 형식: .{ext}  "
                f"지원 형식: {', '.join(sorted(_SUPPORTED_EXTS))}"
            ),
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="파일이 비어 있습니다.")

    try:
        pdf_bytes, output_filename = await process_document(file_bytes, filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("doc_summary 처리 실패 [%s]: %s", filename, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "문서 처리 중 오류가 발생했습니다. "
                "파일을 확인한 후 다시 시도해 주세요."
            ),
        )

    encoded = quote(output_filename, safe="")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
            "Content-Length": str(len(pdf_bytes)),
        },
    )
