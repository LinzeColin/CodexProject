"""PFI v0.2.5 Stage 9.3 decision review and same-snapshot export contract.

The contract consumes only the redacted, immutable Phase 9.2 analysis snapshot.
It creates operational review suggestions, never trading instructions.  Every
suggestion requires an explicit human outcome and retains a SHA-256 chained
history.  HTML, PDF, CSV and Markdown exports are deterministic projections of
one export snapshot and carry the same snapshot identity.
"""

from __future__ import annotations

from copy import deepcopy
import base64
import csv
from html import escape
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Mapping

from pfi_os.application.analysis.stage9_reviewed_analysis import (
    validate_stage9_reviewed_analysis_pack,
)
from pfi_os.application.reports.contracts import canonical_hash, file_hash


VERSION = "v0.2.5"
STAGE = 9
PHASE = "9.3"
PHASE_ID = "V025-S9-P9.3"
TASK_IDS = ("S9-P3-T1", "S9-P3-T2", "S9-P3-T3", "S9-P3-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE9-WHOLE-REVIEW"
EXPORT_FORMATS = ("html", "pdf", "csv", "markdown")
REVIEW_OUTCOMES = ("accepted", "rejected", "deferred", "invalidated")
REVIEW_STATUSES = ("awaiting_human_review", *REVIEW_OUTCOMES)
EXPORT_FILENAMES = {
    "html": "pfi_v025_decision_review.html",
    "pdf": "pfi_v025_decision_review.pdf",
    "csv": "pfi_v025_decision_review.csv",
    "markdown": "pfi_v025_decision_review.md",
}
EXPORT_CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "pdf": "application/pdf",
    "csv": "text/csv; charset=utf-8",
    "markdown": "text/markdown; charset=utf-8",
}

PFI_ROOT = Path(__file__).resolve().parents[4]
ANALYSIS_SNAPSHOT_RELATIVE = Path(
    "config/reports/v025_stage9_reviewed_analysis_snapshot.json"
)
BUILDER_RELATIVE = Path(
    "src/pfi_os/application/decisions/decision_review.py"
)
EMBEDDED_DATA_RELATIVE = Path(
    "web/app/pages/reports/stage9DecisionReviewData.js"
)

_ALLOWED_TRANSITIONS = {
    "awaiting_human_review": REVIEW_OUTCOMES,
    "accepted": ("invalidated",),
    "deferred": ("accepted", "rejected", "invalidated"),
    "rejected": (),
    "invalidated": (),
}
_TRADE_PATTERN = re.compile(
    r"(?i)(place[_ -]?order|execute[_ -]?trade|buy[_ -]?order|sell[_ -]?order|自动交易已启用|自动下单已启用|直接下单)"
)
_FINANCIAL_VALUE_PATTERN = re.compile(
    r"\bCNY\s+-?[0-9]|\"(?:value|amount|financial_value)\"\s*:|\"[a-z0-9_]+_cny\"\s*:"
)


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _assert_redacted(label: str, payload: Mapping[str, Any]) -> None:
    if payload.get("contains_private_values") not in (None, False):
        raise ValueError(f"{label} contains private values")
    if payload.get("financial_values_emitted") not in (None, 0):
        raise ValueError(f"{label} emitted financial values")


def build_phase93_contract() -> dict[str, object]:
    return {
        "schema": "PFIV025Stage9Phase93ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "phase_name": "建议、复盘与导出",
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "risk_tier": "T3_FINANCIAL_DECISION_REVIEW_EXPORT",
        "current_phase_only": True,
        "phase_9_2_candidate_required": True,
        "human_review_required": True,
        "review_outcomes": list(REVIEW_OUTCOMES),
        "export_formats": list(EXPORT_FORMATS),
        "same_snapshot_export_required": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "deterministic_financial_advice_allowed": False,
        "financial_fixture_acceptance_allowed": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "stage_9_whole_stage_review_done": False,
        "stage_10_started": False,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def _event_hash(event: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_hash"}
    return canonical_hash(payload)


def _created_event(decision_id: str, observed_at: str) -> dict[str, Any]:
    event = {
        "event_id": f"{decision_id}-EVT-0001",
        "event_type": "created",
        "from_status": None,
        "to_status": "awaiting_human_review",
        "outcome": None,
        "actor_role": "system",
        "actor_ref": "phase_9_3_builder",
        "reason_zh": "由同一 Phase 9.2 分析快照生成，等待人工复核。",
        "observed_at": observed_at,
        "prior_event_hash": None,
    }
    event["event_hash"] = _event_hash(event)
    return event


def _analysis_maps(analysis: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    reports = {
        str(row["report_type"]): row
        for row in analysis["report_set"]
        if isinstance(row, Mapping)
    }
    reviews = {
        str(row["review_id"]): row
        for row in analysis["source_review_index"]
        if isinstance(row, Mapping)
    }
    return reports, reviews


def _decision_objects(
    analysis: Mapping[str, Any], *, observed_at: str
) -> list[dict[str, Any]]:
    reports, reviews = _analysis_maps(analysis)
    consumption = reports["consumption"]
    partition = consumption["calculable_components"][0]
    pending_count = int(partition["review_queue_record_count"])
    missing_review_ids = sorted(
        review_id
        for review_id, row in reviews.items()
        if row.get("status") != "ready"
    )
    missing_source_ids = sorted(
        str(reviews[review_id]["source_id"])
        for review_id in missing_review_ids
    )

    common = {
        "version": "1.0.0",
        "horizon": "next_human_review_session",
        "status": "awaiting_human_review",
        "human_review_required": True,
        "allowed_review_outcomes": list(REVIEW_OUTCOMES),
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "source_analysis_pack_hash": str(analysis["pack_hash"]),
    }
    queue_decision_id = "DEC-PFI-V025-REVIEW-QUEUE"
    source_decision_id = "DEC-PFI-V025-SOURCE-COMPLETENESS"
    decisions = [
        {
            **common,
            "decision_id": queue_decision_id,
            "action": "review_pending_transaction_classification",
            "action_label_zh": "人工复核待复核交易分类",
            "confidence_dimensions": [
                {
                    "dimension": "evidence_coverage",
                    "status": "partial",
                    "basis_refs": ["pfi-v025-consumption", "REVIEW-SRC-TRANSACTIONS-ALIPAY"],
                },
                {
                    "dimension": "model_validity",
                    "status": "structure_validated_ground_truth_missing",
                    "basis_refs": ["FORM-PFI-015", "FORM-PFI-020", "MOD-PFI-010"],
                },
                {
                    "dimension": "execution_safety",
                    "status": "review_only_no_trade_capability",
                    "basis_refs": [PHASE_ID],
                },
            ],
            "thesis": {
                "scope": "operational_review_only",
                "statement_zh": f"当前有 {pending_count:,} 条记录仍在待复核队列；先人工核对分类与退款/转账边界，再解释消费结构。",
                "evidence_refs": ["pfi-v025-consumption", "FORM-PFI-015", "FORM-PFI-020"],
            },
            "catalysts": [
                {
                    "catalyst_id": "CAT-QUEUE-REVIEW",
                    "statement_zh": "待复核记录减少且无静默丢弃时，可扩大消费报告的已验证覆盖。",
                    "review_route": "/ledger?tab=review",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "EVID-QUEUE-PARTITION",
                    "kind": "real_source_partition",
                    "statement_zh": f"真实来源分区中待复核记录为 {pending_count:,} 条，当前财务金额未进入公开决策对象。",
                    "source_refs": ["pfi-v025-consumption", "SRC-TRANSACTIONS-ALIPAY"],
                }
            ],
            "counter_evidence": [
                {
                    "counter_evidence_id": "COUNTER-QUEUE-CONTEXT",
                    "statement_zh": "队列数量不能证明分类准确性，且未标注 ground truth 时不能声明模型有效率。",
                    "effect": "blocks_accuracy_claim",
                    "review_route": "/reports/metric-drilldown?formula=FORM-PFI-020",
                },
                {
                    "counter_evidence_id": "COUNTER-QUEUE-STALE",
                    "statement_zh": "新导入、退款识别或人工重分类会改变当前队列与覆盖结论。",
                    "effect": "requires_snapshot_refresh",
                    "review_route": "/data/sources",
                },
            ],
            "invalidation_conditions": [
                {
                    "condition_id": "INVALIDATE-QUEUE-EMPTY",
                    "predicate": "review_queue_record_count_equals_zero",
                    "current_state": "not_met",
                    "review_route": "/ledger?tab=review",
                },
                {
                    "condition_id": "INVALIDATE-ANALYSIS-HASH-DRIFT",
                    "predicate": "source_analysis_pack_hash_changes",
                    "current_state": "not_met",
                    "review_route": "/reports",
                },
            ],
            "risks": [
                "待复核记录可能包含转账、退款或投资活动，不能直接解释为生活消费。",
                "缺少分类 labels 与样本外 ground truth，不能声明分类准确率。",
            ],
            "portfolio_effect": {
                "status": "not_calculable",
                "statement_zh": "该动作只影响分类复核与报告覆盖，不生成组合交易或金额影响。",
            },
            "model_versions": [
                {"model_id": "MOD-PFI-010", "version": "v0.2.5", "status": "partial_validated_with_blocked_components"},
                {"model_id": "FORM-PFI-015", "version": "1.0.0", "status": "validated_real_snapshot"},
                {"model_id": "FORM-PFI-020", "version": "1.0.0", "status": "validated_structure_only"},
            ],
            "source_ids": ["SRC-TRANSACTIONS-ALIPAY"],
            "review_route": "/ledger?tab=review",
            "review_history": [_created_event(queue_decision_id, observed_at)],
        },
        {
            **common,
            "decision_id": source_decision_id,
            "action": "complete_missing_financial_source_review",
            "action_label_zh": "补齐并复核关键财务来源",
            "confidence_dimensions": [
                {
                    "dimension": "evidence_coverage",
                    "status": "blocked_missing_required_sources",
                    "basis_refs": missing_review_ids,
                },
                {
                    "dimension": "model_validity",
                    "status": "blocked_for_full_financial_conclusion",
                    "basis_refs": ["FORM-PFI-016", "FORM-PFI-017", "FORM-PFI-018"],
                },
                {
                    "dimension": "execution_safety",
                    "status": "review_only_no_trade_capability",
                    "basis_refs": [PHASE_ID],
                },
            ],
            "thesis": {
                "scope": "data_completeness_review_only",
                "statement_zh": "账户余额、负债、持仓、价格、FX 与 Economic Event lineage 未全部 ready；先补齐来源，再解释净资产、现金或投资结果。",
                "evidence_refs": ["pfi-v025-net-worth", "pfi-v025-cash", "pfi-v025-investment", *missing_review_ids],
            },
            "catalysts": [
                {
                    "catalyst_id": "CAT-SOURCES-READY",
                    "statement_zh": "所有关键来源与 lineage 达到 ready 后，可重建完整度并重新评估报告状态。",
                    "review_route": "/data/sources",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "EVID-MISSING-SOURCE-SET",
                    "kind": "source_dependency_state",
                    "statement_zh": f"当前有 {len(missing_source_ids)} 个关键来源或 lineage 依赖未 ready。",
                    "source_refs": missing_source_ids,
                }
            ],
            "counter_evidence": [
                {
                    "counter_evidence_id": "COUNTER-TRANSACTIONS-READY",
                    "statement_zh": "交易来源已有真实覆盖，因此消费与现金流仍可保留 partial 的覆盖结论。",
                    "effect": "prevents_all_reports_blocked_claim",
                    "review_route": "/data/sources",
                },
                {
                    "counter_evidence_id": "COUNTER-SOURCE-STATE-DRIFT",
                    "statement_zh": "来源状态可能在新快照中改变，当前建议不得跨 snapshot 延用。",
                    "effect": "requires_snapshot_refresh",
                    "review_route": "/reports",
                },
            ],
            "invalidation_conditions": [
                {
                    "condition_id": "INVALIDATE-SOURCES-READY",
                    "predicate": "all_required_sources_and_lineage_ready",
                    "current_state": "not_met",
                    "review_route": "/data/sources",
                },
                {
                    "condition_id": "INVALIDATE-ANALYSIS-HASH-DRIFT",
                    "predicate": "source_analysis_pack_hash_changes",
                    "current_state": "not_met",
                    "review_route": "/reports",
                },
            ],
            "risks": [
                "来源未 ready 时强行解释净资产、现金或投资会制造假结论。",
                "持仓、价格与 FX 时间不一致会破坏估值和收益解释。",
            ],
            "portfolio_effect": {
                "status": "not_calculable",
                "statement_zh": "缺少余额、持仓、价格与 FX，组合影响保持不可计算且不生成交易动作。",
            },
            "model_versions": [
                {"model_id": "MOD-PFI-010", "version": "v0.2.5", "status": "partial_validated_with_blocked_components"},
                {"model_id": "FORM-PFI-016", "version": "1.0.0", "status": "blocked_missing_required_sources"},
                {"model_id": "FORM-PFI-017", "version": "1.0.0", "status": "blocked_missing_required_sources"},
                {"model_id": "FORM-PFI-018", "version": "1.0.0", "status": "blocked_insufficient_chain"},
            ],
            "source_ids": missing_source_ids,
            "review_route": "/data/sources",
            "review_history": [_created_event(source_decision_id, observed_at)],
        },
    ]
    return decisions


def _validate_review_history(decision: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    history = decision.get("review_history")
    if not isinstance(history, list) or not history:
        return ["review history is required"]
    expected_prior: str | None = None
    previous_status: str | None = None
    for index, event in enumerate(history):
        if not isinstance(event, Mapping):
            errors.append("review event must be an object")
            continue
        if event.get("prior_event_hash") != expected_prior:
            errors.append(f"review event {index + 1} prior hash mismatch")
        if event.get("event_hash") != _event_hash(event):
            errors.append(f"review event {index + 1} hash mismatch")
        if event.get("from_status") != previous_status:
            errors.append(f"review event {index + 1} from status mismatch")
        to_status = str(event.get("to_status") or "")
        if index == 0:
            if event.get("event_type") != "created" or to_status != "awaiting_human_review":
                errors.append("first review event must create awaiting_human_review")
        elif to_status not in _ALLOWED_TRANSITIONS.get(str(previous_status), ()):
            errors.append(f"invalid review transition: {previous_status}->{to_status}")
        expected_prior = str(event.get("event_hash") or "")
        previous_status = to_status
    if previous_status != decision.get("status"):
        errors.append("review history terminal status mismatch")
    return errors


def _validate_decision(decision: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "decision_id",
        "action",
        "horizon",
        "status",
        "confidence_dimensions",
        "thesis",
        "catalysts",
        "counter_evidence",
        "invalidation_conditions",
        "risks",
        "portfolio_effect",
        "model_versions",
        "source_ids",
        "review_history",
    )
    for key in required:
        if key not in decision or decision.get(key) in (None, "", []):
            errors.append(f"decision field missing: {key}")
    if decision.get("status") not in REVIEW_STATUSES:
        errors.append("invalid decision status")
    if decision.get("human_review_required") is not True:
        errors.append("human review must be required")
    if decision.get("automatic_trading_allowed") is not False:
        errors.append("automatic trading must remain forbidden")
    if decision.get("trade_execution_available") is not False:
        errors.append("trade execution capability must remain unavailable")
    if set(decision.get("allowed_review_outcomes") or []) != set(REVIEW_OUTCOMES):
        errors.append("review outcomes are incomplete")
    if not isinstance(decision.get("counter_evidence"), list) or not decision.get("counter_evidence"):
        errors.append("counter evidence is required")
    if not isinstance(decision.get("invalidation_conditions"), list) or not decision.get("invalidation_conditions"):
        errors.append("invalidation conditions are required")
    serialized = json.dumps(decision, ensure_ascii=False, sort_keys=True)
    if _TRADE_PATTERN.search(serialized):
        errors.append("decision exposes a trade execution instruction")
    if _FINANCIAL_VALUE_PATTERN.search(serialized):
        errors.append("decision contains a public financial value")
    errors.extend(_validate_review_history(decision))
    return errors


def apply_human_review(
    decision: Mapping[str, Any],
    *,
    outcome: str,
    reviewer_ref: str,
    reason_zh: str,
    observed_at: str,
) -> dict[str, Any]:
    """Append one valid human review event without performing the action itself."""

    current = deepcopy(dict(decision))
    existing_errors = _validate_decision(current)
    if existing_errors:
        raise ValueError("invalid decision before review: " + "; ".join(existing_errors))
    normalized_outcome = str(outcome or "").strip()
    current_status = str(current["status"])
    if normalized_outcome not in _ALLOWED_TRANSITIONS[current_status]:
        raise ValueError(f"invalid review transition: {current_status}->{normalized_outcome}")
    reviewer = str(reviewer_ref or "").strip()
    reason = str(reason_zh or "").strip()
    timestamp = str(observed_at or "").strip()
    if not reviewer or not reason or not timestamp:
        raise ValueError("reviewer_ref, reason_zh and observed_at are required")
    history = list(current["review_history"])
    prior_hash = str(history[-1]["event_hash"])
    event = {
        "event_id": f"{current['decision_id']}-EVT-{len(history) + 1:04d}",
        "event_type": "human_review",
        "from_status": current_status,
        "to_status": normalized_outcome,
        "outcome": normalized_outcome,
        "actor_role": "owner",
        "actor_ref": reviewer,
        "reason_zh": reason,
        "observed_at": timestamp,
        "prior_event_hash": prior_hash,
    }
    event["event_hash"] = _event_hash(event)
    current["status"] = normalized_outcome
    current["review_history"] = [*history, event]
    errors = _validate_decision(current)
    if errors:
        raise ValueError("invalid decision after review: " + "; ".join(errors))
    return current


def _export_snapshot(
    analysis: Mapping[str, Any],
    data_quality: Mapping[str, Any],
    decisions: list[dict[str, Any]],
    *,
    observed_at: str,
) -> dict[str, Any]:
    reports = [
        {
            "report_id": row["report_id"],
            "report_type": row["report_type"],
            "title_zh": row["title_zh"],
            "status": row["status"],
            "data_range": row["data_range"],
            "transaction_record_count": row["sample_counts"]["transaction_record_count"],
            "formula_ids": row["formula_ids"],
            "parameter_ids": row["parameter_ids"],
            "review_entry_ids": row["review_entry_ids"],
            "snapshot_hash": row["snapshot_hash"],
            "scope_explanation_zh": row["scope_explanation_zh"],
            "component_cards": deepcopy(row.get("component_cards", [])),
        }
        for row in analysis["report_set"]
    ]
    payload: dict[str, Any] = {
        "schema": "PFIV025Stage9Phase93ExportSnapshotV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "observed_at": observed_at,
        "source_analysis_pack_hash": analysis["pack_hash"],
        "source_analysis_snapshot_hash": file_hash(PFI_ROOT / ANALYSIS_SNAPSHOT_RELATIVE),
        "data_quality_report_hash": data_quality["snapshot_hash"],
        "data_quality_status": data_quality.get("status"),
        "report_count": len(reports),
        "report_statuses": {
            str(row["report_type"]): str(row["status"]) for row in reports
        },
        "reports": reports,
        "decision_count": len(decisions),
        "decisions": deepcopy(decisions),
        "hashes": {
            key: analysis["hashes"][key]
            for key in (
                "data_manifest_hash",
                "read_model_hash",
                "formula_registry_hash",
                "parameter_hash",
                "base_report_manifest_hash",
            )
        },
        "human_review_required": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    payload["snapshot_hash"] = canonical_hash(payload)
    return payload


def build_phase93_core(
    pfi_root: Path | str | None = None,
    *,
    observed_at: str,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    analysis = _json_object(root / ANALYSIS_SNAPSHOT_RELATIVE)
    gate = validate_stage9_reviewed_analysis_pack(analysis, pfi_root=root)
    if gate.get("status") != "pass":
        raise ValueError("Stage 9 reviewed analysis snapshot is not current and passing")
    if analysis.get("status") != "candidate_pass_pending_whole_stage_rereview":
        raise ValueError("Stage 9 reviewed analysis is not a candidate pass")
    data_quality = analysis["data_quality_report"]
    _assert_redacted("Stage 9 reviewed analysis", analysis)
    _assert_redacted("data quality report", data_quality)
    timestamp = str(observed_at or "").strip()
    if not timestamp:
        raise ValueError("observed_at is required")
    decisions = _decision_objects(analysis, observed_at=timestamp)
    decision_errors = [
        f"{row['decision_id']}: {error}"
        for row in decisions
        for error in _validate_decision(row)
    ]
    if decision_errors:
        raise ValueError("decision validation failed: " + "; ".join(decision_errors))
    export_snapshot = _export_snapshot(
        analysis, data_quality, decisions, observed_at=timestamp
    )
    core: dict[str, Any] = {
        "schema": "PFIV025Stage9Phase93DecisionCoreV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "risk_tier": "T3_FINANCIAL_DECISION_REVIEW_EXPORT",
        "status": "candidate_pass",
        "observed_at": timestamp,
        "source_analysis_pack_hash": analysis["pack_hash"],
        "source_analysis_snapshot_hash": file_hash(root / ANALYSIS_SNAPSHOT_RELATIVE),
        "data_quality_report_hash": data_quality["snapshot_hash"],
        "decision_objects": decisions,
        "decision_count": len(decisions),
        "review_outcomes": list(REVIEW_OUTCOMES),
        "export_snapshot": export_snapshot,
        "export_snapshot_hash": export_snapshot["snapshot_hash"],
        "export_formats": list(EXPORT_FORMATS),
        "decision_builder_hash": file_hash(root / BUILDER_RELATIVE),
        "human_review_required": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "stage_9_whole_stage_review_done": False,
        "stage_10_started": False,
    }
    core["core_hash"] = canonical_hash(core)
    return core


def _markdown(snapshot: Mapping[str, Any]) -> str:
    lines = [
        "# PFI v0.2.5 Decision Review Export",
        "",
        f"- Snapshot: `{snapshot['snapshot_hash']}`",
        f"- Analysis pack: `{snapshot['source_analysis_pack_hash']}`",
        f"- Human review required: `{str(snapshot['human_review_required']).lower()}`",
        "- Automatic trading: `forbidden`",
        "",
        "## Report truth",
        "",
        "| Report | Status | Range | Records |",
        "|---|---|---|---:|",
    ]
    for report in snapshot["reports"]:
        data_range = report["data_range"]
        lines.append(
            f"| {report['title_zh']} | {report['status']} | {data_range['start']} to {data_range['end']} | {report['transaction_record_count']} |"
        )
    components = next(
        (report.get("component_cards", []) for report in snapshot["reports"] if report.get("report_type") == "consumption"),
        [],
    )
    lines.extend(
        [
            "",
            "## Consumption and investment activity components",
            "",
            "| Component | Status | Formula | Scope |",
            "|---|---|---|---|",
            *[
                f"| {row['label_zh']} | {row['status_zh']} | {row['formula_id']} | {row['scope_zh']} |"
                for row in components
            ],
            "",
            "Investment activity is not net-worth loss. Private financial values are not persisted in this export.",
        ]
    )
    for decision in snapshot["decisions"]:
        lines.extend(
            [
                "",
                f"## {decision['action_label_zh']}",
                "",
                f"- Decision ID: `{decision['decision_id']}`",
                f"- Status: `{decision['status']}`",
                f"- Horizon: `{decision['horizon']}`",
                f"- Thesis: {decision['thesis']['statement_zh']}",
                f"- Portfolio effect: {decision['portfolio_effect']['statement_zh']}",
                "- Counter evidence:",
                *[f"  - {row['statement_zh']}" for row in decision["counter_evidence"]],
                "- Invalidation conditions:",
                *[f"  - `{row['predicate']}` ({row['current_state']})" for row in decision["invalidation_conditions"]],
                "- Risks:",
                *[f"  - {risk}" for risk in decision["risks"]],
            ]
        )
    lines.extend(
        [
            "",
            "## Canonical snapshot JSON",
            "",
            "```json",
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _html(snapshot: Mapping[str, Any]) -> str:
    report_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['title_zh']))}</td>"
        f"<td>{escape(str(row['status']))}</td>"
        f"<td>{escape(str(row['data_range']['start']))} - {escape(str(row['data_range']['end']))}</td>"
        f"<td>{int(row['transaction_record_count'])}</td>"
        "</tr>"
        for row in snapshot["reports"]
    )
    components = next(
        (report.get("component_cards", []) for report in snapshot["reports"] if report.get("report_type") == "consumption"),
        [],
    )
    component_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['label_zh']))}</td>"
        f"<td>{escape(str(row['status_zh']))}</td>"
        f"<td>{escape(str(row['formula_id']))}</td>"
        f"<td>{escape(str(row['scope_zh']))}</td>"
        "</tr>"
        for row in components
    )
    decisions = []
    for row in snapshot["decisions"]:
        counters = "".join(
            f"<li>{escape(str(item['statement_zh']))}</li>"
            for item in row["counter_evidence"]
        )
        conditions = "".join(
            f"<li><code>{escape(str(item['predicate']))}</code> - {escape(str(item['current_state']))}</li>"
            for item in row["invalidation_conditions"]
        )
        decisions.append(
            "<article>"
            f"<h2>{escape(str(row['action_label_zh']))}</h2>"
            f"<p><strong>{escape(str(row['status']))}</strong> | {escape(str(row['horizon']))}</p>"
            f"<p>{escape(str(row['thesis']['statement_zh']))}</p>"
            "<h3>Counter evidence</h3>"
            f"<ul>{counters}</ul>"
            "<h3>Invalidation conditions</h3>"
            f"<ul>{conditions}</ul>"
            "</article>"
        )
    snapshot_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    return (
        "<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"pfi-export-snapshot-hash\" content=\"{escape(str(snapshot['snapshot_hash']))}\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>PFI v0.2.5 Decision Review</title>"
        "<style>body{font:15px/1.65 system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#17212b}"
        "table{width:100%;border-collapse:collapse}th,td{padding:10px;border:1px solid #ccd4dc;text-align:left}"
        "article{margin:28px 0;padding:20px;border:1px solid #ccd4dc;border-radius:14px}code{overflow-wrap:anywhere}</style>"
        "</head><body><h1>PFI v0.2.5 Decision Review Export</h1>"
        f"<p>Snapshot: <code>{escape(str(snapshot['snapshot_hash']))}</code></p>"
        "<p>Human review is required. Automatic trading and order execution are unavailable.</p>"
        "<h2>Report truth</h2><table><thead><tr><th>Report</th><th>Status</th><th>Range</th><th>Records</th></tr></thead>"
        f"<tbody>{report_rows}</tbody></table>"
        "<h2>Consumption and investment activity components</h2>"
        "<p>Investment activity is not net-worth loss. Private financial values are not persisted.</p>"
        f"<table><thead><tr><th>Component</th><th>Status</th><th>Formula</th><th>Scope</th></tr></thead><tbody>{component_rows}</tbody></table>"
        f"{''.join(decisions)}"
        f"<script type=\"application/json\" id=\"pfi-export-snapshot\">{escape(snapshot_json)}</script>"
        "</body></html>\n"
    )


def _csv_bytes(snapshot: Mapping[str, Any]) -> bytes:
    stream = io.StringIO(newline="")
    columns = [
        "snapshot_hash",
        "record_type",
        "record_id",
        "status",
        "action",
        "horizon",
        "statement_zh",
        "evidence_json",
        "counter_evidence_json",
        "invalidation_conditions_json",
        "risks_json",
        "source_ids_json",
        "model_versions_json",
        "source_analysis_pack_hash",
    ]
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()

    def write_row(row: Mapping[str, Any]) -> None:
        safe = {
            key: (f"'{value}" if isinstance(value, str) and re.match(r"^[=+\-@\t\r]", value) else value)
            for key, value in row.items()
        }
        writer.writerow(safe)

    for report in snapshot["reports"]:
        write_row(
            {
                "snapshot_hash": snapshot["snapshot_hash"],
                "record_type": "report",
                "record_id": report["report_id"],
                "status": report["status"],
                "statement_zh": report["scope_explanation_zh"],
                "evidence_json": json.dumps(
                    {
                        "data_range": report["data_range"],
                        "transaction_record_count": report["transaction_record_count"],
                        "formula_ids": report["formula_ids"],
                        "parameter_ids": report["parameter_ids"],
                        "snapshot_hash": report["snapshot_hash"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "source_analysis_pack_hash": snapshot["source_analysis_pack_hash"],
            }
        )
        for component in report.get("component_cards", []):
            write_row(
                {
                    "snapshot_hash": snapshot["snapshot_hash"],
                    "record_type": "component",
                    "record_id": component["metric_id"],
                    "status": component["status"],
                    "action": "human_review_only",
                    "statement_zh": f"{component['label_zh']}：{component['scope_zh']}",
                    "evidence_json": json.dumps(component, ensure_ascii=False, sort_keys=True),
                    "source_analysis_pack_hash": snapshot["source_analysis_pack_hash"],
                }
            )
    for decision in snapshot["decisions"]:
        write_row(
            {
                "snapshot_hash": snapshot["snapshot_hash"],
                "record_type": "decision",
                "record_id": decision["decision_id"],
                "status": decision["status"],
                "action": decision["action"],
                "horizon": decision["horizon"],
                "statement_zh": decision["thesis"]["statement_zh"],
                "evidence_json": json.dumps(decision["evidence"], ensure_ascii=False, sort_keys=True),
                "counter_evidence_json": json.dumps(decision["counter_evidence"], ensure_ascii=False, sort_keys=True),
                "invalidation_conditions_json": json.dumps(decision["invalidation_conditions"], ensure_ascii=False, sort_keys=True),
                "risks_json": json.dumps(decision["risks"], ensure_ascii=False, sort_keys=True),
                "source_ids_json": json.dumps(decision["source_ids"], ensure_ascii=False, sort_keys=True),
                "model_versions_json": json.dumps(decision["model_versions"], ensure_ascii=False, sort_keys=True),
                "source_analysis_pack_hash": snapshot["source_analysis_pack_hash"],
            }
        )
    return stream.getvalue().encode("utf-8")


def _pdf_bytes(snapshot: Mapping[str, Any]) -> bytes:
    """Render a deterministic, CJK-capable PDF through ReportLab when invoked."""

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover - exercised by product builder runtime
        raise RuntimeError("ReportLab is required only for the PDF export build step") from exc

    font_name = "PFIPhase93CJK"
    font_candidates = (
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    )
    try:
        pdfmetrics.getFont(font_name)
    except KeyError:
        registered = False
        for font_path in font_candidates:
            if not font_path.is_file():
                continue
            try:
                pdfmetrics.registerFont(
                    TTFont(font_name, str(font_path), subfontIndex=0)
                )
            except Exception:  # ReportLab rejects some macOS TTC outline types.
                continue
            registered = True
            break
        if not registered:
            raise RuntimeError("a local embeddable CJK font is required for PDF export")
    buffer = io.BytesIO()
    width, height = A4
    document = canvas.Canvas(
        buffer,
        pagesize=A4,
        pageCompression=0,
        invariant=1,
    )
    document.setTitle("PFI v0.2.5 Decision Review Export")
    document.setAuthor("PFI")
    document.setSubject(str(snapshot["snapshot_hash"]))
    document.setKeywords(
        f"PFI v0.2.5;{snapshot['snapshot_hash']};human-review-required;no-automatic-trading"
    )
    margin = 44
    y = height - margin
    page_number = 1

    def footer() -> None:
        document.setFont(font_name, 8)
        document.setFillColorRGB(0.35, 0.40, 0.45)
        document.drawString(margin, 22, f"PFI v0.2.5 | Page {page_number}")
        document.drawRightString(width - margin, 22, "Human review required | No automatic trading")
        document.setFillColorRGB(0.08, 0.12, 0.17)

    def next_page() -> None:
        nonlocal y, page_number
        footer()
        document.showPage()
        page_number += 1
        y = height - margin

    def lines(text: str, width_chars: int = 72) -> list[str]:
        raw = str(text).replace("\n", " ").strip()
        if not raw:
            return [""]
        return [raw[index:index + width_chars] for index in range(0, len(raw), width_chars)]

    def paragraph(text: str, *, size: int = 9, leading: int = 13, indent: int = 0) -> None:
        nonlocal y
        document.setFont(font_name, size)
        for line in lines(text, 78 - indent):
            if y < 52:
                next_page()
                document.setFont(font_name, size)
            document.drawString(margin + indent * 4, y, line)
            y -= leading

    def hash_identity_line(label: str, value: object) -> None:
        """Keep the full identity hash on one selectable line."""
        nonlocal y
        text = f"{label}: {value}"
        size = 6.5
        available = width - (2 * margin)
        while pdfmetrics.stringWidth(text, "Courier", size) > available and size > 5:
            size -= 0.25
        document.setFont("Courier", size)
        document.drawString(margin, y, text)
        y -= 10

    document.setFillColorRGB(0.08, 0.12, 0.17)
    document.setFont(font_name, 18)
    document.drawString(margin, y, "PFI v0.2.5 决策复盘导出")
    y -= 28
    hash_identity_line("Snapshot", snapshot["snapshot_hash"])
    hash_identity_line("Analysis pack", snapshot["source_analysis_pack_hash"])
    paragraph("人工复核必需；自动交易、直接下单和交易执行能力均不可用。", size=10, leading=15)
    y -= 6
    document.setFont(font_name, 13)
    document.drawString(margin, y, "报告真值")
    y -= 20
    for report in snapshot["reports"]:
        paragraph(
            f"{report['title_zh']} | {report['status']} | {report['data_range']['start']} 至 {report['data_range']['end']} | {report['transaction_record_count']} 条记录",
            size=9,
        )
    components = next(
        (report.get("component_cards", []) for report in snapshot["reports"] if report.get("report_type") == "consumption"),
        [],
    )
    y -= 6
    document.setFont(font_name, 13)
    document.drawString(margin, y, "四项活动组件")
    y -= 20
    for component in components:
        paragraph(
            f"{component['label_zh']} | {component['status_zh']} | {component['formula_id']} | {component['scope_zh']}",
            size=9,
        )
    paragraph("投资活动不等于净资产损失；本导出不持久化私有财务数值。", size=9)
    for decision in snapshot["decisions"]:
        y -= 8
        if y < 90:
            next_page()
        document.setFont(font_name, 13)
        document.drawString(margin, y, str(decision["action_label_zh"]))
        y -= 19
        paragraph(f"ID: {decision['decision_id']} | 状态: {decision['status']} | 期限: {decision['horizon']}")
        paragraph(f"依据: {decision['thesis']['statement_zh']}")
        paragraph(f"组合影响: {decision['portfolio_effect']['statement_zh']}")
        paragraph("反方证据:")
        for item in decision["counter_evidence"]:
            paragraph(f"- {item['statement_zh']}", indent=2)
        paragraph("失效条件:")
        for item in decision["invalidation_conditions"]:
            paragraph(f"- {item['predicate']} ({item['current_state']})", indent=2)
        paragraph("风险:")
        for item in decision["risks"]:
            paragraph(f"- {item}", indent=2)
    footer()
    document.save()
    return buffer.getvalue()


def render_phase93_exports(snapshot: Mapping[str, Any]) -> dict[str, bytes]:
    if snapshot.get("snapshot_hash") != canonical_hash(
        {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    ):
        raise ValueError("export snapshot hash is invalid")
    return {
        "html": _html(snapshot).encode("utf-8"),
        "pdf": _pdf_bytes(snapshot),
        "csv": _csv_bytes(snapshot),
        "markdown": _markdown(snapshot).encode("utf-8"),
    }


def _export_manifest(
    exports: Mapping[str, bytes], *, snapshot_hash: str
) -> dict[str, Any]:
    if set(exports) != set(EXPORT_FORMATS):
        raise ValueError("all four export formats are required")
    files = [
        {
            "format": export_format,
            "filename": EXPORT_FILENAMES[export_format],
            "content_type": EXPORT_CONTENT_TYPES[export_format],
            "byte_size": len(exports[export_format]),
            "sha256": _sha_bytes(exports[export_format]),
            "source_snapshot_hash": snapshot_hash,
        }
        for export_format in EXPORT_FORMATS
    ]
    payload: dict[str, Any] = {
        "schema": "PFIV025Stage9Phase93ExportManifestV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "source_snapshot_hash": snapshot_hash,
        "format_count": len(files),
        "formats": list(EXPORT_FORMATS),
        "files": files,
        "cross_format_same_snapshot": True,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    payload["manifest_hash"] = canonical_hash(payload)
    return payload


def _embedded_export_assets(root: Path) -> dict[str, bytes]:
    """Load the exact export bytes served by the generated Stage 9.3 UI asset."""

    text = (root / EMBEDDED_DATA_RELATIVE).read_text(encoding="utf-8")
    marker = "  const data = "
    start = text.find(marker)
    if start < 0:
        raise ValueError("embedded Stage 9.3 data marker is missing")
    start += len(marker)
    end = text.find(";\n", start)
    if end < 0:
        raise ValueError("embedded Stage 9.3 data payload is malformed")
    payload = json.loads(text[start:end])
    assets = payload.get("assetsBase64") if isinstance(payload, Mapping) else None
    if not isinstance(assets, Mapping) or set(assets) != set(EXPORT_FORMATS):
        raise ValueError("embedded Stage 9.3 export asset set differs")
    decoded: dict[str, bytes] = {}
    for export_format in EXPORT_FORMATS:
        value = assets.get(export_format)
        if not isinstance(value, str):
            raise ValueError(f"embedded export asset is invalid: {export_format}")
        try:
            decoded[export_format] = base64.b64decode(value, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError(
                f"embedded export asset is not valid base64: {export_format}"
            ) from exc
    return decoded


def _deterministic_export_assets(
    root: Path,
    rebuilt: Mapping[str, Any],
    supplied: Mapping[str, bytes] | None,
) -> dict[str, bytes]:
    if supplied is not None:
        if set(supplied) != set(EXPORT_FORMATS):
            raise ValueError("supplied export asset set differs")
        if any(not isinstance(supplied[key], bytes) for key in EXPORT_FORMATS):
            raise ValueError("supplied export assets must be bytes")
        return {key: supplied[key] for key in EXPORT_FORMATS}
    try:
        return render_phase93_exports(rebuilt["export_snapshot"])
    except RuntimeError as exc:
        if "ReportLab is required only for the PDF export build step" not in str(exc):
            raise
        return _embedded_export_assets(root)


def _ui_contract(
    core: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    decisions = [
        {
            "decision_id": row["decision_id"],
            "action": row["action"],
            "action_label_zh": row["action_label_zh"],
            "horizon": row["horizon"],
            "status": row["status"],
            "confidence_dimensions": row["confidence_dimensions"],
            "thesis": row["thesis"],
            "catalysts": row["catalysts"],
            "evidence": row["evidence"],
            "counter_evidence": row["counter_evidence"],
            "invalidation_conditions": row["invalidation_conditions"],
            "risks": row["risks"],
            "portfolio_effect": row["portfolio_effect"],
            "model_versions": row["model_versions"],
            "source_ids": row["source_ids"],
            "human_review_required": row["human_review_required"],
            "allowed_review_outcomes": row["allowed_review_outcomes"],
            "review_route": row["review_route"],
            "review_history": row["review_history"],
            "automatic_trading_allowed": False,
            "trade_execution_available": False,
        }
        for row in core["decision_objects"]
    ]
    return {
        "schema": "PFIV025Stage9Phase93UIContractV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "title_zh": "建议、反方证据与人工复核",
        "subtitle_zh": "建议只用于数据与报告复核；接受不触发交易，任何格式导出都绑定同一报告快照。",
        "decision_count": len(decisions),
        "decision_cards": decisions,
        "review_outcomes": list(REVIEW_OUTCOMES),
        "transition_map": {
            key: list(value) for key, value in _ALLOWED_TRANSITIONS.items()
        },
        "export_snapshot_hash": core["export_snapshot_hash"],
        "source_analysis_pack_hash": core["source_analysis_pack_hash"],
        "export_manifest_hash": manifest["manifest_hash"],
        "export_cards": deepcopy(manifest["files"]),
        "export_format_count": manifest["format_count"],
        "same_snapshot_export": manifest["cross_format_same_snapshot"],
        "human_review_required": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "stage_9_whole_stage_review_done": False,
    }


def assemble_phase93_decision_pack(
    core: Mapping[str, Any], exports: Mapping[str, bytes]
) -> dict[str, Any]:
    expected_core_hash = canonical_hash(
        {key: value for key, value in core.items() if key != "core_hash"}
    )
    if core.get("core_hash") != expected_core_hash:
        raise ValueError("Phase 9.3 core hash is invalid")
    manifest = _export_manifest(
        exports, snapshot_hash=str(core["export_snapshot_hash"])
    )
    pack = {
        **deepcopy(dict(core)),
        "schema": "PFIV025Stage9Phase93DecisionPackV1",
        "core_schema": core["schema"],
        "export_manifest": manifest,
        "ui_contract": _ui_contract(core, manifest),
    }
    pack["pack_hash"] = canonical_hash(pack)
    return pack


def _verify_export_files(
    pack: Mapping[str, Any], export_dir: Path
) -> list[str]:
    errors: list[str] = []
    manifest = pack.get("export_manifest")
    if not isinstance(manifest, Mapping):
        return ["export manifest is missing"]
    snapshot_hash = str(pack.get("export_snapshot_hash") or "")
    for entry in manifest.get("files", []):
        if not isinstance(entry, Mapping):
            errors.append("export manifest entry must be an object")
            continue
        path = export_dir / str(entry.get("filename") or "")
        if not path.is_file():
            errors.append(f"export file missing: {path.name}")
            continue
        payload = path.read_bytes()
        if _sha_bytes(payload) != entry.get("sha256"):
            errors.append(f"export hash mismatch: {path.name}")
        if len(payload) != entry.get("byte_size"):
            errors.append(f"export size mismatch: {path.name}")
        if entry.get("source_snapshot_hash") != snapshot_hash:
            errors.append(f"export snapshot mismatch: {path.name}")
    return errors


def validate_phase93_decision_pack(
    pack: Mapping[str, Any],
    *,
    pfi_root: Path | str | None = None,
    export_dir: Path | str | None = None,
    expected_exports: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    root = Path(pfi_root).expanduser().resolve() if pfi_root is not None else PFI_ROOT
    errors: list[str] = []
    observed_at = pack.get("observed_at")
    rebuilt: dict[str, Any] | None = None
    if not isinstance(observed_at, str) or not observed_at:
        errors.append("observed_at is required")
    else:
        try:
            rebuilt = build_phase93_core(root, observed_at=observed_at)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"current-input core rebuild failed: {type(exc).__name__}")
    if rebuilt is not None:
        expected_pack_keys = set(rebuilt) | {
            "schema",
            "core_schema",
            "export_manifest",
            "ui_contract",
            "pack_hash",
        }
        if set(pack) != expected_pack_keys:
            errors.append("Phase 9.3 pack fields differ from deterministic contract")
        if pack.get("schema") != "PFIV025Stage9Phase93DecisionPackV1":
            errors.append("Phase 9.3 pack schema is invalid")
        for key, value in rebuilt.items():
            if key == "schema":
                if pack.get("core_schema") != value:
                    errors.append("Phase 9.3 core schema differs from current input")
                continue
            if pack.get(key) != value:
                errors.append(f"Phase 9.3 core differs from current input: {key}")
    decisions = pack.get("decision_objects")
    if not isinstance(decisions, list) or len(decisions) != 2:
        decisions = []
        errors.append("exactly two review-only decision objects are required")
    for decision in decisions:
        if not isinstance(decision, Mapping):
            errors.append("decision object must be a mapping")
            continue
        errors.extend(
            f"{decision.get('decision_id', 'unknown')}: {error}"
            for error in _validate_decision(decision)
        )
    manifest = pack.get("export_manifest")
    files = manifest.get("files") if isinstance(manifest, Mapping) else None
    if (
        not isinstance(files, list)
        or len(files) != 4
        or {str(row.get("format")) for row in files if isinstance(row, Mapping)}
        != set(EXPORT_FORMATS)
    ):
        errors.append("four-format export manifest is incomplete")
    elif any(
        row.get("source_snapshot_hash") != pack.get("export_snapshot_hash")
        for row in files
        if isinstance(row, Mapping)
    ):
        errors.append("export formats do not share one snapshot")
    if isinstance(manifest, Mapping):
        expected_manifest_keys = {
            "schema",
            "version",
            "phase_id",
            "source_snapshot_hash",
            "format_count",
            "formats",
            "files",
            "cross_format_same_snapshot",
            "financial_values_emitted",
            "contains_private_values",
            "manifest_hash",
        }
        if set(manifest) != expected_manifest_keys:
            errors.append("export manifest fields differ from deterministic contract")
        expected_manifest_metadata = {
            "schema": "PFIV025Stage9Phase93ExportManifestV1",
            "version": VERSION,
            "phase_id": PHASE_ID,
            "source_snapshot_hash": pack.get("export_snapshot_hash"),
            "format_count": len(EXPORT_FORMATS),
            "formats": list(EXPORT_FORMATS),
            "cross_format_same_snapshot": True,
            "financial_values_emitted": 0,
            "contains_private_values": False,
        }
        for key, value in expected_manifest_metadata.items():
            if manifest.get(key) != value:
                errors.append(f"export manifest metadata differs: {key}")
        if isinstance(files, list):
            expected_file_keys = {
                "format",
                "filename",
                "content_type",
                "byte_size",
                "sha256",
                "source_snapshot_hash",
            }
            by_format = {
                str(row.get("format")): row
                for row in files
                if isinstance(row, Mapping)
            }
            for export_format in EXPORT_FORMATS:
                row = by_format.get(export_format)
                if row is None:
                    continue
                if set(row) != expected_file_keys:
                    errors.append(f"export file metadata fields differ: {export_format}")
                if row.get("filename") != EXPORT_FILENAMES[export_format]:
                    errors.append(f"export filename differs: {export_format}")
                if row.get("content_type") != EXPORT_CONTENT_TYPES[export_format]:
                    errors.append(f"export content type differs: {export_format}")
                if not isinstance(row.get("byte_size"), int) or int(row["byte_size"]) <= 0:
                    errors.append(f"export byte size is invalid: {export_format}")
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("sha256") or "")):
                    errors.append(f"export hash format is invalid: {export_format}")
        if rebuilt is not None:
            try:
                deterministic_exports = _deterministic_export_assets(
                    root, rebuilt, expected_exports
                )
                expected_manifest = _export_manifest(
                    deterministic_exports,
                    snapshot_hash=str(rebuilt["export_snapshot_hash"]),
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(
                    "deterministic export manifest rebuild failed: "
                    f"{type(exc).__name__}"
                )
            else:
                if manifest != expected_manifest:
                    errors.append(
                        "export manifest differs from deterministic export bytes"
                    )
        manifest_body = {
            key: value for key, value in manifest.items() if key != "manifest_hash"
        }
        if manifest.get("manifest_hash") != canonical_hash(manifest_body):
            errors.append("export manifest hash is invalid")
        if rebuilt is not None and isinstance(manifest.get("manifest_hash"), str):
            expected_ui = _ui_contract(rebuilt, manifest)
            if pack.get("ui_contract") != expected_ui:
                errors.append("UI contract differs from deterministic current input")
    pack_body = {key: value for key, value in pack.items() if key != "pack_hash"}
    if pack.get("pack_hash") != canonical_hash(pack_body):
        errors.append("Phase 9.3 pack hash is invalid")
    if export_dir is not None:
        errors.extend(_verify_export_files(pack, Path(export_dir)))
    if pack.get("human_review_required") is not True:
        errors.append("human review is not required")
    if pack.get("automatic_trading_allowed") is not False:
        errors.append("automatic trading is not forbidden")
    if pack.get("trade_execution_available") is not False:
        errors.append("trade execution capability is exposed")
    if pack.get("financial_values_emitted") != 0:
        errors.append("financial values were emitted")
    if pack.get("contains_private_values") is not False:
        errors.append("private values were emitted")
    if pack.get("stage_9_whole_stage_review_done") is not False:
        errors.append("Stage 9 whole-stage review scope leak")
    serialized = json.dumps(pack, ensure_ascii=False, sort_keys=True)
    if _TRADE_PATTERN.search(serialized):
        errors.append("pack exposes a trade execution instruction")
    if _FINANCIAL_VALUE_PATTERN.search(serialized):
        errors.append("pack contains a public financial value")
    return {
        "schema": "PFIV025Stage9Phase93DecisionValidationV1",
        "phase_id": PHASE_ID,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "decision_count": len(decisions),
        "counter_evidence_count": sum(
            len(row.get("counter_evidence") or []) for row in decisions
        ),
        "invalidation_condition_count": sum(
            len(row.get("invalidation_conditions") or []) for row in decisions
        ),
        "export_format_count": len(files) if isinstance(files, list) else 0,
        "cross_format_same_snapshot": not any(
            "snapshot" in error for error in errors
        ),
        "automatic_trading_allowed": bool(pack.get("automatic_trading_allowed")),
        "trade_execution_available": bool(pack.get("trade_execution_available")),
        "financial_values_emitted": int(pack.get("financial_values_emitted") or 0),
        "contains_private_values": bool(pack.get("contains_private_values")),
    }


def export_assets_base64(exports: Mapping[str, bytes]) -> dict[str, str]:
    """Return stable browser-embeddable assets for the generated UI module."""

    return {
        export_format: base64.b64encode(exports[export_format]).decode("ascii")
        for export_format in EXPORT_FORMATS
    }
