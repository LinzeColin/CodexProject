from __future__ import annotations

import os
import subprocess
from pathlib import Path

from pfi_os.system.dev_readiness import DEV_READY_CHECK_SCHEMA, build_dev_ready_check


def test_dev_ready_check_passes_minimal_fixture_without_heavy_gates(tmp_path: Path, monkeypatch) -> None:
    for relative in (
        "scripts/statusPFIOS.sh",
        "scripts/cleanCache.sh",
        "scripts/macosAcceptance.sh",
        "scripts/macosAppAcceptanceLite.sh",
        "scripts/macosLifecycleReadiness.sh",
        "scripts/hotspotRuntimeSummary.sh",
        "scripts/uiVisualAcceptance.sh",
        "scripts/macosPublicAcceptanceSummary.sh",
        "scripts/devReadyCheck.sh",
        "scripts/reportValidation.sh",
        "StartPFIOS.command",
        "StopPFIOS.command",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env zsh\nset -euo pipefail\necho ok\n", encoding="utf-8")
        os.chmod(path, 0o755)

    for relative in (
        "src/pfi_os/app/streamlit_app.py",
        "src/pfi_os/system/macos_acceptance_hub.py",
        "src/pfi_os/analysis/market_hotspots.py",
        "src/pfi_os/system/cache_cleanup.py",
        "src/pfi_os/system/macos_lifecycle.py",
        "src/pfi_os/system/macos_runtime_acceptance.py",
        "src/pfi_os/system/macos_public_acceptance.py",
        "src/pfi_os/system/dev_readiness.py",
        "src/pfi_os/system/report_validation_hub.py",
        "src/pfi_os/examples/hotspot_runtime_summary.py",
        "src/pfi_os/examples/macos_acceptance_hub.py",
        "src/pfi_os/examples/macos_public_acceptance.py",
        "src/pfi_os/examples/dev_ready_check.py",
        "src/pfi_os/examples/report_validation_hub.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")

    (tmp_path / ".git").mkdir()

    def fake_run(cmd, **kwargs):
        first = str(cmd[0])
        if first == "/bin/sh":
            return subprocess.CompletedProcess(cmd, 0, stdout="/bin/zsh\n", stderr="")
        if first.endswith("zsh"):
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if first == "git":
            return subprocess.CompletedProcess(cmd, 0, stdout=" M work-in-progress.py\n", stderr="")
        if first.endswith("statusPFIOS.sh"):
            return subprocess.CompletedProcess(cmd, 0, stdout="PFIOS is not running on ports 8501-8510.\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("pfi_os.system.dev_readiness.subprocess.run", fake_run)

    payload = build_dev_ready_check(project_root=tmp_path)

    assert payload["schema"] == DEV_READY_CHECK_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["git_status"]["status"] == "Dirty"
    assert payload["default_gate_policy"]["runs_heavy_release_gates"] is False
    assert payload["default_gate_policy"]["dirty_worktree_is_failure"] is False
    assert all("finalAcceptanceCheck" not in row["evidence"] for row in payload["checks"])
