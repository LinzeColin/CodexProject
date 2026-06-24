import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from backend.app.services.agent_runtime import AutoPaperAgentRuntime
from backend.app.services.atomic_json_store import write_json_atomic


ALPHA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ALPHA_ROOT.parent


def _bash_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name == "nt":
        drive = resolved.drive.rstrip(":").lower()
        if drive:
            parts = [part for part in resolved.parts[1:]]
            return "/mnt/" + drive + "/" + "/".join(parts)
    return resolved.as_posix()


def _paper_loop_result(symbol: str = "TLT"):
    return {
        "run_id": f"run_{symbol.lower()}",
        "status": "completed",
        "intent": {"symbol": symbol, "strategy_id": f"momentum_{symbol}_20d"},
        "risk_check": {"status": "approved_for_owner_review"},
        "approval_queue": {"ticket": {"status": "pending_owner_approval"}},
        "paper_order": {"status": "filled"},
        "paper_portfolio": {"trade_count": 1, "total_equity": 10000.0},
    }


class FileWritingLoop:
    def __init__(self, path: Path, *, delay_seconds: float = 0.04) -> None:
        self.path = path
        self.delay_seconds = delay_seconds
        self.started = False
        self.completed = 0

    def run_once(self):
        self.started = True
        rows = []
        if self.path.exists():
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        rows.append({"event": "cycle_started", "index": self.completed + 1})
        self.path.write_text(json.dumps(rows), encoding="utf-8")
        time.sleep(self.delay_seconds)
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        rows.append({"event": "cycle_committed", "index": self.completed + 1})
        self.path.write_text(json.dumps(rows), encoding="utf-8")
        self.completed += 1
        return _paper_loop_result("SPY")


class ShutdownFaultInjectionTests(unittest.TestCase):
    def test_disk_error_preserves_existing_json_and_removes_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.json"
            target.write_text(json.dumps({"generation": "old"}), encoding="utf-8")

            with mock.patch(
                "backend.app.services.atomic_json_store.os.replace",
                side_effect=OSError("injected disk replace failure"),
            ):
                with self.assertRaises(OSError):
                    write_json_atomic(target, {"generation": "new"})

            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"generation": "old"})
            self.assertEqual(list(Path(tmp).glob(".state.json.*.tmp")), [])

    def test_force_terminated_writer_preserves_valid_previous_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            target = temp_dir / "portfolio.json"
            marker = temp_dir / "replace_ready.marker"
            child_script = temp_dir / "pause_before_replace.py"
            target.write_text(json.dumps({"generation": "old"}), encoding="utf-8")
            child_script.write_text(
                textwrap.dedent(
                    f"""
                    import os
                    import sys
                    import time
                    from pathlib import Path

                    sys.path.insert(0, {str(ALPHA_ROOT)!r})
                    from backend.app.services import atomic_json_store

                    target = Path(sys.argv[1])
                    marker = Path(sys.argv[2])
                    original_replace = atomic_json_store.os.replace

                    def paused_replace(src, dst):
                        marker.write_text("ready", encoding="utf-8")
                        time.sleep(30)
                        original_replace(src, dst)

                    atomic_json_store.os.replace = paused_replace
                    atomic_json_store.write_json_atomic(target, {{"generation": "new"}})
                    """
                ),
                encoding="utf-8",
                newline="\n",
            )

            env = os.environ.copy()
            env["PYTHONPATH"] = str(ALPHA_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.Popen([sys.executable, str(child_script), str(target), str(marker)], env=env)
            try:
                deadline = time.time() + 5
                while time.time() < deadline and not marker.exists():
                    time.sleep(0.02)
                self.assertTrue(marker.exists(), "child did not reach replace fault injection point")
                proc.kill()
                proc.wait(timeout=5)
                self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"generation": "old"})
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)

    def test_runtime_does_not_write_after_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writes_path = Path(tmp) / "writes.json"
            loop = FileWritingLoop(writes_path)
            runtime = AutoPaperAgentRuntime()

            async def exercise():
                runtime.start(loop_factory=lambda: loop, interval_seconds=0.03)
                for _ in range(100):
                    if loop.started:
                        break
                    await asyncio.sleep(0.005)
                stopped = await runtime.stop(timeout_seconds=1)
                stopped_rows = json.loads(writes_path.read_text(encoding="utf-8"))
                await asyncio.sleep(0.12)
                after_wait_rows = json.loads(writes_path.read_text(encoding="utf-8"))
                return stopped, stopped_rows, after_wait_rows

            stopped, stopped_rows, after_wait_rows = asyncio.run(exercise())

            self.assertEqual(stopped["status"], "stopped")
            self.assertFalse(stopped["task_running"])
            self.assertEqual([row["event"] for row in stopped_rows], ["cycle_started", "cycle_committed"])
            self.assertEqual(after_wait_rows, stopped_rows)

    def test_stop_script_archives_reused_pid_without_killing_unrelated_process(self) -> None:
        bash = shutil.which("bash")
        if not bash:
            raise unittest.SkipTest("bash is unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            temp_alpha = Path(tmp) / "Alpha"
            scripts_dir = temp_alpha / "scripts"
            runtime_dir = temp_alpha / "runtime"
            scripts_dir.mkdir(parents=True)
            runtime_dir.mkdir()
            shutil.copy2(ALPHA_ROOT / "scripts" / "stop_alpha_dashboard.sh", scripts_dir / "stop_alpha_dashboard.sh")

            check_script = temp_alpha / "check_reused_pid.sh"
            check_script.write_bytes(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    cd "$(dirname "$0")"
                    sleep 30 &
                    unrelated_pid=$!
                    trap 'kill "$unrelated_pid" 2>/dev/null || true; wait "$unrelated_pid" 2>/dev/null || true' EXIT
                    echo "$unrelated_pid" > runtime/alpha_dashboard.pid
                    bash scripts/stop_alpha_dashboard.sh > runtime/stop.out 2>&1
                    kill -0 "$unrelated_pid"
                    test ! -f runtime/alpha_dashboard.pid
                    ls runtime/alpha_dashboard.pid.stale.* >/dev/null
                    grep -q "non-dashboard process" runtime/stop.out
                    """
                ).encode("utf-8"),
            )

            subprocess.run([bash, _bash_path(check_script)], check=True)

    def test_start_script_checks_dashboard_process_identity(self) -> None:
        start_script = (ALPHA_ROOT / "scripts" / "start_alpha_dashboard.sh").read_text(encoding="utf-8")

        self.assertIn("process_matches_dashboard", start_script)
        self.assertIn("non-dashboard process", start_script)
        self.assertIn("backend.app.main:app", start_script)


if __name__ == "__main__":
    unittest.main()
