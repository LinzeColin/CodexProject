from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json, atomic_write_text


MACOS_PUBLIC_ACCEPTANCE_SCHEMA = "PFIOSMacOSPublicAcceptanceSummaryV1"
RUNTIME_SCHEMA = "PFIOSMacOSRuntimeAcceptanceV1"
UI_SCHEMA = "PFIOSUIVisualAcceptanceV1"


def build_macos_public_acceptance_summary(
    *,
    project_root: Path | str = PROJECT_ROOT,
    runtime_evidence: Path | str | None = None,
    ui_evidence: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    runtime_path = Path(runtime_evidence).expanduser() if runtime_evidence else root / "data/systemAudit/MacOSRuntimeAcceptance_latest.json"
    ui_path = Path(ui_evidence).expanduser() if ui_evidence else root / "data/systemAudit/UIVisualAcceptance_latest.json"

    runtime_payload = _read_payload(runtime_path)
    ui_payload = _read_payload(ui_path)
    runtime = _summarize_runtime(runtime_payload)
    ui = _summarize_ui(ui_payload)
    sources = [runtime, ui]
    source_failures = [source for source in sources if source["status"] != "Pass"]
    overall_status = "Pass" if not source_failures else "Blocked"

    payload: dict[str, Any] = {
        "schema": MACOS_PUBLIC_ACCEPTANCE_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS Public Acceptance Summary",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": overall_status,
        "summary": {
            "sources_total": len(sources),
            "sources_pass": sum(1 for source in sources if source["status"] == "Pass"),
            "sources_blocked": len(source_failures),
            "runtime_status": runtime["status"],
            "ui_status": ui["status"],
        },
        "evidence_sources": sources,
        "coverage": _coverage(runtime_payload, ui_payload),
        "privacy_redaction": {
            "local_paths_included": False,
            "browser_executable_included": False,
            "screenshot_path_included": False,
            "pid_or_process_output_included": False,
            "raw_logs_included": False,
            "private_data_included": False,
        },
        "heavy_smoke_policy": (
            "This public summary is generated from existing local evidence only. It does not run "
            "scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, market refresh, "
            "broker connections, orders, payments, or holdings writes."
        ),
        "safety_boundary": (
            "GitHub-safe sanitized summary. Raw local evidence, screenshots, browser paths, PIDs, "
            "absolute project paths, private data, and runtime logs stay local and gitignored."
        ),
        "next_action": (
            "Use this summary for GitHub handoff. Refresh raw local runtime/UI evidence first if "
            "macOS behavior changes, then regenerate this public summary."
        ),
    }
    _assert_public_payload(payload)
    return payload


def write_macos_public_acceptance_summary(
    *,
    output_dir: Path | str,
    project_root: Path | str = PROJECT_ROOT,
    runtime_evidence: Path | str | None = None,
    ui_evidence: Path | str | None = None,
) -> dict[str, Any]:
    payload = build_macos_public_acceptance_summary(
        project_root=project_root,
        runtime_evidence=runtime_evidence,
        ui_evidence=ui_evidence,
    )
    target = Path(output_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    json_path = target / f"MacOSAcceptancePublicSummary_{stamp}.json"
    latest_json = target / "MacOSAcceptancePublicSummary_latest.json"
    latest_md = target / "MacOSAcceptancePublicSummary_latest.md"
    payload["outputs"] = {
        "json": _public_relative_path(json_path, Path(project_root).expanduser().resolve()),
        "latest_json": _public_relative_path(latest_json, Path(project_root).expanduser().resolve()),
        "latest_markdown": _public_relative_path(latest_md, Path(project_root).expanduser().resolve()),
    }
    _assert_public_payload(payload)
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    atomic_write_text(latest_md, macos_public_acceptance_markdown(payload))
    return payload


def macos_public_acceptance_markdown(payload: dict[str, Any]) -> str:
    sources = payload.get("evidence_sources", [])
    coverage = payload.get("coverage", [])
    lines = [
        "# PFI macOS Public Acceptance Summary",
        "",
        f"- Schema: `{payload.get('schema')}`",
        f"- Status: `{payload.get('status')}`",
        f"- Generated at: `{payload.get('generated_at')}`",
        "",
        "## Evidence Sources",
        "",
        "| Source | Status | Raw schema | Generated at | Pass/Fail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source in sources:
        summary = source.get("summary", {})
        lines.append(
            "| "
            f"{source.get('source')} | "
            f"{source.get('status')} | "
            f"{source.get('raw_schema')} | "
            f"{source.get('raw_generated_at', 'Missing')} | "
            f"{summary.get('pass', 0)}/{summary.get('fail', 0)} |"
        )
    lines.extend(["", "## Coverage", "", "| Gate | Status | Evidence |", "| --- | --- | --- |"])
    for item in coverage:
        lines.append(f"| {item.get('gate')} | {item.get('status')} | {item.get('evidence')} |")
    lines.extend(
        [
            "",
            "## Privacy Boundary",
            "",
            "- Raw local JSON evidence, screenshots, browser executable paths, process IDs, absolute project paths, and runtime logs stay local.",
            "- This summary is safe to commit because it only stores schemas, statuses, counts, gate names, and sanitized evidence.",
            "",
            "## Heavy Smoke Policy",
            "",
            payload.get("heavy_smoke_policy", ""),
            "",
        ]
    )
    text = "\n".join(lines)
    _assert_public_text(text)
    return text


def _read_payload(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _summarize_runtime(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return _missing_source("runtime", RUNTIME_SCHEMA)
    summary = _summary_counts(payload.get("summary", {}))
    failed_checks = _failed_check_names(payload.get("checks", []), name_key="check")
    return {
        "source": "MacOSRuntimeAcceptance_latest.json",
        "raw_schema": payload.get("schema", "Unknown"),
        "raw_generated_at": payload.get("generated_at", "Missing"),
        "status": "Pass" if payload.get("schema") == RUNTIME_SCHEMA and payload.get("status") == "Pass" and not failed_checks else "Blocked",
        "summary": summary,
        "launch_method": payload.get("launch_method", "Unknown"),
        "started_by_acceptance": bool(payload.get("started_by_acceptance", False)),
        "failed_checks": failed_checks,
    }


def _summarize_ui(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return _missing_source("ui", UI_SCHEMA)
    summary = _summary_counts(payload.get("summary", {}))
    failed_checks = _failed_check_names(payload.get("checks", []), name_key="name")
    metrics = payload.get("visual_metrics", {}) if isinstance(payload.get("visual_metrics", {}), dict) else {}
    return {
        "source": "UIVisualAcceptance_latest.json",
        "raw_schema": payload.get("schema", "Unknown"),
        "raw_generated_at": payload.get("generated_at", "Missing"),
        "status": "Pass" if payload.get("schema") == UI_SCHEMA and payload.get("status") == "Pass" and not failed_checks else "Blocked",
        "summary": summary,
        "started_by_acceptance": bool(payload.get("started_by_acceptance", False)),
        "screenshot_bytes": int(metrics.get("screenshot_bytes", 0) or 0),
        "viewport": str(metrics.get("viewport", "Unknown")),
        "failed_checks": failed_checks,
    }


def _missing_source(source: str, expected_schema: str) -> dict[str, Any]:
    return {
        "source": f"{source}_latest.json",
        "raw_schema": expected_schema,
        "raw_generated_at": "Missing",
        "status": "Blocked",
        "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
        "failed_checks": [f"Missing {expected_schema} evidence"],
    }


def _coverage(runtime_payload: dict[str, Any] | None, ui_payload: dict[str, Any] | None) -> list[dict[str, str]]:
    return [
        _coverage_item("App open runtime acceptance", _runtime_check(runtime_payload, "AppOpenLaunched")),
        _coverage_item("Local health after app start", _runtime_check(runtime_payload, "HealthAfterStart")),
        _coverage_item("Cache delete refusal while running", _runtime_check(runtime_payload, "CleanCacheRefusesWhileRunning")),
        _coverage_item("Stop command and post-stop health", _runtime_check(runtime_payload, "HealthAfterStop")),
        _coverage_item("Post-stop cache dry-run", _runtime_check(runtime_payload, "CleanCacheDryRunAfterStop")),
        _coverage_item("Rendered PFI workspace", _ui_check(ui_payload, "VisibleText:PFI")),
        _coverage_item("macOS lifecycle panel visible", _ui_check(ui_payload, "VisibleText:macOS 生命周期")),
        _coverage_item("Runtime evidence visible in UI", _ui_check(ui_payload, "VisibleText:运行时验收证据")),
        _coverage_item("Lifecycle action buttons visible", _all_ui_checks(ui_payload, ["LifecycleButton:开发检查", "LifecycleButton:轻量验收", "LifecycleButton:生命周期验收"])),
        _coverage_item("No visible runtime errors", _all_ui_checks(ui_payload, ["NoVisibleError:Traceback", "NoVisibleError:ModuleNotFoundError", "NoVisibleError:ImportError:", "NoVisibleError:Connection lost"])),
        _coverage_item("Screenshot captured", _ui_check(ui_payload, "ScreenshotCaptured")),
    ]


def _coverage_item(gate: str, passed: bool) -> dict[str, str]:
    return {
        "gate": gate,
        "status": "Pass" if passed else "Blocked",
        "evidence": "sanitized pass/fail only; raw local evidence stays gitignored",
    }


def _runtime_check(payload: dict[str, Any] | None, check_name: str) -> bool:
    if not payload or payload.get("schema") != RUNTIME_SCHEMA:
        return False
    return any(row.get("check") == check_name and row.get("status") == "Pass" for row in _dict_rows(payload.get("checks", [])))


def _ui_check(payload: dict[str, Any] | None, check_name: str) -> bool:
    if not payload or payload.get("schema") != UI_SCHEMA:
        return False
    return any(row.get("name") == check_name and row.get("status") == "Pass" for row in _dict_rows(payload.get("checks", [])))


def _all_ui_checks(payload: dict[str, Any] | None, names: list[str]) -> bool:
    return all(_ui_check(payload, name) for name in names)


def _failed_check_names(rows: Any, *, name_key: str) -> list[str]:
    names: list[str] = []
    for row in _dict_rows(rows):
        if row.get("status") == "Fail":
            names.append(str(row.get(name_key, "Unknown")))
    return names[:20]


def _dict_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _summary_counts(summary: Any) -> dict[str, int]:
    payload = summary if isinstance(summary, dict) else {}
    return {
        "pass": int(payload.get("pass", 0) or 0),
        "fail": int(payload.get("fail", 0) or 0),
        "info": int(payload.get("info", 0) or 0),
        "total": int(payload.get("total", 0) or 0),
    }


def _public_relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return path.name


def _assert_public_payload(payload: dict[str, Any]) -> None:
    _assert_public_text(json.dumps(payload, ensure_ascii=False, default=str))


def _assert_public_text(text: str) -> None:
    forbidden = [
        "/Users/",
        "/Applications/",
        "Contents/MacOS",
        "Google Chrome.app",
        "Microsoft Edge.app",
        "Chromium.app",
        ".png",
        ".log",
        "Process id",
        " pid ",
        "opened=/",
        "file://",
    ]
    leaks = [pattern for pattern in forbidden if pattern in text]
    if leaks:
        raise ValueError(f"Public macOS acceptance summary contains local-only details: {', '.join(leaks)}")
