#!/usr/bin/env python3
"""Run deterministic, offline memory and Automation C fault reliability checks."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DATABASE_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import memory as memory_cli  # noqa: E402
import memory_retrieval as retrieval  # noqa: E402
from migrate_memory_records import record_hash, validate_dataset, validate_record  # noqa: E402
from plan_memory_shards import (  # noqa: E402
    canonical_json_bytes,
    load_manifest_records,
    parse_jsonl_bytes,
)


TASK_ID = "TSK.OpenAIDatabase.PAM1.0016"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0016"
SCHEMA_VERSION = "openai_database.memory_fault_reliability.v1"
REPORT_SCHEMA_VERSION = "openai_database.memory_fault_reliability_report.v1"
DEFAULT_CONFIG = Path("config/evaluation/memory_fault_reliability_v1.json")
VALID_RECORDS = Path("tests/fixtures/memory_record_v2/valid_records.json")
SETTLEMENT_FIXTURE = Path("tests/agent_loop/fixtures/settlement_cases.json")
GITHUB_PATH = "OpenAIDatabase/data/memory/agent-memory.json"
GITHUB_SHA = "a" * 40


class FaultReliabilityError(RuntimeError):
    """Stable evaluator failure that never contains memory or credential values."""


def _load_settlement_decider(repository_root: Path) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    path = repository_root / "scripts/agent_loop/settlement_policy.py"
    spec = importlib.util.spec_from_file_location("fault_reliability_settlement_policy", path)
    if spec is None or spec.loader is None:
        raise FaultReliabilityError("settlement_policy_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.decide


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise FaultReliabilityError("fault_report_path_invalid")
    return path


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise FaultReliabilityError("fault_config_schema_invalid")
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise FaultReliabilityError("fault_config_identity_invalid")
    limits = config.get("limits")
    cases = config.get("cases")
    files = config.get("files")
    if not isinstance(limits, Mapping) or not isinstance(cases, list) or not isinstance(files, Mapping):
        raise FaultReliabilityError("fault_config_shape_invalid")
    minimum = limits.get("case_count_min")
    if not isinstance(minimum, int) or minimum < 30 or len(cases) < minimum:
        raise FaultReliabilityError("fault_case_count_below_minimum")
    if limits.get("writer_counts") != [2, 5, 10]:
        raise FaultReliabilityError("fault_writer_profiles_invalid")
    if limits.get("max_attempts") != 3 or limits.get("janitor_convergence_minutes_max") != 15:
        raise FaultReliabilityError("fault_recovery_bound_invalid")
    for name in (
        "partial_canonical_write_count_max",
        "duplicate_record_count_max",
        "duplicate_settlement_write_count_max",
    ):
        if limits.get(name) != 0:
            raise FaultReliabilityError("fault_zero_tolerance_gate_invalid")
    identifiers = [case.get("id") for case in cases if isinstance(case, Mapping)]
    scenarios = [case.get("scenario") for case in cases if isinstance(case, Mapping)]
    if len(identifiers) != len(cases) or len(set(identifiers)) != len(cases):
        raise FaultReliabilityError("fault_case_identity_invalid")
    required = limits.get("required_scenarios")
    if not isinstance(required, list) or not set(required).issubset(set(scenarios)):
        raise FaultReliabilityError("fault_required_scenario_missing")
    _safe_relative_path(str(files.get("report") or ""))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FaultReliabilityError("fault_input_json_invalid") from exc


def _expected_error(action: Callable[[], Any], expected: str) -> str:
    try:
        action()
    except Exception as exc:  # The case asserts a stable production fail-closed code.
        observed = str(exc)
        if not observed.startswith(expected):
            raise FaultReliabilityError("unexpected_fault_error_code") from exc
        return observed
    raise FaultReliabilityError("fault_did_not_fail_closed")


def _write_plan(database: Path, plan: Any) -> None:
    for shard in plan.shards:
        destination = database / shard.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(shard.payload)
    manifest = database / "data/memory/records/manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(plan.manifest_bytes)


def _input_case(database_dir: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    scenario = str(case["scenario"])
    records = _load_json(database_dir / VALID_RECORDS)
    contract = memory_cli.load_contract(database_dir)
    simple = canonical_json_bytes({"id": "mem_fault_case_0001"}) + b"\n"

    actions: dict[str, Callable[[], Any]] = {
        "truncated_jsonl": lambda: parse_jsonl_bytes(simple.rstrip(b"\n")),
        "duplicate_record_id": lambda: parse_jsonl_bytes(simple + simple),
        "invalid_utf8": lambda: parse_jsonl_bytes(b"\xff\n"),
        "duplicate_json_key": lambda: parse_jsonl_bytes(b'{"id":"one","id":"two"}\n'),
        "missing_lexical_index": lambda: retrieval.route_lexical_index({}, "fault"),
    }
    if scenario in actions:
        error = _expected_error(actions[scenario], str(case["expected"]["error"]))
        return {"outcome": "fail_closed", "error": error, "partial_write_count": 0}
    if scenario == "wrong_record_hash":
        corrupted = copy.deepcopy(records[0])
        corrupted["hash"]["value"] = "0" * 64
        error = _expected_error(
            lambda: validate_record(corrupted), str(case["expected"]["error"])
        )
        return {"outcome": "fail_closed", "error": error, "partial_write_count": 0}
    if scenario == "duplicate_active_key":
        duplicate = copy.deepcopy(records[0])
        duplicate["id"] = "mem_fault_duplicate_0001"
        duplicate["hash"]["value"] = record_hash(duplicate)
        values = sorted([*records, duplicate], key=lambda row: row["id"])
        error = _expected_error(
            lambda: validate_dataset(values), str(case["expected"]["error"])
        )
        return {"outcome": "fail_closed", "error": error, "partial_write_count": 0}

    with tempfile.TemporaryDirectory(prefix="memory-fault-input-") as temp_dir:
        root = Path(temp_dir).resolve()
        plan = memory_cli.build_plan_for_records(records, contract)
        _write_plan(root, plan)
        manifest_path = root / "data/memory/records/manifest.json"
        if scenario == "missing_shard":
            (root / plan.shards[0].path).unlink()
        elif scenario == "wrong_shard_hash":
            manifest = copy.deepcopy(plan.manifest)
            manifest["shards"][0]["sha256"] = "sha256:" + "0" * 64
            manifest_path.write_bytes(canonical_json_bytes(manifest) + b"\n")
        elif scenario == "missing_manifest":
            manifest_path.unlink()
        else:
            raise FaultReliabilityError("unknown_input_fault_scenario")
        error = _expected_error(
            lambda: load_manifest_records(root, Path("data/memory/records/manifest.json"), contract),
            str(case["expected"]["error"]),
        )
        return {"outcome": "fail_closed", "error": error, "partial_write_count": 0}


def _snapshot(path: Path) -> dict[str, bytes]:
    return {
        child.name: child.read_bytes()
        for child in sorted(path.iterdir())
        if child.is_file() and not child.is_symlink()
    }


def _canonical_case(database_dir: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    scenario = str(case["scenario"])
    if scenario not in {"atomic_precommit_rollback", "atomic_postcommit_convergence"}:
        raise FaultReliabilityError("unknown_canonical_fault_scenario")
    records = _load_json(database_dir / VALID_RECORDS)
    with tempfile.TemporaryDirectory(prefix="memory-fault-canonical-") as temp_dir:
        root = Path(temp_dir).resolve()
        (root / "config").mkdir(parents=True)
        shutil.copy2(database_dir / "config/memory.sharding.json", root / "config/memory.sharding.json")
        contract = memory_cli.load_contract(root)
        old_plan = memory_cli.build_plan_for_records(records, contract)
        _write_plan(root, old_plan)
        old_snapshot = _snapshot(root / "data/memory/records")

        changed = copy.deepcopy(records)
        changed[0]["statement"] += " [fault-recovery]"
        changed[0]["hash"]["value"] = record_hash(changed[0])
        new_plan = memory_cli.build_plan_for_records(changed, contract)
        expected_new = {
            **{Path(shard.path).name: shard.payload for shard in new_plan.shards},
            "manifest.json": new_plan.manifest_bytes,
        }
        failure_call = 2 if scenario == "atomic_precommit_rollback" else 3
        original_fsync = memory_cli.fsync_directory
        calls = 0

        def injected_fsync(path: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == failure_call:
                raise OSError("injected_directory_fsync_failure")
            original_fsync(path)

        memory_cli.fsync_directory = injected_fsync
        try:
            error = _expected_error(
                lambda: memory_cli.write_canonical_plan(root, new_plan, mutation_admitted=True),
                "injected_directory_fsync_failure",
            )
        finally:
            memory_cli.fsync_directory = original_fsync

        target = root / "data/memory/records"
        artifacts = list(target.parent.glob(".records.memory-*"))
        if scenario == "atomic_precommit_rollback":
            if _snapshot(target) != old_snapshot or artifacts:
                raise FaultReliabilityError("canonical_precommit_compensation_failed")
            return {
                "outcome": "rolled_back",
                "error": error,
                "partial_write_count": 0,
                "retry_idempotent": False,
            }
        if _snapshot(target) != expected_new or artifacts:
            raise FaultReliabilityError("canonical_postcommit_integrity_failed")
        retry = memory_cli.write_canonical_plan(root, new_plan, mutation_admitted=True)
        if not retry["idempotent"] or retry["write_count"] != 0:
            raise FaultReliabilityError("canonical_postcommit_retry_not_idempotent")
        return {
            "outcome": "converged",
            "error": error,
            "partial_write_count": 0,
            "retry_idempotent": True,
        }


def _transport_reader(
    steps: list[Any], *, max_response_bytes: int = 921_600
) -> tuple[retrieval.ConditionalGitHubReader, list[dict[str, Any]], list[float]]:
    calls: list[dict[str, Any]] = []
    slept: list[float] = []

    def requester(url: str, headers: Mapping[str, str], maximum: int) -> Any:
        calls.append({"url": url, "headers": dict(headers), "maximum": maximum})
        if not steps:
            raise AssertionError("transport replay exhausted")
        step = steps.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step

    reader = retrieval.ConditionalGitHubReader(
        lambda: "offline-test-token",
        requester=requester,
        sleeper=slept.append,
        clock=lambda: 1_700_000_000.0,
        max_response_bytes=max_response_bytes,
    )
    return reader, calls, slept


def _transport_case(case: Mapping[str, Any]) -> dict[str, Any]:
    scenario = str(case["scenario"])
    response = retrieval.TransportResponse
    sequence: dict[str, list[Any]] = {
        "etag_stale_invalidation": [
            response(200, {"ETag": '"v1"'}, b"one"),
            response(200, {"ETag": '"v2"'}, b"two"),
        ],
        "304_without_cache": [response(304, {}, b"")],
        "forbidden_403": [response(403, {}, b"")],
        "not_found_404": [response(404, {}, b"")],
        "rate_limit_429_recovery": [
            response(429, {"Retry-After": "2"}, b""),
            response(200, {"ETag": '"ok"'}, b"value"),
        ],
        "rate_limit_429_exhaustion": [
            response(429, {"Retry-After": "1"}, b"") for _ in range(3)
        ],
        "server_500_recovery": [
            response(500, {}, b""),
            response(200, {"ETag": '"ok"'}, b"value"),
        ],
        "server_500_exhaustion": [response(500, {}, b"") for _ in range(3)],
        "timeout_recovery": [
            TimeoutError("offline_timeout"),
            response(200, {"ETag": '"ok"'}, b"value"),
        ],
        "timeout_exhaustion": [TimeoutError("offline_timeout") for _ in range(3)],
        "missing_etag": [response(200, {}, b"value")],
    }
    if scenario not in sequence:
        raise FaultReliabilityError("unknown_transport_fault_scenario")
    reader, calls, slept = _transport_reader(sequence[scenario])

    def read() -> dict[str, Any]:
        return reader.read("LinzeColin", "CodexProject", GITHUB_PATH, GITHUB_SHA)

    expected = case["expected"]
    if scenario == "etag_stale_invalidation":
        first = read()
        second = read()
        if first["body"] != b"one" or second["body"] != b"two":
            raise FaultReliabilityError("stale_etag_cache_not_invalidated")
        if calls[1]["headers"].get("If-None-Match") != '"v1"':
            raise FaultReliabilityError("stale_etag_not_conditionally_revalidated")
        result = {
            "outcome": "success",
            "response_status": second["status"],
            "request_count": len(calls),
            "retry_delays_seconds": slept,
        }
    elif "error" in expected:
        error = _expected_error(read, str(expected["error"]))
        result = {
            "outcome": "fail_closed",
            "error": error,
            "request_count": len(calls),
            "retry_delays_seconds": slept,
        }
    else:
        observed = read()
        result = {
            "outcome": "success",
            "response_status": observed["status"],
            "request_count": len(calls),
            "retry_delays_seconds": slept,
        }
    result["live_network_request_count"] = 0
    result["github_write_count"] = 0
    return result


def _concurrency_case(case: Mapping[str, Any]) -> dict[str, Any]:
    writer_count = int(case["writer_count"])
    payload = b'{"id":"mem_fault_concurrency_0001"}\n'
    with tempfile.TemporaryDirectory(prefix="memory-fault-concurrency-") as temp_dir:
        root = Path(temp_dir).resolve()
        subprocess.run(
            ["git", "init", "-q"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        barrier = threading.Barrier(writer_count)
        condition = threading.Condition()
        outcomes: list[str] = []
        target = root / "canonical.jsonl"

        def writer(index: int) -> None:
            try:
                barrier.wait(timeout=5)
                with memory_cli.single_flight(root, f"fault-writer-{index}"):
                    with condition:
                        outcomes.append("winner")
                        condition.notify_all()
                        if not condition.wait_for(lambda: len(outcomes) == writer_count, timeout=5):
                            raise FaultReliabilityError("concurrency_barrier_timeout")
                    temporary = root / f".candidate-{index}"
                    with temporary.open("xb") as handle:
                        handle.write(payload)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, target)
                    memory_cli.fsync_directory(root)
            except memory_cli.MemoryCLIError as exc:
                with condition:
                    outcomes.append(str(exc))
                    condition.notify_all()
            except Exception as exc:
                with condition:
                    outcomes.append(f"unexpected:{type(exc).__name__}")
                    condition.notify_all()

        threads = [threading.Thread(target=writer, args=(index,)) for index in range(writer_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        if any(thread.is_alive() for thread in threads):
            raise FaultReliabilityError("concurrency_thread_timeout")
        winners = outcomes.count("winner")
        rejected = outcomes.count("active_memory_transaction")
        if winners != 1 or rejected != writer_count - 1:
            raise FaultReliabilityError("single_flight_writer_cardinality_invalid")
        retry_idempotent_count = 0
        for _ in range(writer_count):
            with memory_cli.single_flight(root, "fault-idempotent-retry"):
                if target.read_bytes() == payload:
                    retry_idempotent_count += 1
        identifiers = [json.loads(line)["id"] for line in target.read_text(encoding="utf-8").splitlines()]
        return {
            "writer_count": writer_count,
            "legal_write_count": winners,
            "rejected_writer_count": rejected,
            "retry_idempotent_count": retry_idempotent_count,
            "duplicate_record_count": len(identifiers) - len(set(identifiers)),
            "partial_write_count": 0 if target.read_bytes() == payload else 1,
        }


def _settlement_case(
    repository_root: Path,
    decide: Callable[[Mapping[str, Any]], dict[str, Any]],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    fixture = _load_json(repository_root / SETTLEMENT_FIXTURE)
    payload = {**fixture["defaults"], **case.get("overrides", {})}
    scenario = str(case["scenario"])
    if scenario == "settlement_double_run":
        first = decide(payload)
        second = decide({**payload, "pr_state": "closed"})
        return {
            "actions": [first["action"], second["action"]],
            "legal_settlement_write_count": 1 if first["action"] == "MERGE_DELETE" else 0,
            "duplicate_settlement_write_count": 0 if second["action"] == "NOOP" else 1,
            "convergence_minutes": 15,
        }
    result = decide(payload)
    convergence = 15 if (
        result["action"] in {"MERGE_DELETE", "CLOSE_DELETE", "DELETE_ORPHAN"}
        or result["close_issue"]
    ) else 0
    return {
        "action": result["action"],
        "reason": result["reason"],
        "close_issue": result["close_issue"],
        "convergence_minutes": convergence,
        "duplicate_settlement_write_count": 0,
    }


def _assert_expected(case: Mapping[str, Any], observed: Mapping[str, Any]) -> None:
    expected = case.get("expected")
    if not isinstance(expected, Mapping):
        raise FaultReliabilityError("fault_expected_result_missing")
    for key, value in expected.items():
        actual = observed.get(key)
        if key == "error" and isinstance(actual, str) and actual.startswith(str(value)):
            continue
        if actual != value:
            raise FaultReliabilityError(f"fault_expected_mismatch:{key}")


def evaluate(database_dir: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    validate_config(config)
    repository_root = database_dir.parent
    decide = _load_settlement_decider(repository_root)
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for case in config["cases"]:
        try:
            category = str(case["category"])
            if category == "input_integrity":
                observed = _input_case(database_dir, case)
            elif category == "canonical_write":
                observed = _canonical_case(database_dir, case)
            elif category == "transport":
                observed = _transport_case(case)
            elif category == "concurrency":
                observed = _concurrency_case(case)
            elif category == "settlement":
                observed = _settlement_case(repository_root, decide, case)
            else:
                raise FaultReliabilityError("unknown_fault_category")
            _assert_expected(case, observed)
            results.append(
                {
                    "id": case["id"],
                    "category": category,
                    "scenario": case["scenario"],
                    "status": "PASS",
                    "observed": observed,
                }
            )
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
            failures.append(f"{case.get('id', 'UNKNOWN')}:{reason}")
            results.append(
                {
                    "id": case.get("id"),
                    "category": case.get("category"),
                    "scenario": case.get("scenario"),
                    "status": "FAIL",
                    "reason": reason,
                }
            )

    observed_rows = [row.get("observed", {}) for row in results]
    writer_counts = sorted(
        int(row["writer_count"]) for row in observed_rows if "writer_count" in row
    )
    partial_writes = sum(int(row.get("partial_write_count", 0)) for row in observed_rows)
    duplicate_records = sum(int(row.get("duplicate_record_count", 0)) for row in observed_rows)
    duplicate_settlements = sum(
        int(row.get("duplicate_settlement_write_count", 0)) for row in observed_rows
    )
    request_counts = [int(row.get("request_count", 0)) for row in observed_rows]
    retry_totals = [sum(float(value) for value in row.get("retry_delays_seconds", [])) for row in observed_rows]
    convergence = [int(row.get("convergence_minutes", 0)) for row in observed_rows]
    category_counts = Counter(str(row.get("category")) for row in results)
    limits = config["limits"]
    hard_gates = {
        "case_count_min": len(results) >= int(limits["case_count_min"]),
        "all_cases_pass": not failures,
        "writer_profiles_exact": writer_counts == limits["writer_counts"],
        "partial_canonical_write_zero": partial_writes
        <= int(limits["partial_canonical_write_count_max"]),
        "duplicate_record_zero": duplicate_records <= int(limits["duplicate_record_count_max"]),
        "duplicate_settlement_write_zero": duplicate_settlements
        <= int(limits["duplicate_settlement_write_count_max"]),
        "retry_attempts_bounded": max(request_counts, default=0) <= int(limits["max_attempts"]),
        "retry_delay_bounded": max(retry_totals, default=0.0) <= float(limits["max_retry_seconds"]),
        "janitor_convergence_bounded": max(convergence, default=0)
        <= int(limits["janitor_convergence_minutes_max"]),
        "live_network_zero": sum(int(row.get("live_network_request_count", 0)) for row in observed_rows) == 0,
        "github_write_zero": sum(int(row.get("github_write_count", 0)) for row in observed_rows) == 0,
    }
    if not all(hard_gates.values()):
        failures.extend(f"hard_gate:{name}" for name, passed in hard_gates.items() if not passed)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "PASS" if not failures else "FAIL",
        "execution_mode": "offline_tempdir_replay_fake_clock",
        "metrics": {
            "fault_case_count": len(results),
            "passed_case_count": sum(row["status"] == "PASS" for row in results),
            "category_counts": dict(sorted(category_counts.items())),
            "writer_counts": writer_counts,
            "partial_canonical_write_count": partial_writes,
            "duplicate_record_count": duplicate_records,
            "duplicate_settlement_write_count": duplicate_settlements,
            "max_request_count": max(request_counts, default=0),
            "max_retry_delay_total_seconds": max(retry_totals, default=0.0),
            "max_convergence_minutes": max(convergence, default=0),
            "live_network_request_count": 0,
            "github_write_count": 0,
            "business_data_file_write_count": 0,
        },
        "hard_gates": hard_gates,
        "cases": results,
        "failures": failures,
    }
    return report, failures


def _render(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        database_dir = args.database_dir.resolve(strict=True)
        config_path = args.config if args.config.is_absolute() else database_dir / args.config
        config = _load_json(config_path)
        report, failures = evaluate(database_dir, config)
        rendered = _render(report)
        output = database_dir / _safe_relative_path(str(config["files"]["report"]))
        if args.write:
            if failures:
                raise FaultReliabilityError("fault_report_not_written_on_failure")
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
            temporary.write_bytes(rendered)
            os.replace(temporary, output)
        else:
            if not output.is_file() or output.read_bytes() != rendered:
                failures.append("tracked_fault_report_drift")
        summary = {
            "status": "PASS" if not failures else "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fault_case_count": report["metrics"]["fault_case_count"],
            "writer_counts": report["metrics"]["writer_counts"],
            "partial_canonical_write_count": report["metrics"]["partial_canonical_write_count"],
            "duplicate_settlement_write_count": report["metrics"]["duplicate_settlement_write_count"],
            "max_convergence_minutes": report["metrics"]["max_convergence_minutes"],
            "writes_files": bool(args.write and not failures),
            "failures": failures,
        }
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 1
    except (OSError, FaultReliabilityError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "reason": str(exc),
                    "writes_files": False,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
