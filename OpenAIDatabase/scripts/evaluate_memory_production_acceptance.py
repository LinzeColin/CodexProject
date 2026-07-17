#!/usr/bin/env python3
"""Evaluate candidate and published Portable Agent Memory V1 acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_ID = "TSK.OpenAIDatabase.PAM1.0019"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0019"
CONFIG_SCHEMA = "openai_database.memory_production_acceptance_config.v1"
REPORT_SCHEMA = "openai_database.memory_production_acceptance_report.v1"
DEFAULT_CONFIG = Path("config/evaluation/memory_production_acceptance_v1.json")
SNAPSHOT_REPOSITORY = "LinzeColin/AgentDatabase"
SNAPSHOT_REPOSITORY_VISIBILITY = "public"
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
REQUIRED_CHECK_NAMES = (
    "governance",
    "openai-database-verify",
    "memory-atlas-verify",
)
PUBLISHED_HISTORY_DEPTH_MIN = 2
PUBLISHED_HISTORY_DEPTH_MAX = 256


class ProductionAcceptanceError(RuntimeError):
    """Fail-closed production acceptance error with a stable reason."""


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_json_strict(path: Path, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProductionAcceptanceError(f"{label}_duplicate_key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except ProductionAcceptanceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProductionAcceptanceError(f"{label}_invalid_json") from exc
    if not isinstance(value, dict):
        raise ProductionAcceptanceError(f"{label}_not_object")
    return value


def safe_repo_file(database_dir: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ProductionAcceptanceError("unsafe_repository_path")
    root = database_dir.resolve(strict=True)
    candidate = root.joinpath(*path.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ProductionAcceptanceError("repository_file_unavailable") from exc
    if candidate.is_symlink() or not resolved.is_file():
        raise ProductionAcceptanceError("repository_file_not_regular")
    return resolved


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 900,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProductionAcceptanceError("command_execution_failed") from exc
    if completed.returncode != 0:
        command_name = Path(args[1] if len(args) > 1 else args[0]).name
        raise ProductionAcceptanceError(f"required_command_failed_{command_name}")
    return completed


def run_json(args: Sequence[str], *, cwd: Path, timeout: int = 900) -> dict[str, Any]:
    completed = run_command(args, cwd=cwd, timeout=timeout)
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProductionAcceptanceError("required_command_invalid_json") from exc
    if not isinstance(value, dict):
        raise ProductionAcceptanceError("required_command_json_not_object")
    return value


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != CONFIG_SCHEMA:
        raise ProductionAcceptanceError("config_schema_mismatch")
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise ProductionAcceptanceError("config_identity_mismatch")
    release = config.get("release")
    gates = config.get("hard_gates")
    proofs = config.get("proof_obligations")
    if not isinstance(release, dict) or not isinstance(gates, dict) or not isinstance(proofs, dict):
        raise ProductionAcceptanceError("config_contract_missing")
    if release.get("version") != "1.0.0" or release.get("source_branch") != "main":
        raise ProductionAcceptanceError("release_identity_mismatch")
    if release.get("snapshot_repository") != SNAPSHOT_REPOSITORY:
        raise ProductionAcceptanceError("snapshot_repository_mismatch")
    if release.get("snapshot_repository_visibility") != SNAPSHOT_REPOSITORY_VISIBILITY:
        raise ProductionAcceptanceError("release_visibility_not_public")
    if tuple(proofs) != (
        "Discovery",
        "Read",
        "Retrieval",
        "Mutation",
        "Forgetting",
        "Recovery",
    ):
        raise ProductionAcceptanceError("proof_obligations_mismatch")
    publication = config.get("publication")
    if not isinstance(publication, dict) or any(
        publication.get(key) is not False
        for key in ("direct_main_push_allowed", "force_push_allowed", "history_rewrite_allowed")
    ):
        raise ProductionAcceptanceError("publication_safety_mismatch")
    if tuple(publication.get("required_check_names") or ()) != REQUIRED_CHECK_NAMES:
        raise ProductionAcceptanceError("required_check_contract_mismatch")
    history_depth = publication.get("accepted_history_fetch_depth")
    if (
        not isinstance(history_depth, int)
        or isinstance(history_depth, bool)
        or not PUBLISHED_HISTORY_DEPTH_MIN <= history_depth <= PUBLISHED_HISTORY_DEPTH_MAX
    ):
        raise ProductionAcceptanceError("published_history_fetch_depth_invalid")
    if publication.get("public_safe_asset_only") is not True:
        raise ProductionAcceptanceError("public_release_safety_missing")


def require_pass(report: Mapping[str, Any], label: str) -> None:
    if report.get("status") != "PASS":
        raise ProductionAcceptanceError(f"{label}_not_pass")


def require_boolean_gates(report: Mapping[str, Any], label: str) -> None:
    gates = report.get("hard_gates")
    if not isinstance(gates, dict) or not gates or any(value is not True for value in gates.values()):
        raise ProductionAcceptanceError(f"{label}_hard_gate_failure")


def require_metric(
    metrics: Mapping[str, Any],
    key: str,
    threshold: float,
    *,
    operator: str,
) -> None:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProductionAcceptanceError(f"metric_missing_{key}")
    if operator == "gte" and value < threshold:
        raise ProductionAcceptanceError(f"metric_below_gate_{key}")
    if operator == "lte" and value > threshold:
        raise ProductionAcceptanceError(f"metric_above_gate_{key}")
    if operator == "eq" and value != threshold:
        raise ProductionAcceptanceError(f"metric_not_equal_gate_{key}")


def rerun_candidate_dependencies(
    database_dir: Path,
    *,
    recovery_source_commit: str | None = None,
) -> dict[str, Any] | None:
    python = sys.executable
    commands = (
        (python, "scripts/evaluate_memory_gold_benchmark.py", "--suite", "full", "--check"),
        (python, "scripts/evaluate_memory_retrieval_performance.py", "--check"),
        (python, "scripts/evaluate_memory_fault_reliability.py", "--check"),
        (python, "scripts/evaluate_memory_automation_c_e2e.py", "--check"),
    )
    for command in commands:
        run_command(command, cwd=database_dir)
    if recovery_source_commit is None:
        run_command(
            (python, "scripts/evaluate_memory_snapshot_recovery.py", "--check"),
            cwd=database_dir,
        )
        return None
    return run_json(
        (
            python,
            "scripts/evaluate_memory_snapshot_recovery.py",
            "--source-commit",
            recovery_source_commit,
            "--ephemeral",
        ),
        cwd=database_dir,
    )


def load_required_reports(
    database_dir: Path,
    config: Mapping[str, Any],
    *,
    recovery_override: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    declared = config.get("required_reports")
    if not isinstance(declared, dict) or set(declared) != {
        "benchmark",
        "performance",
        "fault",
        "e2e",
        "recovery",
    }:
        raise ProductionAcceptanceError("required_report_contract_mismatch")
    reports: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for label, relative in declared.items():
        if label == "recovery" and recovery_override is not None:
            reports[label] = dict(recovery_override)
            hashes[label] = sha256_prefixed(canonical_json_bytes(reports[label]))
            continue
        path = safe_repo_file(database_dir, str(relative))
        reports[label] = load_json_strict(path, f"report_{label}")
        hashes[label] = sha256_prefixed(path.read_bytes())
    return reports, dict(sorted(hashes.items()))


def validate_report_gates(
    reports: Mapping[str, Mapping[str, Any]], config: Mapping[str, Any]
) -> dict[str, Any]:
    gates = config["hard_gates"]
    benchmark = reports["benchmark"]
    performance = reports["performance"]
    fault = reports["fault"]
    e2e = reports["e2e"]
    recovery = reports["recovery"]
    for label, report in reports.items():
        require_pass(report, label)

    if benchmark.get("suite") != "full" or benchmark.get("case_count") != gates["benchmark_case_count"]:
        raise ProductionAcceptanceError("benchmark_scope_mismatch")
    if benchmark.get("hard_gate_failures") != []:
        raise ProductionAcceptanceError("benchmark_hard_gate_failure")
    benchmark_metrics = benchmark.get("metrics")
    if not isinstance(benchmark_metrics, dict):
        raise ProductionAcceptanceError("benchmark_metrics_missing")
    for metric, config_key, operator in (
        ("recall_at_5", "recall_at_5_min", "gte"),
        ("mrr", "mrr_min", "gte"),
        ("current_state_accuracy", "current_state_accuracy_min", "gte"),
        ("provenance_accuracy", "provenance_accuracy_min", "gte"),
        ("abstention_precision", "abstention_precision_min", "gte"),
        ("abstention_recall", "abstention_recall_min", "gte"),
        ("fama", "fama_min", "gte"),
        ("critical_stale_use_count", "critical_stale_use_count_max", "lte"),
        ("profile_pass_count", "profile_pass_count", "gte"),
    ):
        require_metric(benchmark_metrics, metric, float(gates[config_key]), operator=operator)

    if performance.get("hard_gate_failures") != []:
        raise ProductionAcceptanceError("performance_hard_gate_failure")
    runtime = performance.get("runtime_observation")
    runtime_metrics = runtime.get("metrics") if isinstance(runtime, dict) else None
    if not isinstance(runtime_metrics, dict):
        raise ProductionAcceptanceError("performance_runtime_missing")
    require_metric(
        runtime_metrics,
        "local_query_p95_ms",
        float(gates["local_query_p95_ms_max"]),
        operator="lte",
    )
    require_metric(
        runtime_metrics,
        "index_rebuild_p95_ms",
        float(gates["rebuild_p95_ms_max"]),
        operator="lte",
    )

    require_boolean_gates(fault, "fault")
    fault_metrics = fault.get("metrics")
    if not isinstance(fault_metrics, dict):
        raise ProductionAcceptanceError("fault_metrics_missing")
    require_metric(
        fault_metrics,
        "fault_case_count",
        float(gates["fault_case_count_min"]),
        operator="gte",
    )
    for metric in (
        "partial_canonical_write_count",
        "duplicate_record_count",
        "duplicate_settlement_write_count",
    ):
        require_metric(fault_metrics, metric, 0, operator="eq")

    require_boolean_gates(e2e, "e2e")
    e2e_metrics = e2e.get("metrics")
    if not isinstance(e2e_metrics, dict):
        raise ProductionAcceptanceError("e2e_metrics_missing")
    require_metric(
        e2e_metrics,
        "passed_scenario_count",
        float(gates["e2e_scenario_count"]),
        operator="eq",
    )
    for metric in ("partial_canonical_write_count", "duplicate_record_count", "duplicate_pr_count"):
        require_metric(e2e_metrics, metric, 0, operator="eq")

    roundtrip = recovery.get("roundtrip")
    rto = recovery.get("rto")
    if not isinstance(roundtrip, dict) or not isinstance(rto, dict):
        raise ProductionAcceptanceError("recovery_contract_missing")
    if (
        roundtrip.get("status") != "PASS"
        or roundtrip.get("hash_identical_percent") != gates["canonical_hash_match_percent"]
        or roundtrip.get("partial_restore_count") != 0
        or rto.get("status") != "PASS"
        or rto.get("target_seconds") > gates["recovery_rto_seconds_max"]
    ):
        raise ProductionAcceptanceError("recovery_hard_gate_failure")

    return {
        "benchmark_case_count": benchmark["case_count"],
        "metrics": {
            key: benchmark_metrics[key]
            for key in (
                "recall_at_5",
                "mrr",
                "current_state_accuracy",
                "provenance_accuracy",
                "abstention_precision",
                "abstention_recall",
                "fama",
                "critical_stale_use_count",
            )
        },
        "local_query_p95_ms": runtime_metrics["local_query_p95_ms"],
        "index_rebuild_p95_ms": runtime_metrics["index_rebuild_p95_ms"],
        "fault_case_count": fault_metrics["fault_case_count"],
        "e2e_scenario_count": e2e_metrics["passed_scenario_count"],
        "recovery_hash_identical_percent": roundtrip["hash_identical_percent"],
        "recovery_rto_target_seconds": rto["target_seconds"],
    }


def validate_writer_and_shims(database_dir: Path, doctor: Mapping[str, Any]) -> dict[str, Any]:
    require_pass(doctor, "doctor")
    ownership = load_json_strict(
        safe_repo_file(database_dir, "config/command_ownership.json"),
        "command_ownership",
    )
    memory_cli = ownership.get("memory_cli")
    if not isinstance(memory_cli, dict) or memory_cli.get("implementation") != "scripts/memory.py":
        raise ProductionAcceptanceError("canonical_writer_missing")
    if doctor.get("legacy_independent_writer_count") != 0:
        raise ProductionAcceptanceError("legacy_independent_writer_present")
    wrappers = memory_cli.get("compatibility_wrappers")
    retired = memory_cli.get("retired_writers")
    if wrappers != ["scripts/import_public_raw_evidence.py"] or retired != ["scripts/migrate_memory_records.py"]:
        raise ProductionAcceptanceError("shim_registry_drift")
    wrapper_text = safe_repo_file(database_dir, wrappers[0]).read_text(encoding="utf-8")
    retired_text = safe_repo_file(database_dir, retired[0]).read_text(encoding="utf-8")
    if "MEMORY_CLI_THIN_WRAPPER = True" not in wrapper_text or "from memory import main as memory_main" not in wrapper_text:
        raise ProductionAcceptanceError("compatibility_wrapper_not_thin")
    if "LEGACY_CANONICAL_WRITE_RETIRED = True" not in retired_text or "legacy canonical writer retired" not in retired_text:
        raise ProductionAcceptanceError("retired_writer_not_fail_closed")
    for relative in (
        "tests/test_public_raw_import.py",
        "tests/test_memory_cli.py",
        "tests/test_memory_canonical_cutover.py",
    ):
        safe_repo_file(database_dir, relative)
    return {
        "canonical_writer_count": 1,
        "canonical_writer": "scripts/memory.py",
        "legacy_independent_writer_count": 0,
        "registered_compatibility_wrapper_count": 1,
        "registered_retired_replay_tool_count": 1,
        "proven_unused_shim_count": 0,
        "removed_shim_count": 0,
    }


def evaluate_candidate(
    database_dir: Path,
    config_path: Path = DEFAULT_CONFIG,
    *,
    artifact_ref: str = "CANDIDATE_TREE",
    rerun_dependencies: bool = True,
    recovery_source_commit: str | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.expanduser().resolve(strict=True)
    if artifact_ref != "CANDIDATE_TREE" and GIT_SHA_RE.fullmatch(artifact_ref) is None:
        raise ProductionAcceptanceError("artifact_ref_invalid")
    config_file = config_path if config_path.is_absolute() else database_dir / config_path
    config = load_json_strict(config_file, "production_config")
    validate_config(config)
    version = safe_repo_file(database_dir, "VERSION").read_text(encoding="utf-8").strip()
    if version != config["release"]["version"]:
        raise ProductionAcceptanceError("version_file_mismatch")
    safe_repo_file(database_dir, "docs/PORTABLE_AGENT_MEMORY_V1.md")
    recovery_override = None
    if rerun_dependencies:
        recovery_override = rerun_candidate_dependencies(
            database_dir,
            recovery_source_commit=recovery_source_commit,
        )
    elif recovery_source_commit is not None:
        raise ProductionAcceptanceError("recovery_override_requires_rerun")

    python = sys.executable
    profiles = run_json(
        (
            python,
            "scripts/validate_agent_transport_compatibility.py",
            "--database-dir",
            ".",
            "--artifact-ref",
            artifact_ref,
        ),
        cwd=database_dir,
    )
    security = run_json(
        (python, "scripts/memory_security.py", "audit", "--repo-root", "..", "--json"),
        cwd=database_dir,
    )
    doctor = run_json(
        (python, "scripts/memory.py", "--database-dir", ".", "doctor"),
        cwd=database_dir,
    )
    require_pass(profiles, "profiles")
    require_pass(security, "security")
    if profiles.get("profile_count") != 5 or profiles.get("profile_pass_count") != 5:
        raise ProductionAcceptanceError("five_profile_gate_failure")
    corpus = security.get("corpus")
    if not isinstance(corpus, dict) or (
        corpus.get("instruction_obedience_count") != 0
        or corpus.get("credential_block_rate") != 1.0
        or corpus.get("suspected_value_echo_count") != 0
    ):
        raise ProductionAcceptanceError("security_corpus_gate_failure")
    reports, report_hashes = load_required_reports(
        database_dir,
        config,
        recovery_override=recovery_override,
    )
    metric_summary = validate_report_gates(reports, config)
    writer_summary = validate_writer_and_shims(database_dir, doctor)

    proofs = {
        "Discovery": profiles.get("discovery_object_count") == 1,
        "Read": profiles.get("profile_pass_count") == 5 and doctor.get("record_count") == 198,
        "Retrieval": reports["benchmark"].get("status") == "PASS"
        and reports["performance"].get("status") == "PASS",
        "Mutation": reports["e2e"].get("status") == "PASS"
        and reports["fault"].get("status") == "PASS",
        "Forgetting": reports["benchmark"].get("metrics", {}).get("fama", 0)
        >= config["hard_gates"]["fama_min"]
        and reports["e2e"].get("hard_gates", {}).get("old_fact_invisible") is True,
        "Recovery": reports["recovery"].get("roundtrip", {}).get("status") == "PASS",
    }
    if set(proofs) != set(config["proof_obligations"]) or not all(proofs.values()):
        raise ProductionAcceptanceError("six_proof_gate_failure")

    return {
        "schema_version": REPORT_SCHEMA,
        "status": "PASS",
        "phase": "candidate",
        "production_status": "CANDIDATE_READY_NOT_PUBLISHED",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": version,
        "artifact_ref": artifact_ref,
        "proofs": {key: "PASS" for key in proofs},
        "profiles": {
            "count": profiles["profile_count"],
            "pass_count": profiles["profile_pass_count"],
            "profile_ids": [item["profile_id"] for item in profiles["profiles"]],
            "all_same_identity": profiles["all_profiles_same_identity"],
            "remote_memory_target_tested": False,
        },
        "hard_gates": metric_summary,
        "security": {
            "credential_block_rate": corpus["credential_block_rate"],
            "instruction_obedience_count": corpus["instruction_obedience_count"],
            "suspected_value_echo_count": corpus["suspected_value_echo_count"],
            "workflow_count": security["supply_chain"]["workflow_count"],
            "failed_supply_chain_gates": security["supply_chain"]["failed_gates"],
        },
        "writers_and_shims": writer_summary,
        "report_sha256": report_hashes,
        "publication": {
            "source_repository": config["release"]["source_repository"],
            "source_branch": "main",
            "source_tag": config["release"]["source_tag"],
            "snapshot_repository": config["release"]["snapshot_repository"],
            "required_visibility": SNAPSHOT_REPOSITORY_VISIBILITY,
            "public_safe_asset_only": True,
            "asset_published": False,
            "remote_main_verified": False,
            "final_open_pr_issue_non_main": None,
        },
        "hard_gate_failure_count": 0,
    }


def gh_json(args: Sequence[str], *, cwd: Path) -> Any:
    completed = run_command(("gh", *args), cwd=cwd, timeout=120)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProductionAcceptanceError("github_api_invalid_json") from exc


def validate_repository_hygiene(
    report: Mapping[str, Any],
    *,
    expected_treeish: str,
) -> dict[str, Any]:
    if (
        report.get("status") != "PASS"
        or report.get("mode") != expected_treeish
        or report.get("violations") != []
        or report.get("policy_errors") != []
    ):
        raise ProductionAcceptanceError("repository_hygiene_not_clean")
    baseline_tree = report.get("baseline_tree")
    if not isinstance(baseline_tree, str) or GIT_SHA_RE.fullmatch(baseline_tree) is None:
        raise ProductionAcceptanceError("repository_hygiene_evidence_invalid")
    return {
        "status": "PASS",
        "baseline_tree": baseline_tree,
        "violation_count": 0,
    }


def validate_required_check_runs(
    payload: Mapping[str, Any],
    *,
    accepted_commit: str,
    required_names: Sequence[str],
) -> list[dict[str, Any]]:
    runs = payload.get("check_runs")
    if not isinstance(runs, list):
        raise ProductionAcceptanceError("required_checks_payload_invalid")
    summaries: list[dict[str, Any]] = []
    for name in required_names:
        matches = [
            item
            for item in runs
            if isinstance(item, dict)
            and item.get("name") == name
            and item.get("head_sha") == accepted_commit
            and isinstance(item.get("id"), int)
        ]
        if not matches:
            raise ProductionAcceptanceError(f"required_check_missing_{name}")
        latest = max(matches, key=lambda item: int(item["id"]))
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise ProductionAcceptanceError(f"required_check_not_success_{name}")
        summaries.append(
            {
                "name": name,
                "id": latest["id"],
                "status": "completed",
                "conclusion": "success",
            }
        )
    return summaries


def validate_public_snapshot_result(
    report: Mapping[str, Any],
    *,
    accepted_commit: str,
) -> dict[str, Any]:
    require_pass(report, "public_snapshot")
    canonical = report.get("canonical")
    public_release = report.get("public_release")
    if not isinstance(canonical, dict) or not isinstance(public_release, dict):
        raise ProductionAcceptanceError("public_snapshot_summary_missing")
    record_count = canonical.get("record_count")
    if not isinstance(record_count, int) or record_count <= 0:
        raise ProductionAcceptanceError("public_snapshot_record_count_invalid")
    if (
        report.get("source_commit") != accepted_commit
        or report.get("release_candidate") is not True
        or report.get("all_members_from_source_commit") is not True
        or report.get("commit_file_count") != report.get("file_count")
        or report.get("runtime_file_count") != 0
        or report.get("release_repository") != SNAPSHOT_REPOSITORY
        or report.get("release_visibility") != SNAPSHOT_REPOSITORY_VISIBILITY
    ):
        raise ProductionAcceptanceError("public_snapshot_source_boundary_failure")
    if (
        public_release.get("public_release_safe_record_count") != record_count
        or public_release.get("public_repository_allowed_record_count") != record_count
        or public_release.get("redacted_summary_record_count") != record_count
        or public_release.get("credential_present_record_count") != 0
    ):
        raise ProductionAcceptanceError("public_snapshot_record_boundary_failure")
    return {
        "status": "PASS",
        "source_commit": accepted_commit,
        "file_count": report["file_count"],
        "record_count": record_count,
        "public_release_safe_record_count": record_count,
        "credential_present_record_count": 0,
        "all_members_from_source_commit": True,
    }


def evaluate_published(
    database_dir: Path,
    config_path: Path,
    *,
    artifact_ref: str,
) -> dict[str, Any]:
    if GIT_SHA_RE.fullmatch(artifact_ref) is None:
        raise ProductionAcceptanceError("published_ref_invalid")
    database_dir = database_dir.expanduser().resolve(strict=True)
    config_file = config_path if config_path.is_absolute() else database_dir / config_path
    config = load_json_strict(config_file, "production_config")
    validate_config(config)
    release = config["release"]
    source_repository = str(release["source_repository"])
    snapshot_repository = str(release["snapshot_repository"])
    source_url = f"https://github.com/{source_repository}.git"
    if shutil.which("gh") is None or shutil.which("git") is None:
        raise ProductionAcceptanceError("published_tools_missing")

    with tempfile.TemporaryDirectory(prefix="pam-v1-published-") as temporary:
        root = Path(temporary)
        clone = root / "source"
        clone.mkdir()
        run_command(("git", "init", "--quiet"), cwd=clone)
        history_depth = int(config["publication"]["accepted_history_fetch_depth"])
        run_command(
            ("git", "fetch", "--quiet", f"--depth={history_depth}", source_url, artifact_ref),
            cwd=clone,
        )
        run_command(("git", "checkout", "--quiet", "--detach", "FETCH_HEAD"), cwd=clone)
        observed_ref = run_command(("git", "rev-parse", "HEAD"), cwd=clone).stdout.strip()
        if observed_ref != artifact_ref:
            raise ProductionAcceptanceError("published_fetch_ref_mismatch")
        published_database = clone / "OpenAIDatabase"
        candidate = evaluate_candidate(
            published_database,
            DEFAULT_CONFIG,
            artifact_ref=artifact_ref,
            rerun_dependencies=True,
            recovery_source_commit=artifact_ref,
        )
        hygiene_report = run_json(
            (
                sys.executable,
                "scripts/repository_hygiene_audit.py",
                "--root",
                ".",
                "--tree-ish",
                artifact_ref,
            ),
            cwd=clone,
        )
        hygiene_summary = validate_repository_hygiene(
            hygiene_report,
            expected_treeish=artifact_ref,
        )

        source_commit = gh_json(
            ("api", f"repos/{source_repository}/commits/{release['source_branch']}"),
            cwd=clone,
        )
        if not isinstance(source_commit, dict) or source_commit.get("sha") != artifact_ref:
            raise ProductionAcceptanceError("remote_main_not_accepted_commit")
        required_checks_payload = gh_json(
            (
                "api",
                f"repos/{source_repository}/commits/{artifact_ref}/check-runs?per_page=100",
            ),
            cwd=clone,
        )
        if not isinstance(required_checks_payload, dict):
            raise ProductionAcceptanceError("required_checks_payload_invalid")
        required_checks = validate_required_check_runs(
            required_checks_payload,
            accepted_commit=artifact_ref,
            required_names=config["publication"]["required_check_names"],
        )
        tagged_commit = gh_json(
            ("api", f"repos/{source_repository}/commits/{release['source_tag']}"),
            cwd=clone,
        )
        if not isinstance(tagged_commit, dict) or tagged_commit.get("sha") != artifact_ref:
            raise ProductionAcceptanceError("source_tag_not_accepted_commit")

        snapshot_repo = gh_json(("api", f"repos/{snapshot_repository}"), cwd=clone)
        if (
            not isinstance(snapshot_repo, dict)
            or snapshot_repo.get("visibility") != SNAPSHOT_REPOSITORY_VISIBILITY
            or snapshot_repo.get("private") is not False
        ):
            raise ProductionAcceptanceError("snapshot_repository_not_public")
        release_data = gh_json(
            ("api", f"repos/{snapshot_repository}/releases/tags/{release['source_tag']}"),
            cwd=clone,
        )
        if not isinstance(release_data, dict) or release_data.get("draft") or release_data.get("prerelease"):
            raise ProductionAcceptanceError("snapshot_release_not_final")
        asset_name = str(release["snapshot_asset_template"]).format(accepted_commit=artifact_ref)
        assets = release_data.get("assets")
        matches = [item for item in assets or [] if isinstance(item, dict) and item.get("name") == asset_name]
        if len(matches) != 1:
            raise ProductionAcceptanceError("snapshot_asset_cardinality_mismatch")
        asset_metadata = matches[0]
        asset_dir = root / "assets"
        asset_dir.mkdir()
        run_command(
            (
                "gh",
                "release",
                "download",
                str(release["source_tag"]),
                "--repo",
                snapshot_repository,
                "--pattern",
                asset_name,
                "--dir",
                str(asset_dir),
            ),
            cwd=clone,
            timeout=300,
        )
        asset_path = asset_dir / asset_name
        asset_bytes = asset_path.read_bytes()
        if len(asset_bytes) != asset_metadata.get("size"):
            raise ProductionAcceptanceError("snapshot_asset_size_mismatch")
        snapshot_validation = run_json(
            (
                sys.executable,
                "scripts/memory_snapshot.py",
                "validate",
                "--snapshot",
                str(asset_path),
                "--expected-commit",
                artifact_ref,
            ),
            cwd=published_database,
        )
        public_snapshot = validate_public_snapshot_result(
            snapshot_validation,
            accepted_commit=artifact_ref,
        )

        pulls = gh_json(
            ("api", f"repos/{source_repository}/pulls?state=open&per_page=100"), cwd=clone
        )
        issues = gh_json(
            ("api", f"repos/{source_repository}/issues?state=open&per_page=100"), cwd=clone
        )
        branches = gh_json(
            ("api", f"repos/{source_repository}/branches?per_page=100"), cwd=clone
        )
        if not isinstance(pulls, list) or not isinstance(issues, list) or not isinstance(branches, list):
            raise ProductionAcceptanceError("github_terminal_state_invalid")
        issue_count = sum("pull_request" not in item for item in issues if isinstance(item, dict))
        non_main_count = sum(item.get("name") != "main" for item in branches if isinstance(item, dict))
        if (len(pulls), issue_count, non_main_count) != (0, 0, 0):
            raise ProductionAcceptanceError("github_terminal_state_not_zero")

        candidate["phase"] = "published"
        candidate["production_status"] = "PRODUCTION_ACCEPTED"
        candidate["profiles"]["remote_memory_target_tested"] = True
        candidate["publication"] = {
            "source_repository": source_repository,
            "source_branch": "main",
            "source_tag": release["source_tag"],
            "accepted_commit": artifact_ref,
            "accepted_tree": run_command(("git", "rev-parse", "HEAD^{tree}"), cwd=clone).stdout.strip(),
            "snapshot_repository": snapshot_repository,
            "snapshot_repository_visibility": snapshot_repo["visibility"],
            "public_safe_asset_only": True,
            "public_snapshot": public_snapshot,
            "release_id": release_data.get("id"),
            "release_tag": release_data.get("tag_name"),
            "asset_id": asset_metadata.get("id"),
            "asset_name": asset_name,
            "asset_bytes": len(asset_bytes),
            "asset_sha256": sha256_prefixed(asset_bytes),
            "asset_published": True,
            "remote_main_verified": True,
            "repository_hygiene": hygiene_summary,
            "required_checks": required_checks,
            "final_open_pr_issue_non_main": [0, 0, 0],
            "unsigned_sha256_claim": "integrity_only_not_authenticity",
        }
        return candidate


def write_or_check(report: Mapping[str, Any], path: Path, *, check: bool) -> None:
    expected = canonical_json_bytes(report)
    if check:
        try:
            observed = path.read_bytes()
        except OSError as exc:
            raise ProductionAcceptanceError("acceptance_report_missing") from exc
        if observed != expected:
            raise ProductionAcceptanceError("acceptance_report_drift")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_bytes(expected)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--phase", choices=("candidate", "published"), required=True)
    parser.add_argument("--artifact-ref", default="CANDIDATE_TREE")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--reuse-current-reports",
        action="store_true",
        help="Skip dependency reruns only when the same CI job already ran every required check.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        database_dir = args.database_dir.expanduser().resolve(strict=True)
        if args.phase == "candidate":
            report = evaluate_candidate(
                database_dir,
                args.config,
                artifact_ref=args.artifact_ref,
                rerun_dependencies=not args.reuse_current_reports,
            )
            config_file = args.config if args.config.is_absolute() else database_dir / args.config
            config = load_json_strict(config_file, "production_config")
            report_path = args.report or database_dir / str(config["candidate_report"])
        else:
            report = evaluate_published(
                database_dir,
                args.config,
                artifact_ref=args.artifact_ref,
            )
            if args.report is None:
                raise ProductionAcceptanceError("published_report_path_required")
            report_path = args.report
        write_or_check(report, report_path, check=args.check)
        print(canonical_json_bytes(report).decode("utf-8"), end="")
        return 0
    except ProductionAcceptanceError as exc:
        print(
            canonical_json_bytes(
                {
                    "schema_version": REPORT_SCHEMA,
                    "status": "FAIL_CLOSED",
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "reason": str(exc),
                }
            ).decode("utf-8"),
            end="",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
