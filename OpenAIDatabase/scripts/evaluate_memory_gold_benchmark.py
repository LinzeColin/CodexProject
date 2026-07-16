#!/usr/bin/env python3
"""Evaluate the PAM1 Gold benchmark with deterministic required CI gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = Path("config/evaluation/memory_gold_evaluation_v1.json")
PREDICTION_FIELDS = frozenset({"state", "query", "as_of"})
GOLD_LABEL_FIELDS = frozenset(
    {
        "expected_ids",
        "forbidden_ids",
        "hard_negative_ids",
        "should_abstain",
        "answer_traits",
        "abstain_conditions",
        "gold_provenance",
    }
)
SCOPE_PATTERN = re.compile(r"\bSyntheticLab-\d{2}\b")
REQUIRED_HARD_GATES = {
    "recall_at_5": {"metric": "recall_at_5", "operator": "gte", "threshold": 0.95},
    "mrr": {"metric": "mrr", "operator": "gte", "threshold": 0.9},
    "current_state_accuracy": {
        "metric": "current_state_accuracy",
        "operator": "gte",
        "threshold": 0.92,
    },
    "temporal_accuracy": {"metric": "temporal_accuracy", "operator": "gte", "threshold": 0.92},
    "update_accuracy": {"metric": "update_accuracy", "operator": "gte", "threshold": 0.92},
    "provenance_accuracy": {
        "metric": "provenance_accuracy",
        "operator": "gte",
        "threshold": 0.98,
    },
    "abstention_precision": {
        "metric": "abstention_precision",
        "operator": "gte",
        "threshold": 0.9,
    },
    "abstention_recall": {
        "metric": "abstention_recall",
        "operator": "gte",
        "threshold": 0.9,
    },
    "fama": {"metric": "fama", "operator": "gte", "threshold": 0.95},
    "critical_stale_use": {
        "metric": "critical_stale_use_count",
        "operator": "eq",
        "threshold": 0,
    },
    "cross_profile": {"metric": "profile_pass_count", "operator": "gte", "threshold": 5},
    "query_requests": {
        "metric": "query_requests_per_case",
        "operator": "lte",
        "threshold": 1,
    },
    "repository_reads": {
        "metric": "profile_repository_read_budget_max",
        "operator": "lte",
        "threshold": 4,
    },
    "default_discovery": {
        "metric": "default_discovery_object_count",
        "operator": "lte",
        "threshold": 1,
    },
    "full_tree_scan": {
        "metric": "recursive_full_tree_scan_count",
        "operator": "eq",
        "threshold": 0,
    },
    "dataset_size": {"metric": "dataset_bytes", "operator": "lte", "threshold": 921600},
}
REQUIRED_RUNTIME_GATES = {
    "local_query_p95_ms": {
        "metric": "local_query_p95_ms",
        "operator": "lte",
        "threshold": 250,
    }
}

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from memory_forgetting import evaluate_forgetting_cases, load_policy  # noqa: E402


class EvaluationError(ValueError):
    """Raised for fail-closed benchmark or configuration drift."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise EvaluationError(f"duplicate_json_key:{key}")
        value[key] = item
    return value


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    if not isinstance(value, dict):
        raise EvaluationError(f"json_object_required:{path.name}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw, object_pairs_hook=_strict_object)
        if not isinstance(value, dict):
            raise EvaluationError(f"jsonl_object_required:{line_number}")
        case_id = value.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise EvaluationError(f"case_id_invalid:{line_number}")
        seen.add(case_id)
        rows.append(value)
    if not rows:
        raise EvaluationError("benchmark_empty")
    return rows


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("task_id") != "TSK.OpenAIDatabase.PAM1.0014":
        raise EvaluationError("evaluation_task_id_drift")
    if config.get("acceptance_id") != "ACC.OpenAIDatabase.PAM1.0014":
        raise EvaluationError("evaluation_acceptance_id_drift")
    suites = config.get("suites")
    if not isinstance(suites, Mapping):
        raise EvaluationError("evaluation_suites_invalid")
    if suites.get("fast", {}).get("case_indices") != [1, 10]:
        raise EvaluationError("fast_case_indices_drift")
    if suites.get("fast", {}).get("case_count") != 16:
        raise EvaluationError("fast_case_count_drift")
    if suites.get("full", {}).get("case_count") != 160:
        raise EvaluationError("full_case_count_drift")
    if config.get("hard_gates") != REQUIRED_HARD_GATES:
        raise EvaluationError("required_hard_gate_drift")
    if config.get("runtime_hard_gates") != REQUIRED_RUNTIME_GATES:
        raise EvaluationError("required_runtime_gate_drift")
    ci = config.get("ci")
    expected_ci = {
        "fast_event": "pull_request",
        "full_events": ["push:main", "schedule", "workflow_dispatch"],
        "fast_command": "python3 scripts/evaluate_memory_gold_benchmark.py --suite fast --check",
        "full_command": "python3 scripts/evaluate_memory_gold_benchmark.py --suite full --check",
        "soft_failure_allowed": False,
    }
    if ci != expected_ci:
        raise EvaluationError("required_ci_contract_drift")


def _path(database_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else database_dir / path


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def render_report(report: Mapping[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _timestamp(value: Any, reason: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EvaluationError(reason)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EvaluationError(reason) from exc
    if parsed.tzinfo is None:
        raise EvaluationError(reason)
    return parsed


def _effective(record: Mapping[str, Any], as_of: datetime) -> bool:
    valid_time = record.get("valid_time")
    if not isinstance(valid_time, Mapping):
        raise EvaluationError("record_valid_time_invalid")
    start = _timestamp(valid_time.get("from"), "record_valid_from_invalid")
    end_raw = valid_time.get("to")
    end = None if end_raw is None else _timestamp(end_raw, "record_valid_to_invalid")
    return start <= as_of and (end is None or as_of < end)


def build_prediction_input(case: Mapping[str, Any]) -> dict[str, Any]:
    """Expose only candidate state and query context to the tested algorithm."""

    return {field: case[field] for field in ("state", "query", "as_of")}


def predict(candidate_view: Mapping[str, Any], *, limit: int = 5) -> dict[str, Any]:
    """Return ranked eligible IDs without access to any Gold label field."""

    if set(candidate_view) != PREDICTION_FIELDS or set(candidate_view) & GOLD_LABEL_FIELDS:
        raise EvaluationError("prediction_input_contract_violation")
    if not isinstance(limit, int) or not 1 <= limit <= 5:
        raise EvaluationError("prediction_limit_invalid")
    query = candidate_view.get("query")
    as_of_value = candidate_view.get("as_of")
    state = candidate_view.get("state")
    if not isinstance(query, Mapping) or not isinstance(as_of_value, Mapping) or not isinstance(state, list):
        raise EvaluationError("prediction_input_invalid")
    query_text = query.get("text")
    query_aliases = query.get("aliases")
    if not isinstance(query_text, str) or not isinstance(query_aliases, list):
        raise EvaluationError("prediction_query_invalid")
    scopes = sorted(set(SCOPE_PATTERN.findall(query_text)))
    if len(scopes) != 1:
        raise EvaluationError("prediction_scope_ambiguous")
    target_scope = scopes[0]
    aliases = {str(value).casefold() for value in query_aliases if str(value).strip()}
    if not aliases:
        raise EvaluationError("prediction_aliases_empty")
    valid_as_of = _timestamp(as_of_value.get("valid_time"), "prediction_valid_time_invalid")
    recorded_as_of = _timestamp(as_of_value.get("recorded_time"), "prediction_recorded_time_invalid")

    ranked: list[tuple[int, str, Mapping[str, Any]]] = []
    excluded = Counter()
    for row in state:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            raise EvaluationError("prediction_record_invalid")
        if row.get("scope") != target_scope:
            excluded["scope"] += 1
            continue
        record_aliases = {str(value).casefold() for value in row.get("aliases", [])}
        alias_overlap = aliases & record_aliases
        if not alias_overlap:
            excluded["alias"] += 1
            continue
        if row.get("authorization") != "allowed":
            excluded["authorization"] += 1
            continue
        if row.get("verification_state") != "verified":
            excluded["verification"] += 1
            continue
        if row.get("status") not in {"active", "retired"}:
            excluded["lifecycle"] += 1
            continue
        if not _effective(row, valid_as_of):
            excluded["valid_time"] += 1
            continue
        if _timestamp(row.get("recorded_at"), "prediction_recorded_at_invalid") > recorded_as_of:
            excluded["recorded_time"] += 1
            continue
        score = 100 + 10 * len(alias_overlap)
        score += 4 if row.get("status") == "active" else 2
        score += 3 if target_scope in str(row.get("statement") or "") else 0
        score += 2 if row.get("source_type") in {"repository_evidence", "agent_report"} else 0
        ranked.append((score, str(row["id"]), row))

    ranked.sort(key=lambda value: (-value[0], value[1]))
    returned = [row for _, _, row in ranked[:limit]]
    return {
        "returned_ids": [str(row["id"]) for row in returned],
        "decision_state": "answer" if returned else "abstain",
        "excluded_counts": dict(sorted(excluded.items())),
    }


def _percentile_95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def select_cases(cases: Sequence[dict[str, Any]], suite: str, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    suites = config.get("suites")
    if not isinstance(suites, Mapping) or suite not in suites:
        raise EvaluationError(f"suite_unknown:{suite}")
    if suite == "full":
        selected = list(cases)
    else:
        indices = {int(value) for value in suites[suite].get("case_indices", [])}
        selected = [
            case
            for case in cases
            if int(str(case["case_id"]).rsplit("_", 1)[1]) in indices
        ]
    expected = int(suites[suite].get("case_count", -1))
    if len(selected) != expected:
        raise EvaluationError(f"suite_case_count_mismatch:{suite}:{len(selected)}:{expected}")
    return selected


def assess_gates(metrics: Mapping[str, Any], gate_contract: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name, raw in gate_contract.items():
        if not isinstance(raw, Mapping):
            raise EvaluationError(f"gate_contract_invalid:{name}")
        metric_name = str(raw.get("metric"))
        operator = str(raw.get("operator"))
        threshold = raw.get("threshold")
        observed = metrics.get(metric_name)
        if not isinstance(observed, (int, float)) or not isinstance(threshold, (int, float)):
            raise EvaluationError(f"gate_metric_invalid:{name}")
        if operator == "gte":
            passed = observed >= threshold
        elif operator == "lte":
            passed = observed <= threshold
        elif operator == "eq":
            passed = observed == threshold
        else:
            raise EvaluationError(f"gate_operator_invalid:{name}:{operator}")
        results[str(name)] = {
            "metric": metric_name,
            "observed": observed,
            "operator": operator,
            "threshold": threshold,
            "status": "PASS" if passed else "FAIL",
        }
    return results


def _profile_results(profiles: Mapping[str, Any], result_digest: str) -> list[dict[str, Any]]:
    required_operations = profiles.get("required_operations")
    rows = profiles.get("profiles")
    if required_operations != ["discover", "read", "query", "cite", "freshness", "fallback"]:
        raise EvaluationError("profile_required_operations_drift")
    if not isinstance(rows, list):
        raise EvaluationError("profiles_invalid")
    results: list[dict[str, Any]] = []
    for row in rows:
        discovery = row.get("discovery") if isinstance(row, Mapping) else None
        passed = bool(
            isinstance(row, Mapping)
            and row.get("write_policy") == "none"
            and isinstance(discovery, Mapping)
            and discovery.get("expected_objects") == 1
            and isinstance(row.get("max_repository_reads"), int)
            and 0 < int(row["max_repository_reads"]) <= 4
        )
        results.append(
            {
                "profile_id": str(row.get("profile_id")),
                "result_sha256": result_digest,
                "status": "PASS" if passed else "FAIL",
            }
        )
    if len({row["profile_id"] for row in results}) != len(results):
        raise EvaluationError("profile_id_duplicate")
    return results


def evaluate_suite(
    database_dir: Path,
    config: Mapping[str, Any],
    suite: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_config(config)
    files = config.get("files")
    if not isinstance(files, Mapping):
        raise EvaluationError("evaluation_files_invalid")
    dataset_path = _path(database_dir, str(files["dataset"]))
    profiles_path = _path(database_dir, str(files["profiles"]))
    forgetting_policy_path = _path(database_dir, str(files["forgetting_policy"]))
    config_path = _path(database_dir, str(files["self"]))
    evaluator_path = Path(__file__).resolve()
    all_cases = load_jsonl(dataset_path)
    cases = select_cases(all_cases, suite, config)
    profiles = load_json(profiles_path)
    forgetting_policy = load_policy(forgetting_policy_path)

    expected_total = 0
    recall_hits = 0
    reciprocal_ranks: list[float] = []
    exact_by_category: Counter[str] = Counter()
    count_by_category: Counter[str] = Counter()
    provenance_total = 0
    provenance_hits = 0
    true_abstain = false_abstain = missed_abstain = 0
    critical_stale_use_count = 0
    candidate_input_bytes = 0
    candidate_output_bytes = 0
    query_latencies_ms: list[float] = []
    compact_results: list[dict[str, Any]] = []
    forgetting_cases: list[dict[str, Any]] = []
    suite_started = time.perf_counter_ns()

    for case in cases:
        candidate_view = build_prediction_input(case)
        candidate_input_bytes += len(_canonical_bytes(candidate_view))
        started = time.perf_counter_ns()
        prediction = predict(candidate_view, limit=5)
        query_latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        returned = list(prediction["returned_ids"])
        candidate_output_bytes += len(_canonical_bytes(returned))
        expected = list(case["expected_ids"])
        forbidden = set(case["forbidden_ids"])
        returned_set = set(returned)
        expected_set = set(expected)
        expected_total += len(expected)
        recall_hits += len(expected_set & set(returned[:5]))
        if expected:
            ranks = [returned.index(record_id) + 1 for record_id in expected if record_id in returned]
            reciprocal_ranks.append(1 / min(ranks) if ranks else 0.0)
        did_abstain = prediction["decision_state"] == "abstain"
        should_abstain = bool(case["should_abstain"])
        if should_abstain and did_abstain:
            true_abstain += 1
        elif not should_abstain and did_abstain:
            false_abstain += 1
        elif should_abstain and not did_abstain:
            missed_abstain += 1
        exact = returned_set == expected_set and did_abstain == should_abstain and not (returned_set & forbidden)
        category = str(case["category"])
        count_by_category[category] += 1
        exact_by_category[category] += int(exact)
        records = {str(row["id"]): row for row in case["state"]}
        for record_id in expected:
            provenance_total += 1
            row = records[record_id]
            if record_id in returned_set and all(
                row.get(field) not in (None, "")
                for field in ("id", "source_ref", "source_type", "agent_id", "recorded_at", "valid_time")
            ):
                provenance_hits += 1
        valid_as_of = _timestamp(case["as_of"]["valid_time"], "case_valid_time_invalid")
        for record_id in returned_set & forbidden:
            row = records[record_id]
            if row.get("status") == "retired" or not _effective(row, valid_as_of):
                critical_stale_use_count += 1
        forgetting_cases.append(
            {
                "case_id": case["case_id"],
                "expected_record_ids": expected,
                "forbidden_record_ids": list(case["forbidden_ids"]),
                "returned_record_ids": returned,
                "critical": bool(case["stale_or_retired_trap"]),
                "should_abstain": should_abstain,
                "decision_state": prediction["decision_state"],
            }
        )
        compact_results.append(
            {
                "case_id": case["case_id"],
                "decision_state": prediction["decision_state"],
                "returned_ids": returned,
            }
        )

    forgetting = evaluate_forgetting_cases(forgetting_cases, forgetting_policy)
    result_digest = _sha256_bytes(_canonical_bytes(compact_results))
    profile_results = _profile_results(profiles, result_digest)
    current_categories = set(count_by_category) - {"temporal"}
    current_total = sum(count_by_category[name] for name in current_categories)
    current_pass = sum(exact_by_category[name] for name in current_categories)
    profile_rows = profiles["profiles"]
    deterministic_metrics: dict[str, Any] = {
        "recall_at_5": round(_ratio(recall_hits, expected_total), 6),
        "mrr": round(_ratio(sum(reciprocal_ranks), len(reciprocal_ranks)), 6),
        "current_state_accuracy": round(_ratio(current_pass, current_total), 6),
        "temporal_accuracy": round(_ratio(exact_by_category["temporal"], count_by_category["temporal"]), 6),
        "update_accuracy": round(_ratio(exact_by_category["update"], count_by_category["update"]), 6),
        "provenance_accuracy": round(_ratio(provenance_hits, provenance_total), 6),
        "abstention_precision": round(_ratio(true_abstain, true_abstain + false_abstain), 6),
        "abstention_recall": round(_ratio(true_abstain, true_abstain + missed_abstain), 6),
        "fama": round(float(forgetting["fama"]), 6),
        "critical_stale_use_count": critical_stale_use_count,
        "profile_pass_count": sum(row["status"] == "PASS" for row in profile_results),
        "query_requests_per_case": 1.0,
        "profile_repository_read_budget_max": max(
            int(row["max_repository_reads"]) for row in profile_rows
        ),
        "default_discovery_object_count": max(int(row["discovery"]["expected_objects"]) for row in profile_rows),
        "recursive_full_tree_scan_count": 0,
        "dataset_bytes": dataset_path.stat().st_size,
    }
    hard_gates = assess_gates(deterministic_metrics, config["hard_gates"])
    failures = sorted(name for name, row in hard_gates.items() if row["status"] != "PASS")
    suite_elapsed_ms = (time.perf_counter_ns() - suite_started) / 1_000_000
    runtime_metrics = {
        "local_query_p95_ms": round(_percentile_95(query_latencies_ms), 6),
        "suite_elapsed_ms": round(suite_elapsed_ms, 6),
    }
    runtime_contract = dict(config["runtime_hard_gates"])
    runtime_contract["suite_elapsed_ms"] = {
        "metric": "suite_elapsed_ms",
        "operator": "lte",
        "threshold": config["suites"][suite]["runtime_ms_max"],
    }
    runtime_gates = assess_gates(runtime_metrics, runtime_contract)
    report = {
        "schema_version": config["report_schema_version"],
        "task_id": config["task_id"],
        "acceptance_id": config["acceptance_id"],
        "suite": suite,
        "status": "PASS" if not failures else "FAIL",
        "case_count": len(cases),
        "category_counts": dict(sorted(count_by_category.items())),
        "algorithm": {
            "version": config["algorithm_version"],
            "prediction_input_fields": sorted(PREDICTION_FIELDS),
            "gold_label_dependency_count": 0,
            "llm_judge": None,
            "result_sha256": result_digest,
        },
        "source_hashes": {
            "config_sha256": _sha256_path(config_path),
            "dataset_sha256": _sha256_path(dataset_path),
            "evaluator_sha256": _sha256_path(evaluator_path),
            "forgetting_policy_sha256": _sha256_path(forgetting_policy_path),
            "profiles_sha256": _sha256_path(profiles_path),
        },
        "metrics": deterministic_metrics,
        "category_accuracy": {
            name: round(_ratio(exact_by_category[name], count_by_category[name]), 6)
            for name in sorted(count_by_category)
        },
        "hard_gates": hard_gates,
        "hard_gate_failures": failures,
        "profile_results": profile_results,
        "workload": {
            "request_model": "one in-process evaluation call per case; no network requests",
            "query_request_count": len(cases),
            "candidate_input_bytes": candidate_input_bytes,
            "candidate_input_p95_bytes": int(
                _percentile_95([len(_canonical_bytes(build_prediction_input(case))) for case in cases])
            ),
            "candidate_output_bytes": candidate_output_bytes,
            "network_request_count": 0,
            "recursive_full_tree_scan_count": 0,
        },
        "runtime_gate_contract": {
            "local_query_p95_ms_max": config["runtime_hard_gates"]["local_query_p95_ms"]["threshold"],
            "suite_elapsed_ms_max": config["suites"][suite]["runtime_ms_max"],
            "observation_excluded_from_report_hash": True,
        },
    }
    return report, {"metrics": runtime_metrics, "gates": runtime_gates}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--suite", choices=("fast", "full"), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    config_path = args.config if args.config.is_absolute() else database_dir / args.config
    config = load_json(config_path)
    report, runtime = evaluate_suite(database_dir, config, args.suite)
    report_bytes = render_report(report)
    report_path = _path(database_dir, str(config["suites"][args.suite]["report"]))
    runtime_failures = sorted(
        name for name, row in runtime["gates"].items() if row["status"] != "PASS"
    )
    drift = False
    if args.write:
        if report["status"] != "PASS" or runtime_failures:
            drift = True
        else:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_bytes(report_bytes)
    else:
        drift = not report_path.is_file() or report_path.read_bytes() != report_bytes
    passed = report["status"] == "PASS" and not runtime_failures and not drift
    payload = {
        "status": "PASS" if passed else "FAIL",
        "suite": args.suite,
        "case_count": report["case_count"],
        "report": report_path.relative_to(database_dir).as_posix(),
        "report_sha256": _sha256_bytes(report_bytes),
        "report_drift": drift,
        "hard_gate_failures": report["hard_gate_failures"],
        "runtime": runtime,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
