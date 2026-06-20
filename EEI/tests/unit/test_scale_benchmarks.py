from __future__ import annotations

from pathlib import Path

from scripts.run_scale_benchmarks import (
    TARGET_SCALES,
    build_payload,
    parse_scales,
    read_budget_ms,
)


def test_parse_scales_supports_commas_and_underscores() -> None:
    assert parse_scales("10_000,100000, 1000000") == [10_000, 100_000, 1_000_000]


def test_scale_benchmark_smoke_payload_is_partial_until_full_targets() -> None:
    budgets = read_budget_ms(Path("data/parameter_catalog.csv"))
    payload = build_payload(mode="ci_smoke", scales=[1_000], iterations=1, budgets=budgets)
    assert payload["schema_version"] == "eei-scale-benchmark-v1"
    assert payload["task_id"] == "T1306"
    assert payload["acceptance_ids"] == ["A208"]
    assert payload["status"] == "PARTIAL"
    assert payload["target_scales"] == list(TARGET_SCALES)
    assert payload["measured_scales"] == [1_000]
    assert payload["coverage"]["target_scales_measured"] is False
    assert payload["coverage"]["browser_runtime_measured"] is False
    assert payload["coverage"]["full_a208_pass"] is False
    assert payload["results"][0]["metric_groups"]["api"] is True
    assert payload["results"][0]["metric_groups"]["browser_runtime"] is False


def test_scale_benchmark_records_budget_and_pass_fail_per_measured_scale() -> None:
    budgets = read_budget_ms(Path("data/parameter_catalog.csv"))
    payload = build_payload(mode="ci_smoke", scales=[1_000], iterations=1, budgets=budgets)
    result = payload["results"][0]
    assert result["budget_ms"] == budgets[10_000]
    assert result["last_counts"]["returned_edges"] <= 2_000
    assert result["last_counts"]["returned_nodes"] <= 500
    assert result["status"] in {"PASS", "FAIL"}


def test_scale_benchmark_merges_browser_runtime_artifact() -> None:
    budgets = read_budget_ms(Path("data/parameter_catalog.csv"))
    payload = build_payload(
        mode="operator_full",
        scales=[1_000],
        iterations=1,
        budgets=budgets,
        browser_runtime_by_scale={
            1_000: {
                "status": "PASS",
                "browser_render_ms": {"p95": 20.0},
                "browser_frame_delta_ms": {"p95": 32.0},
                "browser_dom_payload_bytes": {"p95": 12000.0},
                "browser_heap_delta_bytes": None,
                "browser_long_task_count": 0,
                "browser_max_long_task_ms": 0,
                "last_counts": {"rendered_nodes": 64, "rendered_edges": 200},
            }
        },
    )
    result = payload["results"][0]
    assert result["metric_groups"]["browser_runtime"] is True
    assert result["browser_runtime"]["status"] == "PASS"
    assert payload["coverage"]["browser_runtime_measured"] is True
