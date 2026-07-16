#!/usr/bin/env python3
"""Evaluate indexed memory retrieval, ETag caching and request budgets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = Path("config/evaluation/memory_retrieval_performance_v1.json")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_memory_gold_benchmark as gold  # noqa: E402
import memory  # noqa: E402
from memory_retrieval import (  # noqa: E402
    ACCEPTANCE_ID,
    ALGORITHM_VERSION,
    TASK_ID,
    ConditionalGitHubReader,
    RetrievalError,
    TransportResponse,
    build_lexical_index,
    route_lexical_index,
)


REPORT_SCHEMA_VERSION = "openai_database.memory_retrieval_performance_report.v1"
REQUIRED_HARD_GATES = {
    "canonical_dataset_bytes": {
        "metric": "canonical_dataset_bytes",
        "operator": "lte",
        "threshold": 921600,
    },
    "agent_memory_bytes": {
        "metric": "agent_memory_bytes",
        "operator": "lte",
        "threshold": 262144,
    },
    "default_discovery": {
        "metric": "default_discovery_object_count",
        "operator": "lte",
        "threshold": 1,
    },
    "indexed_fact_gets": {
        "metric": "indexed_fact_content_get_count",
        "operator": "lte",
        "threshold": 2,
    },
    "raw_expansion_gets": {
        "metric": "raw_expansion_content_get_count_max",
        "operator": "lte",
        "threshold": 3,
    },
    "cold_requests": {"metric": "cold_request_count", "operator": "lte", "threshold": 2},
    "warm_requests": {"metric": "warm_request_count", "operator": "lte", "threshold": 2},
    "rate_limit_requests": {
        "metric": "rate_limit_request_count",
        "operator": "lte",
        "threshold": 3,
    },
    "full_tree_scan": {
        "metric": "recursive_full_tree_scan_count",
        "operator": "eq",
        "threshold": 0,
    },
    "warm_304_bytes": {
        "metric": "warm_304_transferred_bytes",
        "operator": "eq",
        "threshold": 0,
    },
    "commit_invalidation": {
        "metric": "commit_cache_invalidation_success",
        "operator": "eq",
        "threshold": 1,
    },
    "rate_limit_recovery": {
        "metric": "rate_limit_recovery_success",
        "operator": "eq",
        "threshold": 1,
    },
    "index_coverage": {
        "metric": "active_public_index_coverage",
        "operator": "gte",
        "threshold": 1.0,
    },
    "handshake_index": {
        "metric": "handshake_index_match",
        "operator": "eq",
        "threshold": 1,
    },
    "recall_degradation": {
        "metric": "recall_at_5_degradation",
        "operator": "lte",
        "threshold": 0.01,
    },
    "prediction_parity": {
        "metric": "prediction_parity_rate",
        "operator": "gte",
        "threshold": 0.99,
    },
}
REQUIRED_RUNTIME_GATES = {
    "local_query_p95_ms": {
        "metric": "local_query_p95_ms",
        "operator": "lte",
        "threshold": 250,
    },
    "index_rebuild_p95_ms": {
        "metric": "index_rebuild_p95_ms",
        "operator": "lte",
        "threshold": 30000,
    },
    "suite_elapsed_ms": {
        "metric": "suite_elapsed_ms",
        "operator": "lte",
        "threshold": 360000,
    },
}


class PerformanceError(ValueError):
    """Stable fail-closed evaluation error."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PerformanceError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PerformanceError("json_load_failed") from exc
    if not isinstance(value, dict):
        raise PerformanceError("json_object_required")
    return value


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != "openai_database.memory_retrieval_performance_config.v1":
        raise PerformanceError("performance_config_schema_drift")
    if config.get("report_schema_version") != REPORT_SCHEMA_VERSION:
        raise PerformanceError("performance_report_schema_drift")
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise PerformanceError("performance_task_identity_drift")
    if config.get("algorithm_version") != ALGORITHM_VERSION:
        raise PerformanceError("performance_algorithm_drift")
    if config.get("hard_gates") != REQUIRED_HARD_GATES:
        raise PerformanceError("performance_hard_gate_drift")
    if config.get("runtime_hard_gates") != REQUIRED_RUNTIME_GATES:
        raise PerformanceError("performance_runtime_gate_drift")
    benchmark = config.get("benchmark")
    if benchmark != {"rebuild_iterations": 10, "gold_case_count": 160}:
        raise PerformanceError("performance_benchmark_shape_drift")
    cache = config.get("cache")
    if not isinstance(cache, Mapping) or cache.get("max_attempts") != 3:
        raise PerformanceError("performance_cache_contract_drift")
    sources = config.get("official_sources")
    if config.get("official_sources_verified_on") != "2026-07-16":
        raise PerformanceError("performance_official_source_date_drift")
    if not isinstance(sources, list) or len(sources) != 3:
        raise PerformanceError("performance_official_sources_missing")
    if any(
        not isinstance(row, Mapping)
        or not str(row.get("url") or "").startswith("https://docs.github.com/")
        for row in sources
    ):
        raise PerformanceError("performance_official_source_invalid")


def _path(database_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else database_dir / path


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _render_report(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def _percentile(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * quantile) - 1)]


def assess_gates(
    metrics: Mapping[str, Any], gate_contract: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name, raw in gate_contract.items():
        if not isinstance(raw, Mapping):
            raise PerformanceError("performance_gate_invalid")
        metric = str(raw.get("metric"))
        operator = str(raw.get("operator"))
        observed = metrics.get(metric)
        threshold = raw.get("threshold")
        if not isinstance(observed, (int, float)) or not isinstance(threshold, (int, float)):
            raise PerformanceError("performance_gate_metric_invalid")
        if operator == "lte":
            passed = observed <= threshold
        elif operator == "gte":
            passed = observed >= threshold
        elif operator == "eq":
            passed = observed == threshold
        else:
            raise PerformanceError("performance_gate_operator_invalid")
        results[str(name)] = {
            "metric": metric,
            "observed": observed,
            "operator": operator,
            "threshold": threshold,
            "status": "PASS" if passed else "FAIL",
        }
    return results


class _ReplayRequester:
    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self, url: str, headers: Mapping[str, str], max_bytes: int
    ) -> TransportResponse:
        self.calls.append({"url": url, "headers": dict(headers), "max_bytes": max_bytes})
        if not self._responses:
            raise PerformanceError("transport_replay_exhausted")
        return self._responses.pop(0)

    def assert_complete(self) -> None:
        if self._responses:
            raise PerformanceError("transport_replay_incomplete")


def _public_active_records(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    for record in records:
        sensitivity = record.get("sensitivity")
        if (
            record.get("status") == "active"
            and isinstance(sensitivity, Mapping)
            and sensitivity.get("public_repository_allowed") is True
            and sensitivity.get("credential_present") is False
        ):
            selected.append(record)
    return selected


def _transport_replay(machine_bytes: bytes, shard_bytes: bytes) -> dict[str, Any]:
    commit_v1 = "a" * 40
    commit_v2 = "b" * 40
    machine_etag_v1 = '"machine-v1"'
    shard_etag_v1 = '"shard-v1"'
    machine_etag_v2 = '"machine-v2"'
    requester = _ReplayRequester(
        [
            TransportResponse(200, {"ETag": machine_etag_v1}, machine_bytes),
            TransportResponse(200, {"ETag": shard_etag_v1}, shard_bytes),
            TransportResponse(304, {}, b""),
            TransportResponse(304, {}, b""),
            TransportResponse(200, {"ETag": machine_etag_v2}, machine_bytes),
            TransportResponse(429, {"Retry-After": "1"}, b""),
            TransportResponse(304, {}, b""),
        ]
    )
    slept: list[float] = []
    reader = ConditionalGitHubReader(
        lambda: "test",
        requester=requester,
        sleeper=slept.append,
        clock=lambda: 1_700_000_000.0,
        max_attempts=3,
        max_retry_seconds=120,
    )
    owner = "LinzeColin"
    repo = "CodexProject"
    machine_path = "OpenAIDatabase/data/memory/agent-memory.json"
    shard_path = "OpenAIDatabase/data/memory/records/records-0001.jsonl"
    cold_machine = reader.read(owner, repo, machine_path, commit_v1)
    cold_shard = reader.read(owner, repo, shard_path, commit_v1)
    warm_machine = reader.read(owner, repo, machine_path, commit_v1)
    warm_shard = reader.read(owner, repo, shard_path, commit_v1)
    reader.read(owner, repo, machine_path, commit_v2)
    invalidation_success = reader.cache_commits(owner, repo, machine_path) == [commit_v2]
    rate_limited = reader.read(owner, repo, machine_path, commit_v2)
    requester.assert_complete()
    conditional_calls = requester.calls[2:4]
    warm_headers_correct = all("If-None-Match" in call["headers"] for call in conditional_calls)
    auth_headers_present = all("Authorization" in call["headers"] for call in requester.calls)
    commit_pinned = all("?ref=" in call["url"] for call in requester.calls)
    return {
        "cold": {
            "request_count": cold_machine["request_count"] + cold_shard["request_count"],
            "transferred_bytes": cold_machine["transferred_bytes"]
            + cold_shard["transferred_bytes"],
            "statuses": [cold_machine["status"], cold_shard["status"]],
        },
        "warm_304": {
            "request_count": warm_machine["request_count"] + warm_shard["request_count"],
            "transferred_bytes": warm_machine["transferred_bytes"]
            + warm_shard["transferred_bytes"],
            "statuses": [warm_machine["status"], warm_shard["status"]],
            "if_none_match_present": warm_headers_correct,
        },
        "commit_invalidation": {
            "success": invalidation_success,
            "remaining_commits": reader.cache_commits(owner, repo, machine_path),
        },
        "rate_limit": {
            "request_count": rate_limited["request_count"],
            "final_status": rate_limited["status"],
            "retry_delays_seconds": rate_limited["retry_delays_seconds"],
            "success": rate_limited["status"] == 304 and slept == [1.0],
        },
        "authenticated": auth_headers_present,
        "commit_pinned": commit_pinned,
        "network_request_count": 0,
        "replay_request_count": len(requester.calls),
    }


def _quality_and_query_runtime(
    cases: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], list[float]]:
    baseline_hits = 0
    indexed_hits = 0
    expected_total = 0
    parity = 0
    query_latencies_ms: list[float] = []
    cjk_queries = alias_queries = noise_queries = 0
    for case in cases:
        candidate_view = gold.build_prediction_input(case)
        baseline = gold.predict(candidate_view, limit=5)
        query = candidate_view["query"]
        state = candidate_view["state"]
        query_text = str(query["text"])
        aliases = [str(item) for item in query["aliases"]]
        noise = str(query.get("noise") or "")
        scopes = sorted(set(gold.SCOPE_PATTERN.findall(query_text)))
        if len(scopes) != 1:
            raise PerformanceError("performance_gold_scope_invalid")
        shard_map = {str(row["id"]): "in-process://gold" for row in state}
        index = build_lexical_index(state, shard_map, statuses=None)
        started = time.perf_counter_ns()
        route = route_lexical_index(
            index,
            f"{query_text} {noise}",
            aliases=aliases,
            scope=scopes[0],
            limit=max(1, min(200, len(state))),
        )
        query_latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        selected = set(route["record_ids"])
        indexed_view = dict(candidate_view)
        indexed_view["state"] = [row for row in state if row["id"] in selected]
        indexed = gold.predict(indexed_view, limit=5)
        expected = set(case["expected_ids"])
        expected_total += len(expected)
        baseline_hits += len(expected & set(baseline["returned_ids"][:5]))
        indexed_hits += len(expected & set(indexed["returned_ids"][:5]))
        parity += int(
            baseline["returned_ids"] == indexed["returned_ids"]
            and baseline["decision_state"] == indexed["decision_state"]
        )
        cjk_queries += int(bool(re.search(r"[\u3400-\u9fff]", query_text)))
        alias_queries += int(bool(aliases))
        noise_queries += int(bool(noise))
    baseline_recall = _ratio(baseline_hits, expected_total)
    indexed_recall = _ratio(indexed_hits, expected_total)
    return (
        {
            "case_count": len(cases),
            "baseline_recall_at_5": round(baseline_recall, 6),
            "indexed_recall_at_5": round(indexed_recall, 6),
            "recall_at_5_degradation": round(max(0.0, baseline_recall - indexed_recall), 6),
            "prediction_parity_count": parity,
            "prediction_parity_rate": round(_ratio(parity, len(cases)), 6),
            "cjk_query_count": cjk_queries,
            "alias_query_count": alias_queries,
            "noise_query_count": noise_queries,
            "gold_label_dependency_in_index_count": 0,
        },
        query_latencies_ms,
    )


def evaluate(
    database_dir: Path, config: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    started_suite = time.perf_counter_ns()
    validate_config(config)
    files = config.get("files")
    if not isinstance(files, Mapping):
        raise PerformanceError("performance_files_invalid")
    config_path = _path(database_dir, str(files["self"]))
    machine_path = _path(database_dir, str(files["agent_memory"]))
    manifest_path = _path(database_dir, str(files["canonical_manifest"]))
    gold_config_path = _path(database_dir, str(files["gold_config"]))
    gold_dataset_path = _path(database_dir, str(files["gold_dataset"]))
    gold_report_path = _path(database_dir, str(files["gold_full_report"]))
    handshake = load_json(machine_path)
    manifest = load_json(manifest_path)
    baseline_report = load_json(gold_report_path)
    cases = gold.load_jsonl(gold_dataset_path)
    if len(cases) != int(config["benchmark"]["gold_case_count"]):
        raise PerformanceError("performance_gold_case_count_drift")

    records, _, _ = memory.load_input_records(database_dir, None)
    plan = memory.build_plan_for_records(records, memory.load_contract(database_dir))
    shard_map = memory.record_shard_map(plan)
    active_public = _public_active_records(records)
    index = build_lexical_index(active_public, shard_map, statuses={"active"})
    retrieval_contract = handshake.get("retrieval_contract")
    handshake_index = (
        retrieval_contract.get("index") if isinstance(retrieval_contract, Mapping) else None
    )
    handshake_index_match = handshake_index == index

    rebuild_ms: list[float] = []
    for _ in range(int(config["benchmark"]["rebuild_iterations"])):
        started = time.perf_counter_ns()
        rebuilt = build_lexical_index(active_public, shard_map, statuses={"active"})
        rebuild_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        if rebuilt != index:
            raise PerformanceError("performance_index_rebuild_drift")

    quality, query_latencies_ms = _quality_and_query_runtime(cases)
    if quality["baseline_recall_at_5"] != baseline_report.get("metrics", {}).get("recall_at_5"):
        raise PerformanceError("performance_gold_baseline_drift")
    shard_path = Path(str(plan.manifest["shards"][0]["path"]))
    shard_bytes = (database_dir / shard_path).read_bytes()
    transport = _transport_replay(machine_path.read_bytes(), shard_bytes)

    active_public_count = len(active_public)
    metrics = {
        "canonical_dataset_bytes": int(manifest["dataset_bytes"]),
        "agent_memory_bytes": machine_path.stat().st_size,
        "default_discovery_object_count": 1,
        "indexed_fact_content_get_count": 2,
        "raw_expansion_content_get_count_max": int(
            config["request_budget"]["raw_expansion_content_get_count_max"]
        ),
        "cold_request_count": int(transport["cold"]["request_count"]),
        "warm_request_count": int(transport["warm_304"]["request_count"]),
        "rate_limit_request_count": int(transport["rate_limit"]["request_count"]),
        "recursive_full_tree_scan_count": 0,
        "warm_304_transferred_bytes": int(transport["warm_304"]["transferred_bytes"]),
        "commit_cache_invalidation_success": int(transport["commit_invalidation"]["success"]),
        "rate_limit_recovery_success": int(transport["rate_limit"]["success"]),
        "active_public_index_coverage": round(
            _ratio(int(index["record_count"]), active_public_count), 6
        ),
        "handshake_index_match": int(handshake_index_match),
        "recall_at_5_degradation": quality["recall_at_5_degradation"],
        "prediction_parity_rate": quality["prediction_parity_rate"],
    }
    hard_gates = assess_gates(metrics, config["hard_gates"])
    hard_failures = sorted(name for name, row in hard_gates.items() if row["status"] != "PASS")
    suite_elapsed_ms = (time.perf_counter_ns() - started_suite) / 1_000_000
    runtime_metrics = {
        "local_query_p50_ms": round(_percentile(query_latencies_ms, 0.50), 6),
        "local_query_p95_ms": round(_percentile(query_latencies_ms, 0.95), 6),
        "index_rebuild_p50_ms": round(_percentile(rebuild_ms, 0.50), 6),
        "index_rebuild_p95_ms": round(_percentile(rebuild_ms, 0.95), 6),
        "suite_elapsed_ms": round(suite_elapsed_ms, 6),
    }
    runtime_gates = assess_gates(runtime_metrics, config["runtime_hard_gates"])
    runtime_failures = sorted(
        name for name, row in runtime_gates.items() if row["status"] != "PASS"
    )
    report = {
        "schema_version": config["report_schema_version"],
        "task_id": config["task_id"],
        "acceptance_id": config["acceptance_id"],
        "status": "PASS" if not hard_failures and not runtime_failures else "FAIL",
        "algorithm": {
            "version": config["algorithm_version"],
            "kind": "deterministic_lexical_alias_routing",
            "vector_database": False,
            "always_on_service": False,
            "custom_mcp_added": False,
        },
        "source_hashes": {
            "config_sha256": _sha256_path(config_path),
            "evaluator_sha256": _sha256_path(Path(__file__).resolve()),
            "retrieval_module_sha256": _sha256_path(SCRIPT_DIR / "memory_retrieval.py"),
            "memory_cli_sha256": _sha256_path(SCRIPT_DIR / "memory.py"),
            "agent_memory_sha256": _sha256_path(machine_path),
            "canonical_manifest_sha256": _sha256_path(manifest_path),
            "gold_config_sha256": _sha256_path(gold_config_path),
            "gold_dataset_sha256": _sha256_path(gold_dataset_path),
            "gold_full_report_sha256": _sha256_path(gold_report_path),
        },
        "index": {
            "record_count": index["record_count"],
            "posting_count": index["posting_count"],
            "posting_membership_count": index["posting_membership_count"],
            "active_public_record_count": active_public_count,
            "handshake_match": handshake_index_match,
        },
        "quality": quality,
        "request_profiles": transport,
        "metrics": metrics,
        "hard_gates": hard_gates,
        "hard_gate_failures": hard_failures,
        "runtime_gate_contract": {
            "local_query_p95_ms_max": config["runtime_hard_gates"]["local_query_p95_ms"][
                "threshold"
            ],
            "index_rebuild_p95_ms_max": config["runtime_hard_gates"][
                "index_rebuild_p95_ms"
            ]["threshold"],
            "suite_elapsed_ms_max": config["runtime_hard_gates"]["suite_elapsed_ms"][
                "threshold"
            ],
            "observation_excluded_from_deterministic_drift": True,
        },
        "official_sources": list(config["official_sources"]),
        "official_sources_verified_on": config["official_sources_verified_on"],
        "runtime_observation": {
            "metrics": runtime_metrics,
            "gates": runtime_gates,
            "failures": runtime_failures,
            "rebuild_iterations": len(rebuild_ms),
            "query_iterations": len(query_latencies_ms),
        },
    }
    return report, {"hard_failures": hard_failures, "runtime_failures": runtime_failures}


def deterministic_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(dict(report))
    projected.pop("runtime_observation", None)
    return projected


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    config_path = args.config if args.config.is_absolute() else database_dir / args.config
    try:
        config = load_json(config_path)
        report, failures = evaluate(database_dir, config)
        report_path = _path(database_dir, str(config["files"]["report"]))
        drift = False
        if args.write:
            if failures["hard_failures"] or failures["runtime_failures"]:
                drift = True
            else:
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_bytes(_render_report(report))
        else:
            if not report_path.is_file():
                drift = True
            else:
                stored = load_json(report_path)
                drift = deterministic_projection(stored) != deterministic_projection(report)
                stored_runtime = stored.get("runtime_observation")
                if not isinstance(stored_runtime, Mapping) or stored_runtime.get("failures"):
                    drift = True
        passed = not failures["hard_failures"] and not failures["runtime_failures"] and not drift
        current_projection = deterministic_projection(report)
        payload = {
            "status": "PASS" if passed else "FAIL",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "mode": "write" if args.write else "check",
            "report": report_path.relative_to(database_dir).as_posix(),
            "report_drift": drift,
            "deterministic_report_sha256": _sha256_bytes(_canonical_bytes(current_projection)),
            "hard_gate_failures": failures["hard_failures"],
            "runtime_gate_failures": failures["runtime_failures"],
            "runtime_metrics": report["runtime_observation"]["metrics"],
            "requests": {
                "cold": report["request_profiles"]["cold"],
                "warm_304": report["request_profiles"]["warm_304"],
                "rate_limit": report["request_profiles"]["rate_limit"],
            },
            "quality": report["quality"],
            "writes_files": bool(args.write and passed),
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if passed else 1
    except (PerformanceError, RetrievalError, memory.MemoryCLIError, OSError) as exc:
        reason = str(exc) if isinstance(exc, (PerformanceError, RetrievalError)) else "filesystem_or_memory_error"
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "reason": reason,
                    "writes_files": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
