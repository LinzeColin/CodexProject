"""Email Learning V1 content object and renderer.

This module is private to arxiv-daily-push email rendering. It does not define
or mutate public cross-module schemas.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from html import escape
from typing import Any
from urllib.parse import quote


EMAIL_LEARNING_V1_CONTRACT_ID = "EMAIL_LEARNING_V1"
EMAIL_LEARNING_V1_TEMPLATE_VERSION = "1.0.0"
EMAIL_LEARNING_V1_PROMPT_VERSION = "email-learning-v1-chatgpt-prompt-1.0.0"
EMAIL_LEARNING_V1_MODEL_VERSION = "deterministic-email-learning-v1.0.0"
EMAIL_LEARNING_V1_TEMPLATE_MARKER = "data-template=\"EMAIL_LEARNING_V1\""

M1_M4_MAIL_PRODUCTS: dict[str, str] = {
    "M1": "科学与理论前沿邮件",
    "M2": "工程、产品与产业前沿邮件",
    "M3": "政策、资本与地缘前沿邮件",
    "M4": "跨板块总览邮件",
}

FORBIDDEN_VISIBLE_MARKERS: tuple[str, ...] = (
    "阅读时间",
    "预计：",
    "30秒",
    "30 秒",
    "一分钟",
    "1分钟",
    "扫读",
    "跳过",
    "Frontier Delta",
    "Delta",
    "ROI",
    "roi_total_score",
    "ROI score",
    "ROI评分",
    "ROI 分数",
    "Action ladder",
    "问题卡",
    "Release 资料包",
    "GitHub Release",
    "12秒视频",
    "12-second video",
    "delivery policy",
    "后台",
    "class=\"score\"",
)

VISIBLE_TEXT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("roi_total_score", "内部排序依据"),
    ("ROI score", "价值评分"),
    ("ROI评分", "价值评分"),
    ("ROI 分数", "价值评分"),
    ("ROI", "价值回报"),
    ("Frontier Delta", "前沿增量"),
    ("Delta", "增量"),
    ("Release 资料包", "归档资料"),
    ("GitHub Release", "归档记录"),
    ("12秒视频", "短视频材料"),
    ("12-second video", "short video material"),
    ("delivery policy", "投递策略"),
    ("后台", "系统记录"),
    ("扫读", "快速了解"),
    ("跳过", "暂不继续"),
    ("阅读时间", "学习投入"),
)


def render_email_learning_v1(
    *,
    mail_product_id: str,
    source_item: Mapping[str, Any],
    lesson: Mapping[str, Any] | None,
    claims: Sequence[Mapping[str, Any]] | None = None,
    generated_at: str,
    date: str,
    run_id: str,
    report_id: str = "",
    candidate_queue_summary: str = "",
    queue_items: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build, render, and validate one Email Learning V1 message."""

    content = build_email_learning_content_v1(
        mail_product_id=mail_product_id,
        source_item=source_item,
        lesson=lesson or {},
        claims=claims or [],
        generated_at=generated_at,
        date=date,
        run_id=run_id,
        report_id=report_id,
        candidate_queue_summary=candidate_queue_summary,
        queue_items=queue_items or [],
    )
    rendered = {
        "contract_id": EMAIL_LEARNING_V1_CONTRACT_ID,
        "template_version": EMAIL_LEARNING_V1_TEMPLATE_VERSION,
        "mail_product_id": mail_product_id,
        "subject": _subject(content, date=date),
        "plain": _render_plain(content),
        "html": _render_html(content),
        "content": content,
    }
    errors = validate_email_learning_v1_render(rendered)
    if errors:
        raise ValueError("; ".join(errors))
    return rendered


def build_email_learning_content_v1(
    *,
    mail_product_id: str,
    source_item: Mapping[str, Any],
    lesson: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    generated_at: str,
    date: str,
    run_id: str,
    report_id: str = "",
    candidate_queue_summary: str = "",
    queue_items: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Create the structured V1 content object before HTML rendering."""

    mail_product_name = _mail_product_name(mail_product_id)
    source_meta = _source_meta(source_item)
    if not source_meta["source_url"] or not source_meta["pdf_url"]:
        raise ValueError("EMAIL_LEARNING_V1 requires source and reading links")
    if not _is_https(source_meta["source_url"]) or not _is_https(source_meta["pdf_url"]):
        raise ValueError("EMAIL_LEARNING_V1 links must use https")

    frontstage = lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {}
    summary = source_meta["summary"]
    title = source_meta["title"]
    claim_texts = [_clean_text(str(claim.get("statement") or "")) for claim in claims if isinstance(claim, Mapping)]
    core_context = _first_non_empty(summary, "；".join(claim_texts), title)
    terms = _term_explanations(f"{title} {summary}")
    method_flow = _method_flow(frontstage, source_meta, core_context)
    learning_outcomes = _learning_outcomes(source_meta, method_flow)
    knowledge_units = _knowledge_units(source_meta, frontstage, method_flow, claim_texts)
    reusable_methods = _reusable_methods(source_meta, method_flow)
    practical_transfer = _practical_transfer(source_meta, mail_product_id)
    plain_explanation = _plain_explanation(source_meta, method_flow, claim_texts)
    limits = _limits(frontstage, source_meta)
    prompt = _chatgpt_prompt(
        source_meta=source_meta,
        title_zh_plain=_plain_title(source_meta),
        plain_explanation=plain_explanation,
        learning_outcomes=learning_outcomes,
    )
    links = {
        "arxiv_link": source_meta["source_url"],
        "pdf_link": source_meta["pdf_url"],
        "chatgpt_new_chat": "https://chatgpt.com/?q=" + quote(prompt, safe=""),
        "copy_prompt_fallback": prompt,
    }
    return {
        "version": EMAIL_LEARNING_V1_TEMPLATE_VERSION,
        "contract_id": EMAIL_LEARNING_V1_CONTRACT_ID,
        "mail_product_id": mail_product_id,
        "mail_product_name": mail_product_name,
        "title_zh_plain": _plain_title(source_meta),
        "subtitle_plain": _subtitle(source_meta, mail_product_name),
        "source_meta": source_meta,
        "plain_explanation": plain_explanation,
        "learning_outcomes": learning_outcomes,
        "method_flow": method_flow,
        "knowledge_units": knowledge_units,
        "reusable_methods": reusable_methods,
        "practical_transfer": practical_transfer,
        "limits": limits,
        "links": links,
        "term_explanations": terms,
        "candidate_queue_summary": _clean_text(candidate_queue_summary),
        "queue_items": [_queue_item(item) for item in queue_items[:3] if isinstance(item, Mapping)],
        "provenance": {
            "evidence_level": source_meta["evidence_level"],
            "source_family": source_meta["source_family"],
            "paper_id": source_meta["paper_id"],
            "source_url": source_meta["source_url"],
            "prompt_version": EMAIL_LEARNING_V1_PROMPT_VERSION,
            "model_version": EMAIL_LEARNING_V1_MODEL_VERSION,
            "contract_version": "ADP-PRODUCT-CONTRACT-V7.2",
            "run_id": run_id,
            "report_id": report_id,
            "generated_at": generated_at,
            "date": date,
        },
    }


def validate_email_learning_v1_render(rendered: Mapping[str, Any]) -> list[str]:
    """Validate rendered V1 email without trusting the caller."""

    errors: list[str] = []
    if rendered.get("contract_id") != EMAIL_LEARNING_V1_CONTRACT_ID:
        errors.append("email contract must be EMAIL_LEARNING_V1")
    mail_product_id = str(rendered.get("mail_product_id") or "")
    if mail_product_id not in M1_M4_MAIL_PRODUCTS:
        errors.append("mail_product_id must be one of M1, M2, M3, M4")
    content = rendered.get("content")
    if not isinstance(content, Mapping):
        errors.append("content object is required")
        return errors
    for field in (
        "title_zh_plain",
        "plain_explanation",
        "learning_outcomes",
        "method_flow",
        "knowledge_units",
        "reusable_methods",
        "practical_transfer",
        "limits",
        "links",
        "provenance",
    ):
        if not content.get(field):
            errors.append(f"content.{field} is required")
    if len(content.get("learning_outcomes") or []) < 4:
        errors.append("learning_outcomes must contain at least 4 items")
    if len(content.get("knowledge_units") or []) < 4:
        errors.append("knowledge_units must contain at least 4 items")
    if len(content.get("reusable_methods") or []) < 3:
        errors.append("reusable_methods must contain at least 3 items")
    links = content.get("links") if isinstance(content.get("links"), Mapping) else {}
    for key in ("arxiv_link", "pdf_link", "chatgpt_new_chat", "copy_prompt_fallback"):
        if not links.get(key):
            errors.append(f"links.{key} is required")
    if str(links.get("chatgpt_new_chat") or "").startswith("https://chatgpt.com/?q=") is False:
        errors.append("ChatGPT new-chat URL must use https://chatgpt.com/?q=")
    visible = _strip_href_values(str(rendered.get("plain") or "") + "\n" + str(rendered.get("html") or ""))
    for marker in FORBIDDEN_VISIBLE_MARKERS:
        if marker in visible:
            errors.append(f"visible email must not contain marker: {marker}")
    for marker in (
        "先把论文讲成人话",
        "学习成果导航",
        "方法流程",
        "真正的新知识",
        "可复用方法",
        "迁移到你的学习、工作、研究和产品",
        "边界",
        "继续深读",
    ):
        if marker not in visible:
            errors.append(f"visible email missing V1 section: {marker}")
    if EMAIL_LEARNING_V1_TEMPLATE_MARKER not in str(rendered.get("html") or ""):
        errors.append("html must include EMAIL_LEARNING_V1 template marker")
    return errors


def _subject(content: Mapping[str, Any], *, date: str) -> str:
    return " -- ".join(
        [
            _compact_date(date),
            "arXiv Daily Push",
            str(content["mail_product_id"]),
            _truncate_text(str(content["title_zh_plain"]), max_chars=64),
        ]
    )


def _render_plain(content: Mapping[str, Any]) -> str:
    explanation = content["plain_explanation"]
    links = content["links"]
    lines = [
        str(content["title_zh_plain"]),
        str(content["subtitle_plain"]),
        "",
        "【先把论文讲成人话】",
        f"现实问题：{explanation['real_world_problem']}",
        f"为什么难：{explanation['why_difficult']}",
        f"旧做法不够在哪里：{explanation['old_approach_gap']}",
        f"论文怎么做：{explanation['paper_approach']}",
        f"现在能得到什么：{explanation['reported_result']}",
        "",
        "【学习成果导航】",
        *[f"{index}. {item}" for index, item in enumerate(content["learning_outcomes"], start=1)],
        "",
        "【方法流程】",
        " -> ".join(str(item) for item in content["method_flow"]),
        "",
        "【真正的新知识】",
    ]
    for index, unit in enumerate(content["knowledge_units"], start=1):
        lines.extend(
            [
                f"{index}. {unit['title']}",
                f"是什么：{unit['plain_explanation']}",
                f"为什么重要：{unit['causal_logic']}",
                f"论文怎么体现：{unit['paper_specific_example']}",
                f"能迁移到哪里：{unit['transfer_example']}",
                f"容易错在哪里：{unit['common_mistake_or_limit']}",
            ]
        )
    if content.get("candidate_queue_summary"):
        lines.extend(["", "【候选队列摘要】", str(content["candidate_queue_summary"])])
        for item in content.get("queue_items") or []:
            if isinstance(item, Mapping):
                lines.append(f"- {item['title']}（{item['primary_category']}）：{item['reason']}")
    lines.extend(["", "【可复用方法】"])
    for method in content["reusable_methods"]:
        lines.extend(
            [
                f"- {method['name']}：{method['when_to_use']}",
                f"  怎么做：{method['how_to_use']}",
                f"  常见错误：{method['common_mistake']}",
            ]
        )
    lines.extend(["", "【迁移到你的学习、工作、研究和产品】"])
    for item in content["practical_transfer"]:
        lines.append(f"- {item['scenario']}：{item['shared_structure']}；可以这样用：{item['how_to_apply']}")
    lines.extend(
        [
            "",
            "【边界】",
            f"可以确定：{content['limits']['known']}",
            f"不能确定：{content['limits']['unknown']}",
            "",
            "【继续深读】",
            f"{content['source_meta']['source_link_label']}：{links['arxiv_link']}",
            f"{content['source_meta']['pdf_link_label']}：{links['pdf_link']}",
            f"ChatGPT 新对话：{links['chatgpt_new_chat']}",
            "",
            "【来源与生成记录】",
            f"原标题：{content['source_meta']['title']}",
            f"{content['source_meta']['id_label']}：{content['source_meta']['paper_id']}",
            f"分类：{content['source_meta']['primary_category']}",
            f"证据深度：{content['provenance']['evidence_level']}",
            f"模板：{EMAIL_LEARNING_V1_CONTRACT_ID} v{EMAIL_LEARNING_V1_TEMPLATE_VERSION}",
        ]
    )
    return "\n".join(str(line) for line in lines if line is not None)


def _render_html(content: Mapping[str, Any]) -> str:
    explanation = content["plain_explanation"]
    links = content["links"]
    outcomes = "".join(f"<li>{escape(str(item))}</li>" for item in content["learning_outcomes"])
    flow = "".join(f"<div class=\"step\">{escape(str(item))}</div>" for item in content["method_flow"])
    terms = "".join(
        f"<li><b>{escape(str(item['term']))}</b>：{escape(str(item['plain']))}</li>"
        for item in content["term_explanations"]
    )
    knowledge = "".join(_knowledge_unit_html(index, unit) for index, unit in enumerate(content["knowledge_units"], start=1))
    queue = _queue_html(content)
    methods = "".join(_method_html(method) for method in content["reusable_methods"])
    transfers = "".join(
        "<tr><td>"
        + escape(str(item["scenario"]))
        + "</td><td>"
        + escape(str(item["shared_structure"]))
        + "</td><td>"
        + escape(str(item["how_to_apply"]))
        + "</td></tr>"
        for item in content["practical_transfer"]
    )
    source_meta = content["source_meta"]
    prompt_preview = _truncate_text(str(links["copy_prompt_fallback"]), max_chars=420)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(str(content["title_zh_plain"]))}</title>
<style>
:root{{--ink:#172033;--text:#25324a;--muted:#68758a;--line:#e3e8ef;--soft:#f6f8fb;--soft-blue:#eef4ff;--blue:#275dcc;--blue-dark:#1c438f;--green:#1c7357;--paper:#ffffff}}
*{{box-sizing:border-box}}body{{margin:0;background:#f1f4f8;color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:17px;line-height:1.78;-webkit-font-smoothing:antialiased}}
.page{{width:min(780px,calc(100% - 28px));margin:22px auto;background:var(--paper);border:1px solid #e6ebf2;border-radius:14px;overflow:hidden;box-shadow:0 8px 30px rgba(30,52,88,.07)}}
header{{padding:30px 42px 26px;border-top:5px solid var(--blue);border-bottom:1px solid var(--line)}}.meta{{display:flex;flex-wrap:wrap;gap:7px 14px;color:var(--muted);font-size:13px;font-weight:650;margin-bottom:13px}}
h1{{margin:0;color:var(--ink);font-size:31px;line-height:1.34}}.subtitle{{margin:12px 0 0;color:#43516a;font-size:17px;line-height:1.7}}main{{padding:0 42px 42px}}section{{padding:29px 0;border-bottom:1px solid var(--line)}}section:last-child{{border-bottom:0;padding-bottom:6px}}h2{{margin:0 0 15px;color:var(--ink);font-size:23px;line-height:1.4}}h3{{margin:22px 0 8px;color:var(--ink);font-size:19px;line-height:1.45}}p{{margin:9px 0}}strong{{color:#18233a}}.lead{{font-size:18px;color:#26334a}}.problem{{margin:17px 0;padding:14px 17px;background:#fff8e8;border-left:4px solid #d9a22d;border-radius:0 9px 9px 0;color:#3d3526}}.learning-map{{margin-top:17px;padding:18px 20px 15px;background:var(--soft-blue);border:1px solid #dbe7ff;border-radius:11px}}.learning-map strong{{display:block;margin-bottom:8px;color:var(--blue-dark)}}.learning-map ol{{margin:0;padding-left:1.35em;display:grid;grid-template-columns:1fr 1fr;gap:5px 28px}}.flow{{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;align-items:stretch;margin:18px 0 20px}}.step{{position:relative;background:var(--soft);border:1px solid var(--line);border-radius:9px;padding:12px 10px;text-align:center;color:#334158;font-size:14px;line-height:1.45;font-weight:700}}.knowledge{{padding:19px 0 3px;border-top:1px dashed #d9e0ea}}.knowledge:first-of-type{{border-top:0;padding-top:3px}}.knowledge-title{{display:flex;align-items:flex-start;gap:11px;margin-bottom:7px}}.num{{flex:0 0 28px;height:28px;border-radius:50%;display:grid;place-items:center;color:#fff;background:var(--blue);font-size:14px;font-weight:800;margin-top:1px}}.use{{margin-top:9px;color:#45536a;font-size:15px}}.use b{{color:var(--green)}}table{{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border:1px solid var(--line);border-radius:10px;font-size:15px;line-height:1.58}}th,td{{padding:12px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);border-right:1px solid var(--line)}}th:last-child,td:last-child{{border-right:0}}tr:last-child td{{border-bottom:0}}th{{background:var(--soft);color:#303d54;font-size:14px}}td:first-child{{font-weight:750;color:#1d2940;width:21%}}.plain-box{{margin:16px 0 0;padding:15px 17px;border:1px solid #dbe4ef;background:#fafbfd;border-radius:10px}}.source-note{{font-size:14px;color:var(--muted);background:var(--soft);border-radius:9px;padding:13px 15px}}.actions{{display:flex;flex-wrap:wrap;gap:11px;margin-top:17px}}.btn{{display:inline-block;text-decoration:none;border-radius:9px;padding:11px 16px;font-size:15px;font-weight:800;background:var(--blue);color:#fff!important}}.btn.secondary{{background:#edf1f7;color:#25344f!important}}@media(max-width:640px){{.page{{width:100%;margin:0;border-radius:0;border-left:0;border-right:0}}header,main{{padding-left:20px;padding-right:20px}}h1{{font-size:25px}}.learning-map ol,.flow{{display:block}}.step{{margin:7px 0;text-align:left}}table,thead,tbody,tr,th,td{{display:block;width:100%}}th{{display:none}}td{{border-right:0}}td:first-child{{width:100%;background:#fafbfd}}}}
</style>
</head>
<body>
<div class="page" {EMAIL_LEARNING_V1_TEMPLATE_MARKER}>
<header>
  <div class="meta"><span>{escape(str(content["mail_product_id"]))} · {escape(str(content["mail_product_name"]))}</span><span>{escape(str(content["provenance"]["date"]))}</span><span>{escape(str(content["provenance"]["evidence_level"]))}</span></div>
  <h1>{escape(str(content["title_zh_plain"]))}</h1>
  <p class="subtitle">{escape(str(content["subtitle_plain"]))}</p>
</header>
<main>
  <section>
    <h2>先把论文讲成人话</h2>
    <p class="lead"><strong>现实问题：</strong>{escape(str(explanation["real_world_problem"]))}</p>
    <p><strong>为什么难：</strong>{escape(str(explanation["why_difficult"]))}</p>
    <p><strong>旧做法不够在哪里：</strong>{escape(str(explanation["old_approach_gap"]))}</p>
    <p><strong>论文怎么做：</strong>{escape(str(explanation["paper_approach"]))}</p>
    <div class="problem"><strong>现在能得到什么：</strong>{escape(str(explanation["reported_result"]))}</div>
    <div class="plain-box"><strong>术语先解释</strong><ul>{terms}</ul></div>
  </section>
  <section>
    <h2>学习成果导航</h2>
    <div class="learning-map"><strong>读完这封邮件，你应该能带走：</strong><ol>{outcomes}</ol></div>
  </section>
  <section>
    <h2>方法流程</h2>
    <div class="flow">{flow}</div>
  </section>
  <section>
    <h2>真正的新知识</h2>
    {knowledge}
    {queue}
  </section>
  <section>
    <h2>可复用方法</h2>
    {methods}
  </section>
  <section>
    <h2>迁移到你的学习、工作、研究和产品</h2>
    <table><thead><tr><th>场景</th><th>共同结构</th><th>怎么用</th></tr></thead><tbody>{transfers}</tbody></table>
  </section>
  <section>
    <h2>边界</h2>
    <p><strong>目前可以确定：</strong>{escape(str(content["limits"]["known"]))}</p>
    <p><strong>目前不能确定：</strong>{escape(str(content["limits"]["unknown"]))}</p>
  </section>
  <section>
    <h2>继续深读</h2>
    <div class="actions">
      <a class="btn" href="{escape(str(links["chatgpt_new_chat"]), quote=True)}" target="_blank" rel="noopener noreferrer">打开 ChatGPT 新对话</a>
      <a class="btn secondary" href="{escape(str(links["arxiv_link"]), quote=True)}" target="_blank" rel="noopener noreferrer">打开 {escape(str(source_meta["source_link_label"]))}</a>
      <a class="btn secondary" href="{escape(str(links["pdf_link"]), quote=True)}" target="_blank" rel="noopener noreferrer">打开 {escape(str(source_meta["pdf_link_label"]))}</a>
    </div>
    <div class="plain-box"><strong>复制 Prompt 备用：</strong><p>{escape(prompt_preview)}</p></div>
  </section>
  <section>
    <h2>来源与生成记录</h2>
    <p class="source-note">原标题：{escape(str(source_meta["title"]))}<br>{escape(str(source_meta["id_label"]))}：{escape(str(source_meta["paper_id"]))}<br>分类：{escape(str(source_meta["primary_category"]))}<br>模板：{EMAIL_LEARNING_V1_CONTRACT_ID} v{EMAIL_LEARNING_V1_TEMPLATE_VERSION}</p>
  </section>
</main>
</div>
</body>
</html>"""


def _knowledge_unit_html(index: int, unit: Mapping[str, Any]) -> str:
    return (
        '<div class="knowledge"><div class="knowledge-title"><span class="num">'
        + str(index)
        + "</span><h3>"
        + escape(str(unit["title"]))
        + "</h3></div><p><strong>它是什么：</strong>"
        + escape(str(unit["plain_explanation"]))
        + "</p><p><strong>为什么重要：</strong>"
        + escape(str(unit["causal_logic"]))
        + "</p><p><strong>论文如何体现：</strong>"
        + escape(str(unit["paper_specific_example"]))
        + '</p><p class="use"><b>可迁移：</b>'
        + escape(str(unit["transfer_example"]))
        + "</p><p><strong>容易错：</strong>"
        + escape(str(unit["common_mistake_or_limit"]))
        + "</p></div>"
    )


def _method_html(method: Mapping[str, Any]) -> str:
    return (
        '<div class="plain-box"><h3>'
        + escape(str(method["name"]))
        + "</h3><p><strong>什么时候用：</strong>"
        + escape(str(method["when_to_use"]))
        + "</p><p><strong>怎样做：</strong>"
        + escape(str(method["how_to_use"]))
        + "</p><p><strong>常见错误：</strong>"
        + escape(str(method["common_mistake"]))
        + "</p></div>"
    )


def _queue_html(content: Mapping[str, Any]) -> str:
    summary = _clean_text(str(content.get("candidate_queue_summary") or ""))
    items = content.get("queue_items") if isinstance(content.get("queue_items"), list) else []
    if not summary and not items:
        return ""
    rows = "".join(
        "<li>"
        + escape(str(item.get("title") or ""))
        + "（"
        + escape(str(item.get("primary_category") or "unknown"))
        + "）："
        + escape(str(item.get("reason") or "相关候选"))
        + "</li>"
        for item in items
        if isinstance(item, Mapping)
    )
    item_list = f"<ul>{rows}</ul>" if rows else ""
    return '<div class="plain-box"><h3>候选队列摘要</h3><p>' + escape(summary) + "</p>" + item_list + "</div>"


def _mail_product_name(mail_product_id: str) -> str:
    if mail_product_id not in M1_M4_MAIL_PRODUCTS:
        raise ValueError(f"mail_product_id must be one of {', '.join(M1_M4_MAIL_PRODUCTS)}")
    return M1_M4_MAIL_PRODUCTS[mail_product_id]


def _source_meta(source_item: Mapping[str, Any]) -> dict[str, Any]:
    title = _clean_text(str(source_item.get("title") or "Untitled paper"))
    metadata = source_item.get("metadata") if isinstance(source_item.get("metadata"), Mapping) else {}
    arxiv = metadata.get("arxiv") if isinstance(metadata.get("arxiv"), Mapping) else {}
    preprint = metadata.get("preprint") if isinstance(metadata.get("preprint"), Mapping) else {}
    top_journal = metadata.get("top_journal") if isinstance(metadata.get("top_journal"), Mapping) else {}
    stable_id = _source_id(source_item)
    source_url = _https_url(str(source_item.get("canonical_url") or f"https://arxiv.org/abs/{stable_id}"))
    if arxiv:
        source_family = "arxiv"
        source_label = "arXiv"
        summary = _clean_text(str(arxiv.get("summary") or source_item.get("summary") or ""))
        primary_category = _clean_text(str(arxiv.get("primary_category") or "unknown"))
        categories = [str(item) for item in arxiv.get("categories") or [] if item]
        pdf_url = f"https://arxiv.org/pdf/{stable_id}"
        source_link_label = "arXiv 摘要页"
        pdf_link_label = "PDF"
        id_label = "arXiv ID"
        evidence_level = "摘要级 arXiv 元数据"
    elif preprint:
        source_family = "preprint"
        source_label = "bioRxiv/medRxiv"
        summary = _clean_text(str(preprint.get("abstract") or source_item.get("summary") or ""))
        primary_category = _clean_text(str(preprint.get("category") or preprint.get("server") or "preprint"))
        categories = [item for item in (primary_category, str(preprint.get("server") or "")) if item]
        pdf_url = _first_https_content_ref(source_item, ref_type="pdf") or source_url
        source_link_label = "来源页面"
        pdf_link_label = "原文/详情"
        id_label = "来源 ID"
        evidence_level = "摘要级 preprint 元数据"
    elif top_journal:
        journal = _clean_text(str(top_journal.get("journal") or top_journal.get("journal_id") or "Top Journal"))
        article_type = _clean_text(str(top_journal.get("article_type") or "article"))
        source_family = "top_journal"
        source_label = journal
        summary = _clean_text(str(top_journal.get("summary") or source_item.get("summary") or title))
        primary_category = f"{journal} {article_type}".strip()
        categories = [item for item in (journal, article_type, "top_journal") if item]
        pdf_url = _first_https_content_ref(source_item, ref_type="pdf") or source_url
        source_link_label = "来源页面"
        pdf_link_label = "原文/详情"
        id_label = "来源 ID"
        evidence_level = f"摘要级 {journal} RSS 元数据"
    else:
        source_family = str(source_item.get("source_type") or "source")
        source_label = source_family or "Source"
        summary = _clean_text(str(source_item.get("summary") or ""))
        primary_category = _clean_text(str(source_item.get("source_type") or "source"))
        categories = [primary_category] if primary_category else []
        pdf_url = _first_https_content_ref(source_item, ref_type="pdf") or source_url
        source_link_label = "来源页面"
        pdf_link_label = "原文/详情"
        id_label = "来源 ID"
        evidence_level = "摘要级来源元数据"
    return {
        "source_family": source_family,
        "source_label": source_label,
        "source_id": str(source_item.get("source_id") or ""),
        "paper_id": stable_id,
        "title": title,
        "authors": _authors(source_item, arxiv),
        "summary": summary,
        "primary_category": primary_category,
        "categories": categories,
        "source_url": source_url,
        "pdf_url": pdf_url,
        "source_link_label": source_link_label,
        "pdf_link_label": pdf_link_label,
        "id_label": id_label,
        "evidence_level": evidence_level,
    }


def _source_id(source_item: Mapping[str, Any]) -> str:
    raw = str(source_item.get("stable_id") or source_item.get("source_id") or "").removeprefix("arxiv:")
    match = re.search(r"\d{4}\.\d{4,5}(?:v\d+)?", raw)
    if match:
        return re.sub(r"v\d+$", "", match.group(0))
    url = str(source_item.get("canonical_url") or "")
    match = re.search(r"/abs/(\d{4}\.\d{4,5})(?:v\d+)?", url)
    if match:
        return match.group(1)
    cleaned = re.sub(r"^https?://", "", raw or url)
    return _truncate_text(re.sub(r"\s+", "-", cleaned).strip("/:") or "unknown-source", max_chars=80)


def _first_https_content_ref(source_item: Mapping[str, Any], *, ref_type: str) -> str:
    for ref in source_item.get("content_refs") or []:
        if not isinstance(ref, Mapping):
            continue
        if str(ref.get("ref_type") or "").lower() != ref_type:
            continue
        value = _https_url(str(ref.get("uri") or ref.get("url") or ""))
        if _is_https(value):
            return value
    return ""


def _authors(source_item: Mapping[str, Any], arxiv: Mapping[str, Any]) -> list[str]:
    for value in (source_item.get("authors"), arxiv.get("authors")):
        if isinstance(value, list):
            authors = [_clean_text(str(item.get("name") if isinstance(item, Mapping) else item)) for item in value]
            return [item for item in authors if item]
    return []


def _plain_title(source_meta: Mapping[str, Any]) -> str:
    title = str(source_meta["title"])
    text = f"{title} {source_meta.get('summary', '')}".lower()
    if "portfolio" in text or "risk" in text or "market" in text:
        return "把市场风险论文拆成可以验证的决策问题"
    if "agent" in text or "benchmark" in text:
        return "用基准测试检查智能体方法是否真的可靠"
    if "optimization" in text or "control" in text:
        return "把复杂控制问题拆成输入、约束和可观察结果"
    if "image" in text or "microscop" in text or "semiconductor" in text:
        return "用少量图像生成更多可检查样本"
    return "把论文主张拆成普通人能继续追问的问题"


def _subtitle(source_meta: Mapping[str, Any], mail_product_name: str) -> str:
    return f"{mail_product_name}。这封邮件先讲清论文在做什么，再提取新知识、方法、策略、逻辑和可迁移用法。"


def _plain_explanation(
    source_meta: Mapping[str, Any],
    method_flow: Sequence[str],
    claim_texts: Sequence[str],
) -> dict[str, str]:
    summary = _first_sentence(str(source_meta.get("summary") or source_meta["title"]))
    category = str(source_meta.get("primary_category") or "unknown")
    first_claim = _first_non_empty(*(claim_texts[:2]), summary)
    return {
        "real_world_problem": f"这篇论文围绕 {category} 中的一个具体问题：{summary}",
        "why_difficult": "难点不是把标题换成中文，而是要判断论文里的变量、证据和结果是否能被复验。",
        "old_approach_gap": "常见做法只读摘要或只看方法名，容易漏掉输入条件、失败边界和结果能否迁移。",
        "paper_approach": f"作者路线可以拆成：{'，'.join(method_flow[:4])}。",
        "reported_result": f"当前可追踪事实是：{first_claim}",
    }


def _learning_outcomes(source_meta: Mapping[str, Any], method_flow: Sequence[str]) -> list[str]:
    title = _truncate_text(str(source_meta["title"]), max_chars=44)
    return [
        f"用普通中文说明《{title}》到底想解决什么问题。",
        f"把 {source_meta['primary_category']} 的论文变量拆成可观察输入和输出。",
        f"复述论文方法流程：{' -> '.join(method_flow[:3])}。",
        "区分论文事实、解释和迁移建议，避免把摘要当成结论。",
        "把一个新方法迁移到自己的学习、研究或产品验证流程。",
    ]


def _method_flow(frontstage: Mapping[str, Any], source_meta: Mapping[str, Any], core_context: str) -> list[str]:
    raw = frontstage.get("first_principles_chain") if isinstance(frontstage, Mapping) else None
    if isinstance(raw, list):
        items = [_clean_text(str(item)) for item in raw if _clean_text(str(item))]
    else:
        items = []
    if len(items) < 4:
        if any(word in core_context.lower() for word in ("benchmark", "dataset", "evaluation")):
            items = ["定义要比较的任务", "固定数据或基准", "运行候选方法", "比较结果和失败情况", "判断能否复用"]
        elif any(word in core_context.lower() for word in ("portfolio", "risk", "market")):
            items = ["定义市场状态", "建立策略或模型响应", "观察收益与风险变化", "检查拥挤和回撤", "记录失效条件"]
        else:
            items = ["界定现实问题", "找出关键变量", "提出处理机制", "观察结果变化", "记录不能确定的边界"]
    return items[:7]


def _knowledge_units(
    source_meta: Mapping[str, Any],
    frontstage: Mapping[str, Any],
    method_flow: Sequence[str],
    claim_texts: Sequence[str],
) -> list[dict[str, Any]]:
    mappings = frontstage.get("domain_mappings") if isinstance(frontstage.get("domain_mappings"), list) else []
    units: list[dict[str, Any]] = []
    for index, step in enumerate(method_flow[:4], start=1):
        mapping = mappings[index - 1] if index - 1 < len(mappings) and isinstance(mappings[index - 1], Mapping) else {}
        variable = _clean_text(str(mapping.get("paper_variable") or step))
        decision = _clean_text(str(mapping.get("decision_mapping") or "把它转成可观察、可记录、可复验的判断"))
        units.append(
            {
                "title": f"{variable}不是标签，而是可验证对象",
                "plain_explanation": f"{step} 指的是先把论文中的一个说法变成能被检查的对象。",
                "causal_logic": "只有把变量、输入、输出和失败条件拆开，后续判断才不是凭感觉。",
                "paper_specific_example": _first_non_empty(
                    claim_texts[index - 1] if index - 1 < len(claim_texts) else "",
                    f"论文标题《{source_meta['title']}》和分类 {source_meta['primary_category']} 共同指向这个环节。",
                ),
                "transfer_example": decision,
                "common_mistake_or_limit": "最常见错误是只记方法名，不检查它在什么输入条件下才成立。",
            }
        )
    while len(units) < 4:
        units.append(
            {
                "title": f"{source_meta['primary_category']} 的证据边界",
                "plain_explanation": "当前邮件只使用系统已有摘要、元数据和声明证据，不假装读完全文。",
                "causal_logic": "证据深度决定可以下什么结论；摘要级证据只能支持继续追问，不能支持生产决策。",
                "paper_specific_example": f"这篇论文的当前来源是 {source_meta['source_url']}。",
                "transfer_example": "用于决定下一步是打开全文、复现实验，还是只放入观察队列。",
                "common_mistake_or_limit": "不要把预印本摘要改写成已经经过完整验证的事实。",
            }
        )
    return units[:6]


def _reusable_methods(source_meta: Mapping[str, Any], method_flow: Sequence[str]) -> list[dict[str, str]]:
    title = _truncate_text(str(source_meta["title"]), max_chars=48)
    return [
        {
            "name": "变量拆解法",
            "when_to_use": f"遇到像《{title}》这样方法名很多、但目标不一定清楚的论文。",
            "how_to_use": "先写出输入、处理机制、输出、评价方式和失败条件，再读细节。",
            "common_mistake": "直接讨论模型好坏，却没有说明它优化了哪个可观察结果。",
        },
        {
            "name": "证据深度分层法",
            "when_to_use": "当你只有摘要、元数据或局部实验信息时。",
            "how_to_use": "把能确定的事实和需要全文验证的推断分开记录。",
            "common_mistake": "把摘要中的愿景、可能性或实验设定写成已经成立的结论。",
        },
        {
            "name": "迁移结构匹配法",
            "when_to_use": f"当 {source_meta['primary_category']} 的方法看起来可用于别的项目时。",
            "how_to_use": f"找出共同结构：{method_flow[0]} -> {method_flow[min(1, len(method_flow)-1)]}，再换到自己的数据或流程里。",
            "common_mistake": "只迁移术语，不迁移约束、评价指标和失败场景。",
        },
    ]


def _practical_transfer(source_meta: Mapping[str, Any], mail_product_id: str) -> list[dict[str, str]]:
    return [
        {
            "scenario": "你的 ADP 学习工作流",
            "shared_structure": "每天面对一篇新论文时，先做普通中文解释，再抽知识、方法和边界。",
            "how_to_apply": f"把 {source_meta['paper_id']} 的核心变量写进笔记模板，标记事实、解释和迁移建议。",
        },
        {
            "scenario": "研究或产品判断",
            "shared_structure": "论文方法和产品验证都需要输入、约束、输出和失败条件。",
            "how_to_apply": "先做一个最小复验或最小用户场景，不直接把摘要主张升级成路线决策。",
        },
        {
            "scenario": f"{mail_product_id} 后续邮件编排",
            "shared_structure": "M1-M4 只改变板块任务，不改变 V1 学习邮件结构。",
            "how_to_apply": "每个板块都输出同一套 V1 内容对象，便于长期回归和比较。",
        },
    ]


def _limits(frontstage: Mapping[str, Any], source_meta: Mapping[str, Any]) -> dict[str, str]:
    gaps = frontstage.get("evidence_gaps") if isinstance(frontstage.get("evidence_gaps"), list) else []
    known = f"可以确定这是一条来自 {source_meta['source_url']} 的摘要级论文线索，当前分类为 {source_meta['primary_category']}。"
    unknown = _clean_text(str(gaps[0])) if gaps else "还不能确定正文实验、图表、数据和失败条件是否完全支持摘要主张。"
    return {"known": known, "unknown": unknown}


def _term_explanations(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    candidates = [
        ("agent", "智能体", "能根据输入采取行动的软件、模型或规则系统。"),
        ("benchmark", "基准测试", "用固定任务和数据比较方法好坏的一套测试方式。"),
        ("portfolio", "投资组合", "把多个资产放在一起管理风险和收益的集合。"),
        ("optimization", "优化", "在约束条件下寻找更好方案的过程。"),
        ("simulation", "仿真", "用可控环境模拟真实系统可能发生的变化。"),
        ("dataset", "数据集", "用于训练、测试或比较方法的一组样本。"),
        ("risk", "风险", "结果偏离预期并造成损失或失败的可能性。"),
    ]
    rows = [{"term": zh, "plain": plain} for token, zh, plain in candidates if token in lower]
    if len(rows) < 2:
        rows.append({"term": "证据边界", "plain": "说明当前材料能支持哪些判断，哪些还需要读正文或做实验。"})
    if len(rows) < 2:
        rows.append({"term": "迁移", "plain": "把论文里的共同结构拿到学习、研究或产品问题里重新使用。"})
    return rows[:5]


def _chatgpt_prompt(
    *,
    source_meta: Mapping[str, Any],
    title_zh_plain: str,
    plain_explanation: Mapping[str, str],
    learning_outcomes: Sequence[str],
) -> str:
    summary = _truncate_text(str(source_meta.get("summary") or ""), max_chars=1200)
    return "\n".join(
        [
            f"论文中文说明标题：{title_zh_plain}",
            f"英文原标题：{source_meta['title']}",
            f"{source_meta['source_link_label']} URL：{source_meta['source_url']}",
            f"{source_meta['pdf_link_label']} URL：{source_meta['pdf_url']}",
            f"作者：{', '.join(source_meta.get('authors') or []) or '当前元数据未提供'}",
            f"{source_meta['id_label']}：{source_meta['paper_id']}",
            f"分类：{source_meta['primary_category']}",
            f"摘要或关键上下文：{summary}",
            "用户背景：只有高中理科基础的成年人。",
            "学习目标：新知识、新点子、新方法、新策略、新逻辑、新思维，以及它们怎样用于学习、工作、研究和产品。",
            "表达要求：正常中文，术语首次出现先用人话解释，默认不使用公式。",
            "禁止内容：不要写阅读用时、通用价值评分、营销标题或空泛结论。",
            "请区分论文事实、你的解释和迁移建议，并结合正文中的关键图表和实验继续讲解。",
            "邮件中已经给出的普通中文解释：",
            f"- 现实问题：{plain_explanation['real_world_problem']}",
            f"- 论文怎么做：{plain_explanation['paper_approach']}",
            "我想继续深入的学习成果：",
            *[f"- {item}" for item in learning_outcomes[:5]],
        ]
    )


def _queue_item(item: Mapping[str, Any]) -> dict[str, str]:
    return {
        "title": _clean_text(str(item.get("title") or "")),
        "primary_category": _clean_text(str(item.get("primary_category") or "")),
        "reason": _clean_text(str(item.get("reason") or "相关候选")),
    }


def _strip_href_values(text: str) -> str:
    return re.sub(r'href="[^"]*"', 'href=""', text)


def _compact_date(value: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if match:
        return "".join(match.groups())
    digits = re.sub(r"\D+", "", value)
    return digits[:8] or "00000000"


def _first_sentence(text: str) -> str:
    cleaned = _clean_text(text)
    parts = re.split(r"(?<=[.!?。！？])\s+", cleaned)
    return _truncate_text(parts[0] if parts and parts[0] else cleaned, max_chars=220)


def _first_non_empty(*values: str) -> str:
    for value in values:
        cleaned = _clean_text(value)
        if cleaned:
            return cleaned
    return "当前材料没有提供足够细节，只能作为继续阅读线索。"


def _https_url(value: str) -> str:
    if value.startswith("http://arxiv.org/"):
        return "https://" + value.removeprefix("http://")
    return value


def _is_https(value: str) -> bool:
    return value.startswith("https://")


def _truncate_text(value: str, *, max_chars: int) -> str:
    cleaned = _clean_text(value)
    return cleaned if len(cleaned) <= max_chars else cleaned[: max_chars - 3].rstrip(" ,.;:，。；：") + "..."


def _clean_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    for needle, replacement in VISIBLE_TEXT_REPLACEMENTS:
        cleaned = cleaned.replace(needle, replacement)
    return cleaned
