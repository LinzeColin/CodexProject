"""Stage 1 B1/arXiv text report and email artifact builder."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .contracts import stable_content_hash, validate_evidence_claim, validate_source_item
from .evidence_gate import EvidenceGateError, build_claim_ledger
from .lesson import LessonGenerationError, generate_lesson
from .mail_templates import build_chatgpt_learning_url, mail_product_for_board, safe_https_url, source_pdf_url


STAGE1_B1_REPORT_MODEL_ID = "adp-stage1-b1-report-email-v1"
STAGE1_B1_REPORT_SCHEMA_VERSION = 1
STAGE1_B1_BOARD_ID = "B1"
STAGE1_B1_BOARD_NAME = "研究前沿"
STAGE1_B1_SUBJECT_CONTRACT = "YYYYMMDD -- Project Name -- arXiv Group -- Theme"
STAGE1_B1_REQUIRED_CRITICAL_CLAIM_COVERAGE = 100.0
STAGE1_B1_PROHIBITED_EMAIL_MARKERS = (
    "project:",
    "recipient:",
    "ROI",
    "roi_",
    "delivery_policy",
    "Claim Ledger",
    "Release 资料包",
    "12秒视频",
    ".mp4",
    "阅读时间",
    "30 秒",
    "30秒",
    "Frontier Delta",
    "Delta",
)


def build_b1_report_email_package(
    payload: Mapping[str, Any],
    *,
    generated_at: str,
    recipient: str = DEFAULT_RECIPIENT,
    artifact_dir: str | Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Build text-first B1 report/email artifacts from a daily input package."""

    daily_input = _extract_daily_input(payload)
    if not daily_input:
        return _blocked_package(generated_at=generated_at, reasons=["payload must contain daily_input or be a daily input object"])

    errors = _validate_daily_input(daily_input)
    if errors:
        return _blocked_package(generated_at=generated_at, reasons=errors)

    source_item = dict(daily_input["source_item"])
    claims = [dict(claim) for claim in daily_input["claims"] if isinstance(claim, Mapping)]
    candidate_queue_summary = _candidate_queue_summary(payload, source_item)
    try:
        ledger = build_claim_ledger(source_item, claims, extracted_at=generated_at)
        if ledger["blocking_reasons"]:
            return _blocked_package(generated_at=generated_at, reasons=list(ledger["blocking_reasons"]))
        lesson = generate_lesson(source_item, claims, generated_at=generated_at)
    except (EvidenceGateError, LessonGenerationError, ValueError) as error:
        return _blocked_package(generated_at=generated_at, reasons=[str(error)])

    date = str(daily_input["date"])
    source_id = str(source_item["source_id"])
    report_id = f"b1-report:{date}:{_safe_id(source_id)}"
    email_id = f"b1-email:{date}:{_safe_id(source_id)}:{stable_content_hash({'report_id': report_id, 'recipient': recipient})[:10]}"
    subject = _email_subject(date, source_item)
    evidence_audit = _evidence_audit(ledger)
    report_markdown = _render_report_markdown(
        report_id=report_id,
        daily_input=daily_input,
        source_item=source_item,
        ledger=ledger,
        lesson=lesson,
        generated_at=generated_at,
    )
    report_html = _markdown_to_simple_html(report_markdown, title=subject)
    email_plain = _render_email_plain(
        subject=subject,
        report_id=report_id,
        daily_input=daily_input,
        source_item=source_item,
        lesson=lesson,
        evidence_audit=evidence_audit,
        candidate_queue_summary=candidate_queue_summary,
    )
    email_html = _render_email_html(
        subject=subject,
        report_id=report_id,
        daily_input=daily_input,
        source_item=source_item,
        lesson=lesson,
        evidence_audit=evidence_audit,
        candidate_queue_summary=candidate_queue_summary,
    )
    content_hash = stable_content_hash(
        {
            "subject": subject,
            "report_markdown": report_markdown,
            "email_plain": email_plain,
            "email_html": email_html,
            "claim_ids": [claim["claim_id"] for claim in ledger["claims"]],
        }
    )
    package: dict[str, Any] = {
        "model_id": STAGE1_B1_REPORT_MODEL_ID,
        "schema_version": STAGE1_B1_REPORT_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "board_id": STAGE1_B1_BOARD_ID,
        "board_name": STAGE1_B1_BOARD_NAME,
        "status": "pass",
        "generated_at": generated_at,
        "date": date,
        "timezone": str(daily_input.get("timezone") or DEFAULT_TIMEZONE),
        "run_id": str(daily_input["run_id"]),
        "publication_id": str(daily_input["publication_id"]),
        "source_id": source_id,
        "report_id": report_id,
        "email_id": email_id,
        "recipient": recipient,
        "subject_contract": STAGE1_B1_SUBJECT_CONTRACT,
        "email_subject": subject,
        "content_hash": content_hash,
        "quality_gates": {
            "critical_claim_coverage_percent": evidence_audit["critical_claim_coverage_percent"],
            "key_claim_evidence_binding_100_percent": evidence_audit["critical_claim_coverage_percent"]
            == STAGE1_B1_REQUIRED_CRITICAL_CLAIM_COVERAGE,
            "chinese_first_email": _contains_chinese(email_plain),
            "teaching_not_digest": True,
            "no_video_required": True,
            "no_release_required": True,
            "no_real_smtp_send": True,
            "unsupported_claims_published": False,
        },
        "side_effect_policy": {
            "real_smtp_sent": False,
            "release_uploaded": False,
            "video_generated": False,
            "network_fetch_performed": False,
            "secret_values_logged": False,
        },
        "claim_evidence_audit": evidence_audit,
        "candidate_queue_summary": candidate_queue_summary,
        "report_markdown": report_markdown,
        "report_html": report_html,
        "email_plain": email_plain,
        "email_html": email_html,
        "artifact_files": {},
        "content_ledger_update": _content_ledger_update(
            report_id=report_id,
            email_id=email_id,
            daily_input=daily_input,
            source_item=source_item,
            generated_at=generated_at,
        ),
        "blocking_reasons": [],
    }
    if write:
        if artifact_dir is None:
            return _blocked_package(generated_at=generated_at, reasons=["artifact_dir is required when write is true"])
        package["artifact_files"] = _write_artifacts(package, Path(artifact_dir))
    validation_errors = validate_b1_report_email_package(package)
    if validation_errors:
        return {**package, "status": "blocked", "blocking_reasons": validation_errors}
    return package


def validate_b1_report_email_package(package: Mapping[str, Any]) -> list[str]:
    """Validate the S1-07 B1 report/email package without trusting the builder."""

    errors: list[str] = []
    if package.get("model_id") != STAGE1_B1_REPORT_MODEL_ID:
        errors.append("model_id must be adp-stage1-b1-report-email-v1")
    if package.get("schema_version") != STAGE1_B1_REPORT_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if package.get("status") not in {"pass", "blocked"}:
        errors.append("status must be pass or blocked")
    if package.get("status") == "blocked":
        if not package.get("blocking_reasons"):
            errors.append("blocked package requires blocking_reasons")
        return errors

    for field in (
        "report_id",
        "email_id",
        "run_id",
        "publication_id",
        "source_id",
        "date",
        "generated_at",
        "email_subject",
        "report_markdown",
        "report_html",
        "email_plain",
        "email_html",
        "content_hash",
    ):
        if not package.get(field):
            errors.append(f"{field} is required")

    if package.get("board_id") != STAGE1_B1_BOARD_ID:
        errors.append("board_id must be B1")
    if package.get("subject_contract") != STAGE1_B1_SUBJECT_CONTRACT:
        errors.append("subject_contract must match owner subject contract")
    subject = str(package.get("email_subject") or "")
    if not re.match(r"^\d{8} -- .+ -- .+ -- .+$", subject):
        errors.append("email_subject must follow YYYYMMDD -- Project Name -- arXiv Group -- Theme")
    email_plain = str(package.get("email_plain") or "")
    email_html = str(package.get("email_html") or "")
    report_markdown = str(package.get("report_markdown") or "")
    if not _contains_chinese(email_plain):
        errors.append("email_plain must be Chinese-first")
    if not _contains_chinese(report_markdown):
        errors.append("report_markdown must be Chinese-first")
    for marker in STAGE1_B1_PROHIBITED_EMAIL_MARKERS:
        if marker in email_plain or marker in email_html:
            errors.append(f"user-facing email must not contain marker: {marker}")
    if "claim:" not in report_markdown:
        errors.append("report_markdown must retain claim evidence references")

    gates = package.get("quality_gates")
    if not isinstance(gates, Mapping):
        errors.append("quality_gates is required")
    else:
        if gates.get("key_claim_evidence_binding_100_percent") is not True:
            errors.append("key claim evidence binding must be 100 percent")
        if gates.get("unsupported_claims_published") is not False:
            errors.append("unsupported claims must not be published")
        for key in ("no_video_required", "no_release_required", "no_real_smtp_send", "chinese_first_email"):
            if gates.get(key) is not True:
                errors.append(f"quality_gates.{key} must be true")

    side_effects = package.get("side_effect_policy")
    if not isinstance(side_effects, Mapping):
        errors.append("side_effect_policy is required")
    else:
        for key in ("real_smtp_sent", "release_uploaded", "video_generated", "network_fetch_performed", "secret_values_logged"):
            if side_effects.get(key) is not False:
                errors.append(f"side_effect_policy.{key} must be false")

    audit = package.get("claim_evidence_audit")
    if not isinstance(audit, Mapping):
        errors.append("claim_evidence_audit is required")
    else:
        if audit.get("critical_claim_coverage_percent") != STAGE1_B1_REQUIRED_CRITICAL_CLAIM_COVERAGE:
            errors.append("critical claim evidence coverage must be 100.0")
        if audit.get("unsupported_critical_claim_ids"):
            errors.append("unsupported critical claim IDs must be empty")
    if not package.get("candidate_queue_summary"):
        errors.append("candidate_queue_summary is required")
    return errors


def _extract_daily_input(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(payload.get("daily_input"), Mapping):
        return payload["daily_input"]  # type: ignore[return-value]
    if {"run_id", "publication_id", "source_item", "claims"}.issubset(payload.keys()):
        return payload
    return {}


def _validate_daily_input(daily_input: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "publication_id", "date", "generated_at", "source_item", "claims"):
        if not daily_input.get(field):
            errors.append(f"daily_input.{field} is required")
    source_item = daily_input.get("source_item")
    if isinstance(source_item, Mapping):
        errors.extend(validate_source_item(source_item))
        if source_item.get("source_type") != "arxiv":
            errors.append("S1-07 only accepts arXiv SourceItem input")
    else:
        errors.append("daily_input.source_item must be an object")
    claims = daily_input.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("daily_input.claims must be a non-empty array")
    else:
        for index, claim in enumerate(claims):
            if isinstance(claim, Mapping):
                errors.extend(f"daily_input.claims[{index}]: {error}" for error in validate_evidence_claim(claim))
            else:
                errors.append(f"daily_input.claims[{index}] must be an object")
    return errors


def _evidence_audit(ledger: Mapping[str, Any]) -> dict[str, Any]:
    claims = [claim for claim in ledger.get("claims") or [] if isinstance(claim, Mapping)]
    critical = [claim for claim in claims if claim.get("priority") in {"P0", "P1"}]
    supported_critical = [claim for claim in critical if claim.get("support_status") == "supported"]
    coverage = 100.0 if not critical else round(len(supported_critical) * 100.0 / len(critical), 2)
    return {
        "ledger_id": str(ledger.get("ledger_id") or ""),
        "total_claim_count": len(claims),
        "critical_claim_count": len(critical),
        "supported_critical_claim_count": len(supported_critical),
        "critical_claim_coverage_percent": coverage,
        "unsupported_critical_claim_ids": [
            str(claim.get("claim_id")) for claim in critical if claim.get("support_status") != "supported"
        ],
        "critical_claim_ids": [str(claim.get("claim_id")) for claim in critical],
        "source_policy": "arxiv_atom_summary_and_metadata_only",
        "evidence_boundary": "预印本摘要和 arXiv 元数据；不声称同行评审、商业验证或真实部署。",
    }


def _render_report_markdown(
    *,
    report_id: str,
    daily_input: Mapping[str, Any],
    source_item: Mapping[str, Any],
    ledger: Mapping[str, Any],
    lesson: Mapping[str, Any],
    generated_at: str,
) -> str:
    arxiv = _arxiv_meta(source_item)
    frontstage = lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {}
    category = str(arxiv.get("primary_category") or "unknown")
    title = _clean_text(str(source_item.get("title") or "Untitled"))
    url = str(source_item.get("canonical_url") or "")
    lines = [
        f"# B1 研究前沿讲解报告：{title}",
        "",
        f"- report_id: `{report_id}`",
        f"- run_id: `{daily_input.get('run_id')}`",
        f"- source: `{source_item.get('source_id')}` / `{category}`",
        f"- generated_at: `{generated_at}`",
        f"- source_url: {url}",
        "",
        "## 1. 先把论文讲成人话",
        "",
        str(frontstage.get("plain_language_explanation") or frontstage.get("one_line_takeaway") or "这篇论文应先作为学习和验证线索，而不是直接当作已验证结论。"),
        "",
        "## 2. 学习成果导航",
        "",
    ]
    for index, item in enumerate(frontstage.get("learning_outcomes") or [], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 3. 作者具体怎么做", ""])
    for index, item in enumerate(frontstage.get("method_flow") or frontstage.get("first_principles_chain") or [], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 4. 证据与边界", ""])
    for claim in ledger.get("claims") or []:
        if not isinstance(claim, Mapping):
            continue
        marker = str(claim.get("claim_id") or "")
        priority = str(claim.get("priority") or "")
        status = str(claim.get("support_status") or "")
        statement = _clean_text(str(claim.get("statement") or ""))
        lines.append(f"- `{marker}` [{priority}/{status}] {statement}")
    lines.extend(
        [
            "",
            "## 5. 真正值得学的新知识",
            "",
        ]
    )
    for unit in frontstage.get("knowledge_units") or []:
        if isinstance(unit, Mapping):
            lines.append(f"- **{unit.get('title')}**：{unit.get('what')} {unit.get('why')}")
    lines.extend(["", "## 6. 可以直接复用的方法", ""])
    for method in frontstage.get("reusable_methods") or []:
        if isinstance(method, Mapping):
            lines.append(f"- **{method.get('name')}**：{method.get('when')} {method.get('how')} 不适用：{method.get('not_for')}")
    lines.extend(["", "## 7. 具体迁移", ""])
    for scenario in frontstage.get("transfer_scenarios") or []:
        if isinstance(scenario, Mapping):
            lines.append(f"- **{scenario.get('scenario')}**：{scenario.get('connection')}")
    lines.extend(
        [
            "",
            "## 8. 下一步动作",
            "",
            str(frontstage.get("default_action") or "先做最小复现实验，再决定是否深读全文。"),
            "",
            "## 9. 不能越界的地方",
            "",
            "- 当前证据只来自 arXiv 摘要和元数据。",
            "- 不得把摘要主张改写成已证实事实。",
            "- 不得声称同行评审、生产部署、投资收益或商业转化已经成立。",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_email_plain(
    *,
    subject: str,
    report_id: str,
    daily_input: Mapping[str, Any],
    source_item: Mapping[str, Any],
    lesson: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
    candidate_queue_summary: str,
) -> str:
    arxiv = _arxiv_meta(source_item)
    frontstage = lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {}
    title = _clean_text(str(source_item.get("title") or "Untitled"))
    product = mail_product_for_board(STAGE1_B1_BOARD_ID)
    url = safe_https_url(source_item.get("canonical_url"))
    pdf_url = source_pdf_url(source_item)
    chatgpt_url = build_chatgpt_learning_url(source_item, chinese_title=_learning_title(frontstage, title))
    category = str(arxiv.get("primary_category") or "unknown")
    boundary = frontstage.get("learning_boundary") if isinstance(frontstage.get("learning_boundary"), Mapping) else {}
    return "\n".join(
        [
            subject,
            "",
            f"【{product['id']}｜{product['name']}】",
            str(product["focus"]),
            "",
            "【先把论文讲成人话】",
            f"论文：{title}",
            f"分类：{category}；证据深度：摘要级 arXiv 元数据",
            str(frontstage.get("plain_language_explanation") or frontstage.get("one_line_takeaway") or "这篇论文目前适合作为学习线索，不能直接当作已验证结论。"),
            "",
            "【学习成果导航】",
            *_numbered_lines(frontstage.get("learning_outcomes"), limit=6),
            "",
            "【作者具体怎么做】",
            " → ".join(str(item) for item in frontstage.get("method_flow") or frontstage.get("first_principles_chain") or ["问题", "变量", "机制", "输出", "失败条件"]),
            "",
            "【真正值得学的新知识】",
            *_knowledge_unit_lines(frontstage.get("knowledge_units"), limit=5),
            "",
            "【可以直接复用的方法】",
            *_method_lines(frontstage.get("reusable_methods"), limit=4),
            "",
            "【连接到你的学习、研究和产品】",
            *_transfer_lines(frontstage.get("transfer_scenarios"), limit=4),
            "",
            "【边界】",
            "可以确定：" + "；".join(str(item) for item in boundary.get("can_determine", [])[:2]) if isinstance(boundary.get("can_determine"), list) else str(evidence_audit.get("evidence_boundary")),
            "不能确定：" + "；".join(str(item) for item in boundary.get("cannot_determine", [])[:2]) if isinstance(boundary.get("cannot_determine"), list) else "不能把摘要主张当成全文验证结果。",
            "",
            "【你今天可以做的最小动作】",
            str(frontstage.get("default_action") or "列出输入、输出和失败条件，再决定是否深读全文。"),
            "",
            "【继续学习入口】",
            f"arXiv 摘要页：{url}",
            f"PDF：{pdf_url}",
            f"ChatGPT 新对话：{chatgpt_url}",
            f"报告：{report_id}",
            f"Run：{daily_input.get('run_id')}",
            "",
            "【候选队列状态】",
            candidate_queue_summary,
        ]
    )


def _render_email_html(
    *,
    subject: str,
    report_id: str,
    daily_input: Mapping[str, Any],
    source_item: Mapping[str, Any],
    lesson: Mapping[str, Any],
    evidence_audit: Mapping[str, Any],
    candidate_queue_summary: str,
) -> str:
    arxiv = _arxiv_meta(source_item)
    frontstage = lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {}
    title = _clean_text(str(source_item.get("title") or "Untitled"))
    product = mail_product_for_board(STAGE1_B1_BOARD_ID)
    url = safe_https_url(source_item.get("canonical_url"))
    pdf_url = source_pdf_url(source_item)
    chatgpt_url = build_chatgpt_learning_url(source_item, chinese_title=_learning_title(frontstage, title))
    chain = frontstage.get("method_flow") or frontstage.get("first_principles_chain") or ["问题", "变量", "机制", "输出", "失败条件"]
    outcomes = frontstage.get("learning_outcomes") or []
    boundary = frontstage.get("learning_boundary") if isinstance(frontstage.get("learning_boundary"), Mapping) else {}
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN"><head><meta charset="utf-8">',
            f"<title>{html.escape(subject)}</title>",
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;color:#202124;max-width:760px;margin:0 auto;padding:24px;background:#f5f7fb}.page{background:#fff;border:1px solid #e3e8ef;border-radius:10px;padding:24px}h1{font-size:24px;line-height:1.35;margin:0 0 10px}h2{font-size:18px;margin:26px 0 10px}.meta{color:#5f6368}.chain span{display:inline-block;margin:4px 6px 4px 0;padding:6px 9px;border:1px solid #d9e0ea;border-radius:7px;background:#f6f8fb}.unit,.method{border-top:1px solid #e6ebf2;padding:12px 0}.btn{display:inline-block;margin:4px 8px 8px 0;padding:10px 12px;border-radius:7px;text-decoration:none;background:#1c438f;color:#fff!important;font-weight:700}.btn.alt{background:#edf1f7;color:#25344f!important}@media(max-width:560px){body{padding:0}.page{border-radius:0;border-left:0;border-right:0;padding:18px}h1{font-size:21px}}</style>",
            "</head><body>",
            '<div class="page">',
            f"<p class=\"meta\">{html.escape(str(product['id']))}｜{html.escape(str(product['name']))}｜{html.escape(str(product['earliest_send']))}</p>",
            f"<h1>{html.escape(_learning_title(frontstage, title))}</h1>",
            f"<p class=\"meta\">{html.escape(title)} | {html.escape(str(arxiv.get('primary_category') or 'unknown'))} | 摘要级 arXiv 元数据</p>",
            "<h2>先把论文讲成人话</h2>",
            f"<p>{html.escape(str(frontstage.get('plain_language_explanation') or frontstage.get('one_line_takeaway') or '这篇论文目前适合作为学习线索。'))}</p>",
            "<h2>学习成果导航</h2>",
            _html_ordered_list(outcomes[:6]),
            "<h2>作者具体怎么做</h2>",
            "<p class=\"chain\">" + "".join(f"<span>{html.escape(str(item))}</span>" for item in chain) + "</p>",
            "<h2>真正值得学的新知识</h2>",
            _html_knowledge_units(frontstage.get("knowledge_units")),
            "<h2>可以直接复用的方法</h2>",
            _html_methods(frontstage.get("reusable_methods")),
            "<h2>连接到你的学习、研究和产品</h2>",
            _html_transfer(frontstage.get("transfer_scenarios")),
            "<h2>边界</h2>",
            f"<p><strong>可以确定：</strong>{html.escape('；'.join(str(item) for item in boundary.get('can_determine', [])[:2]) if isinstance(boundary.get('can_determine'), list) else str(evidence_audit.get('evidence_boundary')))}</p>",
            f"<p><strong>不能确定：</strong>{html.escape('；'.join(str(item) for item in boundary.get('cannot_determine', [])[:2]) if isinstance(boundary.get('cannot_determine'), list) else '不能把摘要主张当成全文验证结果。')}</p>",
            "<h2>今天的最小动作</h2>",
            f"<p>{html.escape(str(frontstage.get('default_action') or '列出输入、输出和失败条件，再决定是否深读全文。'))}</p>",
            "<h2>继续学习入口</h2>",
            f"<p>{_safe_link('arXiv 摘要页', url, primary=True)}{_safe_link('PDF', pdf_url, primary=False)}{_safe_link('ChatGPT 新对话', chatgpt_url, primary=False)}</p>",
            "<h2>候选队列</h2>",
            f"<p>{html.escape(candidate_queue_summary)}</p>",
            f"<p class=\"meta\">报告：{html.escape(report_id)}<br>Run：{html.escape(str(daily_input.get('run_id')))}</p>",
            "</div></body></html>",
        ]
    )


def _learning_title(frontstage: Mapping[str, Any], title: str) -> str:
    plain = _clean_text(str(frontstage.get("plain_language_title") or ""))
    if plain:
        return plain
    takeaway = _clean_text(str(frontstage.get("one_line_takeaway") or ""))
    if takeaway and len(takeaway) <= 72:
        return takeaway
    return f"用普通中文读懂：{_truncate(title, 54)}"


def _numbered_lines(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return ["1. 识别论文事实、解释和迁移建议。"]
    return [f"{index}. {item}" for index, item in enumerate([str(item) for item in value[:limit] if str(item).strip()], start=1)]


def _knowledge_unit_lines(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return ["1. 证据入口：先确认论文主张来自哪里、能支持到什么程度。"]
    lines = []
    for index, item in enumerate(value[:limit], start=1):
        if not isinstance(item, Mapping):
            continue
        lines.append(
            f"{index}. {item.get('title')}：{item.get('what')} 为什么重要：{item.get('why')} "
            f"迁移：{item.get('transfer')}"
        )
    return lines or ["1. 证据入口：先确认论文主张来自哪里、能支持到什么程度。"]


def _method_lines(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return ["- 摘要级证据分层：先分开事实、解释和迁移建议；不能替代全文核查。"]
    lines = []
    for item in value[:limit]:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- {item.get('name')}：{item.get('when')} {item.get('how')} 不适用：{item.get('not_for')}")
    return lines or ["- 摘要级证据分层：先分开事实、解释和迁移建议；不能替代全文核查。"]


def _transfer_lines(value: Any, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return ["- 学习：把论文拆成事实、解释、方法和边界。"]
    lines = []
    for item in value[:limit]:
        if isinstance(item, Mapping):
            lines.append(f"- {item.get('scenario')}：{item.get('connection')}")
    return lines or ["- 学习：把论文拆成事实、解释、方法和边界。"]


def _html_ordered_list(items: Sequence[Any]) -> str:
    rows = "".join(f"<li>{html.escape(str(item))}</li>" for item in items if str(item).strip())
    return f"<ol>{rows}</ol>" if rows else "<ol><li>识别论文事实、解释和迁移建议。</li></ol>"


def _html_knowledge_units(value: Any) -> str:
    if not isinstance(value, list):
        return "<p>先确认论文主张来自哪里、能支持到什么程度。</p>"
    rows = []
    for item in value[:5]:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            "<div class=\"unit\">"
            f"<strong>{html.escape(str(item.get('title') or '知识单元'))}</strong>"
            f"<p>{html.escape(str(item.get('what') or ''))}</p>"
            f"<p>{html.escape(str(item.get('why') or ''))}</p>"
            f"<p><em>迁移：</em>{html.escape(str(item.get('transfer') or ''))}</p>"
            "</div>"
        )
    return "".join(rows) or "<p>先确认论文主张来自哪里、能支持到什么程度。</p>"


def _html_methods(value: Any) -> str:
    if not isinstance(value, list):
        return "<p>摘要级证据分层：先分开事实、解释和迁移建议。</p>"
    rows = []
    for item in value[:4]:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            "<div class=\"method\">"
            f"<strong>{html.escape(str(item.get('name') or '可复用方法'))}</strong>"
            f"<p>{html.escape(str(item.get('when') or ''))} {html.escape(str(item.get('how') or ''))}</p>"
            f"<p><em>不适用：</em>{html.escape(str(item.get('not_for') or ''))}</p>"
            "</div>"
        )
    return "".join(rows) or "<p>摘要级证据分层：先分开事实、解释和迁移建议。</p>"


def _html_transfer(value: Any) -> str:
    if not isinstance(value, list):
        return "<ul><li>学习：把论文拆成事实、解释、方法和边界。</li></ul>"
    rows = []
    for item in value[:4]:
        if isinstance(item, Mapping):
            rows.append(f"<li><strong>{html.escape(str(item.get('scenario') or '迁移'))}</strong>：{html.escape(str(item.get('connection') or ''))}</li>")
    return f"<ul>{''.join(rows)}</ul>" if rows else "<ul><li>学习：把论文拆成事实、解释、方法和边界。</li></ul>"


def _safe_link(label: str, url: str, *, primary: bool) -> str:
    safe_url = safe_https_url(url)
    if not safe_url:
        return ""
    class_name = "btn" if primary else "btn alt"
    return (
        f"<a class=\"{class_name}\" href=\"{html.escape(safe_url, quote=True)}\" "
        f"target=\"_blank\" rel=\"noopener noreferrer\">{html.escape(label)}</a>"
    )


def _markdown_to_simple_html(markdown: str, *, title: str) -> str:
    lines = [f"<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><title>{html.escape(title)}</title></head><body>"]
    for line in markdown.splitlines():
        if line.startswith("# "):
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            lines.append(f"<p>{html.escape(line)}</p>")
        elif re.match(r"^\d+\. ", line):
            lines.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            lines.append(f"<p>{html.escape(line)}</p>")
    lines.append("</body></html>")
    return "\n".join(lines)


def _write_artifacts(package: Mapping[str, Any], artifact_dir: Path) -> dict[str, dict[str, Any]]:
    stem = f"b1_{package['date']}_{_safe_id(str(package['source_id']))}"
    targets = {
        "report_markdown": artifact_dir / "reports" / f"{stem}.md",
        "report_html": artifact_dir / "reports" / f"{stem}.html",
        "email_plain": artifact_dir / "emails" / f"{stem}.txt",
        "email_html": artifact_dir / "emails" / f"{stem}.html",
        "audit_json": artifact_dir / "audit" / f"{stem}.json",
    }
    contents = {
        "report_markdown": str(package["report_markdown"]),
        "report_html": str(package["report_html"]),
        "email_plain": str(package["email_plain"]),
        "email_html": str(package["email_html"]),
        "audit_json": json.dumps(
            {
                key: value
                for key, value in package.items()
                if key not in {"report_markdown", "report_html", "email_plain", "email_html", "artifact_files"}
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
    }
    refs: dict[str, dict[str, Any]] = {}
    for key, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents[key], encoding="utf-8")
        data = path.read_bytes()
        refs[key] = {
            "path": str(path),
            "sha256": stable_content_hash({"content": contents[key]}),
            "size_bytes": len(data),
        }
    return refs


def _content_ledger_update(
    *,
    report_id: str,
    email_id: str,
    daily_input: Mapping[str, Any],
    source_item: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    arxiv = _arxiv_meta(source_item)
    return {
        "item_id": str(source_item.get("source_id") or ""),
        "board_id": STAGE1_B1_BOARD_ID,
        "title": _clean_text(str(source_item.get("title") or "")),
        "source_id": str(source_item.get("source_id") or ""),
        "primary_category": str(arxiv.get("primary_category") or ""),
        "queue_state": "covered_deep",
        "reason_code": "S1_07_B1_REPORT_EMAIL_READY",
        "report_id": report_id,
        "report_file_state": "generated" if daily_input else "not_generated",
        "email_id": email_id,
        "email_state": "preview_generated",
        "email_sent_at": "NOT_SENT_DRY_RUN",
        "run_id": str(daily_input.get("run_id") or ""),
        "last_updated_at": generated_at,
    }


def _candidate_queue_summary(payload: Mapping[str, Any], source_item: Mapping[str, Any]) -> str:
    title = _truncate(str(source_item.get("title") or "本篇论文"), 42)
    queue_report = payload.get("queue_report") or payload.get("stage1_queue_report")
    if isinstance(queue_report, Mapping):
        total = queue_report.get("total_items")
        active = queue_report.get("active_count")
        if total is not None and active is not None:
            return (
                f"候选队列：本次队列共 {total} 篇，当前有效 {active} 篇；"
                f"已选《{title}》做深讲，其余继续按质量、时效、证据和主题多样性排序。"
            )
    candidate_count = payload.get("candidate_count")
    if candidate_count is not None:
        return (
            f"候选队列：今日 arXiv 候选 {candidate_count} 篇；"
            f"已选《{title}》做深讲，未选项保留到后续队列/ledger。"
        )
    return "候选队列：当前输入未携带完整队列快照；本次只生成主讲文章的报告、邮件预览和 ledger 更新。"


def _blocked_package(*, generated_at: str, reasons: Sequence[str]) -> dict[str, Any]:
    return {
        "model_id": STAGE1_B1_REPORT_MODEL_ID,
        "schema_version": STAGE1_B1_REPORT_SCHEMA_VERSION,
        "project_id": "arxiv-daily-push",
        "board_id": STAGE1_B1_BOARD_ID,
        "board_name": STAGE1_B1_BOARD_NAME,
        "status": "blocked",
        "generated_at": generated_at,
        "blocking_reasons": [str(reason) for reason in reasons if str(reason)],
        "side_effect_policy": {
            "real_smtp_sent": False,
            "release_uploaded": False,
            "video_generated": False,
            "network_fetch_performed": False,
            "secret_values_logged": False,
        },
    }


def _email_subject(date: str, source_item: Mapping[str, Any]) -> str:
    yyyymmdd = date.replace("-", "")
    arxiv = _arxiv_meta(source_item)
    group = f"arXiv {arxiv.get('primary_category') or 'B1'}"
    theme = _theme(source_item)
    return f"{yyyymmdd} -- arXiv Daily Push -- {group} -- {theme}"


def _theme(source_item: Mapping[str, Any]) -> str:
    title = _clean_text(str(source_item.get("title") or "Research frontier"))
    words = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", title)
    text = " ".join(words[:8]) if words else title
    return _truncate(text, 64)


def _decision_mapping_sentence(frontstage: Mapping[str, Any]) -> str:
    mappings = [item for item in frontstage.get("domain_mappings") or [] if isinstance(item, Mapping)]
    if not mappings:
        return "把论文主张拆成变量、机制、输出和失败条件，判断它是否降低学习、研究或验证成本。"
    first = mappings[0]
    return f"先看 {first.get('paper_variable')} 是否能映射到：{first.get('decision_mapping')}。"


def _arxiv_meta(source_item: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = source_item.get("metadata")
    if isinstance(metadata, Mapping) and isinstance(metadata.get("arxiv"), Mapping):
        return metadata["arxiv"]  # type: ignore[return-value]
    return {}


def _contains_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return safe.strip("-") or "unknown"


def _truncate(value: str, max_chars: int) -> str:
    cleaned = _clean_text(value)
    return cleaned if len(cleaned) <= max_chars else cleaned[: max_chars - 3].rstrip(" ,.;:") + "..."


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
