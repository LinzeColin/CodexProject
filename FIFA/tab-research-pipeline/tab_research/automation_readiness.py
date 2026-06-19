from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .artifacts import public_artifact_ref, sanitize_public_payload
from .automation_candidate import build_automation_candidate
from .io import atomic_write_json, atomic_write_text
from .latest_commit import latest_commit_artifact_consistency_issues
from .markdown_visuals import mermaid_bar, mermaid_pie
from .my_bets_bootstrap import (
    build_private_position_bootstrap_status,
    private_dir_for_output,
    report_date_from_preflight_or_latest,
)
from .partial_daily_research import (
    PARTIAL_DAILY_RESEARCH_JSON_LATEST,
    PARTIAL_DAILY_RESEARCH_MD_LATEST,
    PARTIAL_DAILY_RESEARCH_PDF_LATEST,
    partial_daily_research_status,
)
from .raw_refresh import audit_raw_refresh, raw_refresh_health
from .safety import audit_public_artifact_safety
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


AUTOMATION_READINESS_LATEST = "automation_readiness_latest.json"
AUTOMATION_READINESS_REPORT_LATEST = "automation_readiness_latest.md"
AUTOMATION_READINESS_PDF_LATEST = "automation_readiness_latest.pdf"
READINESS_EXPENSIVE_ARTIFACT_SUFFIXES = {".sqlite", ".sqlite3", ".db"}


def write_automation_readiness_summary(
    output_dir: Path,
    output_path: Path | None = None,
    command_status: Dict[str, Any] | None = None,
    latest_commit_override: Dict[str, Any] | None = None,
) -> Dict:
    payload = build_automation_readiness_summary(
        output_dir,
        command_status=command_status,
        latest_commit_override=latest_commit_override,
    )
    atomic_write_json(Path(output_path) if output_path else Path(output_dir) / AUTOMATION_READINESS_LATEST, payload)
    return payload


def write_automation_readiness_report(
    output_dir: Path,
    output_path: Path | None = None,
    summary: Dict[str, Any] | None = None,
    command_status: Dict[str, Any] | None = None,
    latest_commit_override: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = summary or build_automation_readiness_summary(
        output_dir,
        command_status=command_status,
        latest_commit_override=latest_commit_override,
    )
    path = Path(output_path) if output_path else Path(output_dir) / AUTOMATION_READINESS_REPORT_LATEST
    markdown = render_automation_readiness_markdown(payload)
    atomic_write_text(path, markdown)
    return {
        "path": public_artifact_ref(path),
        "status": payload.get("status", ""),
        "formal_report_publish_ready": bool(payload.get("formal_report_publish_ready")),
        "recurring_automation_ready": bool(payload.get("recurring_automation_ready")),
        "mermaid_blocks": markdown.count("```mermaid"),
    }


def write_automation_readiness_pdf(
    output_dir: Path,
    output_path: Path | None = None,
    summary: Dict[str, Any] | None = None,
    command_status: Dict[str, Any] | None = None,
    latest_commit_override: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = summary or build_automation_readiness_summary(
        output_dir,
        command_status=command_status,
        latest_commit_override=latest_commit_override,
    )
    path = Path(output_path) if output_path else Path(output_dir) / AUTOMATION_READINESS_PDF_LATEST
    blockers = payload.get("blockers") or []
    automation_candidate = payload.get("automation_candidate") or {}
    private_bootstrap = payload.get("private_position_bootstrap") or {}
    research_only = payload.get("research_only_daily_report") or {}
    pdf_summary = render_sidecar_pdf(
        path,
        title="TAB FIFA Automation Readiness Report",
        subtitle="Local report-generation gate audit. No automatic wagering execution.",
        summary_rows=[
            ("status", str(payload.get("status", ""))),
            ("formal_report_publish_ready", str(bool(payload.get("formal_report_publish_ready")))),
            ("recurring_automation_ready", str(bool(payload.get("recurring_automation_ready")))),
            ("research_only_daily_report_ready", str(bool(payload.get("research_only_daily_report_ready")))),
            ("research_only_recurring_candidate_ready", str(bool(payload.get("research_only_recurring_candidate_ready")))),
            ("latest_success_run_id", str((payload.get("latest_commit") or {}).get("run_id", ""))),
            ("raw_ready", str(bool((payload.get("raw_refresh") or {}).get("ready")))),
            ("partial_daily_status", str(research_only.get("status", ""))),
            ("partial_daily_pdf", str(research_only.get("pdf", ""))),
            ("private_position_status", str(private_bootstrap.get("status", ""))),
            ("candidate_cadence", str(automation_candidate.get("recommended_cadence", ""))),
        ],
        charts=[
            chart_from_items("Gate readiness mix", gate_readiness_items(payload), "#1F4E79"),
            chart_from_items("Gate scorecard", gate_score_items(payload), "#2E7D32"),
            chart_from_items("Blocker severity mix", blocker_severity_items(blockers), "#C62828"),
            chart_from_items("Next action priority", next_action_priority_items(payload), "#6A4C93"),
        ],
        table_headers=["Code", "Severity", "Message"],
        table_rows=[
            [str(item.get("code", "")), str(item.get("severity", "")), str(item.get("message", ""))]
            for item in blockers
        ],
    )
    return {
        **pdf_summary,
        "status": payload.get("status", ""),
        "formal_report_publish_ready": bool(payload.get("formal_report_publish_ready")),
        "recurring_automation_ready": bool(payload.get("recurring_automation_ready")),
        "research_only_daily_report_ready": bool(payload.get("research_only_daily_report_ready")),
    }


def build_automation_readiness_summary(
    output_dir: Path,
    command_status: Dict[str, Any] | None = None,
    latest_commit_override: Dict[str, Any] | None = None,
) -> Dict:
    output_dir = Path(output_dir)
    latest_commit = latest_commit_override or load_json(output_dir / "latest_commit.json")
    report_index = load_json(output_dir / "report_index_latest.json")
    raw_gate = audit_raw_refresh(output_dir)
    raw_health = raw_refresh_health(raw_gate, refresh_error=latest_raw_refresh_error(output_dir, raw_gate))
    artifact_paths = committed_artifact_paths(output_dir, latest_commit)
    artifact_safety = (
        audit_formal_artifact_safety_for_readiness(latest_commit, artifact_paths)
        if artifact_paths
        else missing_artifact_safety()
    )
    partial_daily = partial_daily_research_status(output_dir)
    partial_artifact_paths = partial_daily_artifact_paths(output_dir, partial_daily)
    partial_artifact_safety = (
        audit_public_artifact_safety(partial_artifact_paths) if partial_artifact_paths else missing_partial_artifact_safety()
    )
    output_safety = audit_readiness_output_safety(output_dir, artifact_paths, partial_artifact_paths)
    latest_attempt_preflight = load_latest_attempt_preflight(output_dir)
    technical_preflight = latest_attempt_preflight_status(output_dir, latest_commit)
    private_bootstrap_report_date = report_date_from_preflight_or_latest(latest_attempt_preflight, latest_commit)
    private_bootstrap = (
        build_private_position_bootstrap_status(private_dir_for_output(output_dir), private_bootstrap_report_date)
        if private_bootstrap_report_date
        else {}
    )
    latest_issues = latest_commit_artifact_consistency_issues(latest_commit) if latest_commit else ["latest_commit.json is missing"]
    report_index_issues = report_index_consistency_issues(latest_commit, report_index)
    automation_candidate = build_automation_candidate()
    latest_ready = latest_commit_ready(latest_commit) and not latest_issues
    research_only_daily_ready = research_only_daily_report_ready(
        partial_daily,
        output_safety,
        partial_artifact_safety,
    )
    research_only_candidate_ready = research_only_daily_ready and bool(automation_candidate.get("candidate_ready"))
    artifact_chain_ready = (
        latest_ready
        and raw_gate.get("raw_refresh_ready") is True
        and output_safety.get("automation_safety_ready") is True
        and artifact_safety.get("public_artifact_safety_ready") is True
        and not report_index_issues
    )
    live_artifacts_ready = artifact_chain_ready and bool(technical_preflight.get("publication_clear"))
    automation_entry_ready = bool(latest_commit.get("automation_entry_ready")) if latest_commit else False
    blockers = readiness_blockers(
        latest_ready=latest_ready,
        latest_issues=latest_issues,
        raw_health=raw_health,
        output_safety=output_safety,
        artifact_safety=artifact_safety,
        technical_preflight=technical_preflight,
        report_index_issues=report_index_issues,
        automation_entry_ready=automation_entry_ready,
    )
    return sanitize_public_payload(
        {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": readiness_status(
                live_artifacts_ready,
                automation_entry_ready,
                latest_ready,
                raw_gate,
                bool(technical_preflight.get("blocks_publication")),
                research_only_daily_ready=research_only_daily_ready,
            ),
            "formal_report_publish_ready": live_artifacts_ready,
            "recurring_automation_ready": live_artifacts_ready and automation_entry_ready,
            "research_only_daily_report_ready": research_only_daily_ready,
            "research_only_recurring_candidate_ready": research_only_candidate_ready,
            "research_only_recurring_ready": research_only_candidate_ready
            and bool(automation_candidate.get("activation_ready_after_authorization")),
            "command_status": command_status or {},
            "latest_commit": {
                "run_id": latest_commit.get("run_id", ""),
                "report_date": latest_commit.get("report_date", ""),
                "status": latest_commit.get("status", ""),
                "technical_automation_ready": bool(latest_commit.get("technical_automation_ready")),
                "automation_entry_ready": automation_entry_ready,
                "public_artifact_safety_ready": bool(latest_commit.get("public_artifact_safety_ready")),
                "ready_required_boards": latest_commit.get("ready_required_boards", ""),
                "issues": latest_issues,
            },
            "report_index": {
                "path": "report_index_latest.json" if report_index else "",
                "ready": bool(report_index) and not report_index_issues,
                "committed_latest_run_id": report_index.get("committed_latest_run_id", ""),
                "latest_success_run_id": report_index.get("latest_success_run_id", ""),
                "run_count": int(report_index.get("run_count") or 0) if report_index else 0,
                "issues": report_index_issues,
            },
            "raw_refresh": {
                "ready": bool(raw_gate.get("raw_refresh_ready")),
                "status": raw_health.get("status", ""),
                "ready_required": f"{raw_gate.get('ready_required_target_count', 0)}/{raw_gate.get('required_target_count', 0)}",
                "blocker_codes": raw_health.get("blocker_codes", []),
                "blocking_reasons": raw_gate.get("blocking_reasons", []),
                "recommended_next_action": raw_health.get("recommended_next_action", ""),
            },
            "public_safety": {
                "output_safety_ready": bool(output_safety.get("automation_safety_ready")),
                "output_blocking_reasons": output_safety.get("blocking_reasons", []),
                "artifact_safety_ready": bool(artifact_safety.get("public_artifact_safety_ready")),
                "artifact_issue_count": int(artifact_safety.get("public_artifact_issue_count") or 0),
                "artifact_blocking_reasons": artifact_safety.get("blocking_reasons", []),
                "partial_artifact_safety_ready": bool(partial_artifact_safety.get("public_artifact_safety_ready")),
                "partial_artifact_issue_count": int(partial_artifact_safety.get("public_artifact_issue_count") or 0),
                "partial_artifact_blocking_reasons": partial_artifact_safety.get("blocking_reasons", []),
            },
            "research_only_daily_report": {
                "ready": research_only_daily_ready,
                "status": partial_daily.get("status", ""),
                "report_date": partial_daily.get("report_date", ""),
                "generated_at": partial_daily.get("generated_at", ""),
                "execution_allowed": bool(partial_daily.get("execution_allowed")),
                "current_executable_new_stake_aud": int(partial_daily.get("current_executable_new_stake_aud") or 0),
                "partial_successful_board_count": int(partial_daily.get("partial_successful_board_count") or 0),
                "partial_attempted_board_count": int(partial_daily.get("partial_attempted_board_count") or 0),
                "unavailable_board_count": int(partial_daily.get("unavailable_board_count") or 0),
                "freshness_status": partial_daily.get("freshness_status", ""),
                "fresh_within_sla": bool(partial_daily.get("fresh_within_sla")),
                "board_scope_source": partial_daily.get("board_scope_source", ""),
                "partial_evidence_source": partial_daily.get("partial_evidence_source", ""),
                "pdf": partial_daily.get("pdf", ""),
                "dated_pdf": partial_daily.get("dated_pdf", ""),
                "artifact_safety_ready": bool(partial_artifact_safety.get("public_artifact_safety_ready")),
                "artifact_issue_count": int(partial_artifact_safety.get("public_artifact_issue_count") or 0),
                "policy": "可进入每4小时 research-only 报告生成；不发布正式下注日报，不解锁新增下注金额。",
                "recommended_next_action": partial_daily.get("recommended_next_action", ""),
            },
            "technical_preflight": technical_preflight,
            "private_position_bootstrap": private_bootstrap,
            "automation_candidate": {
                "ready": bool(automation_candidate.get("candidate_ready")),
                "status": automation_candidate.get("status", ""),
                "installed": bool(automation_candidate.get("installed")),
                "recommended_cadence": automation_candidate.get("recommended_cadence", ""),
                "rrule": automation_candidate.get("rrule", ""),
                "entrypoint": automation_candidate.get("entrypoint", ""),
                "activation_ready_after_authorization": bool(automation_candidate.get("activation_ready_after_authorization")),
                "blocking_reasons": automation_candidate.get("blocking_reasons", []),
            },
            "blocking_reasons": [item["message"] for item in blockers],
            "blockers": blockers,
            "next_actions": next_actions(blockers, raw_health, private_bootstrap),
            "artifacts_checked": [public_artifact_ref(path) for path in artifact_paths],
        }
    )


def load_json(path: Path) -> Dict:
    try:
        if not Path(path).exists():
            return {}
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def latest_raw_refresh_error(output_dir: Path, raw_gate: Dict) -> str:
    if raw_gate.get("raw_refresh_ready"):
        return ""
    raw_health = load_json(Path(output_dir) / "raw_refresh_health_latest.json")
    if raw_health.get("ready") is True or raw_health.get("status") == "ready":
        return ""
    return str(raw_health.get("refresh_error") or "")


def committed_artifact_paths(output_dir: Path, latest_commit: Dict) -> List[Path]:
    names = set()
    for section in ["artifacts", "run_artifacts"]:
        for value in (latest_commit.get(section) or {}).values():
            text = str(value or "")
            if text and "/" not in text and "\\" not in text:
                names.add(text)
    return [Path(output_dir) / name for name in sorted(names)]


def latest_commit_ready(payload: Dict) -> bool:
    return (
        bool(payload)
        and payload.get("status") == "ready_for_manual_report"
        and payload.get("technical_automation_ready") is True
        and payload.get("public_artifact_safety_ready") is True
        and payload.get("ready_required_boards") == "5/5"
    )


def report_index_consistency_issues(latest_commit: Dict, report_index: Dict) -> List[str]:
    issues: List[str] = []
    if not report_index:
        return ["report_index_latest.json is missing"]
    committed_run = str(latest_commit.get("run_id") or "")
    if not committed_run:
        issues.append("latest_commit run_id is missing")
    if str(report_index.get("committed_latest_run_id") or "") != committed_run:
        issues.append("report_index committed_latest_run_id does not match latest_commit")
    if str(report_index.get("latest_success_run_id") or "") != committed_run:
        issues.append("report_index latest_success_run_id does not match latest_commit")
    return issues


def latest_attempt_preflight_status(output_dir: Path, latest_commit: Dict) -> Dict[str, Any]:
    preflight = load_latest_attempt_preflight(output_dir)
    latest_run_id = str((latest_commit or {}).get("run_id") or "")
    if not preflight:
        return {
            "available": False,
            "publication_clear": True,
            "blocks_publication": False,
            "run_id": "",
            "path": "",
            "technical_preflight_ready": None,
            "automation_entry_ready": None,
            "newer_than_latest_success": False,
            "blocking_reasons": [],
            "failed_checks": [],
        }
    run_id = str(preflight.get("run_id") or "")
    newer_than_latest = bool(run_id and latest_run_id and run_id > latest_run_id)
    technical_ready = preflight.get("technical_preflight_ready") is True
    blocks_publication = technical_preflight_publication_blocker(preflight, latest_commit)
    failed_checks = [
        {
            "name": str(check.get("name", "")),
            "message": str(check.get("message", "")),
        }
        for check in (preflight.get("checks") or [])
        if check.get("passed") is not True
    ][:8]
    return {
        "available": True,
        "publication_clear": not blocks_publication,
        "blocks_publication": blocks_publication,
        "run_id": run_id,
        "path": str(preflight.get("_path") or ""),
        "technical_preflight_ready": technical_ready,
        "automation_entry_ready": bool(preflight.get("automation_entry_ready")),
        "newer_than_latest_success": newer_than_latest,
        "blocking_reasons": preflight.get("blocking_reasons", []),
        "failed_checks": failed_checks,
    }


def load_latest_attempt_preflight(output_dir: Path) -> Dict:
    output_dir = Path(output_dir)
    candidates: List[tuple[str, str, Dict[str, Any]]] = []
    for path in sorted(output_dir.glob("automation_preflight_*.json")):
        if path.name == "automation_preflight_latest.json":
            continue
        payload = load_json(path)
        run_id = str(payload.get("run_id") or path.stem.replace("automation_preflight_", ""))
        if not run_id:
            continue
        payload["_path"] = path.name
        candidates.append((run_id, path.name, payload))
    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[-1][2]
    payload = load_json(output_dir / "automation_preflight_latest.json")
    if payload:
        payload["_path"] = "automation_preflight_latest.json"
    return payload


def technical_preflight_publication_blocker(preflight: Dict, latest_commit: Dict) -> bool:
    if not preflight:
        return False
    run_id = str(preflight.get("run_id") or "")
    latest_run_id = str((latest_commit or {}).get("run_id") or "")
    if not run_id or not latest_run_id:
        return preflight.get("technical_preflight_ready") is not True
    if run_id <= latest_run_id:
        return False
    return preflight.get("technical_preflight_ready") is not True


def missing_artifact_safety() -> Dict:
    return {
        "public_artifact_safety_ready": False,
        "public_artifact_issue_count": 1,
        "blocking_reasons": ["latest_commit does not reference public artifacts"],
        "public_artifact_issues": [{"path": "latest_commit.json", "markers": ["missing_public_artifact_refs"]}],
    }


def audit_formal_artifact_safety_for_readiness(latest_commit: Dict[str, Any], artifact_paths: Iterable[Path]) -> Dict[str, Any]:
    scan_paths: List[Path] = []
    skipped: List[str] = []
    for path in artifact_paths:
        candidate = Path(path)
        if candidate.suffix.lower() in READINESS_EXPENSIVE_ARTIFACT_SUFFIXES and candidate.exists():
            skipped.append(candidate.name)
        else:
            scan_paths.append(candidate)
    audit = audit_public_artifact_safety(scan_paths) if scan_paths else {
        "public_artifact_safety_ready": True,
        "public_artifact_issue_count": 0,
        "public_artifact_issues": [],
        "blocking_reasons": [],
    }
    issues = list(audit.get("public_artifact_issues", []))
    blocking_reasons = list(audit.get("blocking_reasons", []))
    latest_declares_safe = latest_commit.get("public_artifact_safety_ready") is True
    if skipped and not latest_declares_safe:
        issues.append({"path": ",".join(skipped), "markers": ["expensive_artifact_requires_latest_commit_safety_ready"]})
        blocking_reasons.append("latest_commit does not confirm safety for skipped large artifacts")
    ready = bool(audit.get("public_artifact_safety_ready")) and (latest_declares_safe or not skipped)
    return {
        "public_artifact_safety_ready": ready,
        "public_artifact_issue_count": len(issues),
        "public_artifact_issues": issues,
        "blocking_reasons": blocking_reasons,
        "scan_scope": "readiness_non_sqlite_plus_latest_commit_cache",
        "skipped_large_artifacts": skipped,
    }


def missing_partial_artifact_safety() -> Dict:
    return {
        "public_artifact_safety_ready": False,
        "public_artifact_issue_count": 1,
        "blocking_reasons": ["partial daily research artifacts are missing"],
        "public_artifact_issues": [{"path": PARTIAL_DAILY_RESEARCH_PDF_LATEST, "markers": ["missing_partial_daily_report"]}],
    }


def audit_readiness_output_safety(
    output_dir: Path,
    artifact_paths: Iterable[Path],
    partial_artifact_paths: Iterable[Path],
) -> Dict[str, Any]:
    # Readiness is generated frequently by the app and scheduler. Scanning the full
    # historical outputs tree can be slow once PDF/SQLite artifacts accumulate, so
    # this gate checks only the current publish candidates and latest sidecars.
    candidates = {
        Path(path)
        for path in list(artifact_paths) + list(partial_artifact_paths)
        if Path(path).exists() and Path(path).suffix.lower() not in READINESS_EXPENSIVE_ARTIFACT_SUFFIXES
    }
    for name in [
        "automation_candidate_latest.json",
        "automation_candidate_latest.md",
        "automation_readiness_latest.json",
        "automation_readiness_latest.md",
    ]:
        path = Path(output_dir) / name
        if path.exists():
            candidates.add(path)
    if not candidates:
        return {
            "automation_safety_ready": True,
            "sensitive_artifact_count": 0,
            "sensitive_artifacts": [],
            "blocking_reasons": [],
            "scan_scope": "current_readiness_artifacts",
        }
    audit = audit_public_artifact_safety(sorted(candidates))
    return {
        "automation_safety_ready": bool(audit.get("public_artifact_safety_ready")),
        "sensitive_artifact_count": int(audit.get("public_artifact_issue_count") or 0),
        "sensitive_artifacts": audit.get("public_artifact_issues", []),
        "blocking_reasons": audit.get("blocking_reasons", []),
        "scan_scope": "current_readiness_artifacts",
    }


def partial_daily_artifact_paths(output_dir: Path, partial_daily: Dict[str, Any]) -> List[Path]:
    names = {
        PARTIAL_DAILY_RESEARCH_JSON_LATEST,
        PARTIAL_DAILY_RESEARCH_MD_LATEST,
        PARTIAL_DAILY_RESEARCH_PDF_LATEST,
    }
    for key in ["pdf", "dated_pdf"]:
        value = str(partial_daily.get(key) or "")
        if value and "/" not in value and "\\" not in value:
            names.add(value)
    return [Path(output_dir) / name for name in sorted(names) if (Path(output_dir) / name).exists()]


def research_only_daily_report_ready(
    partial_daily: Dict[str, Any],
    output_safety: Dict[str, Any],
    partial_artifact_safety: Dict[str, Any],
) -> bool:
    return (
        partial_daily.get("ready") is True
        and partial_daily.get("fresh_within_sla") is True
        and partial_daily.get("execution_allowed") is False
        and int(partial_daily.get("current_executable_new_stake_aud") or 0) == 0
        and output_safety.get("automation_safety_ready") is True
        and partial_artifact_safety.get("public_artifact_safety_ready") is True
    )


def readiness_status(
    live_ready: bool,
    automation_entry_ready: bool,
    latest_ready: bool,
    raw_gate: Dict,
    technical_preflight_blocked: bool = False,
    research_only_daily_ready: bool = False,
) -> str:
    if research_only_daily_ready and not live_ready:
        return "research_only_daily_ready_formal_blocked"
    if technical_preflight_blocked:
        return "current_run_preflight_blocked"
    if live_ready and automation_entry_ready:
        return "automation_ready"
    if live_ready:
        return "manual_report_ready_authorization_pending"
    if latest_ready and not raw_gate.get("raw_refresh_ready"):
        return "code_ready_live_data_blocked"
    return "blocked"


def readiness_blockers(
    *,
    latest_ready: bool,
    latest_issues: List[str],
    raw_health: Dict,
    output_safety: Dict,
    artifact_safety: Dict,
    technical_preflight: Dict,
    report_index_issues: List[str],
    automation_entry_ready: bool,
) -> List[Dict]:
    blockers: List[Dict] = []
    if not latest_ready:
        blockers.append({"code": "latest_commit_not_ready", "severity": "blocker", "message": "; ".join(latest_issues) or "latest_commit is not ready"})
    if raw_health.get("ready") is not True:
        blockers.append(
            {
                "code": "raw_refresh_blocked",
                "severity": "blocker",
                "message": "; ".join(raw_health.get("blocking_reasons", [])) or "raw refresh gate is blocked",
            }
        )
    if output_safety.get("automation_safety_ready") is not True:
        blockers.append(
            {
                "code": "output_safety_failed",
                "severity": "blocker",
                "message": "; ".join(output_safety.get("blocking_reasons", [])) or "output safety gate failed",
            }
        )
    if artifact_safety.get("public_artifact_safety_ready") is not True:
        blockers.append(
            {
                "code": "public_artifact_safety_failed",
                "severity": "blocker",
                "message": "; ".join(artifact_safety.get("blocking_reasons", [])) or "public artifact safety gate failed",
            }
        )
    if technical_preflight.get("blocks_publication") is True:
        blockers.append(
            {
                "code": "current_preflight_blocked",
                "severity": "blocker",
                "message": "; ".join(technical_preflight.get("blocking_reasons", [])) or "latest attempted technical preflight failed",
            }
        )
    if report_index_issues:
        blockers.append({"code": "report_index_inconsistent", "severity": "blocker", "message": "; ".join(report_index_issues)})
    if not automation_entry_ready:
        blockers.append({"code": "recurring_authorization_missing", "severity": "authorization", "message": "user has not authorized recurring automation"})
    return blockers


def next_actions(blockers: Iterable[Dict], raw_health: Dict, private_bootstrap: Dict | None = None) -> List[str]:
    actions: List[str] = []
    codes = {item.get("code") for item in blockers}
    if "raw_refresh_blocked" in codes:
        action = str(raw_health.get("recommended_next_action") or "")
        if action:
            actions.append(action)
    if "report_index_inconsistent" in codes:
        actions.append("重新生成 report_index_latest.json，并确认 latest_success_run_id 与 latest_commit.json 一致。")
    if "latest_commit_not_ready" in codes or "public_artifact_safety_failed" in codes:
        actions.append("保留上一个成功 latest_commit，修复 public artifact safety 后重跑日报。")
    if "current_preflight_blocked" in codes:
        bootstrap_action = str((private_bootstrap or {}).get("next_action") or "")
        actions.append(bootstrap_action or "补齐当日私有持仓快照；通过 technical preflight 后再发布当天正式报告。")
    if "recurring_authorization_missing" in codes:
        actions.append("在用户明确授权前仅允许手动/一次性报告生成，不创建 recurring automation。")
    return actions or ["当前 automation readiness gate 已通过。"]


def render_automation_readiness_markdown(summary: Dict[str, Any]) -> str:
    latest = summary.get("latest_commit") or {}
    report_index = summary.get("report_index") or {}
    raw_refresh = summary.get("raw_refresh") or {}
    public_safety = summary.get("public_safety") or {}
    technical_preflight = summary.get("technical_preflight") or {}
    private_bootstrap = summary.get("private_position_bootstrap") or {}
    automation_candidate = summary.get("automation_candidate") or {}
    research_only = summary.get("research_only_daily_report") or {}
    blockers = summary.get("blockers") or []
    command_status = summary.get("command_status") or {}
    lines = [
        "# TAB FIFA Automation Readiness Report",
        "",
        "本报告用于判断本地系统是否可以发布正式盘口研究日报或进入 recurring automation。它只做报告生成审计，不执行下注。",
        "",
        "## Executive Status",
        "",
        f"- status: `{summary.get('status', '')}`",
        f"- formal_report_publish_ready: `{bool(summary.get('formal_report_publish_ready'))}`",
        f"- recurring_automation_ready: `{bool(summary.get('recurring_automation_ready'))}`",
        f"- research_only_daily_report_ready: `{bool(summary.get('research_only_daily_report_ready'))}`",
        f"- research_only_recurring_candidate_ready: `{bool(summary.get('research_only_recurring_candidate_ready'))}`",
        f"- latest_success_run_id: `{latest.get('run_id', '')}`",
        f"- report_date: `{latest.get('report_date', '')}`",
        f"- partial_daily_status: `{research_only.get('status', '')}` / scope `{research_only.get('board_scope_source', '')}` / PDF `{research_only.get('pdf', '')}` / stake `AUD {research_only.get('current_executable_new_stake_aud', 0)}`",
        f"- private_position_status: `{private_bootstrap.get('status', '')}`",
        f"- command_mode: `{command_status.get('mode', '')}`",
        "",
        "## Visual Summary",
        "",
        "### Gate readiness mix",
        "",
        mermaid_pie("Gate readiness mix", gate_readiness_items(summary)),
        "",
        "### Gate scorecard",
        "",
        mermaid_bar("Gate scorecard", gate_score_items(summary), y_label="ready score"),
        "",
        "### Blocker severity mix",
        "",
        mermaid_pie("Blocker severity mix", blocker_severity_items(blockers)),
        "",
        "### Next action priority",
        "",
        mermaid_bar("Next action priority", next_action_priority_items(summary), y_label="priority"),
        "",
        "## Gate Matrix",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
        f"| latest success pointer | {status_word(not latest.get('issues'))} | `{latest.get('run_id', '')}` / `{latest.get('ready_required_boards', '')}` |",
        f"| report index consistency | {status_word(report_index.get('ready'))} | committed `{report_index.get('committed_latest_run_id', '')}` / success `{report_index.get('latest_success_run_id', '')}` |",
        f"| TAB raw freshness | {status_word(raw_refresh.get('ready'))} | ready `{raw_refresh.get('ready_required', '')}` / status `{raw_refresh.get('status', '')}` |",
        f"| research-only daily PDF | {status_word(research_only.get('ready'))} | `{research_only.get('status', '')}` / `{research_only.get('board_scope_source', '')}` / `{research_only.get('partial_successful_board_count', 0)}/{research_only.get('partial_attempted_board_count', 0)}` / stake `AUD {research_only.get('current_executable_new_stake_aud', 0)}` |",
        f"| current technical preflight | {status_word(technical_preflight.get('publication_clear'))} | run `{technical_preflight.get('run_id', '')}` / technical `{technical_preflight.get('technical_preflight_ready')}` |",
        f"| private position bootstrap | {status_word(private_bootstrap.get('ready'))} | `{private_bootstrap.get('report_date', '')}` / `{private_bootstrap.get('status', '')}` |",
        f"| output safety | {status_word(public_safety.get('output_safety_ready'))} | blockers `{len(public_safety.get('output_blocking_reasons') or [])}` |",
        f"| artifact safety | {status_word(public_safety.get('artifact_safety_ready'))} | issues `{public_safety.get('artifact_issue_count', 0)}` |",
        f"| automation candidate | {status_word(automation_candidate.get('ready'))} | `{automation_candidate.get('recommended_cadence', '')}` / `{automation_candidate.get('status', '')}` |",
        f"| recurring authorization | {status_word(summary.get('recurring_automation_ready'))} | authorization remains user-controlled |",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(
            f"- `{item.get('code', '')}` / `{item.get('severity', '')}`: {item.get('message', '')}"
            for item in blockers
        )
    else:
        lines.append("- 无阻塞项。")
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            *[f"- {item}" for item in (summary.get("next_actions") or [])],
            "",
            "## Public Artifacts Checked",
            "",
            *[f"- `{item}`" for item in (summary.get("artifacts_checked") or [])],
        ]
    )
    return "\n".join(lines)


def status_word(value: Any) -> str:
    return "ready" if bool(value) else "blocked"


def gate_readiness_items(summary: Dict[str, Any]) -> List[tuple[str, float]]:
    states = gate_states(summary)
    return [
        ("ready", sum(1 for _name, ready in states if ready)),
        ("blocked", sum(1 for _name, ready in states if not ready)),
    ]


def gate_score_items(summary: Dict[str, Any]) -> List[tuple[str, float]]:
    return [(name, 1.0 if ready else 0.0) for name, ready in gate_states(summary)]


def gate_states(summary: Dict[str, Any]) -> List[tuple[str, bool]]:
    latest = summary.get("latest_commit") or {}
    report_index = summary.get("report_index") or {}
    raw_refresh = summary.get("raw_refresh") or {}
    public_safety = summary.get("public_safety") or {}
    technical_preflight = summary.get("technical_preflight") or {}
    private_bootstrap = summary.get("private_position_bootstrap") or {}
    automation_candidate = summary.get("automation_candidate") or {}
    research_only = summary.get("research_only_daily_report") or {}
    return [
        ("latest pointer", not bool(latest.get("issues"))),
        ("report index", bool(report_index.get("ready"))),
        ("raw freshness", bool(raw_refresh.get("ready"))),
        ("research-only daily", bool(research_only.get("ready"))),
        ("current preflight", bool(technical_preflight.get("publication_clear", True))),
        ("private position", bool(private_bootstrap.get("ready"))),
        ("output safety", bool(public_safety.get("output_safety_ready"))),
        ("artifact safety", bool(public_safety.get("artifact_safety_ready"))),
        ("automation candidate", bool(automation_candidate.get("ready"))),
        ("recurring gate", bool(summary.get("recurring_automation_ready"))),
    ]


def blocker_severity_items(blockers: Iterable[Dict]) -> List[tuple[str, float]]:
    counts: Dict[str, int] = {}
    for blocker in blockers:
        severity = str(blocker.get("severity") or "unknown")
        counts[severity] = counts.get(severity, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0])) or [("none", 1.0)]


def next_action_priority_items(summary: Dict[str, Any]) -> List[tuple[str, float]]:
    blockers = {item.get("code") for item in (summary.get("blockers") or [])}
    rows = []
    priorities = [
        ("refresh raw", "raw_refresh_blocked", 100),
        ("fix private snapshot", "current_preflight_blocked", 95),
        ("fix public safety", "public_artifact_safety_failed", 90),
        ("repair latest pointer", "latest_commit_not_ready", 80),
        ("repair report index", "report_index_inconsistent", 70),
        ("authorize recurring", "recurring_authorization_missing", 40),
    ]
    for label, code, priority in priorities:
        if code in blockers:
            rows.append((label, float(priority)))
    return rows or [("ready", 100.0)]
