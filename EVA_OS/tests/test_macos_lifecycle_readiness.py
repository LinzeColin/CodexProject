from __future__ import annotations

import os
from pathlib import Path

from quantlab.system.macos_lifecycle import build_macos_lifecycle_readiness, write_macos_lifecycle_readiness


def test_macos_lifecycle_readiness_passes_fixture_without_full_smoke(tmp_path: Path) -> None:
    _fixture_lifecycle(root=tmp_path)

    payload = build_macos_lifecycle_readiness(
        project_root=tmp_path,
        run_status_script=False,
        include_cache_preview=True,
        include_app_acceptance=False,
    )

    assert payload["schema"] == "EVAOSMacOSLifecycleReadinessV1"
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["cache_preview"]["schema"] == "EVACacheCleanupReportV1"
    assert payload["app_acceptance"]["status"] == "Skipped"
    assert "finalAcceptanceCheck.sh" in payload["heavy_smoke_policy"]
    assert "does not start, stop, clean" in payload["safety_boundary"]
    assert any(row["check"] == "AutoShutdownMonitor" and row["status"] == "Pass" for row in payload["checks"])
    assert any(row["check"] == "DevReadyScriptExecutable" and row["status"] == "Pass" for row in payload["checks"])
    assert all("ciSmoke.sh" not in row["evidence"] for row in payload["checks"])


def test_macos_lifecycle_readiness_blocks_missing_heartbeat_ui(tmp_path: Path) -> None:
    _fixture_lifecycle(root=tmp_path)
    streamlit_app = tmp_path / "src" / "quantlab" / "app" / "streamlit_app.py"
    streamlit_app.write_text(
        "LIFECYCLE_SCRIPT_ALLOWLIST = {'scripts/macosAppAcceptanceLite.sh': 30}\n",
        encoding="utf-8",
    )

    payload = build_macos_lifecycle_readiness(
        project_root=tmp_path,
        run_status_script=False,
        include_cache_preview=False,
        include_app_acceptance=False,
    )

    assert payload["status"] == "Blocked"
    assert any(row["check"] == "UIHeartbeatInstalled" and row["status"] == "Fail" for row in payload["checks"])


def test_write_macos_lifecycle_readiness_outputs_json_and_latest(tmp_path: Path) -> None:
    _fixture_lifecycle(root=tmp_path)
    output_dir = tmp_path / "acceptance"

    payload = write_macos_lifecycle_readiness(
        project_root=tmp_path,
        output_dir=output_dir,
        run_status_script=False,
        include_cache_preview=False,
        include_app_acceptance=False,
    )

    assert Path(payload["outputs"]["json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).name == "MacOSLifecycleReadiness_latest.json"


def _fixture_lifecycle(*, root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    app_dir = root / "src" / "quantlab" / "app"
    system_dir = root / "src" / "quantlab" / "system"
    app_dir.mkdir(parents=True)
    system_dir.mkdir(parents=True)

    _write_executable(
        root / "StartQuantLab.command",
        """
#!/bin/zsh
LOCK_DIR="$PROJECT_DIR/data/cache/quantlab_launch.lockdir"
LOCK_PID_FILE="$LOCK_DIR/pid"
source "$PROJECT_DIR/scripts/quantlabRuntime.sh"
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"
HEARTBEAT_TIMEOUT="${QUANTLAB_HEARTBEAT_TIMEOUT:-120}"
export QUANTLAB_HEARTBEAT_URL="http://127.0.0.1:$HEARTBEAT_PORT/heartbeat"
"$PYTHON_BIN" -m streamlit run src/quantlab/app/streamlit_app.py --server.address 127.0.0.1 --server.fileWatcherType none --browser.gatherUsageStats false &
STREAMLIT_PID=$!
"$PYTHON_BIN" -m quantlab.system.shutdown_monitor --streamlit-pid "$STREAMLIT_PID"
""",
    )
    _write_executable(
        scripts / "startQuantLab.sh",
        """
#!/usr/bin/env zsh
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"
"$PYTHON_BIN" -m streamlit run src/quantlab/app/streamlit_app.py --server.address 127.0.0.1 --server.fileWatcherType none --browser.gatherUsageStats false
""",
    )
    _write_executable(
        scripts / "stopQuantLab.sh",
        """
#!/usr/bin/env zsh
process_cwd() { true; }
if [[ "$command" == *"src/quantlab/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
  kill "$pid"
fi
rm -rf "$LOCK_DIR"
""",
    )
    _write_executable(scripts / "statusQuantLab.sh", "#!/usr/bin/env zsh\necho stopped\n")
    _write_executable(scripts / "devReadyCheck.sh", "#!/usr/bin/env zsh\necho dev-ready\n")
    _write_executable(
        scripts / "cleanCache.sh",
        """
#!/usr/bin/env zsh
process_cwd() { true; }
quantlab_is_running() {
  if [[ "$command" == *"src/quantlab/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
    return 0
  fi
}
if quantlab_is_running; then
  echo "QuantLab appears to be running. Stop it before cleaning cache."
fi
PYTHONPATH="$PROJECT_DIR/src" python3 -m quantlab.system.cache_cleanup --dry-run
""",
    )
    _write_executable(scripts / "macosAppAcceptanceLite.sh", "#!/usr/bin/env zsh\necho lite\n")

    (app_dir / "streamlit_app.py").write_text(
        """
def install_shutdown_heartbeat():
    heartbeat_url = _safe_heartbeat_url(os.getenv("QUANTLAB_HEARTBEAT_URL", "").strip())
    fetch(heartbeatUrl)

def _safe_heartbeat_url(value):
    return "http://127.0.0.1:9501/heartbeat"

LIFECYCLE_SCRIPT_ALLOWLIST = {"scripts/devReadyCheck.sh": 45, "scripts/macosAppAcceptanceLite.sh": 30, "scripts/macosLifecycleReadiness.sh": 40}
""",
        encoding="utf-8",
    )
    (system_dir / "shutdown_monitor.py").write_text(
        """
seen_heartbeat = False
def should_shutdown():
    return seen_heartbeat
def stable_timeout(timeout):
    return max(timeout, 60)
""",
        encoding="utf-8",
    )
    (system_dir / "cache_cleanup.py").write_text(
        """
safety_boundary = "Reports, holdings, imports, source samples, SQLite databases, and market bar caches are not deleted"
""",
        encoding="utf-8",
    )


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")
    os.chmod(path, 0o755)
