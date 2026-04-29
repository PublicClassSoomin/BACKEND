# tests/test_doc_summary.py
"""
회의 요약 PDF 생성 기능 테스트.

단위 테스트: extract_text, generate_pdf, extract_meeting_info
통합 테스트: POST /actions/doc-summary/generate (LLM mock)
"""
from __future__ import annotations

import io
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ── 모듈 레벨 패치: conftest가 로드되기 전에도 안전하게 처리됨 ─────────────────
# doc_summary_builder는 conftest mock 리스트에 없으므로 직접 import 가능


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures & helpers
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_SUMMARY = {
    "meeting_topic": "Q2 스프린트 계획",
    "datetime": "2026-04-29 14:00",
    "attendees": ["김민준", "이수민"],
    "discussion_items": [
        {"topic": "백엔드 API 일정", "content": "4월 말까지 완료 목표"},
    ],
    "decisions": [{"content": "Slack 알림 기능 우선 배포"}],
    "action_items": [
        {
            "assignee": "김민준",
            "content": "API 문서 작성",
            "deadline": "2026-05-03",
            "status": "미정",
        },
        {
            "assignee": "확인 필요",
            "content": "QA 테스트 케이스 작성",
            "deadline": "확인 필요",
            "status": "미정",
        },
    ],
    "issues_risks": [{"content": "외부 API 응답 지연 가능성"}],
    "next_steps": ["다음 스프린트 계획 수립"],
}

SAMPLE_TEXT = "Q2 스프린트 계획 회의\n참석자: 김민준, 이수민\n백엔드 API 4월 말까지 완료 목표"


# ─────────────────────────────────────────────────────────────────────────────
# Unit: generate_pdf
# ─────────────────────────────────────────────────────────────────────────────

class TestGeneratePdf:
    def test_pdf_bytes_returned(self):
        from app.domains.action.services.doc_summary_builder import generate_pdf

        pdf = generate_pdf(SAMPLE_SUMMARY, "test_meeting.pdf")
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_pdf_empty_sections(self):
        """액션 아이템 등이 모두 비어 있어도 PDF 생성에 실패하지 않아야 한다."""
        from app.domains.action.services.doc_summary_builder import generate_pdf

        empty = {
            "meeting_topic": "확인 필요",
            "datetime": "확인 필요",
            "attendees": [],
            "discussion_items": [],
            "decisions": [],
            "action_items": [],
            "issues_risks": [],
            "next_steps": [],
        }
        pdf = generate_pdf(empty, "empty.pdf")
        assert pdf[:4] == b"%PDF"

    def test_pdf_none_fields(self):
        """None 값이 들어와도 예외가 발생하지 않아야 한다."""
        from app.domains.action.services.doc_summary_builder import generate_pdf

        sparse = {"meeting_topic": None, "action_items": None}
        pdf = generate_pdf(sparse, "sparse.pdf")
        assert pdf[:4] == b"%PDF"

    def test_pdf_many_action_items(self):
        """액션 아이템이 많아도 표가 정상 생성되어야 한다."""
        from app.domains.action.services.doc_summary_builder import generate_pdf

        summary = dict(SAMPLE_SUMMARY)
        summary["action_items"] = [
            {"assignee": f"담당자{i}", "content": f"태스크 {i}", "deadline": "2026-05-01", "status": "미정"}
            for i in range(20)
        ]
        pdf = generate_pdf(summary, "many_actions.pdf")
        assert pdf[:4] == b"%PDF"


# ─────────────────────────────────────────────────────────────────────────────
# Unit: extract_text
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractText:
    def test_unsupported_extension_raises(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            extract_text(b"data", "file.exe")

    def test_empty_text_raises(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        with patch(
            "app.domains.action.services.doc_summary_builder._extract_md",
            return_value="   ",
        ):
            with pytest.raises(ValueError, match="텍스트를 추출할 수 없습니다"):
                extract_text(b"# empty", "doc.md")

    def test_md_extraction(self):
        """TXT/MD 파일은 단순 디코딩이므로 외부 의존 없이 테스트 가능."""
        from app.domains.action.services.doc_summary_builder import extract_text

        content = "# 회의록\n\n참석자: 김민준"
        result = extract_text(content.encode("utf-8"), "notes.md")
        assert "회의록" in result

    def test_txt_extraction(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        content = "회의 내용입니다."
        result = extract_text(content.encode("utf-8"), "notes.txt")
        assert "회의" in result

    def test_pdf_extraction_mocked(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        with patch(
            "app.domains.action.services.doc_summary_builder._extract_pdf",
            return_value="PDF 내용",
        ):
            result = extract_text(b"%PDF", "doc.pdf")
        assert result == "PDF 내용"

    def test_html_extraction_mocked(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        with patch(
            "app.domains.action.services.doc_summary_builder._extract_html",
            return_value="HTML 본문",
        ):
            result = extract_text(b"<html><body>test</body></html>", "page.html")
        assert result == "HTML 본문"

    def test_docx_extraction_mocked(self):
        from app.domains.action.services.doc_summary_builder import extract_text

        with patch(
            "app.domains.action.services.doc_summary_builder._extract_docx",
            return_value="DOCX 내용",
        ):
            result = extract_text(b"PK\x03\x04", "doc.docx")
        assert result == "DOCX 내용"


# ─────────────────────────────────────────────────────────────────────────────
# Unit: extract_meeting_info
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractMeetingInfo:
    @pytest.mark.asyncio
    async def test_valid_ai_response(self):
        from app.domains.action.services.doc_summary_builder import extract_meeting_info

        mock_response = MagicMock()
        mock_response.content = json.dumps(SAMPLE_SUMMARY)

        with patch(
            "app.domains.action.services.doc_summary_builder._llm",
        ) as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await extract_meeting_info(SAMPLE_TEXT)

        assert result["meeting_topic"] == "Q2 스프린트 계획"
        assert len(result["action_items"]) == 2

    @pytest.mark.asyncio
    async def test_json_embedded_in_text(self):
        """LLM이 JSON 앞뒤에 설명 텍스트를 붙이는 경우 처리."""
        from app.domains.action.services.doc_summary_builder import extract_meeting_info

        mock_response = MagicMock()
        mock_response.content = (
            "아래는 추출 결과입니다.\n"
            + json.dumps(SAMPLE_SUMMARY)
            + "\n이상입니다."
        )

        with patch(
            "app.domains.action.services.doc_summary_builder._llm",
        ) as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await extract_meeting_info(SAMPLE_TEXT)

        assert result["meeting_topic"] == "Q2 스프린트 계획"

    @pytest.mark.asyncio
    async def test_no_json_raises(self):
        from app.domains.action.services.doc_summary_builder import extract_meeting_info

        mock_response = MagicMock()
        mock_response.content = "JSON을 생성할 수 없습니다."

        with patch(
            "app.domains.action.services.doc_summary_builder._llm",
        ) as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            with pytest.raises(ValueError, match="파싱"):
                await extract_meeting_info(SAMPLE_TEXT)

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self):
        from app.domains.action.services.doc_summary_builder import extract_meeting_info

        mock_response = MagicMock()
        mock_response.content = "{broken json: true,}"

        with patch(
            "app.domains.action.services.doc_summary_builder._llm",
        ) as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            with pytest.raises(ValueError, match="형식이 올바르지 않습니다"):
                await extract_meeting_info(SAMPLE_TEXT)


# ─────────────────────────────────────────────────────────────────────────────
# Integration: POST /actions/doc-summary/generate
# ─────────────────────────────────────────────────────────────────────────────

class TestDocSummaryEndpoint:
    def test_unsupported_format(self, client):
        resp = client.post(
            "/api/v1/actions/doc-summary/generate",
            files={"file": ("evil.exe", b"binary data", "application/octet-stream")},
        )
        assert resp.status_code == 415

    def test_empty_file(self, client):
        resp = client.post(
            "/api/v1/actions/doc-summary/generate",
            files={"file": ("notes.md", b"", "text/markdown")},
        )
        assert resp.status_code == 400

    def test_md_success(self, client):
        """Markdown 파일 → PDF 반환 (LLM mock)."""
        with patch(
            "app.domains.action.services.doc_summary_builder.extract_meeting_info",
            new=AsyncMock(return_value=SAMPLE_SUMMARY),
        ):
            resp = client.post(
                "/api/v1/actions/doc-summary/generate",
                files={
                    "file": (
                        "meeting_notes.md",
                        SAMPLE_TEXT.encode(),
                        "text/markdown",
                    )
                },
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
        assert "meeting_summary_" in resp.headers.get("content-disposition", "")

    # anyio 4.x + Starlette TestClient: await 이후 예외 발생 시 CancelledError 전파되는
    # 알려진 호환성 문제로 인해 비동기 처리 중 에러 경로(422/500)의 HTTP 스택 테스트는 생략.
    # 커버리지: test_empty_text_raises(ValueError 발생) + test_unsupported_format(동기 415)
    # + 라우터 코드의 명확한 except ValueError → HTTPException(422) 로직으로 대체.
