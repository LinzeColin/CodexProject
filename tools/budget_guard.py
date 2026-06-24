#!/usr/bin/env python3
"""Read-only S2PCT02 budget and CI event-matrix guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "project-governance.yml"
STOP_HOOK = ROOT / ".codex" / "hooks" / "governance_stop.py"
LEAN_GOVERNANCE = ROOT / "scripts" / "lean_governance.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_report() -> dict[str, Any]:
    workflow = read_text(WORKFLOW)
    hook = read_text(STOP_HOOK)
    lean = read_text(LEAN_GOVERNANCE)
    checks = {
        "workflow_exists": WORKFLOW.is_file(),
        "stop_hook_exists": STOP_HOOK.is_file(),
        "lean_governance_exists": LEAN_GOVERNANCE.is_file(),
        "pull_request_uses_changed_only_ci": (
            "Run changed-only governance CI" in workflow
            and "github.event_name == 'pull_request'" in workflow
            and "scripts/lean_governance.py ci --changed-only" in workflow
            and "github.event.pull_request.base.sha" in workflow
        ),
        "full_validator_tests_not_on_pull_request": (
            "Run full governance validator tests" in workflow
            and "github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')" in workflow
            and "github.event_name == 'pull_request' || github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope != 'information-quality')" not in workflow
        ),
        "full_governance_only_schedule_or_manual_all": (
            "scripts/lean_governance.py validate --all --semantic --drift-report" in workflow
            and "github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')" in workflow
        ),
        "stop_hook_suggests_changed_only_only": (
            "scripts/lean_governance.py ci --changed-only --base-ref <base_ref>" in hook
            and "unittest discover" not in hook
            and "pytest tests/governance" not in hook
            and "--all --semantic --drift-report" not in hook
        ),
        "stop_hook_declares_event_matrix_and_budget_policy": "event_matrix" in hook and "budget_policy" in hook,
        "changed_only_ci_reports_budget_telemetry": (
            '"budget_telemetry"' in lean
            and '"mode": "changed-only-fast-gate"' in lean
            and '"unit": "project-scope-proxy"' in lean
            and '"full_governance_location": "schedule_or_workflow_dispatch_all"' in lean
        ),
        "changed_only_ci_remains_zero_write": '"write": False' in lean and "check_render_project_files(project_root)" in lean,
    }
    missing = sorted(name for name, ok in checks.items() if not ok)
    return {
        "schema_version": 1,
        "command": "budget-guard",
        "status": "PASS" if not missing else "FAIL",
        "checks": checks,
        "missing": missing,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run the local read-only S2PCT02 guard.")
    parser.parse_args(argv)
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
