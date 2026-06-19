from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .boards import BOARD_BY_ID
from .io import atomic_write_json, atomic_write_text
from .parser import parse_market_pairs
from .raw_refresh import RAW_BATCH_MANIFEST, audit_staged_raw_refresh, sha256_file, validate_raw_snapshot
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


REPORT_TZ = ZoneInfo("Australia/Sydney")
PUBLIC_SNAPSHOT_IMPORT_DIR = "manual_verification/public_raw_snapshots"
PUBLIC_SNAPSHOT_IMPORT_STATUS_JSON_LATEST = "public_snapshot_import_status_latest.json"
PUBLIC_SNAPSHOT_IMPORT_STATUS_MD_LATEST = "public_snapshot_import_status_latest.md"
PUBLIC_SNAPSHOT_IMPORT_STATUS_PDF_LATEST = "public_snapshot_import_status_latest.pdf"
PUBLIC_SNAPSHOT_IMPORT_TEMPLATE_JSON_LATEST = "public_snapshot_import_manifest_template_latest.json"
PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST = "public_snapshot_import_preview_raw_latest.json"
PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST = "public_snapshot_import_approval_template_latest.json"
PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST = "public_snapshot_import_publish_preflight_latest.json"
PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_MD_LATEST = "public_snapshot_import_publish_preflight_latest.md"
PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_PDF_LATEST = "public_snapshot_import_publish_preflight_latest.pdf"
PUBLIC_SNAPSHOT_RAW_PUBLISH_JSON_LATEST = "public_snapshot_raw_publish_latest.json"
PUBLIC_SNAPSHOT_RAW_PUBLISH_MD_LATEST = "public_snapshot_raw_publish_latest.md"
PUBLIC_SNAPSHOT_RAW_PUBLISH_PDF_LATEST = "public_snapshot_raw_publish_latest.pdf"
DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH = "manual_verification/public_snapshot_import_approval.json"
EXCLUDED_IMPORT_NAMES = {
    "import_manifest.json",
    PUBLIC_SNAPSHOT_IMPORT_STATUS_JSON_LATEST,
    PUBLIC_SNAPSHOT_IMPORT_TEMPLATE_JSON_LATEST,
    PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST,
    PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST,
    PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST,
    PUBLIC_SNAPSHOT_RAW_PUBLISH_JSON_LATEST,
}
MARKET_FAMILIES = [
    "Result",
    "Total Goals Over/Under",
    "Team Total Goals Over/Under",
    "Handicap",
    "Double Chance",
    "Both Teams to Score",
    "Draw No Bet",
]


def write_public_snapshot_import_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload, preview_raw = build_public_snapshot_import_status(output_dir)
    template_path = output_dir / PUBLIC_SNAPSHOT_IMPORT_TEMPLATE_JSON_LATEST
    preview_raw_path = output_dir / PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST
    json_path = output_dir / PUBLIC_SNAPSHOT_IMPORT_STATUS_JSON_LATEST
    md_path = output_dir / PUBLIC_SNAPSHOT_IMPORT_STATUS_MD_LATEST
    pdf_path = output_dir / PUBLIC_SNAPSHOT_IMPORT_STATUS_PDF_LATEST
    approval_template_path = output_dir / PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST
    publish_preflight_json_path = output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST
    publish_preflight_md_path = output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_MD_LATEST
    publish_preflight_pdf_path = output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_PDF_LATEST

    atomic_write_json(template_path, build_public_snapshot_import_template())
    atomic_write_json(preview_raw_path, preview_raw)
    payload["preview_raw_snapshot"] = preview_raw_path.name
    payload["preview_raw_sha256"] = sha256_file(preview_raw_path) or ""
    approval_template = build_public_snapshot_approval_template(payload)
    publish_preflight = build_public_snapshot_publish_preflight(output_dir, payload)
    atomic_write_json(approval_template_path, approval_template)
    atomic_write_json(publish_preflight_json_path, publish_preflight)
    atomic_write_text(publish_preflight_md_path, render_public_snapshot_publish_preflight_markdown(publish_preflight))
    publish_preflight_pdf_summary = write_public_snapshot_publish_preflight_pdf(
        publish_preflight, publish_preflight_pdf_path
    )
    publish_preflight["artifacts"] = {
        "json": publish_preflight_json_path.name,
        "markdown": publish_preflight_md_path.name,
        "pdf": publish_preflight_pdf_path.name,
        "approval_template": approval_template_path.name,
        "pdf_summary": publish_preflight_pdf_summary,
    }
    atomic_write_json(publish_preflight_json_path, publish_preflight)
    payload["publish_preflight_summary"] = {
        "status": publish_preflight.get("status"),
        "approval_relative_path": publish_preflight.get("approval_relative_path"),
        "approved_by_user": bool(publish_preflight.get("approved_by_user")),
        "snapshot_publish_preflight_passed": bool(publish_preflight.get("snapshot_publish_preflight_passed")),
        "issue_count": len(publish_preflight.get("issues") or []),
        "formal_publish_allowed": False,
        "current_executable_new_stake_aud": 0,
    }
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_public_snapshot_import_markdown(payload))
    pdf_summary = write_public_snapshot_import_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "template_json": template_path.name,
        "preview_raw": preview_raw_path.name,
        "approval_template": approval_template_path.name,
        "publish_preflight_json": publish_preflight_json_path.name,
        "publish_preflight_markdown": publish_preflight_md_path.name,
        "publish_preflight_pdf": publish_preflight_pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def publish_public_snapshot_raw(output_dir: Path) -> dict[str, Any]:
    """Publish a manually signed public snapshot into the Matches raw slot.

    This is intentionally scope-only: it never writes the 5-board batch manifest,
    never unlocks automation, and never creates executable stake.
    """
    output_dir = Path(output_dir)
    payload = write_public_snapshot_import_bundle(output_dir)
    preflight = load_json(output_dir / PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST)
    issues: list[dict[str, str]] = []
    generated_at = datetime.now(REPORT_TZ).isoformat()
    board = BOARD_BY_ID["world_cup_matches"]
    preview_raw_name = str(payload.get("preview_raw_snapshot") or PUBLIC_SNAPSHOT_IMPORT_PREVIEW_RAW_LATEST)
    preview_raw_path = output_dir / preview_raw_name
    preview_raw_sha = sha256_file(preview_raw_path) or ""
    expected_preview_sha = str(preflight.get("preview_raw_sha256") or payload.get("preview_raw_sha256") or "")

    if preflight.get("snapshot_publish_preflight_passed") is not True:
        issues.append({"field": "preflight", "issue": "public snapshot publish preflight has not passed"})
    if not preview_raw_path.exists():
        issues.append({"field": "preview_raw_snapshot", "issue": f"missing {preview_raw_name}"})
    if expected_preview_sha and preview_raw_sha != expected_preview_sha:
        issues.append({"field": "preview_raw_sha256", "issue": "preview raw sha256 changed after approval"})

    preview_raw = load_json(preview_raw_path)
    publish_refresh_id = public_snapshot_publish_refresh_id()
    prepared_raw = prepare_public_snapshot_formal_raw(
        preview_raw,
        payload=payload,
        preflight=preflight,
        refresh_id=publish_refresh_id,
        generated_at=generated_at,
    )
    validation = validate_raw_snapshot(board.board_id, prepared_raw)
    if not validation.get("valid"):
        for error in validation.get("errors") or ["raw validation failed"]:
            issues.append({"field": "raw_validation", "issue": str(error)})

    if issues:
        result = public_snapshot_publish_result(
            generated_at=generated_at,
            status="blocked_publish_preflight",
            ok=False,
            refresh_id=publish_refresh_id,
            payload=payload,
            preflight=preflight,
            destination=board.raw_snapshot or "",
            preview_raw_sha=preview_raw_sha,
            destination_sha="",
            issues=issues,
            raw_gate={},
        )
        write_public_snapshot_publish_artifacts(output_dir, result)
        return result

    destination = output_dir / str(board.raw_snapshot)
    atomic_write_json(destination, sanitize_public_payload(prepared_raw))
    raw_gate = audit_staged_raw_refresh(output_dir, expected_refresh_id=publish_refresh_id)
    result = public_snapshot_publish_result(
        generated_at=generated_at,
        status="published_scope_matches",
        ok=True,
        refresh_id=publish_refresh_id,
        payload=payload,
        preflight=preflight,
        destination=board.raw_snapshot or "",
        preview_raw_sha=preview_raw_sha,
        destination_sha=sha256_file(destination) or "",
        issues=[],
        raw_gate=raw_gate,
    )
    write_public_snapshot_publish_artifacts(output_dir, result)
    return result


def prepare_public_snapshot_formal_raw(
    raw: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
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
            "source": "public_snapshot_manual_verified",
            "source_mode": "user_public_snapshot_manual_verified",
            "board_id": "world_cup_matches",
            "refresh_id": refresh_id,
            "snapshot_import_preview_only": False,
            "public_snapshot_publish_verified": True,
            "selected_snapshot_file": payload.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": payload.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": payload.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": payload.get("preview_raw_sha256", ""),
            "approval_relative_path": preflight.get("approval_relative_path", DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH),
            "approval_file_sha256": preflight.get("approval_file_sha256", ""),
            "approved_by_user": bool(preflight.get("approved_by_user")),
            "operator_initials": preflight.get("operator_initials", ""),
            "signed_at_aest": preflight.get("signed_at_aest", ""),
            "formal_raw_publish_source": "public_snapshot_signature_gate",
            "full_automation_allowed": False,
            "current_executable_new_stake_aud": 0,
            "truthfulness_note": (
                "This raw was published from a user-provided public snapshot after manual hash approval. "
                "It is scope-only Matches raw and does not unlock full automation, My Bets sync, or betting execution."
            ),
        }
    )
    if not isinstance(prepared.get("matches"), list):
        prepared["matches"] = []
    return prepared


def public_snapshot_publish_result(
    *,
    generated_at: str,
    status: str,
    ok: bool,
    refresh_id: str,
    payload: Mapping[str, Any],
    preflight: Mapping[str, Any],
    destination: str,
    preview_raw_sha: str,
    destination_sha: str,
    issues: list[dict[str, str]],
    raw_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return sanitize_public_payload(
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "mode": "public_snapshot_raw_publish",
            "ok": ok,
            "status": status,
            "scope": "matches",
            "board_id": "world_cup_matches",
            "refresh_id": refresh_id,
            "selected_snapshot_file": payload.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": payload.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": payload.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": preview_raw_sha,
            "approval_relative_path": preflight.get("approval_relative_path", DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH),
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
            "next_safe_action": public_snapshot_raw_publish_next_action(status),
            "truthfulness_note": (
                "Public snapshot publish is an explicit manual-signature path for Matches raw only. "
                "It does not prove live TAB page access, does not write a 5-board batch manifest, and does not allow betting execution."
            ),
        }
    )


def public_snapshot_raw_publish_next_action(status: str) -> str:
    if status == "published_scope_matches":
        return "Matches raw 已从人工签名 public snapshot 发布；继续补齐 Team Total、My Bets 和其余 4 个板块后再评估完整 automation。"
    return "先导入有效 public snapshot，并让 approval 文件通过签名预检；发布失败时不要手工复制 preview raw 到正式 raw。"


def write_public_snapshot_publish_artifacts(output_dir: Path, payload: Mapping[str, Any]) -> None:
    output_dir = Path(output_dir)
    json_path = output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_JSON_LATEST
    md_path = output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_MD_LATEST
    pdf_path = output_dir / PUBLIC_SNAPSHOT_RAW_PUBLISH_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_public_snapshot_raw_publish_markdown(payload))
    pdf_summary = write_public_snapshot_raw_publish_pdf(payload, pdf_path)
    next_payload = dict(payload)
    next_payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, sanitize_public_payload(next_payload))


def public_snapshot_publish_refresh_id() -> str:
    return f"{datetime.now(REPORT_TZ).strftime('%Y%m%dT%H%M%S%z')}-public-snapshot"


def build_public_snapshot_import_status(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    import_dir = output_dir / PUBLIC_SNAPSHOT_IMPORT_DIR
    candidate = select_snapshot_candidate(import_dir)
    issues: list[dict[str, str]] = []

    if not candidate:
        status = "waiting_for_snapshot_import"
        preview_raw = empty_preview_raw(generated_at, status, "未发现 public raw snapshot JSON 导入文件。")
        payload = base_payload(generated_at, status)
        payload.update(
            {
                "selected_snapshot_file": "",
                "selected_snapshot_sha256": "",
                "match_count": 0,
                "market_coverage": {},
                "issues": [
                    {
                        "field": "import_dir",
                        "issue": f"请把 JSON 快照放到 {PUBLIC_SNAPSHOT_IMPORT_DIR}/，文件名保持 .json。",
                    }
                ],
                "recommended_next_action": (
                    "把公开导出的 World Cup Matches raw JSON 放入 "
                    f"{PUBLIC_SNAPSHOT_IMPORT_DIR}/ 后重新生成 app；该入口只生成研究预览，不替代 TAB 最终人工校验。"
                ),
            }
        )
        return sanitize_public_payload(payload), sanitize_public_payload(preview_raw)

    raw_payload, load_error = load_snapshot_json(candidate)
    if load_error:
        status = "blocked_import_errors"
        preview_raw = empty_preview_raw(generated_at, status, load_error)
        payload = base_payload(generated_at, status)
        payload.update(
            {
                "selected_snapshot_file": candidate.name,
                "selected_snapshot_relative_path": relative_to_output(candidate, output_dir),
                "selected_snapshot_sha256": sha256_file(candidate) or "",
                "match_count": 0,
                "market_coverage": {},
                "issues": [{"field": "snapshot_json", "issue": load_error}],
                "recommended_next_action": "修复导入 JSON 的格式后重试；当前不允许发布正式 raw 或生成新增下注金额。",
            }
        )
        return sanitize_public_payload(payload), sanitize_public_payload(preview_raw)

    extracted, extraction_issues = extract_raw_snapshot(raw_payload)
    audit = audit_public_snapshot(extracted)
    issues.extend(extraction_issues)
    issues.extend(audit["issues"])
    status = "snapshot_import_preview_ready" if audit["preview_ready"] and not extraction_issues else "blocked_import_errors"
    preview_raw = build_preview_raw(generated_at, status, extracted, audit, candidate, output_dir)
    payload = base_payload(generated_at, status)
    payload.update(
        {
            "selected_snapshot_file": candidate.name,
            "selected_snapshot_relative_path": relative_to_output(candidate, output_dir),
            "selected_snapshot_sha256": sha256_file(candidate) or "",
            "source_generated_at": extracted.get("generated_at", ""),
            "match_count": audit["match_count"],
            "market_coverage": audit["market_coverage"],
            "covered_market_family_count": len([name for name, count in audit["market_coverage"].items() if count > 0]),
            "snapshot_import_preview_ready": bool(status == "snapshot_import_preview_ready"),
            "issues": issues[:50],
            "recommended_next_action": public_snapshot_next_action(status, audit),
        }
    )
    return sanitize_public_payload(payload), sanitize_public_payload(preview_raw)


def base_payload(generated_at: str, status: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "mode": "public_snapshot_importer",
        "status": status,
        "scope": "matches",
        "board_id": "world_cup_matches",
        "source_mode": "user_public_snapshot_import",
        "import_dir_relative_path": PUBLIC_SNAPSHOT_IMPORT_DIR,
        "snapshot_import_preview_ready": False,
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "truthfulness_note": (
            "该入口只接收用户或第三方工具导出的公开 raw JSON 并生成研究预览；"
            "不能证明 TAB 页面真实性，不替代授权 API raw、TAB 人工最终校验、hash/signature gate。"
        ),
    }


def build_public_snapshot_import_template() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mode": "public_snapshot_import_manifest_template",
        "save_dir": PUBLIC_SNAPSHOT_IMPORT_DIR,
        "preferred_snapshot_file": "world_cup_matches_public_snapshot.json",
        "accepted_shapes": [
            {"matches": [{"match": "Mexico v South Africa", "markets": {"Result": "Result\\nMexico\\n2.00"}}]},
            {"raw_snapshot": {"matches": [{"match": "Mexico v South Africa", "markets": {"Result": "..."}}]}},
        ],
        "required_fields": ["matches[].match", "matches[].markets"],
        "recommended_market_families": MARKET_FAMILIES,
        "publish_policy": {
            "formal_publish_allowed": False,
            "full_automation_allowed": False,
            "current_executable_new_stake_aud": 0,
            "manual_tab_final_verification_required": True,
            "approval_template": PUBLIC_SNAPSHOT_APPROVAL_TEMPLATE_JSON_LATEST,
            "approval_save_as": DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH,
            "publish_preflight": PUBLIC_SNAPSHOT_PUBLISH_PREFLIGHT_JSON_LATEST,
        },
    }


def select_snapshot_candidate(import_dir: Path) -> Path | None:
    if not import_dir.exists() or not import_dir.is_dir():
        return None
    preferred = import_dir / "world_cup_matches_public_snapshot.json"
    if preferred.exists() and preferred.is_file():
        return preferred
    candidates = [
        path
        for path in import_dir.glob("*.json")
        if path.is_file() and path.name not in EXCLUDED_IMPORT_NAMES and not path.name.startswith(".")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def load_snapshot_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"JSONDecodeError: {exc.msg} at line {exc.lineno}, column {exc.colno}"
    except OSError as exc:
        return {}, f"OSError: {exc}"
    if not isinstance(payload, dict):
        return {}, "snapshot root must be a JSON object"
    return payload, ""


def extract_raw_snapshot(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    if isinstance(payload.get("matches"), list):
        return dict(payload), issues
    raw_snapshot = payload.get("raw_snapshot")
    if isinstance(raw_snapshot, Mapping) and isinstance(raw_snapshot.get("matches"), list):
        extracted = dict(raw_snapshot)
        for key in ["generated_at", "captured_at", "refresh_id", "board", "source"]:
            if key not in extracted and key in payload:
                extracted[key] = payload[key]
        return extracted, issues
    issues.append({"field": "matches", "issue": "snapshot must contain matches[] or raw_snapshot.matches[]"})
    return {}, issues


def audit_public_snapshot(raw: Mapping[str, Any]) -> dict[str, Any]:
    matches = raw.get("matches") if isinstance(raw, Mapping) else None
    issues: list[dict[str, str]] = []
    if not isinstance(matches, list):
        return {
            "preview_ready": False,
            "match_count": 0,
            "market_coverage": {},
            "issues": [{"field": "matches", "issue": "matches must be a list"}],
        }
    market_coverage = {name: 0 for name in MARKET_FAMILIES}
    valid_match_count = 0
    for index, match in enumerate(matches):
        if not isinstance(match, Mapping):
            issues.append({"field": f"matches[{index}]", "issue": "match row must be an object"})
            continue
        match_name = str(match.get("match") or "").strip()
        markets = match.get("markets")
        if not match_name:
            issues.append({"field": f"matches[{index}].match", "issue": "match name missing"})
            continue
        if not isinstance(markets, Mapping):
            issues.append({"field": f"matches[{index}].markets", "issue": "markets must be an object"})
            continue
        valid_match_count += 1
        for market_name in MARKET_FAMILIES:
            if market_has_any_price(markets.get(market_name), market_name):
                market_coverage[market_name] += 1
    has_core_prices = any(market_coverage.get(name, 0) > 0 for name in ["Result", "Total Goals Over/Under", "Team Total Goals Over/Under"])
    if valid_match_count <= 0:
        issues.append({"field": "matches", "issue": "no valid match rows found"})
    if valid_match_count > 0 and not has_core_prices:
        issues.append({"field": "markets", "issue": "no Result, Total Goals, or Team Total price coverage found"})
    return {
        "preview_ready": valid_match_count > 0 and has_core_prices,
        "match_count": valid_match_count,
        "market_coverage": market_coverage,
        "issues": issues,
    }


def market_has_any_price(value: Any, market_name: str) -> bool:
    if isinstance(value, str):
        return bool(parse_market_pairs(value, market_name))
    if isinstance(value, Mapping):
        if any(is_price_like(item) for item in value.values()):
            return True
        outcomes = value.get("outcomes")
        if isinstance(outcomes, list):
            return any(isinstance(row, Mapping) and is_price_like(row.get("price")) for row in outcomes)
    if isinstance(value, list):
        return any(isinstance(row, Mapping) and is_price_like(row.get("price")) for row in value)
    return False


def is_price_like(value: Any) -> bool:
    try:
        price = float(str(value).strip())
    except (TypeError, ValueError):
        return False
    return 1.01 <= price <= 1000


def build_preview_raw(
    generated_at: str,
    status: str,
    raw: Mapping[str, Any],
    audit: Mapping[str, Any],
    candidate: Path,
    output_dir: Path,
) -> dict[str, Any]:
    preview = dict(raw)
    source_timestamp = raw.get("generated_at") or raw.get("captured_at") or "source_generated_at_missing"
    preview.update(
        {
            "schema_version": 1,
            "generated_at": source_timestamp,
            "captured_at": raw.get("captured_at") or source_timestamp,
            "source": "public_snapshot_import_preview",
            "source_mode": "user_public_snapshot_import_preview",
            "board_id": "world_cup_matches",
            "snapshot_import_status": status,
            "snapshot_import_preview_only": True,
            "selected_snapshot_file": candidate.name,
            "selected_snapshot_relative_path": relative_to_output(candidate, output_dir),
            "selected_snapshot_sha256": sha256_file(candidate) or "",
            "match_count": audit.get("match_count", 0),
            "market_coverage": audit.get("market_coverage", {}),
            "formal_publish_allowed": False,
            "full_automation_allowed": False,
            "current_executable_new_stake_aud": 0,
            "truthfulness_note": (
                "Public snapshot preview is research-only. It cannot be used as formal TAB raw without "
                "authorized source or final manual verification."
            ),
        }
    )
    if not isinstance(preview.get("matches"), list):
        preview["matches"] = []
    return preview


def empty_preview_raw(generated_at: str, status: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "source": "public_snapshot_import_preview",
        "source_mode": "user_public_snapshot_import_preview",
        "board_id": "world_cup_matches",
        "snapshot_import_status": status,
        "snapshot_import_preview_only": True,
        "matches": [],
        "reason": reason,
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
    }


def public_snapshot_next_action(status: str, audit: Mapping[str, Any]) -> str:
    if status == "snapshot_import_preview_ready":
        coverage = audit.get("market_coverage") or {}
        missing = [name for name in ["Result", "Total Goals Over/Under", "Team Total Goals Over/Under"] if not coverage.get(name)]
        if missing:
            return "Preview raw 已生成；继续补齐核心盘口覆盖：" + ", ".join(missing) + "。正式发布仍需 TAB 最终人工校验。"
        return "Preview raw 已生成；下一步是人工核对 TAB 页面并通过签名/发布预检，正式下注金额仍为 AUD 0。"
    if status == "blocked_import_errors":
        return "修复 public snapshot JSON 的 matches/markets 结构或价格字段后重试；当前保持 fail-closed。"
    return f"把公开导出的 Matches JSON 放到 {PUBLIC_SNAPSHOT_IMPORT_DIR}/ 后重试。"


def build_public_snapshot_approval_template(payload: Mapping[str, Any]) -> dict[str, Any]:
    return sanitize_public_payload(
        {
            "schema_version": 1,
            "mode": "public_snapshot_import_approval",
            "save_as": DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH,
            "scope": "matches",
            "board_id": payload.get("board_id", "world_cup_matches"),
            "selected_snapshot_file": payload.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": payload.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": payload.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": payload.get("preview_raw_sha256", ""),
            "snapshot_import_preview_ready": bool(payload.get("snapshot_import_preview_ready")),
            "approved_by_user": False,
            "operator_initials": "",
            "signed_at_aest": "",
            "source_verification_note": "",
            "required_manual_checks": [
                "确认 selected_snapshot_file 来自用户可审计的 TAB/公开盘口导出路径。",
                "确认 JSON 内 match、market、selection、line、decimal odds 未被手工篡改。",
                "确认 preview_raw_sha256 与页面显示值一致。",
                "确认该签名只允许进入后续显式 publish gate，不自动下注。",
            ],
            "forbidden_actions": [
                "不得把 approved_by_user 默认设为 true。",
                "不得自动登录 TAB、点击赔率、加入 Bet Slip 或提交投注。",
                "不得把 public snapshot preview 当成 TAB 官方真实性证明。",
            ],
        }
    )


def build_public_snapshot_publish_preflight(output_dir: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    output_dir = Path(output_dir)
    approval_path = output_dir / DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH
    approval_exists = approval_path.exists()
    approval = load_json(approval_path) if approval_exists else {}
    issues: list[dict[str, str]] = []
    preview_ready = bool(payload.get("snapshot_import_preview_ready"))
    if not preview_ready:
        issues.append({"field": "snapshot_import_preview_ready", "issue": "public snapshot preview is not ready"})
    if not approval_exists:
        issues.append({"field": "approval_file", "issue": f"missing {DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH}"})
    else:
        expected = {
            "mode": "public_snapshot_import_approval",
            "board_id": payload.get("board_id", "world_cup_matches"),
            "selected_snapshot_sha256": payload.get("selected_snapshot_sha256", ""),
            "preview_raw_sha256": payload.get("preview_raw_sha256", ""),
        }
        for field, expected_value in expected.items():
            if approval.get(field) != expected_value:
                issues.append(
                    {
                        "field": field,
                        "issue": f"approval value {approval.get(field) or 'missing'} != expected {expected_value or 'missing'}",
                    }
                )
        if approval.get("approved_by_user") is not True:
            issues.append({"field": "approved_by_user", "issue": "must be true in the manually signed approval file"})
        if not str(approval.get("operator_initials") or "").strip():
            issues.append({"field": "operator_initials", "issue": "operator initials are required"})
        if not str(approval.get("signed_at_aest") or "").strip():
            issues.append({"field": "signed_at_aest", "issue": "signed_at_aest is required"})
        if not str(approval.get("source_verification_note") or "").strip():
            issues.append({"field": "source_verification_note", "issue": "manual source verification note is required"})

    if not preview_ready:
        status = "waiting_for_snapshot_import"
    elif not approval_exists:
        status = "waiting_for_signature"
    elif issues:
        status = "blocked_signature_mismatch"
    else:
        status = "ready_for_snapshot_publish_preflight"
    passed = status == "ready_for_snapshot_publish_preflight"
    payload_out = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "public_snapshot_import_publish_preflight",
        "status": status,
        "scope": "matches",
        "board_id": payload.get("board_id", "world_cup_matches"),
        "approval_relative_path": DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH,
        "approval_file_sha256": sha256_file(approval_path) if approval_exists else "",
        "selected_snapshot_file": payload.get("selected_snapshot_file", ""),
        "selected_snapshot_sha256": payload.get("selected_snapshot_sha256", ""),
        "preview_raw_snapshot": payload.get("preview_raw_snapshot", ""),
        "preview_raw_sha256": payload.get("preview_raw_sha256", ""),
        "match_count": payload.get("match_count", 0),
        "market_coverage": payload.get("market_coverage", {}),
        "approved_by_user": bool(approval.get("approved_by_user")),
        "operator_initials": approval.get("operator_initials", ""),
        "signed_at_aest": approval.get("signed_at_aest", ""),
        "snapshot_publish_preflight_passed": passed,
        "publish_compatible_with_snapshot_preview": passed,
        "issues": issues[:50],
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "next_safe_action": public_snapshot_publish_preflight_next_action(status),
        "truthfulness_note": (
            "该预检只确认 public snapshot preview 与人工签名文件匹配；不证明 TAB 页面真实性，"
            "不写正式 raw，不生成下注金额。"
        ),
    }
    return sanitize_public_payload(payload_out)


def public_snapshot_publish_preflight_next_action(status: str) -> str:
    if status == "ready_for_snapshot_publish_preflight":
        return "Public snapshot 签名预检已通过；仍需显式 raw publish 命令和最终 safety gate，当前新增下注金额保持 AUD 0。"
    if status == "blocked_signature_mismatch":
        return "修复 approval 文件中的 hash、board、operator 或 source note 后重试；不要手工改 preview raw hash。"
    if status == "waiting_for_signature":
        return f"把签名文件保存到 {DEFAULT_PUBLIC_SNAPSHOT_APPROVAL_RELATIVE_PATH}，并匹配 snapshot/preview raw hash。"
    return "先导入有效 public snapshot JSON，生成 preview raw 后再签名。"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def relative_to_output(path: Path, output_dir: Path) -> str:
    try:
        return str(path.relative_to(output_dir))
    except ValueError:
        return path.name


def render_public_snapshot_import_markdown(payload: Mapping[str, Any]) -> str:
    coverage = payload.get("market_coverage") or {}
    lines = [
        "# Public Raw Snapshot Import",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- import_dir: `{payload.get('import_dir_relative_path', '')}`",
        f"- selected_snapshot: `{payload.get('selected_snapshot_file', '')}`",
        f"- selected_snapshot_sha256: `{payload.get('selected_snapshot_sha256', '')}`",
        f"- preview_raw_snapshot: `{payload.get('preview_raw_snapshot', '')}`",
        f"- preview_raw_sha256: `{payload.get('preview_raw_sha256', '')}`",
        f"- match_count: `{payload.get('match_count', 0)}`",
        f"- formal_publish_allowed: `{payload.get('formal_publish_allowed', False)}`",
        f"- full_automation_allowed: `{payload.get('full_automation_allowed', False)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next action: {md(payload.get('recommended_next_action'))}",
        "",
        "## Market Coverage",
        "",
        "| Market | Covered Matches |",
        "|---|---:|",
    ]
    if coverage:
        for name, count in coverage.items():
            lines.append(f"| {md(name)} | {count} |")
    else:
        lines.append("| - | 0 |")
    lines.extend(["", "## Issues", "", "| Field | Issue |", "|---|---|"])
    issues = payload.get("issues") or []
    if issues:
        for row in issues:
            lines.append(f"| `{md(row.get('field'))}` | {md(row.get('issue'))} |")
    else:
        lines.append("| - | No issues. |")
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}", ""])
    return "\n".join(lines)


def write_public_snapshot_import_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    coverage = payload.get("market_coverage") or {}
    issues = payload.get("issues") or []
    digest = str(payload.get("preview_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    table_rows = [[str(name), str(count)] for name, count in coverage.items()]
    if not table_rows:
        table_rows = [["-", "0"]]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Public Snapshot Import",
        subtitle="Research-only public raw snapshot importer. No formal publish and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Board", str(payload.get("board_id", ""))),
            ("Snapshot", str(payload.get("selected_snapshot_file", "")) or "pending"),
            ("Matches", str(payload.get("match_count", 0))),
            ("Preview SHA", short_digest),
            ("Issues", str(len(issues))),
            ("Formal Publish", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Snapshot Import",
                [
                    ("matches", float(payload.get("match_count", 0) or 0)),
                    ("market families", float(payload.get("covered_market_family_count", 0) or 0)),
                    ("issues", float(len(issues))),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Market", "Covered Matches"],
        table_rows=table_rows[:18],
    )


def render_public_snapshot_publish_preflight_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Public Snapshot Publish Preflight",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- approval_relative_path: `{payload.get('approval_relative_path', '')}`",
        f"- approval_file_sha256: `{payload.get('approval_file_sha256', '')}`",
        f"- selected_snapshot_file: `{payload.get('selected_snapshot_file', '')}`",
        f"- selected_snapshot_sha256: `{payload.get('selected_snapshot_sha256', '')}`",
        f"- preview_raw_snapshot: `{payload.get('preview_raw_snapshot', '')}`",
        f"- preview_raw_sha256: `{payload.get('preview_raw_sha256', '')}`",
        f"- match_count: `{payload.get('match_count', 0)}`",
        f"- approved_by_user: `{payload.get('approved_by_user', False)}`",
        f"- snapshot_publish_preflight_passed: `{payload.get('snapshot_publish_preflight_passed', False)}`",
        f"- publish_compatible_with_snapshot_preview: `{payload.get('publish_compatible_with_snapshot_preview', False)}`",
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


def write_public_snapshot_publish_preflight_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    issues = payload.get("issues") or []
    digest = str(payload.get("preview_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    detail_rows = [[str(row.get("field", "")), str(row.get("issue", ""))] for row in issues[:18]]
    if not detail_rows:
        detail_rows = [["-", "No issues."]]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Public Snapshot Publish Preflight",
        subtitle="Manual signature preflight. Research only, no automatic raw publish and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Board", str(payload.get("board_id", ""))),
            ("Matches", str(payload.get("match_count", 0))),
            ("Preview SHA", short_digest),
            ("Approved By User", str(bool(payload.get("approved_by_user"))).lower()),
            ("Preflight Passed", str(bool(payload.get("snapshot_publish_preflight_passed"))).lower()),
            ("Formal Publish", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Publish Preflight",
                [
                    ("passed", 1.0 if payload.get("snapshot_publish_preflight_passed") else 0.0),
                    ("issues", float(len(issues))),
                    ("blocked", 0.0 if payload.get("snapshot_publish_preflight_passed") else 1.0),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Field", "Issue"],
        table_rows=detail_rows,
    )


def render_public_snapshot_raw_publish_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Public Snapshot Raw Publish",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- ok: `{payload.get('ok', False)}`",
        f"- board_id: `{payload.get('board_id', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- selected_snapshot_file: `{payload.get('selected_snapshot_file', '')}`",
        f"- selected_snapshot_sha256: `{payload.get('selected_snapshot_sha256', '')}`",
        f"- preview_raw_snapshot: `{payload.get('preview_raw_snapshot', '')}`",
        f"- preview_raw_sha256: `{payload.get('preview_raw_sha256', '')}`",
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


def write_public_snapshot_raw_publish_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    issues = payload.get("issues") or []
    raw_gate = payload.get("raw_gate") or {}
    blocking = raw_gate.get("blocking_reasons") or []
    digest = str(payload.get("published_raw_sha256") or payload.get("preview_raw_sha256") or "")
    short_digest = f"{digest[:12]}...{digest[-8:]}" if len(digest) > 24 else digest or "pending"
    detail_rows = [[str(row.get("field", "")), str(row.get("issue", ""))] for row in issues[:12]]
    if not detail_rows:
        detail_rows = [["raw_gate", str(blocking[0]) if blocking else "No issues."]]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Public Snapshot Raw Publish",
        subtitle="Manual signature scoped publish. Matches only, no batch manifest and no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Board", str(payload.get("board_id", ""))),
            ("Refresh ID", str(payload.get("refresh_id", ""))),
            ("Published Raw", str(payload.get("published_raw_snapshot", "")) or "blocked"),
            ("Raw SHA", short_digest),
            ("Formal Raw Publish", str(bool(payload.get("formal_raw_publish_performed"))).lower()),
            ("Full Automation", "false"),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Raw Publish",
                [
                    ("published", 1.0 if payload.get("formal_raw_publish_performed") else 0.0),
                    ("issues", float(len(issues))),
                    ("raw gate blocked", 0.0 if payload.get("raw_gate_ready") else 1.0),
                ],
                "#1F4E79",
            )
        ],
        table_headers=["Field", "Issue"],
        table_rows=detail_rows,
    )


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
