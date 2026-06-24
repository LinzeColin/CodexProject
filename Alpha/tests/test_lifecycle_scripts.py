from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_start_script_uses_atomic_pid_and_failed_start_cleanup():
    script = (ROOT / "scripts" / "start_alpha_dashboard.sh").read_text(encoding="utf-8")

    assert "write_pid_file" in script
    assert "mv -f \"$tmp\" \"$DASHBOARD_PID_FILE\"" in script
    assert "cleanup_started_process" in script
    assert "kill -KILL \"$pid\"" in script
    assert "echo \"$!\" > \"$DASHBOARD_PID_FILE\"" not in script


def test_lifecycle_stop_script_preserves_pid_until_process_exit():
    script = (ROOT / "scripts" / "stop_alpha_dashboard.sh").read_text(encoding="utf-8")

    assert "valid_pid" in script
    assert "archive_pid_file" in script
    assert "wait_for_exit \"$pid\" 20" in script
    assert "kill -KILL \"$pid\"" in script
    assert "preserving PID file" in script
