from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .boards import BOARD_CONFIGS, BoardConfig, raw_age, raw_timestamp, read_json_with_error, refresh_driver
from .io import atomic_write_json


RAW_BATCH_MANIFEST = "raw_refresh_batch_latest.json"


@dataclass(frozen=True)
class RawRefreshTarget:
    board_id: str
    name: str
    source_url: str
    raw_snapshot: str
    parser_strategy: str
    refresh_method: str
    refresh_driver: str
    driver_configured: bool


def audit_raw_refresh(
    output_dir: Path,
    boards: List[BoardConfig] = BOARD_CONFIGS,
    max_raw_age_hours: float = 4.0,
    now: datetime | None = None,
) -> Dict:
    now = now or datetime.now(timezone.utc)
    targets = [build_target(board, output_dir, now, max_raw_age_hours) for board in boards if board.raw_snapshot]
    required = [target for target in targets if target["required_for_full_automation"]]
    batch_ready, batch_reason = raw_refresh_batch_status(required)
    manifest_ready, manifest_reason, batch_manifest = raw_refresh_batch_manifest_status(output_dir, required)
    ready_required = [target for target in required if target["refresh_ready"]]
    driver_ready_required = [target for target in required if target["driver_configured"]]
    blocking_reasons = []
    for target in required:
        if not target["raw_exists"]:
            blocking_reasons.append(f"{target['name']} raw snapshot is missing.")
        elif not target["raw_fresh"]:
            blocking_reasons.append(f"{target['name']} raw snapshot is stale.")
        if target["raw_exists"] and not target["raw_valid"]:
            blocking_reasons.extend(f"{target['name']} raw validation failed: {reason}" for reason in target["raw_validation_errors"])
        if not target["driver_configured"]:
            blocking_reasons.append(f"{target['name']} refresh driver is not configured.")
    if not batch_ready and batch_reason:
        blocking_reasons.append(batch_reason)
    if not manifest_ready and manifest_reason:
        blocking_reasons.append(manifest_reason)
    return {
        "generated_at": now.isoformat(),
        "max_raw_age_hours": max_raw_age_hours,
        "raw_refresh_ready": len(ready_required) == len(required) and batch_ready and manifest_ready,
        "refresh_driver_ready": len(driver_ready_required) == len(required),
        "refresh_batch_ready": batch_ready,
        "refresh_batch_manifest_ready": manifest_ready,
        "refresh_batch_manifest": batch_manifest,
        "required_target_count": len(required),
        "ready_required_target_count": len(ready_required),
        "driver_ready_required_target_count": len(driver_ready_required),
        "targets": targets,
        "blocking_reasons": blocking_reasons,
    }


def audit_staged_raw_refresh(
    output_dir: Path,
    boards: List[BoardConfig] = BOARD_CONFIGS,
    expected_refresh_id: str | None = None,
    max_raw_age_hours: float = 4.0,
    now: datetime | None = None,
) -> Dict:
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    targets = []
    blocking_reasons = []
    for board in boards:
        if not board.required_for_full_automation or not board.raw_snapshot:
            continue
        raw_path = output_dir / board.raw_snapshot
        raw, raw_parse_error = read_json_with_error(raw_path)
        timestamp = raw_timestamp(raw) if raw else None
        age_hours = raw_age(timestamp, now)
        raw_fresh = age_hours is not None and age_hours <= max_raw_age_hours
        validation = {"valid": False, "errors": [raw_parse_error]} if raw_parse_error else validate_raw_snapshot(board.board_id, raw)
        refresh_id = (raw or {}).get("refresh_id")
        refresh_id_matches = expected_refresh_id is None or refresh_id == expected_refresh_id
        target = {
            "board_id": board.board_id,
            "name": board.name,
            "raw_snapshot": board.raw_snapshot,
            "raw_exists": raw_path.exists(),
            "raw_parse_error": raw_parse_error,
            "raw_timestamp": timestamp,
            "refresh_id": refresh_id,
            "expected_refresh_id": expected_refresh_id,
            "refresh_id_matches_expected": refresh_id_matches,
            "sha256": sha256_file(raw_path) if raw_path.exists() else None,
            "raw_age_hours": age_hours,
            "raw_fresh": raw_fresh,
            "raw_valid": validation["valid"],
            "raw_validation_errors": validation["errors"],
            "refresh_ready": raw is not None and raw_fresh and validation["valid"] and refresh_id_matches,
        }
        targets.append(target)
        if not target["raw_exists"]:
            blocking_reasons.append(f"{board.name} staged raw snapshot is missing.")
        elif raw_parse_error:
            blocking_reasons.append(f"{board.name} staged raw snapshot is not parseable: {raw_parse_error}")
        elif not raw_fresh:
            blocking_reasons.append(f"{board.name} staged raw snapshot is stale or missing generated_at.")
        if target["raw_exists"] and not validation["valid"]:
            blocking_reasons.extend(f"{board.name} staged raw validation failed: {reason}" for reason in validation["errors"])
        if expected_refresh_id is not None and target["raw_exists"] and not refresh_id_matches:
            blocking_reasons.append(
                f"{board.name} staged raw refresh_id {refresh_id or 'missing'} does not match expected {expected_refresh_id}."
            )
    batch_ready, batch_reason = raw_refresh_batch_status(targets)
    manifest_ready, manifest_reason, batch_manifest = raw_refresh_batch_manifest_status(output_dir, targets, expected_refresh_id=expected_refresh_id)
    if not batch_ready and batch_reason:
        blocking_reasons.append(batch_reason)
    if not manifest_ready and manifest_reason:
        blocking_reasons.append(manifest_reason)
    ready_targets = [target for target in targets if target["refresh_ready"]]
    return {
        "generated_at": now.isoformat(),
        "expected_refresh_id": expected_refresh_id,
        "max_raw_age_hours": max_raw_age_hours,
        "staged_raw_ready": len(ready_targets) == len(targets) and batch_ready and manifest_ready,
        "refresh_batch_ready": batch_ready,
        "refresh_batch_manifest_ready": manifest_ready,
        "refresh_batch_manifest": batch_manifest,
        "required_target_count": len(targets),
        "ready_required_target_count": len(ready_targets),
        "targets": targets,
        "blocking_reasons": blocking_reasons,
    }


def raw_refresh_health(raw_refresh: Dict, refresh_error: str | None = None, refresh_diagnostics: Dict | None = None) -> Dict:
    targets = raw_refresh.get("targets", [])
    target_health = [raw_target_health(target) for target in targets]
    blocker_codes = sorted({code for target in target_health for code in target.get("blocker_codes", [])})
    blocker_codes.extend(refresh_error_blocker_codes(refresh_error or ""))
    if diagnostics_has_ai_controlled_access_rejection(refresh_diagnostics):
        blocker_codes.extend(["access_denied", "ai_controlled_access_rejected"])
    if not raw_refresh.get("refresh_batch_ready", True):
        blocker_codes.append("batch_refresh_id_mismatch")
    if not raw_refresh.get("refresh_batch_manifest_ready", True):
        blocker_codes.append("batch_manifest_mismatch")
    if refresh_error:
        blocker_codes.append("refresh_command_failed")
    blocker_codes = sorted(set(blocker_codes))
    partial = partial_research_refresh_summary(
        refresh_diagnostics,
        now=parse_iso_datetime(raw_refresh.get("generated_at")) or datetime.now(timezone.utc),
        freshness_sla_hours=float(raw_refresh.get("max_raw_age_hours") or 4.0),
    )
    return {
        "schema_version": 1,
        "generated_at": raw_refresh.get("generated_at"),
        "ready": bool(raw_refresh.get("raw_refresh_ready")),
        "status": "ready" if raw_refresh.get("raw_refresh_ready") else "blocked",
        "required_target_count": raw_refresh.get("required_target_count", 0),
        "ready_required_target_count": raw_refresh.get("ready_required_target_count", 0),
        "refresh_driver_ready": bool(raw_refresh.get("refresh_driver_ready")),
        "refresh_batch_ready": bool(raw_refresh.get("refresh_batch_ready")),
        "refresh_batch_manifest_ready": bool(raw_refresh.get("refresh_batch_manifest_ready")),
        "refresh_error": refresh_error or "",
        "blocker_codes": blocker_codes,
        "blocking_reasons": raw_refresh.get("blocking_reasons", []),
        "targets": target_health,
        "partial_research_refresh": partial,
        "access_policy": access_policy_status(blocker_codes, refresh_diagnostics),
        "recommended_next_action": raw_refresh_next_action(blocker_codes),
    }


def raw_target_health(target: Dict) -> Dict:
    codes = []
    errors = target.get("raw_validation_errors", []) or []
    if not target.get("raw_exists"):
        codes.append("missing_raw")
    if target.get("raw_exists") and not target.get("raw_fresh"):
        codes.append("stale_raw")
    if target.get("raw_exists") and not target.get("raw_valid"):
        codes.append("invalid_raw")
    if not target.get("driver_configured", True):
        codes.append("driver_missing")
    if target.get("raw_exists") and not target.get("refresh_id"):
        codes.append("missing_refresh_id")
    if any("Access Denied" in str(error) for error in errors):
        codes.extend(["access_denied", "ai_controlled_access_rejected"])
    if any(looks_like_route_mismatch(error) for error in errors):
        codes.append("route_mismatch")
    if any("coverage" in str(error).lower() for error in errors):
        codes.append("partial_coverage")
    return {
        "board_id": target.get("board_id"),
        "name": target.get("name"),
        "status": "ready" if target.get("refresh_ready") else "blocked",
        "blocker_codes": sorted(set(codes)),
        "raw_snapshot": target.get("raw_snapshot"),
        "raw_timestamp": target.get("raw_timestamp"),
        "raw_age_hours": target.get("raw_age_hours"),
        "raw_exists": bool(target.get("raw_exists")),
        "raw_fresh": bool(target.get("raw_fresh")),
        "raw_valid": bool(target.get("raw_valid")),
        "driver_configured": bool(target.get("driver_configured")),
        "refresh_id": target.get("refresh_id"),
        "validation_errors": errors,
    }


def partial_research_refresh_summary(
    refresh_diagnostics: Dict | None,
    *,
    now: datetime | None = None,
    freshness_sla_hours: float = 4.0,
) -> Dict:
    now = now or datetime.now(timezone.utc)
    if not isinstance(refresh_diagnostics, dict) or not refresh_diagnostics:
        return {
            "status": "not_attempted",
            "research_only_allowed": False,
            "freshness_status": "missing_diagnostics",
            "freshness_sla_hours": freshness_sla_hours,
            "generated_at": "",
            "age_hours": None,
            "fresh_within_sla": False,
            "attempted_board_count": 0,
            "successful_board_count": 0,
            "failed_board_count": 0,
            "successful_boards": [],
            "failed_boards": [],
            "matches_target_count": 0,
            "matches_target_source": "",
            "note": "本次 raw health 未附带刷新诊断，不能证明任何板块当前可研究。",
        }
    attempts = [item for item in refresh_diagnostics.get("attempts", []) if isinstance(item, dict)]
    board_meta = {
        str(board.refresh_board_id or board.board_id): {"board_id": board.board_id, "name": board.name}
        for board in BOARD_CONFIGS
    }
    latest_by_refresh_id: Dict[str, Dict] = {}
    for attempt in attempts:
        refresh_board_id = str(attempt.get("board_id") or "")
        if not refresh_board_id:
            continue
        latest_by_refresh_id[refresh_board_id] = attempt
    successful = []
    failed = []
    for refresh_board_id, attempt in latest_by_refresh_id.items():
        meta = board_meta.get(refresh_board_id, {"board_id": refresh_board_id, "name": refresh_board_id})
        row = {
            "refresh_board_id": refresh_board_id,
            "board_id": meta["board_id"],
            "name": meta["name"],
            "exit_code": attempt.get("exit_code"),
        "access_denied": bool(attempt.get("access_denied")),
        "ai_controlled_access_rejected": bool(
            attempt.get("ai_controlled_access_rejected")
            or attempt.get("access_policy_status") == "blocked_by_access_policy"
            or attempt.get("error_class") == "ai_controlled_access_rejected"
        ),
        "access_policy_status": attempt.get("access_policy_status") or "",
        "error_class": attempt.get("error_class") or "",
    }
        if attempt.get("exit_code") == 0 and not attempt.get("access_denied"):
            successful.append(row)
        else:
            failed.append(row)
    successful = sorted(successful, key=lambda row: row["refresh_board_id"])
    failed = sorted(failed, key=lambda row: row["refresh_board_id"])
    match_targets = int(refresh_diagnostics.get("matches_target_count") or 0)
    generated_at = str(refresh_diagnostics.get("finished_at") or refresh_diagnostics.get("generated_at") or "")
    generated_dt = parse_iso_datetime(generated_at)
    age_hours = round(max(0.0, (now - generated_dt).total_seconds() / 3600), 2) if generated_dt else None
    fresh_within_sla = bool(age_hours is not None and age_hours <= freshness_sla_hours)
    status = "partial_ready" if successful and failed else "all_attempted_ready" if successful else "blocked"
    freshness_status = (
        "fresh_research_only"
        if successful and fresh_within_sla
        else "stale_research_only"
        if successful
        else "blocked"
    )
    return {
        "status": status,
        "research_only_allowed": bool(successful),
        "freshness_status": freshness_status,
        "freshness_sla_hours": freshness_sla_hours,
        "generated_at": generated_at,
        "age_hours": age_hours,
        "fresh_within_sla": fresh_within_sla,
        "execution_allowed": False,
        "attempted_board_count": len(latest_by_refresh_id),
        "successful_board_count": len(successful),
        "failed_board_count": len(failed),
        "successful_boards": successful,
        "failed_boards": failed,
        "matches_target_count": match_targets,
        "matches_target_source": str(refresh_diagnostics.get("matches_target_source") or ""),
        "refresh_id": str(refresh_diagnostics.get("refresh_id") or ""),
        "diagnostics_status": str(refresh_diagnostics.get("status") or ""),
        "note": "成功板块只允许进入研究诊断；只要全量 raw/private/preflight 未通过，当前可执行新增下注仍为 AUD 0。",
    }


def normalize_partial_research_refresh(partial: Dict | None, now: datetime | None = None) -> Dict:
    """Recompute partial raw freshness at read time so old health files cannot stay fresh forever."""
    if not isinstance(partial, dict) or not partial:
        return partial_research_refresh_summary(None, now=now)
    now = now or datetime.now(timezone.utc)
    normalized = dict(partial)
    try:
        freshness_sla_hours = float(normalized.get("freshness_sla_hours") or 4.0)
    except (TypeError, ValueError):
        freshness_sla_hours = 4.0
    successful_boards = normalized.get("successful_boards") if isinstance(normalized.get("successful_boards"), list) else []
    failed_boards = normalized.get("failed_boards") if isinstance(normalized.get("failed_boards"), list) else []
    successful_count = int(normalized.get("successful_board_count") or len(successful_boards) or 0)
    failed_count = int(normalized.get("failed_board_count") or len(failed_boards) or 0)
    attempted_count = int(normalized.get("attempted_board_count") or successful_count + failed_count)
    generated_at = str(normalized.get("generated_at") or "")
    generated_dt = parse_iso_datetime(generated_at)
    age_hours = round(max(0.0, (now - generated_dt).total_seconds() / 3600), 2) if generated_dt else None
    fresh_within_sla = bool(age_hours is not None and age_hours <= freshness_sla_hours)
    if successful_count:
        freshness_status = "fresh_research_only" if fresh_within_sla else "stale_research_only"
    elif generated_at and not generated_dt:
        freshness_status = "timestamp_unparseable"
    else:
        freshness_status = str(normalized.get("freshness_status") or "missing_diagnostics")
    normalized.update(
        {
            "freshness_status": freshness_status,
            "freshness_sla_hours": freshness_sla_hours,
            "age_hours": age_hours,
            "fresh_within_sla": fresh_within_sla,
            "current_research_only_allowed": bool(successful_count and fresh_within_sla),
            "historical_research_evidence_available": bool(successful_count),
            "execution_allowed": False,
            "attempted_board_count": attempted_count,
            "successful_board_count": successful_count,
            "failed_board_count": failed_count,
        }
    )
    if successful_count and not fresh_within_sla:
        normalized["note"] = (
            f"Partial raw 已超过 {freshness_sla_hours:g} 小时 SLA，只能作为历史诊断证据；"
            "不能作为当前研究或下注执行依据。"
        )
    return normalized


def parse_iso_datetime(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def raw_refresh_next_action(blocker_codes: List[str]) -> str:
    codes = set(blocker_codes)
    if "ai_controlled_access_rejected" in codes:
        return (
            "TAB 已拒绝 AI controlled access；公开 raw 自动刷新必须 fail-closed。"
            "不要使用 headed fallback、验证码绕过、指纹伪装或 stealth browser。"
            "下一步接入官方/授权数据源，或由用户导出后导入快照；当前只允许 research-only 诊断，新增执行金额保持 AUD 0。"
        )
    if "route_mismatch" in codes:
        return "TAB 当前导航未列出该板块或深链路由到其他板块；先重新发现 Soccer live board list，若仍缺失则将该板块标记为 temporarily unavailable review queue，不用旧盘口生成建议。"
    if "access_denied" in codes:
        return "TAB 返回 Access Denied；自动 raw 保持 fail-closed，不使用旧盘口生成建议。"
    if "stale_raw" in codes:
        return "当前公开 raw 快照已过期；必须完成一次新的 TAB 只读刷新后才能生成日报。"
    if "batch_manifest_mismatch" in codes or "batch_refresh_id_mismatch" in codes:
        return "raw 文件批次不一致；重新生成完整批次并写入 batch manifest。"
    if "invalid_raw" in codes or "partial_coverage" in codes:
        return "raw 内容不满足覆盖或解析门禁；需要展开缺失盘口后重新刷新。"
    if "refresh_command_failed" in codes:
        return "检查 raw refresh 诊断输出和 Chrome/TAB 访问状态后重新执行只读刷新。"
    if "driver_missing" in codes:
        return "刷新脚本缺失或路径错误；先修复 refresh driver 配置。"
    if "missing_raw" in codes:
        return "缺少 required raw snapshot；先抓取完整 required board。"
    return "raw refresh gate 已通过。"


def refresh_error_blocker_codes(refresh_error: str) -> List[str]:
    codes: List[str] = []
    if looks_like_route_mismatch(refresh_error):
        codes.append("route_mismatch")
    if "Access Denied" in str(refresh_error) or "ai_controlled_access_rejected" in str(refresh_error):
        codes.extend(["access_denied", "ai_controlled_access_rejected"])
    if looks_like_partial_coverage(refresh_error):
        codes.append("partial_coverage")
    return codes


def diagnostics_has_ai_controlled_access_rejection(refresh_diagnostics: Dict | None) -> bool:
    if not isinstance(refresh_diagnostics, dict) or not refresh_diagnostics:
        return False
    if refresh_diagnostics.get("access_policy_status") == "blocked_by_access_policy":
        return True
    if refresh_diagnostics.get("access_policy_blocker_code") == "ai_controlled_access_rejected":
        return True
    for attempt in refresh_diagnostics.get("attempts") or []:
        if not isinstance(attempt, dict):
            continue
        if (
            attempt.get("ai_controlled_access_rejected")
            or attempt.get("access_policy_status") == "blocked_by_access_policy"
            or attempt.get("error_class") == "ai_controlled_access_rejected"
        ):
            return True
    return False


def access_policy_status(blocker_codes: List[str], refresh_diagnostics: Dict | None) -> Dict:
    blocked = "ai_controlled_access_rejected" in set(blocker_codes) or diagnostics_has_ai_controlled_access_rejection(refresh_diagnostics)
    return {
        "status": "blocked_by_access_policy" if blocked else "not_triggered",
        "blocker_code": "ai_controlled_access_rejected" if blocked else "",
        "automated_public_raw_refresh_allowed": False if blocked else True,
        "forbidden_recovery": ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"] if blocked else [],
        "allowed_recovery": ["official_data_feed", "user_authorized_manual_export_import", "research_only_from_existing_fresh_partial_raw"] if blocked else [],
        "next_safe_action": raw_refresh_next_action(["ai_controlled_access_rejected"]) if blocked else "",
    }


def looks_like_route_mismatch(value: object) -> bool:
    text = str(value or "").lower()
    return (
        "route mismatch" in text
        or "landed on 2026 world cup matches" in text
        or "live soccer nav may not list" in text
        or "tab live soccer nav" in text
        or "not currently listed" in text
    )


def looks_like_partial_coverage(value: object) -> bool:
    text = str(value or "").lower()
    return (
        "staged raw validation failed" in text
        or "below 90%" in text
        or "expected 48 teams" in text
        or "expected 12 groups" in text
        or "missing futures teams" in text
        or "missing groups" in text
        or "complete futures rows" in text
        or "complete group winner markets" in text
    )


def build_target(board: BoardConfig, output_dir: Path, now: datetime, max_raw_age_hours: float) -> Dict:
    raw_path = output_dir / board.raw_snapshot
    raw, raw_parse_error = read_json_with_error(raw_path)
    timestamp = raw_timestamp(raw) if raw else None
    age_hours = raw_age(timestamp, now)
    raw_fresh = age_hours is not None and age_hours <= max_raw_age_hours
    source_url = (raw or {}).get("url") or f"https://www.tab.com.au{board.tab_path}"
    driver = refresh_driver(board)
    driver_configured = bool(board.refresh_board_id) and refresh_driver_exists(output_dir, driver)
    validation = {"valid": False, "errors": [raw_parse_error]} if raw_parse_error else validate_raw_snapshot(board.board_id, raw)
    return {
        **asdict(
            RawRefreshTarget(
                board_id=board.board_id,
                name=board.name,
                source_url=source_url,
                raw_snapshot=board.raw_snapshot,
                parser_strategy=board.parser_strategy,
                refresh_method=board.refresh_method,
                refresh_driver=driver,
                driver_configured=driver_configured,
            )
        ),
        "required_for_full_automation": board.required_for_full_automation,
        "raw_exists": raw_path.exists(),
        "raw_parse_error": raw_parse_error,
        "raw_timestamp": timestamp,
        "refresh_id": (raw or {}).get("refresh_id"),
        "sha256": sha256_file(raw_path) if raw_path.exists() else None,
        "raw_age_hours": age_hours,
        "raw_fresh": raw_fresh,
        "raw_valid": validation["valid"],
        "raw_validation_errors": validation["errors"],
        "refresh_ready": raw is not None and raw_fresh and driver_configured and validation["valid"],
    }


def raw_refresh_batch_status(required_targets: List[Dict]) -> tuple[bool, str]:
    existing = [target for target in required_targets if target.get("raw_exists")]
    refresh_ids = {target.get("refresh_id") for target in existing if target.get("refresh_id")}
    missing = [target["name"] for target in existing if not target.get("refresh_id")]
    if not existing:
        return True, ""
    if not refresh_ids or missing:
        detail = ", ".join(sorted(str(item) for item in refresh_ids)) or "none"
        if missing:
            detail = f"{detail}; missing refresh_id: {', '.join(missing)}"
        return False, f"Raw snapshots are missing a required refresh_id batch marker: {detail}."
    if len(refresh_ids) > 1 or missing:
        detail = ", ".join(sorted(str(item) for item in refresh_ids))
        if missing:
            detail = f"{detail}; missing refresh_id: {', '.join(missing)}"
        return False, f"Raw snapshots are not from one refresh batch: {detail}."
    return True, ""


def raw_refresh_batch_manifest_status(
    output_dir: Path,
    required_targets: List[Dict],
    expected_refresh_id: str | None = None,
) -> tuple[bool, str, Dict]:
    existing = [target for target in required_targets if target.get("raw_exists")]
    if not existing:
        return True, "", {}
    manifest_path = Path(output_dir) / RAW_BATCH_MANIFEST
    manifest, parse_error = read_json_with_error(manifest_path)
    if parse_error:
        return False, f"Raw refresh batch manifest is not parseable: {parse_error}", {}
    if not manifest:
        return False, f"Raw refresh batch manifest is missing: {RAW_BATCH_MANIFEST}.", {}
    if expected_refresh_id is not None and manifest.get("refresh_id") != expected_refresh_id:
        return False, f"Raw refresh batch manifest refresh_id {manifest.get('refresh_id') or 'missing'} does not match expected {expected_refresh_id}.", manifest
    by_file = {artifact.get("raw_snapshot"): artifact for artifact in manifest.get("artifacts", [])}
    missing = []
    mismatches = []
    for target in existing:
        artifact = by_file.get(target.get("raw_snapshot"))
        if not artifact:
            missing.append(target.get("raw_snapshot"))
            continue
        if artifact.get("refresh_id") != target.get("refresh_id"):
            mismatches.append(f"{target.get('raw_snapshot')} refresh_id {artifact.get('refresh_id')} != {target.get('refresh_id')}")
        if artifact.get("sha256") != target.get("sha256"):
            mismatches.append(f"{target.get('raw_snapshot')} sha256 mismatch")
    if missing:
        return False, "Raw refresh batch manifest is missing artifacts: " + ", ".join(sorted(missing)) + ".", manifest
    if mismatches:
        return False, "Raw refresh batch manifest does not match current raw files: " + "; ".join(mismatches) + ".", manifest
    return True, "", manifest


def write_raw_refresh_batch_manifest(
    output_dir: Path,
    refresh_id: str,
    boards: List[BoardConfig] = BOARD_CONFIGS,
    generated_at: str | None = None,
) -> Path:
    output_dir = Path(output_dir)
    artifacts = []
    for board in boards:
        if not board.required_for_full_automation or not board.raw_snapshot:
            continue
        raw_path = output_dir / board.raw_snapshot
        raw, raw_parse_error = read_json_with_error(raw_path)
        if raw_parse_error:
            raise RuntimeError(f"raw snapshot is not parseable for batch manifest: {board.raw_snapshot}: {raw_parse_error}")
        if not raw_path.exists() or not raw:
            raise RuntimeError(f"raw snapshot missing for batch manifest: {board.raw_snapshot}")
        raw_refresh_id = raw.get("refresh_id")
        if raw_refresh_id != refresh_id:
            raise RuntimeError(f"raw snapshot refresh_id mismatch for batch manifest: {board.raw_snapshot}: {raw_refresh_id or 'missing'} != {refresh_id}")
        artifacts.append(
            {
                "board_id": board.board_id,
                "name": board.name,
                "raw_snapshot": board.raw_snapshot,
                "refresh_id": raw_refresh_id,
                "raw_timestamp": raw_timestamp(raw),
                "sha256": sha256_file(raw_path),
            }
        )
    payload = {
        "schema_version": 1,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "refresh_id": refresh_id,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    path = output_dir / RAW_BATCH_MANIFEST
    atomic_write_json(path, payload)
    return path


def sha256_file(path: Path) -> str | None:
    path = Path(path)
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refresh_driver_exists(output_dir: Path, refresh_driver: Optional[str]) -> bool:
    if not refresh_driver or refresh_driver == "not_configured":
        return False
    driver_path = refresh_driver.split()[0]
    pipeline_dir = output_dir.parent / "work" / "tab-research-pipeline"
    return (pipeline_dir / driver_path).exists()


def validate_raw_snapshot(board_id: str, raw: Optional[Dict]) -> Dict:
    if raw is None:
        return {"valid": False, "errors": ["raw snapshot missing"]}
    try:
        if board_id == "world_cup_matches":
            from .pipeline import CORE_MAIN_MARKETS, has_full_core_markets, market_has_prices, match_access_denied, pre_match_expected_names, quality_audit

            expected_names, in_play_excluded = pre_match_expected_names(raw)
            by_match = {match.get("match"): match for match in raw.get("matches", [])}
            detail_count = len([name for name in expected_names if name in by_match])
            full_count = sum(1 for name in expected_names if name in by_match and has_full_core_markets(by_match[name]))
            result_count = sum(1 for name in expected_names if name in by_match and market_has_prices(by_match[name], "Result"))
            access_denied = [name for name in expected_names if name in by_match and match_access_denied(by_match[name])]
            market_errors = sum(len(by_match[name].get("errors", [])) for name in expected_names if name in by_match)
            errors = []
            expected_count = len(expected_names)
            if expected_count <= 0:
                errors.append("no pre-match eligible match details remain for raw validation")
            elif detail_count / expected_count < 0.95:
                errors.append(f"detail coverage {detail_count}/{expected_count} below 95%")
            if expected_count > 0 and result_count != detail_count:
                errors.append(f"result market coverage {result_count}/{detail_count} does not match detail coverage")
            if expected_count > 0 and full_count / expected_count < 0.90:
                errors.append(f"full core coverage {full_count}/{expected_count} below 90% for {', '.join(CORE_MAIN_MARKETS)}")
            if access_denied:
                errors.append(f"Access Denied match detail pages: {', '.join(access_denied)}")
            if market_errors:
                errors.append(f"{market_errors} market expansion errors remain")
            integrity = quality_audit(raw).get("market_integrity_errors", [])
            if integrity:
                detail = "; ".join(
                    f"{item.get('match')}: {', '.join(item.get('errors', []))}" for item in integrity[:5]
                )
                errors.append(f"invalid decimal odds remain in match raw data: {detail}")
            return {
                "valid": not errors,
                "errors": errors,
                "pre_match_eligible_count": expected_count,
                "in_play_excluded_matches": in_play_excluded,
            }
        if board_id == "world_cup_futures":
            from .futures import futures_gate, parse_core_futures

            gate = futures_gate(parse_core_futures(raw.get("text", "")), raw)
            return {"valid": gate["automation_ready"], "errors": gate["blocking_reasons"]}
        if board_id == "world_cup_group_betting":
            from .group_betting import group_gate, parse_group_winners

            gate = group_gate(parse_group_winners(raw.get("text", "")))
            return {"valid": gate["automation_ready"], "errors": gate["blocking_reasons"]}
        if board_id == "world_cup_australia_markets":
            from .australia_markets import australia_gate, parse_australia_raw

            route_error = raw.get("route_error") or ""
            if raw.get("route_status") and raw.get("route_status") != "ok":
                return {"valid": False, "errors": [route_error or "2026 World Cup Australia Markets route mismatch"]}
            gate = australia_gate(parse_australia_raw(raw))
            return {"valid": gate["automation_ready"], "errors": gate["blocking_reasons"]}
        if board_id == "world_cup_team_futures_multi":
            from .team_futures_multi import parse_team_futures_multi, team_multi_gate

            gate = team_multi_gate(parse_team_futures_multi(raw.get("text", "")))
            return {"valid": gate["automation_ready"], "errors": gate["blocking_reasons"]}
    except Exception as exc:
        return {"valid": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    return {"valid": True, "errors": []}
