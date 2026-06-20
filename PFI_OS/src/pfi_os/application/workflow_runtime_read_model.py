from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord


WORKFLOW_RUNTIME_READ_MODEL_SCHEMA = "PFIOSPhaseCWorkflowRuntimeReadModelV1"
WORKFLOW_RUNTIME_CONTRACT_SCHEMA = "PFIOSPhaseCWorkflowRuntimeContractV1"
WORKFLOW_RUNTIME_EVIDENCE_CLASS = "workflow_runtime_read_model"
PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA = "PFIOSPFI003SupervisorRuntimeReadModelV1"
PFI003_DURABLE_JOB_STORE_SCHEMA = "PFIOSPFI003DurableJobStoreV1"
PFI010_MINUTE_FAST_PATH_READ_MODEL_SCHEMA = "PFI010MinuteFastPathReadModelV1"
PFI010_MINUTE_FAST_PATH_EVIDENCE_CLASS = "pfi010_minute_fast_path_acceptance"
PFI011_LOCAL_LLM_DEEP_PATH_READ_MODEL_SCHEMA = "PFI011LocalLLMDeepPathReadModelV1"
PFI011_LOCAL_LLM_DEEP_PATH_EVIDENCE_CLASS = "pfi011_local_llm_deep_path_acceptance"
FAST_PATH_TARGET_SECONDS = 60

WORKFLOW_TARGETS: tuple[dict[str, str], ...] = (
    {
        "workspace": "strategy",
        "title": "Strategy Lab",
        "source_type": "strategy_lab_verification",
        "job_type": "strategy_lab_verification",
        "evidence_class": "replay_backtest_result",
        "data_domain": DataDomain.PUBLIC_SHARED_CANONICAL.value,
    },
    {
        "workspace": "market",
        "title": "Markets",
        "source_type": "markets_vertical_slice",
        "job_type": "markets_vertical_slice",
        "evidence_class": "market_observation",
        "data_domain": DataDomain.PUBLIC_SHARED_CANONICAL.value,
    },
    {
        "workspace": "research",
        "title": "Research + Policy",
        "source_type": "research_policy_vertical_slice",
        "job_type": "research_policy_vertical_slice",
        "evidence_class": "research_policy_evidence",
        "data_domain": DataDomain.PUBLIC_SHARED_CANONICAL.value,
    },
    {
        "workspace": "portfolio",
        "title": "Portfolio",
        "source_type": "portfolio_vertical_slice",
        "job_type": "portfolio_vertical_slice",
        "evidence_class": "private_portfolio_review",
        "data_domain": DataDomain.PRIVATE_DERIVED.value,
    },
)


def build_phase_c_workflow_runtime_contract() -> dict[str, Any]:
    return {
        "schema": WORKFLOW_RUNTIME_CONTRACT_SCHEMA,
        "read_model_schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
        "phase": "Phase C",
        "required_workflows": [target["workspace"] for target in WORKFLOW_TARGETS],
        "required_operational_tables": ["source_records", "evidence_records", "job_records", "task_records", "holding_snapshots"],
        "required_runtime_sections": ["workflow_cards", "background_jobs", "task_center_rows", "supervisor_runtime"],
        "required_card_fields": [
            "workspace",
            "title",
            "status",
            "source_type",
            "evidence_class",
            "data_domain",
            "source_id",
            "evidence_id",
            "job_id",
            "task_count",
            "open_task_count",
            "latest_as_of",
            "review_required",
            "freshness",
        ],
        "fast_path": {
            "target_seconds": FAST_PATH_TARGET_SECONDS,
            "cached_read_model_required": True,
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
            "retry_policy": _retry_policy(),
        },
        "non_regression_constraints": {
            "phase_b_workflows_promoted": True,
            "web_shell_cached_read_model": True,
            "sixty_second_fast_path_contract": True,
            "retry_backoff_visible": True,
            "pfi003_supervisor_runtime_visible": True,
            "private_holdings_not_exposed": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "human_review_required": True,
        },
    }


def build_workflow_runtime_read_model(
    store: OperationalStore | None = None,
    *,
    now: datetime | None = None,
    fast_path_target_seconds: int = FAST_PATH_TARGET_SECONDS,
) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    sources = operational_store.table_rows("source_records")
    evidence = operational_store.table_rows("evidence_records")
    jobs = operational_store.table_rows("job_records")
    tasks = operational_store.table_rows("task_records")
    holdings = operational_store.table_rows("holding_snapshots")
    cards = [
        _workflow_card(target, sources=sources, evidence=evidence, jobs=jobs, tasks=tasks, holdings=holdings, now=now)
        for target in WORKFLOW_TARGETS
    ]
    fast_path = _fast_path_acceptance(cards, jobs=jobs, target_seconds=fast_path_target_seconds)
    supervisor_runtime = _supervisor_runtime(jobs)
    minute_fast_path = _minute_fast_path_runtime(evidence)
    local_llm_deep_path = _local_llm_deep_path_runtime(evidence)
    return {
        "schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
        "phase": "Phase C",
        "generated_at": generated_at,
        "fast_path": fast_path,
        "minute_fast_path": minute_fast_path,
        "local_llm_deep_path": local_llm_deep_path,
        "workflow_cards": cards,
        "background_jobs": _background_jobs(jobs),
        "task_center_rows": _task_center_rows(cards, tasks, supervisor_runtime=supervisor_runtime),
        "supervisor_runtime": supervisor_runtime,
        "retry_policy": _retry_policy(),
        "read_model": "OperationalStore -> Phase B workflow records -> PFIOSPhaseCWorkflowRuntimeReadModelV1",
        "cache_policy": "Web Shell consumes this compact runtime model; it does not call providers, brokers, LLMs, or private files directly.",
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
            "private_holdings_not_exposed": True,
        },
        "missing_data_log": _missing_data_log(cards, jobs),
    }


def record_workflow_runtime_read_model(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    source_id: str = "",
    as_of: str = "",
    artifact_uri: str = "operational_store:workflow_runtime_read_model",
) -> dict[str, str]:
    if payload.get("schema") != WORKFLOW_RUNTIME_READ_MODEL_SCHEMA:
        raise ValueError(f"payload schema must be {WORKFLOW_RUNTIME_READ_MODEL_SCHEMA}")
    store.initialize()
    runtime_id = _stable_id("phase-c-runtime", payload.get("generated_at", ""), payload.get("workflow_cards", []), payload.get("fast_path", {}))
    source_id = source_id or f"src-phase-c-runtime-{runtime_id}"
    as_of = as_of or str(payload.get("generated_at", ""))
    evidence_id = f"evidence-{runtime_id}"
    job_id = f"job-{runtime_id}"
    task_id = f"task-{runtime_id}"

    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PRIVATE_DERIVED,
            source_type="phase_c_workflow_runtime_read_model",
            uri=artifact_uri,
            as_of=as_of,
            evidence_class=WORKFLOW_RUNTIME_EVIDENCE_CLASS,
            title="Phase C workflow runtime read model",
            checksum=_stable_id(payload),
            metadata={
                "runtime_id": runtime_id,
                "schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
                "fast_path": payload.get("fast_path", {}),
                "safety_boundary": payload.get("safety_boundary", {}),
            },
        )
    )
    store.upsert_entity("phase_c_workflow_runtime", entity_type="runtime_read_model", display_name="Phase C Workflow Runtime", canonical_symbol="phase_c_workflow_runtime")
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id="phase_c_workflow_runtime",
            as_of=as_of,
            evidence_class=WORKFLOW_RUNTIME_EVIDENCE_CLASS,
            summary=_evidence_summary(payload),
            artifact_uri=artifact_uri,
            model_version="DisabledProvider",
            metadata={"runtime_id": runtime_id, "workflow_runtime_read_model": payload},
        )
    )
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="phase_c_workflow_runtime_read_model",
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
            artifact_uri=artifact_uri,
            metadata={"runtime_id": runtime_id, "schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="data",
            action="Review Phase C workflow runtime fast path, retry policy, stale sources, and open human-review tasks.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={"runtime_id": runtime_id, "fast_path": payload.get("fast_path", {})},
        )
    )
    return {"source_id": source_id, "evidence_id": evidence_id, "job_id": job_id, "task_id": task_id}


def empty_workflow_runtime_read_model() -> dict[str, Any]:
    return {
        "schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
        "phase": "Phase C",
        "generated_at": "",
        "fast_path": {
            "status": "Review",
            "target_seconds": FAST_PATH_TARGET_SECONDS,
            "estimated_seconds": 0,
            "ready_workflow_count": 0,
            "required_workflow_count": len(WORKFLOW_TARGETS),
            "blocked_workflow_count": len(WORKFLOW_TARGETS),
            "running_job_count": 0,
            "failed_job_count": 0,
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
        },
        "minute_fast_path": _empty_minute_fast_path_runtime(),
        "local_llm_deep_path": _empty_local_llm_deep_path_runtime(),
        "workflow_cards": [],
        "background_jobs": [],
        "task_center_rows": [],
        "supervisor_runtime": {
            "schema": PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA,
            "status": "Review",
            "total_job_count": 0,
            "active_job_count": 0,
            "queued_job_count": 0,
            "running_job_count": 0,
            "retrying_job_count": 0,
            "dead_letter_count": 0,
            "latest_job_id": "",
            "latest_phase": "",
            "latest_event": {},
            "web_shell_visible": True,
            "read_model": "OperationalStore.job_records -> workflow_runtime.supervisor_runtime",
            "safety_boundary": _supervisor_safety_boundary(),
        },
        "retry_policy": _retry_policy(),
        "read_model": "OperationalStore -> Phase B workflow records -> PFIOSPhaseCWorkflowRuntimeReadModelV1",
        "cache_policy": "Web Shell consumes this compact runtime model; it does not call providers, brokers, LLMs, or private files directly.",
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
            "private_holdings_not_exposed": True,
        },
        "missing_data_log": [],
    }


def _workflow_card(
    target: dict[str, str],
    *,
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    holdings: list[dict[str, Any]],
    now: datetime | None,
) -> dict[str, Any]:
    workspace = target["workspace"]
    source = _latest([row for row in sources if str(row.get("source_type", "")) == target["source_type"]])
    evidence_row = _latest(
        [
            row
            for row in evidence
            if str(row.get("source_id", "")) == str(source.get("source_id", ""))
            or str(row.get("evidence_class", "")) == target["evidence_class"]
        ]
    )
    job = _latest([row for row in jobs if str(row.get("source_id", "")) == str(source.get("source_id", "")) or str(row.get("job_type", "")) == target["job_type"]], key="updated_at")
    workflow_tasks = [
        row
        for row in tasks
        if str(row.get("source_id", "")) == str(source.get("source_id", ""))
        or str(row.get("evidence_id", "")) == str(evidence_row.get("evidence_id", ""))
        or str(row.get("owner_workspace", "")) in {workspace, _owner_workspace_alias(workspace)}
    ]
    open_tasks = [row for row in workflow_tasks if str(row.get("status", "")).lower() in {"open", "queued", "running"}]
    latest_as_of = _latest_text([source.get("as_of", ""), evidence_row.get("as_of", ""), job.get("as_of", ""), *(row.get("as_of", "") for row in workflow_tasks)])
    holding_snapshot_count = 0
    if workspace == "portfolio":
        holding_snapshot_count = sum(1 for row in holdings if str(row.get("source_id", "")) == str(source.get("source_id", "")) or str(row.get("portfolio_id", "")))
    return {
        "workspace": workspace,
        "title": target["title"],
        "status": _workflow_status(source, evidence_row, job),
        "source_type": target["source_type"],
        "evidence_class": target["evidence_class"],
        "data_domain": str(source.get("domain", "")) or target["data_domain"],
        "source_id": str(source.get("source_id", "")),
        "evidence_id": str(evidence_row.get("evidence_id", "")),
        "job_id": str(job.get("job_id", "")),
        "task_count": len(workflow_tasks),
        "open_task_count": len(open_tasks),
        "latest_as_of": latest_as_of,
        "review_required": True,
        "freshness": _freshness(latest_as_of, now=now),
        "holding_snapshot_count": holding_snapshot_count,
        "summary": _card_summary(target, source, evidence_row, job, open_tasks),
    }


def _fast_path_acceptance(cards: list[dict[str, Any]], *, jobs: list[dict[str, Any]], target_seconds: int) -> dict[str, Any]:
    ready = [card for card in cards if card["status"] in {"Ready", "Review"} and card.get("source_id") and card.get("evidence_id")]
    blocked = [card for card in cards if card["status"] == "Missing"]
    running_jobs = [row for row in jobs if str(row.get("status", "")).lower() in {"queued", "running"} and _is_phase_b_job(row)]
    failed_jobs = [row for row in jobs if str(row.get("status", "")).lower() in {"failed", "error", "blocked"} and _is_phase_b_job(row)]
    estimated_seconds = min(target_seconds, 4 + len(cards) * 3 + len(running_jobs) * 10)
    if failed_jobs:
        status = "Blocked"
    elif blocked or running_jobs or estimated_seconds > target_seconds:
        status = "Review"
    else:
        status = "Pass"
    return {
        "status": status,
        "target_seconds": int(target_seconds),
        "estimated_seconds": int(estimated_seconds),
        "ready_workflow_count": len(ready),
        "required_workflow_count": len(cards),
        "blocked_workflow_count": len(blocked),
        "running_job_count": len(running_jobs),
        "failed_job_count": len(failed_jobs),
        "provider_fetch_required": False,
        "broker_required": False,
        "llm_required": False,
        "cached_read_model_required": True,
    }


def _background_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted([item for item in jobs if _is_phase_b_job(item) or _is_pfi003_supervisor_job(item)], key=lambda item: str(item.get("updated_at", "")), reverse=True)[:8]:
        rows.append(
            {
                "job_id": str(row.get("job_id", "")),
                "source_id": str(row.get("source_id", "")),
                "job_type": str(row.get("job_type", "")),
                "status": str(row.get("status", "")),
                "phase": str(row.get("phase", "")),
                "progress": float(row.get("progress", 0.0) or 0.0),
                "retry_count": int(row.get("retry_count", 0) or 0),
                "leave_page_safe": True,
                "supervisor_managed": _is_pfi003_supervisor_job(row),
            }
        )
    return rows


def _task_center_rows(cards: list[dict[str, Any]], tasks: list[dict[str, Any]], *, supervisor_runtime: dict[str, Any] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if supervisor_runtime:
        supervisor_status = str(supervisor_runtime.get("status", "Review"))
        rows.append(
            {
                "priority": "P0" if supervisor_runtime.get("dead_letter_count", 0) else "P1",
                "workspace": "data",
                "object": "PFI-003 监督器",
                "action": (
                    f"复核后台任务：活跃 {supervisor_runtime.get('active_job_count', 0)}，"
                    f"死信 {supervisor_runtime.get('dead_letter_count', 0)}。"
                ),
                "status": supervisor_status,
                "evidence": str(supervisor_runtime.get("latest_job_id", "") or "job_records"),
            }
        )
    for card in cards:
        priority = "P0" if card["status"] in {"Missing", "Blocked"} else "P1"
        rows.append(
            {
                "priority": priority,
                "workspace": str(card["workspace"]),
                "object": str(card["title"]),
                "action": f"Review {card['title']} workflow runtime card.",
                "status": str(card["status"]),
                "evidence": str(card.get("evidence_id", "") or card.get("evidence_class", "")),
            }
        )
    for row in sorted(tasks, key=lambda item: (str(item.get("priority", "P9")), str(item.get("task_id", ""))))[:4]:
        rows.append(
            {
                "priority": str(row.get("priority", "")),
                "workspace": str(row.get("owner_workspace", "")),
                "object": str(row.get("task_id", "")),
                "action": str(row.get("action", "")),
                "status": str(row.get("status", "")),
                "evidence": str(row.get("evidence_id", "")),
            }
        )
    return rows[:8]


def _supervisor_runtime(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    supervisor_jobs = [row for row in jobs if _is_pfi003_supervisor_job(row)]
    status_counts: dict[str, int] = {}
    for row in supervisor_jobs:
        status = str(row.get("status", "")).lower()
        status_counts[status] = status_counts.get(status, 0) + 1
    latest = _latest(supervisor_jobs, key="updated_at")
    latest_metadata = _metadata(latest)
    latest_events = latest_metadata.get("event_log", [])
    latest_event = latest_events[-1] if isinstance(latest_events, list) and latest_events else {}
    active_count = sum(status_counts.get(status, 0) for status in ["queued", "retrying", "resumed", "running"])
    dead_letter_count = status_counts.get("dead_letter", 0)
    if dead_letter_count:
        status = "Blocked"
    elif active_count:
        status = "Running"
    elif supervisor_jobs:
        status = "Ready"
    else:
        status = "Review"
    return {
        "schema": PFI003_SUPERVISOR_RUNTIME_READ_MODEL_SCHEMA,
        "status": status,
        "total_job_count": len(supervisor_jobs),
        "active_job_count": active_count,
        "queued_job_count": status_counts.get("queued", 0),
        "running_job_count": status_counts.get("running", 0),
        "retrying_job_count": status_counts.get("retrying", 0),
        "dead_letter_count": dead_letter_count,
        "latest_job_id": str(latest.get("job_id", "")),
        "latest_phase": str(latest.get("phase", "")),
        "latest_event": _json_safe(latest_event),
        "web_shell_visible": True,
        "read_model": "OperationalStore.job_records -> workflow_runtime.supervisor_runtime",
        "safety_boundary": _supervisor_safety_boundary(),
    }


def _minute_fast_path_runtime(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in evidence if str(row.get("evidence_class", "")) == PFI010_MINUTE_FAST_PATH_EVIDENCE_CLASS]
    latest = _latest(rows, key="created_at")
    metadata = _metadata(latest)
    payload = metadata.get("minute_fast_path", {})
    if isinstance(payload, dict) and payload.get("schema") == PFI010_MINUTE_FAST_PATH_READ_MODEL_SCHEMA:
        clean = _json_safe(payload)
        clean["web_shell_visible"] = True
        return clean
    return _empty_minute_fast_path_runtime()


def _empty_minute_fast_path_runtime() -> dict[str, Any]:
    return {
        "schema": PFI010_MINUTE_FAST_PATH_READ_MODEL_SCHEMA,
        "issue": "PFI-010",
        "gate": "Gate 4",
        "status": "Review",
        "target_seconds": FAST_PATH_TARGET_SECONDS,
        "p95_seconds": 0.0,
        "max_seconds": 0.0,
        "source_count": 0,
        "sample_count": 0,
        "page_closed_updates": False,
        "failure_injection_status": "Missing",
        "logical_1h_soak_status": "Missing",
        "logical_24h_soak_status": "Missing",
        "web_shell_visible": True,
        "ui_push": {
            "mode": "cached_read_model_local_polling",
            "runtime_field": "workflow_runtime.minute_fast_path",
            "sse_required": False,
            "push_after_page_closed": False,
        },
        "latency_dashboard": {"rows": []},
        "safety_boundary": {
            "research_only": True,
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
            "network_required": False,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_payment_or_betting": True,
            "human_review_required": True,
        },
    }


def _local_llm_deep_path_runtime(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in evidence if str(row.get("evidence_class", "")) == PFI011_LOCAL_LLM_DEEP_PATH_EVIDENCE_CLASS]
    latest = _latest(rows, key="created_at")
    metadata = _metadata(latest)
    payload = metadata.get("local_llm_deep_path", {})
    if isinstance(payload, dict) and payload.get("schema") == PFI011_LOCAL_LLM_DEEP_PATH_READ_MODEL_SCHEMA:
        clean = _json_safe(payload)
        clean["web_shell_visible"] = True
        return clean
    return _empty_local_llm_deep_path_runtime()


def _empty_local_llm_deep_path_runtime() -> dict[str, Any]:
    return {
        "schema": PFI011_LOCAL_LLM_DEEP_PATH_READ_MODEL_SCHEMA,
        "issue": "PFI-011",
        "gate": "Gate 5",
        "status": "Review",
        "provider_interface_ready": False,
        "default_provider": "DisabledProvider",
        "local_provider": "",
        "disabled_provider_available": True,
        "fallback_used": True,
        "citation_count": 0,
        "schema_validation_status": "Missing",
        "citation_validation_status": "Missing",
        "timeout_fallback_status": "Missing",
        "cancel_status": "Missing",
        "resource_budget_status": "Missing",
        "prompt_injection_status": "Missing",
        "hardware_status": "Missing",
        "web_shell_visible": True,
        "safety_boundary": {
            "research_only": True,
            "provider_fetch_required": False,
            "network_required": False,
            "broker_required": False,
            "order_execution": False,
            "payment_or_betting": False,
            "autonomous_advice": False,
            "human_review_required": True,
        },
    }


def _missing_data_log(cards: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for card in cards:
        if card["status"] == "Missing":
            rows.append({"dataset": "phase_b_workflow", "status": "Missing", "message": f"{card['title']} workflow evidence is missing."})
    for row in jobs:
        if _is_phase_b_job(row) and str(row.get("status", "")).lower() in {"failed", "error", "blocked"}:
            rows.append({"dataset": "phase_b_job", "status": str(row.get("status", "")), "message": f"{row.get('job_id', '')}: {row.get('error_message', '')}"})
    return rows


def _workflow_status(source: dict[str, Any], evidence: dict[str, Any], job: dict[str, Any]) -> str:
    if not source or not evidence:
        return "Missing"
    job_status = str(job.get("status", "")).lower()
    if job_status in {"failed", "error", "blocked"}:
        return "Blocked"
    if job_status in {"queued", "running"}:
        return "Running"
    return "Ready"


def _card_summary(target: dict[str, str], source: dict[str, Any], evidence: dict[str, Any], job: dict[str, Any], open_tasks: list[dict[str, Any]]) -> str:
    if not source or not evidence:
        return f"{target['title']} workflow has no Operational Store source/evidence yet."
    return (
        f"{target['title']} workflow source={source.get('source_id', '')}, "
        f"evidence={evidence.get('evidence_id', '')}, job_status={job.get('status', 'missing')}, "
        f"open_tasks={len(open_tasks)}."
    )


def _freshness(value: str, *, now: datetime | None) -> dict[str, Any]:
    reference = pd.Timestamp(now or datetime.now(timezone.utc))
    timestamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(timestamp):
        return {"status": "Missing", "age_hours": None}
    age_hours = max(0.0, float((reference - timestamp).total_seconds() / 3600))
    if age_hours <= 36:
        status = "Fresh"
    elif age_hours <= 168:
        status = "Delayed"
    else:
        status = "Stale"
    return {"status": status, "age_hours": round(age_hours, 2)}


def _retry_policy() -> dict[str, Any]:
    return {
        "max_attempts": 3,
        "backoff_seconds": [1, 5, 15],
        "fail_closed": True,
        "idempotency_key_fields": ["source_id", "as_of", "evidence_class", "workflow_schema"],
        "retryable_statuses": ["queued", "running", "error"],
    }


def _is_phase_b_job(row: dict[str, Any]) -> bool:
    return str(row.get("job_type", "")) in {target["job_type"] for target in WORKFLOW_TARGETS}


def _is_pfi003_supervisor_job(row: dict[str, Any]) -> bool:
    metadata = _metadata(row)
    job_type = str(row.get("job_type", ""))
    return (
        metadata.get("schema") == PFI003_DURABLE_JOB_STORE_SCHEMA
        or str(row.get("source_id", "")) == "src-pfi003-durable-job-store"
        or job_type.startswith("pfi003")
        or "_pfi003_" in job_type
    )


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata_json", "{}")
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _supervisor_safety_boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_payment_or_betting": True,
        "human_review_required": True,
        "private_data_commit_path": False,
    }


def _owner_workspace_alias(workspace: str) -> str:
    return {"market": "markets", "strategy": "strategy_lab"}.get(workspace, workspace)


def _latest(rows: list[dict[str, Any]], *, key: str = "as_of") -> dict[str, Any]:
    if not rows:
        return {}
    return sorted(rows, key=lambda item: (str(item.get(key, "")), str(item.get("created_at", ""))), reverse=True)[0]


def _latest_text(values) -> str:
    clean = sorted((str(item or "").strip() for item in values if str(item or "").strip()), reverse=True)
    return clean[0] if clean else ""


def _evidence_summary(payload: dict[str, Any]) -> str:
    fast_path = payload.get("fast_path", {})
    return (
        "Phase C workflow runtime read model: "
        f"fast_path={fast_path.get('status', 'Review')}, "
        f"ready={fast_path.get('ready_workflow_count', 0)}/{fast_path.get('required_workflow_count', 0)}."
    )


def _stable_id(*parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items() if key != "holdings_json"}
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
