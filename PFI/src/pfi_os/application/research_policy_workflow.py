from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord
from pfi_os.policy import build_policy_radar
from pfi_os.research import build_report_gap_validation_tasks


RESEARCH_POLICY_WORKFLOW_SCHEMA = "PFIOSPhaseBResearchPolicyWorkflowV1"


def build_research_policy_workflow(
    *,
    source_id: str,
    as_of: str,
    opportunities: list[dict[str, Any]] | None = None,
    report_decision_payload: dict[str, Any] | None = None,
    project_root: Path | str | None = None,
    report_root: Path | str | None = None,
    evidence_class: str = "research_policy_evidence",
    model_version: str = "DisabledProvider",
) -> dict[str, Any]:
    """Build the Phase B Research + Policy vertical workflow.

    This workflow summarizes evidence and opens review tasks only. It cannot
    file policy applications, give legal conclusions, or create trading
    instructions.
    """
    root = Path(project_root).expanduser() if project_root is not None else Path.cwd()
    reports = Path(report_root).expanduser() if report_root is not None else root / "reports"
    policy = build_policy_radar(as_of=as_of, project_root=root, opportunities=opportunities or [])
    gap_tasks = build_report_gap_validation_tasks(
        as_of=as_of,
        project_root=root,
        report_root=reports,
        report_decision_payload=report_decision_payload or _empty_report_decision_payload(),
    )
    cards = _cards(policy, gap_tasks, source_id=source_id, evidence_class=evidence_class)
    decision = _decision_object(
        source_id=source_id,
        as_of=as_of,
        evidence_class=evidence_class,
        policy=policy,
        gap_tasks=gap_tasks,
        model_version=model_version,
    )
    workflow_id = _stable_id("research-policy", source_id, as_of, _policy_fingerprint(policy), _gap_fingerprint(gap_tasks))
    return {
        "schema": RESEARCH_POLICY_WORKFLOW_SCHEMA,
        "workspace": "research",
        "subworkspace": "policy",
        "workflow_id": workflow_id,
        "status": _workflow_status(policy, gap_tasks),
        "source_id": source_id,
        "as_of": as_of,
        "evidence_class": evidence_class,
        "model_versions": [model_version],
        "policy_radar": {
            "schema": policy.get("schema", ""),
            "policy_status": policy.get("policy_status", ""),
            "summary": policy.get("summary", {}),
            "runtime_summary": policy.get("runtime_summary", {}),
            "action_queue": policy.get("action_queue", [])[:8],
            "top_opportunities": policy.get("opportunities", [])[:8],
        },
        "report_gap_tasks": {
            "schema": gap_tasks.get("schema", ""),
            "source_schema": gap_tasks.get("source_schema", ""),
            "source_record_count": int(gap_tasks.get("source_record_count", 0) or 0),
            "task_count": int(gap_tasks.get("task_count", 0) or 0),
            "gap_counts": gap_tasks.get("gap_counts", []),
            "tasks": gap_tasks.get("tasks", [])[:12],
        },
        "cards": cards,
        "decision": decision,
        "assumptions": [
            "Research + Policy workflow consumes reviewed policy opportunities and report-decision payloads only.",
            "Policy outputs require source authority, source URL or evidence path, and manual review before Actionable status.",
            "Research gap tasks are evidence repair requests, not trading instructions.",
            "No government portal, legal filing, payment, broker call, holding mutation, or order execution is performed.",
        ],
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_government_portal_action": True,
            "no_legal_or_tax_advice": True,
            "human_review_required": True,
        },
        "missing_data_log": _missing_data_log(policy, gap_tasks),
    }


def record_research_policy_workflow(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    artifact_uri: str = "operational_store:research_policy_workflow",
) -> dict[str, str]:
    if payload.get("schema") != RESEARCH_POLICY_WORKFLOW_SCHEMA:
        raise ValueError(f"payload schema must be {RESEARCH_POLICY_WORKFLOW_SCHEMA}")
    store.initialize()
    source_id = str(payload["source_id"])
    as_of = str(payload["as_of"])
    evidence_class = str(payload["evidence_class"])
    workflow_id = str(payload["workflow_id"])
    evidence_id = f"evidence-{workflow_id}"
    job_id = f"job-{workflow_id}"
    task_id = f"task-{workflow_id}"
    entity_id = "research_policy"

    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="research_policy_vertical_slice",
            uri=artifact_uri,
            as_of=as_of,
            evidence_class=evidence_class,
            title="Research + Policy vertical workflow",
            checksum=_stable_id(payload.get("policy_radar", {}), payload.get("report_gap_tasks", {})),
            metadata={
                "workflow_id": workflow_id,
                "policy_status": payload.get("policy_radar", {}).get("policy_status", ""),
                "task_count": payload.get("report_gap_tasks", {}).get("task_count", 0),
                "safety_boundary": payload.get("safety_boundary", {}),
            },
        )
    )
    store.upsert_entity(entity_id, entity_type="research_policy_workflow", display_name="Research + Policy", canonical_symbol=entity_id)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id=entity_id,
            as_of=as_of,
            evidence_class=evidence_class,
            summary=_evidence_summary(payload),
            artifact_uri=artifact_uri,
            model_version=",".join(payload.get("model_versions", ["DisabledProvider"])),
            metadata={
                "workflow_id": workflow_id,
                "cards": payload.get("cards", []),
                "decision": payload.get("decision", {}),
                "policy_radar": payload.get("policy_radar", {}),
                "report_gap_tasks": payload.get("report_gap_tasks", {}),
            },
        )
    )
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="research_policy_vertical_slice",
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
            artifact_uri=artifact_uri,
            metadata={"workflow_id": workflow_id, "schema": RESEARCH_POLICY_WORKFLOW_SCHEMA},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="research",
            action="Review policy authority, evidence gaps, counter-evidence, and invalidation conditions before reuse.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={"workflow_id": workflow_id, "decision": payload.get("decision", {})},
        )
    )
    return {"source_id": source_id, "evidence_id": evidence_id, "job_id": job_id, "task_id": task_id}


def build_phase_b_research_policy_contract() -> dict[str, Any]:
    return {
        "schema": "PFIOSPhaseBResearchPolicyContractV1",
        "workflow_schema": RESEARCH_POLICY_WORKFLOW_SCHEMA,
        "workspace": "research",
        "subworkspace": "policy",
        "required_steps": [
            "load_reviewed_policy_opportunities",
            "build_policy_radar",
            "build_report_evidence_gap_tasks",
            "publish_cards_with_authority_and_review_status",
            "publish_evidence_and_review_task",
        ],
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "required_card_fields": ["card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "review_required"],
        "decision_contract_fields": [
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
        ],
        "non_regression_constraints": {
            "research_policy_vertical_slice": True,
            "policy_authority_visible": True,
            "research_gap_tasks_visible": True,
            "no_government_portal_action": True,
            "no_live_trading": True,
            "human_review_required": True,
            "llm_required": False,
        },
    }


def _cards(policy: dict[str, Any], gap_tasks: dict[str, Any], *, source_id: str, evidence_class: str) -> list[dict[str, Any]]:
    runtime = policy.get("runtime_summary", {})
    summary = policy.get("summary", {})
    task_count = int(gap_tasks.get("task_count", 0) or 0)
    as_of = str(policy.get("as_of") or gap_tasks.get("as_of") or "")
    return [
        {
            "card_id": "policy_authority",
            "title": "Policy authority",
            "status": str(runtime.get("status", "Blocked")),
            "summary": (
                f"opportunities={policy.get('opportunity_count', 0)}, "
                f"authoritative={runtime.get('authoritative_source_records', 0)}, "
                f"needs_authority_review={runtime.get('needs_authority_review_records', 0)}"
            ),
            "source_ids": [source_id],
            "as_of": as_of,
            "evidence_class": evidence_class,
            "review_required": str(runtime.get("status", "")) != "Pass",
        },
        {
            "card_id": "policy_opportunities",
            "title": "Policy opportunities",
            "status": str(policy.get("policy_status", "")),
            "summary": (
                f"actionable={summary.get('actionable_count', 0)}, "
                f"watch={summary.get('watch_count', 0)}, "
                f"missing_evidence={summary.get('missing_evidence_count', 0)}"
            ),
            "source_ids": [source_id],
            "as_of": as_of,
            "evidence_class": evidence_class,
            "review_required": True,
        },
        {
            "card_id": "research_evidence_gaps",
            "title": "Research evidence gaps",
            "status": "Review" if task_count else "Pass",
            "summary": f"gap_tasks={task_count}, source_records={gap_tasks.get('source_record_count', 0)}",
            "source_ids": [source_id],
            "as_of": str(gap_tasks.get("as_of", as_of)),
            "evidence_class": evidence_class,
            "review_required": task_count > 0,
        },
    ]


def _decision_object(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    policy: dict[str, Any],
    gap_tasks: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    summary = policy.get("summary", {})
    runtime = policy.get("runtime_summary", {})
    task_count = int(gap_tasks.get("task_count", 0) or 0)
    return {
        "decision_id": _stable_id("research-policy-decision", source_id, as_of, summary, gap_tasks.get("gap_counts", [])),
        "entity_id": "research_policy",
        "action": "review_research_policy_evidence",
        "horizon": "policy_and_research_review_window",
        "target_weight_change": 0.0,
        "status": "ReviewRequired",
        "confidence": _confidence(runtime, task_count),
        "evidence_class": evidence_class,
        "as_of": as_of,
        "thesis": [
            "Policy radar summarizes reviewed policy opportunities with source authority and evidence completeness gates.",
            "Report evidence gap tasks identify missing validation before research outputs can be reused.",
        ],
        "catalysts": [
            f"Actionable policy count: {summary.get('actionable_count', 0)}.",
            f"Research evidence gap task count: {task_count}.",
        ],
        "counter_evidence": [
            "Policy radar is not real-time policy coverage.",
            "News, research, or manual sources cannot independently support actionable policy decisions.",
            "Evidence gaps mean research reports remain review-only until validation tasks are completed.",
        ],
        "invalidation_conditions": [
            "Source authority, URL, evidence path, review status, or publication date changes.",
            "A policy opportunity lacks official, regulator, government, or exchange evidence.",
            "Report readiness is NeedsMoreEvidence or DoNotUse after updated validation.",
        ],
        "risks": ["Authority risk", "Missing evidence", "Legal or compliance interpretation risk", "Research overreach"],
        "portfolio_effect": {"no_private_holdings_used": True, "requires_portfolio_slice_before_position_impact": True},
        "model_versions": [model_version],
        "source_ids": [source_id],
        "human_review_required": True,
    }


def _workflow_status(policy: dict[str, Any], gap_tasks: dict[str, Any]) -> str:
    runtime_status = str(policy.get("runtime_summary", {}).get("status", "Blocked"))
    opportunity_count = int(policy.get("opportunity_count", 0) or 0)
    task_count = int(gap_tasks.get("task_count", 0) or 0)
    if opportunity_count == 0 and task_count == 0:
        return "Blocked"
    if runtime_status == "Pass" and task_count == 0:
        return "Pass"
    return "Review"


def _confidence(runtime: dict[str, Any], task_count: int) -> float:
    base = 0.5
    if runtime.get("status") == "Pass":
        base += 0.2
    elif runtime.get("status") == "Blocked":
        base -= 0.2
    if int(runtime.get("authoritative_source_records", 0) or 0) > 0:
        base += 0.05
    if task_count > 0:
        base -= 0.1
    return round(min(max(base, 0.0), 0.85), 2)


def _missing_data_log(policy: dict[str, Any], gap_tasks: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in policy.get("runtime_summary", {}).get("evidence_gate", []):
        if not isinstance(gate, dict):
            continue
        if gate.get("status") != "Pass":
            rows.append(
                {
                    "dataset": "policy_radar",
                    "status": str(gate.get("status", "")),
                    "message": f"{gate.get('gate', '')}: {gate.get('evidence', '')}",
                }
            )
    if int(gap_tasks.get("task_count", 0) or 0) > 0:
        rows.append({"dataset": "report_gap_tasks", "status": "Review", "message": f"{gap_tasks.get('task_count', 0)} evidence gap tasks require validation."})
    return rows


def _policy_fingerprint(policy: dict[str, Any]) -> Any:
    return {
        "policy_status": policy.get("policy_status", ""),
        "summary": policy.get("summary", {}),
        "top": [
            {
                "policy_id": row.get("policy_id", ""),
                "title": row.get("title", ""),
                "status": row.get("opportunity_status", ""),
            }
            for row in policy.get("opportunities", [])[:12]
            if isinstance(row, dict)
        ],
    }


def _gap_fingerprint(gap_tasks: dict[str, Any]) -> Any:
    return {
        "task_count": gap_tasks.get("task_count", 0),
        "gap_counts": gap_tasks.get("gap_counts", []),
        "tasks": [
            {
                "task_id": row.get("task_id", ""),
                "gap": row.get("evidence_gap", ""),
                "symbol": row.get("symbol", ""),
            }
            for row in gap_tasks.get("tasks", [])[:12]
            if isinstance(row, dict)
        ],
    }


def _evidence_summary(payload: dict[str, Any]) -> str:
    policy_status = payload.get("policy_radar", {}).get("policy_status", "")
    task_count = payload.get("report_gap_tasks", {}).get("task_count", 0)
    return f"Research + Policy workflow: policy_status={policy_status}, report_gap_tasks={task_count}."


def _empty_report_decision_payload() -> dict[str, Any]:
    return {
        "schema": "PFIOSReportDecisionSupportIndexV1",
        "record_count": 0,
        "records": [],
    }


def _stable_id(*parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
