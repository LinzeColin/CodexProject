import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = "/opt/anaconda3/bin/python3.12"


def test_pfi_supervisor_script_exposes_cli_without_heavy_runtime_dependencies():
    script = (PROJECT_ROOT / "scripts" / "pfiSupervisor.sh").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "pfi_os" / "examples" / "pfi_supervisor.py").read_text(encoding="utf-8")

    assert "pfi_os.examples.pfi_supervisor" in script
    assert "PYTHONDONTWRITEBYTECODE=1" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "pip install" not in script
    assert "broker" in module
    assert "no_order_execution" in module
    assert "smoke-double-worker" in module
    assert "smoke-crash-recovery" in module
    assert "acceptance" in module
    assert "worker-hold-lease" in module
    assert "TERMWorkerRecovery" in module
    assert "KILLWorkerRecovery" in module
    assert "PrivateLogScan" in module


def test_pfi_supervisor_contract_and_status_are_json_safe(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    contract = _run_cli(["--db-path", str(db_path), "--json", "contract"])
    status = _run_cli(["--db-path", str(db_path), "--json", "status", "--worker-id", "worker-a"])

    assert contract["schema"] == "PFIOSPFI003RuntimeSupervisorContractV1"
    assert contract["claiming"]["atomic_claim"] is True
    assert status["schema"] == "PFIOSPFI003RuntimeSupervisorContractV1"
    assert status["web"]["ready"] is True
    assert status["api"]["ready"] is True
    assert status["worker"]["ready"] is True
    assert status["safety_boundary"]["no_broker_calls"] is True
    assert status["safety_boundary"]["no_order_execution"] is True


def test_pfi_supervisor_doctor_reports_recovery_and_no_execution_boundary(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    _run_cli(["--db-path", str(db_path), "--json", "enqueue", "--job-type", "doctor_job", "--idempotency-key", "doctor-1"])
    doctor = _run_cli(["--db-path", str(db_path), "--json", "doctor", "--worker-id", "doctor-worker", "--recover-expired"])
    checks = {row["name"]: row for row in doctor["checks"]}

    assert doctor["schema"] == "PFIOSPFI003SupervisorDoctorV1"
    assert doctor["status"] == "Pass"
    assert checks["WebReady"]["status"] == "Pass"
    assert checks["APIReady"]["status"] == "Pass"
    assert checks["WorkerReady"]["status"] == "Pass"
    assert checks["JobStoreReady"]["status"] == "Pass"
    assert checks["NoExecutionBoundary"]["status"] == "Pass"
    assert checks["NoBrokerBoundary"]["status"] == "Pass"
    assert checks["ExpiredLeaseRecovery"]["status"] == "Pass"
    assert doctor["safety_boundary"]["no_order_execution"] is True


def test_pfi_supervisor_double_worker_smoke_allows_only_one_claim(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    payload = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "smoke-double-worker",
            "--job-type",
            "double_worker_job",
            "--idempotency-key",
            "double-worker-1",
            "--worker-a",
            "worker-a",
            "--worker-b",
            "worker-b",
        ]
    )

    assert payload["schema"] == "PFIOSPFI003DoubleWorkerSmokeV1"
    assert payload["status"] == "Pass"
    assert payload["first_claim"]["claimed"] is True
    assert payload["first_claim"]["lease_owner"] == "worker-a"
    assert payload["second_claim"]["claimed"] is False
    assert payload["double_worker_behavior"] == "only_one_worker_receives_active_lease"


def test_pfi_supervisor_crash_recovery_smoke_recovers_expired_lease(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    payload = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "smoke-crash-recovery",
            "--job-type",
            "crash_recovery_job",
            "--idempotency-key",
            "crash-1",
            "--worker-id",
            "worker-crash",
            "--lease-seconds",
            "2",
            "--advance-seconds",
            "3",
        ]
    )

    assert payload["schema"] == "PFIOSPFI003CrashRecoverySmokeV1"
    assert payload["status"] == "Pass"
    assert payload["claimed"]["claimed"] is True
    assert payload["recovered"]["recovered_count"] == 1
    assert payload["recovered"]["recovered"][0]["status"] == "retrying"
    assert "lease expiry recovered job" in payload["simulated_signal"]
    assert payload["safety_boundary"]["no_broker_calls"] is True


def test_pfi_supervisor_acceptance_runs_process_recovery_and_writes_manifest(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"
    runtime_dir = tmp_path / "runtime"

    payload = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "acceptance",
            "--runtime-dir",
            str(runtime_dir),
            "--lease-seconds",
            "2",
            "--advance-seconds",
            "3",
            "--worker-timeout-seconds",
            "6",
            "--sleep-wake-seconds",
            "120",
            "--hold-seconds",
            "30",
        ]
    )
    checks = {row["name"]: row for row in payload["checks"]}
    manifest_path = Path(payload["outputs"]["manifest_path"])
    log_path = Path(payload["outputs"]["log_path"])
    backup_path = Path(payload["outputs"]["backup_path"])
    manifest_text = manifest_path.read_text(encoding="utf-8")
    log_text = log_path.read_text(encoding="utf-8")

    assert payload["schema"] == "PFIOSPFI003SupervisorAcceptanceV1"
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    for name in [
        "DoctorReadiness",
        "DoubleWorkerClaimExclusion",
        "TERMWorkerRecovery",
        "KILLWorkerRecovery",
        "SleepWakeRecovery",
        "BackupManifest",
        "PrivateLogScan",
        "NoExecutionBoundary",
    ]:
        assert checks[name]["status"] == "Pass"
    assert payload["cases"]["term_worker"]["recovered"]["recovered_count"] == 1
    assert payload["cases"]["kill_worker"]["recovered"]["recovered_count"] == 1
    assert payload["cases"]["sleep_wake"]["recovered"]["recovered_count"] == 1
    assert payload["manifest"]["schema"] == "PFIOSPFI003SupervisorAcceptanceManifestV1"
    assert payload["manifest"]["backup_bytes"] > 0
    assert len(payload["manifest"]["backup_sha256"]) == 64
    case_statuses = payload["manifest"]["case_statuses"]
    assert any(row["schema"] == "PFIOSPFI003ProcessRecoveryCaseV1" and row["mode"] == "TERM" for row in case_statuses)
    assert any(row["schema"] == "PFIOSPFI003ProcessRecoveryCaseV1" and row["mode"] == "KILL" for row in case_statuses)
    assert manifest_path.exists()
    assert log_path.exists()
    assert backup_path.exists()
    assert "claimed" in log_text
    for forbidden in ["/Users/", "/Applications/", "password", "secret", "token", "holdings_json", "broker_account"]:
        assert forbidden not in manifest_text
        assert forbidden not in log_text


def test_pfi_supervisor_lifecycle_commands_round_trip(tmp_path: Path):
    db_path = tmp_path / "private" / "operational" / "pfi.sqlite"

    queued = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "enqueue",
            "--job-type",
            "round_trip",
            "--idempotency-key",
            "round-trip-1",
            "--payload-json",
            '{"symbol":"SPY"}',
        ]
    )
    claimed = _run_cli(["--db-path", str(db_path), "--json", "claim", "--job-type", "round_trip", "--worker-id", "worker-a"])
    heartbeat = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "heartbeat",
            "--job-id",
            queued["job_id"],
            "--worker-id",
            "worker-a",
            "--progress",
            "0.4",
            "--phase",
            "running_cli_round_trip",
        ]
    )
    completed = _run_cli(
        [
            "--db-path",
            str(db_path),
            "--json",
            "complete",
            "--job-id",
            queued["job_id"],
            "--worker-id",
            "worker-a",
            "--artifact-uri",
            "operational_store:round_trip",
        ]
    )

    assert queued["status"] == "queued"
    assert claimed["claimed"] is True
    assert heartbeat["phase"] == "running_cli_round_trip"
    assert heartbeat["progress"] == 0.4
    assert completed["status"] == "completed"
    assert completed["artifact_uri"] == "operational_store:round_trip"


def _run_cli(args: list[str]) -> dict:
    completed = subprocess.run(
        [PYTHON, "-m", "pfi_os.examples.pfi_supervisor", *args],
        cwd=PROJECT_ROOT,
        env={
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": "/private/tmp/pfi003-cli-pycache",
        },
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)
