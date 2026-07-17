from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile


TRACE_VERSION = "v1.5-s02-p2-requirement-trace-r1"
SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
STAGE_CLOSURE_DECISION = "S02_P2_STAGE_CLOSURE_DECISION"
CONTROLLED_DERIVATION = "CONTROLLED_S02_P2_DERIVATION"
NOT_APPLICABLE = "NOT_APPLICABLE"
CROSS_CUTTING = "CROSS_CUTTING"

SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
REQUIREMENTS_MEMBER_SHA256 = (
    "2ff4eb93f83d52e9bd1c482dceb442d40686a9e2cc54ce9277dfee00e106ab41"
)
ROADMAP_MEMBER_SHA256 = (
    "741fdf6a1dd6d04fdaaf916f8cf84ebce07207fbb50d7971736c1c9fc46a5145"
)

REQUIREMENTS_SUFFIX = "04_KMFA_需求追溯矩阵_v2_0.csv"
ROADMAP_SUFFIX = "02B_KMFA_Codex_Development_Roadmap_v2_0.json"

EXPECTED_REQUIREMENT_IDS = tuple(f"R{index:03d}" for index in range(1, 56))
EXPECTED_CLOSURE_BINDINGS = {
    ("R017", "S11P2T01"),
    ("R023", "S21P1T02"),
}

TRACE_COLUMNS = [
    "trace_version",
    "requirement_id",
    "priority",
    "requirement_name",
    "normative_requirement_public_safe",
    "requirement_source_refs",
    "requirement_source_sha256",
    "primary_stage_refs",
    "source_task_refs",
    "mapping_origin",
    "mapping_decision",
    "mapping_basis_refs",
    "stage_id",
    "stage_name",
    "phase_id",
    "phase_name",
    "task_id",
    "task_name",
    "implementation_action",
    "implementation_output",
    "test_evidence_requirement",
    "acceptance_criterion",
    "stop_condition",
    "business_line_refs",
    "business_line_mapping_status",
    "role_view_refs",
    "user_flow_refs",
    "page_scope_refs",
    "data_source_refs",
    "data_layer_refs",
    "rule_formula_model_refs",
    "report_scope_refs",
    "dimension_mapping_status",
    "dimension_mapping_basis_refs",
    "dimension_na_reason",
    "current_implementation_status",
    "implementation_gap_type",
    "current_evidence_refs",
    "conflict_status",
    "conflict_disposition",
    "resolution_target_stage",
    "requirement_acceptance_status",
    "implementation_allowed_by_s02_p2",
    "public_safe_status",
]

BUSINESS_LINE_VALUES = {f"BL-{index:02d}" for index in range(1, 11)} | {
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
ROLE_VALUES = {"经营", "财务", "税务", CROSS_CUTTING, NOT_APPLICABLE}
FLOW_VALUES = {f"F{index:02d}" for index in range(1, 17)} | {
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
PAGE_VALUES = {
    "经营首页",
    "项目",
    "项目详情",
    "回款",
    "资金",
    "税务与政策",
    "数据更新",
    "数据源检查板",
    "待确认事项",
    "报告",
    "报告中心",
    "设置/数据与计算/数据来源",
    "设置/数据与计算/计算规则",
    "设置/数据与计算/处理记录",
    "设置/数据与计算/权限与审计",
    "设置/数据与计算/系统状态",
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
DATA_SOURCE_VALUES = {
    "红圈",
    "金蝶",
    "WPS",
    "银行",
    "税务/数电票",
    "合同资料",
    "政策证据",
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
DATA_LAYER_VALUES = {f"L{index}" for index in range(8)} | {
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
RULE_VALUES = {
    "AMT-NORMALIZE-001",
    "AMT-EXACT-002",
    "PROJECT-MATCH-001",
    "COST-TOTAL-001",
    "MARGIN-CONTRACT-001",
    "MARGIN-SETTLEMENT-002",
    "MARGIN-MANAGEMENT-003",
    "MARGIN-CASH-004",
    "MARGIN-RATE-005",
    "COST-COMPLETENESS-006",
    "AR-COLLECTION-001",
    "AR-AGING-002",
    "AR-PRIORITY-003",
    "CASH-RUNWAY-001",
    "CASH-GAP-002",
    "HEALTH-001",
    "ACTION-PRIORITY-001",
    "DATA-QUALITY-001",
    "FRESHNESS-001",
    "REPORT-RELEASE-001",
    "RERUN-001",
    "CROSS-SOURCE-001",
    CROSS_CUTTING,
    NOT_APPLICABLE,
}
REPORT_VALUES = {
    "Dashboard",
    "HTML",
    "PDF",
    "CSV/Excel专业附表",
    "本期经营摘要",
    "经营结果与项目组合",
    "项目成本与利润质量",
    "回款、应收与资金",
    "税务、发票与政策准备",
    "口径差异与管理调整摘要",
    "下期重点事项",
    "专业附表与数据来源",
    CROSS_CUTTING,
    NOT_APPLICABLE,
}

ALL_RULE_IDS = sorted(RULE_VALUES - {CROSS_CUTTING, NOT_APPLICABLE})
ALL_SOURCE_SYSTEMS = ["红圈", "金蝶", "WPS", "银行", "税务/数电票", "合同资料", "政策证据"]
ALL_REPORT_FORMATS = ["Dashboard", "HTML", "PDF", "CSV/Excel专业附表"]
ALL_REPORT_SECTIONS = [
    "本期经营摘要",
    "经营结果与项目组合",
    "项目成本与利润质量",
    "回款、应收与资金",
    "税务、发票与政策准备",
    "口径差异与管理调整摘要",
    "下期重点事项",
    "专业附表与数据来源",
]

GOVERNANCE_ONLY_IDS = {
    "R001",
    "R048",
    "R049",
    "R050",
    "R051",
    "R052",
    "R053",
    "R054",
    "R055",
}

FLOW_MAP = {
    "R002": ["F01", "F13"],
    "R003": ["F02"],
    "R004": ["F02", "F07"],
    "R005": ["F03", "F14"],
    "R006": ["F03", "F14"],
    "R007": ["F03", "F11", "F12", "F15"],
    "R008": ["F05", "F06"],
    "R009": ["F05"],
    "R010": ["F06"],
    "R011": ["F05", "F06", "F14"],
    "R012": ["F02", "F07", "F11", "F12"],
    "R013": ["F02"],
    "R014": ["F05", "F06"],
    "R015": ["F02", "F07"],
    "R016": ["F08", "F09", "F13"],
    "R017": ["F03", "F04"],
    "R018": ["F03"],
    "R019": ["F04"],
    "R020": ["F03", "F04"],
    "R021": ["F03", "F04", "F11"],
    "R022": ["F11"],
    "R023": ["F05", "F06", "F11"],
    "R024": ["F03", "F05", "F06", "F07"],
    "R025": ["F03", "F05", "F06", "F07"],
    "R026": ["F02", "F08", "F09", "F10", "F11"],
    "R027": ["F01"],
    "R028": ["F01"],
    "R029": ["F02", "F07"],
    "R030": ["F02", "F08", "F09"],
    "R031": ["F08"],
    "R032": ["F09"],
    "R033": ["F10"],
    "R034": ["F11", "F12"],
    "R035": ["F11", "F12"],
    "R036": ["F11", "F12"],
    "R037": ["F04", "F11"],
    "R038": ["F01", "F02", "F03", "F04", "F08", "F09", "F10", "F11"],
    "R039": ["F01", "F16"],
    "R040": ["F01", "F02", "F03", "F08", "F09", "F10", "F11"],
    "R041": ["F01", "F02", "F11", "F16"],
    "R042": [f"F{index:02d}" for index in range(1, 15)],
    "R043": ["F03", "F05", "F06", "F07", "F11", "F12", "F14"],
    "R044": ["F14", "F16"],
    "R045": ["F03", "F11", "F12", "F14", "F15"],
    "R046": ["F15"],
    "R047": ["F11", "F13", "F15"],
}

PAGE_MAP = {
    "R002": ["经营首页", "设置/数据与计算/权限与审计"],
    "R003": ["项目", "项目详情"],
    "R004": ["项目", "项目详情"],
    "R005": ["数据更新", "设置/数据与计算/数据来源"],
    "R006": ["数据更新", "设置/数据与计算/数据来源"],
    "R007": ["设置/数据与计算/权限与审计", "设置/数据与计算/系统状态"],
    "R008": ["数据更新", "待确认事项", "设置/数据与计算/处理记录"],
    "R009": ["待确认事项", "设置/数据与计算/处理记录"],
    "R010": ["待确认事项", "设置/数据与计算/处理记录"],
    "R011": ["待确认事项", "设置/数据与计算/处理记录"],
    "R012": ["项目详情", "报告"],
    "R013": ["项目详情", "设置/数据与计算/数据来源"],
    "R014": ["待确认事项", "设置/数据与计算/处理记录"],
    "R015": ["项目", "项目详情", "待确认事项"],
    "R016": ["项目详情", "回款", "资金"],
    "R017": ["数据更新", "数据源检查板", "设置/数据与计算/数据来源"],
    "R018": ["数据更新"],
    "R019": ["数据源检查板"],
    "R020": ["数据更新", "数据源检查板"],
    "R021": ["数据源检查板", "报告"],
    "R022": ["报告", "设置/数据与计算/计算规则"],
    "R023": ["待确认事项", "报告", "设置/数据与计算/计算规则"],
    "R024": ["数据更新", "待确认事项", "设置/数据与计算/处理记录"],
    "R025": ["待确认事项", "经营首页", "项目详情", "报告"],
    "R026": ["设置/数据与计算/计算规则"],
    "R027": ["经营首页"],
    "R028": ["经营首页", "待确认事项"],
    "R029": ["项目详情"],
    "R030": ["项目详情", "回款", "资金"],
    "R031": ["回款", "项目详情"],
    "R032": ["资金"],
    "R033": ["税务与政策"],
    "R034": ["报告", "报告中心"],
    "R035": ["报告", "报告中心"],
    "R036": ["报告", "报告中心"],
    "R037": ["数据源检查板", "报告"],
    "R038": ["经营首页", "项目", "项目详情", "回款", "资金", "税务与政策", "数据更新", "报告"],
    "R039": ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"],
    "R040": ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"],
    "R041": ["经营首页", "项目详情", "报告"],
    "R042": [CROSS_CUTTING],
    "R043": [CROSS_CUTTING],
    "R044": [CROSS_CUTTING],
    "R045": [CROSS_CUTTING],
    "R046": ["设置/数据与计算/系统状态"],
    "R047": ["设置/数据与计算/权限与审计", "报告中心"],
}

RULE_MAP = {
    "R008": ["RERUN-001", "CROSS-SOURCE-001"],
    "R009": ["RERUN-001"],
    "R010": ["CROSS-SOURCE-001"],
    "R011": ["RERUN-001", "CROSS-SOURCE-001"],
    "R012": ["AMT-NORMALIZE-001", "AMT-EXACT-002", "COST-TOTAL-001"],
    "R015": ["PROJECT-MATCH-001"],
    "R020": ["DATA-QUALITY-001", "FRESHNESS-001"],
    "R021": ["DATA-QUALITY-001", "FRESHNESS-001", "REPORT-RELEASE-001"],
    "R022": ["CROSS-SOURCE-001"],
    "R023": ["CROSS-SOURCE-001"],
    "R025": ["RERUN-001"],
    "R026": ALL_RULE_IDS,
    "R027": ["HEALTH-001"],
    "R028": ["ACTION-PRIORITY-001"],
    "R029": ["COST-TOTAL-001", "COST-COMPLETENESS-006"],
    "R030": [
        "MARGIN-CONTRACT-001",
        "MARGIN-SETTLEMENT-002",
        "MARGIN-MANAGEMENT-003",
        "MARGIN-CASH-004",
        "MARGIN-RATE-005",
    ],
    "R031": ["AR-COLLECTION-001", "AR-AGING-002", "AR-PRIORITY-003"],
    "R032": ["CASH-RUNWAY-001", "CASH-GAP-002"],
    "R034": ["REPORT-RELEASE-001"],
    "R035": ["REPORT-RELEASE-001"],
    "R036": ["AMT-EXACT-002", "REPORT-RELEASE-001"],
    "R037": ["REPORT-RELEASE-001"],
    "R045": [CROSS_CUTTING],
}


def _join(values: Iterable[str]) -> str:
    return ";".join(dict.fromkeys(values))


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _member_by_suffix(archive: ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"source member lookup failed for {suffix}: {matches}")
    return matches[0]


def _csv_rows_from_bytes(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))


def _load_public_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _public_safe_text(value: str) -> str:
    value = re.sub(
        r"/" + r"Users/[^/\s]+/Downloads/KMFA_MetaData",
        "RAW_ROOT_TOKEN",
        value,
    )
    return re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "OWNER_NOTIFICATION_EMAIL_TOKEN",
        value,
    )


def _roadmap_tasks(roadmap: dict) -> dict[str, dict[str, str]]:
    tasks: dict[str, dict[str, str]] = {}
    for stage in roadmap["stages"]:
        for phase in stage["phases"]:
            for task in phase["tasks"]:
                task_id = f"{stage['id']}{phase['id']}{task['id']}"
                tasks[task_id] = {
                    "stage_id": stage["id"],
                    "stage_name": _public_safe_text(stage["name"]),
                    "phase_id": phase["id"],
                    "phase_name": _public_safe_text(phase["name"]),
                    "task_id": task_id,
                    "task_name": _public_safe_text(task["name"]),
                    "implementation_action": _public_safe_text(task["action"]),
                    "implementation_output": _public_safe_text(task["output"]),
                    "test_evidence_requirement": _public_safe_text(task["evidence"]),
                    "acceptance_criterion": _public_safe_text(task["acceptance"]),
                    "stop_condition": _public_safe_text(task["stop"]),
                }
    return tasks


def _role_refs(requirement_id: str) -> list[str]:
    if requirement_id in GOVERNANCE_ONLY_IDS:
        return [NOT_APPLICABLE]
    if requirement_id == "R033":
        return ["税务"]
    if requirement_id in {"R027", "R028", "R039", "R041", "R046"}:
        return ["经营"]
    if requirement_id in {
        "R003",
        "R004",
        "R012",
        "R013",
        "R015",
        "R029",
        "R030",
        "R031",
        "R032",
    }:
        return ["经营", "财务"]
    if requirement_id in {"R007", "R010", "R011", "R022", "R023", "R026", "R034", "R035", "R036", "R037", "R047"}:
        return ["经营", "财务", "税务"]
    return ["财务"]


def _data_source_refs(requirement_id: str) -> list[str]:
    if requirement_id in {"R017", "R018", "R019", "R020", "R021", "R038", "R042", "R043", "R044", "R045"}:
        return ALL_SOURCE_SYSTEMS
    if requirement_id in {"R004", "R008", "R009", "R010", "R011", "R012", "R014", "R015", "R022", "R023", "R024", "R025", "R026", "R029", "R030", "R034", "R035", "R036", "R037"}:
        return [CROSS_CUTTING]
    if requirement_id == "R016":
        return ["红圈", "金蝶", "WPS", "银行"]
    if requirement_id == "R031":
        return ["红圈", "金蝶", "WPS", "银行", "合同资料"]
    if requirement_id == "R032":
        return ["银行"]
    if requirement_id == "R033":
        return ["金蝶", "WPS", "税务/数电票", "合同资料", "政策证据"]
    if requirement_id == "R052":
        return ["红圈"]
    return [NOT_APPLICABLE]


def _data_layer_refs(requirement_id: str) -> list[str]:
    if requirement_id == "R005":
        return ["L0"]
    if requirement_id == "R006":
        return [f"L{index}" for index in range(1, 8)]
    if requirement_id == "R007":
        return [CROSS_CUTTING]
    if requirement_id in {"R008", "R009", "R010", "R011", "R014", "R022", "R023", "R024", "R025"}:
        return [f"L{index}" for index in range(2, 8)]
    if requirement_id in {"R012", "R013", "R015", "R016", "R017", "R018", "R019", "R020", "R021", "R026", "R029", "R030", "R031", "R032", "R033", "R034", "R035", "R036", "R037"}:
        return [CROSS_CUTTING]
    return [NOT_APPLICABLE]


def _report_refs(requirement_id: str) -> list[str]:
    if requirement_id == "R023":
        return ["口径差异与管理调整摘要"]
    if requirement_id in {"R004", "R012", "R013", "R029", "R030"}:
        return ["项目成本与利润质量", "专业附表与数据来源"]
    if requirement_id in {"R016", "R031", "R032"}:
        return ["回款、应收与资金"]
    if requirement_id == "R033":
        return ["税务、发票与政策准备"]
    if requirement_id == "R027":
        return ["本期经营摘要", "经营结果与项目组合"]
    if requirement_id == "R028":
        return ["本期经营摘要", "下期重点事项"]
    if requirement_id == "R034":
        return ALL_REPORT_FORMATS + ALL_REPORT_SECTIONS
    if requirement_id == "R035":
        return ALL_REPORT_SECTIONS
    if requirement_id == "R036":
        return ALL_REPORT_FORMATS
    if requirement_id == "R037":
        return ["本期经营摘要"]
    if requirement_id in {"R007", "R021", "R022", "R025", "R026", "R042", "R043", "R045", "R046", "R047"}:
        return [CROSS_CUTTING]
    return [NOT_APPLICABLE]


def _dimension_values(
    requirement_id: str,
    business_by_requirement: dict[str, list[str]],
) -> dict[str, str]:
    business = list(business_by_requirement.get(requirement_id, []))
    if requirement_id == "R051":
        business = [f"BL-{index:02d}" for index in range(1, 11)]
    elif not business:
        business = [
            NOT_APPLICABLE
            if requirement_id in GOVERNANCE_ONLY_IDS
            else CROSS_CUTTING
        ]

    values = {
        "business_line_refs": _join(business),
        "business_line_mapping_status": CONTROLLED_DERIVATION,
        "role_view_refs": _join(_role_refs(requirement_id)),
        "user_flow_refs": _join(FLOW_MAP.get(requirement_id, [NOT_APPLICABLE])),
        "page_scope_refs": _join(PAGE_MAP.get(requirement_id, [NOT_APPLICABLE])),
        "data_source_refs": _join(_data_source_refs(requirement_id)),
        "data_layer_refs": _join(_data_layer_refs(requirement_id)),
        "rule_formula_model_refs": _join(RULE_MAP.get(requirement_id, [NOT_APPLICABLE])),
        "report_scope_refs": _join(_report_refs(requirement_id)),
        "dimension_mapping_status": CONTROLLED_DERIVATION,
        "dimension_mapping_basis_refs": _join(
            [
                "SOURCE_PACKAGE_TOKEN::04_KMFA_需求追溯矩阵_v2_0.csv",
                "SOURCE_PACKAGE_TOKEN::05_KMFA_真实用户任务流验收矩阵_v2_0.csv",
                "SOURCE_PACKAGE_TOKEN::06_KMFA_数据治理准确性与只读协议_v2_0.md",
                "SOURCE_PACKAGE_TOKEN::07_KMFA_界面交互全量重构规范_v2_0.md",
                "SOURCE_PACKAGE_TOKEN::08_KMFA_模型公式函数参数主注册表_v2_0.yaml",
                "SOURCE_PACKAGE_TOKEN::09_KMFA_数据源检查矩阵模板_v2_0.csv",
                "SOURCE_PACKAGE_TOKEN::13_KMFA_阶段一与阶段二五环节信息继承清单_v2_0.md",
            ]
        ),
    }
    dimension_fields = (
        "business_line_refs",
        "role_view_refs",
        "user_flow_refs",
        "page_scope_refs",
        "data_source_refs",
        "data_layer_refs",
        "rule_formula_model_refs",
        "report_scope_refs",
    )
    reasons = [
        f"{field}=需求不直接约束该维度"
        for field in dimension_fields
        if NOT_APPLICABLE in values[field].split(";")
    ]
    values["dimension_na_reason"] = _join(reasons) if reasons else "NONE"
    return values


def build_requirement_task_trace(
    source_package: Path | str,
    p1_ledger_path: Path | str,
    p1_business_path: Path | str,
) -> list[dict[str, str]]:
    source_package = Path(source_package)
    p1_ledger_path = Path(p1_ledger_path)
    p1_business_path = Path(p1_business_path)

    if _sha256(source_package) != SOURCE_PACKAGE_SHA256:
        raise ValueError("source package SHA256 mismatch")

    with ZipFile(source_package) as archive:
        requirements_member = _member_by_suffix(archive, REQUIREMENTS_SUFFIX)
        roadmap_member = _member_by_suffix(archive, ROADMAP_SUFFIX)
        requirements_payload = archive.read(requirements_member)
        roadmap_payload = archive.read(roadmap_member)

    if sha256(requirements_payload).hexdigest() != REQUIREMENTS_MEMBER_SHA256:
        raise ValueError("requirements member SHA256 mismatch")
    if sha256(roadmap_payload).hexdigest() != ROADMAP_MEMBER_SHA256:
        raise ValueError("roadmap member SHA256 mismatch")

    source_requirements = _csv_rows_from_bytes(requirements_payload)
    source_by_id = {row["需求ID"]: row for row in source_requirements}
    if tuple(source_by_id) != EXPECTED_REQUIREMENT_IDS:
        raise ValueError("requirements source must contain ordered R001-R055")

    ledger_rows = _load_public_csv(p1_ledger_path)
    ledger_by_id = {row["requirement_id"]: row for row in ledger_rows}
    if tuple(ledger_by_id) != EXPECTED_REQUIREMENT_IDS:
        raise ValueError("P1 ledger must contain ordered R001-R055")

    business_rows = _load_public_csv(p1_business_path)
    if {row["business_line_id"] for row in business_rows} != {
        f"BL-{index:02d}" for index in range(1, 11)
    }:
        raise ValueError("P1 business matrix must contain BL-01..BL-10")
    business_by_requirement: dict[str, list[str]] = defaultdict(list)
    for business_row in business_rows:
        for requirement_id in re.findall(r"\bR\d{3}\b", business_row["source_refs"]):
            business_by_requirement[requirement_id].append(
                business_row["business_line_id"]
            )

    roadmap = json.loads(roadmap_payload)
    if (roadmap["stage_count"], roadmap["phase_count"], roadmap["task_count"]) != (
        24,
        72,
        216,
    ):
        raise ValueError("roadmap cardinality mismatch")
    tasks = _roadmap_tasks(roadmap)
    if len(tasks) != 216:
        raise ValueError("roadmap task cardinality mismatch")

    rows: list[dict[str, str]] = []
    for requirement_id in EXPECTED_REQUIREMENT_IDS:
        source = source_by_id[requirement_id]
        ledger = ledger_by_id[requirement_id]
        if source["优先级"] != ledger["priority"]:
            raise ValueError(f"priority mismatch for {requirement_id}")
        if source["需求名称"] != ledger["requirement_name"]:
            raise ValueError(f"name mismatch for {requirement_id}")
        if source["主要Stage"] != ledger["primary_stage_refs"]:
            raise ValueError(f"stage refs mismatch for {requirement_id}")
        if source["对应Task"] != ledger["task_refs"]:
            raise ValueError(f"task refs mismatch for {requirement_id}")
        if ledger["public_safe_status"] != "PUBLIC_SAFE":
            raise ValueError(f"P1 ledger row is not public-safe: {requirement_id}")

        task_ids = source["对应Task"].split(";")
        task_ids.extend(
            task_id
            for closure_requirement, task_id in sorted(EXPECTED_CLOSURE_BINDINGS)
            if closure_requirement == requirement_id
        )
        dimensions = _dimension_values(requirement_id, business_by_requirement)

        for task_id in task_ids:
            if task_id not in tasks:
                raise ValueError(f"unknown roadmap task {task_id} for {requirement_id}")
            is_closure = (requirement_id, task_id) in EXPECTED_CLOSURE_BINDINGS
            row = {
                "trace_version": TRACE_VERSION,
                "requirement_id": requirement_id,
                "priority": ledger["priority"],
                "requirement_name": ledger["requirement_name"],
                "normative_requirement_public_safe": ledger["normative_requirement"],
                "requirement_source_refs": ledger["source_refs"],
                "requirement_source_sha256": ledger["source_member_sha256"],
                "primary_stage_refs": ledger["primary_stage_refs"],
                "source_task_refs": ledger["task_refs"],
                "mapping_origin": (
                    STAGE_CLOSURE_DECISION if is_closure else SOURCE_EXPLICIT
                ),
                "mapping_decision": (
                    "ADD_EXISTING_TASK_FOR_PRIMARY_STAGE_CLOSURE"
                    if is_closure
                    else "SOURCE_TASK_BINDING"
                ),
                "mapping_basis_refs": _join(
                    [
                        "SOURCE_PACKAGE_TOKEN::04_KMFA_需求追溯矩阵_v2_0.csv",
                        "SOURCE_PACKAGE_TOKEN::02B_KMFA_Codex_Development_Roadmap_v2_0.json",
                        "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/requirements_ledger_public_safe.csv",
                    ]
                ),
                **tasks[task_id],
                **dimensions,
                "current_implementation_status": ledger[
                    "current_implementation_status"
                ],
                "implementation_gap_type": ledger["implementation_gap_type"],
                "current_evidence_refs": ledger["current_evidence_refs"],
                "conflict_status": ledger["conflict_status"],
                "conflict_disposition": ledger["conflict_disposition"],
                "resolution_target_stage": ledger["resolution_target_stage"],
                "requirement_acceptance_status": "NOT_ACCEPTED",
                "implementation_allowed_by_s02_p2": "false",
                "public_safe_status": "PUBLIC_SAFE",
            }
            rows.append({column: row[column] for column in TRACE_COLUMNS})

    rows.sort(key=lambda row: (int(row["requirement_id"][1:]), row["task_id"]))
    errors = validate_requirement_task_trace(rows)
    if errors:
        raise ValueError("built requirement trace is invalid: " + " | ".join(errors))
    return rows


def _tracked_roadmap_tasks() -> dict[str, dict[str, str]]:
    path = Path(__file__).resolve().parents[1] / "taskpack" / "v1_5" / "roadmap_v2_0.json"
    with path.open(encoding="utf-8") as handle:
        return _roadmap_tasks(json.load(handle))


def _tokens(value: str) -> list[str]:
    return [token for token in value.split(";") if token]


def validate_requirement_task_trace(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(rows) != 134:
        errors.append(f"row_count: expected=134 actual={len(rows)}")
    if not rows:
        return errors + ["requirement_coverage: trace is empty"]

    for index, row in enumerate(rows, start=1):
        if list(row) != TRACE_COLUMNS:
            errors.append(f"schema: row={index} columns differ from TRACE_COLUMNS")

    requirement_ids = {row.get("requirement_id", "") for row in rows}
    expected_ids = set(EXPECTED_REQUIREMENT_IDS)
    if requirement_ids != expected_ids:
        errors.append(
            "requirement_coverage: "
            f"missing={sorted(expected_ids - requirement_ids)} "
            f"extra={sorted(requirement_ids - expected_ids)}"
        )

    key_counts = Counter(
        (row.get("requirement_id", ""), row.get("task_id", "")) for row in rows
    )
    duplicates = sorted(key for key, count in key_counts.items() if count != 1)
    if duplicates:
        errors.append(f"binding_uniqueness: duplicate={duplicates}")

    origin_counts = Counter(row.get("mapping_origin", "") for row in rows)
    if origin_counts != Counter({SOURCE_EXPLICIT: 132, STAGE_CLOSURE_DECISION: 2}):
        errors.append(f"mapping_origin: invalid counts={dict(origin_counts)}")
    closure_pairs = {
        (row.get("requirement_id", ""), row.get("task_id", ""))
        for row in rows
        if row.get("mapping_origin") == STAGE_CLOSURE_DECISION
    }
    if closure_pairs != EXPECTED_CLOSURE_BINDINGS:
        errors.append(
            f"mapping_origin: closure expected={sorted(EXPECTED_CLOSURE_BINDINGS)} "
            f"actual={sorted(closure_pairs)}"
        )

    try:
        tasks = _tracked_roadmap_tasks()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"roadmap_load: {exc}")
        tasks = {}

    contract_fields = (
        "task_name",
        "implementation_action",
        "implementation_output",
        "test_evidence_requirement",
        "acceptance_criterion",
        "stop_condition",
    )
    for row in rows:
        requirement_id = row.get("requirement_id", "")
        task_id = row.get("task_id", "")
        task = tasks.get(task_id)
        if task is None:
            errors.append(f"unknown_task: {requirement_id}/{task_id}")
        else:
            for field in (
                "stage_id",
                "stage_name",
                "phase_id",
                "phase_name",
                "task_id",
                *contract_fields,
            ):
                if row.get(field) != task[field]:
                    errors.append(
                        f"task_contract:{field}: {requirement_id}/{task_id} "
                        "does not match roadmap"
                    )
        for field in contract_fields:
            if not row.get(field, "").strip():
                errors.append(f"task_contract:{field}: {requirement_id}/{task_id} blank")

        if row.get("mapping_origin") == SOURCE_EXPLICIT:
            if task_id not in _tokens(row.get("source_task_refs", "")):
                errors.append(
                    f"mapping_origin: source binding absent from source refs {requirement_id}/{task_id}"
                )
        elif row.get("mapping_origin") == STAGE_CLOSURE_DECISION:
            if task_id in _tokens(row.get("source_task_refs", "")):
                errors.append(
                    f"mapping_origin: closure already present in source refs {requirement_id}/{task_id}"
                )
        else:
            errors.append(
                f"mapping_origin: unsupported origin {row.get('mapping_origin')}"
            )

    # Requirement-to-primary-Stage closure is stronger than the source pack's
    # original any-valid-Task check.
    rows_by_requirement: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_requirement[row.get("requirement_id", "")].append(row)
    p0_p1_stage_total = 0
    p0_p1_stage_covered = 0
    all_stage_total = 0
    all_stage_covered = 0
    for requirement_id in EXPECTED_REQUIREMENT_IDS:
        requirement_rows = rows_by_requirement.get(requirement_id, [])
        if not requirement_rows:
            continue
        primary_stages = set(requirement_rows[0].get("primary_stage_refs", "").split(","))
        bound_stages = {row.get("stage_id", "") for row in requirement_rows}
        all_stage_total += len(primary_stages)
        all_stage_covered += len(primary_stages & bound_stages)
        if requirement_rows[0].get("priority") in {"P0", "P1"}:
            p0_p1_stage_total += len(primary_stages)
            p0_p1_stage_covered += len(primary_stages & bound_stages)
        if not primary_stages <= bound_stages:
            errors.append(
                f"stage_closure: {requirement_id} missing={sorted(primary_stages - bound_stages)}"
            )
    if (p0_p1_stage_covered, p0_p1_stage_total) != (96, 96):
        errors.append(
            "stage_closure: P0/P1 expected=96/96 "
            f"actual={p0_p1_stage_covered}/{p0_p1_stage_total}"
        )
    if (all_stage_covered, all_stage_total) != (97, 97):
        errors.append(
            f"stage_closure: all expected=97/97 actual={all_stage_covered}/{all_stage_total}"
        )

    unique_priority = {
        requirement_id: requirement_rows[0].get("priority", "")
        for requirement_id, requirement_rows in rows_by_requirement.items()
        if requirement_rows
    }
    if Counter(unique_priority.values()) != Counter({"P0": 46, "P1": 8, "P2": 1}):
        errors.append(f"priority_counts: invalid={dict(Counter(unique_priority.values()))}")
    if Counter(row.get("priority", "") for row in rows) != Counter(
        {"P0": 114, "P1": 19, "P2": 1}
    ):
        errors.append("priority_binding_counts: expected P0/P1/P2=114/19/1")

    r051_expected = _join(f"BL-{index:02d}" for index in range(1, 11))
    if {
        row.get("business_line_refs", "")
        for row in rows_by_requirement.get("R051", [])
    } != {r051_expected}:
        errors.append("R051_business_lines: expected BL-01..BL-10")

    dimension_rules = {
        "business_line_refs": BUSINESS_LINE_VALUES,
        "role_view_refs": ROLE_VALUES,
        "user_flow_refs": FLOW_VALUES,
        "page_scope_refs": PAGE_VALUES,
        "data_source_refs": DATA_SOURCE_VALUES,
        "data_layer_refs": DATA_LAYER_VALUES,
        "rule_formula_model_refs": RULE_VALUES,
        "report_scope_refs": REPORT_VALUES,
    }
    for row in rows:
        requirement_id = row.get("requirement_id", "")
        if row.get("business_line_mapping_status") != CONTROLLED_DERIVATION:
            errors.append(
                f"dimension_status: business lines {requirement_id} must be controlled derivation"
            )
        if row.get("dimension_mapping_status") != CONTROLLED_DERIVATION:
            errors.append(
                f"dimension_status: {requirement_id} must be controlled derivation"
            )
        requires_na_reason = False
        for field, allowed in dimension_rules.items():
            values = _tokens(row.get(field, ""))
            illegal = sorted(set(values) - allowed)
            if not values or illegal:
                errors.append(
                    f"illegal_dimension:{field}: {requirement_id} values={values} illegal={illegal}"
                )
            if NOT_APPLICABLE in values:
                requires_na_reason = True
        if requires_na_reason and not row.get("dimension_na_reason", "").strip():
            errors.append(f"dimension_na_reason: {requirement_id} required")

        if row.get("implementation_allowed_by_s02_p2") != "false":
            errors.append(
                f"implementation_allowed_by_s02_p2: {requirement_id} must be false"
            )
        if row.get("requirement_acceptance_status") != "NOT_ACCEPTED":
            errors.append(
                f"requirement_acceptance_status: {requirement_id} must remain NOT_ACCEPTED"
            )
        if row.get("public_safe_status") != "PUBLIC_SAFE":
            errors.append(f"public_safe: {requirement_id} status is not PUBLIC_SAFE")

        joined = "\n".join(str(row.get(column, "")) for column in TRACE_COLUMNS)
        if re.search(
            r"/" + r"Users/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            joined,
        ):
            errors.append(f"public_safe: {requirement_id} contains absolute path or email")

    if rows_by_requirement.get("R005") and "RAW_ROOT_TOKEN" not in rows_by_requirement["R005"][0].get(
        "normative_requirement_public_safe", ""
    ):
        errors.append("public_safe: R005 must retain RAW_ROOT_TOKEN")
    if rows_by_requirement.get("R046") and "OWNER_NOTIFICATION_EMAIL_TOKEN" not in rows_by_requirement["R046"][0].get(
        "normative_requirement_public_safe", ""
    ):
        errors.append("public_safe: R046 must retain OWNER_NOTIFICATION_EMAIL_TOKEN")

    for row in rows_by_requirement.get("R007", []):
        if (
            row.get("conflict_status") != "RESOLVED_BY_V15_PRECEDENCE"
            or row.get("resolution_target_stage") != "S03"
            or "DEPRECATE_OWNER_AUTHORIZED_RAW_PLAINTEXT_EXCEPTION_IN_S03"
            not in row.get("conflict_disposition", "")
        ):
            errors.append("R007_open_gap: precedence resolved but implementation gap must target S03")
            break

    if "R053" not in rows_by_requirement:
        errors.append("requirement_coverage: deferred P2 R053 is missing")
    return errors


__all__ = [
    "SOURCE_EXPLICIT",
    "STAGE_CLOSURE_DECISION",
    "TRACE_COLUMNS",
    "build_requirement_task_trace",
    "validate_requirement_task_trace",
]
