from pathlib import Path

import numpy as np
import pandas as pd

from pfi_os.analysis import default_sentiment_universe
from pfi_os.application import (
    MARKETS_WORKFLOW_SCHEMA,
    OperationalStore,
    build_markets_workflow,
    build_phase_b_markets_contract,
    record_markets_workflow,
)


DECISION_FIELDS = {
    "decision_id",
    "entity_id",
    "action",
    "horizon",
    "target_weight_change",
    "status",
    "confidence",
    "evidence_class",
    "as_of",
    "thesis",
    "catalysts",
    "counter_evidence",
    "invalidation_conditions",
    "risks",
    "portfolio_effect",
    "model_versions",
    "source_ids",
    "human_review_required",
}


CARD_FIELDS = {"card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "freshness"}


def _bars(close_values, symbol: str):
    index = pd.date_range("2026-06-01", periods=len(close_values), freq="B")
    close = np.array(close_values, dtype=float)
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": symbol,
            "market": "US",
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000,
        }
    )


def _price_frames():
    instruments = default_sentiment_universe("US")[:4]
    frames = {
        instruments[0].symbol: _bars(np.linspace(100, 130, 90), instruments[0].symbol),
        instruments[1].symbol: _bars(np.r_[np.linspace(120, 105, 45), np.linspace(105, 135, 45)], instruments[1].symbol),
        instruments[2].symbol: _bars(np.linspace(30, 24, 90), instruments[2].symbol),
        instruments[3].symbol: _bars(np.linspace(180, 200, 90), instruments[3].symbol),
    }
    return frames, instruments


def test_phase_b_markets_contract_declares_card_decision_and_safety_constraints():
    contract = build_phase_b_markets_contract()

    assert contract["schema"] == "PFIOSPhaseBMarketsContractV1"
    assert contract["workflow_schema"] == MARKETS_WORKFLOW_SCHEMA
    assert contract["workspace"] == "markets"
    assert "build_market_event_log" in contract["required_steps"]
    assert "classify_freshness_and_coverage" in contract["required_steps"]
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert set(contract["required_card_fields"]) == CARD_FIELDS
    assert set(contract["decision_contract_fields"]) == DECISION_FIELDS
    assert contract["non_regression_constraints"] == {
        "markets_vertical_slice": True,
        "source_freshness_visible": True,
        "evidence_and_counter_evidence_required": True,
        "no_live_trading": True,
        "human_review_required": True,
        "provider_fetch_required": False,
        "llm_required": False,
    }


def test_markets_workflow_builds_event_hotspot_sentiment_cards_and_decision():
    frames, instruments = _price_frames()

    payload = build_markets_workflow(
        frames,
        instruments,
        source_id="src-markets-us-2026-06-19",
        as_of="2026-06-19T16:00:00+10:00",
        data_source="Sample",
        market="US",
        interval="1d",
        max_snapshots=12,
    )

    assert payload["schema"] == MARKETS_WORKFLOW_SCHEMA
    assert payload["workspace"] == "markets"
    assert payload["source_id"] == "src-markets-us-2026-06-19"
    assert payload["evidence_class"] == "market_observation"
    assert payload["model_versions"] == ["DisabledProvider"]
    assert payload["requested_count"] == 4
    assert payload["observed_symbol_count"] == 4
    assert payload["market_event_log"]["schema"] == "PFIOSMarketEventLogV1"
    assert payload["market_event_log"]["event_count"] == 90
    assert payload["sentiment"]["summary"]["object_count"] == 4
    assert len(payload["sentiment"]["rows"]) == 4
    assert payload["hotspots"]["summary"]["object_count"] == 4
    assert len(payload["hotspots"]["focus_rows"]) > 0
    assert payload["freshness"]["status"] in {"Fresh", "Delayed", "Stale"}
    assert {card["card_id"] for card in payload["cards"]} == {"market_event_log", "market_hotspots", "market_sentiment"}
    for card in payload["cards"]:
        assert set(card) == CARD_FIELDS
        assert card["source_ids"]
        assert card["freshness"]["latest_event_time"]
    assert set(payload["decision"]) == DECISION_FIELDS
    assert payload["decision"]["action"] == "review_market_update"
    assert payload["decision"]["target_weight_change"] == 0.0
    assert payload["decision"]["human_review_required"] is True
    assert payload["decision"]["counter_evidence"]
    assert payload["decision"]["invalidation_conditions"]
    assert payload["decision"]["portfolio_effect"]["no_private_holdings_used"] is True
    assert payload["safety_boundary"] == {
        "research_only": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "human_review_required": True,
    }


def test_markets_workflow_is_stable_for_identical_inputs():
    frames, instruments = _price_frames()
    kwargs = {
        "source_id": "src-markets-stable",
        "as_of": "2026-06-19T16:00:00+10:00",
        "data_source": "Sample",
        "market": "US",
        "interval": "1d",
        "max_snapshots": 12,
    }

    first = build_markets_workflow(frames, instruments, **kwargs)
    second = build_markets_workflow(frames, instruments, **kwargs)

    assert first["workflow_id"] == second["workflow_id"]
    assert first["market_event_log"]["quality_report"]["checksum"] == second["market_event_log"]["quality_report"]["checksum"]
    assert first["cards"] == second["cards"]


def test_markets_workflow_records_operational_store_evidence_job_and_review_task(tmp_path: Path):
    frames, instruments = _price_frames()
    payload = build_markets_workflow(
        frames,
        instruments,
        source_id="src-markets-store",
        as_of="2026-06-19T16:00:00+10:00",
        data_source="Sample",
        market="US",
        interval="1d",
        max_snapshots=12,
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")

    ids = record_markets_workflow(store, payload)

    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")
    jobs = store.table_rows("job_records")
    tasks = store.table_rows("task_records")

    assert ids == {
        "source_id": "src-markets-store",
        "evidence_id": f"evidence-{payload['workflow_id']}",
        "job_id": f"job-{payload['workflow_id']}",
        "task_id": f"task-{payload['workflow_id']}",
    }
    assert sources[0]["source_type"] == "markets_vertical_slice"
    assert sources[0]["evidence_class"] == "market_observation"
    assert evidence[0]["entity_id"] == "US"
    assert "Markets workflow for US" in evidence[0]["summary"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["progress"] == 1.0
    assert tasks[0]["owner_workspace"] == "markets"
    assert tasks[0]["human_review_required"] == 1
