#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import platform
import statistics
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET_SCALES = (10_000, 100_000, 1_000_000)
MAX_VISIBLE_NODES = 500
MAX_VISIBLE_EDGES = 2_000
FRAME_BUDGET_MS = 16.67
LONG_TASK_BUDGET_MS = 50.0
BENCHMARK_PARAMETER_KEYS = {
    10_000: "benchmark.scale_10k_p95_ms",
    100_000: "benchmark.scale_100k_p95_ms",
    1_000_000: "benchmark.scale_1m_p95_ms",
}
RELATIONSHIP_FAMILY_CYCLE = (
    "supply_chain_operations",
    "technology_data_ip",
    "commercial_dependency",
    "ownership_control",
)
VISIBLE_RELATIONSHIP_FAMILY_INDEXES = {0, 1}


@dataclass(frozen=True)
class SyntheticEdge:
    edge_id: int
    subject_id: int
    object_id: int
    confidence: float
    observed_rank: int
    family: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic EEI graph scale benchmark smoke/full contracts."
    )
    parser.add_argument(
        "--scales",
        default="1000",
        help="Comma-separated relationship scales to measure, e.g. 10000,100000,1000000.",
    )
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument(
        "--mode",
        default="ci_smoke",
        choices=["ci_smoke", "operator_full"],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/eei-scale-benchmark-smoke.json"),
    )
    parser.add_argument(
        "--fail-on-budget",
        action="store_true",
        help="Exit non-zero when any measured scale exceeds its applicable p95 budget.",
    )
    parser.add_argument(
        "--require-full-targets",
        action="store_true",
        help="Exit non-zero unless 10k, 100k and 1m target scales are all measured.",
    )
    parser.add_argument(
        "--browser-runtime-artifact",
        type=Path,
        help="Optional browser runtime benchmark JSON to merge into A208 full pass coverage.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write the benchmark payload without printing the full JSON to stdout.",
    )
    return parser.parse_args()


def parse_scales(raw_value: str) -> list[int]:
    scales: list[int] = []
    for raw_item in raw_value.split(","):
        item = raw_item.strip().replace("_", "")
        if not item:
            continue
        value = int(item)
        if value <= 0:
            raise ValueError(f"Scale must be positive: {raw_item}")
        scales.append(value)
    if not scales:
        raise ValueError("At least one scale is required")
    return scales


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("Cannot compute percentile for empty values")
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    lower_value = ordered[lower] * (upper - position)
    upper_value = ordered[upper] * (position - lower)
    return lower_value + upper_value


def summary(values: list[float]) -> dict[str, float]:
    return {
        "min": round(min(values), 4),
        "p50": round(statistics.median(values), 4),
        "p95": round(percentile(values, 0.95), 4),
        "p99": round(percentile(values, 0.99), 4),
        "max": round(max(values), 4),
    }


def read_budget_ms(parameter_catalog: Path) -> dict[int, float]:
    budgets: dict[int, float] = {}
    with parameter_catalog.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for scale, parameter_key in BENCHMARK_PARAMETER_KEYS.items():
                if row["parameter_key"] == parameter_key:
                    budgets[scale] = float(row["default_value"])
    missing = sorted(scale for scale in TARGET_SCALES if scale not in budgets)
    if missing:
        raise RuntimeError(f"Missing benchmark budget parameters for scales: {missing}")
    return budgets


def budget_for_scale(scale: int, budgets: dict[int, float]) -> float:
    eligible_scales = [target for target in TARGET_SCALES if scale <= target]
    if eligible_scales:
        return budgets[min(eligible_scales)]
    return budgets[max(TARGET_SCALES)]


def synthetic_edge(index: int, scale: int) -> SyntheticEdge:
    object_id = (index % max(32, scale // 8)) + 2
    confidence = 0.5 + ((index * 37) % 5000) / 10000
    return SyntheticEdge(
        edge_id=index + 1,
        subject_id=1 if index % 2 == 0 else object_id,
        object_id=object_id if index % 2 == 0 else 1,
        confidence=confidence,
        observed_rank=scale - index,
        family=RELATIONSHIP_FAMILY_CYCLE[index % len(RELATIONSHIP_FAMILY_CYCLE)],
    )


def measure_api_projection(scale: int) -> tuple[dict[str, Any], list[SyntheticEdge]]:
    start = perf_counter()
    candidate_count = 0
    top_edges: list[tuple[tuple[float, int, int], int]] = []
    for index in range(scale):
        if index % len(RELATIONSHIP_FAMILY_CYCLE) not in VISIBLE_RELATIONSHIP_FAMILY_INDEXES:
            continue
        candidate_count += 1
        edge_id = index + 1
        confidence = 0.5 + ((index * 37) % 5000) / 10000
        rank_key = (confidence, scale - index, -edge_id)
        if len(top_edges) < MAX_VISIBLE_EDGES + 1:
            heapq.heappush(top_edges, (rank_key, index))
        elif rank_key > top_edges[0][0]:
            heapq.heapreplace(top_edges, (rank_key, index))
    selected_edges = [
        synthetic_edge(index, scale)
        for _, index in sorted(
            top_edges,
            key=lambda item: item[0],
            reverse=True,
        )
    ][: MAX_VISIBLE_EDGES + 1]
    truncated = candidate_count > MAX_VISIBLE_EDGES
    selected_edges = selected_edges[:MAX_VISIBLE_EDGES]
    elapsed_ms = (perf_counter() - start) * 1000
    unique_nodes = {1}
    for edge in selected_edges:
        unique_nodes.add(edge.subject_id)
        unique_nodes.add(edge.object_id)
        if len(unique_nodes) >= MAX_VISIBLE_NODES:
            break
    return (
        {
            "elapsed_ms": elapsed_ms,
            "candidate_edges": candidate_count,
            "returned_edges": len(selected_edges),
            "returned_nodes": min(len(unique_nodes), MAX_VISIBLE_NODES),
            "truncated": truncated,
        },
        selected_edges,
    )


def measure_layout(
    selected_edges: list[SyntheticEdge],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    start = perf_counter()
    node_ids: list[int] = [1]
    seen_node_ids = {1}
    for edge in selected_edges:
        for node_id in (edge.subject_id, edge.object_id):
            if node_id not in seen_node_ids:
                node_ids.append(node_id)
                seen_node_ids.add(node_id)
            if len(node_ids) >= MAX_VISIBLE_NODES:
                break
        if len(node_ids) >= MAX_VISIBLE_NODES:
            break
    positioned_nodes: list[dict[str, Any]] = []
    for index, node_id in enumerate(node_ids):
        lane = -1 if index % 3 == 0 else 1 if index % 3 == 1 else 0
        radius = 80 + (index // 3) * 18
        angle = (index * 137.5) % 360
        positioned_nodes.append(
            {
                "id": node_id,
                "x": round(lane * radius + math.cos(math.radians(angle)) * 16, 4),
                "y": round((index % 32) * 18 + math.sin(math.radians(angle)) * 16, 4),
            }
        )
    elapsed_ms = (perf_counter() - start) * 1000
    return {"elapsed_ms": elapsed_ms, "positioned_nodes": len(positioned_nodes)}, positioned_nodes


def measure_render(
    selected_edges: list[SyntheticEdge],
    positioned_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    start = perf_counter()
    node_set = {node["id"] for node in positioned_nodes}
    rendered_edges = [
        {
            "id": edge.edge_id,
            "source": edge.subject_id,
            "target": edge.object_id,
            "class": f"edge edge-{edge.family}",
        }
        for edge in selected_edges
        if edge.subject_id in node_set and edge.object_id in node_set
    ]
    render_payload = {
        "nodes": positioned_nodes,
        "edges": rendered_edges,
        "viewbox": [0, 0, 1440, 900],
    }
    serialized = json.dumps(render_payload, separators=(",", ":"))
    elapsed_ms = (perf_counter() - start) * 1000
    memory_bytes = len(serialized.encode("utf-8"))
    estimated_frame_ms = elapsed_ms / max(1, math.ceil(elapsed_ms / FRAME_BUDGET_MS))
    long_task_count = int(elapsed_ms > LONG_TASK_BUDGET_MS)
    return {
        "elapsed_ms": elapsed_ms,
        "rendered_nodes": len(positioned_nodes),
        "rendered_edges": len(rendered_edges),
        "payload_bytes": memory_bytes,
        "estimated_frame_ms": estimated_frame_ms,
        "synthetic_long_task_count": long_task_count,
    }


def measure_scale(scale: int, iterations: int, budgets: dict[int, float]) -> dict[str, Any]:
    api_times: list[float] = []
    layout_times: list[float] = []
    render_times: list[float] = []
    frame_times: list[float] = []
    total_times: list[float] = []
    memory_bytes: list[int] = []
    long_task_counts: list[int] = []
    last_api: dict[str, Any] = {}
    last_layout: dict[str, Any] = {}
    last_render: dict[str, Any] = {}

    for _ in range(iterations):
        iteration_start = perf_counter()
        api_result, selected_edges = measure_api_projection(scale)
        layout_result, positioned_nodes = measure_layout(selected_edges)
        render_result = measure_render(selected_edges, positioned_nodes)
        total_ms = (perf_counter() - iteration_start) * 1000

        api_times.append(float(api_result["elapsed_ms"]))
        layout_times.append(float(layout_result["elapsed_ms"]))
        render_times.append(float(render_result["elapsed_ms"]))
        frame_times.append(float(render_result["estimated_frame_ms"]))
        total_times.append(total_ms)
        memory_bytes.append(int(render_result["payload_bytes"]))
        long_task_counts.append(int(render_result["synthetic_long_task_count"]))
        last_api = api_result
        last_layout = layout_result
        last_render = render_result

    p95_budget_ms = budget_for_scale(scale, budgets)
    total_summary = summary(total_times)
    passed_budget = total_summary["p95"] <= p95_budget_ms
    return {
        "scale_relationships": scale,
        "iterations": iterations,
        "budget_ms": p95_budget_ms,
        "status": "PASS" if passed_budget else "FAIL",
        "api_projection_ms": summary(api_times),
        "layout_ms": summary(layout_times),
        "render_contract_ms": summary(render_times),
        "estimated_frame_ms": summary(frame_times),
        "total_ms": total_summary,
        "memory_payload_bytes": {
            "max": max(memory_bytes),
            "p95": round(percentile([float(value) for value in memory_bytes], 0.95), 4),
        },
        "synthetic_long_task_count": max(long_task_counts),
        "last_counts": {
            "candidate_edges": last_api["candidate_edges"],
            "returned_edges": last_api["returned_edges"],
            "returned_nodes": last_api["returned_nodes"],
            "positioned_nodes": last_layout["positioned_nodes"],
            "rendered_edges": last_render["rendered_edges"],
            "truncated": last_api["truncated"],
        },
        "metric_groups": {
            "api": True,
            "layout": True,
            "render_contract": True,
            "memory_payload": True,
            "estimated_frame": True,
            "synthetic_long_task": True,
            "browser_runtime": False,
        },
    }


def environment_payload() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }


def read_browser_runtime_artifact(path: Path | None) -> dict[int, dict[str, Any]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "eei-browser-scale-benchmark-v1":
        raise ValueError("browser runtime artifact schema mismatch")
    if payload.get("task_id") != "T1306" or "A208" not in payload.get("acceptance_ids", []):
        raise ValueError("browser runtime artifact must cite T1306/A208")
    return {
        int(result["scale_relationships"]): result
        for result in payload.get("results", [])
        if result.get("status") == "PASS"
    }


def build_payload(
    *,
    mode: str,
    scales: list[int],
    iterations: int,
    budgets: dict[int, float],
    browser_runtime_by_scale: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    results = [measure_scale(scale, iterations, budgets) for scale in scales]
    browser_runtime_by_scale = browser_runtime_by_scale or {}
    for result in results:
        scale = int(result["scale_relationships"])
        browser_runtime = browser_runtime_by_scale.get(scale)
        if browser_runtime:
            result["metric_groups"]["browser_runtime"] = True
            result["browser_runtime"] = {
                "status": browser_runtime["status"],
                "browser_render_ms": browser_runtime["browser_render_ms"],
                "browser_frame_delta_ms": browser_runtime["browser_frame_delta_ms"],
                "browser_dom_payload_bytes": browser_runtime["browser_dom_payload_bytes"],
                "browser_heap_delta_bytes": browser_runtime.get("browser_heap_delta_bytes"),
                "browser_long_task_count": browser_runtime["browser_long_task_count"],
                "browser_max_long_task_ms": browser_runtime["browser_max_long_task_ms"],
                "last_counts": browser_runtime["last_counts"],
            }
    measured_scales = {result["scale_relationships"] for result in results}
    all_target_scales_measured = set(TARGET_SCALES).issubset(measured_scales)
    all_measured_pass = all(result["status"] == "PASS" for result in results)
    browser_runtime_measured = all(
        result["metric_groups"]["browser_runtime"] for result in results
    )
    full_a208_pass = all_target_scales_measured and all_measured_pass and browser_runtime_measured
    status = "PASS" if full_a208_pass else "PARTIAL" if all_measured_pass else "FAIL"
    remaining_to_close = []
    if not all_target_scales_measured:
        remaining_to_close.append(
            "Run operator_full mode for 10k, 100k and 1m relationship scales."
        )
    if not browser_runtime_measured:
        remaining_to_close.append(
            "Attach browser runtime frame, memory and long-task measurements."
        )
    if not full_a208_pass:
        remaining_to_close.append(
            "Record pass/fail release evidence after full benchmark completes."
        )
    return {
        "schema_version": "eei-scale-benchmark-v1",
        "system_name": "EEI",
        "task_id": "T1306",
        "acceptance_ids": ["A208"],
        "status": status,
        "mode": mode,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "environment": environment_payload(),
        "target_scales": list(TARGET_SCALES),
        "measured_scales": sorted(measured_scales),
        "iterations": iterations,
        "budgets_ms": {str(scale): budgets[scale] for scale in TARGET_SCALES},
        "results": results,
        "coverage": {
            "target_scales_measured": all_target_scales_measured,
            "browser_runtime_measured": browser_runtime_measured,
            "full_a208_pass": full_a208_pass,
            "required_metric_groups": [
                "api",
                "layout",
                "render",
                "memory",
                "frame",
                "long_task",
            ],
        },
        "remaining_to_close_a208": remaining_to_close,
    }


def write_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    args = parse_args()
    if args.iterations <= 0:
        raise ValueError("--iterations must be positive")
    scales = parse_scales(args.scales)
    budgets = read_budget_ms(ROOT / "data/parameter_catalog.csv")
    payload = build_payload(
        mode=args.mode,
        scales=scales,
        iterations=args.iterations,
        budgets=budgets,
        browser_runtime_by_scale=read_browser_runtime_artifact(args.browser_runtime_artifact),
    )
    write_payload(args.output, payload)
    if not args.quiet:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.fail_on_budget and payload["status"] == "FAIL":
        return 1
    if args.require_full_targets and not payload["coverage"]["full_a208_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
