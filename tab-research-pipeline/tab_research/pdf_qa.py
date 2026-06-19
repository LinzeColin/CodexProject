from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List


DEFAULT_REQUIRED_TERMS = [
    "盘口下注研究分析报告",
    "公开脱敏研究副本",
    "可视化仪表盘摘要",
    "板块自动化就绪度",
    "新旧报告对比",
    "盘口推荐分布",
    "跨板块新增金额分配",
    "比赛盘口价值排序",
    "概率-赔率边际",
    "开源模型分歧",
    "模型共识强度",
    "开源模型采用覆盖",
    "模型能力覆盖矩阵",
    "主执行下注建议",
    "动态仓位买入",
    "模型交叉验证",
    "模型交叉验证审计",
    "Top分歧比赛",
    "Elo/Dixon-Coles",
    "Hicruben",
    "goalmodel",
    "RyanSCodes",
]


def audit_pdf_report(
    pdf_path: Path,
    required_terms: Iterable[str] | None = None,
    min_pages: int = 3,
    min_text_chars: int = 2500,
    min_size_bytes: int = 50_000,
    visual_smoke: bool = False,
    require_visual_smoke: bool = False,
    visual_sample_pages: int = 4,
    min_visible_pixel_ratio: float = 0.001,
) -> dict:
    pdf_path = Path(pdf_path)
    terms = list(DEFAULT_REQUIRED_TERMS if required_terms is None else required_terms)
    result = {
        "schema_version": 2,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pdf_file": pdf_path.name,
        "pdf_qa_ready": False,
        "page_count": 0,
        "text_char_count": 0,
        "size_bytes": 0,
        "min_pages": min_pages,
        "min_text_chars": min_text_chars,
        "min_size_bytes": min_size_bytes,
        "required_terms": terms,
        "missing_terms": [],
        "blocking_reasons": [],
        "warnings": [],
        "visual_smoke": {
            "enabled": bool(visual_smoke),
            "required": bool(require_visual_smoke),
            "renderer": "",
            "available": False,
            "ready": False,
            "sampled_pages": [],
            "rendered_page_count": 0,
            "visible_page_count": 0,
            "min_visible_pixel_ratio": min_visible_pixel_ratio,
            "blocking_reasons": [],
        },
    }
    if not pdf_path.exists():
        result["blocking_reasons"].append("PDF file is missing")
        result["missing_terms"] = terms
        if require_visual_smoke:
            result["visual_smoke"]["blocking_reasons"].append("PDF file is missing")
        return result
    result["size_bytes"] = pdf_path.stat().st_size
    try:
        text, page_count = extract_pdf_text(pdf_path)
    except Exception as exc:
        result["blocking_reasons"].append(f"PDF text extraction failed: {type(exc).__name__}")
        result["missing_terms"] = terms
        return result
    result["page_count"] = page_count
    result["text_char_count"] = len(text)
    result["missing_terms"] = [term for term in terms if term not in text]
    if page_count < min_pages:
        result["blocking_reasons"].append(f"PDF page_count {page_count} below minimum {min_pages}")
    if len(text) < min_text_chars:
        result["blocking_reasons"].append(f"PDF text length {len(text)} below minimum {min_text_chars}")
    if result["size_bytes"] < min_size_bytes:
        result["blocking_reasons"].append(f"PDF size {result['size_bytes']} below minimum {min_size_bytes}")
    if result["missing_terms"]:
        result["blocking_reasons"].append("PDF missing required terms: " + ", ".join(result["missing_terms"]))
    if visual_smoke or require_visual_smoke:
        visual = render_pdf_visual_smoke(
            pdf_path,
            page_count=page_count,
            sample_pages=visual_sample_pages,
            min_visible_pixel_ratio=min_visible_pixel_ratio,
        )
        visual["required"] = bool(require_visual_smoke)
        result["visual_smoke"] = visual
        if not visual["available"]:
            message = "; ".join(visual.get("blocking_reasons", [])) or "PDF visual smoke renderer is unavailable"
            if require_visual_smoke:
                result["blocking_reasons"].append(f"PDF visual smoke unavailable: {message}")
            else:
                result["warnings"].append(f"PDF visual smoke unavailable: {message}")
        elif not visual["ready"]:
            reasons = "; ".join(visual.get("blocking_reasons", [])) or "PDF visual smoke failed"
            result["blocking_reasons"].append(f"PDF visual smoke failed: {reasons}")
    result["pdf_qa_ready"] = not result["blocking_reasons"]
    return result


def extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages: List[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages), len(reader.pages)


def render_pdf_visual_smoke(
    pdf_path: Path,
    page_count: int,
    sample_pages: int = 4,
    min_visible_pixel_ratio: float = 0.001,
    render_scale: float = 0.5,
) -> dict:
    result = {
        "enabled": True,
        "required": False,
        "renderer": "pymupdf",
        "available": False,
        "ready": False,
        "sampled_pages": [],
        "rendered_page_count": 0,
        "visible_page_count": 0,
        "min_visible_pixel_ratio": min_visible_pixel_ratio,
        "blocking_reasons": [],
    }
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised only on hosts missing PyMuPDF.
        return render_pdf_content_stream_smoke(
            pdf_path,
            page_count=page_count,
            sample_pages=sample_pages,
            min_visible_pixel_ratio=min_visible_pixel_ratio,
            fallback_reason=f"PyMuPDF import failed: {type(exc).__name__}",
        )

    if page_count <= 0:
        result["available"] = True
        result["blocking_reasons"].append("PDF has no renderable pages")
        return result

    page_indexes = visual_sample_page_indexes(page_count, sample_pages)
    result["available"] = True
    try:
        with fitz.open(str(pdf_path)) as document:
            for page_index in page_indexes:
                page = document.load_page(page_index)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), alpha=False)
                ratio = visible_pixel_ratio(pixmap.samples, pixmap.width, pixmap.height)
                visible = ratio >= min_visible_pixel_ratio
                result["sampled_pages"].append(
                    {
                        "page": page_index + 1,
                        "width": pixmap.width,
                        "height": pixmap.height,
                        "visible_pixel_ratio": round(ratio, 6),
                        "visible": visible,
                    }
                )
                result["rendered_page_count"] += 1
                if visible:
                    result["visible_page_count"] += 1
    except Exception as exc:
        result["blocking_reasons"].append(f"PDF page render failed: {type(exc).__name__}")
        return result

    blank_pages = [
        str(page["page"])
        for page in result["sampled_pages"]
        if float(page.get("visible_pixel_ratio", 0.0)) < min_visible_pixel_ratio
    ]
    if blank_pages:
        result["blocking_reasons"].append(
            "rendered sample pages below visible pixel threshold: " + ", ".join(blank_pages)
        )
    result["ready"] = result["available"] and not result["blocking_reasons"]
    return result


def render_pdf_content_stream_smoke(
    pdf_path: Path,
    page_count: int,
    sample_pages: int = 4,
    min_visible_pixel_ratio: float = 0.001,
    *,
    fallback_reason: str = "",
) -> dict:
    result = {
        "enabled": True,
        "required": False,
        "renderer": "pdf-content-stream",
        "available": False,
        "ready": False,
        "sampled_pages": [],
        "rendered_page_count": 0,
        "visible_page_count": 0,
        "min_visible_pixel_ratio": min_visible_pixel_ratio,
        "blocking_reasons": [],
        "fallback_reason": fallback_reason,
    }
    if page_count <= 0:
        result["available"] = True
        result["blocking_reasons"].append("PDF has no renderable pages")
        return result
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        page_indexes = visual_sample_page_indexes(page_count, sample_pages)
        result["available"] = True
        for page_index in page_indexes:
            page = reader.pages[page_index]
            content = page.get_contents()
            content_bytes = content.get_data() if content is not None else b""
            visible = pdf_content_stream_has_visible_marks(content_bytes)
            ratio = 1.0 if visible else 0.0
            result["sampled_pages"].append(
                {
                    "page": page_index + 1,
                    "width": int(float(page.mediabox.width or 0)),
                    "height": int(float(page.mediabox.height or 0)),
                    "visible_pixel_ratio": ratio,
                    "visible": visible,
                    "smoke_method": "non-white paint operators",
                }
            )
            result["rendered_page_count"] += 1
            if visible:
                result["visible_page_count"] += 1
    except Exception as exc:
        result["blocking_reasons"].append(f"PDF content stream smoke failed: {type(exc).__name__}")
        return result

    blank_pages = [
        str(page["page"])
        for page in result["sampled_pages"]
        if float(page.get("visible_pixel_ratio", 0.0)) < min_visible_pixel_ratio
    ]
    if blank_pages:
        result["blocking_reasons"].append(
            "sample pages have no non-white visible drawing operators: " + ", ".join(blank_pages)
        )
    result["ready"] = result["available"] and not result["blocking_reasons"]
    return result


PDF_CONTENT_TOKEN_RE = re.compile(
    r"\((?:\\.|[^\\)])*\)|\[(?:\\.|[^\]])*\]|/[^\s\[\]()<>{}%]+|[-+]?(?:\d+\.\d+|\d+|\.\d+)|[A-Za-z*'\"]+"
)
PDF_PAINT_OPERATORS = {"f", "F", "f*", "B", "B*", "b", "b*"}
PDF_STROKE_OPERATORS = {"S", "s", "B", "B*", "b", "b*"}
PDF_TEXT_OPERATORS = {"Tj", "TJ", "'", '"'}


def pdf_content_stream_has_visible_marks(content_bytes: bytes, white_threshold: float = 0.96) -> bool:
    text = content_bytes.decode("latin1", errors="ignore")
    tokens = PDF_CONTENT_TOKEN_RE.findall(text)
    operands: list[str] = []
    fill_visible = True
    stroke_visible = True
    for token in tokens:
        if is_pdf_operator(token):
            if token in {"rg", "g", "k"}:
                fill_visible = pdf_color_operands_visible(token, operands, white_threshold)
            elif token in {"RG", "G", "K"}:
                stroke_visible = pdf_color_operands_visible(token, operands, white_threshold)
            elif token in PDF_TEXT_OPERATORS and fill_visible:
                return True
            elif token in PDF_PAINT_OPERATORS and fill_visible:
                return True
            elif token in PDF_STROKE_OPERATORS and stroke_visible:
                return True
            elif token == "Do":
                return True
            operands = []
        else:
            operands.append(token)
    return False


def is_pdf_operator(token: str) -> bool:
    if not token or token.startswith("(") or token.startswith("[") or token.startswith("/"):
        return False
    return not is_number_token(token)


def pdf_color_operands_visible(operator: str, operands: list[str], white_threshold: float) -> bool:
    values = [float(value) for value in operands if is_number_token(value)]
    if operator in {"g", "G"}:
        return not values or values[-1] < white_threshold
    if operator in {"rg", "RG"}:
        rgb = values[-3:] if len(values) >= 3 else []
        return not rgb or any(value < white_threshold for value in rgb)
    if operator in {"k", "K"}:
        cmyk = values[-4:] if len(values) >= 4 else []
        return not cmyk or any(value > (1 - white_threshold) for value in cmyk)
    return True


def is_number_token(token: str) -> bool:
    try:
        float(token)
        return True
    except (TypeError, ValueError):
        return False


def visual_sample_page_indexes(page_count: int, sample_pages: int) -> List[int]:
    if page_count <= 0 or sample_pages <= 0:
        return []
    candidates = [0, 1, page_count // 2, page_count - 1]
    indexes: List[int] = []
    for index in candidates:
        if 0 <= index < page_count and index not in indexes:
            indexes.append(index)
        if len(indexes) >= sample_pages:
            return indexes
    for index in range(page_count):
        if index not in indexes:
            indexes.append(index)
        if len(indexes) >= sample_pages:
            break
    return indexes


def visible_pixel_ratio(samples: bytes, width: int, height: int, white_threshold: int = 245) -> float:
    total_pixels = max(width * height, 1)
    visible_pixels = 0
    for offset in range(0, len(samples), 3):
        red = samples[offset]
        green = samples[offset + 1]
        blue = samples[offset + 2]
        if red < white_threshold or green < white_threshold or blue < white_threshold:
            visible_pixels += 1
    return visible_pixels / total_pixels
