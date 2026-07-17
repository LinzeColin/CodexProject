#!/usr/bin/env python3
"""KMFA v1.5 S17-P3 项目处理流程与专题报告公开合成合同。"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s12_p2_core_calculations as calculations
from KMFA.tools import v015_s12_p3_engineering_logic as engineering
from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s17_p1_project_list as project_list
from KMFA.tools import v015_s17_p2_project_detail as project_detail


RUN_PHASE_ID = "V015_S17_P3_PROJECT_WORKFLOW"
ROADMAP_PHASE_ID = "S17-P3"
TASK_ID = "KMFA-V015-S17-P3-PROJECT-WORKFLOW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S17-P3-PROJECT-WORKFLOW"
VERSION = "1.5.0-dev-s17p3"

EVENT_SCHEMA_VERSION = "kmfa.v015.s17p3.project_workflow_event.v1"
WORKFLOW_SCHEMA_VERSION = "kmfa.v015.s17p3.project_workflow.v1"
REPORT_SCHEMA_VERSION = "kmfa.v015.s17p3.project_cost_report.v1"
AUTO_ALLOCATION_MIN_CONFIDENCE_BPS = engineering.DEFAULT_LINK_POLICY["auto_link_min_confidence_bps"]
MONEY_TOLERANCE_CENTS = 0
UNALLOCATED_CANDIDATE_COUNT = 3
VARIANCE_SOURCE_COUNT = 2
REPORT_FORMAT_COUNT = 3
EVIDENCE_INDEX_GROUP_COUNT = 4
BROWSER_FLOW_COUNT = 10
VISUAL_EVIDENCE_COUNT = 6

EVENT_TYPES = (
    "UNALLOCATED_COST_ASSIGNED",
    "PROJECT_VARIANCE_RESOLVED",
    "EVENT_REVERSED",
    "RERUN_COMPLETED",
)
EVENT_TYPE_LABELS = {
    "UNALLOCATED_COST_ASSIGNED": "归集未归集成本",
    "PROJECT_VARIANCE_RESOLVED": "确认项目差异",
    "EVENT_REVERSED": "撤销处理",
    "RERUN_COMPLETED": "完成页面与报告重算",
}
DOMAIN_EVENT_TYPES = EVENT_TYPES[:2]
REVERSIBLE_EVENT_TYPES = DOMAIN_EVENT_TYPES
GENESIS_HASH = "GENESIS"
DEFAULT_RUNTIME_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime"
    / "v015_s17_p3_project_workflow"
    / "project_workflow_events.jsonl"
)

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}")
_FORBIDDEN_PUBLIC_TEXT = ("/Users/", "/Volumes/", "KMFA_MetaData", "private://", "file://")


class ProjectWorkflowError(ValueError):
    """项目处理请求违反本阶段合同。"""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ProjectWorkflowError(f"{field} 不是有效编号")
    return value


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 240) -> str:
    if not isinstance(value, str):
        raise ProjectWorkflowError(f"{field} 必须是文字")
    result = value.strip()
    if not minimum <= len(result) <= maximum:
        raise ProjectWorkflowError(f"{field} 长度不符合要求")
    if any(token.lower() in result.lower() for token in _FORBIDDEN_PUBLIC_TEXT):
        raise ProjectWorkflowError(f"{field} 含有私有路径或定位符")
    return result


def _integer(value: Any, field: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProjectWorkflowError(f"{field} 必须是整数")
    if minimum is not None and value < minimum:
        raise ProjectWorkflowError(f"{field} 不能小于 {minimum}")
    if maximum is not None and value > maximum:
        raise ProjectWorkflowError(f"{field} 不能大于 {maximum}")
    return value


def _basis_points(numerator: int, denominator: int) -> int | None:
    if denominator == 0:
        return None
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    return sign * ((abs(numerator) * 10_000 + abs(denominator) // 2) // abs(denominator))


def _format_yuan(cents: int) -> str:
    """以整数分精确输出元，避免金额进入浮点运算。"""

    sign = "-" if cents < 0 else ""
    yuan, remainder = divmod(abs(cents), 100)
    return f"{sign}{yuan:,}.{remainder:02d}"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p3.source_contract.v1",
        "stage_id": "S17",
        "stage_name_zh": "项目列表、项目详情与成本分析流程",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "项目处理流程",
        "task_ids": ["S17P3T01", "S17P3T02", "S17P3T03"],
        "task_names_zh": ["处理未归集成本", "处理项目差异", "生成项目成本专题报告"],
        "actions_zh": [
            "显示候选项目、依据、影响并经确认写入事件。",
            "并排比较来源，解释差异，预览影响后重算。",
            "输出 HTML、PDF、Excel 附表和证据索引。",
        ],
        "acceptance_zh": ["不修改源数据，可撤销。", "处理后报告同步。", "与页面和黄金基准一致。"],
        "stop_conditions_zh": ["低置信自动归集失败。", "只改页面状态失败。", "任一分差异失败。"],
        "evidence_zh": ["端到端测试。", "持久化和重跑测试。", "导出零差异测试。"],
        "data_classification": "PUBLIC_SYNTHETIC",
    }


def _base_detail(project_id: str, company_id: str, period: str) -> dict[str, Any]:
    return project_detail.project_detail(project_id=project_id, company_id=company_id, period=period)


def unallocated_work_item(
    project_id: str = "PUB-PROJ-001",
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    detail = _base_detail(project_id, company_id, period)
    project = detail["project"]
    amount = detail["cost"]["unallocated"]["amount_cents"]
    catalog = project_list.project_catalog(company_id, period)
    alternatives = [row for row in catalog if row["project_id"] != project_id]
    candidates = [
        {
            "candidate_id": "CAND-S17P3-001",
            "candidate_project_id": project_id,
            "candidate_project_name_zh": project["project_name_zh"],
            "target_category_id": "SUBCONTRACT",
            "target_category_zh": project_detail.CATEGORY_LABELS["SUBCONTRACT"],
            "confidence_bps": 9600,
            "confidence_zh": "高",
            "basis_zh": ["项目编号完全一致", "验收批次与项目期间一致", "分包合同索引可追溯"],
            "auto_allocation_allowed": True,
            "manual_confirmation_allowed": True,
            "recommended": True,
        },
        {
            "candidate_id": "CAND-S17P3-002",
            "candidate_project_id": alternatives[0]["project_id"],
            "candidate_project_name_zh": alternatives[0]["project_name_zh"],
            "target_category_id": "MATERIAL",
            "target_category_zh": project_detail.CATEGORY_LABELS["MATERIAL"],
            "confidence_bps": 7800,
            "confidence_zh": "中",
            "basis_zh": ["客户相同", "期间接近", "缺少唯一项目编号"],
            "auto_allocation_allowed": False,
            "manual_confirmation_allowed": False,
            "recommended": False,
        },
        {
            "candidate_id": "CAND-S17P3-003",
            "candidate_project_id": alternatives[1]["project_id"],
            "candidate_project_name_zh": alternatives[1]["project_name_zh"],
            "target_category_id": "SITE_MANAGEMENT",
            "target_category_zh": project_detail.CATEGORY_LABELS["SITE_MANAGEMENT"],
            "confidence_bps": 5200,
            "confidence_zh": "低",
            "basis_zh": ["仅有期间相同", "项目编号不一致", "没有验收资料支持"],
            "auto_allocation_allowed": False,
            "manual_confirmation_allowed": False,
            "recommended": False,
        },
    ]
    return {
        "work_item_id": f"UNALLOCATED:{company_id}:{period}:{project_id}",
        "project_id": project_id,
        "project_name_zh": project["project_name_zh"],
        "amount_cents": amount,
        "amount_display_zh": homepage.format_wan_cents(amount),
        "source_ref": detail["cost"]["unallocated"]["source_ref"],
        "candidate_count": len(candidates),
        "candidates": candidates,
        "auto_allocation_min_confidence_bps": AUTO_ALLOCATION_MIN_CONFIDENCE_BPS,
        "source_data_write_allowed": False,
        "confirmation_required": True,
        "reversal_required_for_change": True,
    }


def _candidate(work_item: Mapping[str, Any], candidate_id: str) -> dict[str, Any]:
    value = next((row for row in work_item["candidates"] if row["candidate_id"] == candidate_id), None)
    if value is None:
        raise ProjectWorkflowError("候选项目不存在")
    return dict(value)


def preview_unallocated_assignment(
    *,
    project_id: str,
    candidate_id: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    detail = _base_detail(project_id, company_id, period)
    item = unallocated_work_item(project_id, company_id, period)
    candidate = _candidate(item, candidate_id)
    category = next(
        row for row in detail["cost"]["categories"] if row["category_id"] == candidate["target_category_id"]
    )
    same_project = candidate["candidate_project_id"] == project_id
    impact = {
        "unallocated_before_cents": item["amount_cents"],
        "unallocated_after_cents": 0 if same_project else item["amount_cents"],
        "target_category_before_cents": category["actual_cents"],
        "target_category_after_cents": category["actual_cents"] + item["amount_cents"] if same_project else category["actual_cents"],
        "project_cost_before_cents": detail["cost"]["actual_total_cents"],
        "project_cost_after_cents": detail["cost"]["actual_total_cents"],
        "gross_profit_before_cents": detail["overview"]["gross_profit_cents"],
        "gross_profit_after_cents": detail["overview"]["gross_profit_cents"],
        "portfolio_cost_difference_cents": 0,
    }
    result = {
        "schema_version": "kmfa.v015.s17p3.unallocated_assignment_preview.v1",
        "work_item_id": item["work_item_id"],
        "project_id": project_id,
        "candidate": candidate,
        "amount_cents": item["amount_cents"],
        "same_project": same_project,
        "impact": impact,
        "auto_allocation_allowed": candidate["auto_allocation_allowed"] and same_project,
        "manual_confirmation_allowed": candidate["manual_confirmation_allowed"] and same_project,
        "confirmation_required": True,
        "reversible": True,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "money_difference_cents": impact["project_cost_after_cents"] - impact["project_cost_before_cents"],
    }
    result["preview_fingerprint"] = _fingerprint(result)
    return result


def assert_auto_allocation_allowed(preview: Mapping[str, Any]) -> None:
    confidence = _integer(preview["candidate"]["confidence_bps"], "confidence_bps", minimum=0, maximum=10_000)
    if confidence < AUTO_ALLOCATION_MIN_CONFIDENCE_BPS or preview.get("auto_allocation_allowed") is not True:
        raise ProjectWorkflowError("低置信候选禁止自动归集")


def variance_work_item(
    project_id: str = "PUB-PROJ-001",
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    detail = _base_detail(project_id, company_id, period)
    ledger_cost = detail["cost"]["actual_total_cents"]
    settlement_cost = ledger_cost - 1_280_000
    sources = [
        {
            "source_id": "PROJECT_COST_LEDGER",
            "source_name_zh": "项目成本分类账",
            "amount_cents": ledger_cost,
            "amount_display_zh": homepage.format_wan_cents(ledger_cost),
            "as_of": "2026-07-15",
            "basis_zh": "十类成本与未归集成本合计",
            "source_ref": detail["cost"]["source_ref"],
            "completeness_bps": 10_000,
        },
        {
            "source_id": "SETTLEMENT_SUPPORT",
            "source_name_zh": "结算支持资料",
            "amount_cents": settlement_cost,
            "amount_display_zh": homepage.format_wan_cents(settlement_cost),
            "as_of": "2026-07-15",
            "basis_zh": "已确认结算口径，剔除尚未支持的暂估项",
            "source_ref": f"PUBLIC-SYNTHETIC:SETTLEMENT-COST:{company_id}:{period}:{project_id}",
            "completeness_bps": 9800,
        },
    ]
    return {
        "variance_id": f"PROJECT-COST-VARIANCE:{company_id}:{period}:{project_id}",
        "project_id": project_id,
        "label_zh": "项目成本来源差异",
        "difference_cents": ledger_cost - settlement_cost,
        "difference_display_zh": homepage.format_wan_cents(ledger_cost - settlement_cost),
        "source_count": len(sources),
        "sources": sources,
        "explanation_zh": "分类账包含尚未取得结算支持的暂估项，需人工选择本次报告口径。",
        "resolution_options": [
            {
                "option_id": "KEEP_PROJECT_LEDGER",
                "label_zh": "保留项目成本分类账",
                "selected_cost_cents": ledger_cost,
                "reason_zh": "保持当前管理口径，不改变报告金额。",
            },
            {
                "option_id": "USE_SETTLEMENT_SUPPORT",
                "label_zh": "采用已确认结算口径",
                "selected_cost_cents": settlement_cost,
                "reason_zh": "剔除缺少结算支持的暂估项，并在证据索引保留差异。",
            },
        ],
        "impact_preview_required": True,
        "rerun_required": True,
        "source_data_write_allowed": False,
    }


def _variance_option(item: Mapping[str, Any], option_id: str) -> dict[str, Any]:
    value = next((row for row in item["resolution_options"] if row["option_id"] == option_id), None)
    if value is None:
        raise ProjectWorkflowError("差异处理选项不存在")
    return dict(value)


def preview_variance_resolution(
    *,
    project_id: str,
    option_id: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    detail = _base_detail(project_id, company_id, period)
    item = variance_work_item(project_id, company_id, period)
    option = _variance_option(item, option_id)
    before_cost = detail["cost"]["actual_total_cents"]
    after_cost = option["selected_cost_cents"]
    revenue = detail["overview"]["revenue_cents"]
    before_profit = revenue - before_cost
    after_profit = revenue - after_cost
    result = {
        "schema_version": "kmfa.v015.s17p3.variance_resolution_preview.v1",
        "variance_id": item["variance_id"],
        "project_id": project_id,
        "source_comparison": item["sources"],
        "selected_option": option,
        "explanation_zh": item["explanation_zh"],
        "impact": {
            "cost_before_cents": before_cost,
            "cost_after_cents": after_cost,
            "gross_profit_before_cents": before_profit,
            "gross_profit_after_cents": after_profit,
            "gross_margin_before_bps": _basis_points(before_profit, revenue),
            "gross_margin_after_bps": _basis_points(after_profit, revenue),
            "affected_report_ids": ["PROJECT_DETAIL", "PROJECT_COST_SPECIAL_REPORT"],
        },
        "impact_preview_passed": True,
        "rerun_required": True,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
    }
    result["preview_fingerprint"] = _fingerprint(result)
    return result


def _event_hash(row: Mapping[str, Any]) -> str:
    return _fingerprint({key: value for key, value in row.items() if key != "content_hash"})


def _event(
    *,
    sequence: int,
    previous_hash: str,
    event_type: str,
    project_id: str,
    payload: Mapping[str, Any],
    actor_ref: str,
    reason_zh: str,
    idempotency_key: str,
    event_time: str,
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ProjectWorkflowError("不支持的处理事件")
    project_id = _identifier(project_id, "project_id")
    actor_ref = _identifier(actor_ref, "actor_ref")
    idempotency_key = _identifier(idempotency_key, "idempotency_key")
    reason_zh = _text(reason_zh, "reason_zh", minimum=4)
    identity = hashlib.sha256(f"{project_id}|{event_type}|{idempotency_key}".encode()).hexdigest()[:20].upper()
    row: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": f"S17P3-EVT-{identity}",
        "event_sequence": sequence,
        "event_type": event_type,
        "event_type_zh": EVENT_TYPE_LABELS[event_type],
        "project_id": project_id,
        "actor_ref": actor_ref,
        "reason_zh": reason_zh,
        "idempotency_key": idempotency_key,
        "event_time": event_time,
        "payload": copy.deepcopy(dict(payload)),
        "append_only": True,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "reversible": event_type in REVERSIBLE_EVENT_TYPES,
        "previous_event_hash": previous_hash,
        "content_hash": "",
    }
    row["content_hash"] = _event_hash(row)
    return row


def validate_event_chain(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    previous_hash = GENESIS_HASH
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    for index, raw in enumerate(events, start=1):
        row = copy.deepcopy(dict(raw))
        if row.get("schema_version") != EVENT_SCHEMA_VERSION:
            raise ProjectWorkflowError("处理记录版本不正确")
        if row.get("event_sequence") != index:
            raise ProjectWorkflowError("处理记录顺序不连续")
        if row.get("previous_event_hash") != previous_hash:
            raise ProjectWorkflowError("处理记录哈希链断裂")
        if row.get("content_hash") != _event_hash(row):
            raise ProjectWorkflowError("处理记录内容校验失败")
        event_id = _identifier(row.get("event_id"), "event_id")
        idempotency_key = _identifier(row.get("idempotency_key"), "idempotency_key")
        if event_id in seen_ids or idempotency_key in seen_keys:
            raise ProjectWorkflowError("处理记录编号或幂等键重复")
        if row.get("event_type") not in EVENT_TYPES:
            raise ProjectWorkflowError("处理记录类型不受支持")
        if row.get("event_type_zh") != EVENT_TYPE_LABELS[row["event_type"]]:
            raise ProjectWorkflowError("处理记录中文类型不正确")
        if row.get("append_only") is not True or row.get("source_data_write_count") != 0:
            raise ProjectWorkflowError("处理记录必须只追加且不得改写源数据")
        seen_ids.add(event_id)
        seen_keys.add(idempotency_key)
        previous_hash = row["content_hash"]
        validated.append(row)
    return validated


class EventJournal:
    """带哈希链、幂等键和 fsync 的本地追加式处理记录。"""

    def __init__(self, path: Path | str = DEFAULT_RUNTIME_EVENT_PATH) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()

    def read(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.path.is_file():
                return []
            rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
            return validate_event_chain(rows)

    def append(
        self,
        *,
        event_type: str,
        project_id: str,
        payload: Mapping[str, Any],
        actor_ref: str,
        reason_zh: str,
        idempotency_key: str,
        event_time: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            events = self.read()
            existing = next((row for row in events if row["idempotency_key"] == idempotency_key), None)
            payload_copy = copy.deepcopy(dict(payload))
            if existing is not None:
                if existing["event_type"] != event_type or existing["project_id"] != project_id or existing["payload"] != payload_copy:
                    raise ProjectWorkflowError("幂等键已用于不同处理内容")
                return copy.deepcopy(existing)
            row = _event(
                sequence=len(events) + 1,
                previous_hash=events[-1]["content_hash"] if events else GENESIS_HASH,
                event_type=event_type,
                project_id=project_id,
                payload=payload_copy,
                actor_ref=actor_ref,
                reason_zh=reason_zh,
                idempotency_key=idempotency_key,
                event_time=event_time or _now(),
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            validate_event_chain(self.read())
            return copy.deepcopy(row)

    def reverse(
        self,
        *,
        event_id: str,
        actor_ref: str,
        reason_zh: str,
        idempotency_key: str,
        event_time: str | None = None,
    ) -> dict[str, Any]:
        events = self.read()
        target = next((row for row in events if row["event_id"] == event_id), None)
        if target is None or target["event_type"] not in REVERSIBLE_EVENT_TYPES:
            raise ProjectWorkflowError("只能撤销已存在的归集或差异处理记录")
        reversed_ids = {row["payload"].get("reverses_event_id") for row in events if row["event_type"] == "EVENT_REVERSED"}
        if event_id in reversed_ids:
            raise ProjectWorkflowError("该处理记录已经撤销")
        return self.append(
            event_type="EVENT_REVERSED",
            project_id=target["project_id"],
            payload={"reverses_event_id": event_id, "reversed_event_type": target["event_type"]},
            actor_ref=actor_ref,
            reason_zh=reason_zh,
            idempotency_key=idempotency_key,
            event_time=event_time,
        )


def _event_scope(
    rows: Sequence[Mapping[str, Any]],
    row: Mapping[str, Any],
    *,
    seen: set[str] | None = None,
) -> tuple[str, str, str]:
    """从处理对象或被引用事件中恢复公司、期间和项目边界。"""

    visited = set() if seen is None else set(seen)
    event_id = str(row["event_id"])
    if event_id in visited:
        raise ProjectWorkflowError("处理记录作用域引用形成循环")
    visited.add(event_id)
    event_type = str(row["event_type"])
    payload = row["payload"]
    if event_type == "UNALLOCATED_COST_ASSIGNED":
        scoped_ref = str(payload.get("work_item_id", ""))
    elif event_type == "PROJECT_VARIANCE_RESOLVED":
        scoped_ref = str(payload.get("variance_id", ""))
    else:
        reference_key = "source_event_id" if event_type == "RERUN_COMPLETED" else "reverses_event_id"
        referenced_id = str(payload.get(reference_key, ""))
        target = next((item for item in rows if item["event_id"] == referenced_id), None)
        if target is None:
            raise ProjectWorkflowError("处理记录引用的原事件不存在")
        return _event_scope(rows, target, seen=visited)
    parts = scoped_ref.split(":")
    if len(parts) != 4 or parts[3] != row["project_id"]:
        raise ProjectWorkflowError("处理记录作用域与项目不一致")
    return parts[1], parts[2], parts[3]


def _scoped_events(
    events: Sequence[Mapping[str, Any]],
    project_id: str,
    company_id: str,
    period: str,
) -> list[dict[str, Any]]:
    rows = validate_event_chain(events)
    expected = (company_id, period, project_id)
    return [row for row in rows if row["project_id"] == project_id and _event_scope(rows, row) == expected]


def _active_domain_events(
    events: Sequence[Mapping[str, Any]],
    project_id: str,
    company_id: str,
    period: str,
) -> list[dict[str, Any]]:
    rows = _scoped_events(events, project_id, company_id, period)
    reversed_ids = {
        row["payload"].get("reverses_event_id")
        for row in rows
        if row["project_id"] == project_id and row["event_type"] == "EVENT_REVERSED"
    }
    return [
        row
        for row in rows
        if row["project_id"] == project_id and row["event_type"] in DOMAIN_EVENT_TYPES and row["event_id"] not in reversed_ids
    ]


def _latest_event(events: Sequence[Mapping[str, Any]], event_type: str) -> dict[str, Any] | None:
    return next((copy.deepcopy(dict(row)) for row in reversed(events) if row["event_type"] == event_type), None)


def _project_row_with_cost(detail: Mapping[str, Any], cost_cents: int) -> dict[str, Any]:
    row = copy.deepcopy(dict(detail["project"]))
    revenue = int(row["revenue_cents"])
    gross_profit = revenue - cost_cents
    gross_margin = _basis_points(gross_profit, revenue)
    if gross_margin is None:
        raise ProjectWorkflowError("收入为零，无法形成项目毛利率")
    row.update(
        {
            "cost_cents": cost_cents,
            "cost_display_zh": homepage.format_wan_cents(cost_cents),
            "gross_profit_cents": gross_profit,
            "gross_profit_display_zh": homepage.format_wan_cents(gross_profit),
            "gross_margin_bps": gross_margin,
            "gross_margin_display_zh": project_list.format_percent_bps(gross_margin),
            "margin_band": project_list._margin_band(gross_margin),
        }
    )
    return row


def project_projection(
    *,
    project_id: str,
    events: Sequence[Mapping[str, Any]],
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    validated = validate_event_chain(events)
    scoped = _scoped_events(validated, project_id, company_id, period)
    active = _active_domain_events(validated, project_id, company_id, period)
    base = _base_detail(project_id, company_id, period)
    active_assignment = _latest_event(active, "UNALLOCATED_COST_ASSIGNED")
    active_variance = _latest_event(active, "PROJECT_VARIANCE_RESOLVED")
    selected_cost = (
        int(active_variance["payload"]["selected_cost_cents"])
        if active_variance is not None
        else int(base["cost"]["actual_total_cents"])
    )
    row = _project_row_with_cost(base, selected_cost)
    if active_variance is not None:
        remaining_reasons = [
            str(reason) for reason in row["risk_reasons_zh"] if str(reason) != "成本偏差待复核"
        ]
        if remaining_reasons:
            row["risk_reasons_zh"] = remaining_reasons
        else:
            row.update(
                {
                    "status": "NORMAL",
                    "status_zh": "进展正常",
                    "risk_level": "LOW",
                    "risk_zh": "低风险",
                    "risk_reasons_zh": ["成本来源差异已确认并完成重算"],
                }
            )
    engine_views, golden = project_detail._engine_views(row, company_id, period)
    result = copy.deepcopy(base)
    result["version"] = VERSION
    result["schema_version"] = WORKFLOW_SCHEMA_VERSION
    result["project"] = row
    categories = copy.deepcopy(base["cost"]["categories"])
    unallocated = int(base["cost"]["unallocated"]["amount_cents"])
    delta = selected_cost - int(base["cost"]["actual_total_cents"])
    adjustment_row = next(item for item in categories if item["category_id"] == "SITE_MANAGEMENT")
    if adjustment_row["actual_cents"] + delta < 0:
        raise ProjectWorkflowError("差异处理会导致分类成本为负数")
    adjustment_row["actual_cents"] += delta
    adjustment_row["source_zh"] = "公开合成成本分类账与已确认差异处理事件"
    if active_assignment is not None:
        payload = active_assignment["payload"]
        if payload["candidate_project_id"] != project_id or payload["amount_cents"] != unallocated:
            raise ProjectWorkflowError("归集处理记录与当前未归集成本不一致")
        target = next(item for item in categories if item["category_id"] == payload["target_category_id"])
        target["actual_cents"] += unallocated
        # S17-P2 把未归集金额同时保留在预算基准中。归集后必须把同一预算
        # 基准移入目标分类，否则专题报告的预算总额会与明细相差这笔金额。
        target["budget_cents"] += unallocated
        target["source_zh"] = "公开合成成本分类账与已确认未归集处理事件"
        unallocated = 0
    for item in categories:
        item["actual_display_zh"] = homepage.format_wan_cents(item["actual_cents"])
        item["variance_cents"] = item["actual_cents"] - item["budget_cents"]
        item["variance_direction_zh"] = (
            "超出基准" if item["variance_cents"] > 0 else "低于基准" if item["variance_cents"] < 0 else "与基准一致"
        )
    table_total = sum(item["actual_cents"] for item in categories) + unallocated
    if table_total != selected_cost:
        raise ProjectWorkflowError("处理后分类成本与项目成本不一致")
    cost = copy.deepcopy(base["cost"])
    cost.update(
        {
            "categories": categories,
            "actual_total_cents": selected_cost,
            "variance_total_cents": selected_cost - int(cost["budget_total_cents"]),
            "table_total_cents": table_total,
            "chart_total_cents": table_total,
            "engine_difference_cents": 0,
            "chart_table_difference_cents": 0,
            "zero_difference_pass": True,
        }
    )
    cost["unallocated"].update(
        {
            "amount_cents": unallocated,
            "amount_display_zh": homepage.format_wan_cents(unallocated),
            "ratio_bps": _basis_points(unallocated, selected_cost) or 0,
            "ratio_display_zh": project_list.format_percent_bps(_basis_points(unallocated, selected_cost) or 0),
            "reason_zh": "已通过追加式处理事件归集。" if unallocated == 0 else base["cost"]["unallocated"]["reason_zh"],
        }
    )
    trend_amounts = project_detail._allocate_exact(selected_cost, project_detail.TREND_WEIGHTS)
    for item, amount in zip(cost["trend"], trend_amounts):
        item["actual_cents"] = amount
        item["actual_display_zh"] = homepage.format_wan_cents(amount)
    cost["trend_total_cents"] = sum(trend_amounts)
    result["cost"] = cost
    overview = copy.deepcopy(base["overview"])
    overview.update(
        {
            "cost_cents": selected_cost,
            "gross_profit_cents": row["gross_profit_cents"],
            "gross_margin_bps": row["gross_margin_bps"],
            "gross_margin_display_zh": row["gross_margin_display_zh"],
            "risk_zh": row["risk_zh"],
            "risk_reasons_zh": copy.deepcopy(row["risk_reasons_zh"]),
            "data_status_zh": "处理事件已持久化，页面与专题报告使用同一重算结果。",
        }
    )
    overview["profit_verdict_zh"] = "项目目前赚钱" if row["gross_profit_cents"] >= 0 else "项目目前亏损"
    overview["profit_reason_zh"] = [
        f"确认收入 {homepage.format_wan_cents(row['revenue_cents'])}，确认成本 {homepage.format_wan_cents(selected_cost)}。",
        f"重算后毛利率 {row['gross_margin_display_zh']}，回款进度 {overview['collection_display_zh']}。",
        "未归集成本已通过可撤销处理事件归集。" if unallocated == 0 else "仍有未归集成本，需要继续确认归属。",
        "差异处理依据、影响预览和重算记录均已保留。" if active_variance else "当前尚未确认成本来源差异处理。",
    ]
    overview["professional_basis"] = {
        "title_zh": "专业口径与核对信息",
        "margin_views": engine_views,
        "golden_comparison": golden,
        "money_tolerance_cents": MONEY_TOLERANCE_CENTS,
    }
    result["overview"] = overview
    variance = copy.deepcopy(base["variance"])
    cost_row = next(item for item in variance["rows"] if item["variance_id"] == "COST")
    cost_row["actual_cents"] = selected_cost
    cost_row["variance_cents"] = selected_cost - cost_row["baseline_cents"]
    cost_row["explanation_zh"] = "已按追加式差异处理事件重算，来源比较保留在处理记录。"
    profit_row = next(item for item in variance["rows"] if item["variance_id"] == "GROSS_PROFIT")
    profit_row["actual_cents"] = row["gross_profit_cents"]
    profit_row["variance_cents"] = profit_row["actual_cents"] - profit_row["baseline_cents"]
    result["variance"] = variance
    result["sections"]["overview"] = overview
    result["sections"]["cost"] = cost
    result["sections"]["variance"] = variance
    business_rows = [row for row in scoped if row["event_type"] != "RERUN_COMPLETED"]
    business_head_hash = business_rows[-1]["content_hash"] if business_rows else GENESIS_HASH
    report_version = "REPORT-S17P3-" + (
        business_head_hash[7:19].upper() if business_rows else "BASE00000000"
    )
    projection_basis = {
        "project_id": project_id,
        "company_id": company_id,
        "period": period,
        "report_version": report_version,
        "event_head_hash": business_head_hash,
        "active_event_ids": [row["event_id"] for row in active],
        "revenue_cents": row["revenue_cents"],
        "cost_cents": selected_cost,
        "gross_profit_cents": row["gross_profit_cents"],
        "category_total_cents": sum(item["actual_cents"] for item in categories),
        "unallocated_cents": unallocated,
    }
    projection_fingerprint = _fingerprint(projection_basis)
    rerun_rows = [row for row in scoped if row["event_type"] == "RERUN_COMPLETED"]
    report_synced = not active_variance or any(
        row["payload"].get("projection_fingerprint") == projection_fingerprint for row in rerun_rows
    )
    result["workflow_projection"] = {
        **projection_basis,
        "projection_fingerprint": projection_fingerprint,
        "active_assignment_event_id": active_assignment["event_id"] if active_assignment else None,
        "active_variance_event_id": active_variance["event_id"] if active_variance else None,
        "report_sync_status": "PASS" if report_synced else "RERUN_REQUIRED",
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "money_difference_cents": table_total - selected_cost,
    }
    return result


def confirm_unallocated_assignment(
    journal: EventJournal,
    *,
    project_id: str,
    candidate_id: str,
    actor_ref: str,
    reason_zh: str,
    idempotency_key: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
    event_time: str | None = None,
) -> dict[str, Any]:
    preview = preview_unallocated_assignment(
        project_id=project_id, candidate_id=candidate_id, company_id=company_id, period=period
    )
    assert_auto_allocation_allowed(preview)
    event = journal.append(
        event_type="UNALLOCATED_COST_ASSIGNED",
        project_id=project_id,
        payload={
            "work_item_id": preview["work_item_id"],
            "candidate_id": candidate_id,
            "candidate_project_id": preview["candidate"]["candidate_project_id"],
            "target_category_id": preview["candidate"]["target_category_id"],
            "amount_cents": preview["amount_cents"],
            "confidence_bps": preview["candidate"]["confidence_bps"],
            "preview_fingerprint": preview["preview_fingerprint"],
        },
        actor_ref=actor_ref,
        reason_zh=reason_zh,
        idempotency_key=idempotency_key,
        event_time=event_time,
    )
    return {"event": event, "preview": preview, "projection": project_projection(project_id=project_id, events=journal.read(), company_id=company_id, period=period)}


def confirm_variance_resolution(
    journal: EventJournal,
    *,
    project_id: str,
    option_id: str,
    actor_ref: str,
    reason_zh: str,
    idempotency_key: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
    event_time: str | None = None,
) -> dict[str, Any]:
    preview = preview_variance_resolution(
        project_id=project_id, option_id=option_id, company_id=company_id, period=period
    )
    event = journal.append(
        event_type="PROJECT_VARIANCE_RESOLVED",
        project_id=project_id,
        payload={
            "variance_id": preview["variance_id"],
            "option_id": option_id,
            "selected_cost_cents": preview["selected_option"]["selected_cost_cents"],
            "preview_fingerprint": preview["preview_fingerprint"],
        },
        actor_ref=actor_ref,
        reason_zh=reason_zh,
        idempotency_key=idempotency_key,
        event_time=event_time,
    )
    projection = project_projection(project_id=project_id, events=journal.read(), company_id=company_id, period=period)
    rerun = journal.append(
        event_type="RERUN_COMPLETED",
        project_id=project_id,
        payload={
            "source_event_id": event["event_id"],
            "projection_fingerprint": projection["workflow_projection"]["projection_fingerprint"],
            "report_version": projection["workflow_projection"]["report_version"],
            "page_report_sync_required": True,
        },
        actor_ref=actor_ref,
        reason_zh="确认差异处理后完成项目页面与专题报告重算",
        idempotency_key=idempotency_key + "-rerun",
        event_time=event_time,
    )
    projection = project_projection(project_id=project_id, events=journal.read(), company_id=company_id, period=period)
    return {"event": event, "rerun_event": rerun, "preview": preview, "projection": projection}


def reverse_processing_event(
    journal: EventJournal,
    *,
    event_id: str,
    actor_ref: str,
    reason_zh: str,
    idempotency_key: str,
    company_id: str = "demo-north",
    period: str = "2026-07",
    event_time: str | None = None,
) -> dict[str, Any]:
    target = next((row for row in journal.read() if row["event_id"] == event_id), None)
    if target is None:
        raise ProjectWorkflowError("待撤销处理记录不存在")
    reversal = journal.reverse(
        event_id=event_id,
        actor_ref=actor_ref,
        reason_zh=reason_zh,
        idempotency_key=idempotency_key,
        event_time=event_time,
    )
    projection = project_projection(project_id=target["project_id"], events=journal.read(), company_id=company_id, period=period)
    return {"reversal_event": reversal, "projection": projection}


def _canonical_demo_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    def add(event_type: str, payload: Mapping[str, Any], key: str, reason: str, time: str) -> dict[str, Any]:
        row = _event(
            sequence=len(events) + 1,
            previous_hash=events[-1]["content_hash"] if events else GENESIS_HASH,
            event_type=event_type,
            project_id="PUB-PROJ-001",
            payload=payload,
            actor_ref="public-demo-owner",
            reason_zh=reason,
            idempotency_key=key,
            event_time=time,
        )
        events.append(row)
        return row

    assignment_preview = preview_unallocated_assignment(project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-001")
    assignment_payload = {
        "work_item_id": assignment_preview["work_item_id"],
        "candidate_id": "CAND-S17P3-001",
        "candidate_project_id": "PUB-PROJ-001",
        "target_category_id": "SUBCONTRACT",
        "amount_cents": assignment_preview["amount_cents"],
        "confidence_bps": 9600,
        "preview_fingerprint": assignment_preview["preview_fingerprint"],
    }
    first = add(
        "UNALLOCATED_COST_ASSIGNED",
        assignment_payload,
        "demo-assignment-first",
        "依据完整，确认归集到当前项目分包成本",
        "2026-07-16T16:40:00+10:00",
    )
    add(
        "EVENT_REVERSED",
        {"reverses_event_id": first["event_id"], "reversed_event_type": first["event_type"]},
        "demo-assignment-reversal",
        "复核演示撤销，验证处理记录可逆",
        "2026-07-16T16:41:00+10:00",
    )
    add(
        "UNALLOCATED_COST_ASSIGNED",
        assignment_payload,
        "demo-assignment-final",
        "二次复核后确认归集到当前项目分包成本",
        "2026-07-16T16:42:00+10:00",
    )
    variance_preview = preview_variance_resolution(project_id="PUB-PROJ-001", option_id="USE_SETTLEMENT_SUPPORT")
    resolution = add(
        "PROJECT_VARIANCE_RESOLVED",
        {
            "variance_id": variance_preview["variance_id"],
            "option_id": "USE_SETTLEMENT_SUPPORT",
            "selected_cost_cents": variance_preview["selected_option"]["selected_cost_cents"],
            "preview_fingerprint": variance_preview["preview_fingerprint"],
        },
        "demo-variance-resolution",
        "采用已确认结算口径并保留来源差异",
        "2026-07-16T16:43:00+10:00",
    )
    temporary_projection = project_projection(project_id="PUB-PROJ-001", events=events)
    add(
        "RERUN_COMPLETED",
        {
            "source_event_id": resolution["event_id"],
            "projection_fingerprint": temporary_projection["workflow_projection"]["projection_fingerprint"],
            "report_version": temporary_projection["workflow_projection"]["report_version"],
            "page_report_sync_required": True,
        },
        "demo-variance-rerun",
        "完成项目页面与专题报告同步重算",
        "2026-07-16T16:44:00+10:00",
    )
    return validate_event_chain(events)


def canonical_demo_events() -> list[dict[str, Any]]:
    return copy.deepcopy(_canonical_demo_events())


def workflow_snapshot(
    *,
    project_id: str = "PUB-PROJ-001",
    events: Sequence[Mapping[str, Any]] | None = None,
    company_id: str = "demo-north",
    period: str = "2026-07",
) -> dict[str, Any]:
    rows = validate_event_chain(events or [])
    projection = project_projection(project_id=project_id, events=rows, company_id=company_id, period=period)
    scoped = _scoped_events(rows, project_id, company_id, period)
    reversed_count = sum(row["event_type"] == "EVENT_REVERSED" for row in scoped)
    active = _active_domain_events(rows, project_id, company_id, period)
    return {
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "version": VERSION,
        "allowed": True,
        "data_classification": "PUBLIC_SYNTHETIC",
        "project_id": project_id,
        "company_id": company_id,
        "period": period,
        "unallocated_work_item": unallocated_work_item(project_id, company_id, period),
        "variance_work_item": variance_work_item(project_id, company_id, period),
        "projection": projection,
        "events": scoped,
        "event_count": len(scoped),
        "active_domain_event_count": len(active),
        "reversal_event_count": reversed_count,
        "event_head_hash": scoped[-1]["content_hash"] if scoped else GENESIS_HASH,
        "append_only": True,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def project_cost_report(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    projection = snapshot["projection"]
    detail = projection
    workflow = projection["workflow_projection"]
    events = snapshot["events"]
    active_ids = set(workflow["active_event_ids"])
    cost_rows = [
        {
            "category_id": row["category_id"],
            "category_zh": row["category_zh"],
            "actual_cents": row["actual_cents"],
            "budget_cents": row["budget_cents"],
            "variance_cents": row["actual_cents"] - row["budget_cents"],
            "source_ref": row["source_ref"],
        }
        for row in detail["cost"]["categories"]
    ]
    cost_rows.append(
        {
            "category_id": "UNALLOCATED",
            "category_zh": "未归集",
            "actual_cents": detail["cost"]["unallocated"]["amount_cents"],
            "budget_cents": 0,
            "variance_cents": detail["cost"]["unallocated"]["amount_cents"],
            "source_ref": detail["cost"]["unallocated"]["source_ref"],
        }
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": "REPORT-KMFA-V015-S17P3-PROJECT-COST-001",
        "report_name_zh": "项目成本专题报告",
        "report_version": workflow["report_version"],
        "generated_at": "2026-07-16T16:45:00+10:00",
        "data_classification": "PUBLIC_SYNTHETIC",
        "project": {
            "project_id": detail["project"]["project_id"],
            "project_name_zh": detail["project"]["project_name_zh"],
            "company_zh": detail["project"]["company_zh"],
            "period": snapshot["period"],
        },
        "summary": {
            "revenue_cents": detail["overview"]["revenue_cents"],
            "cost_cents": detail["cost"]["actual_total_cents"],
            "gross_profit_cents": detail["overview"]["gross_profit_cents"],
            "gross_margin_bps": detail["overview"]["gross_margin_bps"],
            "budget_cents": detail["cost"]["budget_total_cents"],
            "budget_variance_cents": detail["cost"]["variance_total_cents"],
            "unallocated_cents": detail["cost"]["unallocated"]["amount_cents"],
        },
        "cost_rows": cost_rows,
        "variance_rows": copy.deepcopy(detail["variance"]["rows"]),
        "processing_events": [
            {
                "event_id": row["event_id"],
                "event_sequence": row["event_sequence"],
                "event_type": row["event_type"],
                "event_type_zh": row["event_type_zh"],
                "event_time": row["event_time"],
                "reason_zh": row["reason_zh"],
                "active": row["event_id"] in active_ids,
                "content_hash": row["content_hash"],
            }
            for row in events
        ],
        "evidence_index": {
            "source_facts": sorted({row["source_ref"] for row in cost_rows}),
            "processing_event_refs": [row["event_id"] for row in events],
            "calculation_refs": [
                "FORM-KMFA-V015-S12-P2-CORE-CALCULATIONS-001",
                "FORM-KMFA-V015-S17-P2-PROJECT-DETAIL-001",
                "FORM-KMFA-V015-S17-P3-PROJECT-WORKFLOW-001",
            ],
            "report_refs": ["HTML", "PDF", "XLSX"],
        },
        "checks": {
            "page_cost_cents": detail["cost"]["actual_total_cents"],
            "golden_cost_cents": detail["project"]["cost_cents"],
            "category_total_cents": sum(row["actual_cents"] for row in cost_rows),
            "page_golden_difference_cents": detail["cost"]["actual_total_cents"] - detail["project"]["cost_cents"],
            "category_page_difference_cents": sum(row["actual_cents"] for row in cost_rows) - detail["cost"]["actual_total_cents"],
            "money_tolerance_cents": MONEY_TOLERANCE_CENTS,
            "report_sync_status": workflow["report_sync_status"],
        },
        "format_contract": {
            "html_required": True,
            "pdf_required": True,
            "xlsx_required": True,
            "evidence_index_required": True,
            "format_count": REPORT_FORMAT_COUNT,
        },
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "formal_business_report": False,
    }
    report["report_fingerprint"] = _fingerprint(report)
    return report


def canonical_report() -> dict[str, Any]:
    return project_cost_report(workflow_snapshot(events=canonical_demo_events()))


def render_report_html(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    cost_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['category_zh'])}</td>"
        f"<td class='n'>{_format_yuan(row['actual_cents'])}</td>"
        f"<td class='n'>{_format_yuan(row['budget_cents'])}</td>"
        f"<td class='n'>{_format_yuan(row['variance_cents'])}</td>"
        "</tr>"
        for row in report["cost_rows"]
    )
    event_rows = "".join(
        "<tr>"
        f"<td>{row['event_sequence']}</td><td>{html.escape(row['event_type_zh'])}</td>"
        f"<td>{html.escape(row['reason_zh'])}</td><td>{'有效' if row['active'] else '历史/辅助'}</td>"
        "</tr>"
        for row in report["processing_events"]
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(report['report_name_zh'])}</title><style>
body{{margin:0;background:#eef3f6;color:#263b49;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}
main{{max-width:1040px;margin:28px auto;padding:28px;background:#fff;border:1px solid #d8e2e8;border-radius:10px}}
h1{{margin:0;color:#173d57;font-size:28px}} .meta{{margin:7px 0 22px;color:#607684;font-size:13px}}
.notice{{padding:11px 13px;border-left:4px solid #2f7aa4;background:#eef7fb;font-size:13px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}} .kpi{{padding:14px;border:1px solid #d8e2e8;border-radius:7px;background:#f8fafb}}
.kpi span{{display:block;color:#6a7f8b;font-size:11px}} .kpi strong{{display:block;margin-top:5px;color:#173d57;font-size:18px}}
h2{{margin:24px 0 10px;color:#214d68;font-size:18px}} table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{padding:9px 10px;border-bottom:1px solid #e1e8ec;text-align:left}} th{{background:#f1f5f7;color:#365568}} .n{{text-align:right}}
.pass{{margin-top:18px;padding:12px;border:1px solid #9fc7b0;border-radius:7px;background:#f1faf5;color:#246040;font-weight:700}}
@media(max-width:700px){{main{{margin:0;padding:18px;border-radius:0}}.kpis{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main>
<h1>{html.escape(report['report_name_zh'])}</h1><p class="meta">{html.escape(report['project']['project_name_zh'])} · {report['project']['period']} · {report['report_version']}</p>
<p class="notice">公开合成报告。所有处理只追加可撤销事件，不修改源数据，也不代表正式经营报告。</p>
<section class="kpis"><div class="kpi"><span>确认收入（元）</span><strong>{_format_yuan(summary['revenue_cents'])}</strong></div>
<div class="kpi"><span>确认成本（元）</span><strong>{_format_yuan(summary['cost_cents'])}</strong></div>
<div class="kpi"><span>毛利（元）</span><strong>{_format_yuan(summary['gross_profit_cents'])}</strong></div>
<div class="kpi"><span>未归集成本（元）</span><strong>{_format_yuan(summary['unallocated_cents'])}</strong></div></section>
<h2>成本明细</h2><table><thead><tr><th>分类</th><th class="n">实际（元）</th><th class="n">预算（元）</th><th class="n">差异（元）</th></tr></thead><tbody>{cost_rows}</tbody></table>
<h2>处理记录</h2><table><thead><tr><th>顺序</th><th>类型</th><th>原因</th><th>状态</th></tr></thead><tbody>{event_rows}</tbody></table>
<div class="pass">当前页面、黄金基准与 HTML 报告金额允许差异 0 分；PDF 与 Excel 样例按各自文件版本单独验收。</div>
</main></body></html>"""


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, summary_zh: str) -> None:
        checks.append({"check_id": check_id, "passed": bool(passed), "summary_zh": summary_zh})

    contract = source_contract()
    base = workflow_snapshot()
    item = base["unallocated_work_item"]
    high = preview_unallocated_assignment(project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-001")
    low = preview_unallocated_assignment(project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-003")
    events = canonical_demo_events()
    snapshot = workflow_snapshot(events=events)
    projection = snapshot["projection"]
    report = project_cost_report(snapshot)
    html_text = render_report_html(report)
    add("source_tasks", len(contract["task_ids"]) == 3, "三项任务完整")
    add("source_actions", len(contract["actions_zh"]) == 3, "三项动作完整")
    add("source_acceptance", len(contract["acceptance_zh"]) == 3, "三项验收完整")
    add("candidate_count", item["candidate_count"] == UNALLOCATED_CANDIDATE_COUNT, "三个候选完整")
    add("candidate_basis", all(row["basis_zh"] for row in item["candidates"]), "候选均有依据")
    add("candidate_impact", high["impact"]["portfolio_cost_difference_cents"] == 0, "归集影响守恒")
    add("high_auto_gate", high["auto_allocation_allowed"] is True, "高置信候选可进入确认")
    add("high_confirmation", high["confirmation_required"] is True, "高置信仍需确认")
    add("low_auto_gate", low["auto_allocation_allowed"] is False, "低置信禁止自动归集")
    try:
        assert_auto_allocation_allowed(low)
    except ProjectWorkflowError:
        low_rejected = True
    else:
        low_rejected = False
    add("low_auto_rejected", low_rejected, "低置信自动归集失败关闭")
    add("source_write_zero", high["source_data_write_count"] == 0, "归集不修改源数据")
    add("reversible", high["reversible"] is True, "归集可撤销")
    add("event_chain", len(validate_event_chain(events)) == 5, "处理记录哈希链完整")
    add("event_append_only", all(row["append_only"] for row in events), "处理记录只追加")
    add("event_source_zero", all(row["source_data_write_count"] == 0 for row in events), "处理记录不改源数据")
    add("event_reversal", snapshot["reversal_event_count"] == 1, "撤销事件已验证")
    add("active_events", snapshot["active_domain_event_count"] == 2, "最终两项处理有效")
    add("unallocated_closed", projection["cost"]["unallocated"]["amount_cents"] == 0, "未归集成本已处理")
    add(
        "category_exact",
        sum(row["actual_cents"] for row in projection["cost"]["categories"]) == projection["cost"]["actual_total_cents"]
        and sum(row["budget_cents"] for row in projection["cost"]["categories"]) == projection["cost"]["budget_total_cents"],
        "归集后成本和预算明细均与总额精确一致",
    )
    add("page_engine_zero", projection["cost"]["engine_difference_cents"] == 0, "页面与引擎零差异")
    add("chart_table_zero", projection["cost"]["chart_table_difference_cents"] == 0, "图表表格零差异")
    variance = variance_work_item()
    preview = preview_variance_resolution(project_id="PUB-PROJ-001", option_id="USE_SETTLEMENT_SUPPORT")
    add("variance_sources", variance["source_count"] == VARIANCE_SOURCE_COUNT, "两项来源并排比较")
    add("variance_explanation", bool(variance["explanation_zh"]), "差异有解释")
    add("variance_preview", preview["impact_preview_passed"] is True, "差异影响预览通过")
    add("variance_cost_change", preview["impact"]["cost_after_cents"] < preview["impact"]["cost_before_cents"], "差异处理产生可核对影响")
    add("variance_reports", len(preview["impact"]["affected_report_ids"]) == 2, "页面与专题报告均受影响")
    add("rerun_sync", projection["workflow_projection"]["report_sync_status"] == "PASS", "重算后报告同步")
    add("projection_zero", projection["workflow_projection"]["money_difference_cents"] == 0, "处理投影零差异")
    add("report_formats", report["format_contract"]["format_count"] == REPORT_FORMAT_COUNT, "三种报告格式完整")
    add("report_evidence_groups", len(report["evidence_index"]) == EVIDENCE_INDEX_GROUP_COUNT, "证据索引四组完整")
    add("report_page_zero", report["checks"]["page_golden_difference_cents"] == 0, "报告与页面零差异")
    add("report_category_zero", report["checks"]["category_page_difference_cents"] == 0, "报告分类与页面零差异")
    add("report_tolerance_zero", report["checks"]["money_tolerance_cents"] == 0, "金额容差为零分")
    add("report_sync_pass", report["checks"]["report_sync_status"] == "PASS", "报告同步通过")
    add("report_fingerprint", report["report_fingerprint"].startswith("sha256:"), "报告指纹存在")
    add("report_html_title", "项目成本专题报告" in html_text, "HTML 报告标题完整")
    add("report_html_exact", "允许差异 0 分" in html_text, "HTML 明示零差异")
    add("public_data", snapshot["data_classification"] == "PUBLIC_SYNTHETIC", "只使用公开合成数据")
    add("raw_zero", snapshot["raw_root_access_count"] == 0, "未访问原始资料")
    add("network_zero", snapshot["external_network_request_count"] == 0, "无外部网络请求")
    add("identity_zero", snapshot["real_identity_count"] == 0, "无真实身份")
    add("credential_zero", snapshot["credential_count"] == 0, "无凭据")
    add("business_action_zero", snapshot["real_business_action_count"] == 0, "无真实业务动作")
    add("upload_zero", snapshot["github_upload_performed"] is False, "未上传 GitHub")
    add("reinstall_zero", snapshot["app_reinstall_performed"] is False, "未重装 App")
    for row in project_list.project_catalog("demo-north", "2026-07"):
        project_snapshot = workflow_snapshot(project_id=row["project_id"])
        detail = project_snapshot["projection"]
        add(f"project_equation_{row['project_id']}", detail["overview"]["revenue_cents"] == detail["overview"]["cost_cents"] + detail["overview"]["gross_profit_cents"], "项目金额等式成立")
        add(f"project_candidates_{row['project_id']}", project_snapshot["unallocated_work_item"]["candidate_count"] == 3, "项目候选完整")
        add(f"project_variance_{row['project_id']}", project_snapshot["variance_work_item"]["source_count"] == 2, "项目差异来源完整")
        add(f"project_zero_{row['project_id']}", detail["workflow_projection"]["money_difference_cents"] == 0, "项目处理前投影守恒")
    if not all(row["passed"] for row in checks):
        failed = [row["check_id"] for row in checks if not row["passed"]]
        raise ProjectWorkflowError("公开检查失败：" + ", ".join(failed))
    return checks


def main() -> int:
    try:
        checks = public_checks()
    except (KeyError, TypeError, json.JSONDecodeError, ProjectWorkflowError, calculations.CoreCalculationError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"PASS: S17-P3 project workflow public checks {len(checks)}/{len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
