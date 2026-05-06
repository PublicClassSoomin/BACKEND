"""
PyMuPDF(fitz) 기반 PDF 오버레이 렌더러.
storage/templates/minutes_template.pdf(자동 생성)에
필드 값을 좌표 기반으로 삽입한다.

[넘침 정책] 클리핑 — insert_textbox 가 rect 경계를 자동으로 클리핑.
[폰트 정책] storage/fonts/NanumGothic.ttf → 시스템 경로 → helv(한글 깨짐)
[실패 정책] 예외를 그대로 raise → 호출자(router)가 HTML 렌더러로 폴백.
"""
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.action.minutes_pipeline.data_mapper import MinuteFields

logger = logging.getLogger(__name__)

_TEMPLATE_DIR  = Path("storage/templates")
_TEMPLATE_PATH = _TEMPLATE_DIR / "minutes_template.pdf"
_FONT_DIR      = Path("storage/fonts")

_SYSTEM_FONT_CANDIDATES = [
    "/Library/Fonts/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
]

# ── A4 / 레이아웃 상수 (fallback_renderer 와 동일 비율) ─────────────────
_W, _H = 595.28, 841.89
_M     = 40.0            # 여백
_LW    = 56.0            # 레이블 열 너비
_CW    = _W - 2 * _M     # 콘텐츠 너비 = 515.28

# 메타 테이블 열 너비 (fallback_renderer mc 와 동일)
_MC_WIDTHS = [56.0, 145.0, 32.0, 75.0, 38.0, _CW - 346.0]   # sum=515.28
_MC_X = [_M + sum(_MC_WIDTHS[:i]) for i in range(len(_MC_WIDTHS) + 1)]
# _MC_X: [40, 96, 241, 273, 348, 386, 555.28]

# ── 섹션 Y 좌표 ─────────────────────────────────────────────────────────
_TITLE_Y0  = 40.0
_TITLE_Y1  = 70.0

_META_ROW_H = 18.0
_META_R1_Y0 = 80.0
_META_R1_Y1 = _META_R1_Y0 + _META_ROW_H   # 98
_META_R2_Y0 = _META_R1_Y1                  # 98
_META_R2_Y1 = _META_R2_Y0 + _META_ROW_H   # 116

_AGENDA_Y0  = _META_R2_Y1 + 6.0            # 122
_AGENDA_H_H = 16.0
_AGENDA_C_H = 52.0
_AGENDA_C_Y0 = _AGENDA_Y0 + _AGENDA_H_H   # 138
_AGENDA_Y1   = _AGENDA_C_Y0 + _AGENDA_C_H # 190

_DISC_Y0   = _AGENDA_Y1 + 6.0             # 196
_DISC_H_H  = 16.0
_DISC_C_H  = 240.0
_DISC_C_Y0 = _DISC_Y0 + _DISC_H_H        # 212
_DISC_Y1   = _DISC_C_Y0 + _DISC_C_H      # 452

_DEC_Y0    = _DISC_Y1 + 6.0              # 458
_DEC_H_H   = 16.0
_DEC_ROW_H = 17.0
_DEC_ROWS  = 4
_DEC_C_Y0  = _DEC_Y0 + _DEC_H_H         # 474
_DEC_Y1    = _DEC_C_Y0 + _DEC_ROWS * _DEC_ROW_H  # 542

_NOTES_Y0  = _DEC_Y1 + 6.0              # 548
_NOTES_H_H = 16.0
_NOTES_C_H = 90.0
_NOTES_C_Y0 = _NOTES_Y0 + _NOTES_H_H   # 564
_NOTES_Y1   = _NOTES_C_Y0 + _NOTES_C_H # 654

# 회의내용/결정사항 내용 열 너비 (fallback_renderer 와 동일 비율)
_RW      = _CW - _LW                            # 459.28
_DISC_W  = round(_RW * 0.765)                   # 351
_DEC_W   = round(_RW * 0.695)                   # 319

# ── 필드별 텍스트 삽입 영역 (x0, y0, x1, y1) ────────────────────────────
# 넘침 처리: 클리핑 (insert_textbox 기본 동작)
FIELD_RECTS: dict[str, tuple[float, float, float, float]] = {
    "datetime":           (_MC_X[1]+1, _META_R1_Y0+2, _MC_X[2]-1, _META_R1_Y1-2),
    "dept":               (_MC_X[3]+1, _META_R1_Y0+2, _MC_X[4]-1, _META_R1_Y1-2),
    "author":             (_MC_X[5]+1, _META_R1_Y0+2, _MC_X[6]-1, _META_R1_Y1-2),
    "attendees":          (_MC_X[1]+1, _META_R2_Y0+2, _MC_X[6]-1, _META_R2_Y1-2),
    "agenda_items":       (_MC_X[1]+1, _AGENDA_C_Y0+2, _MC_X[6]-1, _AGENDA_Y1-2),
    "discussion_content": (_MC_X[1]+1, _DISC_C_Y0+2,  _M+_LW+_DISC_W-1, _DISC_Y1-2),
    "special_notes":      (_MC_X[1]+1, _NOTES_C_Y0+2, _MC_X[6]-1, _NOTES_Y1-2),
}

# 결정사항 행별 rect
DECISION_ROW_RECTS: list[tuple[float, float, float, float]] = [
    (
        _MC_X[1]+1,
        _DEC_C_Y0 + i * _DEC_ROW_H + 1,
        _M + _LW + _DEC_W - 1,
        _DEC_C_Y0 + (i + 1) * _DEC_ROW_H - 1,
    )
    for i in range(_DEC_ROWS)
]

_FONT_NAME_KEY = "nanum"   # insert_textbox 내부 등록 키


def _get_font_path() -> str | None:
    """사용 가능한 한글 폰트 경로를 반환한다. 없으면 None."""
    p = _FONT_DIR / "NanumGothic.ttf"
    if p.exists() and p.stat().st_size > 10_000:
        return str(p)

    try:
        from app.domains.action.minutes_pipeline.pdf_renderer import prefetch_fonts
        if prefetch_fonts() and p.exists() and p.stat().st_size > 10_000:
            return str(p)
    except Exception:
        pass

    for sp in _SYSTEM_FONT_CANDIDATES:
        if Path(sp).exists():
            logger.info("시스템 폰트 사용: %s", sp)
            return sp

    logger.warning("한글 폰트 없음 — 기본 폰트 사용 (한글 깨짐 가능)")
    return None


def _tb(page, rect: tuple, text: str, fontsize: float, font_path: str | None,
        align: int = 0) -> None:
    """rect 내에 텍스트를 삽입 (클리핑). 빈 텍스트는 건너뜀."""
    if not text or not str(text).strip():
        return
    import fitz
    r = fitz.Rect(*rect)
    kwargs: dict = {"fontsize": fontsize, "color": (0, 0, 0), "align": align}
    if font_path:
        kwargs["fontname"] = _FONT_NAME_KEY
        kwargs["fontfile"] = font_path
    else:
        kwargs["fontname"] = "helv"
    overflow = page.insert_textbox(r, str(text), **kwargs)
    if isinstance(overflow, (int, float)) and overflow < -0.1:
        logger.debug("텍스트 클리핑 (rect=%s, overflow=%.1f)", rect, overflow)


def _draw_template(page, font_path: str | None) -> None:
    """빈 회의록 양식(레이블 + 박스)을 페이지에 그린다."""
    import fitz

    BLACK = (0, 0, 0)
    GRAY  = (0.75, 0.75, 0.75)

    def box(x0, y0, x1, y1, w=0.5, c=BLACK):
        page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=c, width=w, fill=None)

    def hline(x0, y, x1, w=0.4, c=GRAY):
        page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y), color=c, width=w)

    def vline(x, y0, y1, w=0.4, c=GRAY):
        page.draw_line(fitz.Point(x, y0), fitz.Point(x, y1), color=c, width=w)

    def lbl(x0, y0, x1, y1, text, size=7.5):
        _tb(page, (x0, y0, x1, y1), text, size, font_path)

    # ── 제목 ────────────────────────────────────────────────────────
    _tb(page, (_M, _TITLE_Y0, _W - _M, _TITLE_Y1), "회의록",
        fontsize=22.0, font_path=font_path, align=1)

    # ── 메타 테이블 ──────────────────────────────────────────────────
    box(_M, _META_R1_Y0, _MC_X[6], _META_R2_Y1, w=0.75)
    hline(_M, _META_R1_Y1, _MC_X[6])
    for xi in _MC_X[1:6]:
        vline(xi, _META_R1_Y0, _META_R1_Y1)
    vline(_MC_X[1], _META_R2_Y0, _META_R2_Y1)

    lbl(_M+2,       _META_R1_Y0+2, _MC_X[1]-2,  _META_R1_Y1-2, "회의일시")
    lbl(_MC_X[2]+2, _META_R1_Y0+2, _MC_X[3]-2,  _META_R1_Y1-2, "부서")
    lbl(_MC_X[4]+2, _META_R1_Y0+2, _MC_X[5]-2,  _META_R1_Y1-2, "작성자")
    lbl(_M+2,       _META_R2_Y0+2, _MC_X[1]-2,  _META_R2_Y1-2, "참석자")

    # ── 회의안건 ─────────────────────────────────────────────────────
    box(_M, _AGENDA_Y0, _MC_X[6], _AGENDA_Y1, w=0.75)
    hline(_M, _AGENDA_C_Y0, _MC_X[6])
    vline(_MC_X[1], _AGENDA_Y0, _AGENDA_Y1)
    lbl(_M+2, _AGENDA_Y0+2, _MC_X[1]-2, _AGENDA_C_Y0-2, "회의안건", 8.0)

    # ── 회의내용 ─────────────────────────────────────────────────────
    _disc_bigo_x = _M + _LW + _DISC_W
    box(_M, _DISC_Y0, _MC_X[6], _DISC_Y1, w=0.75)
    hline(_M, _DISC_C_Y0, _MC_X[6])
    vline(_MC_X[1], _DISC_Y0, _DISC_Y1)
    vline(_disc_bigo_x, _DISC_Y0, _DISC_Y1)
    lbl(_M+2,          _DISC_Y0+2, _MC_X[1]-2,      _DISC_C_Y0-2, "회의내용", 8.0)
    lbl(_MC_X[1]+2,    _DISC_Y0+2, _disc_bigo_x-2,  _DISC_C_Y0-2, "내용")
    lbl(_disc_bigo_x+2, _DISC_Y0+2, _MC_X[6]-2,     _DISC_C_Y0-2, "비고")

    # ── 결정사항 ─────────────────────────────────────────────────────
    _dec_sched_x = _M + _LW + _DEC_W
    box(_M, _DEC_Y0, _MC_X[6], _DEC_Y1, w=0.75)
    hline(_M, _DEC_C_Y0, _MC_X[6])
    vline(_MC_X[1], _DEC_Y0, _DEC_Y1)
    vline(_dec_sched_x, _DEC_Y0, _DEC_Y1)
    for i in range(1, _DEC_ROWS):
        hline(_MC_X[1], _DEC_C_Y0 + i * _DEC_ROW_H, _MC_X[6])
    lbl(_M+2,            _DEC_Y0+2, _MC_X[1]-2,       _DEC_C_Y0-2, "결정사항", 8.0)
    lbl(_MC_X[1]+2,      _DEC_Y0+2, _dec_sched_x-2,   _DEC_C_Y0-2, "내용")
    lbl(_dec_sched_x+2,  _DEC_Y0+2, _MC_X[6]-2,       _DEC_C_Y0-2, "진행일정")

    # ── 특이사항 ─────────────────────────────────────────────────────
    box(_M, _NOTES_Y0, _MC_X[6], _NOTES_Y1, w=0.75)
    hline(_M, _NOTES_C_Y0, _MC_X[6])
    vline(_MC_X[1], _NOTES_Y0, _NOTES_Y1)
    lbl(_M+2, _NOTES_Y0+2, _MC_X[1]-2, _NOTES_C_Y0-2, "특이사항", 8.0)


def _ensure_template() -> Path:
    """템플릿 PDF를 반환. 없으면 새로 생성한다."""
    if _TEMPLATE_PATH.exists() and _TEMPLATE_PATH.stat().st_size > 500:
        return _TEMPLATE_PATH

    _TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    import fitz
    fp = _get_font_path()
    doc = fitz.open()
    page = doc.new_page(width=_W, height=_H)
    _draw_template(page, fp)
    _TEMPLATE_PATH.write_bytes(doc.tobytes(garbage=4, deflate=True))
    doc.close()
    logger.info("회의록 템플릿 생성: %s", _TEMPLATE_PATH)
    return _TEMPLATE_PATH


def render(fields: "MinuteFields") -> bytes:
    """
    오버레이 방식으로 회의록 PDF를 생성한다.
    예외 발생 시 그대로 raise — 호출자(router)가 HTML 렌더러로 폴백한다.
    """
    import fitz

    template_path = _ensure_template()
    font_path = _get_font_path()

    doc = fitz.open(str(template_path))
    page = doc[0]

    def put(key: str, text: str, fontsize: float = 8.0) -> None:
        _tb(page, FIELD_RECTS[key], text, fontsize, font_path)

    put("datetime",           fields.datetime)
    put("dept",               fields.dept)
    put("author",             fields.author)
    put("attendees",          fields.attendees)
    put("agenda_items",       fields.agenda_items)
    put("discussion_content", fields.discussion_content)
    put("special_notes",      fields.special_notes)

    # 결정사항: 행별 처리
    dec_lines = [r for r in fields.decision_rows if r.strip()]
    for i, row_rect in enumerate(DECISION_ROW_RECTS):
        if i >= len(dec_lines):
            break
        _tb(page, row_rect, dec_lines[i], 8.0, font_path)

    pdf_bytes = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return pdf_bytes
