"""Stage 1 B1/arXiv text report and email artifact builder."""

from __future__ import annotations

import html
import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE
from .contracts import stable_content_hash, validate_evidence_claim, validate_source_item
from .evidence_gate import EvidenceGateError, build_claim_ledger
from .lesson import LessonGenerationError, generate_lesson
from .mail_templates import (
    EMAIL_LEARNING_V1_CONTRACT_ID,
    EMAIL_LEARNING_V1_TEMPLATE_VERSION,
    render_email_learning_v1,
)
from .security_boundary import sanitize_public_url, validate_trust_boundary_receipt, validate_typed_frontstage


STAGE1_B1_REPORT_MODEL_ID = "adp-stage1-b1-report-email-v1"
STAGE1_B1_REPORT_SCHEMA_VERSION = 1
STAGE1_B1_BOARD_ID = "B1"
STAGE1_B1_BOARD_NAME = "研究前沿"
STAGE1_B1_SUBJECT_CONTRACT = "YYYYMMDD -- Project Name -- Mail Product -- Plain Theme"
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
    evidence_audit = _evidence_audit(ledger)
    report_markdown = _render_report_markdown(
        report_id=report_id,
        daily_input=daily_input,
        source_item=source_item,
        ledger=ledger,
        lesson=lesson,
        generated_at=generated_at,
    )
    rendered_email = render_email_learning_v1(
        mail_product_id="M1",
        source_item=source_item,
        lesson=lesson,
        claims=claims,
        generated_at=generated_at,
        date=date,
        run_id=str(daily_input["run_id"]),
        report_id=report_id,
        candidate_queue_summary=candidate_queue_summary,
    )
    subject = str(rendered_email["subject"])
    report_html = _markdown_to_simple_html(report_markdown, title=subject)
    email_plain = str(rendered_email["plain"])
    email_html = str(rendered_email["html"])
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
        "email_template_contract": EMAIL_LEARNING_V1_CONTRACT_ID,
        "email_template_version": EMAIL_LEARNING_V1_TEMPLATE_VERSION,
        "mail_product_id": "M1",
        "email_learning_content_v1": rendered_email["content"],
        "content_hash": content_hash,
        "quality_gates": {
            "critical_claim_coverage_percent": evidence_audit["critical_claim_coverage_percent"],
            "key_claim_evidence_binding_100_percent": evidence_audit["critical_claim_coverage_percent"]
            == STAGE1_B1_REQUIRED_CRITICAL_CLAIM_COVERAGE,
            "email_learning_v1_template": True,
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
        "lesson_claim_ids": [str(claim_id) for claim_id in lesson.get("claim_ids", []) if claim_id],
        "lesson_frontstage": lesson.get("frontstage") if isinstance(lesson.get("frontstage"), Mapping) else {},
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
    validation_errors = validate_b1_report_email_package(package)
    if validation_errors:
        return {**package, "status": "blocked", "blocking_reasons": validation_errors}
    if write:
        if artifact_dir is None:
            return _blocked_package(generated_at=generated_at, reasons=["artifact_dir is required when write is true"])
        package["artifact_files"] = _write_artifacts(package, Path(artifact_dir))
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
        errors.append("email_subject must follow YYYYMMDD -- Project Name -- Mail Product -- Plain Theme")
    if package.get("email_template_contract") != EMAIL_LEARNING_V1_CONTRACT_ID:
        errors.append("email_template_contract must be EMAIL_LEARNING_V1")
    if package.get("email_template_version") != EMAIL_LEARNING_V1_TEMPLATE_VERSION:
        errors.append("email_template_version must match Email V1")
    if package.get("mail_product_id") != "M1":
        errors.append("B1 report email must use M1 mail product")
    if not isinstance(package.get("email_learning_content_v1"), Mapping):
        errors.append("email_learning_content_v1 is required")
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
        for key in ("email_learning_v1_template", "no_video_required", "no_release_required", "no_real_smtp_send", "chinese_first_email"):
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
        if int(audit.get("critical_claim_count") or 0) <= 0:
            errors.append("critical claim count must be greater than 0")
        if audit.get("unsupported_critical_claim_ids"):
            errors.append("unsupported critical claim IDs must be empty")
    content = package.get("email_learning_content_v1")
    if isinstance(content, Mapping):
        source_meta = content.get("source_meta") if isinstance(content.get("source_meta"), Mapping) else {}
        if source_meta and not sanitize_public_url(str(source_meta.get("source_url") or "")):
            errors.append("email source URL must be safe")
    frontstage = package.get("lesson_frontstage")
    if isinstance(frontstage, Mapping):
        allowed_claim_ids = [str(item) for item in package.get("lesson_claim_ids") or [] if item]
        errors.extend(validate_typed_frontstage(frontstage, allowed_claim_ids=allowed_claim_ids))
        receipt = frontstage.get("trust_boundary_receipt")
        if isinstance(receipt, Mapping):
            errors.extend(validate_trust_boundary_receipt(receipt))
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
    coverage = 0.0 if not critical else round(len(supported_critical) * 100.0 / len(critical), 2)
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
    url = sanitize_public_url(str(source_item.get("canonical_url") or ""))
    if not url:
        url = "UNSAFE_SOURCE_URL_REMOVED"
    lines = [
        f"# B1 研究前沿讲解报告：{title}",
        "",
        f"- report_id: `{report_id}`",
        f"- run_id: `{daily_input.get('run_id')}`",
        f"- source: `{source_item.get('source_id')}` / `{category}`",
        f"- generated_at: `{generated_at}`",
        f"- source_url: {url}",
        "",
        "## 1. 先给结论",
        "",
        str(frontstage.get("one_line_takeaway") or "这篇论文应先作为学习和验证线索，而不是直接当作已验证结论。"),
        "",
        "## 2. 一阶机制拆解",
        "",
    ]
    for index, item in enumerate(frontstage.get("first_principles_chain") or ["问题定义", "变量", "机制", "输出", "失败条件"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 3. 证据与边界", ""])
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
            "## 4. 决策映射",
            "",
        ]
    )
    for mapping in frontstage.get("domain_mappings") or []:
        if isinstance(mapping, Mapping):
            lines.append(f"- {mapping.get('paper_variable')}: {mapping.get('decision_mapping')}")
    lines.extend(["", "## 5. 三个必须追问的问题", ""])
    for question in frontstage.get("key_questions") or []:
        lines.append(f"- {question}")
    lines.extend(
        [
            "",
            "## 6. 下一步动作",
            "",
            str(frontstage.get("default_action") or "先做最小复现实验，再决定是否深读全文。"),
            "",
            "## 7. 不能越界的地方",
            "",
            "- 当前证据只来自 arXiv 摘要和元数据。",
            "- 不得把摘要主张改写成已证实事实。",
            "- 不得声称同行评审、生产部署、投资收益或商业转化已经成立。",
        ]
    )
    return "\n".join(lines) + "\n"


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
    package_hash = stable_content_hash(
        {
            "report_id": package["report_id"],
            "email_id": package["email_id"],
            "content_hash": package["content_hash"],
        }
    )[:12]
    package_dir_name = f"{stem}_{package_hash}"
    final_root = artifact_dir / "packages" / package_dir_name
    staging_parent = artifact_dir / ".b1_staging"
    staging_root = staging_parent / package_dir_name
    if final_root.exists():
        return _artifact_refs(package, final_root)
    if staging_root.exists():
        shutil.rmtree(staging_root)
    try:
        _write_artifact_payloads(package, staging_root)
        _verify_artifact_refs(_artifact_refs(package, staging_root))
        final_root.parent.mkdir(parents=True, exist_ok=True)
        _atomic_publish_artifact_tree(staging_root, final_root)
        return _artifact_refs(package, final_root)
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    finally:
        try:
            staging_parent.rmdir()
        except OSError:
            pass


def _write_artifact_payloads(package: Mapping[str, Any], root: Path) -> None:
    contents = _artifact_contents(package)
    for key, path in _artifact_targets(package, root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents[key], encoding="utf-8")


def _atomic_publish_artifact_tree(staging_root: Path, final_root: Path) -> None:
    os.replace(staging_root, final_root)


def _artifact_refs(package: Mapping[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    contents = _artifact_contents(package)
    refs: dict[str, dict[str, Any]] = {}
    for key, path in _artifact_targets(package, root).items():
        data = path.read_bytes()
        refs[key] = {
            "path": str(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "content_hash": stable_content_hash({"content": contents[key]}),
            "size_bytes": len(data),
        }
    return refs


def _verify_artifact_refs(refs: Mapping[str, Mapping[str, Any]]) -> None:
    for key, artifact in refs.items():
        path = Path(str(artifact.get("path") or ""))
        if not path.is_file():
            raise FileNotFoundError(f"artifact {key} was not staged: {path}")
        if artifact.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"artifact {key} sha256 mismatch before publish")


def _artifact_targets(package: Mapping[str, Any], root: Path) -> dict[str, Path]:
    stem = f"b1_{package['date']}_{_safe_id(str(package['source_id']))}"
    return {
        "report_markdown": root / "reports" / f"{stem}.md",
        "report_html": root / "reports" / f"{stem}.html",
        "email_plain": root / "emails" / f"{stem}.txt",
        "email_html": root / "emails" / f"{stem}.html",
        "audit_json": root / "audit" / f"{stem}.json",
    }


def _artifact_contents(package: Mapping[str, Any]) -> dict[str, str]:
    return {
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
