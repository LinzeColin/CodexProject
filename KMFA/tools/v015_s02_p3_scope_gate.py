#!/usr/bin/env python3
"""Build and validate KMFA v1.5 S02-P3 scope/change-control contracts.

The module is deliberately planning-only.  It reads the public-safe S02-P1
registries and the versioned TaskPack package, but never reads the raw business
inbox and never enables product, report, payment, tax, invoice, payroll, or
external-send behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence
from zipfile import ZipFile


SOURCE_PACKAGE_NAME = (
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
P1_MACHINE_ROOT = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine"
)
REQUIREMENTS_PATH = P1_MACHINE_ROOT / "requirements_ledger_public_safe.csv"
BUSINESS_LINE_PATH = P1_MACHINE_ROOT / "business_line_matrix_public_safe.csv"
SCOPE_LOCK_PATH = P1_MACHINE_ROOT / "scope_lock_dispositions_public_safe.csv"

SCOPE_COLUMNS = (
    "scope_item_type",
    "scope_item_id",
    "priority",
    "scope_item_name",
    "source_scope_ref",
    "roadmap_stage_refs",
    "delivery_route",
    "scope_status",
    "in_scope_registry",
    "priority_locked_by_s02_p3",
    "quality_gate_required",
    "change_control_required",
    "time_pressure_quality_tradeoff_allowed",
    "product_acceptance_inherited",
    "implementation_authorized_by_s02_p3",
    "public_safe_status",
)

PROHIBITION_COLUMNS = (
    "prohibition_id",
    "source_scope",
    "source_ref",
    "business_line_id",
    "action_family",
    "prohibited_action",
    "detection_tokens",
    "hard_stop_condition",
    "required_response",
    "hard_stop_required",
    "planning_gate_defined",
    "automatic_execution_allowed",
    "runtime_guard_implemented",
    "prohibited_action_implemented_in_s02_p3",
    "product_action_authorized",
    "merge_allowed_on_detection",
    "stop_triggered_in_s02_p3",
    "change_control_can_override",
    "owner_authorization_can_override",
    "public_safe_status",
)

EXPLICIT_PROHIBITIONS = (
    ("PAYMENT", "付款", ("付款", "支付", "bank payment")),
    ("TAX_FILING", "报税", ("报税", "纳税申报", "tax filing")),
    ("INVOICE_ISSUANCE", "开票", ("开票", "开发票", "invoice issuance")),
    ("PAYROLL_APPROVAL", "工资审批", ("工资审批", "奖金审批", "payroll approval")),
    (
        "FULL_REPORT_EXTERNAL_SEND",
        "对外发送完整报告",
        ("对外发送完整报告", "完整经营报告", "external full report"),
    ),
    (
        "RAW_DATA_MUTATION",
        "修改原始数据",
        (
            "修改原始数据",
            "创建 raw",
            "删除 raw",
            "移动 raw",
            "重命名 raw",
            "覆盖 raw",
            "原地解压",
            "原地转换",
            "raw 写缓存",
            "raw 写日志",
            "raw mutation",
        ),
    ),
)

AUDITABLE_DOMAINS = ("FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT")
CHANGE_TYPES = ("REQUIREMENT", "FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT")
PRIORITIES = ("P0", "P1", "P2", "NA")
REQUIRED_CHANGE_FIELDS = (
    "schema_version",
    "change_id",
    "requested_at",
    "requester_role",
    "change_type",
    "reason",
    "affected_requirement_ids",
    "affected_scope_item_ids",
    "affected_stage_phase_task_refs",
    "affected_artifact_refs",
    "impact_domains",
    "before_version",
    "after_version",
    "old_priority",
    "new_priority",
    "priority_change_justification",
    "time_pressure_only",
    "quality_tradeoff_allowed",
    "scope_disposition",
    "impact_summary",
    "security_impact",
    "privacy_impact",
    "precision_impact",
    "report_impact",
    "acceptance_impact",
    "regression_scope",
    "risk_level",
    "approval_state",
    "approver_role",
    "change_state",
    "implementation_refs",
    "validation_refs",
    "evidence_refs",
    "rollback_plan",
    "audit_event_refs",
    "public_safe_status",
)
DOMAIN_REQUIREMENTS = {
    "FRONTEND": ("user_flow", "accessibility", "runtime_e2e"),
    "BACKEND": ("api_contract", "persistence", "authorization", "error_path"),
    "FORMULA": ("fixture", "boundary", "precision", "zero_delta"),
    "DATA_CONTRACT": ("schema", "migration", "lineage", "compatibility"),
}
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
_PUBLIC_SAFE_FORBIDDEN = (
    "/Users/",
    "/Volumes/",
    "/private/",
    "/tmp/",
    "KMFA_MetaData",
    "/home/",
)


class ScopeGateError(RuntimeError):
    """Raised when authoritative S02-P3 planning evidence is invalid."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _public_safe_errors(value: Any) -> list[str]:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    errors = [
        "PUBLIC_SAFE_TOKEN_VIOLATION"
        for token in _PUBLIC_SAFE_FORBIDDEN
        if token in encoded
    ]
    if _EMAIL_RE.search(encoded):
        errors.append("PUBLIC_SAFE_EMAIL_VIOLATION")
    return sorted(set(errors))


def load_s02_p3_task_contract(
    source_package: Path = DEFAULT_SOURCE_PACKAGE,
) -> dict[str, dict[str, str]]:
    """Load the exact three S02-P3 tasks from the authoritative package."""

    package = Path(source_package)
    if not package.is_file():
        raise ScopeGateError("source package missing")
    if _sha256(package) != SOURCE_PACKAGE_SHA256:
        raise ScopeGateError("source package SHA-256 drift")
    with ZipFile(package) as archive:
        members = [
            name
            for name in archive.namelist()
            if name.rsplit("/", 1)[-1].startswith("02B_")
            and name.endswith(".json")
        ]
        if len(members) != 1:
            raise ScopeGateError("source roadmap member count drift")
        roadmap = json.loads(archive.read(members[0]).decode("utf-8-sig"))
    if (
        roadmap.get("stage_count"),
        roadmap.get("phase_count"),
        roadmap.get("task_count"),
    ) != (24, 72, 216):
        raise ScopeGateError("source roadmap 24/72/216 drift")
    stages = [stage for stage in roadmap.get("stages", []) if stage.get("id") == "S02"]
    if len(stages) != 1:
        raise ScopeGateError("S02 source stage count drift")
    phases = [phase for phase in stages[0].get("phases", []) if phase.get("id") == "P3"]
    if len(phases) != 1:
        raise ScopeGateError("S02-P3 source phase count drift")
    contract: dict[str, dict[str, str]] = {}
    for task in phases[0].get("tasks", []):
        task_id = "S02P3" + str(task.get("id", ""))
        contract[task_id] = {
            "name": str(task.get("name", "")),
            "action": str(task.get("action", "")),
            "output": str(task.get("output", "")),
            "acceptance": str(task.get("acceptance", "")),
            "evidence": str(task.get("evidence", "")),
            "stop": str(task.get("stop", "")),
        }
    expected = {
        "S02P3T01": "锁定 P0/P1/P2 范围",
        "S02P3T02": "锁定禁止事项",
        "S02P3T03": "建立变更控制",
    }
    if {key: value.get("name") for key, value in contract.items()} != expected:
        raise ScopeGateError("S02-P3 task identity drift")
    return contract


def _requirement_route(row: Mapping[str, str]) -> str:
    item_id = row["requirement_id"]
    if item_id == "R004":
        return "V15_PROJECT_COST_FIRST"
    if item_id == "R018":
        return "V15_FILE_IMPORT_FIRST_AUTOMATION_LATER"
    if item_id == "R052":
        return "POST_STABILITY_SEPARATE_CONNECTOR"
    if item_id == "R053":
        return "FUTURE_SEPARATE_INITIATIVE"
    if item_id == "R054":
        return "POST_STABILITY_LOW_COUPLING_INTEGRATION"
    return "V15_MANDATORY" if row["priority"] == "P0" else "V15_CORE_AFTER_PROJECT_COST"


def _business_line_route(row: Mapping[str, str]) -> str:
    if row["business_line_id"] == "BL-01":
        return "V15_PROJECT_COST_FIRST"
    if row["priority"] == "P1":
        return "V15_CORE_AFTER_PROJECT_COST"
    return "V15_LATER_WAVE_CONTROLLED"


def _capability_route(row: Mapping[str, str]) -> str:
    if row["capability_id"] == "CAP-037":
        return "POST_STABILITY_SEPARATE_CONNECTOR"
    return {
        "KEEP_GOVERNANCE_BASELINE": "V15_PRESERVE_AND_REVALIDATE",
        "REBUILD": "V15_REBUILD",
        "DEPRECATE": "V15_DEPRECATE",
        "DEFER": "V15_LATER_STAGE_REIMPLEMENT_OR_VERIFY",
    }[row["v15_scope_class"]]


def build_scope_priority_rows(
    requirements_path: Path = REQUIREMENTS_PATH,
    business_line_path: Path = BUSINESS_LINE_PATH,
    scope_lock_path: Path = SCOPE_LOCK_PATH,
) -> list[dict[str, Any]]:
    """Build one scope-lock row for every requirement, line, and capability."""

    requirements = _read_csv(Path(requirements_path))
    business_lines = _read_csv(Path(business_line_path))
    capabilities = _read_csv(Path(scope_lock_path))
    if len(requirements) != 55 or len(business_lines) != 10 or len(capabilities) != 37:
        raise ScopeGateError("S02-P1 priority authority count drift")
    rows: list[dict[str, Any]] = []
    for source in requirements:
        rows.append(
            {
                "scope_item_type": "REQUIREMENT",
                "scope_item_id": source["requirement_id"],
                "priority": source["priority"],
                "scope_item_name": source["requirement_name"],
                "source_scope_ref": (
                    "S02-P1.requirements_ledger_public_safe.csv#"
                    + source["requirement_id"]
                ),
                "roadmap_stage_refs": source["primary_stage_refs"],
                "delivery_route": _requirement_route(source),
                "scope_status": "LOCKED_PLANNING_ONLY",
                "in_scope_registry": True,
                "priority_locked_by_s02_p3": True,
                "quality_gate_required": True,
                "change_control_required": True,
                "time_pressure_quality_tradeoff_allowed": False,
                "product_acceptance_inherited": False,
                "implementation_authorized_by_s02_p3": False,
                "public_safe_status": "PUBLIC_SAFE",
            }
        )
    for source in business_lines:
        rows.append(
            {
                "scope_item_type": "BUSINESS_LINE",
                "scope_item_id": source["business_line_id"],
                "priority": source["priority"],
                "scope_item_name": source["business_line_name"],
                "source_scope_ref": (
                    "S02-P1.business_line_matrix_public_safe.csv#"
                    + source["business_line_id"]
                ),
                "roadmap_stage_refs": source["recommended_stage_ids"],
                "delivery_route": _business_line_route(source),
                "scope_status": "LOCKED_PLANNING_ONLY",
                "in_scope_registry": True,
                "priority_locked_by_s02_p3": True,
                "quality_gate_required": True,
                "change_control_required": True,
                "time_pressure_quality_tradeoff_allowed": False,
                "product_acceptance_inherited": False,
                "implementation_authorized_by_s02_p3": False,
                "public_safe_status": "PUBLIC_SAFE",
            }
        )
    for source in capabilities:
        rows.append(
            {
                "scope_item_type": "CAPABILITY",
                "scope_item_id": source["capability_id"],
                "priority": "NA",
                "scope_item_name": source["capability_name"],
                "source_scope_ref": (
                    "S02-P1.scope_lock_dispositions_public_safe.csv#"
                    + source["capability_id"]
                ),
                "roadmap_stage_refs": source["target_stage"],
                "delivery_route": _capability_route(source),
                "scope_status": "LOCKED_PLANNING_ONLY",
                "in_scope_registry": True,
                "priority_locked_by_s02_p3": True,
                "quality_gate_required": True,
                "change_control_required": True,
                "time_pressure_quality_tradeoff_allowed": False,
                "product_acceptance_inherited": False,
                "implementation_authorized_by_s02_p3": False,
                "public_safe_status": "PUBLIC_SAFE",
            }
        )
    rows.append(
        {
            "scope_item_type": "POLICY",
            "scope_item_id": "DEFERRED-POLICY-CONTRACT-SCANNING",
            "priority": "NA",
            "scope_item_name": "合同扫描后置策略",
            "source_scope_ref": (
                "SOURCE_PACKAGE_TOKEN::S02P3T01;"
                "SOURCE_PACKAGE_TOKEN::09_KMFA_数据源检查矩阵模板_v2_0.csv"
            ),
            "roadmap_stage_refs": "S24",
            "delivery_route": "FUTURE_SEPARATE_CONTRACT_SCANNING",
            "scope_status": "LOCKED_PLANNING_ONLY",
            "in_scope_registry": True,
            "priority_locked_by_s02_p3": True,
            "quality_gate_required": True,
            "change_control_required": True,
            "time_pressure_quality_tradeoff_allowed": False,
            "product_acceptance_inherited": False,
            "implementation_authorized_by_s02_p3": False,
            "public_safe_status": "PUBLIC_SAFE",
        }
    )
    errors = validate_scope_priority_rows(rows)
    if errors:
        raise ScopeGateError("scope priority invalid: " + "; ".join(errors))
    return rows


def _authoritative_scope_semantics() -> dict[tuple[str, str], dict[str, str]]:
    expected: dict[tuple[str, str], dict[str, str]] = {}
    for source in _read_csv(REQUIREMENTS_PATH):
        item_id = source["requirement_id"]
        expected[("REQUIREMENT", item_id)] = {
            "priority": source["priority"],
            "scope_item_name": source["requirement_name"],
            "source_scope_ref": (
                "S02-P1.requirements_ledger_public_safe.csv#" + item_id
            ),
            "roadmap_stage_refs": source["primary_stage_refs"],
            "delivery_route": _requirement_route(source),
        }
    for source in _read_csv(BUSINESS_LINE_PATH):
        item_id = source["business_line_id"]
        expected[("BUSINESS_LINE", item_id)] = {
            "priority": source["priority"],
            "scope_item_name": source["business_line_name"],
            "source_scope_ref": (
                "S02-P1.business_line_matrix_public_safe.csv#" + item_id
            ),
            "roadmap_stage_refs": source["recommended_stage_ids"],
            "delivery_route": _business_line_route(source),
        }
    for source in _read_csv(SCOPE_LOCK_PATH):
        item_id = source["capability_id"]
        expected[("CAPABILITY", item_id)] = {
            "priority": "NA",
            "scope_item_name": source["capability_name"],
            "source_scope_ref": (
                "S02-P1.scope_lock_dispositions_public_safe.csv#" + item_id
            ),
            "roadmap_stage_refs": source["target_stage"],
            "delivery_route": _capability_route(source),
        }
    expected[("POLICY", "DEFERRED-POLICY-CONTRACT-SCANNING")] = {
        "priority": "NA",
        "scope_item_name": "合同扫描后置策略",
        "source_scope_ref": (
            "SOURCE_PACKAGE_TOKEN::S02P3T01;"
            "SOURCE_PACKAGE_TOKEN::09_KMFA_数据源检查矩阵模板_v2_0.csv"
        ),
        "roadmap_stage_refs": "S24",
        "delivery_route": "FUTURE_SEPARATE_CONTRACT_SCANNING",
    }
    return expected


def validate_scope_priority_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    keys = [(row.get("scope_item_type"), row.get("scope_item_id")) for row in rows]
    if len(rows) != 103:
        errors.append("SCOPE_ROW_COUNT_MISMATCH")
    if len(keys) != len(set(keys)):
        errors.append("SCOPE_ID_NOT_UNIQUE")
    requirement_ids = {
        str(row.get("scope_item_id"))
        for row in rows
        if row.get("scope_item_type") == "REQUIREMENT"
    }
    business_line_ids = {
        str(row.get("scope_item_id"))
        for row in rows
        if row.get("scope_item_type") == "BUSINESS_LINE"
    }
    capability_ids = {
        str(row.get("scope_item_id"))
        for row in rows
        if row.get("scope_item_type") == "CAPABILITY"
    }
    policy_ids = {
        str(row.get("scope_item_id"))
        for row in rows
        if row.get("scope_item_type") == "POLICY"
    }
    if requirement_ids != {f"R{index:03d}" for index in range(1, 56)}:
        errors.append("REQUIREMENT_SCOPE_COVERAGE_MISMATCH")
    if business_line_ids != {f"BL-{index:02d}" for index in range(1, 11)}:
        errors.append("BUSINESS_LINE_SCOPE_COVERAGE_MISMATCH")
    if capability_ids != {f"CAP-{index:03d}" for index in range(1, 38)}:
        errors.append("CAPABILITY_SCOPE_COVERAGE_MISMATCH")
    if policy_ids != {"DEFERRED-POLICY-CONTRACT-SCANNING"}:
        errors.append("DEFERRED_POLICY_SCOPE_COVERAGE_MISMATCH")
    expected_counts = {
        ("REQUIREMENT", "P0"): 46,
        ("REQUIREMENT", "P1"): 8,
        ("REQUIREMENT", "P2"): 1,
        ("BUSINESS_LINE", "P0"): 1,
        ("BUSINESS_LINE", "P1"): 7,
        ("BUSINESS_LINE", "P2"): 2,
        ("CAPABILITY", "NA"): 37,
        ("POLICY", "NA"): 1,
    }
    actual_counts: dict[tuple[Any, Any], int] = {}
    for row in rows:
        key = (row.get("scope_item_type"), row.get("priority"))
        actual_counts[key] = actual_counts.get(key, 0) + 1
        if set(row) != set(SCOPE_COLUMNS):
            errors.append("SCOPE_SCHEMA_MISMATCH")
        for field in (
            "scope_item_id",
            "scope_item_name",
            "source_scope_ref",
            "roadmap_stage_refs",
            "delivery_route",
        ):
            if not _non_empty(row.get(field)):
                errors.append("SCOPE_REQUIRED_FIELD_MISSING")
        for field in (
            "in_scope_registry",
            "priority_locked_by_s02_p3",
            "quality_gate_required",
            "change_control_required",
        ):
            if row.get(field) is not True:
                errors.append("SCOPE_FAIL_CLOSED_GATE_MISSING")
        for field in (
            "time_pressure_quality_tradeoff_allowed",
            "product_acceptance_inherited",
            "implementation_authorized_by_s02_p3",
        ):
            if row.get(field) is not False:
                errors.append("SCOPE_BOUNDARY_VIOLATION")
        if row.get("scope_status") != "LOCKED_PLANNING_ONLY":
            errors.append("SCOPE_STATUS_DRIFT")
        if row.get("public_safe_status") != "PUBLIC_SAFE":
            errors.append("SCOPE_PUBLIC_SAFE_STATUS_DRIFT")
    if actual_counts != expected_counts:
        errors.append("SCOPE_PRIORITY_ACCOUNTING_MISMATCH")
    try:
        authority = _authoritative_scope_semantics()
    except (KeyError, OSError, csv.Error):
        errors.append("SCOPE_AUTHORITY_UNAVAILABLE")
        authority = {}
    for row in rows:
        key = (str(row.get("scope_item_type")), str(row.get("scope_item_id")))
        expected = authority.get(key)
        if expected is None or any(row.get(field) != value for field, value in expected.items()):
            errors.append("SCOPE_AUTHORITATIVE_SEMANTIC_DRIFT")
    by_id = {str(row.get("scope_item_id")): row for row in rows}
    for item_id, route in {
        "R004": "V15_PROJECT_COST_FIRST",
        "R018": "V15_FILE_IMPORT_FIRST_AUTOMATION_LATER",
        "R052": "POST_STABILITY_SEPARATE_CONNECTOR",
        "R053": "FUTURE_SEPARATE_INITIATIVE",
        "R054": "POST_STABILITY_LOW_COUPLING_INTEGRATION",
        "BL-01": "V15_PROJECT_COST_FIRST",
        "CAP-037": "POST_STABILITY_SEPARATE_CONNECTOR",
        "DEFERRED-POLICY-CONTRACT-SCANNING": "FUTURE_SEPARATE_CONTRACT_SCANNING",
    }.items():
        if by_id.get(item_id, {}).get("delivery_route") != route:
            errors.append("SCOPE_SPECIAL_ROUTE_DRIFT")
    errors.extend(_public_safe_errors(rows))
    return sorted(set(errors))


def _classify_action(action: str) -> str:
    lower = action.lower()
    if any(token in lower for token in ("raw", "原始", "修改来源")):
        return "RAW_DATA_MUTATION"
    if any(token in action for token in ("纳税申报", "报税", "税务调整", "政策申报")):
        return "TAX_FILING"
    if any(token in action for token in ("开发票", "开票")):
        return "INVOICE_ISSUANCE"
    if "付款" in action:
        return "PAYMENT"
    if any(token in action for token in ("工资", "奖金", "绩效审批", "薪资")):
        return "PAYROLL_APPROVAL"
    if "报告" in action and any(token in action for token in ("发送", "发布")):
        return "FULL_REPORT_EXTERNAL_SEND"
    if any(token in action for token in ("会计", "入账")):
        return "ACCOUNTING_POSTING"
    if any(token in action for token in ("采购", "下单", "供应商选择")):
        return "PROCUREMENT_COMMITMENT"
    if any(token in action for token in ("贷款交易", "银行交易")):
        return "FINANCIAL_TRANSACTION"
    if any(token in action for token in ("联系客户", "法律文件", "法律/专业")):
        return "EXTERNAL_CONTACT_OR_LEGAL"
    if any(token in action for token in ("技术决策", "安全决策", "技术/安全签字")):
        return "SAFETY_TECHNICAL_DECISION"
    if any(token in action for token in ("老板最终", "最终经营判断")):
        return "EXECUTIVE_DECISION"
    if "跨主体" in action:
        return "CROSS_ENTITY_MERGE"
    if any(token in action for token in ("自动", "低置信", "无证据")):
        return "AUTOMATED_UNVERIFIED_DECISION"
    if any(token in action for token in ("预测", "事实", "标完整")):
        return "FACT_INTEGRITY"
    return "OTHER_HIGH_RISK_ACTION"


def _prohibition_row(
    prohibition_id: str,
    source_scope: str,
    source_ref: str,
    business_line_id: str,
    action_family: str,
    action: str,
    detection_tokens: Sequence[str],
) -> dict[str, Any]:
    return {
        "prohibition_id": prohibition_id,
        "source_scope": source_scope,
        "source_ref": source_ref,
        "business_line_id": business_line_id,
        "action_family": action_family,
        "prohibited_action": action,
        "detection_tokens": list(detection_tokens),
        "hard_stop_condition": "DETECT_INTENT_OR_IMPLEMENTATION::" + action_family,
        "required_response": "STOP_AND_BLOCK_MERGE",
        "hard_stop_required": True,
        "planning_gate_defined": True,
        "automatic_execution_allowed": False,
        "runtime_guard_implemented": False,
        "prohibited_action_implemented_in_s02_p3": False,
        "product_action_authorized": False,
        "merge_allowed_on_detection": False,
        "stop_triggered_in_s02_p3": False,
        "change_control_can_override": False,
        "owner_authorization_can_override": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _authoritative_prohibition_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (family, action, tokens) in enumerate(EXPLICIT_PROHIBITIONS, 1):
        rows.append(
            _prohibition_row(
                f"PROH-S02P3-{index:03d}",
                "S02_P3_EXPLICIT",
                "SOURCE_PACKAGE_TOKEN::S02P3T02",
                "",
                family,
                action,
                tokens,
            )
        )
    for source in _read_csv(BUSINESS_LINE_PATH):
        fragments = [
            fragment.strip()
            for fragment in source["prohibited_automatic_actions"].split("；")
            if fragment.strip()
        ]
        for index, action in enumerate(fragments, 1):
            family = _classify_action(action)
            rows.append(
                _prohibition_row(
                    f"PROH-{source['business_line_id'].replace('-', '')}-{index:03d}",
                    "BUSINESS_LINE_MATRIX",
                    "S02-P1.business_line_matrix_public_safe.csv#"
                    + source["business_line_id"],
                    source["business_line_id"],
                    family,
                    action,
                    (action, family),
                )
            )
    return rows


def build_prohibited_action_rows(
    business_line_path: Path = BUSINESS_LINE_PATH,
) -> list[dict[str, Any]]:
    """Build explicit and business-line-complete high-risk hard-stop rows."""

    rows: list[dict[str, Any]] = []
    for index, (family, action, tokens) in enumerate(EXPLICIT_PROHIBITIONS, 1):
        rows.append(
            _prohibition_row(
                f"PROH-S02P3-{index:03d}",
                "S02_P3_EXPLICIT",
                "SOURCE_PACKAGE_TOKEN::S02P3T02",
                "",
                family,
                action,
                tokens,
            )
        )
    business_lines = _read_csv(Path(business_line_path))
    if len(business_lines) != 10:
        raise ScopeGateError("business-line prohibition authority count drift")
    for source in business_lines:
        fragments = [
            fragment.strip()
            for fragment in source["prohibited_automatic_actions"].split("；")
            if fragment.strip()
        ]
        if not fragments:
            raise ScopeGateError("business-line prohibition list empty")
        for index, action in enumerate(fragments, 1):
            family = _classify_action(action)
            rows.append(
                _prohibition_row(
                    f"PROH-{source['business_line_id'].replace('-', '')}-{index:03d}",
                    "BUSINESS_LINE_MATRIX",
                    "S02-P1.business_line_matrix_public_safe.csv#"
                    + source["business_line_id"],
                    source["business_line_id"],
                    family,
                    action,
                    (action, family),
                )
            )
    errors = validate_prohibited_action_rows(rows)
    if errors:
        raise ScopeGateError("prohibition contract invalid: " + "; ".join(errors))
    return rows


def validate_prohibited_action_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    ids = [str(row.get("prohibition_id", "")) for row in rows]
    if len(rows) != 51:
        errors.append("PROHIBITION_ROW_COUNT_MISMATCH")
    if not rows or len(ids) != len(set(ids)):
        errors.append("PROHIBITION_ID_NOT_UNIQUE")
    explicit = {
        str(row.get("action_family"))
        for row in rows
        if row.get("source_scope") == "S02_P3_EXPLICIT"
    }
    if explicit != {row[0] for row in EXPLICIT_PROHIBITIONS}:
        errors.append("EXPLICIT_PROHIBITION_COVERAGE_MISMATCH")
    if sum(row.get("source_scope") == "S02_P3_EXPLICIT" for row in rows) != 6:
        errors.append("EXPLICIT_PROHIBITION_COUNT_MISMATCH")
    business_lines = {
        str(row.get("business_line_id"))
        for row in rows
        if row.get("source_scope") == "BUSINESS_LINE_MATRIX"
    }
    if business_lines != {f"BL-{index:02d}" for index in range(1, 11)}:
        errors.append("BUSINESS_LINE_PROHIBITION_COVERAGE_MISMATCH")
    if sum(row.get("source_scope") == "BUSINESS_LINE_MATRIX" for row in rows) != 45:
        errors.append("BUSINESS_LINE_PROHIBITION_COUNT_MISMATCH")
    try:
        authority = {
            str(row["prohibition_id"]): row
            for row in _authoritative_prohibition_rows()
        }
    except (KeyError, OSError, csv.Error):
        errors.append("PROHIBITION_AUTHORITY_UNAVAILABLE")
        authority = {}
    for row in rows:
        expected = authority.get(str(row.get("prohibition_id")))
        if expected is None or dict(row) != expected:
            errors.append("PROHIBITION_AUTHORITATIVE_SEMANTIC_DRIFT")
    for row in rows:
        if set(row) != set(PROHIBITION_COLUMNS):
            errors.append("PROHIBITION_SCHEMA_MISMATCH")
        for field in (
            "prohibition_id",
            "source_scope",
            "source_ref",
            "action_family",
            "prohibited_action",
            "detection_tokens",
            "hard_stop_condition",
            "required_response",
        ):
            if not _non_empty(row.get(field)):
                errors.append("PROHIBITION_REQUIRED_FIELD_MISSING")
        for field in ("hard_stop_required", "planning_gate_defined"):
            if row.get(field) is not True:
                errors.append("PROHIBITION_HARD_STOP_MISSING")
        for field in (
            "automatic_execution_allowed",
            "runtime_guard_implemented",
            "prohibited_action_implemented_in_s02_p3",
            "product_action_authorized",
            "merge_allowed_on_detection",
            "stop_triggered_in_s02_p3",
            "change_control_can_override",
            "owner_authorization_can_override",
        ):
            if row.get(field) is not False:
                errors.append("PROHIBITION_BOUNDARY_VIOLATION")
        if row.get("public_safe_status") != "PUBLIC_SAFE":
            errors.append("PROHIBITION_PUBLIC_SAFE_STATUS_DRIFT")
    errors.extend(_public_safe_errors(rows))
    return sorted(set(errors))


def build_change_control_protocol() -> dict[str, Any]:
    """Return the deterministic v1.5 change registration and merge contract."""

    return {
        "schema_version": "kmfa.v015.s02_p3_change_control_protocol.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "roadmap_phase_id": "S02-P3",
        "task_id": "S02P3T03",
        "protocol_version": "CHANGE-KMFA-V015-S02P3-001",
        "required_change_fields": list(REQUIRED_CHANGE_FIELDS),
        "auditable_domains": list(AUDITABLE_DOMAINS),
        "change_types": list(CHANGE_TYPES),
        "domain_requirements": {
            domain: list(requirements)
            for domain, requirements in DOMAIN_REQUIREMENTS.items()
        },
        "state_machine": {
            "states": [
                "DRAFT",
                "IMPACT_ASSESSED",
                "APPROVED",
                "IMPLEMENTED",
                "VALIDATED",
                "REJECTED",
                "CANCELLED",
            ],
            "initial_state": "DRAFT",
            "merge_eligible_state": "VALIDATED",
            "allowed_transitions": {
                "DRAFT": ["IMPACT_ASSESSED", "REJECTED", "CANCELLED"],
                "IMPACT_ASSESSED": ["APPROVED", "REJECTED", "CANCELLED"],
                "APPROVED": ["IMPLEMENTED", "CANCELLED"],
                "IMPLEMENTED": ["VALIDATED", "CANCELLED"],
                "VALIDATED": [],
                "REJECTED": [],
                "CANCELLED": [],
            },
        },
        "merge_gate": {
            "registration_required": True,
            "reason_required": True,
            "impact_assessment_required": True,
            "priority_decision_required": True,
            "regression_scope_required": True,
            "approval_required": True,
            "validation_required": True,
            "rollback_required": True,
            "audit_event_required": True,
            "unregistered_change_merge_allowed": False,
            "unapproved_change_merge_allowed": False,
            "unvalidated_change_merge_allowed": False,
        },
        "scope_integrity": {
            "new_requirement_registration_required": True,
            "time_pressure_quality_tradeoff_allowed": False,
            "priority_change_requires_justification": True,
            "p0_p1_silent_removal_allowed": False,
            "p2_silent_promotion_allowed": False,
            "prohibited_action_override_allowed": False,
        },
        "audit_event_contract": {
            "append_only": True,
            "silent_update_allowed": False,
            "content_hash_required": True,
            "actor_role_required": True,
            "timestamp_required": True,
            "reversal_event_required_after_approval": True,
        },
        "change_record_evaluator": (
            "KMFA.tools.v015_s02_p3_scope_gate.evaluate_change_record"
        ),
        "evaluator_scope": "PLANNING_SCHEMA_COMPLETENESS_ONLY",
        "registry_resolution_implemented_in_s02_p3": False,
        "artifact_reference_resolution_implemented_in_s02_p3": False,
        "audit_event_resolution_implemented_in_s02_p3": False,
        "merge_authorization_emitted_by_evaluator": False,
        "runtime_or_ci_hook_implemented_in_s02_p3": False,
        "product_implementation_authorized": False,
        "formal_report_authorized": False,
        "business_execution_authorized": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def validate_change_control_protocol(protocol: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if protocol.get("schema_version") != "kmfa.v015.s02_p3_change_control_protocol.v1":
        errors.append("CHANGE_PROTOCOL_SCHEMA_DRIFT")
    if protocol.get("auditable_domains") != list(AUDITABLE_DOMAINS):
        errors.append("CHANGE_PROTOCOL_DOMAIN_COVERAGE_MISMATCH")
    if protocol.get("change_types") != list(CHANGE_TYPES):
        errors.append("CHANGE_PROTOCOL_TYPE_COVERAGE_MISMATCH")
    if protocol.get("domain_requirements") != {
        domain: list(requirements)
        for domain, requirements in DOMAIN_REQUIREMENTS.items()
    }:
        errors.append("CHANGE_PROTOCOL_DOMAIN_REQUIREMENTS_DRIFT")
    if protocol.get("required_change_fields") != list(REQUIRED_CHANGE_FIELDS):
        errors.append("CHANGE_PROTOCOL_REQUIRED_FIELD_SET_DRIFT")
    state_machine = protocol.get("state_machine", {})
    if state_machine.get("merge_eligible_state") != "VALIDATED":
        errors.append("CHANGE_PROTOCOL_STATE_MACHINE_DRIFT")
    merge_gate = protocol.get("merge_gate", {})
    for field in (
        "registration_required",
        "reason_required",
        "impact_assessment_required",
        "priority_decision_required",
        "regression_scope_required",
        "approval_required",
        "validation_required",
        "rollback_required",
        "audit_event_required",
    ):
        if merge_gate.get(field) is not True:
            errors.append("CHANGE_PROTOCOL_MERGE_GATE_OPEN")
    for field in (
        "unregistered_change_merge_allowed",
        "unapproved_change_merge_allowed",
        "unvalidated_change_merge_allowed",
    ):
        if merge_gate.get(field) is not False:
            errors.append("CHANGE_PROTOCOL_FAIL_OPEN")
    integrity = protocol.get("scope_integrity", {})
    for field in (
        "new_requirement_registration_required",
        "priority_change_requires_justification",
    ):
        if integrity.get(field) is not True:
            errors.append("CHANGE_PROTOCOL_SCOPE_INTEGRITY_FAIL_OPEN")
    for field in (
        "time_pressure_quality_tradeoff_allowed",
        "p0_p1_silent_removal_allowed",
        "p2_silent_promotion_allowed",
        "prohibited_action_override_allowed",
    ):
        if integrity.get(field) is not False:
            errors.append("CHANGE_PROTOCOL_SCOPE_INTEGRITY_FAIL_OPEN")
    audit_contract = protocol.get("audit_event_contract", {})
    for field in (
        "append_only",
        "content_hash_required",
        "actor_role_required",
        "timestamp_required",
        "reversal_event_required_after_approval",
    ):
        if audit_contract.get(field) is not True:
            errors.append("CHANGE_PROTOCOL_AUDIT_CONTRACT_FAIL_OPEN")
    if audit_contract.get("silent_update_allowed") is not False:
        errors.append("CHANGE_PROTOCOL_AUDIT_CONTRACT_FAIL_OPEN")
    for field in (
        "registry_resolution_implemented_in_s02_p3",
        "artifact_reference_resolution_implemented_in_s02_p3",
        "audit_event_resolution_implemented_in_s02_p3",
        "merge_authorization_emitted_by_evaluator",
        "runtime_or_ci_hook_implemented_in_s02_p3",
        "product_implementation_authorized",
        "formal_report_authorized",
        "business_execution_authorized",
    ):
        if protocol.get(field) is not False:
            errors.append("CHANGE_PROTOCOL_PHASE_BOUNDARY_VIOLATION")
    if protocol.get("evaluator_scope") != "PLANNING_SCHEMA_COMPLETENESS_ONLY":
        errors.append("CHANGE_PROTOCOL_EVALUATOR_SCOPE_DRIFT")
    if protocol.get("public_safe_status") != "PUBLIC_SAFE":
        errors.append("CHANGE_PROTOCOL_PUBLIC_SAFE_STATUS_DRIFT")
    errors.extend(_public_safe_errors(protocol))
    return sorted(set(errors))


def evaluate_change_record(
    record: Mapping[str, Any],
    protocol: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Evaluate planning-schema completeness without authorizing a real merge.

    S02-P3 has no registry, artifact-reference, audit-event, runtime, or CI
    resolver.  A schema-complete record may therefore become a planning review
    candidate only; this function must never emit real merge eligibility.
    """

    active_protocol = build_change_control_protocol() if protocol is None else protocol
    protocol_errors = validate_change_control_protocol(active_protocol)
    blocking: list[str] = []
    if protocol_errors:
        blocking.append("CHANGE_PROTOCOL_INVALID")
    required_fields = active_protocol.get("required_change_fields", [])
    if any(field not in record or not _non_empty(record.get(field)) for field in required_fields):
        blocking.append("REQUIRED_CHANGE_FIELD_MISSING")
    registered = bool(
        record.get("schema_version") == "kmfa.v015.change_request.v1"
        and re.fullmatch(r"CHG-KMFA-V015-[0-9]{4,}", str(record.get("change_id", "")))
        and _non_empty(record.get("requested_at"))
        and _non_empty(record.get("requester_role"))
        and record.get("change_type") in CHANGE_TYPES
    )
    if not registered:
        blocking.append("CHANGE_NOT_REGISTERED")
    if record.get("change_type") == "REQUIREMENT" and not _non_empty(
        record.get("affected_requirement_ids")
    ):
        blocking.append("AFFECTED_REQUIREMENT_ID_MISSING")
    if not _non_empty(record.get("reason")):
        blocking.append("CHANGE_REASON_MISSING")

    impact_domains = record.get("impact_domains", [])
    impact_assessed = bool(
        isinstance(impact_domains, list)
        and impact_domains
        and set(impact_domains).issubset(set(AUDITABLE_DOMAINS))
        and _non_empty(record.get("impact_summary"))
        and _non_empty(record.get("affected_scope_item_ids"))
        and _non_empty(record.get("affected_stage_phase_task_refs"))
        and _non_empty(record.get("affected_artifact_refs"))
        and _non_empty(record.get("before_version"))
        and _non_empty(record.get("after_version"))
        and all(
            _non_empty(record.get(field))
            for field in (
                "security_impact",
                "privacy_impact",
                "precision_impact",
                "report_impact",
                "acceptance_impact",
            )
        )
    )
    if not impact_assessed:
        blocking.append("IMPACT_ASSESSMENT_INCOMPLETE")
    if (
        record.get("change_type") in AUDITABLE_DOMAINS
        and record.get("change_type") not in impact_domains
    ):
        blocking.append("CHANGE_TYPE_IMPACT_DOMAIN_MISMATCH")
        impact_assessed = False

    priority_recorded = bool(
        record.get("old_priority") in PRIORITIES
        and record.get("new_priority") in PRIORITIES
        and _non_empty(record.get("priority_change_justification"))
        and record.get("time_pressure_only") is False
        and record.get("quality_tradeoff_allowed") is False
    )
    if not priority_recorded:
        blocking.append("PRIORITY_DECISION_INVALID")
    if record.get("time_pressure_only") is True:
        blocking.append("TIME_PRESSURE_ONLY_CHANGE_FORBIDDEN")
    if record.get("quality_tradeoff_allowed") is True:
        blocking.append("QUALITY_TRADEOFF_FORBIDDEN")

    regression_scope = record.get("regression_scope", {})
    regression_scope_complete = bool(
        impact_assessed
        and isinstance(regression_scope, dict)
        and all(
            isinstance(regression_scope.get(domain), list)
            and set(active_protocol.get("domain_requirements", {}).get(domain, []))
            .issubset(set(regression_scope.get(domain, [])))
            for domain in impact_domains
        )
    )
    if not regression_scope_complete:
        blocking.append("REGRESSION_SCOPE_INCOMPLETE")

    approval_complete = bool(
        record.get("approval_state") == "APPROVED"
        and _non_empty(record.get("approver_role"))
    )
    if not approval_complete:
        blocking.append("CHANGE_NOT_APPROVED")
    validation_complete = bool(
        record.get("change_state") == "VALIDATED"
        and _non_empty(record.get("implementation_refs"))
        and _non_empty(record.get("validation_refs"))
        and _non_empty(record.get("evidence_refs"))
        and _non_empty(record.get("rollback_plan"))
        and _non_empty(record.get("audit_event_refs"))
    )
    if not validation_complete:
        blocking.append("CHANGE_NOT_VALIDATED")
    if record.get("public_safe_status") != "PUBLIC_SAFE" or _public_safe_errors(record):
        blocking.append("CHANGE_RECORD_NOT_PUBLIC_SAFE")

    blocking = sorted(set(blocking))
    planning_record_complete = bool(
        registered
        and impact_assessed
        and priority_recorded
        and regression_scope_complete
        and approval_complete
        and validation_complete
        and not blocking
    )
    return {
        "registered": registered,
        "impact_assessed": impact_assessed,
        "priority_recorded": priority_recorded,
        "regression_scope_complete": regression_scope_complete,
        "approval_complete": approval_complete,
        "validation_complete": validation_complete,
        "planning_record_complete": planning_record_complete,
        "merge_review_candidate": planning_record_complete,
        "merge_eligible": False,
        "merge_enforcement_verified": False,
        "enforcement_limitations": [
            "REGISTRY_RESOLUTION_NOT_IMPLEMENTED",
            "ARTIFACT_REFERENCE_RESOLUTION_NOT_IMPLEMENTED",
            "AUDIT_EVENT_RESOLUTION_NOT_IMPLEMENTED",
            "RUNTIME_OR_CI_HOOK_NOT_IMPLEMENTED",
        ],
        "blocking_reasons": blocking,
    }
