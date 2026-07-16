"""PFI v0.2.5 Stage 9.1 report schema, completeness and quality-report contract."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


VERSION = "v0.2.5"
STAGE = 9
PHASE = "9.1"
PHASE_ID = "V025-S9-P9.1"
TASK_IDS = ("S9-P1-T1", "S9-P1-T2", "S9-P1-T3", "S9-P1-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE9-WHOLE-REVIEW"
REPORT_TYPES = (
    "data_quality",
    "net_worth",
    "cash",
    "investment",
    "consumption",
    "cashflow",
)
FINANCIAL_REPORT_TYPES = tuple(
    report_type for report_type in REPORT_TYPES if report_type != "data_quality"
)
COMPLETENESS_STATUSES = ("complete", "partial", "blocked")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

PFI_ROOT = Path(__file__).resolve().parents[4]
REPORT_SCHEMA_RELATIVE = Path("config/reports/v025_report.schema.json")
COMPLETENESS_RULES_RELATIVE = Path("config/reports/v025_completeness_rules.json")
SOURCE_MANIFEST_RELATIVE = Path(
    "reports/pfi_v025/stage_2/phase_2_1/source_manifest.json"
)
STAGE4_READ_MODEL_RELATIVE = Path(
    "reports/pfi_v025/stage_4/phase_4_3/read_model_status.json"
)
STAGE7_WORKFLOW_RELATIVE = Path(
    "reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json"
)
FORMULA_REGISTRY_RELATIVE = Path("config/formulas/v025_formula_registry.json")
PARAMETER_CATALOG_RELATIVE = Path("config/pfi_parameters.yaml")
BUILDER_RELATIVE = Path("src/pfi_os/application/reports/contracts.py")

SOURCE_MANIFEST_REF = f"PFI/{SOURCE_MANIFEST_RELATIVE.as_posix()}"
STAGE4_READ_MODEL_REF = f"PFI/{STAGE4_READ_MODEL_RELATIVE.as_posix()}"
STAGE7_WORKFLOW_REF = f"PFI/{STAGE7_WORKFLOW_RELATIVE.as_posix()}"
FORMULA_REGISTRY_REF = f"PFI/{FORMULA_REGISTRY_RELATIVE.as_posix()}"
PARAMETER_CATALOG_REF = f"PFI/{PARAMETER_CATALOG_RELATIVE.as_posix()}"


def canonical_hash(payload: object) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _require_sha256(label: str, value: object) -> str:
    normalized = str(value or "")
    if not SHA256_PATTERN.fullmatch(normalized):
        raise ValueError(f"{label} must be a sha256 value")
    return normalized


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def build_phase91_contract() -> dict[str, object]:
    return {
        "schema": "PFIV025Stage9Phase91ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "phase_name": "报告合同与完整度",
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "risk_tier": "T2",
        "current_phase_only": True,
        "report_types": list(REPORT_TYPES),
        "completeness_statuses": list(COMPLETENESS_STATUSES),
        "data_quality_report_generatable_in_any_dependency_state": True,
        "blocked_financial_conclusion_allowed": False,
        "cross_report_hash_fields": [
            "data_manifest_hash",
            "read_model_hash",
            "formula_registry_hash",
            "parameter_hash",
        ],
        "phase_9_2_started": False,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
        "push_performed": False,
        "app_install_performed": False,
        "finder_used": False,
        "external_network_performed": False,
        "explicitly_not_done": [
            "Phase 9.2 financial analysis, sensitivity and model validation",
            "Phase 9.3 decision lifecycle, review and multi-format export",
            "Stage 9 whole-stage independent review, remediation, re-review and transition acceptance",
            "GitHub push, canonical PFI.app reinstall and production/final acceptance",
        ],
    }


def _source_dependency_states(
    source_manifest: Mapping[str, Any],
    workflow_validation: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    sources = source_manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source manifest must contain sources")
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("source manifest entry must be an object")
        source_id = str(source.get("source_id") or "")
        if not source_id or source_id in states:
            raise ValueError("source IDs must be present and unique")
        raw_status = str(source.get("status") or "not_loaded")
        status = raw_status if raw_status in {"ready", "partial", "not_loaded"} else "blocked"
        reason = source.get("blocking_reason_zh")
        if status != "ready" and not reason:
            reason = "来源未达到 ready，不能支持确定性财务结论。"
        states[source_id] = {
            "dependency_id": source_id,
            "status": status,
            "critical": True,
            "blocking_reason_zh": str(reason) if reason else None,
            "review_route": "/sync",
        }

    workflows = workflow_validation.get("workflows")
    if not isinstance(workflows, Mapping):
        raise ValueError("Stage 7 workflow evidence is missing workflows")
    metric_lineage = workflows.get("metric_lineage")
    if not isinstance(metric_lineage, Mapping):
        raise ValueError("Stage 7 workflow evidence is missing metric_lineage")
    interconnection = metric_lineage.get("interconnection_map")
    if not isinstance(interconnection, Mapping):
        raise ValueError("Stage 7 metric lineage is missing interconnection_map")
    adapter_ready = (
        interconnection.get("status") == "ready"
        and interconnection.get("lineage_missing_count") == 0
    )
    states["economic_event_adapter"] = {
        "dependency_id": "economic_event_adapter",
        "status": "ready" if adapter_ready else "blocked",
        "critical": True,
        "blocking_reason_zh": (
            None
            if adapter_ready
            else "经济事件适配与 lineage 尚未完整，指标保持 blocked/null。"
        ),
        "review_route": "/data/interconnection",
    }
    states["financial_analysis_implementation"] = {
        "dependency_id": "financial_analysis_implementation",
        "status": "blocked",
        "critical": True,
        "blocking_reason_zh": "Phase 9.2 尚未开始，本 Phase 不生成完整财务分析结论。",
        "review_route": "/reports",
    }
    return states


def derive_report_status(
    report_type: str,
    dependency_states: Mapping[str, Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> tuple[str, str | None]:
    if report_type == "data_quality":
        return "complete", None
    report_dependencies = rules.get("report_dependencies")
    if not isinstance(report_dependencies, Mapping):
        raise ValueError("completeness rules are missing report_dependencies")
    rule = report_dependencies.get(report_type)
    if not isinstance(rule, Mapping):
        raise ValueError(f"missing completeness rule for {report_type}")
    critical = rule.get("critical")
    if not isinstance(critical, list) or not critical:
        raise ValueError(f"{report_type} requires critical dependencies")
    try:
        all_ready = all(
            dependency_states[str(dependency_id)]["status"] == "ready"
            for dependency_id in critical
        )
    except KeyError as exc:
        raise ValueError(f"unknown report dependency: {exc.args[0]}") from exc
    if all_ready:
        return "complete", None
    partial_scopes = rule.get("partial_scopes", [])
    if not isinstance(partial_scopes, list):
        raise ValueError(f"{report_type}.partial_scopes must be a list")
    for scope in partial_scopes:
        if not isinstance(scope, Mapping):
            raise ValueError(f"{report_type} partial scope must be an object")
        dependencies = scope.get("dependencies")
        if not isinstance(dependencies, list) or not dependencies:
            raise ValueError(f"{report_type} partial scope requires dependencies")
        if all(
            dependency_states[str(dependency_id)]["status"] == "ready"
            for dependency_id in dependencies
        ):
            return "partial", str(scope.get("scope_id") or "")
    return "blocked", None


def _input_hashes(
    pfi_root: Path,
    source_manifest: Mapping[str, Any],
    read_model_status: Mapping[str, Any],
    workflow_validation: Mapping[str, Any],
) -> dict[str, str]:
    schema_hash = file_hash(pfi_root / REPORT_SCHEMA_RELATIVE)
    rules_hash = file_hash(pfi_root / COMPLETENESS_RULES_RELATIVE)
    formula_hash = file_hash(pfi_root / FORMULA_REGISTRY_RELATIVE)
    parameter_hash = file_hash(pfi_root / PARAMETER_CATALOG_RELATIVE)
    workflows = workflow_validation["workflows"]
    metric_lineage = workflows["metric_lineage"]
    interconnection = metric_lineage["interconnection_map"]
    parameter_center = metric_lineage["parameter_center"]
    if parameter_center.get("formula_registry_hash") != formula_hash:
        raise ValueError("accepted Stage 7 formula registry hash differs from current file")
    if parameter_center.get("parameter_hash") != parameter_hash:
        raise ValueError("accepted Stage 7 parameter hash differs from current file")
    if source_manifest.get("acceptance_gate_status") != "pass":
        raise ValueError("Stage 2 source manifest is not passing")
    if workflow_validation.get("status") != "pass":
        raise ValueError("Stage 7 workflow evidence is not passing")
    if source_manifest.get("financial_fixture_fallback_used") is not False:
        raise ValueError("formal source manifest used a financial fallback")
    if read_model_status.get("contains_private_values") is not False:
        raise ValueError("Stage 4 read-model evidence contains private values")
    if workflow_validation.get("contains_private_values") is not False:
        raise ValueError("Stage 7 workflow evidence contains private values")
    values = {
        "data_manifest_hash": file_hash(pfi_root / SOURCE_MANIFEST_RELATIVE),
        "read_model_hash": _require_sha256(
            "read_model_hash", interconnection.get("read_model_hash")
        ),
        "formula_registry_hash": formula_hash,
        "parameter_hash": parameter_hash,
        "report_contract_hash": canonical_hash(
            {
                "report_schema_hash": schema_hash,
                "completeness_rules_hash": rules_hash,
            }
        ),
        "report_builder_hash": file_hash(pfi_root / BUILDER_RELATIVE),
        "stage4_read_model_artifact_hash": file_hash(
            pfi_root / STAGE4_READ_MODEL_RELATIVE
        ),
        "stage7_workflow_artifact_hash": file_hash(
            pfi_root / STAGE7_WORKFLOW_RELATIVE
        ),
    }
    values["input_bundle_hash"] = canonical_hash(values)
    return values


def _source_summary(
    source_manifest: Mapping[str, Any],
    workflow_validation: Mapping[str, Any],
) -> dict[str, Any]:
    sources = [item for item in source_manifest["sources"] if isinstance(item, Mapping)]
    statuses = Counter(str(item.get("status") or "not_loaded") for item in sources)
    starts = [
        str(item["coverage"]["start"])
        for item in sources
        if isinstance(item.get("coverage"), Mapping) and item["coverage"].get("start")
    ]
    ends = [
        str(item["coverage"]["end"])
        for item in sources
        if isinstance(item.get("coverage"), Mapping) and item["coverage"].get("end")
    ]
    as_of_values = [str(item["as_of"]) for item in sources if item.get("as_of")]
    workflows = workflow_validation["workflows"]
    ledger = workflows["import_review_ledger"]
    metric_lineage = workflows["metric_lineage"]
    interconnection = metric_lineage["interconnection_map"]
    drilldown = metric_lineage["metric_drilldown"]
    return {
        "report_as_of": max(as_of_values) if as_of_values else "UNKNOWN",
        "data_range": {
            "start": min(starts) if starts else None,
            "end": max(ends) if ends else None,
        },
        "sample_counts": {
            "registered_source_count": len(sources),
            "ready_source_count": int(statuses.get("ready", 0)),
            "partial_source_count": int(statuses.get("partial", 0)),
            "not_loaded_source_count": int(statuses.get("not_loaded", 0)),
            "transaction_record_count": int(
                next(
                    (
                        item.get("record_count")
                        for item in sources
                        if item.get("source_id") == "SRC-TRANSACTIONS-ALIPAY"
                    ),
                    0,
                )
                or 0
            ),
            "operational_event_count": int(ledger.get("confirmed_ledger_count") or 0),
            "metric_count": int(drilldown.get("metric_count") or 0),
            "lineage_complete_count": int(
                interconnection.get("lineage_complete_count") or 0
            ),
            "lineage_missing_count": int(
                interconnection.get("lineage_missing_count") or 0
            ),
        },
        "coverage": {
            "source_status_counts": dict(sorted(statuses.items())),
            "metric_status": drilldown.get("status"),
            "non_ready_false_zero_count": int(
                drilldown.get("non_ready_false_zero_count") or 0
            ),
            "lineage_status": interconnection.get("status"),
            "all_required_metric_fields_present": bool(
                drilldown.get("all_required_fields_present")
            ),
            "required_metric_field_values_valid": bool(
                drilldown.get("required_field_values_valid")
            ),
        },
    }


def _gaps(
    dependency_rows: list[dict[str, Any]],
    review_links: list[str],
) -> list[dict[str, str]]:
    default_route = (
        "/data/interconnection"
        if "/data/interconnection" in review_links
        else review_links[0]
    )
    return [
        {
            "dependency_id": str(row["dependency_id"]),
            "statement_zh": str(
                row.get("blocking_reason_zh")
                or "关键依赖未 ready，不能生成确定性财务结论。"
            ),
            "review_route": str(row.get("review_route") or default_route),
        }
        for row in dependency_rows
        if row.get("status") != "ready"
    ]


def _data_quality_conclusions(
    summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    counts = summary["sample_counts"]
    coverage = summary["coverage"]
    return [
        {
            "code": "DQ-SOURCE-AVAILABILITY",
            "scope": "data_quality_only",
            "statement_zh": (
                f"当前 {counts['registered_source_count']} 个注册源中 "
                f"{counts['ready_source_count']} 个 ready、"
                f"{counts['partial_source_count']} 个 partial、"
                f"{counts['not_loaded_source_count']} 个 not_loaded；"
                "这只说明数据可用性，不是财务结论。"
            ),
            "evidence_refs": [SOURCE_MANIFEST_REF],
        },
        {
            "code": "DQ-LINEAGE-COMPLETENESS",
            "scope": "data_quality_only",
            "statement_zh": (
                f"当前 lineage complete={counts['lineage_complete_count']}、"
                f"missing={counts['lineage_missing_count']}，"
                f"metric status={coverage['metric_status']}；未完整前指标保持 blocked/null。"
            ),
            "evidence_refs": [STAGE7_WORKFLOW_REF],
        },
        {
            "code": "DQ-FALSE-ZERO-GATE",
            "scope": "data_quality_only",
            "statement_zh": (
                f"非 ready 指标假零数量为 "
                f"{coverage['non_ready_false_zero_count']}；本报告未输出财务数值。"
            ),
            "evidence_refs": [STAGE4_READ_MODEL_REF, STAGE7_WORKFLOW_REF],
        },
    ]


def _anomalies(
    dependency_states: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dependency_id, state in dependency_states.items():
        if state.get("status") == "ready":
            continue
        if dependency_id == "financial_analysis_implementation":
            continue
        rows.append(
            {
                "code": "DQ-" + re.sub(r"[^A-Z0-9]+", "-", dependency_id.upper()).strip("-"),
                "severity": (
                    "blocking"
                    if state.get("status") in {"blocked", "not_loaded"}
                    else "warning"
                ),
                "statement_zh": str(
                    state.get("blocking_reason_zh")
                    or "依赖未 ready，需要人工复核。"
                ),
                "evidence_refs": [
                    STAGE7_WORKFLOW_REF
                    if dependency_id == "economic_event_adapter"
                    else SOURCE_MANIFEST_REF
                ],
            }
        )
    return rows


def _snapshot_hash(snapshot: Mapping[str, Any]) -> str:
    return canonical_hash(
        {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    )


def _report_snapshot(
    *,
    report_type: str,
    generated_at: str,
    summary: Mapping[str, Any],
    hashes: Mapping[str, str],
    dependency_states: Mapping[str, Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    report_rules = rules["report_dependencies"][report_type]
    review_links = [str(value) for value in report_rules["review_links"]]
    status, partial_scope = derive_report_status(
        report_type, dependency_states, rules
    )
    dependency_ids = [str(value) for value in report_rules.get("critical", [])]
    dependency_rows = [
        {
            "dependency_id": dependency_id,
            "status": str(dependency_states[dependency_id]["status"]),
            "critical": True,
            "blocking_reason_zh": dependency_states[dependency_id].get(
                "blocking_reason_zh"
            ),
        }
        for dependency_id in dependency_ids
    ]
    gap_rows = _gaps(
        [
            {
                **row,
                "review_route": dependency_states[str(row["dependency_id"])].get(
                    "review_route"
                ),
            }
            for row in dependency_rows
        ],
        review_links,
    )
    if report_type == "data_quality":
        dependency_rows = [
            {
                "dependency_id": dependency_id,
                "status": str(state["status"]),
                "critical": False,
                "blocking_reason_zh": state.get("blocking_reason_zh"),
            }
            for dependency_id, state in dependency_states.items()
        ]
        gap_rows = _gaps(
            [
                {
                    **row,
                    "review_route": dependency_states[
                        str(row["dependency_id"])
                    ].get("review_route"),
                }
                for row in dependency_rows
            ],
            review_links,
        )
        conclusions = _data_quality_conclusions(summary)
        anomalies = _anomalies(dependency_states)
        conclusion_policy = "data_quality_only"
        rule_id = "data_quality"
    elif status == "partial":
        conclusions = [
            {
                "code": "REPORT-PARTIAL-SOURCE-COVERAGE",
                "scope": "source_coverage_only",
                "statement_zh": (
                    "交易来源的范围与样本元数据可追溯；经济事件适配和 Phase 9.2 "
                    "分析尚未完成，因此不生成消费、现金流金额或确定性财务结论。"
                ),
                "evidence_refs": [SOURCE_MANIFEST_REF, STAGE7_WORKFLOW_REF],
            }
        ]
        anomalies = []
        conclusion_policy = "scoped_partial_only"
        rule_id = str(partial_scope or "partial")
    else:
        conclusions = []
        anomalies = []
        conclusion_policy = (
            "financial_conclusion_allowed"
            if status == "complete"
            else "financial_conclusion_forbidden"
        )
        rule_id = status

    snapshot: dict[str, Any] = {
        "schema": "PFIV025ReportSnapshotV1",
        "report_id": f"pfi-v025-{report_type.replace('_', '-')}",
        "report_type": report_type,
        "status": status,
        "version": VERSION,
        "generated_at": generated_at,
        "report_as_of": str(summary["report_as_of"]),
        "data_range": deepcopy(summary["data_range"]),
        "sample_counts": deepcopy(summary["sample_counts"]),
        "coverage": deepcopy(summary["coverage"]),
        "hashes": dict(hashes),
        "dependencies": dependency_rows,
        "completeness": {
            "rule_id": rule_id,
            "critical_dependency_count": len(
                [row for row in dependency_rows if row["critical"]]
            ),
            "ready_dependency_count": sum(
                row["status"] == "ready" for row in dependency_rows
            ),
            "gap_count": len(gap_rows),
            "conclusion_policy": conclusion_policy,
        },
        "conclusions": conclusions,
        "anomalies": anomalies,
        "gaps": gap_rows,
        "limitations": [
            "本 Phase 只建立报告合同、完整度和数据质量报告，不实现 Phase 9.2 财务分析。",
            "报告仅包含 aggregate metadata 与 hash，不含账户标识、原始行或财务数值。",
            "blocked/partial 状态不得解释为模型有效或完整财务结论。",
        ],
        "review_links": review_links,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "immutable": True,
    }
    snapshot["snapshot_hash"] = _snapshot_hash(snapshot)
    return snapshot


def build_phase91_report_pack(
    pfi_root: Path | str | None = None,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = (
        Path(pfi_root).expanduser().resolve()
        if pfi_root is not None
        else PFI_ROOT
    )
    source_manifest = _json_object(root / SOURCE_MANIFEST_RELATIVE)
    read_model_status = _json_object(root / STAGE4_READ_MODEL_RELATIVE)
    workflow_validation = _json_object(root / STAGE7_WORKFLOW_RELATIVE)
    rules = _json_object(root / COMPLETENESS_RULES_RELATIVE)
    dependency_states = _source_dependency_states(
        source_manifest, workflow_validation
    )
    hashes = _input_hashes(
        root, source_manifest, read_model_status, workflow_validation
    )
    summary = _source_summary(source_manifest, workflow_validation)
    observed_at = generated_at or _now()
    reports = [
        _report_snapshot(
            report_type=report_type,
            generated_at=observed_at,
            summary=summary,
            hashes=hashes,
            dependency_states=dependency_states,
            rules=rules,
        )
        for report_type in REPORT_TYPES
    ]
    pack: dict[str, Any] = {
        "schema": "PFIV025Stage9Phase91ReportManifestV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass",
        "generated_at": observed_at,
        "report_as_of": summary["report_as_of"],
        "data_range": summary["data_range"],
        "sample_counts": summary["sample_counts"],
        "coverage": summary["coverage"],
        "hashes": hashes,
        "reports": reports,
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "input_files_read_only": True,
        "database_read": False,
        "database_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "phase_9_2_started": False,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
    }
    pack["manifest_hash"] = canonical_hash(pack)
    return pack


def validate_phase91_report_pack(
    pack: Mapping[str, Any],
    *,
    pfi_root: Path | str | None = None,
) -> dict[str, Any]:
    root = (
        Path(pfi_root).expanduser().resolve()
        if pfi_root is not None
        else PFI_ROOT
    )
    errors: list[str] = []
    if pack.get("schema") != "PFIV025Stage9Phase91ReportManifestV1":
        errors.append("manifest schema mismatch")
    if pack.get("phase_id") != PHASE_ID or pack.get("task_ids") != list(TASK_IDS):
        errors.append("phase/task binding mismatch")
    if pack.get("acceptance_id") != ACCEPTANCE_ID:
        errors.append("acceptance binding mismatch")
    if pack.get("contains_private_values") is not False:
        errors.append("private values are forbidden")
    if pack.get("financial_values_emitted") != 0:
        errors.append("financial values are forbidden in Phase 9.1 evidence")
    if pack.get("phase_9_2_started") is not False:
        errors.append("Phase 9.2 scope leak")
    if pack.get("phase_9_3_started") is not False:
        errors.append("Phase 9.3 scope leak")
    if pack.get("stage_9_whole_stage_review_done") is not False:
        errors.append("Stage 9 whole-stage review scope leak")
    if pack.get("input_files_read_only") is not True:
        errors.append("input files must remain read-only")
    if (
        pack.get("database_read") is not False
        or pack.get("database_changed") is not False
    ):
        errors.append("database access is forbidden in Phase 9.1")
    if (
        pack.get("formula_values_changed") is not False
        or pack.get("parameter_values_changed") is not False
    ):
        errors.append("formula/parameter values changed in Phase 9.1")
    reports = pack.get("reports")
    if not isinstance(reports, list):
        reports = []
        errors.append("reports must be a list")
    by_type = {
        str(row.get("report_type")): row
        for row in reports
        if isinstance(row, Mapping)
    }
    if set(by_type) != set(REPORT_TYPES) or len(reports) != len(REPORT_TYPES):
        errors.append("report type set must be exact and unique")
    rules = _json_object(root / COMPLETENESS_RULES_RELATIVE)
    source_manifest = _json_object(root / SOURCE_MANIFEST_RELATIVE)
    read_model_status = _json_object(root / STAGE4_READ_MODEL_RELATIVE)
    workflow = _json_object(root / STAGE7_WORKFLOW_RELATIVE)
    dependency_states = _source_dependency_states(source_manifest, workflow)
    expected_hashes = pack.get("hashes")
    if not isinstance(expected_hashes, Mapping):
        expected_hashes = {}
        errors.append("manifest hashes are missing")
    current_hashes = _input_hashes(
        root,
        source_manifest,
        read_model_status,
        workflow,
    )
    if expected_hashes != current_hashes:
        errors.append("manifest hashes differ from current accepted inputs")
    for report_type, row in by_type.items():
        if row.get("status") not in COMPLETENESS_STATUSES:
            errors.append(f"{report_type}: unsupported completeness status")
        if row.get("hashes") != expected_hashes:
            errors.append(f"{report_type}: cross-report hash mismatch")
        if row.get("snapshot_hash") != _snapshot_hash(row):
            errors.append(f"{report_type}: snapshot hash mismatch")
        dependencies = row.get("dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"{report_type}: dependencies must be a list")
            continue
        ids = [
            str(item.get("dependency_id"))
            for item in dependencies
            if isinstance(item, Mapping)
        ]
        if len(ids) != len(set(ids)) or len(ids) != len(dependencies):
            errors.append(f"{report_type}: dependency IDs must be unique objects")
        expected_status, _ = derive_report_status(
            report_type, dependency_states, rules
        )
        if row.get("status") != expected_status:
            errors.append(f"{report_type}: completeness status is not rebuildable")
        conclusions = row.get("conclusions")
        gaps = row.get("gaps")
        if not isinstance(conclusions, list) or not isinstance(gaps, list):
            errors.append(f"{report_type}: conclusions/gaps must be lists")
            continue
        if report_type == "data_quality":
            if row.get("status") != "complete" or not conclusions:
                errors.append("data_quality must always be complete with quality conclusions")
        elif row.get("status") == "blocked" and conclusions:
            errors.append(f"{report_type}: blocked report emitted conclusions")
        elif row.get("status") == "partial":
            if (
                not conclusions
                or not all(isinstance(item, Mapping) for item in conclusions)
                or any(
                    item.get("scope") != "source_coverage_only"
                    for item in conclusions
                    if isinstance(item, Mapping)
                )
            ):
                errors.append(f"{report_type}: partial conclusions exceed safe scope")
        if row.get("status") != "complete" and not gaps:
            errors.append(f"{report_type}: incomplete report requires explicit gaps")
        if row.get("financial_values_emitted") != 0:
            errors.append(f"{report_type}: financial values emitted")
        if row.get("contains_private_values") is not False:
            errors.append(f"{report_type}: private values emitted")
    expected_manifest_hash = canonical_hash(
        {key: value for key, value in pack.items() if key != "manifest_hash"}
    )
    if pack.get("manifest_hash") != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    serialized = json.dumps(pack, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in (
        "/users/",
        "cny 0.00",
        "mock_financial",
        "sample_financial",
        "demo_financial",
        "synthetic_financial",
        "fixture_financial",
        "fake_financial",
    ):
        if forbidden in serialized:
            errors.append(f"forbidden evidence content: {forbidden}")
    return {
        "schema": "PFIV025Stage9Phase91ReportValidationV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "report_count": len(reports),
        "report_types": sorted(by_type),
        "complete_report_ids": sorted(
            str(row.get("report_id"))
            for row in reports
            if isinstance(row, Mapping) and row.get("status") == "complete"
        ),
        "partial_report_ids": sorted(
            str(row.get("report_id"))
            for row in reports
            if isinstance(row, Mapping) and row.get("status") == "partial"
        ),
        "blocked_report_ids": sorted(
            str(row.get("report_id"))
            for row in reports
            if isinstance(row, Mapping) and row.get("status") == "blocked"
        ),
        "cross_report_hashes_consistent": all(
            isinstance(row, Mapping) and row.get("hashes") == expected_hashes
            for row in reports
        ),
        "financial_values_emitted": int(pack.get("financial_values_emitted") or 0),
        "contains_private_values": bool(pack.get("contains_private_values")),
    }
