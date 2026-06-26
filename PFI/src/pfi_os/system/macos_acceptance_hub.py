from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT


MACOS_ACCEPTANCE_HUB_SCHEMA = "PFIOSMacOSAcceptanceHubV1"


@dataclass(frozen=True)
class AcceptanceAction:
    action_id: str
    label: str
    command: tuple[str, ...]
    timeout_seconds: int
    starts_service: bool = False
    opens_browser: bool = False


MODE_SPECS: dict[str, dict[str, Any]] = {
    "daily": {
        "label": "日常验收",
        "description": "默认用户入口：聚合开发就绪和 GitHub-safe 公开验收摘要。",
        "actions": (
            AcceptanceAction("dev_ready", "开发就绪", ("scripts/devReadyCheck.sh", "--summary-json"), 45),
            AcceptanceAction("public_summary", "公开验收摘要", ("scripts/macosPublicAcceptanceSummary.sh", "--summary-json"), 30),
        ),
    },
    "app-entry": {
        "label": "App 入口检查",
        "description": "只读检查 Desktop、Downloads、Applications 的 PFI.app 入口。",
        "actions": (
            AcceptanceAction("app_entry", "App 入口轻量验收", ("scripts/macosAppAcceptanceLite.sh", "--summary-json"), 30),
        ),
    },
    "lifecycle": {
        "label": "生命周期检查",
        "description": "只读检查启动、停止、缓存保护和 UI allowlist。",
        "actions": (
            AcceptanceAction("lifecycle", "生命周期只读验收", ("scripts/macosLifecycleReadiness.sh", "--summary-json"), 40),
        ),
    },
    "runtime": {
        "label": "真实运行验收",
        "description": "受控启动本地服务、检查 health、停止并复核；必须显式选择。",
        "actions": (
            AcceptanceAction("runtime", "运行时验收", ("scripts/macosRuntimeAcceptance.sh", "--summary-json"), 140, starts_service=True),
        ),
    },
    "app-runtime": {
        "label": "App 打开路径验收",
        "description": "通过 Downloads PFI.app 打开路径做真实启动/停止闭环；必须显式选择。",
        "actions": (
            AcceptanceAction(
                "app_runtime",
                "App 打开路径验收",
                ("scripts/macosRuntimeAcceptance.sh", "--launch-method", "app", "--app-path", "~/Downloads/PFI.app", "--summary-json"),
                320,
                starts_service=True,
                opens_browser=True,
            ),
        ),
    },
    "ui": {
        "label": "UI 可见性验收",
        "description": "用 headless Chrome 验证工作台真实渲染；必须显式选择。",
        "actions": (
            AcceptanceAction("ui_visual", "UI 可见性验收", ("scripts/uiVisualAcceptance.sh", "--summary-json"), 180, starts_service=True, opens_browser=True),
        ),
    },
    "public-summary": {
        "label": "公开摘要",
        "description": "只读取本机 evidence，生成/检查 GitHub-safe 摘要。",
        "actions": (
            AcceptanceAction("public_summary", "公开验收摘要", ("scripts/macosPublicAcceptanceSummary.sh", "--summary-json"), 30),
        ),
    },
}


def build_macos_acceptance_mode_guide() -> dict[str, Any]:
    return {
        "schema": MACOS_ACCEPTANCE_HUB_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS Acceptance Hub",
        "generated_at": _now(),
        "status": "Guide",
        "default_mode": "daily",
        "modes": [
            {
                "mode": mode,
                "label": spec["label"],
                "description": spec["description"],
                "starts_service": any(action.starts_service for action in spec["actions"]),
                "opens_browser": any(action.opens_browser for action in spec["actions"]),
                "commands": [" ".join(action.command) for action in spec["actions"]],
            }
            for mode, spec in MODE_SPECS.items()
        ],
        "user_policy": "Use daily first. Choose runtime/ui modes only when you explicitly need real macOS acceptance evidence.",
    }


def run_macos_acceptance_hub(
    *,
    project_root: Path | str = PROJECT_ROOT,
    mode: str = "daily",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    if mode not in MODE_SPECS:
        return {
            "schema": MACOS_ACCEPTANCE_HUB_SCHEMA,
            "system": "PFI",
            "subsystem": "macOS Acceptance Hub",
            "generated_at": _now(),
            "status": "Blocked",
            "mode": mode,
            "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
            "actions": [{"action_id": "mode", "label": "Unknown mode", "status": "Fail", "evidence": f"unknown mode: {mode}"}],
            "available_modes": list(MODE_SPECS),
        }
    spec = MODE_SPECS[mode]
    rows = [_run_action(root, action) for action in spec["actions"]]
    summary = _summary(rows)
    return {
        "schema": MACOS_ACCEPTANCE_HUB_SCHEMA,
        "system": "PFI",
        "subsystem": "macOS Acceptance Hub",
        "generated_at": _now(),
        "status": "Pass" if summary["fail"] == 0 else "Blocked",
        "mode": mode,
        "label": spec["label"],
        "summary": summary,
        "actions": rows,
        "mode_policy": {
            "default_mode": "daily",
            "starts_service": any(action.starts_service for action in spec["actions"]),
            "opens_browser": any(action.opens_browser for action in spec["actions"]),
            "heavy_smoke": False,
        },
        "heavy_smoke_policy": (
            "macOS Acceptance Hub never runs scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, "
            "market refresh, broker connections, orders, payments, or holdings writes."
        ),
        "next_action": _next_action(mode, summary),
    }


def acceptance_hub_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "mode": payload.get("mode"),
        "label": payload.get("label"),
        "summary": payload.get("summary"),
        "actions": payload.get("actions"),
        "mode_policy": payload.get("mode_policy"),
        "heavy_smoke_policy": payload.get("heavy_smoke_policy"),
        "next_action": payload.get("next_action"),
    }


def _run_action(root: Path, action: AcceptanceAction) -> dict[str, Any]:
    completed = _run_command(root, action.command, timeout_seconds=action.timeout_seconds)
    payload = _loads_json(completed["stdout"])
    compact = _compact_payload(payload)
    ok = completed["returncode"] == 0 and compact.get("status") == "Pass"
    evidence = compact if payload is not None else {"returncode": completed["returncode"], "stderr": _sanitize_text(completed["stderr"], root)}
    return {
        "action_id": action.action_id,
        "label": action.label,
        "status": "Pass" if ok else "Fail",
        "command": " ".join(action.command),
        "starts_service": action.starts_service,
        "opens_browser": action.opens_browser,
        "evidence": evidence,
    }


def _run_command(root: Path, command: tuple[str, ...], *, timeout_seconds: int) -> dict[str, Any]:
    executable = root / command[0]
    args = [str(executable), *command[1:]]
    completed = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _loads_json(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _compact_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"schema": "Unknown", "status": "Blocked"}
    compact: dict[str, Any] = {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary"),
    }
    if payload.get("schema") == "PFIOSDevReadyCheckV1":
        compact["runtime_status"] = (payload.get("runtime_status") or {}).get("status")
        compact["cache_candidates"] = (payload.get("cache_preview") or {}).get("candidate_count")
        compact["git_status"] = (payload.get("git_status") or {}).get("status")
        compact["changed_count"] = (payload.get("git_status") or {}).get("changed_count")
    if payload.get("schema") == "PFIOSMacOSPublicAcceptanceSummaryV1":
        compact["sources_pass"] = (payload.get("summary") or {}).get("sources_pass")
        compact["sources_total"] = (payload.get("summary") or {}).get("sources_total")
    if payload.get("schema") == "PFIOSUIVisualAcceptanceV1":
        compact["screenshot_bytes"] = (payload.get("visual_metrics") or {}).get("screenshot_bytes")
    if payload.get("failed_checks"):
        compact["failed_checks"] = payload.get("failed_checks")
    return compact


def _summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    fail = sum(1 for row in rows if row.get("status") == "Fail")
    passed = sum(1 for row in rows if row.get("status") == "Pass")
    return {"pass": passed, "fail": fail, "info": 0, "total": len(rows)}


def _sanitize_text(text: str, root: Path) -> str:
    cleaned = text.replace(str(root), "<project_root>")
    cleaned = re.sub(r"/Users/[^\s\"']+", "<local_path>", cleaned)
    cleaned = re.sub(r"/Applications/[^\n\"']+", "<app_path>", cleaned)
    return cleaned[:1200]


def _next_action(mode: str, summary: dict[str, int]) -> str:
    if summary["fail"]:
        return "Open the failed action evidence, fix that component, then rerun scripts/macosAcceptance.sh --mode daily --summary-json."
    if mode == "daily":
        return "Daily macOS acceptance is clean. Use explicit runtime/ui modes only when refreshing real local evidence."
    return "Use daily mode for routine checks; keep this mode for explicit component-level acceptance."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
