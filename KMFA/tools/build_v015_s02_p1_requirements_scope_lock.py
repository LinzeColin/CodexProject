#!/usr/bin/env python3
"""Build deterministic public-safe core artifacts for KMFA v1.5 S02-P1.

This builder consolidates the authoritative v2.0 requirement trace matrix,
the v1.4 inheritance/rebuild guidance, the Stage 1/2 inheritance checklist,
and the S01-P2 implementation/migration inventories.  It does not read raw
business data and it does not authorize product implementation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence
from zipfile import ZipFile


SOURCE_PACKAGE_NAME = (
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
SOURCE_MEMBER_HASHES = {
    "04_KMFA_需求追溯矩阵_v2_0.csv": (
        "2ff4eb93f83d52e9bd1c482dceb442d40686a9e2cc54ce9277dfee00e106ab41"
    ),
    "11_KMFA_1_4继承_重构_废弃清单_v2_0.md": (
        "96c733d0690f462d4c3e3ea852c9b6172c45f54a94506fe67a22066cb10555ad"
    ),
    "13_KMFA_阶段一与阶段二五环节信息继承清单_v2_0.md": (
        "cc61d0daef141311bac67e2dbf54d751a6b8485cfc7c8ce05389538de5770262"
    ),
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK")

GAP_MATRIX_RELATIVE = Path(
    "stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/"
    "machine/implementation_gap_matrix_public_safe.csv"
)
MIGRATION_MATRIX_RELATIVE = Path(
    "stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/"
    "machine/migration_decision_matrix_public_safe.csv"
)

LEDGER_RELATIVE = Path("machine/requirements_ledger_public_safe.csv")
LEDGER_HUMAN_RELATIVE = Path("human/requirements_ledger_zh.md")
BUSINESS_RELATIVE = Path("machine/business_line_matrix_public_safe.csv")
SCOPE_RELATIVE = Path("machine/scope_lock_dispositions_public_safe.csv")
SCOPE_HUMAN_RELATIVE = Path("human/rebuild_scope_lock_zh.md")

LEDGER_HEADERS = [
    "ledger_version",
    "requirement_id",
    "priority",
    "requirement_name",
    "normative_requirement",
    "source_refs",
    "source_member_sha256",
    "primary_stage_refs",
    "task_refs",
    "acceptance_requirement",
    "evidence_requirement",
    "current_implementation_status",
    "implementation_gap_type",
    "severity",
    "gap_impact",
    "current_evidence_refs",
    "migration_disposition",
    "conflict_status",
    "conflict_refs",
    "conflict_disposition",
    "resolution_target_stage",
    "v15_requirement_accepted",
    "implementation_allowed_by_s02_p1",
    "public_safe_status",
]

BUSINESS_HEADERS = [
    "business_line_id",
    "priority",
    "business_line_name",
    "first_manual_work_to_replace",
    "input_classes",
    "output_classes",
    "human_review_boundary",
    "prohibited_automatic_actions",
    "recommended_stage_ids",
    "routing_status",
    "source_refs",
    "product_acceptance_inherited",
    "implementation_allowed_by_s02_p1",
]

SCOPE_HEADERS = [
    "capability_id",
    "capability_name",
    "domain",
    "s01_p2_historical_decision",
    "v15_scope_class",
    "verification_status",
    "source_evidence_refs",
    "scope_rationale",
    "target_stage",
    "preservation_constraint",
    "product_acceptance_inherited",
    "implementation_allowed_by_s02_p1",
]

TRACE_SOURCE_REF = "SOURCE_PACKAGE_TOKEN::04_KMFA_需求追溯矩阵_v2_0.csv"
INHERITANCE_SOURCE_REF = (
    "SOURCE_PACKAGE_TOKEN::11_KMFA_1_4继承_重构_废弃清单_v2_0.md"
)
HISTORY_SOURCE_REF = (
    "SOURCE_PACKAGE_TOKEN::13_KMFA_阶段一与阶段二五环节信息继承清单_v2_0.md"
)
LEDGER_SOURCE_REFS = ";".join(
    [TRACE_SOURCE_REF, INHERITANCE_SOURCE_REF, HISTORY_SOURCE_REF]
)

_RAW_ROOT_RE = re.compile(r"/Users/[^/\s]+/Downloads/KMFA_MetaData")
_EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class BuildError(RuntimeError):
    """Raised when an authoritative source or invariant drifts."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sanitize_public_safe(value: object) -> str:
    text = "" if value is None else str(value)
    text = _RAW_ROOT_RE.sub("RAW_ROOT_TOKEN", text)
    text = _EMAIL_RE.sub("OWNER_NOTIFICATION_EMAIL_TOKEN", text)
    return text


def _normalize_project_root(project_root: Optional[Path]) -> Path:
    root = PROJECT_ROOT if project_root is None else Path(project_root).resolve()
    if (root / "stage_artifacts").is_dir() and (root / "tools").is_dir():
        return root
    nested = root / "KMFA"
    if (nested / "stage_artifacts").is_dir() and (nested / "tools").is_dir():
        return nested
    raise BuildError(f"KMFA project root not found: {root}")


def _read_csv_path(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        raise BuildError(f"required input missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _find_zip_member(archive: ZipFile, basename: str) -> str:
    matches = [name for name in archive.namelist() if Path(name).name == basename]
    if len(matches) != 1:
        raise BuildError(
            f"expected exactly one source member {basename!r}; found {len(matches)}"
        )
    return matches[0]


def _load_source_members(source_package: Path) -> Dict[str, bytes]:
    if not source_package.is_file():
        raise BuildError(f"source package missing: {source_package}")
    package_bytes = source_package.read_bytes()
    actual_package_hash = _sha256(package_bytes)
    if actual_package_hash != SOURCE_PACKAGE_SHA256:
        raise BuildError(
            "source package hash drift: "
            f"expected {SOURCE_PACKAGE_SHA256}, got {actual_package_hash}"
        )

    members: Dict[str, bytes] = {}
    with ZipFile(source_package) as archive:
        for basename, expected_hash in SOURCE_MEMBER_HASHES.items():
            member = _find_zip_member(archive, basename)
            payload = archive.read(member)
            actual_hash = _sha256(payload)
            if actual_hash != expected_hash:
                raise BuildError(
                    f"source member hash drift for {basename}: "
                    f"expected {expected_hash}, got {actual_hash}"
                )
            members[basename] = payload
    return members


def _validate_source_context(members: Mapping[str, bytes]) -> None:
    inheritance = members[
        "11_KMFA_1_4继承_重构_废弃清单_v2_0.md"
    ].decode("utf-8-sig")
    history = members[
        "13_KMFA_阶段一与阶段二五环节信息继承清单_v2_0.md"
    ].decode("utf-8-sig")

    inheritance_anchors = [
        "优先保留但必须复验",
        "必须重构",
        "不再作为产品验收基线",
        "最终切换前执行页面、API、报告和导出零差异",
    ]
    history_anchors = [
        "阶段一锁定信息",
        "阶段二第一环节",
        "阶段二第五环节",
        "融合附件 1–10 业务线，忽略 11 以后",
        "不把内部复核方式写成 Codex 角色任务",
    ]
    for anchor in inheritance_anchors:
        if anchor not in inheritance:
            raise BuildError(f"inheritance source anchor missing: {anchor}")
    for anchor in history_anchors:
        if anchor not in history:
            raise BuildError(f"history source anchor missing: {anchor}")


def _trace_rows(members: Mapping[str, bytes]) -> List[Dict[str, str]]:
    text = members["04_KMFA_需求追溯矩阵_v2_0.csv"].decode("utf-8-sig")
    rows = [dict(row) for row in csv.DictReader(io.StringIO(text))]
    required_headers = {
        "需求ID",
        "优先级",
        "需求名称",
        "需求说明",
        "主要Stage",
        "对应Task",
        "验收要求",
        "证据要求",
    }
    if not rows or not required_headers.issubset(rows[0]):
        raise BuildError("authoritative requirement trace matrix schema drift")

    expected_ids = [f"R{index:03d}" for index in range(1, 56)]
    actual_ids = [row["需求ID"] for row in rows]
    if actual_ids != expected_ids:
        raise BuildError("requirement IDs must be exact ordered R001-R055")
    if len({row["需求名称"] for row in rows}) != 55:
        raise BuildError("requirement names are not unique")
    if len({row["需求说明"].strip() for row in rows}) != 55:
        raise BuildError("requirement normative texts are not unique")
    priority_counts = Counter(row["优先级"] for row in rows)
    if priority_counts != Counter({"P0": 46, "P1": 8, "P2": 1}):
        raise BuildError(f"requirement priority drift: {dict(priority_counts)}")
    return rows


def _build_requirement_rows(
    trace_rows: Sequence[Mapping[str, str]],
    gap_rows: Sequence[Mapping[str, str]],
) -> List[Dict[str, str]]:
    gap_by_id = {row["requirement_id"]: row for row in gap_rows}
    if len(gap_rows) != 55 or len(gap_by_id) != 55:
        raise BuildError("S01-P2 gap matrix must contain 55 unique rows")

    expected_ids = {row["需求ID"] for row in trace_rows}
    if set(gap_by_id) != expected_ids:
        raise BuildError("S01-P2 gap matrix requirement IDs drift from source trace")

    output: List[Dict[str, str]] = []
    for source in trace_rows:
        requirement_id = source["需求ID"]
        gap = gap_by_id[requirement_id]
        if gap["priority"] != source["优先级"]:
            raise BuildError(f"priority drift for {requirement_id}")
        if gap["requirement_name"] != source["需求名称"]:
            raise BuildError(f"name drift for {requirement_id}")

        if requirement_id == "R007":
            if gap["current_status"] != "CONFLICTING_POLICY":
                raise BuildError("R007 must preserve the open legacy policy implementation gap")
            conflict_status = "RESOLVED_BY_V15_PRECEDENCE"
            conflict_refs = (
                "KMFA/metadata/security/public_repo_sensitive_data_policy.jsonl;CAP-029"
            )
            conflict_disposition = (
                "RESOLVED_BY_v1.5_PRECEDENCE;"
                "DEPRECATE_OWNER_AUTHORIZED_RAW_PLAINTEXT_EXCEPTION_IN_S03;"
                "KEEP_PUBLIC_SAFE_SCANNER"
            )
            resolution_target_stage = "S03"
        else:
            conflict_status = "NONE"
            conflict_refs = ""
            conflict_disposition = ""
            resolution_target_stage = ""

        output.append(
            {
                "ledger_version": "v1.5-s02-p1-r1",
                "requirement_id": requirement_id,
                "priority": source["优先级"],
                "requirement_name": _sanitize_public_safe(source["需求名称"]),
                "normative_requirement": _sanitize_public_safe(source["需求说明"]),
                "source_refs": LEDGER_SOURCE_REFS,
                "source_member_sha256": SOURCE_MEMBER_HASHES[
                    "04_KMFA_需求追溯矩阵_v2_0.csv"
                ],
                "primary_stage_refs": source["主要Stage"],
                "task_refs": source["对应Task"],
                "acceptance_requirement": _sanitize_public_safe(source["验收要求"]),
                "evidence_requirement": _sanitize_public_safe(source["证据要求"]),
                "current_implementation_status": gap["current_status"],
                "implementation_gap_type": gap["gap_type"],
                "severity": gap["severity"],
                "gap_impact": _sanitize_public_safe(gap["impact"]),
                "current_evidence_refs": _sanitize_public_safe(gap["evidence_refs"]),
                "migration_disposition": gap["migration_hint"],
                "conflict_status": conflict_status,
                "conflict_refs": conflict_refs,
                "conflict_disposition": conflict_disposition,
                "resolution_target_stage": resolution_target_stage,
                "v15_requirement_accepted": "false",
                "implementation_allowed_by_s02_p1": "false",
                "public_safe_status": "PUBLIC_SAFE",
            }
        )

    if sum(row["priority"] in {"P0", "P1"} for row in output) != 54:
        raise BuildError("P0/P1 requirement count must be 54")
    if any(row["v15_requirement_accepted"] != "false" for row in output):
        raise BuildError("S02-P1 must not accept any v1.5 product requirement")
    if any(row["implementation_allowed_by_s02_p1"] != "false" for row in output):
        raise BuildError("S02-P1 must not authorize product implementation")
    return output


def _business_line_rows() -> List[Dict[str, str]]:
    shared_source = HISTORY_SOURCE_REF
    rows = [
        {
            "business_line_id": "BL-01",
            "priority": "P0",
            "business_line_name": "项目成本分析",
            "first_manual_work_to_replace": "抄表、分类、汇总、毛利、差异、成本报告草稿",
            "input_classes": "合同/结算/签证变更；项目、主体、期间及来源版本；人工、材料、机械、外协、运输、差旅、税费、现场管理、返工、质保成本；开票、回款、付款、质保金",
            "output_classes": "项目收入/成本事实；合同/结算/管理毛利；现金毛利；未归集池；差异队列；成本报告草稿",
            "human_review_boundary": "黄金基准锁定；跨源冲突；低置信成本归集；任何 1 分差异；报告发布",
            "prohibited_automatic_actions": "会计正式入账；低置信自动归集；把未确认值写成事实；正式报告自动发布；老板最终经营判断",
            "recommended_stage_ids": "S06,S07,S12,S17,S20,S21,S23",
            "source_refs": f"{shared_source};R004;R012;R013;R029;R030",
        },
        {
            "business_line_id": "BL-02",
            "priority": "P1",
            "business_line_name": "财务经营报表",
            "first_manual_work_to_replace": "跨表汇总、周/月报初稿、经营摘要",
            "input_classes": "唯一合法账本及经营/项目/资金/税务视图；项目成本；回款应收；资金；税务；质量状态；事实/公式/参数版本",
            "output_classes": "周/月/季/半年/年报草稿；经营摘要；Dashboard；HTML/PDF/CSV/Excel 草稿",
            "human_review_boundary": "主体、期间与报告范围；管理调整；数据限制/等级；跨格式一致性；复核与发布",
            "prohibited_automatic_actions": "会计正式入账；缺关键数据仍标完整；自动批准/发布；对外发送完整经营报告；老板最终经营判断",
            "recommended_stage_ids": "S09,S12,S13,S16,S21,S22,S23",
            "source_refs": f"{shared_source};R022;R026;R034;R035;R036;R037",
        },
        {
            "business_line_id": "BL-03",
            "priority": "P1",
            "business_line_name": "回款与应收账龄",
            "first_manual_work_to_replace": "回款统计、账龄、保证金、催收优先级",
            "input_classes": "合同节点；开票；回款；账龄截止日；争议；质保金/保证金；客户、项目、主体；银行回单",
            "output_classes": "回款统计；应收与账龄；质保金/保证金状态；争议清单；可解释催收优先级",
            "human_review_boundary": "客户/项目归属；未开票与应收区分；争议和质保金；排序依据；是否联系客户",
            "prohibited_automatic_actions": "自动催收决定；自动联系客户；法律文件；修改来源；跨主体错误汇总",
            "recommended_stage_ids": "S08,S18,S20,S21,S23",
            "source_refs": f"{shared_source};R031",
        },
        {
            "business_line_id": "BL-04",
            "priority": "P1",
            "business_line_name": "销售绩效事实",
            "first_manual_work_to_replace": "绩效基础事实和复核清单，不做最终审批",
            "input_classes": "客户、项目、合同；签约、结算、开票、回款事实；绩效政策版本；责任归属及证据",
            "output_classes": "绩效基础事实；归属候选；异常清单；人工复核清单",
            "human_review_boundary": "政策版本；人员/项目归属；例外；最终绩效结果",
            "prohibited_automatic_actions": "最终绩效审批；工资或奖金最终审批；薪资导出/发放；无证据自动归属",
            "recommended_stage_ids": "S08,S12,S13,S20,S21,S23",
            "source_refs": f"{shared_source};R051",
        },
        {
            "business_line_id": "BL-05",
            "priority": "P1",
            "business_line_name": "资金、现金与贷款",
            "first_manual_work_to_replace": "资金缺口、余额、贷款到期，不执行付款",
            "input_classes": "公司主体、银行、账户；流水、余额、回单；预计收付款；回款计划；贷款、利率、到期日；情景假设版本",
            "output_classes": "账户余额；现金缺口；现金预测/资金计划；贷款到期；情景结果",
            "human_review_boundary": "主体/银行/账户匹配；余额日期；事实与预测边界；假设；融资/付款决定",
            "prohibited_automatic_actions": "银行付款；贷款交易；跨主体自动合并；把预测写成事实",
            "recommended_stage_ids": "S08,S13,S18,S20,S21,S23",
            "source_refs": f"{shared_source};R016;R032",
        },
        {
            "business_line_id": "BL-06",
            "priority": "P1",
            "business_line_name": "开票、纳税与政策",
            "first_manual_work_to_replace": "风险和证据缺口，不做正式申报",
            "input_classes": "合同与项目；销项/进项；税率、抵扣、红冲、未开票；账务与项目事实；研发项目、人员、费用、知识产权、高新收入等政策证据",
            "output_classes": "发票/税率异常；项目税负；风险清单；政策资格候选；证据缺口与准备清单",
            "human_review_boundary": "税率及规则有效期；发票异常；抵扣/红冲；资格判断；证据完整度；专业签字",
            "prohibited_automatic_actions": "开发票；纳税申报；自动税务调整；政策申报；法律/专业最终结论",
            "recommended_stage_ids": "S09,S13,S19,S20,S21,S23",
            "source_refs": f"{shared_source};R033",
        },
        {
            "business_line_id": "BL-07",
            "priority": "P1",
            "business_line_name": "外协采购成本",
            "first_manual_work_to_replace": "外协归集、重复候选、未归集池",
            "input_classes": "外协、采购、材料、领料、库存、付款事实；供应商；项目与主体；来源/期间",
            "output_classes": "外协/采购成本归集；重复候选；未归集池；跨项目异常；影响预览",
            "human_review_boundary": "供应商/项目匹配；低置信归集；重复判定；跨项目异常；成本守恒",
            "prohibited_automatic_actions": "供应商选择；采购/下单；付款；会计正式入账；低置信自动归集",
            "recommended_stage_ids": "S08,S12,S17,S20,S21,S23",
            "source_refs": f"{shared_source};R029;R051",
        },
        {
            "business_line_id": "BL-08",
            "priority": "P1",
            "business_line_name": "项目交付状态",
            "first_manual_work_to_replace": "开工、完工、结算、开票、回款生命周期",
            "input_classes": "合同；开工/完工日期；里程碑；签证变更；结算、开票、回款；责任人；来源版本",
            "output_classes": "项目生命周期；当前状态；逾期/缺证据事项；状态冲突；交付摘要",
            "human_review_boundary": "冲突状态；里程碑确认；验收/结算依据；责任人；历史状态变更",
            "prohibited_automatic_actions": "修改来源状态；现场安全或技术决策；技术/安全签字；法律文件；无证据自动推进状态",
            "recommended_stage_ids": "S08,S12,S17,S20,S21,S23",
            "source_refs": f"{shared_source};R051",
        },
        {
            "business_line_id": "BL-09",
            "priority": "P2",
            "business_line_name": "客户经营",
            "first_manual_work_to_replace": "客户价值、项目毛利、回款质量",
            "input_classes": "客户主数据及历史名称；项目组合；项目毛利；回款/应收；争议；合同履约；数据质量",
            "output_classes": "客户价值视图；项目毛利；回款质量；风险/重点事项；客户组合摘要",
            "human_review_boundary": "客户合并；价值/信用/风险解释；优先级；经营判断",
            "prohibited_automatic_actions": "客户催收决定；自动联系客户；信用/价格最终决策；法律文件；老板最终经营判断",
            "recommended_stage_ids": "S08,S12,S13,S16,S17,S18,S20,S21,S23",
            "source_refs": f"{shared_source};R027;R028;R051",
        },
        {
            "business_line_id": "BL-10",
            "priority": "P2",
            "business_line_name": "财务 SOP",
            "first_manual_work_to_replace": "操作检查和交接知识，不参与自动财务执行",
            "input_classes": "版本化治理规则；来源检查状态；角色权限；审计事件；操作清单；异常与历史证据",
            "output_classes": "检查清单；交接知识；异常升级路径；操作证据；SOP 版本",
            "human_review_boundary": "SOP 版本批准；角色与权限；例外处理；完成证据；交接确认",
            "prohibited_automatic_actions": "会计入账、付款、开票、报税、工资/奖金审批等任何自动财务执行；把清单完成当成业务事实",
            "recommended_stage_ids": "S15,S20,S22,S23,S24",
            "source_refs": f"{shared_source};R047;R051;R055",
        },
    ]

    for row in rows:
        row["routing_status"] = "PROPOSED_FOR_S02_P2_TRACEABILITY"
        row["product_acceptance_inherited"] = "false"
        row["implementation_allowed_by_s02_p1"] = "false"
        for key, value in list(row.items()):
            row[key] = _sanitize_public_safe(value)

    expected_ids = [f"BL-{index:02d}" for index in range(1, 11)]
    if [row["business_line_id"] for row in rows] != expected_ids:
        raise BuildError("business line IDs must be exact BL-01..BL-10")
    priority_counts = Counter(row["priority"] for row in rows)
    if priority_counts != Counter({"P0": 1, "P1": 7, "P2": 2}):
        raise BuildError(f"business line priority drift: {dict(priority_counts)}")
    return rows


def _build_scope_rows(
    migration_rows: Sequence[Mapping[str, str]],
) -> List[Dict[str, str]]:
    if len(migration_rows) != 37:
        raise BuildError("S01-P2 migration matrix must contain 37 rows")
    expected_ids = [f"CAP-{index:03d}" for index in range(1, 38)]
    actual_ids = [row["capability_id"] for row in migration_rows]
    if actual_ids != expected_ids:
        raise BuildError("migration capability IDs must be exact ordered CAP-001..CAP-037")

    historical_counts = Counter(row["decision"] for row in migration_rows)
    expected_historical = Counter(
        {"KEEP": 12, "REFACTOR": 12, "UNVERIFIED": 8, "DEPRECATE": 5}
    )
    if historical_counts != expected_historical:
        raise BuildError(f"historical migration decision drift: {dict(historical_counts)}")

    scope_class = {
        "KEEP": "KEEP_GOVERNANCE_BASELINE",
        "REFACTOR": "REBUILD",
        "UNVERIFIED": "DEFER",
        "DEPRECATE": "DEPRECATE",
    }
    output: List[Dict[str, str]] = []
    for source in migration_rows:
        output.append(
            {
                "capability_id": source["capability_id"],
                "capability_name": _sanitize_public_safe(source["capability_name"]),
                "domain": source["domain"],
                "s01_p2_historical_decision": source["decision"],
                "v15_scope_class": scope_class[source["decision"]],
                "verification_status": source["verification_status"],
                "source_evidence_refs": _sanitize_public_safe(source["evidence_refs"]),
                "scope_rationale": _sanitize_public_safe(source["rationale"]),
                "target_stage": source["target_stage"],
                "preservation_constraint": _sanitize_public_safe(
                    source["preservation_constraint"]
                ),
                "product_acceptance_inherited": "false",
                "implementation_allowed_by_s02_p1": "false",
            }
        )

    derived_counts = Counter(row["v15_scope_class"] for row in output)
    expected_derived = Counter(
        {
            "KEEP_GOVERNANCE_BASELINE": 12,
            "REBUILD": 12,
            "DEFER": 8,
            "DEPRECATE": 5,
        }
    )
    if derived_counts != expected_derived:
        raise BuildError(f"v1.5 scope class drift: {dict(derived_counts)}")
    if any(row["product_acceptance_inherited"] != "false" for row in output):
        raise BuildError("no historical product acceptance may be inherited")
    if any(row["implementation_allowed_by_s02_p1"] != "false" for row in output):
        raise BuildError("S02-P1 may not authorize capability implementation")
    return output


def _csv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(headers),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    return buffer.getvalue().encode("utf-8")


def _md_cell(value: object) -> str:
    return _sanitize_public_safe(value).replace("|", "\\|").replace("\n", "<br>")


def _requirements_markdown(rows: Sequence[Mapping[str, str]]) -> bytes:
    lines = [
        "# KMFA v1.5 S02-P1 唯一需求总账",
        "",
        "## 结论",
        "",
        "- canonical requirements：55（P0=46、P1=8、P2=1；P0/P1=54）。",
        "- `R001-R055` 的 ID、优先级、名称和规范说明以 v2.0 source package 的需求追溯矩阵为准。",
        "- 55 项当前 `v15_requirement_accepted=false`，且 `implementation_allowed_by_s02_p1=false`。本 Phase 只做需求合并与范围锁，不表示产品能力已实现或验收。",
        "- R007 的规范冲突已按 v1.5 strict public-safe 规则决策；旧政策实现差距仍为 `CONFLICTING_POLICY / OPEN`，必须在 S03 废止 owner raw/plaintext 例外。",
        "- source package：`SOURCE_PACKAGE_TOKEN`；package SHA-256：`"
        + SOURCE_PACKAGE_SHA256
        + "`。",
        "",
        "## 权威与冲突规则",
        "",
        "1. 需求追溯矩阵决定 canonical ID、priority、normative text、Stage/Task、acceptance 与 evidence。",
        "2. 继承清单仅提供来源上下文；S01-P2 gap/migration 仅提供现状与迁移 annotation，不新建 requirement。",
        "3. 同一语义只保留一行并登记多个 source refs；新增需求必须进入 change control。",
        "4. 语义冲突不得静默选边；没有明确权威处置时必须标记阻塞。",
        "",
        "## Requirement ledger",
        "",
        "| ID | Priority | 需求 | 规范要求 | 当前实现状态 | 迁移处置 | 冲突状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {requirement_id} | {priority} | {requirement_name} | "
            "{normative_requirement} | {current_implementation_status} | "
            "{migration_disposition} | {conflict_status} |".format(
                **{key: _md_cell(value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Public-safe boundary",
            "",
            "总账只保存规范文本、token、相对 evidence refs 和状态；不保存 raw 业务内容、raw 绝对路径、通知邮箱、private hash 或凭据。",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _scope_markdown(rows: Sequence[Mapping[str, str]]) -> bytes:
    lines = [
        "# KMFA v0.1.4 治理基线到 v1.5 FULL REBUILD 范围锁",
        "",
        "## 结论",
        "",
        "- capability 总数：37。",
        "- `KEEP_GOVERNANCE_BASELINE=12`：仅继承不变量、合同和测试意图，不继承产品验收。",
        "- `REBUILD=12`：在未来真实 runtime 中重建，不在旧静态产品上叠加。",
        "- `DEFER=8`：仍在 v1.5 范围内，但目标 Stage 新证据前保持未验收和 NO_GO。",
        "- `DEPRECATE=5`：不得作为 v1.5 产品基线；保留历史/回滚证据不表示本 Phase 删除文件。",
        "- 37/37 均为 `product_acceptance_inherited=false`、`implementation_allowed_by_s02_p1=false`。",
        "",
        "## 硬边界",
        "",
        "1. `FULL REBUILD` 不得解释成旧 runtime refactor；S01 的 `RUNTIME_OBJECT_MISSING / BLOCKED / NOT_PASSED / NO_GO` 历史事实不变。",
        "2. CAP-029 必须 `DEPRECATE`：v1.5 公开仓库不得保留 owner 授权 raw/plaintext 例外；S03 才执行治理实现修复。",
        "3. 静态 App launcher、旧静态 IA、DOM 点击验收和普通页面技术词不得作为 v1.5 产品验收基线。",
        "4. 本 Phase 不启动 runtime/API/DB/UI、S02-P2/P3 或 S03+ 实现，不授权业务动作、GitHub upload 或 App reinstall。",
        "",
        "## Scope dispositions",
        "",
        "| Capability | 名称 | 历史决策 | v1.5 scope class | 验证状态 | 目标 Stage | 产品验收继承 | 实现授权 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {capability_id} | {capability_name} | {s01_p2_historical_decision} | "
            "{v15_scope_class} | {verification_status} | {target_stage} | "
            "{product_acceptance_inherited} | {implementation_allowed_by_s02_p1} |".format(
                **{key: _md_cell(value) for key, value in row.items()}
            )
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        text = payload.decode("utf-8")
        if "/Users/" in text:
            raise BuildError(f"absolute user path leaked into output: {path}")
        if _EMAIL_RE.search(text):
            raise BuildError(f"email leaked into output: {path}")
        if "KMFA_MetaData" in text:
            raise BuildError(f"raw root name leaked instead of token: {path}")


def expected_core_outputs(
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> Dict[Path, bytes]:
    """Return deterministic absolute-path to bytes mappings for five artifacts."""

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    destination = (
        root / OUTPUT_ROOT_RELATIVE
        if output_root is None
        else Path(output_root).resolve()
    )

    members = _load_source_members(package)
    _validate_source_context(members)
    trace_rows = _trace_rows(members)
    gap_rows = _read_csv_path(root / GAP_MATRIX_RELATIVE)
    migration_rows = _read_csv_path(root / MIGRATION_MATRIX_RELATIVE)

    requirement_rows = _build_requirement_rows(trace_rows, gap_rows)
    business_rows = _business_line_rows()
    scope_rows = _build_scope_rows(migration_rows)

    outputs = {
        destination / LEDGER_RELATIVE: _csv_bytes(LEDGER_HEADERS, requirement_rows),
        destination / LEDGER_HUMAN_RELATIVE: _requirements_markdown(
            requirement_rows
        ),
        destination / BUSINESS_RELATIVE: _csv_bytes(BUSINESS_HEADERS, business_rows),
        destination / SCOPE_RELATIVE: _csv_bytes(SCOPE_HEADERS, scope_rows),
        destination / SCOPE_HUMAN_RELATIVE: _scope_markdown(scope_rows),
    }
    _assert_public_safe(outputs)
    return outputs


def _write_outputs(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"WROTE {path}")


def _check_outputs(outputs: Mapping[Path, bytes]) -> None:
    failures: List[str] = []
    for path, expected in outputs.items():
        if not path.is_file():
            failures.append(f"MISSING {path}")
            continue
        actual = path.read_bytes()
        if actual != expected:
            failures.append(
                f"DRIFT {path} expected_sha256={_sha256(expected)} "
                f"actual_sha256={_sha256(actual)}"
            )
    if failures:
        raise BuildError("core artifact check failed:\n" + "\n".join(failures))
    print(f"PASS: exact core outputs match ({len(outputs)} files)")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build/check v1.5 S02-P1 requirements and scope-lock core artifacts"
    )
    parser.add_argument(
        "--source-package",
        type=Path,
        default=DEFAULT_SOURCE_PACKAGE,
        help="authoritative v2.0 TaskPack/Roadmap ZIP",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="KMFA project root (the directory containing tools and stage_artifacts)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="optional artifact destination override",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare existing artifacts byte-for-byte instead of writing",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        outputs = expected_core_outputs(
            project_root=args.project_root,
            source_package=args.source_package,
            output_root=args.output_root,
        )
        if args.check:
            _check_outputs(outputs)
        else:
            _write_outputs(outputs)
    except (BuildError, OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
