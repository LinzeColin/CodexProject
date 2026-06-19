from __future__ import annotations

import json
from pathlib import Path

from quantlab.system import macos_acceptance_hub as hub


def test_daily_mode_combines_dev_ready_and_public_summary(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_command(_root: Path, command: tuple[str, ...], *, timeout_seconds: int):
        calls.append(command)
        if command[0] == "scripts/devReadyCheck.sh":
            payload = {
                "schema": "EVAOSDevReadyCheckV1",
                "status": "Pass",
                "summary": {"pass": 32, "fail": 0, "info": 1, "total": 33},
                "runtime_status": {"status": "Stopped"},
                "cache_preview": {"candidate_count": 0},
                "git_status": {"status": "Clean", "changed_count": 0},
            }
        elif command[0] == "scripts/macosPublicAcceptanceSummary.sh":
            payload = {
                "schema": "EVAOSMacOSPublicAcceptanceSummaryV1",
                "status": "Pass",
                "summary": {"sources_total": 2, "sources_pass": 2, "sources_blocked": 0},
            }
        else:
            raise AssertionError(command)
        return {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""}

    monkeypatch.setattr(hub, "_run_command", fake_run_command)

    payload = hub.run_macos_acceptance_hub(project_root=tmp_path, mode="daily")

    assert payload["schema"] == "EVAOSMacOSAcceptanceHubV1"
    assert payload["status"] == "Pass"
    assert payload["mode"] == "daily"
    assert payload["summary"] == {"pass": 2, "fail": 0, "info": 0, "total": 2}
    assert calls == [
        ("scripts/devReadyCheck.sh", "--summary-json"),
        ("scripts/macosPublicAcceptanceSummary.sh", "--summary-json"),
    ]
    assert payload["mode_policy"]["starts_service"] is False
    assert payload["mode_policy"]["opens_browser"] is False


def test_runtime_and_ui_modes_are_explicit_in_guide() -> None:
    guide = hub.build_macos_acceptance_mode_guide()
    modes = {row["mode"]: row for row in guide["modes"]}

    assert guide["default_mode"] == "daily"
    assert modes["daily"]["starts_service"] is False
    assert modes["runtime"]["starts_service"] is True
    assert modes["ui"]["opens_browser"] is True
    assert "macosRuntimeAcceptance.sh" in " ".join(modes["runtime"]["commands"])
    assert "uiVisualAcceptance.sh" in " ".join(modes["ui"]["commands"])


def test_unknown_mode_blocks_with_available_modes(tmp_path: Path) -> None:
    payload = hub.run_macos_acceptance_hub(project_root=tmp_path, mode="unknown")

    assert payload["status"] == "Blocked"
    assert "daily" in payload["available_modes"]
