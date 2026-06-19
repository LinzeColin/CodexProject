import json
from pathlib import Path

from pfi_os.app.dashboard import vectorized_research_shell_summary
from pfi_os.application import (
    OperationalStore,
    build_vectorized_research_read_model,
    empty_vectorized_research_read_model,
    ingest_vectorized_research_cache,
)


def test_vectorized_read_model_ingests_latest_cache_without_private_paths(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_path = project_root / "data" / "vectorized" / "VectorizedResearch_latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps(_payload(tmp_path), ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_vectorized_research_cache(store, project_root=project_root)
    model = build_vectorized_research_read_model(store)
    source = store.table_rows("source_records")[0]
    evidence = store.table_rows("evidence_records")[0]
    metadata_blob = "\n".join(
        row["metadata_json"]
        for row in [*store.table_rows("source_records"), *store.table_rows("evidence_records"), *store.table_rows("job_records")]
    )

    assert result["schema"] == "PFIOSVectorizedResearchCacheIngestionV1"
    assert result["status"] == "Ingested"
    assert source["source_type"] == "vectorized_research_cache"
    assert source["domain"] == "PUBLIC_SHARED_CANONICAL"
    assert source["uri"] == "data/vectorized/VectorizedResearch_latest.json"
    assert evidence["evidence_class"] == "vectorized_research_summary"
    assert model["schema"] == "PFIOSVectorizedResearchBatchV1"
    assert model["status"] == "Pass"
    assert model["selected_symbol"] == "SPY"
    assert model["summary_rows"][0]["symbol"] == "SPY"
    assert model["outputs"]["latest_json"] == "data/vectorized/VectorizedResearch_latest.json"
    assert model["source_uri"] == "data/vectorized/VectorizedResearch_latest.json"
    assert model["evidence_id"]
    assert "OperationalStore -> vectorized_research_summary" in model["read_model"]
    assert str(tmp_path) not in metadata_blob
    assert store.table_rows("task_records") == []


def test_vectorized_read_model_creates_review_task_for_non_pass_status(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    cache_path = project_root / "data" / "vectorized" / "VectorizedResearch_latest.json"
    cache_path.parent.mkdir(parents=True)
    payload = _payload(tmp_path)
    payload["status"] = "NeedsReview"
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_vectorized_research_cache(store, project_root=project_root)
    task = store.table_rows("task_records")[0]
    model = build_vectorized_research_read_model(store)

    assert result["status"] == "Ingested"
    assert result["task_id"] == task["task_id"]
    assert task["owner_workspace"] == "data_system"
    assert task["human_review_required"] == 1
    assert "NeedsReview" in task["action"]
    assert model["status"] == "NeedsReview"


def test_vectorized_read_model_skips_missing_or_wrong_schema_cache(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    missing = ingest_vectorized_research_cache(store, project_root=project_root)
    cache_path = project_root / "data" / "vectorized" / "VectorizedResearch_latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps({"schema": "Wrong"}), encoding="utf-8")
    wrong_schema = ingest_vectorized_research_cache(store, project_root=project_root)
    model = build_vectorized_research_read_model(store)

    assert missing["status"] == "Skipped"
    assert wrong_schema["status"] == "Skipped"
    assert model["status"] == "Missing"
    assert store.table_rows("source_records") == []
    assert store.table_rows("evidence_records") == []


def test_empty_vectorized_read_model_is_compatible_with_shell_summary():
    model = empty_vectorized_research_read_model()
    summary = vectorized_research_shell_summary(model)

    assert model["schema"] == "PFIOSVectorizedResearchBatchV1"
    assert summary["schema"] == "VectorizedResearchShellSummaryV1"
    assert summary["status"] == "Missing"
    assert summary["rows"] == []


def _payload(tmp_path: Path) -> dict:
    return {
        "schema": "PFIOSVectorizedResearchBatchV1",
        "as_of": "2026-06-19",
        "generated_at": "2026-06-19T09:30:00+00:00",
        "mode": "local_batch",
        "status": "Pass",
        "replay_path": str(tmp_path / "private" / "EventReplay_latest.json"),
        "replay_status": "Pass",
        "row_count": 240,
        "symbol_count": 1,
        "available_symbols": ["SPY"],
        "selected_symbol": "SPY",
        "first_datetime": "2026-06-01",
        "last_datetime": "2026-06-19",
        "strategy_id": "moving_average_crossover",
        "parameter_grid": {"short_window": [2, 3], "long_window": [4, 5]},
        "parameter_run_count": 4,
        "scan_run_count": 4,
        "best_run": {"run_id": "run_1", "sharpe": 1.25, "artifact_path": str(tmp_path / "private" / "run_1.json")},
        "stability": {"stability_status": "Stable", "parameter_coverage": 1.0},
        "missing_data_log": [{"path": str(tmp_path / "private" / "missing.csv")}],
        "assumptions": ["Fixture payload only."],
        "summary_rows": [
            {
                "symbol": "SPY",
                "short_window": 2,
                "long_window": 4,
                "total_return_pct": 4.2,
                "max_drawdown_pct": -1.5,
                "sharpe": 1.25,
            }
        ],
        "outputs": {
            "latest_json": "data/vectorized/VectorizedResearch_latest.json",
            "private_path": str(tmp_path / "private" / "VectorizedResearch_latest.json"),
        },
    }
