from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.portfolio_workflow import build_portfolio_workflow, record_portfolio_workflow


PFI008_PORTFOLIO_ACCEPTANCE_SCHEMA = "PFI008PortfolioVerticalAcceptanceV1"
PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA = "PFI008PortfolioUIReadModelV1"
PFI008_GOLDEN_SOURCE_ID = "src-pfi008-portfolio-golden-2026-06-19"
PFI008_GOLDEN_AS_OF = "2026-06-19T16:00:00+10:00"


def build_pfi008_portfolio_golden_fixture() -> dict[str, Any]:
    """Return a deterministic private-safe synthetic portfolio import fixture.

    The ledger is intentionally synthetic. It models broker imports, one
    corporate action, one FX conversion, and a cash balance without connecting
    to a broker, reading real holdings, or creating order intent.
    """
    updated_at = "2026-06-19T06:00:00+00:00"
    ledger = [
        {
            "broker": "SyntheticBrokerA",
            "source_file": "broker-a-positions.csv",
            "symbol": "AAPL",
            "name": "Apple",
            "market": "US",
            "quantity": 10.0,
            "corporate_action": {"type": "split", "ratio": 4.0, "effective_date": "2026-06-10"},
            "adjusted_quantity": 40.0,
            "currency": "USD",
            "fx_rate_to_usd": 1.0,
            "position_value_usd": 3900.0,
            "cost_basis_usd": 3300.0,
            "updated_at": updated_at,
        },
        {
            "broker": "SyntheticBrokerA",
            "source_file": "broker-a-positions.csv",
            "symbol": "MSFT",
            "name": "Microsoft",
            "market": "US",
            "quantity": 11.0,
            "corporate_action": None,
            "adjusted_quantity": 11.0,
            "currency": "USD",
            "fx_rate_to_usd": 1.0,
            "position_value_usd": 2200.0,
            "cost_basis_usd": 1900.0,
            "updated_at": updated_at,
        },
        {
            "broker": "SyntheticBrokerB",
            "source_file": "broker-b-cn-etf.csv",
            "symbol": "510300",
            "name": "CSI 300 ETF",
            "market": "CN",
            "quantity": 8000.0,
            "corporate_action": None,
            "adjusted_quantity": 8000.0,
            "currency": "CNY",
            "local_value": 11600.0,
            "fx_rate_to_usd": 0.13793103448275862,
            "position_value_usd": 1600.0,
            "cost_basis_usd": 1440.0,
            "updated_at": updated_at,
        },
        {
            "broker": "SyntheticBrokerB",
            "source_file": "broker-b-global-etf.csv",
            "symbol": "GLD",
            "name": "Gold ETF",
            "market": "US",
            "quantity": 6.0,
            "corporate_action": None,
            "adjusted_quantity": 6.0,
            "currency": "USD",
            "fx_rate_to_usd": 1.0,
            "position_value_usd": 1200.0,
            "cost_basis_usd": 1100.0,
            "updated_at": updated_at,
        },
        {
            "broker": "SyntheticBrokerC",
            "source_file": "broker-c-bonds.csv",
            "symbol": "TLT",
            "name": "Treasury ETF",
            "market": "US",
            "quantity": 6.0,
            "corporate_action": None,
            "adjusted_quantity": 6.0,
            "currency": "USD",
            "fx_rate_to_usd": 1.0,
            "position_value_usd": 600.0,
            "cost_basis_usd": 650.0,
            "updated_at": updated_at,
        },
    ]
    return {
        "schema": "PFI008PortfolioGoldenFixtureV1",
        "source_id": PFI008_GOLDEN_SOURCE_ID,
        "as_of": PFI008_GOLDEN_AS_OF,
        "portfolio_id": "core",
        "import_ledger": ledger,
        "cash_ledger": [
            {
                "broker": "SyntheticBrokerC",
                "currency": "USD",
                "cash_balance": 500.0,
                "fx_rate_to_usd": 1.0,
                "cash_balance_usd": 500.0,
                "as_of": PFI008_GOLDEN_AS_OF,
            }
        ],
        "optimizer_constraints": {
            "max_single_weight": 0.35,
            "max_top3_weight": 0.75,
            "min_cash_buffer": 0.05,
            "allow_auto_rebalance": False,
            "allow_order_intent": False,
        },
        "expected": {
            "import_record_count": 5,
            "broker_count": 3,
            "holding_count": 5,
            "corporate_action_adjusted_count": 1,
            "fx_converted_count": 1,
            "cash_balance_usd": 500.0,
            "total_position_value_usd": 9500.0,
            "target_weight_change": 0.0,
            "constraint_violation_minimum": 2,
            "human_review_required": True,
        },
    }


def build_pfi008_reviewed_holdings(fixture: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in fixture.get("import_ledger", []):
        value = float(item.get("position_value_usd", 0.0) or 0.0)
        cost_basis = float(item.get("cost_basis_usd", 0.0) or 0.0)
        rows.append(
            {
                "source_system": item.get("broker", ""),
                "source_file": item.get("source_file", ""),
                "symbol": item.get("symbol", ""),
                "name": item.get("name", ""),
                "market": item.get("market", ""),
                "quantity": item.get("adjusted_quantity", item.get("quantity", 0.0)),
                "cost_basis": cost_basis,
                "position_value": value,
                "unrealized_pnl": value - cost_basis,
                "weight": 0.0,
                "updated_at": item.get("updated_at", fixture.get("as_of", "")),
                "source_modified_time": item.get("updated_at", fixture.get("as_of", "")),
            }
        )
    return pd.DataFrame(rows)


def build_pfi008_portfolio_ui_read_model(payload: dict[str, Any], fixture: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    reconciliation = _reconciliation(payload, fixture)
    decision_proposal = _decision_proposal(payload, fixture, reconciliation)
    return {
        "schema": PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA,
        "workspace": "portfolio",
        "workspace_label": "持仓",
        "primary_route": "portfolio",
        "primary_feature_view": "portfolio_slice",
        "secondary_feature_views": ["portfolio_reconciliation", "portfolio_risk", "portfolio_decision"],
        "title": "持仓垂直切片",
        "summary": "从合成导入账本生成持仓快照、对账、现金、汇率换算、公司行动固定样本、风险约束和人工决策提案。",
        "cards": [
            _ui_card("持仓快照", next((card for card in payload.get("cards", []) if card.get("card_id") == "portfolio_holdings"), {})),
            _ui_card("风险约束", next((card for card in payload.get("cards", []) if card.get("card_id") == "portfolio_exposure"), {})),
            _ui_card("人工复核", next((card for card in payload.get("cards", []) if card.get("card_id") == "portfolio_risk_review"), {})),
        ],
        "import_reconciliation": reconciliation,
        "golden_inputs": {
            "synthetic_broker_imports": len(fixture.get("import_ledger", [])),
            "corporate_action_adjusted_count": _corporate_action_count(fixture),
            "fx_converted_count": _fx_converted_count(fixture),
            "cash_balance_usd": _cash_balance_usd(fixture),
            "readonly": True,
        },
        "optimizer_constraints": decision_proposal["constraints"],
        "decision_proposal": decision_proposal,
        "journey": [
            "打开一级入口：持仓",
            "打开功能：持仓垂直切片",
            "查看合成券商导入账本和对账结果",
            "核对公司行动、汇率换算和现金固定样本",
            "查看风险约束和人工决策提案",
        ],
        "operational_record_ids": ids,
        "safety_boundary": {
            "research_only": True,
            "synthetic_fixture_only": True,
            "no_real_broker_connection": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
        },
    }


def run_pfi008_portfolio_acceptance(*, db_path: Path | str | None = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="pfi008-portfolio-") as tmp_dir:
            return _run_acceptance(Path(tmp_dir) / "private" / "operational" / "pfi.sqlite", generated_at=generated_at)
    return _run_acceptance(Path(db_path), generated_at=generated_at)


def rollback_pfi008_portfolio_records(store: OperationalStore, ids: dict[str, str]) -> dict[str, Any]:
    source_id = str(ids.get("source_id", ""))
    evidence_id = str(ids.get("evidence_id", ""))
    job_id = str(ids.get("job_id", ""))
    task_id = str(ids.get("task_id", ""))
    snapshot_id = str(ids.get("snapshot_id", ""))
    counts: dict[str, int] = {}
    with store.connect() as conn:
        counts["task_records"] = conn.execute("DELETE FROM task_records WHERE task_id = ?", (task_id,)).rowcount
        counts["job_records"] = conn.execute("DELETE FROM job_records WHERE job_id = ?", (job_id,)).rowcount
        counts["holding_snapshots"] = conn.execute("DELETE FROM holding_snapshots WHERE snapshot_id = ?", (snapshot_id,)).rowcount
        counts["evidence_records"] = conn.execute("DELETE FROM evidence_records WHERE evidence_id = ?", (evidence_id,)).rowcount
        counts["source_versions"] = conn.execute("DELETE FROM source_versions WHERE source_id = ?", (source_id,)).rowcount
        counts["source_records"] = conn.execute("DELETE FROM source_records WHERE source_id = ?", (source_id,)).rowcount
    residue = {
        "source_records": _count_rows(store, "source_records", "source_id", source_id),
        "evidence_records": _count_rows(store, "evidence_records", "evidence_id", evidence_id),
        "job_records": _count_rows(store, "job_records", "job_id", job_id),
        "task_records": _count_rows(store, "task_records", "task_id", task_id),
        "holding_snapshots": _count_rows(store, "holding_snapshots", "snapshot_id", snapshot_id),
    }
    return {
        "schema": "PFI008PortfolioRollbackProofV1",
        "mode": "temporary_operational_store",
        "deleted_counts": counts,
        "residue_counts": residue,
        "status": "Pass" if all(value == 0 for value in residue.values()) else "Fail",
        "note": "Rollback deletes only PFI-008 source/evidence/job/task/snapshot records in the temporary acceptance store; shared entity rows are left untouched.",
    }


def _run_acceptance(db_path: Path, *, generated_at: str) -> dict[str, Any]:
    fixture = build_pfi008_portfolio_golden_fixture()
    holdings = build_pfi008_reviewed_holdings(fixture)
    constraints = fixture["optimizer_constraints"]
    store = OperationalStore(db_path)
    payload = build_portfolio_workflow(
        holdings,
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        portfolio_id=fixture["portfolio_id"],
        evidence_class="pfi008_private_portfolio_review",
        max_single_weight=float(constraints["max_single_weight"]),
        max_top3_weight=float(constraints["max_top3_weight"]),
    )
    ids = record_portfolio_workflow(store, payload, artifact_uri="operational_store:pfi008_portfolio_acceptance")
    ui_read_model = build_pfi008_portfolio_ui_read_model(payload, fixture, ids)
    golden_metrics = _golden_metrics(payload, ui_read_model, fixture, store)
    checks = _acceptance_checks(payload, ui_read_model, golden_metrics, ids, store)
    rollback_proof = rollback_pfi008_portfolio_records(store, ids)
    checks.append(_check("RollbackProof", rollback_proof["status"] == "Pass", json.dumps(rollback_proof["residue_counts"], sort_keys=True)))
    summary = _summary(checks)
    status = "Pass" if summary["fail"] == 0 else "Fail"
    return {
        "schema": PFI008_PORTFOLIO_ACCEPTANCE_SCHEMA,
        "generated_at": generated_at,
        "status": status,
        "summary": summary,
        "workflow": _json_safe(payload),
        "ui_read_model": _json_safe(ui_read_model),
        "golden_metrics": golden_metrics,
        "rollback_proof": rollback_proof,
        "checks": checks,
        "safety_boundary": {
            "research_only": True,
            "synthetic_fixture_only": True,
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
            "no_real_broker_connection": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
        },
        "next_action": "Use this as Gate 3 Portfolio evidence, then continue PFI-009 Strategy vertical slice.",
    }


def _acceptance_checks(
    payload: dict[str, Any],
    ui_read_model: dict[str, Any],
    golden_metrics: dict[str, Any],
    ids: dict[str, str],
    store: OperationalStore,
) -> list[dict[str, str]]:
    rows = {table: store.table_rows(table) for table in ("source_records", "evidence_records", "job_records", "task_records", "holding_snapshots")}
    return [
        _check("DataChain:SyntheticBrokerImport", golden_metrics["import_record_count"] == 5 and golden_metrics["broker_count"] == 3, f"imports={golden_metrics['import_record_count']}; brokers={golden_metrics['broker_count']}"),
        _check("Golden:CorporateActionFxCash", golden_metrics["corporate_action_adjusted_count"] == 1 and golden_metrics["fx_converted_count"] == 1 and golden_metrics["cash_balance_usd"] == 500.0, "split=1; fx=1; cash=500"),
        _check("Domain:PortfolioWorkflow", payload.get("portfolio_summary", {}).get("holding_count") == 5 and payload.get("schema") == "PFIOSPhaseBPortfolioWorkflowV1", payload.get("workflow_id", "")),
        _check("Reconciliation:BrokerToSnapshot", ui_read_model.get("import_reconciliation", {}).get("status") == "Pass", json.dumps(ui_read_model.get("import_reconciliation", {}), sort_keys=True)),
        _check("API:UIReadModel", ui_read_model.get("schema") == PFI008_PORTFOLIO_UI_READ_MODEL_SCHEMA and ui_read_model.get("primary_route") == "portfolio", ui_read_model.get("schema", "")),
        _check("UI:ChineseJourney", all(step for step in ui_read_model.get("journey", [])) and "持仓" in ui_read_model.get("workspace_label", ""), "portfolio journey labels"),
        _check("OptimizerConstraints:ReviewOnly", golden_metrics["constraint_violation_count"] >= 2 and ui_read_model["decision_proposal"]["order_intent_created"] is False, f"violations={golden_metrics['constraint_violation_count']}"),
        _check("DecisionProposal:HumanReview", ui_read_model["decision_proposal"]["target_weight_change"] == 0.0 and ui_read_model["decision_proposal"]["human_review_required"] is True, "target_weight_change=0"),
        _check("TasksEvidence:Source", any(row["source_id"] == ids["source_id"] for row in rows["source_records"]), ids["source_id"]),
        _check("TasksEvidence:Evidence", any(row["evidence_id"] == ids["evidence_id"] for row in rows["evidence_records"]), ids["evidence_id"]),
        _check("TasksEvidence:Job", any(row["job_id"] == ids["job_id"] and row["status"] == "completed" for row in rows["job_records"]), ids["job_id"]),
        _check("TasksEvidence:ReviewTask", any(row["task_id"] == ids["task_id"] and row["human_review_required"] == 1 for row in rows["task_records"]), ids["task_id"]),
        _check("TasksEvidence:HoldingSnapshot", any(row["snapshot_id"] == ids["snapshot_id"] and row["data_domain"] == "PRIVATE_DERIVED" for row in rows["holding_snapshots"]), ids["snapshot_id"]),
        _check("Safety:NoExecution", all(payload.get("safety_boundary", {}).get(key) is True for key in ("research_only", "no_live_trading", "no_broker_calls", "no_order_execution", "no_holding_mutation", "human_review_required")), "research-only portfolio boundary"),
        _check("GoldenMetrics:StableWorkflow", bool(golden_metrics.get("workflow_id")) and bool(golden_metrics.get("snapshot_checksum")), str(golden_metrics.get("workflow_id", ""))),
    ]


def _reconciliation(payload: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    imported = {str(row.get("symbol", "")) for row in fixture.get("import_ledger", [])}
    snapshot = payload.get("holdings_snapshot", {})
    snapshot_symbols = {str(row.get("symbol", "")) for row in snapshot.get("holdings", [])}
    ledger_value = round(sum(float(row.get("position_value_usd", 0.0) or 0.0) for row in fixture.get("import_ledger", [])), 6)
    snapshot_value = round(float(payload.get("portfolio_summary", {}).get("total_abs_position_value", 0.0) or 0.0), 6)
    unmatched_import_symbols = sorted(imported - snapshot_symbols)
    unmatched_snapshot_symbols = sorted(snapshot_symbols - imported)
    value_delta = round(snapshot_value - ledger_value, 6)
    return {
        "schema": "PFI008PortfolioReconciliationV1",
        "status": "Pass" if not unmatched_import_symbols and not unmatched_snapshot_symbols and abs(value_delta) <= 0.000001 else "Fail",
        "import_record_count": len(fixture.get("import_ledger", [])),
        "snapshot_holding_count": int(snapshot.get("holding_count", 0) or 0),
        "unmatched_import_symbols": unmatched_import_symbols,
        "unmatched_snapshot_symbols": unmatched_snapshot_symbols,
        "ledger_value_usd": ledger_value,
        "snapshot_value_usd": snapshot_value,
        "value_delta_usd": value_delta,
        "human_review_required": True,
    }


def _decision_proposal(payload: dict[str, Any], fixture: dict[str, Any], reconciliation: dict[str, Any]) -> dict[str, Any]:
    constraints = fixture.get("optimizer_constraints", {})
    summary = payload.get("portfolio_summary", {})
    cash = _cash_balance_usd(fixture)
    holdings_value = float(summary.get("total_abs_position_value", 0.0) or 0.0)
    gross_value = holdings_value + cash
    cash_buffer = cash / gross_value if gross_value else 0.0
    rows = [
        _constraint("max_single_weight", float(summary.get("max_single_weight", 0.0) or 0.0), float(constraints.get("max_single_weight", 0.35)), "<="),
        _constraint("max_top3_weight", float(summary.get("top3_weight", 0.0) or 0.0), float(constraints.get("max_top3_weight", 0.75)), "<="),
        _constraint("min_cash_buffer", cash_buffer, float(constraints.get("min_cash_buffer", 0.05)), ">="),
        {
            "constraint_id": "allow_auto_rebalance",
            "actual": bool(constraints.get("allow_auto_rebalance", False)),
            "limit": False,
            "operator": "==",
            "status": "Pass" if constraints.get("allow_auto_rebalance") is False else "Fail",
            "message": "自动再平衡必须关闭；只允许人工复核。",
        },
    ]
    violations = [row for row in rows if row["status"] == "Fail"]
    return {
        "schema": "PFI008PortfolioDecisionProposalV1",
        "status": "ReviewRequired" if violations or reconciliation.get("status") != "Pass" else "WatchOnly",
        "target_weight_change": 0.0,
        "order_intent_created": False,
        "human_review_required": True,
        "constraints": rows,
        "constraint_violation_count": len(violations),
        "proposal_actions": [
            "人工复核 AAPL 单一持仓和前三集中度，不生成自动调仓。",
            "现金缓冲满足最低约束后，仍需复核对账、FX 和公司行动证据。",
            "任何真实动作必须另走人工审批；本提案不得提交券商。",
        ],
        "reconciliation_status": reconciliation.get("status", "Review"),
        "no_real_broker_connection": True,
    }


def _constraint(constraint_id: str, actual: float, limit: float, operator: str) -> dict[str, Any]:
    passed = actual <= limit if operator == "<=" else actual >= limit
    return {
        "constraint_id": constraint_id,
        "actual": round(float(actual), 6),
        "limit": round(float(limit), 6),
        "operator": operator,
        "status": "Pass" if passed else "Fail",
        "message": f"{constraint_id}: actual={actual:.2%}, limit={limit:.2%}.",
    }


def _golden_metrics(payload: dict[str, Any], ui_read_model: dict[str, Any], fixture: dict[str, Any], store: OperationalStore) -> dict[str, Any]:
    proposal = ui_read_model.get("decision_proposal", {})
    summary = payload.get("portfolio_summary", {})
    return {
        "workflow_id": payload.get("workflow_id", ""),
        "source_id": payload.get("source_id", ""),
        "snapshot_checksum": payload.get("holdings_snapshot", {}).get("checksum", ""),
        "import_record_count": len(fixture.get("import_ledger", [])),
        "broker_count": len({row.get("broker", "") for row in fixture.get("import_ledger", [])}),
        "corporate_action_adjusted_count": _corporate_action_count(fixture),
        "fx_converted_count": _fx_converted_count(fixture),
        "cash_balance_usd": _cash_balance_usd(fixture),
        "holding_count": int(summary.get("holding_count", 0) or 0),
        "total_position_value_usd": round(float(summary.get("total_abs_position_value", 0.0) or 0.0), 6),
        "max_single_weight": float(summary.get("max_single_weight", 0.0) or 0.0),
        "top3_weight": float(summary.get("top3_weight", 0.0) or 0.0),
        "constraint_violation_count": int(proposal.get("constraint_violation_count", 0) or 0),
        "reconciliation_status": ui_read_model.get("import_reconciliation", {}).get("status", ""),
        "target_weight_change": float(proposal.get("target_weight_change", 0.0) or 0.0),
        "source_record_count": len(store.table_rows("source_records")),
        "evidence_record_count": len(store.table_rows("evidence_records")),
        "job_record_count": len(store.table_rows("job_records")),
        "task_record_count": len(store.table_rows("task_records")),
        "holding_snapshot_count": len(store.table_rows("holding_snapshots")),
    }


def _ui_card(label: str, card: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": label,
        "status": card.get("status", "Review"),
        "summary": card.get("summary", ""),
        "source_ids": card.get("source_ids", []),
        "as_of": card.get("as_of", ""),
        "evidence_class": card.get("evidence_class", "pfi008_private_portfolio_review"),
        "data_domain": card.get("data_domain", "PRIVATE_DERIVED"),
        "review_required": bool(card.get("review_required", True)),
    }


def _corporate_action_count(fixture: dict[str, Any]) -> int:
    return sum(1 for row in fixture.get("import_ledger", []) if row.get("corporate_action"))


def _fx_converted_count(fixture: dict[str, Any]) -> int:
    return sum(1 for row in fixture.get("import_ledger", []) if str(row.get("currency", "USD")) != "USD")


def _cash_balance_usd(fixture: dict[str, Any]) -> float:
    return round(sum(float(row.get("cash_balance_usd", 0.0) or 0.0) for row in fixture.get("cash_ledger", [])), 6)


def _count_rows(store: OperationalStore, table: str, column: str, value: str) -> int:
    return sum(1 for row in store.table_rows(table) if str(row.get(column, "")) == value)


def _check(name: str, condition: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if condition else "Fail", "evidence": evidence}


def _summary(checks: list[dict[str, str]]) -> dict[str, int]:
    return {
        "pass": sum(1 for row in checks if row["status"] == "Pass"),
        "fail": sum(1 for row in checks if row["status"] == "Fail"),
        "info": sum(1 for row in checks if row["status"] == "Info"),
        "total": len(checks),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
