from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.research_policy_workflow import build_research_policy_workflow, record_research_policy_workflow
from pfi_os.policy import create_policy_opportunity


PFI007_RESEARCH_POLICY_ACCEPTANCE_SCHEMA = "PFI007ResearchPolicyVerticalAcceptanceV1"
PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA = "PFI007ResearchPolicyUIReadModelV1"
PFI007_GOLDEN_SOURCE_ID = "src-pfi007-research-policy-golden-2026-06-19"
PFI007_GOLDEN_AS_OF = "2026-06-19"


def build_pfi007_research_policy_golden_fixture() -> dict[str, Any]:
    official = create_policy_opportunity(
        published_date="2026-06-18",
        title="Official AI compute grant",
        source_name="Department of Industry",
        source_type="Government",
        source_url="https://example.gov/ai-compute-grant",
        evidence_path="docs/evidence/policy/official-ai-compute-grant.md",
        jurisdiction="AU",
        policy_level="National",
        opportunity_type="IndustrySupport",
        sectors="AI, Semiconductor",
        affected_entities="AI infrastructure suppliers",
        impact_summary="Official grant may affect AI compute supply-chain demand.",
        required_action="Review eligibility and deadline.",
        authority_score=95,
        relevance_score=85,
        urgency_score=80,
        feasibility_score=70,
        review_status="Reviewed",
    )
    news = create_policy_opportunity(
        published_date="2026-06-17",
        title="News summary of proposed tax setting",
        source_name="News Desk",
        source_type="News",
        source_url="https://example.com/tax-summary",
        opportunity_type="Tax",
        sectors="Software",
        affected_entities="Software companies",
        impact_summary="News summary requires official confirmation before reuse.",
        required_action="Find official source before action.",
        authority_score=70,
        relevance_score=80,
        urgency_score=60,
        feasibility_score=50,
        review_status="Reviewed",
    )
    for row, policy_id in (
        (official, "policy-pfi007-official-ai-compute-grant"),
        (news, "policy-pfi007-news-tax-summary"),
    ):
        row["policy_id"] = policy_id
        row["created_at"] = "2026-06-19T00:00:00"
        row["updated_at"] = "2026-06-19T00:00:00"
    return {
        "schema": "PFI007ResearchPolicyGoldenFixtureV1",
        "source_id": PFI007_GOLDEN_SOURCE_ID,
        "as_of": PFI007_GOLDEN_AS_OF,
        "opportunities": [official, news],
        "report_decision_payload": {
            "schema": "PFIOSReportDecisionSupportIndexV1",
            "record_count": 1,
            "records": [
                {
                    "run": "RunMetadata_20260619",
                    "date_folder": "2026-06-19",
                    "strategy_id": "ma_crossover",
                    "symbol": "AAPL",
                    "market": "US",
                    "report_readiness": "NeedsMoreEvidence",
                    "critical_missing_evidence": "数据质量状态; 多源交叉校验; walk-forward 验证",
                    "metadata_path": "reports/RunMetadata_20260619.json",
                    "linked_report_path": "reports/BacktestReport_20260619.docx",
                }
            ],
        },
        "expected": {
            "opportunity_count": 2,
            "authoritative_source_records": 1,
            "report_gap_task_minimum": 3,
            "human_review_required": True,
            "target_weight_change": 0.0,
        },
    }


def build_pfi007_research_policy_ui_read_model(payload: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    policy = payload.get("policy_radar", {})
    report_gaps = payload.get("report_gap_tasks", {})
    decision = payload.get("decision", {})
    return {
        "schema": PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA,
        "workspace": "research",
        "workspace_label": "研究",
        "primary_route": "research",
        "primary_feature_view": "research_policy_slice",
        "secondary_feature_views": ["citation_locator", "report_manifest", "policy"],
        "title": "研究与政策垂直切片",
        "summary": "统一展示政策权威来源、研究证据缺口、引用定位和报告清单。",
        "cards": [_ui_card(card) for card in payload.get("cards", [])],
        "citation_locator": _citation_locator(policy, report_gaps),
        "report_manifest": _report_manifest(report_gaps),
        "review_queue": [
            {
                "queue_id": "policy_authority_review",
                "label": "政策权威来源复核",
                "status": policy.get("runtime_summary", {}).get("status", "Review"),
                "action": "确认官方、监管、政府或交易所来源后再复用",
                "human_review_required": True,
            },
            {
                "queue_id": "report_evidence_gap_review",
                "label": "报告证据缺口复核",
                "status": "Review" if int(report_gaps.get("task_count", 0) or 0) else "Pass",
                "action": "按 manifest 补齐数据质量、多源校验和 walk-forward 证据",
                "human_review_required": True,
            },
        ],
        "decision": {
            "decision_id": decision.get("decision_id", ""),
            "status": decision.get("status", ""),
            "target_weight_change": float(decision.get("target_weight_change", 0.0) or 0.0),
            "confidence": float(decision.get("confidence", 0.0) or 0.0),
            "human_review_required": bool(decision.get("human_review_required", True)),
            "counter_evidence": decision.get("counter_evidence", []),
            "invalidation_conditions": decision.get("invalidation_conditions", []),
        },
        "journey": [
            "打开一级入口：研究",
            "打开功能：研究与政策垂直切片",
            "定位官方政策引用",
            "打开报告清单",
            "把缺口任务交给人工复核队列",
        ],
        "operational_record_ids": ids,
        "safety_boundary": {
            "research_only": True,
            "no_government_portal_action": True,
            "no_legal_or_tax_advice": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_private_holdings_used": True,
            "human_review_required": True,
        },
    }


def run_pfi007_research_policy_acceptance(*, db_path: Path | str | None = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="pfi007-research-policy-") as tmp_dir:
            return _run_acceptance(Path(tmp_dir), generated_at=generated_at)
    db = Path(db_path)
    return _run_acceptance(db.parent.parent.parent if db.name == "pfi.sqlite" else db, generated_at=generated_at, explicit_db_path=db)


def rollback_pfi007_research_policy_records(store: OperationalStore, ids: dict[str, str]) -> dict[str, Any]:
    source_id = str(ids.get("source_id", ""))
    evidence_id = str(ids.get("evidence_id", ""))
    job_id = str(ids.get("job_id", ""))
    task_id = str(ids.get("task_id", ""))
    counts: dict[str, int] = {}
    with store.connect() as conn:
        counts["task_records"] = conn.execute("DELETE FROM task_records WHERE task_id = ?", (task_id,)).rowcount
        counts["job_records"] = conn.execute("DELETE FROM job_records WHERE job_id = ?", (job_id,)).rowcount
        counts["evidence_records"] = conn.execute("DELETE FROM evidence_records WHERE evidence_id = ?", (evidence_id,)).rowcount
        counts["source_versions"] = conn.execute("DELETE FROM source_versions WHERE source_id = ?", (source_id,)).rowcount
        counts["source_records"] = conn.execute("DELETE FROM source_records WHERE source_id = ?", (source_id,)).rowcount
    residue = {
        "source_records": _count_rows(store, "source_records", "source_id", source_id),
        "evidence_records": _count_rows(store, "evidence_records", "evidence_id", evidence_id),
        "job_records": _count_rows(store, "job_records", "job_id", job_id),
        "task_records": _count_rows(store, "task_records", "task_id", task_id),
    }
    return {
        "schema": "PFI007ResearchPolicyRollbackProofV1",
        "mode": "temporary_operational_store",
        "deleted_counts": counts,
        "residue_counts": residue,
        "status": "Pass" if all(value == 0 for value in residue.values()) else "Fail",
        "note": "Rollback deletes only PFI-007 source/evidence/job/task records in the temporary acceptance store; shared entity rows are left untouched.",
    }


def _run_acceptance(root: Path, *, generated_at: str, explicit_db_path: Path | None = None) -> dict[str, Any]:
    fixture = build_pfi007_research_policy_golden_fixture()
    db_path = explicit_db_path or root / "private" / "operational" / "pfi.sqlite"
    store = OperationalStore(db_path)
    payload = build_research_policy_workflow(
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        opportunities=fixture["opportunities"],
        report_decision_payload=fixture["report_decision_payload"],
        project_root=root,
        report_root=root / "reports",
    )
    ids = record_research_policy_workflow(store, payload, artifact_uri="operational_store:pfi007_research_policy_acceptance")
    ui_read_model = build_pfi007_research_policy_ui_read_model(payload, ids)
    golden_metrics = _golden_metrics(payload, ui_read_model, store)
    checks = _acceptance_checks(payload, ui_read_model, golden_metrics, ids, store)
    rollback_proof = rollback_pfi007_research_policy_records(store, ids)
    checks.append(_check("RollbackProof", rollback_proof["status"] == "Pass", json.dumps(rollback_proof["residue_counts"], sort_keys=True)))
    summary = _summary(checks)
    status = "Pass" if summary["fail"] == 0 else "Fail"
    return {
        "schema": PFI007_RESEARCH_POLICY_ACCEPTANCE_SCHEMA,
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
            "provider_fetch_required": False,
            "government_portal_required": False,
            "broker_required": False,
            "llm_required": False,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_government_portal_action": True,
            "no_legal_or_tax_advice": True,
            "no_private_holdings_used": True,
            "human_review_required": True,
        },
        "next_action": "Use this as Gate 3 Research + Policy evidence, then continue PFI-008 Portfolio vertical slice.",
    }


def _acceptance_checks(
    payload: dict[str, Any],
    ui_read_model: dict[str, Any],
    golden_metrics: dict[str, Any],
    ids: dict[str, str],
    store: OperationalStore,
) -> list[dict[str, str]]:
    rows = {table: store.table_rows(table) for table in ("source_records", "evidence_records", "job_records", "task_records")}
    return [
        _check("DataChain:PolicyRadar", payload.get("policy_radar", {}).get("summary", {}).get("total_records") == 2, "policy_records=2"),
        _check("Domain:ReportGapTasks", payload.get("report_gap_tasks", {}).get("task_count", 0) >= 3, f"tasks={payload.get('report_gap_tasks', {}).get('task_count', 0)}"),
        _check("API:UIReadModel", ui_read_model.get("schema") == PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA and ui_read_model.get("primary_route") == "research", ui_read_model.get("schema", "")),
        _check("UI:ChineseJourney", all(step for step in ui_read_model.get("journey", [])) and "研究" in ui_read_model.get("workspace_label", ""), "research journey labels"),
        _check("CitationLocator:OfficialSource", golden_metrics.get("official_citation_count", 0) >= 1, f"official_citations={golden_metrics.get('official_citation_count')}"),
        _check("ReportManifest:Present", golden_metrics.get("report_manifest_count", 0) >= 1 and golden_metrics.get("report_gap_count", 0) >= 3, f"reports={golden_metrics.get('report_manifest_count')}; gaps={golden_metrics.get('report_gap_count')}"),
        _check("TasksEvidence:Source", any(row["source_id"] == ids["source_id"] for row in rows["source_records"]), ids["source_id"]),
        _check("TasksEvidence:Evidence", any(row["evidence_id"] == ids["evidence_id"] for row in rows["evidence_records"]), ids["evidence_id"]),
        _check("TasksEvidence:Job", any(row["job_id"] == ids["job_id"] and row["status"] == "completed" for row in rows["job_records"]), ids["job_id"]),
        _check("TasksEvidence:ReviewTask", any(row["task_id"] == ids["task_id"] and row["human_review_required"] == 1 for row in rows["task_records"]), ids["task_id"]),
        _check("Decision:ReviewOnly", ui_read_model.get("decision", {}).get("target_weight_change") == 0.0 and ui_read_model.get("decision", {}).get("human_review_required") is True, "target_weight_change=0"),
        _check("Safety:NoExecution", all(payload.get("safety_boundary", {}).get(key) is True for key in ("research_only", "no_government_portal_action", "no_live_trading", "no_broker_calls", "no_order_execution", "human_review_required")), "research-only policy boundary"),
        _check("GoldenMetrics:StableWorkflow", bool(golden_metrics.get("workflow_id")) and golden_metrics.get("policy_record_count") == 2, str(golden_metrics.get("workflow_id", ""))),
    ]


def _citation_locator(policy: dict[str, Any], report_gaps: dict[str, Any]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for row in policy.get("top_opportunities", []):
        if not isinstance(row, dict):
            continue
        citation_id = f"policy:{row.get('policy_id', '')}"
        citations.append(
            {
                "citation_id": citation_id,
                "label": row.get("title", ""),
                "source_type": row.get("source_type", ""),
                "source_name": row.get("source_name", ""),
                "source_url": row.get("source_url", ""),
                "evidence_path": row.get("evidence_path", ""),
                "authority_status": "OfficialEvidence" if row.get("source_type") in {"Official", "Regulator", "Government", "Exchange"} and (row.get("source_url") or row.get("evidence_path")) else "NeedsAuthorityReview",
                "linked_cards": ["policy_authority", "policy_opportunities"],
                "manual_review_required": True,
            }
        )
    for task in report_gaps.get("tasks", [])[:6]:
        if not isinstance(task, dict):
            continue
        citations.append(
            {
                "citation_id": f"report-gap:{task.get('task_id', '')}",
                "label": task.get("research_topic", ""),
                "source_type": "ReportEvidenceGap",
                "source_name": task.get("source_report", ""),
                "source_url": "",
                "evidence_path": task.get("metadata_path", ""),
                "authority_status": "EvidenceRepairRequired",
                "linked_cards": ["research_evidence_gaps"],
                "manual_review_required": True,
            }
        )
    return citations


def _report_manifest(report_gaps: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for task in report_gaps.get("tasks", []):
        if not isinstance(task, dict):
            continue
        key = str(task.get("run") or task.get("source_report") or task.get("metadata_path") or "report")
        row = grouped.setdefault(
            key,
            {
                "report_id": key,
                "source_report": task.get("source_report", ""),
                "metadata_path": task.get("metadata_path", ""),
                "symbol": task.get("symbol", ""),
                "market": task.get("market", ""),
                "readiness": "NeedsMoreEvidence",
                "gap_count": 0,
                "evidence_gaps": [],
                "validation_task_ids": [],
                "readonly": True,
            },
        )
        row["gap_count"] += 1
        row["evidence_gaps"].append(task.get("evidence_gap", ""))
        row["validation_task_ids"].append(task.get("task_id", ""))
    return list(grouped.values())


def _ui_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": {
            "policy_authority": "政策权威来源",
            "policy_opportunities": "政策机会",
            "research_evidence_gaps": "研究证据缺口",
        }.get(card.get("card_id", ""), card.get("title", "")),
        "status": card.get("status", "Review"),
        "summary": card.get("summary", ""),
        "source_ids": card.get("source_ids", []),
        "as_of": card.get("as_of", ""),
        "evidence_class": card.get("evidence_class", "research_policy_evidence"),
        "review_required": bool(card.get("review_required", True)),
    }


def _golden_metrics(payload: dict[str, Any], ui_read_model: dict[str, Any], store: OperationalStore) -> dict[str, Any]:
    citations = ui_read_model.get("citation_locator", [])
    manifest = ui_read_model.get("report_manifest", [])
    return {
        "workflow_id": payload.get("workflow_id", ""),
        "source_id": payload.get("source_id", ""),
        "policy_record_count": payload.get("policy_radar", {}).get("summary", {}).get("total_records", 0),
        "authoritative_source_records": payload.get("policy_radar", {}).get("runtime_summary", {}).get("authoritative_source_records", 0),
        "report_gap_count": payload.get("report_gap_tasks", {}).get("task_count", 0),
        "citation_count": len(citations),
        "official_citation_count": sum(1 for item in citations if item.get("authority_status") == "OfficialEvidence"),
        "report_manifest_count": len(manifest),
        "confidence": payload.get("decision", {}).get("confidence", 0.0),
        "target_weight_change": payload.get("decision", {}).get("target_weight_change", 0.0),
        "source_record_count": len(store.table_rows("source_records")),
        "evidence_record_count": len(store.table_rows("evidence_records")),
        "job_record_count": len(store.table_rows("job_records")),
        "task_record_count": len(store.table_rows("task_records")),
    }


def _count_rows(store: OperationalStore, table: str, column: str, value: str) -> int:
    with store.connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {column} = ?", (value,)).fetchone()
    return int(row["count"])


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if passed else "Fail", "evidence": evidence}


def _summary(checks: list[dict[str, str]]) -> dict[str, int]:
    passed = sum(1 for item in checks if item["status"] == "Pass")
    failed = sum(1 for item in checks if item["status"] == "Fail")
    info = sum(1 for item in checks if item["status"] == "Info")
    return {"pass": passed, "fail": failed, "info": info, "total": len(checks)}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
