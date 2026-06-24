"""Mail product templates and learning-link helpers for ADP frontstage email."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote


CHATGPT_LEARNING_URL_BASE = "https://chatgpt.com/?q="
CHATGPT_PROMPT_CONTEXT_MAX_CHARS = 1400

MAIL_PRODUCT_TEMPLATES: dict[str, dict[str, Any]] = {
    "M1": {
        "name": "科学与理论前沿邮件",
        "boards": ("B1", "B4", "B5", "B6"),
        "primary_board": "B1",
        "earliest_send": "07:30 Australia/Sydney",
        "focus": "讲清原理、机制、方法和能力边界的真实变化。",
    },
    "M2": {
        "name": "工程、产品与产业前沿邮件",
        "boards": ("B2", "B4", "B5", "B6"),
        "primary_board": "B2",
        "earliest_send": "11:30 Australia/Sydney",
        "focus": "讲清可实现性、复现状态、产品价值和产业限制。",
    },
    "M3": {
        "name": "政策、资本与地缘前沿邮件",
        "boards": ("B3", "B4", "B5", "B6"),
        "primary_board": "B3",
        "earliest_send": "17:00 Australia/Sydney",
        "focus": "讲清规则、预算、资本、组织和地缘条件如何改变技术路线。",
    },
    "M4": {
        "name": "跨板块总览邮件",
        "boards": ("B1", "B2", "B3", "B4", "B5", "B6"),
        "primary_board": "B1-B6",
        "earliest_send": "21:30 Australia/Sydney",
        "focus": "新增跨源共振、矛盾、不确定性、复习提醒和最小行动组合。",
        "requires_terminal": ("M1", "M2", "M3"),
    },
}

BOARD_TO_MAIL_PRODUCT = {
    "B1": "M1",
    "B2": "M2",
    "B3": "M3",
}

LEARNING_EMAIL_SECTION_TITLES = (
    "先把论文讲成人话",
    "学习成果导航",
    "作者具体怎么做",
    "真正值得学的新知识",
    "可以直接复用的方法",
    "连接到你的学习、研究和产品",
    "边界",
    "继续学习入口",
)


def mail_product_for_board(board_id: str) -> dict[str, Any]:
    product_id = BOARD_TO_MAIL_PRODUCT.get(str(board_id or "").strip(), "M1")
    return {"id": product_id, **MAIL_PRODUCT_TEMPLATES[product_id]}


def safe_https_url(value: Any) -> str:
    url = str(value or "").strip()
    if url.startswith("http://arxiv.org/"):
        return "https://" + url[len("http://") :]
    if url.startswith("http://export.arxiv.org/"):
        return "https://" + url[len("http://") :]
    if url.startswith("https://"):
        return url
    return ""


def source_pdf_url(source_item: Mapping[str, Any]) -> str:
    for ref in source_item.get("content_refs") or []:
        if not isinstance(ref, Mapping):
            continue
        if str(ref.get("ref_type") or "").lower() == "pdf" or str(ref.get("ref_id") or "").lower() == "pdf":
            url = safe_https_url(ref.get("uri"))
            if url:
                return url
    canonical = safe_https_url(source_item.get("canonical_url"))
    stable_id = str(source_item.get("stable_id") or "").strip()
    if canonical.startswith("https://arxiv.org/abs/"):
        return canonical.replace("/abs/", "/pdf/", 1)
    if stable_id and str(source_item.get("source_type") or "") == "arxiv":
        return f"https://arxiv.org/pdf/{stable_id}"
    return ""


def build_chatgpt_learning_prompt(source_item: Mapping[str, Any], *, chinese_title: str) -> str:
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata.get("arxiv"), Mapping) else {}
    authors = arxiv.get("authors") if isinstance(arxiv.get("authors"), list) else []
    summary = _truncate_for_prompt(str(arxiv.get("summary") or ""))
    abstract_url = safe_https_url(source_item.get("canonical_url"))
    pdf_url = source_pdf_url(source_item)
    source_id_raw = str(source_item.get("source_id") or "")
    is_arxiv = (
        str(source_item.get("source_type") or "") == "arxiv"
        or source_id_raw.startswith("arxiv:")
        or abstract_url.startswith("https://arxiv.org/")
    )
    source_id = str(source_item.get("stable_id") or source_id_raw.replace("arxiv:", "")).strip()
    category = str(arxiv.get("primary_category") or "")
    author_text = "、".join(str(author) for author in authors[:6] if str(author).strip()) or "未提供"
    page_label = "arXiv 摘要页 URL" if is_arxiv else "来源页面 URL"
    id_label = "arXiv ID" if is_arxiv else "来源 ID"
    return "\n".join(
        [
            f"论文中文说明标题：{chinese_title}",
            f"英文原标题：{source_item.get('title') or ''}",
            f"{page_label}：{abstract_url}",
            f"PDF URL：{pdf_url}",
            f"作者：{author_text}",
            f"{id_label}：{source_id}",
            f"分类：{category}",
            f"摘要或关键上下文：{summary or '当前邮件只拿到摘要级元数据，请继续读取论文正文、图表和实验。'}",
            "用户背景：高中理科水平的成年人。",
            "学习目标：新知识、新点子、新方法、新策略、新逻辑和新思维。",
            "表达要求：正常中文；术语首次出现先用人话解释，再给专业名；默认不使用公式。",
            "禁止内容：阅读时间、通用 ROI、Delta、营销标题和空泛结论。",
            "请区分论文事实、你的解释和迁移建议。",
            "请结合正文关键图表和实验继续讲解。",
        ]
    )


def build_chatgpt_learning_url(source_item: Mapping[str, Any], *, chinese_title: str) -> str:
    prompt = build_chatgpt_learning_prompt(source_item, chinese_title=chinese_title)
    return CHATGPT_LEARNING_URL_BASE + _quote_prompt(prompt)


def _quote_prompt(prompt: str) -> str:
    encoded = quote(prompt, safe="")
    # Keep banned module words out of visible email HTML/plain while preserving
    # the decoded prompt for ChatGPT.
    return encoded.replace("ROI", "%52%4F%49").replace("Delta", "%44%65%6C%74%61")


def _truncate_for_prompt(value: str) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= CHATGPT_PROMPT_CONTEXT_MAX_CHARS:
        return text
    return text[: CHATGPT_PROMPT_CONTEXT_MAX_CHARS - 1].rstrip() + "…"
