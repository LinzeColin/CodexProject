from __future__ import annotations

import hashlib
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

from pfi_os.application.supervisor import RuntimeJobSupervisor


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"


def _hash(label: str) -> str:
    return hashlib.sha256(f"stage10-kill:{label}".encode()).hexdigest()


def _policy() -> dict[str, object]:
    return {
        "dependency_registry_sha256": _hash("registry"),
        "data_hash": _hash("data"),
        "formula_hash": _hash("formula"),
        "parameter_hash": _hash("parameter"),
        "read_model_hash": _hash("read-model"),
        "streamlit_cache_key": _hash("cache"),
        "dependency_snapshot_valid": True,
        "ordinary_run_network_allowed": False,
        "no_diff_network_allowed": False,
    }


def test_sigkill_then_new_process_recovers_the_sqlite_checkpoint(tmp_path: Path) -> None:
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    supervisor = RuntimeJobSupervisor(
        db_path,
        cache_policy_builder=_policy,
        lease_seconds=1,
        auto_start=False,
    )
    submitted = supervisor.submit_cache_refresh(request_id="actual-sigkill")
    job_id = submitted["job"]["job_id"]
    worker_source = """
import sys
import time
from pfi_os.infrastructure.jobs import SQLiteDurableJobStore

db_path, job_id = sys.argv[1:3]
store = SQLiteDurableJobStore(db_path)
claim = store.claim(
    job_type="cache.refresh",
    worker_id="killed-process-worker",
    lease_seconds=1,
)
assert claim["claimed"] is True
assert claim["job"]["job_id"] == job_id
store.record_progress(
    job_id,
    worker_id="killed-process-worker",
    lease_token=claim["lease"]["token"],
    expected_revision=claim["job"]["revision"],
    completed_units=1,
    total_units=3,
    step="cache.dependency_snapshot",
)
print("CHECKPOINT_PERSISTED", flush=True)
time.sleep(60)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", worker_source, str(db_path), job_id],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(PFI_ROOT / "src")},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        ready, _writeable, _errors = select.select([process.stdout], [], [], 10)
        assert ready, "worker did not persist its checkpoint before the kill deadline"
        assert process.stdout.readline().strip() == "CHECKPOINT_PERSISTED"
        os.kill(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        assert process.returncode == -signal.SIGKILL
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    time.sleep(1.1)
    restarted = RuntimeJobSupervisor(
        db_path,
        cache_policy_builder=_policy,
        lease_seconds=1,
        auto_start=False,
    )
    recovery = restarted.recover_and_resume()
    assert recovery["recovered_count"] == 1
    assert recovery["recovered_job_ids"] == [job_id]
    resumed = restarted.run_pending_once()
    assert resumed is not None
    assert resumed["status"] == "succeeded"

    final = restarted.get(job_id)
    assert final["job"]["attempt_count"] == 2
    assert final["job"]["progress"]["completed_units"] == 3
    assert final["job"]["observability"]["retry_count"] == 1
    assert "lease_expired_requeued" in [event["event_type"] for event in final["events"]]
    assert final["external_network_calls"] == 0
    assert restarted.store.integrity()["status"] == "pass"
