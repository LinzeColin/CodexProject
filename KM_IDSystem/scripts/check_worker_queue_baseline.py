#!/usr/bin/env python3
"""Run the isolated STAGE-038 Phase 2 asynchronous worker-queue slice."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from typing import Any, Callable, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
INDEX_PATH = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_baseline_index.json"
)
STAGE037_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_job_state_model.py"
GOVERNANCE_VALIDATOR_PATH = (
    PURSUE_ROOT / "validate_stage005_governance_regression.py"
)

INDEX_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.index.v1"
CONTRACT_SCHEMA_VERSION = "ids.worker_queue_baseline.v0_1.p2"
OPERATION_SCHEMA_VERSION = "ids.worker.operation.hash_tracked_control_ref.v1"
TASK_ID = "IDS-V0_1-STAGE038-P2"
ACCEPTANCE_ID = "ACC-STAGE-038"
NEXT_GATE = "IDS-STAGE038-P3-GATE"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE"
QUEUE_MODE = "ASYNCIO_IN_MEMORY_ISOLATED_NON_PRODUCTION"
SUBMISSION_MODE = "SYNCHRONOUS_ACK_ASYNC_WORKER"
ORDERING_POLICY = "FIFO_ADMISSION_SEQUENCE_NO_PRIORITY_REORDERING"
MAXIMUM_ISOLATED_CAPACITY = 16
DEFAULT_ISOLATED_CAPACITY = 1
PAYLOAD_SIZE_MAXIMUM = 1048576
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
)
AUDIT_REF = (
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md#Runtime-Evidence"
)
RESOURCE_GATE_REFS = [
    "contract:control-metadata-no-external-drive-or-api",
    "contract:local-project-disk-capacity-check-before-read",
]

SOURCE_BINDINGS = {
    "stage037_job_state_index_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/job_state_model/"
            "stage037_job_state_model_index.json"
        ),
        "sha256": "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    },
    "stage037_job_state_checker_ref": {
        "path": "scripts/check_job_state_model.py",
        "sha256": "7de8746b70ca1eaba78b672deebd9973113cedeacf3edbba09d2afb90407f404",
    },
    "stage038_phase1_boundary_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
        ),
        "sha256": "d8930c3c3c9551afb2801952bb42d135247847352838aeb37b988d6c283f6e76",
    },
    "stage038_source_reverification_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
        ),
        "sha256": "e5806522985fe06cb0c09af8c15da310af643b338a4cc2b60baca1bfcb3e04d9",
    },
}

EXPECTED_RUNTIME_OWNERSHIP = {
    "queue_and_claim_transport_baseline": "STAGE-038",
    "retry_and_dead_letter_policy": "STAGE-039",
    "measured_backpressure_and_fairness": "STAGE-040",
    "production_lock_lease_and_fencing": "STAGE-041",
    "production_automatic_lifecycle": "STAGE-042",
    "worker_crash_recovery": "STAGE-043",
    "half_product_cleanup": "STAGE-044",
}

ENVELOPE_FIELDS = {
    "job_id",
    "job_type",
    "job_state",
    "state_version",
    "idempotency_key",
    "transition_request_id",
    "parent_job_id",
    "dependency_refs",
    "attempt_id",
    "retry_count",
    "max_retries",
    "retry_pending",
    "next_eligible_at",
    "input_refs",
    "output_refs",
    "checkpoint_ref",
    "operation_contract_version",
    "lease_owner_ref",
    "lease_expires_at",
    "fencing_token",
    "lock_key",
    "priority_ref",
    "pause_reason_code",
    "stop_reason",
    "owner_action_ref",
    "resource_gate_refs",
    "safe_error_code",
    "error_ref",
    "audit_ref",
    "transition_actor_ref",
    "created_at",
    "updated_at",
    "cleanup_manifest_ref",
}
PRIORITY_REFS = {
    "P0_CRITICAL_ENGINEERING_DATA",
    "P1_HIGH_VALUE_ENGINEERING_DATA",
    "P2_SUPPORTING_ENGINEERING_DATA",
    "P3_LOW_VALUE_OR_DEFERRED_DATA",
}
JOB_TYPES = {
    "IMPORT",
    "ARCHIVE",
    "PARSE",
    "OCR",
    "CHUNK",
    "EMBED",
    "INDEX",
    "REPORT",
}
REF_LIST_FIELDS = {
    "dependency_refs",
    "input_refs",
    "output_refs",
    "resource_gate_refs",
}
REF_SCALAR_FIELDS = {
    "job_id",
    "idempotency_key",
    "transition_request_id",
    "parent_job_id",
    "attempt_id",
    "next_eligible_at",
    "checkpoint_ref",
    "lease_owner_ref",
    "lease_expires_at",
    "lock_key",
    "owner_action_ref",
    "safe_error_code",
    "error_ref",
    "audit_ref",
    "transition_actor_ref",
    "cleanup_manifest_ref",
}

_STAGE037_MODULE: Any = None
_GOVERNANCE_MODULE: Any = None


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stage037_module() -> Any:
    global _STAGE037_MODULE
    if _STAGE037_MODULE is None:
        _STAGE037_MODULE = _load_module(
            STAGE037_CHECKER_PATH, "stage037_job_state_for_stage038"
        )
    return _STAGE037_MODULE


def _governance_module() -> Any:
    global _GOVERNANCE_MODULE
    if _GOVERNANCE_MODULE is None:
        _GOVERNANCE_MODULE = _load_module(
            GOVERNANCE_VALIDATOR_PATH, "stage005_governance_for_stage038"
        )
    return _GOVERNANCE_MODULE


def _parse_yaml_text(text: str) -> dict[str, Any]:
    parsed = _governance_module()._parse_yaml_text(text)
    return parsed if isinstance(parsed, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_index() -> dict[str, Any]:
    parsed = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def _source_integrity(index: Mapping[str, Any]) -> tuple[dict[str, bool], dict[str, str]]:
    bindings = index.get("source_bindings")
    bindings = bindings if isinstance(bindings, dict) else {}
    checks: dict[str, bool] = {}
    observed: dict[str, str] = {}
    for name, expected in SOURCE_BINDINGS.items():
        actual = bindings.get(name)
        actual = actual if isinstance(actual, dict) else {}
        path = PROJECT_ROOT / expected["path"]
        digest = _sha256_file(path) if path.is_file() else ""
        observed[name] = digest
        checks[name] = (
            actual == expected
            and path.is_file()
            and digest == expected["sha256"]
        )
    checks["exact_source_binding_keys"] = set(bindings) == set(SOURCE_BINDINGS)
    return checks, observed


def _contract_checks(index: Mapping[str, Any]) -> dict[str, bool]:
    queue_contract = index.get("worker_queue_contract")
    queue_contract = queue_contract if isinstance(queue_contract, dict) else {}
    reference = index.get("reference_policy")
    reference = reference if isinstance(reference, dict) else {}
    operation = index.get("operation_contract")
    operation = operation if isinstance(operation, dict) else {}
    truth = index.get("truth_contract")
    truth = truth if isinstance(truth, dict) else {}
    source_checks, _ = _source_integrity(index)
    try:
        stage037_report = _stage037_module().build_stage037_job_state_report()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        stage037_report = {}

    return {
        "identity_exact": (
            index.get("schema_version") == INDEX_SCHEMA_VERSION
            and index.get("stage") == "STAGE-038"
            and index.get("phase") == "Phase 2"
            and index.get("task_id") == TASK_ID
            and index.get("acceptance_id") == ACCEPTANCE_ID
        ),
        "source_bindings_exact": all(source_checks.values()),
        "stage037_contract_valid": stage037_report.get("contract_valid") is True,
        "queue_contract_exact": (
            queue_contract.get("schema_version") == CONTRACT_SCHEMA_VERSION
            and queue_contract.get("queue_mode") == QUEUE_MODE
            and queue_contract.get("submission_mode") == SUBMISSION_MODE
            and queue_contract.get("ordering_policy") == ORDERING_POLICY
            and queue_contract.get("job_control_envelope_schema")
            == "ids.job_control_envelope.v1"
            and queue_contract.get("job_state_model_version") == "ids.job_state.v1"
            and queue_contract.get("state_transition_owner") == "STAGE-037"
            and queue_contract.get("worker_count") == 1
            and queue_contract.get("default_isolated_capacity")
            == DEFAULT_ISOLATED_CAPACITY
            and queue_contract.get("maximum_isolated_capacity")
            == MAXIMUM_ISOLATED_CAPACITY
            and queue_contract.get("capacity_backpressure_result")
            == "QUEUE_CAPACITY_REACHED"
            and queue_contract.get("duplicate_admission_result")
            == "EXISTING_QUEUE_ENTRY"
            and queue_contract.get("identity_derivation")
            == "SHA256_TASK_INPUT_JOB_TYPE"
            and queue_contract.get("lock_key_derivation")
            == "SAME_INPUT_SAME_RESOURCE_CONFLICT_KEY"
            and queue_contract.get("dependency_policy")
            == "NONEMPTY_DEPENDENCY_REFS_FAIL_CLOSED_IN_BASELINE"
            and queue_contract.get("claim_mode")
            == "IN_PROCESS_RESOURCE_LOCK_AND_FENCING_ONLY"
            and queue_contract.get("operation_contract_version")
            == OPERATION_SCHEMA_VERSION
            and queue_contract.get("runtime_persistence_performed") is False
            and queue_contract.get("production_runtime_activation_allowed") is False
        ),
        "reference_policy_exact": (
            reference.get("payload_size_bytes_maximum") == PAYLOAD_SIZE_MAXIMUM
            and reference.get("maximum_text_length") == 512
            and reference.get("maximum_refs_per_field") == 64
            and reference.get("input_ref_count") == 1
            and reference.get("input_ref_prefix") == "repo:KM_IDSystem/"
            and reference.get("input_must_be_git_tracked") is True
            and reference.get("absolute_path_allowed") is False
            and reference.get("parent_path_segment_allowed") is False
            and reference.get("raw_body_fields_allowed") is False
            and reference.get("plaintext_secrets_allowed") is False
            and reference.get("raw_metadata_content_access_allowed") is False
        ),
        "operation_contract_exact": (
            operation.get("schema_version") == OPERATION_SCHEMA_VERSION
            and operation.get("operation") == "SHA256_GIT_TRACKED_CONTROL_FILE"
            and operation.get("allowed_repository_prefix") == "KM_IDSystem/"
            and operation.get("output_ref_format") == "sha256:<64-lower-hex>"
            and operation.get("checkpoint_ref_format")
            == "checkpoint:sha256:<64-lower-hex>"
            and operation.get("writes_runtime_output") is False
            and operation.get("reads_ids_business_data") is False
            and operation.get("calls_external_api") is False
        ),
        "runtime_ownership_exact": (
            index.get("runtime_ownership") == EXPECTED_RUNTIME_OWNERSHIP
        ),
        "truth_contract_exact": (
            truth.get("execution_mode") == EXECUTION_MODE
            and truth.get("isolated_non_production_runtime_allowed") is True
            and truth.get("queue_runtime_performed_by_phase2_smoke") is True
            and truth.get("worker_runtime_performed_by_phase2_smoke") is True
            and truth.get("isolated_control_job_created_by_phase2_smoke") is True
            and truth.get("production_runtime_activation_performed") is False
            and truth.get("claim_persistence_performed") is False
            and truth.get("persistent_queue_write_performed") is False
            and truth.get("database_connection_performed") is False
            and truth.get("schema_change_performed") is False
            and truth.get("state_registry_write_performed") is False
            and truth.get("runtime_output_written") is False
            and truth.get("ids_business_source_read_performed") is False
            and truth.get("external_api_call_performed") is False
            and truth.get("raw_metadata_content_accessed") is False
            and truth.get("fake_ids_business_data_used") is False
            and truth.get("real_ids_business_job_created") is False
            and truth.get("github_upload_allowed") is False
            and truth.get("app_reinstall_allowed") is False
        ),
    }


def _safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 512:
        return False
    normalized = value.replace("\\", "/").lower()
    if (
        "\\" in value
        or "%2f" in normalized
        or "%5c" in normalized
        or "/users/linzezhang/downloads/ids_metadata" in normalized
    ):
        return False
    return ".." not in PurePosixPath(normalized).parts


def _repo_path_from_ref(value: Any) -> Optional[str]:
    if not _safe_ref(value) or not str(value).startswith("repo:"):
        return None
    path = str(value)[len("repo:") :]
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    normalized = pure.as_posix()
    if not normalized.startswith("KM_IDSystem/"):
        return None
    return normalized


def _git_tracked(path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _canonical_fingerprint(value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def build_control_envelope(
    input_ref: str,
    *,
    job_type: str = "PARSE",
    priority_ref: str = "P1_HIGH_VALUE_ENGINEERING_DATA",
) -> dict[str, Any]:
    seed = hashlib.sha256(f"{TASK_ID}|{input_ref}|{job_type}".encode("utf-8")).hexdigest()
    return {
        "job_id": f"control:stage038:{seed[:24]}",
        "job_type": job_type,
        "job_state": "QUEUED",
        "state_version": 0,
        "idempotency_key": f"idempotency:stage038:{seed}",
        "transition_request_id": f"admission:stage038:{seed}",
        "parent_job_id": None,
        "dependency_refs": [],
        "attempt_id": None,
        "retry_count": 0,
        "max_retries": 0,
        "retry_pending": False,
        "next_eligible_at": None,
        "input_refs": [input_ref],
        "output_refs": [],
        "checkpoint_ref": None,
        "operation_contract_version": OPERATION_SCHEMA_VERSION,
        "lease_owner_ref": None,
        "lease_expires_at": None,
        "fencing_token": 0,
        "lock_key": f"resource:stage038:{seed}",
        "priority_ref": priority_ref,
        "pause_reason_code": None,
        "stop_reason": None,
        "owner_action_ref": f"acceptance:{ACCEPTANCE_ID}",
        "resource_gate_refs": copy.deepcopy(RESOURCE_GATE_REFS),
        "safe_error_code": None,
        "error_ref": None,
        "audit_ref": AUDIT_REF,
        "transition_actor_ref": f"task:{TASK_ID}",
        "created_at": None,
        "updated_at": None,
        "cleanup_manifest_ref": None,
    }


def _expected_envelope_identity(envelope: Mapping[str, Any]) -> dict[str, str]:
    input_refs = envelope.get("input_refs")
    input_ref = (
        input_refs[0]
        if isinstance(input_refs, list)
        and len(input_refs) == 1
        and isinstance(input_refs[0], str)
        else ""
    )
    job_type = envelope.get("job_type")
    seed = hashlib.sha256(
        f"{TASK_ID}|{input_ref}|{job_type}".encode("utf-8")
    ).hexdigest()
    return {
        "job_id": f"control:stage038:{seed[:24]}",
        "idempotency_key": f"idempotency:stage038:{seed}",
        "transition_request_id": f"admission:stage038:{seed}",
        "lock_key": f"resource:stage038:{seed}",
    }


def _validate_envelope(envelope: Any) -> tuple[bool, str]:
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE_FIELDS:
        return False, "INVALID_ENVELOPE_SHAPE"
    try:
        encoded = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        return False, "INVALID_ENVELOPE_SHAPE"
    if len(encoded) > PAYLOAD_SIZE_MAXIMUM:
        return False, "ENVELOPE_TOO_LARGE"
    if (
        envelope.get("job_type") not in JOB_TYPES
        or envelope.get("job_state") != "QUEUED"
        or envelope.get("state_version") != 0
        or envelope.get("retry_count") != 0
        or envelope.get("max_retries") != 0
        or envelope.get("retry_pending") is not False
        or envelope.get("priority_ref") not in PRIORITY_REFS
        or envelope.get("operation_contract_version") != OPERATION_SCHEMA_VERSION
        or envelope.get("dependency_refs") != []
        or envelope.get("output_refs") != []
        or envelope.get("checkpoint_ref") is not None
        or envelope.get("error_ref") is not None
        or envelope.get("lease_owner_ref") is not None
        or envelope.get("lease_expires_at") is not None
        or envelope.get("attempt_id") is not None
        or envelope.get("fencing_token") != 0
        or envelope.get("resource_gate_refs") != RESOURCE_GATE_REFS
    ):
        return False, "INVALID_ENVELOPE_VALUE"
    for field in REF_SCALAR_FIELDS:
        value = envelope.get(field)
        if value is not None and not _safe_ref(value):
            return False, "FORBIDDEN_REFERENCE"
    for field in REF_LIST_FIELDS:
        values = envelope.get(field)
        if (
            not isinstance(values, list)
            or len(values) > 64
            or any(not _safe_ref(value) for value in values)
        ):
            return False, "FORBIDDEN_REFERENCE"
    input_refs = envelope.get("input_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        return False, "INVALID_CONTROL_INPUT_COUNT"
    input_path = _repo_path_from_ref(input_refs[0])
    if input_path is None:
        return False, "FORBIDDEN_REFERENCE"
    expected_identity = _expected_envelope_identity(envelope)
    if any(envelope.get(key) != value for key, value in expected_identity.items()):
        return False, "INVALID_ENVELOPE_IDENTITY"
    if not _git_tracked(input_path):
        return False, "UNTRACKED_CONTROL_REFERENCE"
    return True, "QUEUE_ADMISSION_ACCEPTED"


def _snapshot_from_envelope(envelope: Mapping[str, Any], stage037: Any) -> dict[str, Any]:
    return {
        "evaluation_mode": stage037.EVALUATION_MODE,
        "job_id": envelope["job_id"],
        "job_type": envelope["job_type"],
        "job_state": "QUEUED",
        "state_version": envelope["state_version"],
        "retry_count": envelope["retry_count"],
        "max_retries": envelope["max_retries"],
        "retry_pending": envelope["retry_pending"],
        "retry_disposition": "none",
        "next_eligible_at": envelope["next_eligible_at"],
        "lease_active": False,
        "lock_active": False,
        "fencing_token": envelope["fencing_token"],
        "attempt_id": None,
        "lease_owner_ref": None,
        "lease_expires_at": None,
        "lock_key": None,
        "pause_reason_code": None,
        "stop_reason": None,
        "input_refs": copy.deepcopy(envelope["input_refs"]),
        "output_refs": [],
        "checkpoint_ref": None,
        "quarantine_ref": None,
        "error_ref": None,
    }


def _transition_request(
    snapshot: Mapping[str, Any],
    target: str,
    suffix: str,
    *,
    guard_facts: Mapping[str, bool],
    output_refs: Optional[list[str]] = None,
    checkpoint_ref: Optional[str] = None,
    error_ref: Optional[str] = None,
    candidate_claim: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "job_id": snapshot["job_id"],
        "transition_request_id": (
            f"acceptance:{ACCEPTANCE_ID}:{snapshot['job_id']}:{suffix}"
        ),
        "expected_state": snapshot["job_state"],
        "expected_state_version": snapshot["state_version"],
        "target_state": target,
        "actor_ref": f"task:{TASK_ID}",
        "reason_code": f"STAGE038_PHASE2_{suffix.upper()}",
        "audit_ref": AUDIT_REF,
        "guard_facts": dict(guard_facts),
        "input_refs": [],
        "output_refs": copy.deepcopy(output_refs or []),
        "checkpoint_ref": checkpoint_ref,
        "quarantine_ref": None,
        "error_ref": error_ref,
        "resource_gate_refs": [],
        "pause_reason_code": None,
        "stop_reason": None,
        "next_eligible_at": None,
        "next_eligible_evidence_ref": None,
        "fencing_token": (
            snapshot["fencing_token"]
            if snapshot["job_state"] in {"CLAIMED", "RUNNING", "PAUSE_REQUESTED"}
            else None
        ),
        "candidate_claim": copy.deepcopy(candidate_claim),
    }


async def _hash_tracked_control_file(
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    input_ref = envelope["input_refs"][0]
    path = _repo_path_from_ref(input_ref)
    if path is None or not _git_tracked(path):
        raise RuntimeError("control reference is not a tracked project file")
    absolute = REPO_ROOT / path
    data = absolute.read_bytes()
    disk = shutil.disk_usage(PROJECT_ROOT)
    if disk.free < len(data) + 1024 * 1024:
        raise RuntimeError("local project disk capacity gate blocked")
    await asyncio.sleep(0)
    digest = hashlib.sha256(data).hexdigest()
    return {
        "output_refs": [f"sha256:{digest}"],
        "checkpoint_ref": f"checkpoint:sha256:{digest}",
    }


class IsolatedWorkerQueue:
    """One-worker, in-memory queue for tracked control metadata only."""

    def __init__(
        self,
        *,
        capacity: int = DEFAULT_ISOLATED_CAPACITY,
        operation: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        index: Optional[dict[str, Any]] = None,
    ) -> None:
        contract = copy.deepcopy(index) if index is not None else _load_index()
        checks = _contract_checks(contract)
        if not all(checks.values()):
            raise ValueError("invalid STAGE-038 worker-queue contract")
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
            or capacity > MAXIMUM_ISOLATED_CAPACITY
        ):
            raise ValueError("isolated queue capacity must be between 1 and 16")
        self._capacity = capacity
        self._operation = operation or _hash_tracked_control_file
        self._stage037 = _stage037_module()
        self._stage037_contract = self._stage037.load_contract()
        self._queue: Any = None
        self._pending_refs: list[str] = []
        self._records: dict[str, dict[str, Any]] = {}
        self._idempotency_refs: dict[str, str] = {}
        self._idempotency_fingerprints: dict[str, str] = {}
        self._resource_locks: dict[str, asyncio.Lock] = {}
        self._worker_task: Any = None
        self._closed = False

    @property
    def queue_size(self) -> int:
        if self._queue is None:
            return len(self._pending_refs)
        return self._queue.qsize()

    @property
    def record_count(self) -> int:
        return len(self._records)

    def _owner_projection(self, state: str) -> dict[str, Any]:
        projections = self._stage037_contract.get("human_status_projection", {})
        value = projections.get(state, {})
        return copy.deepcopy(value) if isinstance(value, dict) else {}

    def _decision(
        self,
        *,
        accepted: bool,
        result_code: str,
        queue_entry_ref: Optional[str],
        duplicate: bool,
        state: Optional[str],
    ) -> dict[str, Any]:
        owner_state = state if state in self._stage037.JOB_STATES else "FAILED"
        return {
            "accepted": accepted,
            "result_code": result_code,
            "queue_entry_ref": queue_entry_ref,
            "duplicate": duplicate,
            "machine_state": state,
            "owner_status": self._owner_projection(owner_state),
            "submission_mode": SUBMISSION_MODE,
            "job_completion_waited": False,
        }

    def submit(self, envelope: Any) -> dict[str, Any]:
        if self._closed:
            return self._decision(
                accepted=False,
                result_code="QUEUE_CLOSED",
                queue_entry_ref=None,
                duplicate=False,
                state=None,
            )
        valid, result_code = _validate_envelope(envelope)
        if not valid:
            return self._decision(
                accepted=False,
                result_code=result_code,
                queue_entry_ref=None,
                duplicate=False,
                state=None,
            )
        assert isinstance(envelope, dict)
        idempotency_key = envelope["idempotency_key"]
        fingerprint = _canonical_fingerprint(envelope)
        existing_ref = self._idempotency_refs.get(idempotency_key)
        if existing_ref is not None:
            if self._idempotency_fingerprints[idempotency_key] != fingerprint:
                return self._decision(
                    accepted=False,
                    result_code="IDEMPOTENCY_KEY_CONFLICT",
                    queue_entry_ref=None,
                    duplicate=False,
                    state=None,
                )
            record = self._records[existing_ref]
            return self._decision(
                accepted=True,
                result_code="EXISTING_QUEUE_ENTRY",
                queue_entry_ref=existing_ref,
                duplicate=True,
                state=record["machine_state"],
            )
        queue_full = (
            len(self._pending_refs) >= self._capacity
            if self._queue is None
            else self._queue.full()
        )
        if queue_full:
            return self._decision(
                accepted=False,
                result_code="QUEUE_CAPACITY_REACHED",
                queue_entry_ref=None,
                duplicate=False,
                state="PAUSED",
            )

        queue_entry_ref = f"queue-entry:stage038:{fingerprint}"
        snapshot = _snapshot_from_envelope(envelope, self._stage037)
        self._records[queue_entry_ref] = {
            "queue_entry_ref": queue_entry_ref,
            "job_id": envelope["job_id"],
            "idempotency_key": idempotency_key,
            "priority_ref": envelope["priority_ref"],
            "lock_key": envelope["lock_key"],
            "machine_state": "QUEUED",
            "owner_status": self._owner_projection("QUEUED"),
            "input_refs": copy.deepcopy(envelope["input_refs"]),
            "output_refs": [],
            "checkpoint_ref": None,
            "error_ref": None,
            "state_history": ["QUEUED"],
            "transition_audit": [],
            "in_memory_only": True,
            "persisted": False,
            "_envelope": copy.deepcopy(envelope),
            "_snapshot": snapshot,
        }
        self._idempotency_refs[idempotency_key] = queue_entry_ref
        self._idempotency_fingerprints[idempotency_key] = fingerprint
        if self._queue is None:
            self._pending_refs.append(queue_entry_ref)
        else:
            self._queue.put_nowait(queue_entry_ref)
        return self._decision(
            accepted=True,
            result_code="QUEUE_ADMISSION_ACCEPTED",
            queue_entry_ref=queue_entry_ref,
            duplicate=False,
            state="QUEUED",
        )

    def get_record(self, queue_entry_ref: str) -> dict[str, Any]:
        record = copy.deepcopy(self._records[queue_entry_ref])
        record.pop("_envelope", None)
        record.pop("_snapshot", None)
        return record

    async def start(self) -> None:
        if self._closed:
            raise RuntimeError("queue is closed")
        if self._worker_task is None:
            self._queue = asyncio.Queue(maxsize=self._capacity)
            for queue_entry_ref in self._pending_refs:
                self._queue.put_nowait(queue_entry_ref)
            self._pending_refs.clear()
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def join(self) -> None:
        if self._queue is None:
            return
        await self._queue.join()

    async def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._worker_task is not None:
            assert self._queue is not None
            await self._queue.put(None)
            await self._worker_task
            self._worker_task = None

    def _apply_transition(
        self,
        record: dict[str, Any],
        decision: Mapping[str, Any],
    ) -> None:
        if decision.get("accepted") is not True:
            raise RuntimeError(
                f"state transition rejected: {decision.get('result_code')}"
            )
        snapshot = decision.get("next_snapshot")
        projection = decision.get("human_status_projection")
        if not isinstance(snapshot, dict) or not isinstance(projection, dict):
            raise RuntimeError("state transition returned invalid candidate")
        record["_snapshot"] = copy.deepcopy(snapshot)
        record["machine_state"] = snapshot["job_state"]
        record["owner_status"] = copy.deepcopy(projection)
        record["input_refs"] = copy.deepcopy(snapshot["input_refs"])
        record["output_refs"] = copy.deepcopy(snapshot["output_refs"])
        record["checkpoint_ref"] = snapshot["checkpoint_ref"]
        record["error_ref"] = snapshot["error_ref"]
        record["state_history"].append(snapshot["job_state"])
        record["transition_audit"].append(
            copy.deepcopy(decision["transition_candidate"])
        )

    def _claim_request(self, record: Mapping[str, Any]) -> dict[str, Any]:
        snapshot = record["_snapshot"]
        candidate_claim = {
            "attempt_id": f"acceptance:{ACCEPTANCE_ID}:{record['job_id']}",
            "lease_owner_ref": f"task:{TASK_ID}:isolated-worker",
            "lease_expires_at": "contract:isolated-process-lifetime",
            "fencing_token": snapshot["fencing_token"] + 1,
            "lock_key": record["lock_key"],
        }
        return _transition_request(
            snapshot,
            "CLAIMED",
            "claim",
            guard_facts={
                "admission_gates_passed": True,
                "claim_lease_and_lock_acquired": True,
            },
            candidate_claim=candidate_claim,
        )

    def _running_request(self, record: Mapping[str, Any]) -> dict[str, Any]:
        return _transition_request(
            record["_snapshot"],
            "RUNNING",
            "run",
            guard_facts={
                "live_lease_valid": True,
                "fencing_token_matches": True,
            },
        )

    def _success_request(
        self,
        record: Mapping[str, Any],
        operation_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        return _transition_request(
            record["_snapshot"],
            "SUCCEEDED",
            "succeed",
            guard_facts={
                "live_lease_valid": True,
                "fencing_token_matches": True,
                "output_validated": True,
            },
            output_refs=list(operation_result["output_refs"]),
            checkpoint_ref=str(operation_result["checkpoint_ref"]),
        )

    def _failure_request(
        self,
        record: Mapping[str, Any],
        error_ref: str,
    ) -> dict[str, Any]:
        return _transition_request(
            record["_snapshot"],
            "FAILED",
            "fail",
            guard_facts={
                "live_lease_valid": True,
                "fencing_token_matches": True,
                "permanent_failure_recorded": True,
                "error_evidence_present": True,
            },
            error_ref=error_ref,
        )

    def _operation_result_valid(self, value: Any) -> bool:
        if not isinstance(value, dict) or set(value) != {
            "output_refs",
            "checkpoint_ref",
        }:
            return False
        outputs = value.get("output_refs")
        checkpoint = value.get("checkpoint_ref")
        return (
            isinstance(outputs, list)
            and len(outputs) == 1
            and re.fullmatch(r"sha256:[0-9a-f]{64}", outputs[0]) is not None
            and isinstance(checkpoint, str)
            and re.fullmatch(
                r"checkpoint:sha256:[0-9a-f]{64}", checkpoint
            )
            is not None
        )

    async def _process_entry(self, queue_entry_ref: str) -> None:
        record = self._records[queue_entry_ref]
        lock = self._resource_locks.setdefault(
            record["lock_key"], asyncio.Lock()
        )
        async with lock:
            try:
                claim = self._stage037.evaluate_transition(
                    record["_snapshot"],
                    self._claim_request(record),
                    contract=self._stage037_contract,
                )
                self._apply_transition(record, claim)
                running = self._stage037.evaluate_transition(
                    record["_snapshot"],
                    self._running_request(record),
                    contract=self._stage037_contract,
                )
                self._apply_transition(record, running)

                operation_result = self._operation(record["_envelope"])
                if inspect.isawaitable(operation_result):
                    operation_result = await operation_result
                if not self._operation_result_valid(operation_result):
                    raise RuntimeError("invalid bounded operation result")

                success = self._stage037.evaluate_transition(
                    record["_snapshot"],
                    self._success_request(record, operation_result),
                    contract=self._stage037_contract,
                )
                self._apply_transition(record, success)
            except Exception as exc:
                error_ref = f"error:{type(exc).__name__}"
                if record["machine_state"] == "RUNNING":
                    failed = self._stage037.evaluate_transition(
                        record["_snapshot"],
                        self._failure_request(record, error_ref),
                        contract=self._stage037_contract,
                    )
                    if failed.get("accepted") is True:
                        self._apply_transition(record, failed)
                        return
                raise

    async def _worker_loop(self) -> None:
        assert self._queue is not None
        while True:
            queue_entry_ref = await self._queue.get()
            try:
                if queue_entry_ref is None:
                    return
                await self._process_entry(queue_entry_ref)
            finally:
                self._queue.task_done()


async def _run_isolated_slice(index: dict[str, Any]) -> dict[str, Any]:
    operation_started = asyncio.Event()
    release_operation = asyncio.Event()

    async def controlled_operation(envelope: Mapping[str, Any]) -> dict[str, Any]:
        operation_started.set()
        await release_operation.wait()
        return await _hash_tracked_control_file(envelope)

    queue = IsolatedWorkerQueue(
        capacity=DEFAULT_ISOLATED_CAPACITY,
        operation=controlled_operation,
        index=index,
    )
    await queue.start()
    envelope = build_control_envelope(CONTROL_INPUT_REF)
    acknowledgement = queue.submit(envelope)
    acknowledgement_before_worker_started = not operation_started.is_set()
    duplicate = queue.submit(envelope)
    await asyncio.wait_for(operation_started.wait(), timeout=2.0)
    running_record = queue.get_record(acknowledgement["queue_entry_ref"])
    release_operation.set()
    await asyncio.wait_for(queue.join(), timeout=2.0)
    final_record = queue.get_record(acknowledgement["queue_entry_ref"])
    await queue.shutdown()

    checks = {
        "submission_accepted": acknowledgement.get("accepted") is True,
        "submission_acknowledged_before_worker_started": (
            acknowledgement_before_worker_started
        ),
        "submission_did_not_wait_for_completion": (
            acknowledgement.get("job_completion_waited") is False
        ),
        "duplicate_returned_existing_entry": (
            duplicate.get("accepted") is True
            and duplicate.get("duplicate") is True
            and duplicate.get("queue_entry_ref")
            == acknowledgement.get("queue_entry_ref")
        ),
        "one_queue_record_created": queue.record_count == 1,
        "worker_observed_running": running_record.get("machine_state") == "RUNNING",
        "final_state_succeeded": final_record.get("machine_state") == "SUCCEEDED",
        "stage037_state_history_exact": final_record.get("state_history")
        == ["QUEUED", "CLAIMED", "RUNNING", "SUCCEEDED"],
        "bounded_input_recorded": final_record.get("input_refs")
        == [CONTROL_INPUT_REF],
        "bounded_output_recorded": (
            isinstance(final_record.get("output_refs"), list)
            and len(final_record["output_refs"]) == 1
            and final_record["output_refs"][0].startswith("sha256:")
        ),
        "checkpoint_recorded": str(final_record.get("checkpoint_ref", "")).startswith(
            "checkpoint:sha256:"
        ),
        "error_field_recorded": final_record.get("error_ref") is None,
        "record_not_persisted": final_record.get("persisted") is False,
    }
    return {
        "checks": checks,
        "submission_ack": acknowledgement,
        "duplicate_ack": duplicate,
        "running_record": running_record,
        "final_record": final_record,
        "slice_valid": all(checks.values()),
    }


def build_stage038_phase2_report(
    *,
    index: Optional[dict[str, Any]] = None,
    execute_slice: bool = True,
) -> dict[str, Any]:
    load_error: Optional[str] = None
    if index is None:
        try:
            contract = _load_index()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            contract = {}
            load_error = f"{type(exc).__name__}: {exc}"
    else:
        contract = copy.deepcopy(index) if isinstance(index, dict) else {}
        if not isinstance(index, dict):
            load_error = "index must be a JSON object"

    checks = _contract_checks(contract)
    source_integrity, observed_hashes = _source_integrity(contract)
    contract_valid = load_error is None and all(checks.values())
    report: dict[str, Any] = {
        "schema_version": "ids.stage038.worker_queue_baseline.phase2.report.v1",
        "stage": "STAGE-038",
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "execution_state": (
            "CONTRACT_VALID_RUNTIME_NOT_EXECUTED"
            if contract_valid and not execute_slice
            else "BLOCKED_INVALID_WORKER_QUEUE_CONTRACT"
        ),
        "contract_valid": contract_valid,
        "contract_checks": checks,
        "source_integrity": source_integrity,
        "observed_source_sha256": observed_hashes,
        "load_error": load_error,
        "slice_valid": False,
        "slice_checks": {},
        "submission_ack_returned_before_completion": False,
        "submission_ack": None,
        "duplicate_ack": None,
        "running_record": None,
        "final_record": None,
        "queue_runtime_performed": False,
        "worker_runtime_performed": False,
        "isolated_control_job_created": False,
        "production_runtime_activation_performed": False,
        "claim_persistence_performed": False,
        "persistent_queue_write_performed": False,
        "database_connection_performed": False,
        "schema_change_performed": False,
        "state_registry_write_performed": False,
        "runtime_output_written": False,
        "ids_business_source_read_performed": False,
        "external_api_call_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "real_ids_business_job_created": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "next_gate": NEXT_GATE,
        "owner_feedback_zh": (
            "Worker 队列 Phase 2 合同无效；未启动隔离队列或 worker。"
            if not contract_valid
            else "Worker 队列 Phase 2 合同有效；隔离运行切片尚未执行。"
        ),
    }
    if not contract_valid or not execute_slice:
        return report

    try:
        slice_result = asyncio.run(_run_isolated_slice(contract))
    except (OSError, RuntimeError, ValueError, asyncio.TimeoutError) as exc:
        report["execution_state"] = "BLOCKED_ISOLATED_SLICE_FAILED"
        report["load_error"] = f"{type(exc).__name__}: {exc}"
        report["owner_feedback_zh"] = (
            "隔离 Worker 队列切片执行失败；未激活生产队列、数据库或原始资料访问。"
        )
        return report

    report.update(
        {
            "slice_valid": slice_result["slice_valid"],
            "slice_checks": slice_result["checks"],
            "submission_ack_returned_before_completion": slice_result["checks"][
                "submission_acknowledged_before_worker_started"
            ],
            "submission_ack": slice_result["submission_ack"],
            "duplicate_ack": slice_result["duplicate_ack"],
            "running_record": slice_result["running_record"],
            "final_record": slice_result["final_record"],
            "queue_runtime_performed": True,
            "worker_runtime_performed": True,
            "isolated_control_job_created": True,
            "execution_state": (
                "ISOLATED_ASYNC_SLICE_SUCCEEDED_PRODUCTION_DISABLED"
                if slice_result["slice_valid"]
                else "BLOCKED_ISOLATED_SLICE_INVALID"
            ),
            "owner_feedback_zh": (
                "隔离 Worker 队列切片已完成：提交立即返回，后台 worker 处理真实 Git-tracked "
                "控制文件引用并记录输入、输出、错误字段和 checkpoint；生产运行继续禁用。"
                if slice_result["slice_valid"]
                else "隔离 Worker 队列切片未通过全部检查；生产运行继续禁用。"
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage038_phase2_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["contract_valid"] and report["slice_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
