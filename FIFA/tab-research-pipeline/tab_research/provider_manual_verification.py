from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .boards import BOARD_BY_ID
from .io import atomic_write_json, atomic_write_text
from .odds import valid_decimal_odds
from .provider_fallback_verification import (
    TEAM_TOTAL_LABEL,
    build_verification_queue,
    first_matches_target,
    load_staged_matches_raw,
)
from .raw_refresh import RAW_BATCH_MANIFEST, audit_staged_raw_refresh, sha256_file, validate_raw_snapshot
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


REPORT_TZ = ZoneInfo("Australia/Sydney")
PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST = "provider_manual_verification_template_latest.csv"
PROVIDER_MANUAL_VERIFICATION_STATUS_JSON_LATEST = "provider_manual_verification_status_latest.json"
PROVIDER_MANUAL_VERIFICATION_STATUS_MD_LATEST = "provider_manual_verification_status_latest.md"
PROVIDER_MANUAL_VERIFICATION_STATUS_PDF_LATEST = "provider_manual_verification_status_latest.pdf"
PROVIDER_MANUAL_HASH_GATE_JSON_LATEST = "provider_manual_hash_gate_latest.json"
PROVIDER_MANUAL_HASH_GATE_MD_LATEST = "provider_manual_hash_gate_latest.md"
PROVIDER_MANUAL_HASH_GATE_PDF_LATEST = "provider_manual_hash_gate_latest.pdf"
PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST = "provider_manual_overlay_preview_latest.json"
PROVIDER_MANUAL_OVERLAY_PREVIEW_MD_LATEST = "provider_manual_overlay_preview_latest.md"
PROVIDER_MANUAL_OVERLAY_PREVIEW_PDF_LATEST = "provider_manual_overlay_preview_latest.pdf"
PROVIDER_MANUAL_OVERLAY_RAW_LATEST = "provider_manual_team_total_overlay_raw_latest.json"
PROVIDER_MANUAL_OVERLAY_APPROVAL_TEMPLATE_JSON_LATEST = "provider_manual_overlay_approval_template_latest.json"
PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST = "provider_manual_overlay_publish_preflight_latest.json"
PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_MD_LATEST = "provider_manual_overlay_publish_preflight_latest.md"
PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_PDF_LATEST = "provider_manual_overlay_publish_preflight_latest.pdf"
PROVIDER_MANUAL_OVERLAY_PUBLISH_JSON_LATEST = "provider_manual_overlay_publish_latest.json"
PROVIDER_MANUAL_OVERLAY_PUBLISH_MD_LATEST = "provider_manual_overlay_publish_latest.md"
PROVIDER_MANUAL_OVERLAY_PUBLISH_PDF_LATEST = "provider_manual_overlay_publish_latest.pdf"
PROVIDER_MANUAL_WORKBENCH_JSON_LATEST = "provider_manual_workbench_latest.json"
PROVIDER_MANUAL_WORKBENCH_MD_LATEST = "provider_manual_workbench_latest.md"
PROVIDER_MANUAL_WORKBENCH_PDF_LATEST = "provider_manual_workbench_latest.pdf"
PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST = "provider_manual_pair_template_latest.csv"
PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST = "provider_manual_next_batch_pair_template_latest.csv"
DEFAULT_IMPORT_RELATIVE_PATH = "manual_verification/provider_team_total_manual_verification.csv"
DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH = "manual_verification/provider_team_total_overlay_approval.json"
DEFAULT_WORKBENCH_BATCH_SIZE = 8
CSV_FIELDS = [
    "event_id",
    "rank",
    "match",
    "commence_time",
    "priority_tier",
    "missing_market",
    "tab_match_name",
    "team_scope",
    "tab_market_name",
    "selection_name",
    "line",
    "decimal_odds",
    "observed_at_aest",
    "operator_initials",
    "evidence_note_or_screenshot_ref",
    "verification_status",
]
QUALITY_REQUIRED_FIELDS = [
    "tab_match_name",
    "team_scope",
    "tab_market_name",
    "selection_name",
    "line",
    "decimal_odds",
    "observed_at_aest",
    "operator_initials",
    "evidence_note_or_screenshot_ref",
    "verification_status",
]


def write_provider_manual_verification_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_provider_manual_verification_status(output_dir)
    template_path = output_dir / PROVIDER_MANUAL_VERIFICATION_TEMPLATE_CSV_LATEST
    json_path = output_dir / PROVIDER_MANUAL_VERIFICATION_STATUS_JSON_LATEST
    md_path = output_dir / PROVIDER_MANUAL_VERIFICATION_STATUS_MD_LATEST
    pdf_path = output_dir / PROVIDER_MANUAL_VERIFICATION_STATUS_PDF_LATEST
    gate_payload = build_provider_manual_hash_gate(output_dir)
    gate_json_path = output_dir / PROVIDER_MANUAL_HASH_GATE_JSON_LATEST
    gate_md_path = output_dir / PROVIDER_MANUAL_HASH_GATE_MD_LATEST
    gate_pdf_path = output_dir / PROVIDER_MANUAL_HASH_GATE_PDF_LATEST
    overlay_json_path = output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST
    overlay_md_path = output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_MD_LATEST
    overlay_pdf_path = output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_PDF_LATEST
    overlay_raw_path = output_dir / PROVIDER_MANUAL_OVERLAY_RAW_LATEST
    approval_template_path = output_dir / PROVIDER_MANUAL_OVERLAY_APPROVAL_TEMPLATE_JSON_LATEST
    overlay_preflight_json_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST
    overlay_preflight_md_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_MD_LATEST
    overlay_preflight_pdf_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_PDF_LATEST
    workbench_json_path = output_dir / PROVIDER_MANUAL_WORKBENCH_JSON_LATEST
    workbench_md_path = output_dir / PROVIDER_MANUAL_WORKBENCH_MD_LATEST
    workbench_pdf_path = output_dir / PROVIDER_MANUAL_WORKBENCH_PDF_LATEST
    pair_template_path = output_dir / PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST
    next_batch_pair_template_path = output_dir / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST
    overlay_payload, overlay_raw = build_provider_manual_overlay_preview(output_dir)
    atomic_write_text(template_path, render_manual_verification_template_csv(payload.get("queue") or []))
    atomic_write_text(pair_template_path, render_pair_entry_template_csv(payload.get("queue") or []))
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_manual_verification_status_markdown(payload))
    pdf_summary = write_manual_verification_status_pdf(payload, pdf_path)
    atomic_write_json(gate_json_path, gate_payload)
    atomic_write_text(gate_md_path, render_manual_hash_gate_markdown(gate_payload))
    gate_pdf_summary = write_manual_hash_gate_pdf(gate_payload, gate_pdf_path)
    atomic_write_json(overlay_raw_path, overlay_raw)
    overlay_payload["overlay_raw_snapshot"] = overlay_raw_path.name
    overlay_payload["overlay_raw_sha256"] = sha256_file(overlay_raw_path)
    overlay_draft = overlay_payload.get("provider_tab_final_verification_overlay_draft") or {}
    overlay_draft["overlay_raw_sha256"] = overlay_payload["overlay_raw_sha256"]
    overlay_payload["provider_tab_final_verification_overlay_draft"] = overlay_draft
    atomic_write_json(overlay_json_path, overlay_payload)
    atomic_write_text(overlay_md_path, render_manual_overlay_preview_markdown(overlay_payload))
    overlay_pdf_summary = write_manual_overlay_preview_pdf(overlay_payload, overlay_pdf_path)
    overlay_payload["artifacts"] = {
        "json": overlay_json_path.name,
        "markdown": overlay_md_path.name,
        "pdf": overlay_pdf_path.name,
        "overlay_raw": overlay_raw_path.name,
        "pdf_summary": overlay_pdf_summary,
    }
    atomic_write_json(overlay_json_path, overlay_payload)
    approval_template = build_overlay_approval_template(overlay_payload)
    overlay_preflight_payload = build_provider_manual_overlay_publish_preflight(output_dir, overlay_payload)
    atomic_write_json(approval_template_path, approval_template)
    atomic_write_json(overlay_preflight_json_path, overlay_preflight_payload)
    atomic_write_text(overlay_preflight_md_path, render_manual_overlay_publish_preflight_markdown(overlay_preflight_payload))
    overlay_preflight_pdf_summary = write_manual_overlay_publish_preflight_pdf(
        overlay_preflight_payload, overlay_preflight_pdf_path
    )
    overlay_preflight_payload["artifacts"] = {
        "json": overlay_preflight_json_path.name,
        "markdown": overlay_preflight_md_path.name,
        "pdf": overlay_preflight_pdf_path.name,
        "approval_template": approval_template_path.name,
        "pdf_summary": overlay_preflight_pdf_summary,
    }
    atomic_write_json(overlay_preflight_json_path, overlay_preflight_payload)
    workbench_payload = build_provider_manual_workbench(
        payload,
        hash_gate=gate_payload,
        overlay_preview=overlay_payload,
        overlay_publish_preflight=overlay_preflight_payload,
    )
    next_batch_rows = (workbench_payload.get("next_batch") or {}).get("rows") or []
    atomic_write_text(next_batch_pair_template_path, render_pair_entry_template_csv(next_batch_rows))
    workbench_payload["pair_templates"] = {
        "all_candidates_csv": pair_template_path.name,
        "next_batch_csv": next_batch_pair_template_path.name,
        "all_candidate_pair_rows": len(payload.get("queue") or []) * 2,
        "next_batch_pair_rows": len(next_batch_rows) * 2,
        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
        "note": "成对模板预留 Over/Under 两行，但核心字段默认留空；人工填写后保存到 import_target。",
    }
    attach_manual_workbench_operator_cockpit(workbench_payload)
    atomic_write_json(workbench_json_path, workbench_payload)
    atomic_write_text(workbench_md_path, render_manual_workbench_markdown(workbench_payload))
    workbench_pdf_summary = write_manual_workbench_pdf(workbench_payload, workbench_pdf_path)
    workbench_payload["artifacts"] = {
        "json": workbench_json_path.name,
        "markdown": workbench_md_path.name,
        "pdf": workbench_pdf_path.name,
        "pdf_summary": workbench_pdf_summary,
    }
    atomic_write_json(workbench_json_path, workbench_payload)
    gate_payload["artifacts"] = {
        "json": gate_json_path.name,
        "markdown": gate_md_path.name,
        "pdf": gate_pdf_path.name,
        "pdf_summary": gate_pdf_summary,
    }
    atomic_write_json(gate_json_path, gate_payload)
    payload["artifacts"] = {
        "template_csv": template_path.name,
        "pair_template_csv": pair_template_path.name,
        "next_batch_pair_template_csv": next_batch_pair_template_path.name,
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
        "hash_gate_json": gate_json_path.name,
        "hash_gate_markdown": gate_md_path.name,
        "hash_gate_pdf": gate_pdf_path.name,
        "overlay_preview_json": overlay_json_path.name,
        "overlay_preview_markdown": overlay_md_path.name,
        "overlay_preview_pdf": overlay_pdf_path.name,
        "overlay_raw_preview": overlay_raw_path.name,
        "overlay_approval_template": approval_template_path.name,
        "overlay_publish_preflight_json": overlay_preflight_json_path.name,
        "overlay_publish_preflight_markdown": overlay_preflight_md_path.name,
        "overlay_publish_preflight_pdf": overlay_preflight_pdf_path.name,
        "manual_workbench_json": workbench_json_path.name,
        "manual_workbench_markdown": workbench_md_path.name,
        "manual_workbench_pdf": workbench_pdf_path.name,
    }
    payload["hash_gate_summary"] = {
        "status": gate_payload.get("status"),
        "manual_import_sha256": gate_payload.get("manual_import_sha256", ""),
        "complete_event_count": (gate_payload.get("completion") or {}).get("complete_event_count", 0),
        "ready_for_manual_signature": bool(gate_payload.get("ready_for_manual_signature")),
        "approved_by_user": False,
    }
    payload["overlay_preview_summary"] = {
        "status": overlay_payload.get("status"),
        "overlay_event_count": overlay_payload.get("overlay_event_count", 0),
        "overlay_row_count": overlay_payload.get("overlay_row_count", 0),
        "overlay_raw_sha256": overlay_payload.get("overlay_raw_sha256", ""),
        "ready_for_publish_preflight": bool(overlay_payload.get("ready_for_publish_preflight")),
        "approved_by_user": False,
    }
    payload["overlay_publish_preflight_summary"] = {
        "status": overlay_preflight_payload.get("status"),
        "overlay_publish_preflight_passed": bool(overlay_preflight_payload.get("overlay_publish_preflight_passed")),
        "approved_by_user": bool(overlay_preflight_payload.get("approved_by_user")),
        "issue_count": len(overlay_preflight_payload.get("issues") or []),
        "formal_publish_allowed": False,
        "current_executable_new_stake_aud": 0,
    }
    payload["manual_workbench_summary"] = {
        "status": workbench_payload.get("status"),
        "batch_count": workbench_payload.get("batch_count", 0),
        "next_batch_id": (workbench_payload.get("next_batch") or {}).get("batch_id", ""),
        "remaining_event_count": workbench_payload.get("remaining_event_count", 0),
        "remaining_high_priority_count": workbench_payload.get("remaining_high_priority_count", 0),
        "pair_template_csv": pair_template_path.name,
        "next_batch_pair_template_csv": next_batch_pair_template_path.name,
        "next_batch_pair_rows": len(next_batch_rows) * 2,
        "current_executable_new_stake_aud": 0,
    }
    atomic_write_json(json_path, payload)
    return payload


def publish_provider_manual_overlay(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    write_provider_manual_verification_bundle(output_dir)
    overlay_preview = load_json(output_dir / PROVIDER_MANUAL_OVERLAY_PREVIEW_JSON_LATEST)
    preflight = load_json(output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PREFLIGHT_JSON_LATEST)
    issues: list[dict[str, str]] = []
    generated_at = datetime.now(REPORT_TZ).isoformat()
    board = BOARD_BY_ID["world_cup_matches"]
    overlay_raw_name = str(overlay_preview.get("overlay_raw_snapshot") or PROVIDER_MANUAL_OVERLAY_RAW_LATEST)
    overlay_raw_path = output_dir / overlay_raw_name
    overlay_raw_sha = sha256_file(overlay_raw_path) or ""
    expected_overlay_sha = str(preflight.get("overlay_raw_sha256") or overlay_preview.get("overlay_raw_sha256") or "")

    if preflight.get("overlay_publish_preflight_passed") is not True:
        issues.append({"field": "preflight", "issue": "manual Team Total overlay publish preflight has not passed"})
    if not overlay_raw_path.exists():
        issues.append({"field": "overlay_raw_snapshot", "issue": f"missing {overlay_raw_name}"})
    if expected_overlay_sha and overlay_raw_sha != expected_overlay_sha:
        issues.append({"field": "overlay_raw_sha256", "issue": "overlay raw sha256 changed after approval"})

    overlay_raw = load_json(overlay_raw_path)
    publish_refresh_id = provider_manual_overlay_publish_refresh_id()
    prepared_raw = prepare_provider_manual_overlay_formal_raw(
        overlay_raw,
        overlay_preview=overlay_preview,
        preflight=preflight,
        refresh_id=publish_refresh_id,
        generated_at=generated_at,
    )
    validation = validate_raw_snapshot(board.board_id, prepared_raw)
    if not validation.get("valid"):
        for error in validation.get("errors") or ["raw validation failed"]:
            issues.append({"field": "raw_validation", "issue": str(error)})

    if issues:
        result = provider_manual_overlay_publish_result(
            generated_at=generated_at,
            status="blocked_overlay_publish_preflight",
            ok=False,
            refresh_id=publish_refresh_id,
            overlay_preview=overlay_preview,
            preflight=preflight,
            destination=board.raw_snapshot or "",
            overlay_raw_sha=overlay_raw_sha,
            destination_sha="",
            issues=issues,
            raw_gate={},
        )
        write_provider_manual_overlay_publish_artifacts(output_dir, result)
        return result

    destination = output_dir / str(board.raw_snapshot)
    atomic_write_json(destination, sanitize_public_payload(prepared_raw))
    raw_gate = audit_staged_raw_refresh(output_dir, expected_refresh_id=publish_refresh_id)
    result = provider_manual_overlay_publish_result(
        generated_at=generated_at,
        status="published_scope_matches_overlay",
        ok=True,
        refresh_id=publish_refresh_id,
        overlay_preview=overlay_preview,
        preflight=preflight,
        destination=board.raw_snapshot or "",
        overlay_raw_sha=overlay_raw_sha,
        destination_sha=sha256_file(destination) or "",
        issues=[],
        raw_gate=raw_gate,
    )
    write_provider_manual_overlay_publish_artifacts(output_dir, result)
    return result


def prepare_provider_manual_overlay_formal_raw(
    raw: Mapping[str, Any],
    *,
    overlay_preview: Mapping[str, Any],
    preflight: Mapping[str, Any],
    refresh_id: str,
    generated_at: str,
) -> dict[str, Any]:
    prepared = dict(raw or {})
    prepared.update(
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "captured_at": raw.get("captured_at") or raw.get("generated_at") or generated_at,
            "source_mode": "provider_manual_team_total_overlay_verified",
            "board_id": "world_cup_matches",
            "refresh_id": refresh_id,
            "overlay_preview_only": False,
            "provider_manual_team_total_overlay_published": True,
            "manual_import_sha256": overlay_preview.get("manual_import_sha256", ""),
            "overlay_raw_snapshot": overlay_preview.get("overlay_raw_snapshot", PROVIDER_MANUAL_OVERLAY_RAW_LATEST),
            "overlay_raw_sha256": overlay_preview.get("overlay_raw_sha256", ""),
            "approval_relative_path": preflight.get("approval_relative_path", DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH),
            "approval_file_sha256": preflight.get("approval_file_sha256", ""),
            "approved_by_user": bool(preflight.get("approved_by_user")),
            "operator_initials": preflight.get("operator_initials", ""),
            "signed_at_aest": preflight.get("signed_at_aest", ""),
            "formal_raw_publish_source": "provider_manual_team_total_overlay_signature_gate",
            "full_automation_allowed": False,
            "current_executable_new_stake_aud": 0,
            "truthfulness_note": (
                "This raw was published from a manually signed Team Total CSV overlay. "
                "It is scope-only Matches raw and does not unlock full automation, My Bets sync, or betting execution."
            ),
        }
    )
    if not isinstance(prepared.get("matches"), list):
        prepared["matches"] = []
    for match in prepared.get("matches") or []:
        if not isinstance(match, dict):
            continue
        preview_meta = match.pop("manual_team_total_overlay_preview", None)
        if preview_meta:
            match["manual_team_total_overlay_verified"] = {
                "row_count": preview_meta.get("row_count", 0) if isinstance(preview_meta, Mapping) else 0,
                "market_family": TEAM_TOTAL_LABEL,
                "approved_by_user": bool(preflight.get("approved_by_user")),
                "formal_publish_allowed": False,
            }
    return prepared


def provider_manual_overlay_publish_result(
    *,
    generated_at: str,
    status: str,
    ok: bool,
    refresh_id: str,
    overlay_preview: Mapping[str, Any],
    preflight: Mapping[str, Any],
    destination: str,
    overlay_raw_sha: str,
    destination_sha: str,
    issues: list[dict[str, str]],
    raw_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return sanitize_public_payload(
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "mode": "provider_manual_team_total_overlay_publish",
            "ok": ok,
            "status": status,
            "scope": "matches",
            "board_id": "world_cup_matches",
            "market_family": TEAM_TOTAL_LABEL,
            "refresh_id": refresh_id,
            "provider_refresh_id": overlay_preview.get("refresh_id", ""),
            "manual_import_sha256": overlay_preview.get("manual_import_sha256", ""),
            "overlay_raw_snapshot": overlay_preview.get("overlay_raw_snapshot", ""),
            "overlay_raw_sha256": overlay_raw_sha,
            "overlay_event_count": overlay_preview.get("overlay_event_count", 0),
            "overlay_row_count": overlay_preview.get("overlay_row_count", 0),
            "approval_relative_path": preflight.get("approval_relative_path", DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH),
            "approval_file_sha256": preflight.get("approval_file_sha256", ""),
            "published_raw_snapshot": destination if ok else "",
            "published_raw_sha256": destination_sha,
            "formal_raw_publish_performed": ok,
            "full_automation_allowed": False,
            "raw_batch_manifest_written": False,
            "raw_batch_manifest": RAW_BATCH_MANIFEST,
            "raw_gate_ready": bool(raw_gate.get("staged_raw_ready")),
            "raw_gate": raw_gate,
            "current_executable_new_stake_aud": 0,
            "issues": issues[:50],
            "next_safe_action": provider_manual_overlay_publish_next_action(status),
            "truthfulness_note": (
                "Manual Team Total overlay publish is an explicit signature-gated path for Matches raw only. "
                "It does not prove live TAB page access, does not write a 5-board batch manifest, and does not allow betting execution."
            ),
        }
    )


def provider_manual_overlay_publish_next_action(status: str) -> str:
    if status == "published_scope_matches_overlay":
        return "Team Total overlay 已通过人工签名并发布到 Matches raw slot；继续补 My Bets、Australia Markets 和完整 batch gate。"
    return "先完成 Team Total CSV 导入、overlay raw 预览和人工签名预检；发布失败时不要手工复制 overlay raw 到正式 raw。"


def write_provider_manual_overlay_publish_artifacts(output_dir: Path, payload: Mapping[str, Any]) -> None:
    output_dir = Path(output_dir)
    json_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_JSON_LATEST
    md_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_MD_LATEST
    pdf_path = output_dir / PROVIDER_MANUAL_OVERLAY_PUBLISH_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_manual_overlay_publish_markdown(payload))
    pdf_summary = write_manual_overlay_publish_pdf(payload, pdf_path)
    next_payload = dict(payload)
    next_payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, sanitize_public_payload(next_payload))


def provider_manual_overlay_publish_refresh_id() -> str:
    return f"{datetime.now(REPORT_TZ).strftime('%Y%m%dT%H%M%S%z')}-manual-overlay"


def build_provider_manual_hash_gate(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    target = first_matches_target(coverage)
    raw = load_staged_matches_raw(output_dir, target)
    matches = [item for item in raw.get("matches") or [] if isinstance(item, Mapping)]
    queue = build_verification_queue(matches)
    import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
    import_rows, import_errors = read_import_rows(import_path)
    audit = audit_import_rows(queue, import_rows, import_errors)
    canonical_rows = audit.get("canonical_complete_rows") or []
    digest = canonical_rows_sha256(canonical_rows) if canonical_rows else ""
    status = hash_gate_status(audit, import_path.exists())
    completion = audit["completion"]
    ready_for_manual_signature = status in {"ready_partial_manual_hash", "ready_full_manual_hash"}
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_manual_hash_gate",
        "status": status,
        "refresh_id": coverage.get("refresh_id", ""),
        "scope": coverage.get("scope", "matches"),
        "board_id": "world_cup_matches",
        "market_family": TEAM_TOTAL_LABEL,
        "import_file": Path(DEFAULT_IMPORT_RELATIVE_PATH).name,
        "import_relative_path": DEFAULT_IMPORT_RELATIVE_PATH,
        "import_file_sha256": sha256_file(import_path) if import_path.exists() else "",
        "manual_import_sha256": digest,
        "canonical_row_count": len(canonical_rows),
        "completion": {
            key: completion.get(key)
            for key in [
                "valid_row_count",
                "invalid_row_count",
                "complete_event_count",
                "partial_event_count",
                "queue_count",
                "completion_pct",
                "high_priority_complete_count",
                "high_priority_count",
                "high_priority_completion_pct",
            ]
        },
        "complete_event_ids_sample": audit.get("verified_event_ids", [])[:20],
        "invalid_rows": audit.get("invalid_rows", [])[:20],
        "import_quality_summary": import_quality_summary(audit.get("import_quality") or {}),
        "ready_for_manual_signature": ready_for_manual_signature,
        "provider_tab_final_verification_draft": provider_tab_final_verification_draft(
            coverage=coverage,
            digest=digest,
            completion=completion,
            ready_for_manual_signature=ready_for_manual_signature,
        ),
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "recommended_next_action": hash_gate_next_action(status, completion),
        "truthfulness_note": (
            "该 hash gate 只证明人工导入 CSV 的规范化内容可复核；不证明 TAB 盘口真实性，"
            "不替代 provider raw sha256 publish gate，不自动设置 approved_by_user。"
        ),
    }
    return sanitize_public_payload(payload)


def build_provider_manual_verification_status(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    target = first_matches_target(coverage)
    raw = load_staged_matches_raw(output_dir, target)
    matches = [item for item in raw.get("matches") or [] if isinstance(item, Mapping)]
    queue = build_verification_queue(matches)
    import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
    import_rows, import_errors = read_import_rows(import_path)
    audit = audit_import_rows(queue, import_rows, import_errors)
    status = status_from_audit(audit, import_path.exists())
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_manual_verification_import",
        "status": status,
        "refresh_id": coverage.get("refresh_id", ""),
        "scope": coverage.get("scope", "matches"),
        "queue_count": len(queue),
        "high_priority_count": len([row for row in queue if row.get("priority_tier") == "high"]),
        "import_file": Path(DEFAULT_IMPORT_RELATIVE_PATH).name,
        "import_relative_path": DEFAULT_IMPORT_RELATIVE_PATH,
        "template_fields": CSV_FIELDS,
        "completion": audit["completion"],
        "verified_event_ids": audit["verified_event_ids"],
        "partial_event_ids": audit["partial_event_ids"],
        "verified_event_ids_sample": audit["verified_event_ids"][:20],
        "partial_event_ids_sample": audit["partial_event_ids"][:20],
        "invalid_rows": audit["invalid_rows"][:20],
        "import_quality": audit.get("import_quality") or {},
        "queue": queue,
        "manual_workflow": {
            "step_1": "下载 provider_manual_verification_template_latest.csv。",
            "step_2": f"人工只读 TAB，填写 Team Total 行后保存到 outputs/{DEFAULT_IMPORT_RELATIVE_PATH}。",
            "step_3": "重建 app 或运行主动测试，检查 provider_manual_verification_status_latest.json。",
            "step_4": "完成候选只进入 hash gate；未通过 formal publish 前 stake 保持 AUD 0。",
        },
        "recommended_next_action": recommended_next_action(status, audit),
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "truthfulness_note": (
            "该状态只验证人工填写文件是否结构完整；不证明 TAB 盘口真实性，不自动登录 TAB、不点击赔率、不下注。"
        ),
    }
    return sanitize_public_payload(payload)


def build_provider_manual_overlay_preview(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    output_dir = Path(output_dir)
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    target = first_matches_target(coverage)
    raw = load_staged_matches_raw(output_dir, target)
    matches = [item for item in raw.get("matches") or [] if isinstance(item, Mapping)]
    queue = build_verification_queue(matches)
    import_path = output_dir / DEFAULT_IMPORT_RELATIVE_PATH
    import_rows, import_errors = read_import_rows(import_path)
    audit = audit_import_rows(queue, import_rows, import_errors)
    completion = audit["completion"]
    canonical_rows = audit.get("canonical_complete_rows") or []
    status = manual_overlay_status(audit, import_path.exists())
    grouped_rows = rows_by_event(canonical_rows) if status in {"overlay_preview_partial", "overlay_preview_full"} else {}
    overlay_raw = build_manual_overlay_raw(
        raw=raw,
        coverage=coverage,
        grouped_rows=grouped_rows,
        status=status,
        completion=completion,
    )
    overlay_event_count = len(grouped_rows)
    overlay_row_count = sum(len(rows) for rows in grouped_rows.values())
    manual_import_sha = canonical_rows_sha256(canonical_rows) if canonical_rows else ""
    ready_for_publish_preflight = overlay_event_count > 0 and completion.get("invalid_row_count", 0) == 0
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_manual_team_total_overlay_preview",
        "status": status,
        "refresh_id": coverage.get("refresh_id", ""),
        "scope": coverage.get("scope", "matches"),
        "board_id": "world_cup_matches",
        "market_family": TEAM_TOTAL_LABEL,
        "import_file": Path(DEFAULT_IMPORT_RELATIVE_PATH).name,
        "import_relative_path": DEFAULT_IMPORT_RELATIVE_PATH,
        "manual_import_sha256": manual_import_sha,
        "overlay_event_count": overlay_event_count,
        "overlay_row_count": overlay_row_count,
        "team_total_overlay_count": overlay_event_count,
        "completion": {
            key: completion.get(key)
            for key in [
                "valid_row_count",
                "invalid_row_count",
                "complete_event_count",
                "partial_event_count",
                "queue_count",
                "completion_pct",
                "high_priority_complete_count",
                "high_priority_count",
                "high_priority_completion_pct",
            ]
        },
        "overlaid_event_ids_sample": sorted(grouped_rows.keys())[:20],
        "invalid_rows": audit.get("invalid_rows", [])[:20],
        "import_quality_summary": import_quality_summary(audit.get("import_quality") or {}),
        "ready_for_publish_preflight": ready_for_publish_preflight,
        "overlay_preview_only": True,
        "provider_tab_final_verification_overlay_draft": {
            "schema_version": 1,
            "mode": "provider_tab_final_verification_overlay_preview_draft",
            "refresh_id": coverage.get("refresh_id", ""),
            "board_id": "world_cup_matches",
            "market_family": TEAM_TOTAL_LABEL,
            "manual_import_sha256": manual_import_sha,
            "overlay_raw_sha256": "",
            "overlay_event_count": overlay_event_count,
            "approved_by_user": False,
            "operator_signature_required": True,
            "publish_compatible_with_provider_raw": False,
            "note": "这是 Team Total overlay raw 预览草案，不是正式 provider raw publish approval；不能用于自动下注或自动发布。",
        },
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "recommended_next_action": manual_overlay_next_action(status, completion),
        "truthfulness_note": (
            "该 overlay 只把已通过结构校验的人工 Team Total CSV 合入一个 preview-only raw；"
            "不覆盖正式 raw，不证明 TAB 盘口真实性，不设置 approved_by_user，不生成新增可执行下注金额。"
        ),
    }
    return sanitize_public_payload(payload), sanitize_public_payload(overlay_raw)


def build_manual_overlay_raw(
    *,
    raw: Mapping[str, Any],
    coverage: Mapping[str, Any],
    grouped_rows: Mapping[str, list[Mapping[str, Any]]],
    status: str,
    completion: Mapping[str, Any],
) -> dict[str, Any]:
    base = json.loads(json.dumps(raw, ensure_ascii=False)) if raw and grouped_rows else {}
    if not base:
        return {
            "schema_version": 1,
            "generated_at": datetime.now(REPORT_TZ).isoformat(),
            "refresh_id": coverage.get("refresh_id", ""),
            "source_mode": "provider_manual_team_total_overlay_preview",
            "overlay_preview_only": True,
            "status": status,
            "board": "world_cup_matches",
            "market_family": TEAM_TOTAL_LABEL,
            "matches": [],
            "team_total_overlay_event_count": 0,
            "team_total_overlay_row_count": 0,
            "formal_publish_allowed": False,
            "full_automation_allowed": False,
            "current_executable_new_stake_aud": 0,
            "blocked_reason": manual_overlay_next_action(status, completion),
            "truthfulness_note": "没有完整人工导入行时不生成可用 overlay matches；该文件只保留为预览状态 envelope。",
        }
    overlay_count = 0
    overlay_row_count = 0
    for match in base.get("matches") or []:
        if not isinstance(match, dict):
            continue
        event_id = str(match.get("provider_event_id") or "")
        rows = grouped_rows.get(event_id)
        if not rows:
            continue
        markets = match.get("markets") if isinstance(match.get("markets"), dict) else {}
        markets[TEAM_TOTAL_LABEL] = render_team_total_market_text(rows, str(match.get("match") or ""))
        match["markets"] = markets
        kinds = list(dict.fromkeys([*list(match.get("provider_request_kinds") or []), "manual_team_total_overlay_preview"]))
        match["provider_request_kinds"] = kinds
        match["manual_team_total_overlay_preview"] = {
            "row_count": len(rows),
            "market_family": TEAM_TOTAL_LABEL,
            "approved_by_user": False,
            "formal_publish_allowed": False,
        }
        overlay_count += 1
        overlay_row_count += len(rows)
    base["source_mode"] = "provider_manual_team_total_overlay_preview"
    base["overlay_preview_only"] = True
    base["status"] = status
    base["market_family"] = TEAM_TOTAL_LABEL
    base["team_total_overlay_event_count"] = overlay_count
    base["team_total_overlay_row_count"] = overlay_row_count
    base["formal_publish_allowed"] = False
    base["full_automation_allowed"] = False
    base["current_executable_new_stake_aud"] = 0
    base["truthfulness_note"] = (
        "Manual Team Total overlay preview only. This is not official provider raw, not TAB proof, "
        "not approved_by_user, and not an executable betting signal."
    )
    return base


def render_team_total_market_text(rows: list[Mapping[str, Any]], match_name: str) -> str:
    lines = [TEAM_TOTAL_LABEL]
    for row in sorted(rows, key=team_total_row_sort_key):
        lines.append(team_total_selection_label(row, match_name))
        lines.append(str(row.get("decimal_odds") or ""))
    return "\n".join(lines) + "\n"


def team_total_row_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    selection = str(row.get("selection_name") or "").lower()
    if "over" in selection:
        direction_rank = 0
    elif "under" in selection:
        direction_rank = 1
    else:
        direction_rank = 2
    try:
        line_value = float(str(row.get("line") or "999").replace("+", ""))
    except ValueError:
        line_value = 999.0
    return (str(row.get("team_scope") or ""), line_value, direction_rank, selection)


def team_total_selection_label(row: Mapping[str, Any], match_name: str) -> str:
    selection = normalize_text(row.get("selection_name"))
    direction = team_total_direction(selection)
    line = normalize_text(row.get("line"))
    team = team_total_team_name(match_name, str(row.get("team_scope") or ""))
    selection_lower = selection.lower()
    if direction and ("goal" not in selection_lower or line not in selection):
        if team and team.lower() not in selection_lower:
            return f"{team} {direction} {line} Goals".strip()
        if line and line not in selection:
            return f"{selection} {line} Goals".strip()
    return selection


def team_total_direction(selection: str) -> str:
    lower = selection.lower()
    if "over" in lower:
        return "Over"
    if "under" in lower:
        return "Under"
    return ""


def team_total_team_name(match_name: str, team_scope: str) -> str:
    parts = [part.strip() for part in match_name.split(" v ", 1)]
    scope = team_scope.lower().strip()
    if scope in {"home", "home team", "team_home", "home_team"} and len(parts) == 2:
        return parts[0]
    if scope in {"away", "away team", "team_away", "away_team"} and len(parts) == 2:
        return parts[1]
    if team_scope:
        return normalize_text(team_scope)
    return parts[0] if parts else ""


def rows_by_event(rows: list[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        event_id = str(row.get("event_id") or "")
        if event_id:
            grouped.setdefault(event_id, []).append(row)
    return grouped


def manual_overlay_status(audit: Mapping[str, Any], import_exists: bool) -> str:
    completion = audit.get("completion") or {}
    if not import_exists:
        return "waiting_for_import"
    if completion.get("invalid_row_count", 0):
        return "blocked_import_errors"
    if completion.get("complete_event_count", 0) <= 0:
        return "waiting_for_complete_pairs"
    if completion.get("complete_event_count", 0) < completion.get("queue_count", 0):
        return "overlay_preview_partial"
    return "overlay_preview_full"


def manual_overlay_next_action(status: str, completion: Mapping[str, Any]) -> str:
    if status == "waiting_for_import":
        return "等待人工导入 Team Total CSV；当前 overlay raw 只生成空预览 envelope。"
    if status == "blocked_import_errors":
        return f"先修复 {completion.get('invalid_row_count', 0)} 行导入错误，再生成 overlay raw 预览。"
    if status == "waiting_for_complete_pairs":
        return "至少补齐一个候选的 Over/Under 成对记录后，才能生成 Team Total overlay raw 预览。"
    if status == "overlay_preview_partial":
        return "已有部分 Team Total 可合入 preview raw；继续补高优先级，并在正式发布前人工签名复核。"
    return "所有 Team Total 候选已合入 preview raw；仍需人工签名与正式 publish gate，不自动下注。"


def build_overlay_approval_template(overlay_payload: Mapping[str, Any]) -> dict[str, Any]:
    return sanitize_public_payload(
        {
            "schema_version": 1,
            "mode": "provider_manual_team_total_overlay_approval",
            "refresh_id": overlay_payload.get("refresh_id", ""),
            "board_id": "world_cup_matches",
            "market_family": TEAM_TOTAL_LABEL,
            "manual_import_sha256": overlay_payload.get("manual_import_sha256", ""),
            "overlay_raw_sha256": overlay_payload.get("overlay_raw_sha256", ""),
            "overlay_event_count": overlay_payload.get("overlay_event_count", 0),
            "approved_by_user": False,
            "operator_initials": "",
            "signed_at_aest": "",
            "evidence_note_or_screenshot_ref": "",
            "approval_scope": "只确认人工 Team Total CSV 与 overlay raw hash 匹配；不自动发布、不自动下注。",
            "save_as": DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH,
        }
    )


def build_provider_manual_overlay_publish_preflight(output_dir: Path, overlay_payload: Mapping[str, Any]) -> dict[str, Any]:
    output_dir = Path(output_dir)
    approval_path = output_dir / DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH
    approval_exists = approval_path.exists()
    approval = load_json(approval_path) if approval_exists else {}
    status, issues = overlay_publish_preflight_status(overlay_payload, approval, approval_exists)
    passed = status == "ready_for_overlay_publish_preflight"
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_manual_team_total_overlay_publish_preflight",
        "status": status,
        "refresh_id": overlay_payload.get("refresh_id", ""),
        "board_id": "world_cup_matches",
        "market_family": TEAM_TOTAL_LABEL,
        "approval_file": Path(DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH).name,
        "approval_relative_path": DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH,
        "approval_file_sha256": sha256_file(approval_path) if approval_exists else "",
        "manual_import_sha256": overlay_payload.get("manual_import_sha256", ""),
        "overlay_raw_snapshot": overlay_payload.get("overlay_raw_snapshot", ""),
        "overlay_raw_sha256": overlay_payload.get("overlay_raw_sha256", ""),
        "overlay_event_count": overlay_payload.get("overlay_event_count", 0),
        "overlay_row_count": overlay_payload.get("overlay_row_count", 0),
        "approved_by_user": bool(approval.get("approved_by_user") is True),
        "operator_initials": str(approval.get("operator_initials") or ""),
        "signed_at_aest": str(approval.get("signed_at_aest") or ""),
        "issues": issues,
        "overlay_publish_preflight_passed": passed,
        "publish_compatible_with_provider_raw": passed,
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "next_safe_action": overlay_publish_preflight_next_action(status, issues),
        "truthfulness_note": (
            "该预检只验证人工签名文件与 overlay preview hash 是否匹配；即使通过，也只是进入后续显式 publish 流程的前置条件。"
            "它不会自动覆盖正式 raw，不会解锁自动下注。"
        ),
    }
    return sanitize_public_payload(payload)


def overlay_publish_preflight_status(
    overlay_payload: Mapping[str, Any],
    approval: Mapping[str, Any],
    approval_exists: bool,
) -> tuple[str, list[dict[str, str]]]:
    overlay_status = str(overlay_payload.get("status") or "")
    if overlay_status in {"waiting_for_import", "waiting_for_complete_pairs"}:
        return overlay_status, [{"field": "overlay", "issue": "overlay raw preview is not ready"}]
    if overlay_status == "blocked_import_errors":
        return "blocked_import_errors", [{"field": "overlay", "issue": "manual import has invalid rows"}]
    if not approval_exists:
        return "waiting_for_signature", [{"field": "approval_file", "issue": f"missing {DEFAULT_OVERLAY_APPROVAL_RELATIVE_PATH}"}]
    issues = validate_overlay_approval(overlay_payload, approval)
    if issues:
        return "blocked_signature_mismatch", issues
    return "ready_for_overlay_publish_preflight", []


def validate_overlay_approval(overlay_payload: Mapping[str, Any], approval: Mapping[str, Any]) -> list[dict[str, str]]:
    checks = [
        ("refresh_id", str(overlay_payload.get("refresh_id") or "")),
        ("board_id", "world_cup_matches"),
        ("market_family", TEAM_TOTAL_LABEL),
        ("manual_import_sha256", str(overlay_payload.get("manual_import_sha256") or "")),
        ("overlay_raw_sha256", str(overlay_payload.get("overlay_raw_sha256") or "")),
    ]
    issues: list[dict[str, str]] = []
    for field, expected in checks:
        actual = str(approval.get(field) or "")
        if actual != expected:
            issues.append({"field": field, "issue": f"expected {expected or '<empty>'}, got {actual or '<empty>'}"})
    if approval.get("approved_by_user") is not True:
        issues.append({"field": "approved_by_user", "issue": "must be true"})
    for field in ["operator_initials", "signed_at_aest"]:
        if not str(approval.get(field) or "").strip():
            issues.append({"field": field, "issue": "required"})
    return issues


def overlay_publish_preflight_next_action(status: str, issues: list[Mapping[str, Any]]) -> str:
    if status in {"waiting_for_import", "waiting_for_complete_pairs"}:
        return "先完成 Team Total 人工 CSV 导入并生成非空 overlay raw 预览。"
    if status == "blocked_import_errors":
        return "先修复人工 CSV 导入错误，再生成 overlay publish 预检。"
    if status == "waiting_for_signature":
        return "下载 approval template，人工核对 overlay raw hash 后保存到 manual_verification/provider_team_total_overlay_approval.json。"
    if status == "blocked_signature_mismatch":
        fields = ", ".join(str(item.get("field") or "") for item in issues[:5])
        return f"签名文件与当前 overlay 不匹配；先修复字段：{fields}。"
    return "签名和 overlay hash 匹配；下一步可由显式 publish 命令设计/执行正式 raw merge gate，当前仍不自动下注。"


def render_manual_verification_template_csv(queue: list[Mapping[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in queue:
        writer.writerow(
            {
                "event_id": row.get("event_id", ""),
                "rank": row.get("rank", ""),
                "match": row.get("match", ""),
                "commence_time": row.get("commence_time", ""),
                "priority_tier": row.get("priority_tier", ""),
                "missing_market": TEAM_TOTAL_LABEL,
                "tab_match_name": "",
                "team_scope": "",
                "tab_market_name": "",
                "selection_name": "",
                "line": "",
                "decimal_odds": "",
                "observed_at_aest": "",
                "operator_initials": "",
                "evidence_note_or_screenshot_ref": "",
                "verification_status": "pending",
            }
        )
    return buffer.getvalue()


def render_pair_entry_template_csv(queue: list[Mapping[str, Any]]) -> str:
    fieldnames = [*CSV_FIELDS, "entry_slot", "direction_hint", "manual_instruction"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in queue:
        for direction in ("Over", "Under"):
            writer.writerow(
                {
                    "event_id": row.get("event_id", ""),
                    "rank": row.get("rank", ""),
                    "match": row.get("match", ""),
                    "commence_time": row.get("commence_time", ""),
                    "priority_tier": row.get("priority_tier", ""),
                    "missing_market": TEAM_TOTAL_LABEL,
                    "tab_match_name": "",
                    "team_scope": "",
                    "tab_market_name": "",
                    "selection_name": "",
                    "line": "",
                    "decimal_odds": "",
                    "observed_at_aest": "",
                    "operator_initials": "",
                    "evidence_note_or_screenshot_ref": "",
                    "verification_status": "pending",
                    "entry_slot": f"{direction.lower()}_leg",
                    "direction_hint": direction,
                    "manual_instruction": (
                        f"填写同一 team_scope 和 line 的 {direction} 选择、decimal_odds、observed_at_aest；"
                        "完成后把 verification_status 改为 verified。"
                    ),
                }
            )
    return buffer.getvalue()


def read_import_rows(path: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [{str(key or ""): str(value or "").strip() for key, value in row.items()} for row in reader]
    except Exception as exc:
        return [], [{"row_number": 0, "issue": f"cannot_read_csv: {str(exc).splitlines()[0][:120]}"}]
    missing = [field for field in CSV_FIELDS if field not in (reader.fieldnames or [])]
    if missing:
        return rows, [{"row_number": 0, "issue": f"missing_columns: {', '.join(missing)}"}]
    return rows, []


def audit_import_rows(
    queue: list[Mapping[str, Any]],
    import_rows: list[Mapping[str, str]],
    import_errors: list[Mapping[str, Any]],
) -> dict[str, Any]:
    queue_ids = {str(row.get("event_id") or "") for row in queue if row.get("event_id")}
    priority_by_event = {str(row.get("event_id") or ""): str(row.get("priority_tier") or "watch") for row in queue}
    queue_by_event = {str(row.get("event_id") or ""): row for row in queue if row.get("event_id")}
    valid_rows_by_event: dict[str, list[Mapping[str, str]]] = {}
    invalid_rows = [dict(row) for row in import_errors]
    for row_number, row in enumerate(import_rows, start=2):
        if is_blank_template_seed(row):
            continue
        event_id = str(row.get("event_id") or "")
        issues = validate_import_row(row, queue_ids)
        if issues:
            invalid_rows.append({"row_number": row_number, "event_id": event_id, "issue": "; ".join(issues)})
            continue
        valid_rows_by_event.setdefault(event_id, []).append(row)
    complete_event_ids = []
    partial_event_ids = []
    for event_id, rows in valid_rows_by_event.items():
        selections = {str(row.get("selection_name") or "").lower() for row in rows}
        has_over = any("over" in value for value in selections)
        has_under = any("under" in value for value in selections)
        if len(rows) >= 2 and has_over and has_under:
            complete_event_ids.append(event_id)
        else:
            partial_event_ids.append(event_id)
    high_priority_ids = {event_id for event_id, tier in priority_by_event.items() if tier == "high"}
    high_complete = len([event_id for event_id in complete_event_ids if event_id in high_priority_ids])
    completion = {
        "valid_row_count": sum(len(rows) for rows in valid_rows_by_event.values()),
        "invalid_row_count": len(invalid_rows),
        "complete_event_count": len(complete_event_ids),
        "partial_event_count": len(partial_event_ids),
        "queue_count": len(queue),
        "completion_pct": len(complete_event_ids) / len(queue) if queue else 1.0,
        "high_priority_complete_count": high_complete,
        "high_priority_count": len(high_priority_ids),
        "high_priority_completion_pct": high_complete / len(high_priority_ids) if high_priority_ids else 1.0,
    }
    return {
        "completion": completion,
        "verified_event_ids": sorted(complete_event_ids),
        "partial_event_ids": sorted(partial_event_ids),
        "invalid_rows": invalid_rows,
        "import_quality": build_import_quality(
            queue=queue,
            import_rows=import_rows,
            import_errors=import_errors,
            valid_rows_by_event=valid_rows_by_event,
            invalid_rows=invalid_rows,
            complete_event_ids=complete_event_ids,
            partial_event_ids=partial_event_ids,
        ),
        "canonical_complete_rows": canonical_complete_rows(valid_rows_by_event, complete_event_ids, queue_by_event),
    }


def build_import_quality(
    *,
    queue: list[Mapping[str, Any]],
    import_rows: list[Mapping[str, str]],
    import_errors: list[Mapping[str, Any]],
    valid_rows_by_event: Mapping[str, list[Mapping[str, str]]],
    invalid_rows: list[Mapping[str, Any]],
    complete_event_ids: list[str],
    partial_event_ids: list[str],
) -> dict[str, Any]:
    nonblank_rows = [row for row in import_rows if not is_blank_template_seed(row)]
    raw_rows_by_event: dict[str, list[Mapping[str, str]]] = {}
    for row in nonblank_rows:
        event_id = str(row.get("event_id") or "").strip()
        if event_id:
            raw_rows_by_event.setdefault(event_id, []).append(row)
    invalid_by_event: dict[str, list[str]] = {}
    for row in invalid_rows:
        event_id = str(row.get("event_id") or "").strip()
        issue = str(row.get("issue") or "").strip()
        if event_id and issue:
            invalid_by_event.setdefault(event_id, []).append(issue)
    complete_ids = set(complete_event_ids)
    partial_ids = set(partial_event_ids)
    field_counts = {field: 0 for field in QUALITY_REQUIRED_FIELDS}
    direction_counts = {"over": 0, "under": 0}
    event_rows = []
    for queue_row in queue:
        event_id = str(queue_row.get("event_id") or "").strip()
        raw_rows = raw_rows_by_event.get(event_id, [])
        valid_rows = list(valid_rows_by_event.get(event_id) or [])
        missing_fields = missing_quality_fields(raw_rows)
        directions = selection_directions(valid_rows)
        for field in QUALITY_REQUIRED_FIELDS:
            if any(str(row.get(field) or "").strip() for row in raw_rows):
                field_counts[field] += 1
        for direction in directions:
            direction_counts[direction] += 1
        if event_id in complete_ids:
            status = "complete_pair"
        elif invalid_by_event.get(event_id):
            status = "invalid_rows"
        elif event_id in partial_ids or raw_rows:
            status = "partial_or_incomplete"
        else:
            status = "missing_rows"
        missing_directions = [direction for direction in ("over", "under") if direction not in directions]
        event_rows.append(
            {
                "event_id": event_id,
                "rank": queue_row.get("rank", ""),
                "match": queue_row.get("match", ""),
                "commence_time": queue_row.get("commence_time", ""),
                "priority_tier": queue_row.get("priority_tier", ""),
                "status": status,
                "raw_row_count": len(raw_rows),
                "valid_row_count": len(valid_rows),
                "missing_fields": missing_fields,
                "missing_directions": missing_directions,
                "invalid_issues": invalid_by_event.get(event_id, [])[:4],
                "next_action": import_quality_event_next_action(status, missing_fields, missing_directions),
            }
        )
    queue_count = len(queue)
    missing_count = sum(1 for row in event_rows if row["status"] == "missing_rows")
    partial_count = sum(1 for row in event_rows if row["status"] == "partial_or_incomplete")
    invalid_event_count = sum(1 for row in event_rows if row["status"] == "invalid_rows")
    complete_count = sum(1 for row in event_rows if row["status"] == "complete_pair")
    field_coverage = [
        {
            "field": field,
            "filled_event_count": count,
            "missing_event_count": max(0, queue_count - count),
            "coverage_pct": count / queue_count if queue_count else 1.0,
        }
        for field, count in field_counts.items()
    ]
    return {
        "schema_version": 1,
        "status": import_quality_status(missing_count, partial_count, invalid_event_count, complete_count, queue_count),
        "queue_count": queue_count,
        "import_row_count": len(nonblank_rows),
        "import_error_count": len(import_errors),
        "complete_event_count": complete_count,
        "partial_event_count": partial_count,
        "invalid_event_count": invalid_event_count,
        "missing_event_count": missing_count,
        "field_coverage": field_coverage,
        "direction_coverage": {
            "over_event_count": direction_counts["over"],
            "under_event_count": direction_counts["under"],
            "complete_direction_pair_count": complete_count,
        },
        "event_quality": event_rows,
        "event_quality_sample": event_rows[:20],
        "next_action": import_quality_next_action(missing_count, partial_count, invalid_event_count, complete_count, queue_count),
    }


def missing_quality_fields(rows: list[Mapping[str, str]]) -> list[str]:
    if not rows:
        return list(QUALITY_REQUIRED_FIELDS)
    missing = []
    for field in QUALITY_REQUIRED_FIELDS:
        if not any(str(row.get(field) or "").strip() for row in rows):
            missing.append(field)
    return missing


def selection_directions(rows: list[Mapping[str, str]]) -> set[str]:
    directions: set[str] = set()
    for row in rows:
        selection = str(row.get("selection_name") or "").lower()
        if "over" in selection:
            directions.add("over")
        if "under" in selection:
            directions.add("under")
    return directions


def import_quality_status(
    missing_count: int,
    partial_count: int,
    invalid_event_count: int,
    complete_count: int,
    queue_count: int,
) -> str:
    if invalid_event_count:
        return "blocked_invalid_rows"
    if complete_count == queue_count and queue_count:
        return "complete_quality_ready_for_hash_gate"
    if complete_count:
        return "partial_quality_ready"
    if partial_count:
        return "partial_quality_missing_pairs"
    if missing_count:
        return "waiting_for_manual_rows"
    return "no_queue"


def import_quality_next_action(
    missing_count: int,
    partial_count: int,
    invalid_event_count: int,
    complete_count: int,
    queue_count: int,
) -> str:
    if invalid_event_count:
        return f"先修复 {invalid_event_count} 场的无效行，再继续补齐 Over/Under 成对记录。"
    if complete_count == queue_count and queue_count:
        return "全部候选均已形成质量合格的 Over/Under 成对记录；下一步复核 hash gate 和签名。"
    if complete_count:
        return f"{complete_count} 场已合格；继续补齐剩余缺口，优先 high priority。"
    if partial_count:
        return f"{partial_count} 场已有部分行；补齐缺失字段和 Over/Under 另一边。"
    if missing_count:
        return "当前未检测到人工行；从 TT-001 下一批成对模板开始填写。"
    return "当前无 Team Total 人工队列。"


def import_quality_event_next_action(status: str, missing_fields: list[str], missing_directions: list[str]) -> str:
    if status == "complete_pair":
        return "已形成 Over/Under 成对记录；进入 hash/overlay 复核。"
    if status == "invalid_rows":
        return "先修复该场无效行。"
    parts = []
    if missing_fields:
        parts.append("补字段 " + ", ".join(missing_fields[:4]))
    if missing_directions:
        parts.append("补方向 " + "/".join(missing_directions))
    return "；".join(parts) or "补齐同一 line 的 Over/Under 成对记录。"


def import_quality_summary(quality: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": quality.get("status", "missing"),
        "queue_count": quality.get("queue_count", 0),
        "import_row_count": quality.get("import_row_count", 0),
        "complete_event_count": quality.get("complete_event_count", 0),
        "partial_event_count": quality.get("partial_event_count", 0),
        "invalid_event_count": quality.get("invalid_event_count", 0),
        "missing_event_count": quality.get("missing_event_count", 0),
        "next_action": quality.get("next_action", ""),
    }


def canonical_complete_rows(
    valid_rows_by_event: Mapping[str, list[Mapping[str, str]]],
    complete_event_ids: list[str],
    queue_by_event: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for event_id in sorted(complete_event_ids):
        queue_row = queue_by_event.get(event_id) or {}
        for row in valid_rows_by_event.get(event_id) or []:
            rows.append(
                {
                    "event_id": event_id,
                    "provider_match": str(queue_row.get("match") or row.get("match") or ""),
                    "commence_time": str(queue_row.get("commence_time") or row.get("commence_time") or ""),
                    "priority_tier": str(queue_row.get("priority_tier") or row.get("priority_tier") or ""),
                    "tab_match_name": normalize_text(row.get("tab_match_name")),
                    "team_scope": normalize_text(row.get("team_scope")).lower(),
                    "tab_market_name": normalize_text(row.get("tab_market_name")),
                    "selection_name": normalize_text(row.get("selection_name")),
                    "line": normalize_text(row.get("line")),
                    "decimal_odds": normalize_decimal_text(row.get("decimal_odds")),
                    "observed_at_aest": normalize_text(row.get("observed_at_aest")),
                    "evidence_note_or_screenshot_ref": normalize_text(row.get("evidence_note_or_screenshot_ref")),
                    "verification_status": normalize_text(row.get("verification_status")).lower(),
                }
            )
    rows.sort(
        key=lambda item: (
            item["event_id"],
            item["team_scope"],
            item["selection_name"].lower(),
            item["line"],
            item["decimal_odds"],
        )
    )
    return rows


def canonical_rows_sha256(rows: list[Mapping[str, Any]]) -> str:
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def provider_tab_final_verification_draft(
    *,
    coverage: Mapping[str, Any],
    digest: str,
    completion: Mapping[str, Any],
    ready_for_manual_signature: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mode": "provider_tab_final_verification_manual_import_draft",
        "refresh_id": coverage.get("refresh_id", ""),
        "board_id": "world_cup_matches",
        "market_family": TEAM_TOTAL_LABEL,
        "manual_import_sha256": digest,
        "complete_event_count": completion.get("complete_event_count", 0),
        "high_priority_complete_count": completion.get("high_priority_complete_count", 0),
        "approved_by_user": False,
        "operator_signature_required": True,
        "ready_for_manual_signature": ready_for_manual_signature,
        "publish_compatible_with_provider_raw": False,
        "note": "这是人工导入 hash gate 草案，不是 provider raw publish approvals；不能直接传给 --verification-file 发布 raw。",
    }


def hash_gate_status(audit: Mapping[str, Any], import_exists: bool) -> str:
    completion = audit.get("completion") or {}
    if not import_exists:
        return "waiting_for_import"
    if completion.get("invalid_row_count", 0):
        return "blocked_import_errors"
    if completion.get("complete_event_count", 0) <= 0:
        return "waiting_for_complete_pairs"
    if completion.get("complete_event_count", 0) < completion.get("queue_count", 0):
        return "ready_partial_manual_hash"
    return "ready_full_manual_hash"


def hash_gate_next_action(status: str, completion: Mapping[str, Any]) -> str:
    if status == "waiting_for_import":
        return "先填写人工 Team Total CSV；当前没有可 hash 的完整候选。"
    if status == "blocked_import_errors":
        return f"先修复 {completion.get('invalid_row_count', 0)} 行导入错误，再生成 hash gate。"
    if status == "waiting_for_complete_pairs":
        return "至少补齐一个候选的 Over/Under 成对记录后，才能生成可签名 hash。"
    if status == "ready_partial_manual_hash":
        return "已有部分候选可签名；建议继续补高优先级，再由用户/操作员人工签名。"
    return "所有候选已生成可签名 hash；下一步人工签名和正式 raw merge 设计，仍不自动下注。"


def is_blank_template_seed(row: Mapping[str, str]) -> bool:
    manual_fields = [
        "tab_match_name",
        "team_scope",
        "tab_market_name",
        "selection_name",
        "line",
        "decimal_odds",
        "observed_at_aest",
    ]
    status = str(row.get("verification_status") or "").strip().lower()
    return status in {"", "pending"} and not any(str(row.get(field) or "").strip() for field in manual_fields)


def validate_import_row(row: Mapping[str, str], queue_ids: set[str]) -> list[str]:
    issues = []
    event_id = str(row.get("event_id") or "")
    if not event_id:
        issues.append("missing event_id")
    elif event_id not in queue_ids:
        issues.append("event_id not in current queue")
    for field in ["tab_match_name", "team_scope", "tab_market_name", "selection_name", "line", "decimal_odds", "observed_at_aest"]:
        if not str(row.get(field) or "").strip():
            issues.append(f"missing {field}")
    odds_value = str(row.get("decimal_odds") or "").strip()
    if odds_value and not valid_decimal_odds(odds_value):
        issues.append("invalid decimal_odds")
    market = str(row.get("tab_market_name") or "").lower()
    if market and "total" not in market:
        issues.append("tab_market_name does not look like Team Total")
    status = str(row.get("verification_status") or "").lower()
    if status not in {"verified", "manual_verified", "pending_review"}:
        issues.append("verification_status must be verified/manual_verified/pending_review")
    return issues


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_decimal_text(value: Any) -> str:
    text = str(value or "").strip()
    try:
        return f"{float(text):.4f}".rstrip("0").rstrip(".")
    except ValueError:
        return text


def status_from_audit(audit: Mapping[str, Any], import_exists: bool) -> str:
    completion = audit.get("completion") or {}
    if not import_exists:
        return "import_missing"
    if completion.get("invalid_row_count", 0):
        return "import_has_errors"
    if completion.get("complete_event_count", 0) == 0:
        return "import_empty_or_incomplete"
    if completion.get("complete_event_count", 0) < completion.get("queue_count", 0):
        return "import_partially_complete"
    return "import_ready_for_hash_gate"


def recommended_next_action(status: str, audit: Mapping[str, Any]) -> str:
    completion = audit.get("completion") or {}
    if status == "import_missing":
        return "下载 CSV 模板，人工只读 TAB 后保存到 manual_verification/provider_team_total_manual_verification.csv。"
    if status == "import_has_errors":
        return f"修复 {completion.get('invalid_row_count', 0)} 行导入错误后重跑状态检查。"
    if status == "import_empty_or_incomplete":
        return "当前导入未形成完整 Over/Under 成对记录；优先补 high priority 候选。"
    if status == "import_partially_complete":
        return "已有部分候选可进入 hash gate；继续补 high priority 缺口，不解锁新增 stake。"
    return "导入结构完整；下一步生成 provider_tab_final_verification hash gate，仍不自动下注。"


def build_provider_manual_workbench(
    payload: Mapping[str, Any],
    *,
    hash_gate: Mapping[str, Any],
    overlay_preview: Mapping[str, Any],
    overlay_publish_preflight: Mapping[str, Any],
    batch_size: int = DEFAULT_WORKBENCH_BATCH_SIZE,
) -> dict[str, Any]:
    queue = [dict(row) for row in payload.get("queue") or [] if isinstance(row, Mapping)]
    verified = {str(event_id) for event_id in payload.get("verified_event_ids") or []}
    partial = {str(event_id) for event_id in payload.get("partial_event_ids") or []}
    invalid_count = int((payload.get("completion") or {}).get("invalid_row_count") or 0)
    remaining = [row for row in queue if str(row.get("event_id") or "") not in verified]
    high_remaining = [row for row in remaining if row.get("priority_tier") == "high"]
    batches = build_manual_workbench_batches(remaining, batch_size=batch_size)
    next_batch = batches[0] if batches else {}
    import_quality = payload.get("import_quality") or {}
    status = manual_workbench_status(payload.get("status", ""), invalid_count, remaining)
    payload_out = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_manual_team_total_workbench",
        "status": status,
        "refresh_id": payload.get("refresh_id", ""),
        "scope": payload.get("scope", "matches"),
        "board_id": "world_cup_matches",
        "market_family": TEAM_TOTAL_LABEL,
        "batch_size": batch_size,
        "queue_count": len(queue),
        "remaining_event_count": len(remaining),
        "remaining_high_priority_count": len(high_remaining),
        "partial_event_count": len(partial),
        "invalid_row_count": invalid_count,
        "verified_event_count": len(verified),
        "completion": payload.get("completion") or {},
        "import_quality": import_quality_summary(import_quality),
        "batch_count": len(batches),
        "next_batch": next_batch,
        "next_batch_quality": manual_workbench_next_batch_quality(next_batch, import_quality),
        "batches": batches,
        "operator_checklist": [
            "打开 TAB 的 2026 World Cup Matches，对照 batch 中 match 和 commence_time。",
            "只读 Team Total Goals Over/Under；每个 event 至少记录同一 line 的 Over 与 Under 成对赔率。",
            "保存 event_id、team_scope、selection_name、line、decimal_odds、observed_at_aest、operator_initials 和证据备注。",
            f"写入 {DEFAULT_IMPORT_RELATIVE_PATH} 后重建 app；通过 hash gate 前 stake 保持 AUD 0。",
        ],
        "gate_snapshot": {
            "import_status": payload.get("status", ""),
            "hash_gate_status": hash_gate.get("status", "missing"),
            "overlay_preview_status": overlay_preview.get("status", "missing"),
            "overlay_publish_preflight_status": overlay_publish_preflight.get("status", "missing"),
            "ready_for_manual_signature": bool(hash_gate.get("ready_for_manual_signature")),
            "ready_for_publish_preflight": bool(overlay_preview.get("ready_for_publish_preflight")),
            "overlay_publish_preflight_passed": bool(overlay_publish_preflight.get("overlay_publish_preflight_passed")),
        },
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "recommended_next_action": manual_workbench_next_action(status, next_batch, len(high_remaining)),
        "truthfulness_note": (
            "该 workbench 只组织人工只读校验任务；不自动登录 TAB、不点击赔率、不修改 Bet Slip、"
            "不发布正式 raw，也不生成新增下注金额。"
        ),
    }
    return sanitize_public_payload(payload_out)


def attach_manual_workbench_operator_cockpit(payload: dict[str, Any]) -> dict[str, Any]:
    next_batch = payload.get("next_batch") or {}
    pair_templates = payload.get("pair_templates") or {}
    gate_snapshot = payload.get("gate_snapshot") or {}
    next_batch_rows = [row for row in next_batch.get("rows") or [] if isinstance(row, Mapping)]
    high_priority_count = sum(1 for row in next_batch_rows if row.get("priority_tier") == "high")
    ranks = [row.get("rank") for row in next_batch_rows if row.get("rank") not in (None, "")]
    current_batch_id = str(next_batch.get("batch_id") or "none")
    import_target = str(pair_templates.get("import_target") or DEFAULT_IMPORT_RELATIVE_PATH)
    next_batch_csv = str(pair_templates.get("next_batch_csv") or PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST)
    all_candidates_csv = str(pair_templates.get("all_candidates_csv") or PROVIDER_MANUAL_PAIR_TEMPLATE_CSV_LATEST)
    next_batch_pair_rows = int(pair_templates.get("next_batch_pair_rows") or len(next_batch_rows) * 2)
    import_status = str(gate_snapshot.get("import_status") or "missing")
    hash_gate_status = str(gate_snapshot.get("hash_gate_status") or "missing")
    overlay_preview_status = str(gate_snapshot.get("overlay_preview_status") or "missing")
    overlay_preflight_status = str(gate_snapshot.get("overlay_publish_preflight_status") or "missing")
    can_publish_now = bool(
        gate_snapshot.get("ready_for_manual_signature")
        and gate_snapshot.get("ready_for_publish_preflight")
        and gate_snapshot.get("overlay_publish_preflight_passed")
    )
    payload["operator_cockpit"] = {
        "title": "TT-001 Team Total 补齐操作台",
        "status": payload.get("status", "missing"),
        "primary_action": payload.get("recommended_next_action", ""),
        "current_batch_id": current_batch_id,
        "current_batch_event_count": int(next_batch.get("event_count") or len(next_batch_rows)),
        "current_batch_pair_rows": next_batch_pair_rows,
        "next_batch_pair_template_csv": next_batch_csv,
        "all_pair_template_csv": all_candidates_csv,
        "import_target": import_target,
        "import_status": import_status,
        "hash_gate_status": hash_gate_status,
        "overlay_preview_status": overlay_preview_status,
        "overlay_publish_preflight_status": overlay_preflight_status,
        "publish_status": "ready_for_explicit_publish" if can_publish_now else "blocked_until_manual_import_and_signature",
        "can_publish_now": can_publish_now,
        "stake_policy": "通过 manual import、hash gate、overlay preview、签名预检和 explicit publish 前，current executable new stake 固定 AUD 0。",
        "operator_warning": "只读 TAB 页面并人工记录；禁止点击赔率、加入 Bet Slip、提交下注或绕过 TAB 访问控制。",
    }
    payload["next_batch_summary"] = {
        "batch_id": current_batch_id,
        "event_count": int(next_batch.get("event_count") or len(next_batch_rows)),
        "pair_rows_required": next_batch_pair_rows,
        "rank_start": next_batch.get("rank_start", ranks[0] if ranks else ""),
        "rank_end": next_batch.get("rank_end", ranks[-1] if ranks else ""),
        "high_priority_count": high_priority_count,
        "priority_mix": next_batch.get("priority_mix") or {},
        "top_matches": [
            {
                "rank": row.get("rank", ""),
                "match": row.get("match", ""),
                "commence_time": row.get("commence_time", ""),
                "priority_tier": row.get("priority_tier", ""),
            }
            for row in next_batch_rows[:5]
        ],
    }
    payload["field_checklist"] = manual_workbench_field_checklist()
    payload["quality_gate_summary"] = manual_workbench_quality_gate_summary(payload)
    payload["workflow_steps"] = manual_workbench_workflow_steps(payload)
    payload["action_contract"] = manual_workbench_action_contract()
    payload["manual_intake_contract"] = manual_workbench_intake_contract(payload)
    return payload


def manual_workbench_next_batch_quality(next_batch: Mapping[str, Any], import_quality: Mapping[str, Any]) -> dict[str, Any]:
    rows = [row for row in next_batch.get("rows") or [] if isinstance(row, Mapping)]
    event_ids = {str(row.get("event_id") or "") for row in rows if row.get("event_id")}
    quality_rows = [
        row for row in import_quality.get("event_quality") or [] if str(row.get("event_id") or "") in event_ids
    ]
    status_counts: dict[str, int] = {}
    missing_field_counts: dict[str, int] = {}
    missing_direction_counts: dict[str, int] = {}
    for row in quality_rows:
        status = str(row.get("status") or "missing_rows")
        status_counts[status] = status_counts.get(status, 0) + 1
        for field in row.get("missing_fields") or []:
            missing_field_counts[str(field)] = missing_field_counts.get(str(field), 0) + 1
        for direction in row.get("missing_directions") or []:
            missing_direction_counts[str(direction)] = missing_direction_counts.get(str(direction), 0) + 1
    return {
        "batch_id": next_batch.get("batch_id", ""),
        "event_count": len(rows),
        "status_counts": status_counts,
        "missing_field_counts": missing_field_counts,
        "missing_direction_counts": missing_direction_counts,
        "rows": quality_rows,
        "next_action": next_batch_quality_next_action(status_counts),
    }


def next_batch_quality_next_action(status_counts: Mapping[str, int]) -> str:
    if status_counts.get("invalid_rows"):
        return "先修复下一批中的 invalid rows。"
    if status_counts.get("partial_or_incomplete"):
        return "下一批已有部分行；优先补缺失字段和 Over/Under 另一边。"
    if status_counts.get("missing_rows"):
        return "下一批尚未填写；从成对模板开始录入。"
    if status_counts.get("complete_pair"):
        return "下一批已形成合格成对记录；复核 hash gate。"
    return "当前没有下一批质量缺口。"


def manual_workbench_quality_gate_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    quality = payload.get("import_quality") or {}
    gate = payload.get("gate_snapshot") or {}
    next_batch_quality = payload.get("next_batch_quality") or {}
    return {
        "import_quality_status": quality.get("status", "missing"),
        "next_batch_quality_status_counts": next_batch_quality.get("status_counts") or {},
        "missing_event_count": quality.get("missing_event_count", 0),
        "partial_event_count": quality.get("partial_event_count", 0),
        "invalid_event_count": quality.get("invalid_event_count", 0),
        "complete_event_count": quality.get("complete_event_count", 0),
        "hash_gate_status": gate.get("hash_gate_status", "missing"),
        "overlay_preview_status": gate.get("overlay_preview_status", "missing"),
        "publish_preflight_status": gate.get("overlay_publish_preflight_status", "missing"),
        "next_action": quality.get("next_action") or next_batch_quality.get("next_action", ""),
    }


def manual_workbench_field_checklist() -> list[dict[str, Any]]:
    return [
        {
            "field": "event_id",
            "label": "事件 ID",
            "required": True,
            "validation": "必须来自模板，不要手写改动。",
            "reason": "用于把人工 Team Total 行合回 provider staged match。",
        },
        {
            "field": "team_scope",
            "label": "主/客队范围",
            "required": True,
            "validation": "home 或 away。",
            "reason": "区分 Team Total 属于哪支球队。",
        },
        {
            "field": "tab_match_name",
            "label": "TAB 比赛名",
            "required": True,
            "validation": "按 TAB 页面显示填写。",
            "reason": "用于人工复核 provider match 与 TAB match 是否一致。",
        },
        {
            "field": "tab_market_name",
            "label": "TAB 盘口名",
            "required": True,
            "validation": "必须包含 Team Total / Team Goals 等语义。",
            "reason": "防止把 Total Score O/U 错填为 Team Total。",
        },
        {
            "field": "selection_name",
            "label": "下注项名称",
            "required": True,
            "validation": "同一 event、team_scope、line 必须有 Over 与 Under 两行。",
            "reason": "成对记录才能进入 hash gate。",
        },
        {
            "field": "line",
            "label": "盘口线",
            "required": True,
            "validation": "必须是数字，如 0.5、1.5、2.5。",
            "reason": "用于验证 Over/Under 是否同线。",
        },
        {
            "field": "decimal_odds",
            "label": "十进制赔率",
            "required": True,
            "validation": "必须大于 1.00。",
            "reason": "进入概率/EV 研究前必须是可解析价格。",
        },
        {
            "field": "observed_at_aest",
            "label": "观察时间",
            "required": True,
            "validation": "使用 AEST 时间戳。",
            "reason": "后续 CLV、回测和旧报告对比需要时间点。",
        },
        {
            "field": "operator_initials",
            "label": "操作员缩写",
            "required": True,
            "validation": "填写人工核验人缩写。",
            "reason": "人工签名和后续复盘需要责任链。",
        },
        {
            "field": "evidence_note_or_screenshot_ref",
            "label": "证据备注",
            "required": True,
            "validation": "写明 TAB 页面观察备注或截图引用。",
            "reason": "正式发布前需要人工复核依据。",
        },
        {
            "field": "verification_status",
            "label": "校验状态",
            "required": True,
            "validation": "verified / manual_verified / pending_review。",
            "reason": "只有明确人工校验状态的行才能进入质量诊断。",
        },
    ]


def manual_workbench_workflow_steps(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    cockpit = payload.get("operator_cockpit") or {}
    return [
        {
            "step": 1,
            "title": "打开下一批模板",
            "action": f"使用 {cockpit.get('next_batch_pair_template_csv', PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST)}。",
            "output": "TT-001 的 Over/Under 成对待填行。",
            "status": "manual_required",
        },
        {
            "step": 2,
            "title": "只读 TAB 核验",
            "action": "按 match、commence_time、team_scope 查 Team Total Goals Over/Under。",
            "output": "同一 team_scope + line 的 Over 与 Under 两行。",
            "status": "manual_required",
        },
        {
            "step": 3,
            "title": "保存导入文件",
            "action": f"把填好的行保存到 {cockpit.get('import_target', DEFAULT_IMPORT_RELATIVE_PATH)}。",
            "output": "manual import CSV。",
            "status": str(cockpit.get("import_status") or "waiting_for_import"),
        },
        {
            "step": 4,
            "title": "重建工作台与 Hash Gate",
            "action": "运行 build/download app 或 provider manual verification bundle。",
            "output": "hash gate、overlay preview、publish preflight。",
            "status": str(cockpit.get("hash_gate_status") or "waiting_for_import"),
        },
        {
            "step": 5,
            "title": "签名后显式发布",
            "action": "只有 overlay approval hash 匹配后，才运行 publish_provider_manual_overlay.py。",
            "output": "正式 Matches raw publish gate；仍不自动下注。",
            "status": str(cockpit.get("publish_status") or "blocked"),
        },
    ]


def manual_workbench_action_contract() -> dict[str, Any]:
    return {
        "allowed_actions": [
            "读取 TAB 页面上的 Team Total 盘口文字和赔率",
            "填写 CSV 模板",
            "运行本地状态/报告重建命令",
            "在签名 gate 通过后显式发布 raw",
        ],
        "forbidden_actions": [
            "自动下注",
            "点击赔率",
            "加入 Bet Slip",
            "提交或修改 wagering ticket",
            "绕过 TAB CAPTCHA、指纹、登录或访问控制",
        ],
        "unlock_conditions": [
            "manual CSV 结构完整",
            "hash gate ready_for_manual_signature=true",
            "overlay preview ready_for_publish_preflight=true",
            "overlay approval hash 匹配且 approved_by_user=true",
            "explicit publish command 成功",
        ],
        "stake_boundary": "所有条件满足前 current_executable_new_stake_aud 必须保持 0。",
    }


def manual_workbench_intake_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    cockpit = payload.get("operator_cockpit") or {}
    quality = payload.get("quality_gate_summary") or {}
    next_batch = payload.get("next_batch_summary") or {}
    action_contract = payload.get("action_contract") or {}
    import_target = str(cockpit.get("import_target") or DEFAULT_IMPORT_RELATIVE_PATH)
    next_batch_csv = str(
        cockpit.get("next_batch_pair_template_csv") or PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST
    )
    return {
        "title": "TT-001 Team Total 人工导入合同",
        "status": str(payload.get("status") or "missing"),
        "current_batch_id": str(cockpit.get("current_batch_id") or next_batch.get("batch_id") or "none"),
        "template_csv": next_batch_csv,
        "template_asset_path": f"app_assets/{next_batch_csv}",
        "import_target": import_target,
        "import_target_display": f"outputs/{import_target}",
        "rebuild_command": "TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py",
        "status_check_command": "python3 -m unittest tab-research-pipeline.tests.test_pipeline.PipelineTests.test_provider_manual_verification_accepts_complete_over_under_pair",
        "publish_command_after_signature": "python3 publish_provider_manual_overlay.py",
        "current_state": {
            "missing_event_count": int(quality.get("missing_event_count") or 0),
            "partial_event_count": int(quality.get("partial_event_count") or 0),
            "invalid_event_count": int(quality.get("invalid_event_count") or 0),
            "complete_event_count": int(quality.get("complete_event_count") or 0),
            "next_batch_pair_rows": int(cockpit.get("current_batch_pair_rows") or 0),
            "can_publish_now": bool(cockpit.get("can_publish_now")),
            "current_executable_new_stake_aud": 0,
        },
        "operator_steps": [
            f"打开 {next_batch_csv}，只处理当前批次 {cockpit.get('current_batch_id') or 'TT-001'}。",
            "在 TAB 页面只读核验 Team Total Goals Over/Under；每个 event 至少填同一 team_scope + line 的 Over 与 Under 两行。",
            f"保存完整 CSV 到 outputs/{import_target}。",
            "运行 rebuild_command 重建 workbench、hash gate、overlay preview 和 Downloads app。",
            "只有 hash/approval/preflight 全部通过后，才允许人工显式运行 publish_command_after_signature；仍不自动下注。",
        ],
        "acceptance_criteria": [
            "next_batch_quality.status_counts 中不再出现 missing_rows 或 invalid_rows。",
            "import_quality.invalid_event_count=0。",
            "hash_gate_status 不再是 waiting_for_import。",
            "overlay_preview_status 不再是 waiting_for_import。",
            "formal_publish_allowed=false 直到人工签名和显式 publish 通过。",
            "current_executable_new_stake_aud=0。",
        ],
        "forbidden_actions": action_contract.get("forbidden_actions") or [],
        "next_safe_action": quality.get("next_action") or payload.get("recommended_next_action", ""),
    }


def build_manual_workbench_batches(rows: list[Mapping[str, Any]], *, batch_size: int) -> list[dict[str, Any]]:
    safe_batch_size = max(1, int(batch_size or DEFAULT_WORKBENCH_BATCH_SIZE))
    batches = []
    for start in range(0, len(rows), safe_batch_size):
        chunk = rows[start : start + safe_batch_size]
        if not chunk:
            continue
        tier_counts: dict[str, int] = {}
        for row in chunk:
            tier = str(row.get("priority_tier") or "watch")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        batch_number = len(batches) + 1
        batch_rows = [
            {
                "rank": row.get("rank", ""),
                "event_id": row.get("event_id", ""),
                "match": row.get("match", ""),
                "commence_time": row.get("commence_time", ""),
                "priority_tier": row.get("priority_tier", ""),
                "covered_markets": row.get("covered_markets", []),
                "rank_reason": row.get("rank_reason", ""),
                "required_fields": [
                    "team_scope",
                    "tab_market_name",
                    "selection_name",
                    "line",
                    "decimal_odds",
                    "observed_at_aest",
                    "operator_initials",
                    "evidence_note_or_screenshot_ref",
                ],
            }
            for row in chunk
        ]
        batches.append(
            {
                "batch_id": f"TT-{batch_number:03d}",
                "status": "pending_manual_readonly_verification",
                "event_count": len(chunk),
                "rank_start": chunk[0].get("rank", ""),
                "rank_end": chunk[-1].get("rank", ""),
                "priority_mix": tier_counts,
                "action": "人工只读 TAB Team Total O/U，补齐 Over/Under 成对赔率；不点击 odds，不加入 Bet Slip。",
                "rows": batch_rows,
            }
        )
    return batches


def manual_workbench_status(import_status: str, invalid_count: int, remaining: list[Mapping[str, Any]]) -> str:
    if invalid_count > 0:
        return "blocked_import_errors"
    if not remaining:
        return "all_candidates_imported_review_gates"
    if import_status in {"import_partially_complete", "import_ready_for_hash_gate"}:
        return "continue_remaining_batches"
    return "waiting_for_first_batch"


def manual_workbench_next_action(status: str, next_batch: Mapping[str, Any], high_remaining_count: int) -> str:
    if status == "blocked_import_errors":
        return "先修复 CSV 错误行，再继续下一批人工校验。"
    if status == "all_candidates_imported_review_gates":
        return "全部候选已导入；下一步复核 hash gate、overlay preview 和人工签名。"
    batch_id = next_batch.get("batch_id") or "TT-001"
    event_count = next_batch.get("event_count") or DEFAULT_WORKBENCH_BATCH_SIZE
    return f"下一批执行 {batch_id}，校验 {event_count} 场；剩余高优先级 {high_remaining_count} 场，仍保持 stake AUD 0。"


def render_manual_workbench_markdown(payload: Mapping[str, Any]) -> str:
    next_batch = payload.get("next_batch") or {}
    cockpit = payload.get("operator_cockpit") or {}
    intake = payload.get("manual_intake_contract") or {}
    lines = [
        "# Provider Manual Team Total Workbench",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- remaining_event_count: `{payload.get('remaining_event_count', 0)}`",
        f"- remaining_high_priority_count: `{payload.get('remaining_high_priority_count', 0)}`",
        f"- batch_count: `{payload.get('batch_count', 0)}`",
        f"- next_batch: `{next_batch.get('batch_id', '')}`",
        f"- all_pair_template: `{(payload.get('pair_templates') or {}).get('all_candidates_csv', '')}`",
        f"- next_batch_pair_template: `{(payload.get('pair_templates') or {}).get('next_batch_csv', '')}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Operator Cockpit",
        "",
        f"- title: `{cockpit.get('title', '')}`",
        f"- primary_action: {md(cockpit.get('primary_action'))}",
        f"- current_batch: `{cockpit.get('current_batch_id', '')}` / events `{cockpit.get('current_batch_event_count', 0)}` / pair rows `{cockpit.get('current_batch_pair_rows', 0)}`",
        f"- next_batch_pair_template: `{cockpit.get('next_batch_pair_template_csv', '')}`",
        f"- import_target: `{cockpit.get('import_target', '')}`",
        f"- publish_status: `{cockpit.get('publish_status', '')}`",
        f"- can_publish_now: `{cockpit.get('can_publish_now', False)}`",
        f"- stake_policy: {md(cockpit.get('stake_policy'))}",
        "",
        "## Manual Intake Contract",
        "",
        f"- status: `{intake.get('status', '')}`",
        f"- current_batch_id: `{intake.get('current_batch_id', '')}`",
        f"- template_csv: `{intake.get('template_csv', '')}`",
        f"- import_target: `{intake.get('import_target_display', intake.get('import_target', ''))}`",
        f"- rebuild_command: `{intake.get('rebuild_command', '')}`",
        f"- publish_command_after_signature: `{intake.get('publish_command_after_signature', '')}`",
        f"- next_safe_action: {md(intake.get('next_safe_action'))}",
        "",
        "### Acceptance Criteria",
        "",
    ]
    lines.extend(f"- {md(item)}" for item in intake.get("acceptance_criteria") or [])
    lines.extend(
        [
            "",
            "### Operator Steps",
            "",
        ]
    )
    lines.extend(f"{idx}. {md(item)}" for idx, item in enumerate(intake.get("operator_steps") or [], start=1))
    lines.extend(
        [
            "",
        "## Workflow Steps",
        "",
        "| Step | Title | Status | Action |",
        "|---:|---|---|---|",
        ]
    )
    for step in payload.get("workflow_steps") or []:
        lines.append(
            f"| {step.get('step', '')} | {md(step.get('title'))} | `{step.get('status', '')}` | {md(step.get('action'))} |"
        )
    lines.extend(
        [
            "",
            "## Field Checklist",
            "",
            "| Field | Required | Validation | Reason |",
            "|---|---|---|---|",
        ]
    )
    for field in payload.get("field_checklist") or []:
        lines.append(
            f"| `{field.get('field', '')}` | `{field.get('required', False)}` | {md(field.get('validation'))} | {md(field.get('reason'))} |"
        )
    quality_gate = payload.get("quality_gate_summary") or {}
    next_quality = payload.get("next_batch_quality") or {}
    lines.extend(
        [
            "",
            "## Import Quality",
            "",
            f"- import_quality_status: `{quality_gate.get('import_quality_status', '')}`",
            f"- next_batch_status_counts: `{json.dumps(quality_gate.get('next_batch_quality_status_counts') or {}, ensure_ascii=False, sort_keys=True)}`",
            f"- missing_event_count: `{quality_gate.get('missing_event_count', 0)}`",
            f"- partial_event_count: `{quality_gate.get('partial_event_count', 0)}`",
            f"- invalid_event_count: `{quality_gate.get('invalid_event_count', 0)}`",
            f"- complete_event_count: `{quality_gate.get('complete_event_count', 0)}`",
            f"- next_action: {md(quality_gate.get('next_action'))}",
            "",
            "| Rank | Match | Quality | Missing Fields | Missing Directions | Next Action |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for row in (next_quality.get("rows") or [])[:12]:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('match'))} | `{row.get('status', '')}` | "
            f"{md(', '.join(str(item) for item in row.get('missing_fields') or []))} | "
            f"{md('/'.join(str(item) for item in row.get('missing_directions') or []))} | "
            f"{md(row.get('next_action'))} |"
        )
    if not next_quality.get("rows"):
        lines.append("| - | No next-batch quality rows. | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Operator Checklist",
            "",
        ]
    )
    lines.extend(f"- {md(item)}" for item in payload.get("operator_checklist") or [])
    lines.extend(["", "## Next Batch", "", "| Rank | Match | Time | Tier | Reason |", "|---:|---|---|---|---|"])
    for row in next_batch.get("rows") or []:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('match'))} | `{row.get('commence_time', '')}` | "
            f"`{row.get('priority_tier', '')}` | {md(row.get('rank_reason'))} |"
        )
    if not next_batch.get("rows"):
        lines.append("| - | No remaining manual rows. | - | - | - |")
    lines.extend(["", "## Gate Snapshot", ""])
    for key, value in (payload.get("gate_snapshot") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_workbench_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    next_batch = payload.get("next_batch") or {}
    cockpit = payload.get("operator_cockpit") or {}
    quality_gate = payload.get("quality_gate_summary") or {}
    intake = payload.get("manual_intake_contract") or {}
    rows = [
        [
            str(row.get("rank", "")),
            str(row.get("match", "")),
            str(row.get("commence_time", "")),
            str(row.get("priority_tier", "")),
            str(row.get("rank_reason", "")),
        ]
        for row in (next_batch.get("rows") or [])[:16]
    ]
    if not rows:
        rows = [["-", "No remaining manual rows", "-", "-", "Review gates"]]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Team Total Workbench",
        subtitle="Batch-oriented manual verification queue. Research only, no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Remaining", str(payload.get("remaining_event_count", 0))),
            ("High Remaining", str(payload.get("remaining_high_priority_count", 0))),
            ("Next Batch", str(next_batch.get("batch_id", "") or "none")),
            ("Pair Template", str((payload.get("pair_templates") or {}).get("next_batch_csv", ""))),
            ("Import Target", str(cockpit.get("import_target", ""))),
            ("Rebuild", str(intake.get("rebuild_command", ""))),
            ("Next Safe Action", str(intake.get("next_safe_action", ""))),
            ("Publish Status", str(cockpit.get("publish_status", ""))),
            ("Quality", str(quality_gate.get("import_quality_status", ""))),
            ("Missing Events", str(quality_gate.get("missing_event_count", 0))),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Manual Workbench",
                [
                    ("verified", float(payload.get("verified_event_count", 0) or 0)),
                    ("remaining high", float(payload.get("remaining_high_priority_count", 0) or 0)),
                    ("remaining total", float(payload.get("remaining_event_count", 0) or 0)),
                    ("invalid rows", float(payload.get("invalid_row_count", 0) or 0)),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Rank", "Match", "Time", "Tier", "Reason"],
        table_rows=rows,
    )


def render_manual_verification_status_markdown(payload: Mapping[str, Any]) -> str:
    completion = payload.get("completion") or {}
    lines = [
        "# Provider Manual Verification Import Status",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- import_file: `{payload.get('import_relative_path', '')}`",
        f"- complete_event_count: `{completion.get('complete_event_count', 0)}/{completion.get('queue_count', 0)}`",
        f"- high_priority_complete_count: `{completion.get('high_priority_complete_count', 0)}/{completion.get('high_priority_count', 0)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Required Columns",
        "",
        ", ".join(f"`{field}`" for field in payload.get("template_fields") or []),
        "",
        "## Invalid Rows",
        "",
        "| Row | Event | Issue |",
        "|---:|---|---|",
    ]
    invalid_rows = payload.get("invalid_rows") or []
    if invalid_rows:
        for row in invalid_rows:
            lines.append(f"| {row.get('row_number', '')} | `{md(row.get('event_id'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | - | No invalid rows. |")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_verification_status_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    completion = payload.get("completion") or {}
    invalid_rows = payload.get("invalid_rows") or []
    detail_rows = [
        [
            str(row.get("row_number", "")),
            str(row.get("event_id", "")),
            str(row.get("issue", "")),
        ]
        for row in invalid_rows[:18]
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Manual Verification Import",
        subtitle="Human verification import status. Research only, no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Complete Events", f"{completion.get('complete_event_count', 0)}/{completion.get('queue_count', 0)}"),
            ("High Priority Complete", f"{completion.get('high_priority_complete_count', 0)}/{completion.get('high_priority_count', 0)}"),
            ("Invalid Rows", str(completion.get("invalid_row_count", 0))),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Import Completion",
                [
                    ("complete", float(completion.get("complete_event_count", 0))),
                    ("partial", float(completion.get("partial_event_count", 0))),
                    ("remaining", max(0.0, float(completion.get("queue_count", 0)) - float(completion.get("complete_event_count", 0)))),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Row", "Event", "Issue"],
        table_rows=detail_rows,
    )


def render_manual_hash_gate_markdown(payload: Mapping[str, Any]) -> str:
    completion = payload.get("completion") or {}
    draft = payload.get("provider_tab_final_verification_draft") or {}
    lines = [
        "# Provider Manual Hash Gate",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- market_family: `{payload.get('market_family', '')}`",
        f"- complete_event_count: `{completion.get('complete_event_count', 0)}/{completion.get('queue_count', 0)}`",
        f"- high_priority_complete_count: `{completion.get('high_priority_complete_count', 0)}/{completion.get('high_priority_count', 0)}`",
        f"- import_file_sha256: `{payload.get('import_file_sha256', '')}`",
        f"- manual_import_sha256: `{payload.get('manual_import_sha256', '')}`",
        f"- ready_for_manual_signature: `{payload.get('ready_for_manual_signature', False)}`",
        f"- approved_by_user: `{draft.get('approved_by_user', False)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Draft Boundary",
        "",
        f"- publish_compatible_with_provider_raw: `{draft.get('publish_compatible_with_provider_raw', False)}`",
        f"- note: {md(draft.get('note'))}",
        "",
        "## Invalid Rows",
        "",
        "| Row | Event | Issue |",
        "|---:|---|---|",
    ]
    invalid_rows = payload.get("invalid_rows") or []
    if invalid_rows:
        for row in invalid_rows:
            lines.append(f"| {row.get('row_number', '')} | `{md(row.get('event_id'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | - | No invalid rows. |")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_hash_gate_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    completion = payload.get("completion") or {}
    invalid_rows = payload.get("invalid_rows") or []
    detail_rows = [
        [str(row.get("row_number", "")), str(row.get("event_id", "")), str(row.get("issue", ""))]
        for row in invalid_rows[:18]
    ]
    digest = str(payload.get("manual_import_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Manual Hash Gate",
        subtitle="Manual Team Total import hash gate. Research only, no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Complete Events", f"{completion.get('complete_event_count', 0)}/{completion.get('queue_count', 0)}"),
            ("High Priority Complete", f"{completion.get('high_priority_complete_count', 0)}/{completion.get('high_priority_count', 0)}"),
            ("Manual Import SHA", short_digest),
            ("Approved By User", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Hash Gate Completion",
                [
                    ("complete", float(completion.get("complete_event_count", 0))),
                    ("remaining", max(0.0, float(completion.get("queue_count", 0)) - float(completion.get("complete_event_count", 0)))),
                    ("errors", float(completion.get("invalid_row_count", 0))),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Row", "Event", "Issue"],
        table_rows=detail_rows,
    )


def render_manual_overlay_preview_markdown(payload: Mapping[str, Any]) -> str:
    completion = payload.get("completion") or {}
    draft = payload.get("provider_tab_final_verification_overlay_draft") or {}
    lines = [
        "# Provider Manual Team Total Overlay Preview",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- market_family: `{payload.get('market_family', '')}`",
        f"- overlay_event_count: `{payload.get('overlay_event_count', 0)}/{completion.get('queue_count', 0)}`",
        f"- overlay_row_count: `{payload.get('overlay_row_count', 0)}`",
        f"- high_priority_complete_count: `{completion.get('high_priority_complete_count', 0)}/{completion.get('high_priority_count', 0)}`",
        f"- manual_import_sha256: `{payload.get('manual_import_sha256', '')}`",
        f"- overlay_raw_snapshot: `{payload.get('overlay_raw_snapshot', '')}`",
        f"- overlay_raw_sha256: `{payload.get('overlay_raw_sha256', '')}`",
        f"- ready_for_publish_preflight: `{payload.get('ready_for_publish_preflight', False)}`",
        f"- approved_by_user: `{draft.get('approved_by_user', False)}`",
        f"- formal_publish_allowed: `{payload.get('formal_publish_allowed', False)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Overlay Boundary",
        "",
        f"- overlay_preview_only: `{payload.get('overlay_preview_only', True)}`",
        f"- publish_compatible_with_provider_raw: `{draft.get('publish_compatible_with_provider_raw', False)}`",
        f"- note: {md(draft.get('note'))}",
        "",
        "## Invalid Rows",
        "",
        "| Row | Event | Issue |",
        "|---:|---|---|",
    ]
    invalid_rows = payload.get("invalid_rows") or []
    if invalid_rows:
        for row in invalid_rows:
            lines.append(f"| {row.get('row_number', '')} | `{md(row.get('event_id'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | - | No invalid rows. |")
    overlaid = payload.get("overlaid_event_ids_sample") or []
    lines.extend(["", "## Overlaid Events Sample", ""])
    if overlaid:
        lines.extend(f"- `{md(event_id)}`" for event_id in overlaid[:20])
    else:
        lines.append("- None.")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_overlay_preview_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    completion = payload.get("completion") or {}
    invalid_rows = payload.get("invalid_rows") or []
    detail_rows = [
        [str(row.get("row_number", "")), str(row.get("event_id", "")), str(row.get("issue", ""))]
        for row in invalid_rows[:18]
    ]
    digest = str(payload.get("overlay_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Manual Team Total Overlay Preview",
        subtitle="Preview-only raw overlay. Research only, no publish and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Overlay Events", f"{payload.get('overlay_event_count', 0)}/{completion.get('queue_count', 0)}"),
            ("Overlay Rows", str(payload.get("overlay_row_count", 0))),
            ("Overlay Raw SHA", short_digest),
            ("Approved By User", "false"),
            ("Formal Publish", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Overlay Coverage",
                [
                    ("overlay", float(payload.get("overlay_event_count", 0))),
                    ("remaining", max(0.0, float(completion.get("queue_count", 0)) - float(payload.get("overlay_event_count", 0)))),
                    ("errors", float(completion.get("invalid_row_count", 0))),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Row", "Event", "Issue"],
        table_rows=detail_rows,
    )


def render_manual_overlay_publish_preflight_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Provider Manual Team Total Overlay Publish Preflight",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- market_family: `{payload.get('market_family', '')}`",
        f"- approval_relative_path: `{payload.get('approval_relative_path', '')}`",
        f"- approval_file_sha256: `{payload.get('approval_file_sha256', '')}`",
        f"- manual_import_sha256: `{payload.get('manual_import_sha256', '')}`",
        f"- overlay_raw_snapshot: `{payload.get('overlay_raw_snapshot', '')}`",
        f"- overlay_raw_sha256: `{payload.get('overlay_raw_sha256', '')}`",
        f"- overlay_event_count: `{payload.get('overlay_event_count', 0)}`",
        f"- approved_by_user: `{payload.get('approved_by_user', False)}`",
        f"- overlay_publish_preflight_passed: `{payload.get('overlay_publish_preflight_passed', False)}`",
        f"- publish_compatible_with_provider_raw: `{payload.get('publish_compatible_with_provider_raw', False)}`",
        f"- formal_publish_allowed: `{payload.get('formal_publish_allowed', False)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('next_safe_action'))}",
        "",
        "## Issues",
        "",
        "| Field | Issue |",
        "|---|---|",
    ]
    issues = payload.get("issues") or []
    if issues:
        for row in issues:
            lines.append(f"| `{md(row.get('field'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | No issues. |")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_overlay_publish_preflight_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    issues = payload.get("issues") or []
    detail_rows = [[str(row.get("field", "")), str(row.get("issue", ""))] for row in issues[:18]]
    digest = str(payload.get("overlay_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Overlay Publish Preflight",
        subtitle="Manual signature hash preflight. Research only, no automatic raw publish and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Overlay Events", str(payload.get("overlay_event_count", 0))),
            ("Overlay Raw SHA", short_digest),
            ("Approved By User", str(bool(payload.get("approved_by_user"))).lower()),
            ("Preflight Passed", str(bool(payload.get("overlay_publish_preflight_passed"))).lower()),
            ("Formal Publish", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Publish Preflight",
                [
                    ("passed", 1.0 if payload.get("overlay_publish_preflight_passed") else 0.0),
                    ("issues", float(len(issues))),
                    ("blocked", 0.0 if payload.get("overlay_publish_preflight_passed") else 1.0),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Field", "Issue"],
        table_rows=detail_rows,
    )


def render_manual_overlay_publish_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Provider Manual Team Total Overlay Publish",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- ok: `{payload.get('ok', False)}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- market_family: `{payload.get('market_family', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- provider_refresh_id: `{payload.get('provider_refresh_id', '')}`",
        f"- manual_import_sha256: `{payload.get('manual_import_sha256', '')}`",
        f"- overlay_raw_snapshot: `{payload.get('overlay_raw_snapshot', '')}`",
        f"- overlay_raw_sha256: `{payload.get('overlay_raw_sha256', '')}`",
        f"- overlay_event_count: `{payload.get('overlay_event_count', 0)}`",
        f"- overlay_row_count: `{payload.get('overlay_row_count', 0)}`",
        f"- approval_relative_path: `{payload.get('approval_relative_path', '')}`",
        f"- approval_file_sha256: `{payload.get('approval_file_sha256', '')}`",
        f"- published_raw_snapshot: `{payload.get('published_raw_snapshot', '')}`",
        f"- published_raw_sha256: `{payload.get('published_raw_sha256', '')}`",
        f"- formal_raw_publish_performed: `{payload.get('formal_raw_publish_performed', False)}`",
        f"- full_automation_allowed: `{payload.get('full_automation_allowed', False)}`",
        f"- raw_batch_manifest_written: `{payload.get('raw_batch_manifest_written', False)}`",
        f"- raw_gate_ready: `{payload.get('raw_gate_ready', False)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('next_safe_action'))}",
        "",
        "## Issues",
        "",
        "| Field | Issue |",
        "|---|---|",
    ]
    issues = payload.get("issues") or []
    if issues:
        for row in issues:
            lines.append(f"| `{md(row.get('field'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | No issues. |")
    raw_gate = payload.get("raw_gate") or {}
    blocking = raw_gate.get("blocking_reasons") or []
    lines.extend(["", "## Raw Gate", "", f"- staged_raw_ready: `{raw_gate.get('staged_raw_ready', False)}`", ""])
    if blocking:
        lines.extend(["| Blocking Reason |", "|---|"])
        for reason in blocking[:20]:
            lines.append(f"| {md(reason)} |")
    else:
        lines.append("No raw-gate blocking reasons recorded.")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_manual_overlay_publish_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    issues = payload.get("issues") or []
    raw_gate = payload.get("raw_gate") or {}
    blocking = raw_gate.get("blocking_reasons") or []
    digest = str(payload.get("published_raw_sha256") or payload.get("overlay_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    detail_rows = [[str(row.get("field", "")), str(row.get("issue", ""))] for row in issues[:12]]
    if not detail_rows:
        detail_rows = [["raw_gate", str(blocking[0]) if blocking else "No issues."]]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Team Total Overlay Publish",
        subtitle="Manual signature scoped publish. Matches only, no batch manifest and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Board", str(payload.get("board_id", ""))),
            ("Overlay Events", str(payload.get("overlay_event_count", 0))),
            ("Published Raw", str(payload.get("published_raw_snapshot", "")) or "blocked"),
            ("Raw SHA", short_digest),
            ("Formal Raw Publish", str(bool(payload.get("formal_raw_publish_performed"))).lower()),
            ("Full Automation", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Overlay Publish",
                [
                    ("published", 1.0 if payload.get("formal_raw_publish_performed") else 0.0),
                    ("overlay events", float(payload.get("overlay_event_count", 0) or 0)),
                    ("issues", float(len(issues))),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Field", "Issue"],
        table_rows=detail_rows,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
