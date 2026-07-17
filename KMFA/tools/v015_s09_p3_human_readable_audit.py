#!/usr/bin/env python3
"""KMFA v1.5 S09-P3 human-readable difference and audit kernel.

This module turns the S09-P1/P2 rule contracts into plain-Chinese review
material, projects only decision-relevant differences into a management
summary, and enforces an append-only six-step difference-closure history.
It works exclusively with public-safe synthetic evidence and never reads or
writes the private raw-data inbox.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s09_p1_scope_rule_modeling as s09p1
from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as s09p2


RUN_PHASE_ID = "V015_S09_P3_HUMAN_READABLE_AUDIT"
ROADMAP_PHASE_ID = "S09-P3"
TASK_ID = "KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT"
VERSION = "1.5.0-dev-s09p3"

RULE_MANUAL_SCHEMA = "kmfa.v015.s09p3.human_rule_manual.v1"
REPORT_SPEC_SCHEMA = "kmfa.v015.s09p3.report_difference_display_spec.v1"
CLOSURE_SNAPSHOT_SCHEMA = "kmfa.v015.s09p3.difference_closure_snapshot.v1"
CLOSURE_EVENT_SCHEMA = "kmfa.v015.s09p3.difference_closure_event.v1"

REQUIRED_AUDIENCES = ("FINANCE_REVIEWER", "OWNER")
REPORT_ITEM_FIELDS = (
    "title_zh",
    "what_changed_zh",
    "business_impact_zh",
    "current_status_zh",
    "recommended_action_zh",
)
FORBIDDEN_REPORT_TERMS = (
    "schema_version",
    "debug",
    "traceback",
    "stack trace",
    "exception",
    "sql",
    "json",
    "sha256",
    "source_ref",
    "rule_ref",
    "event_ref",
    "rerun_chain",
    "api",
)
CLOSURE_STEPS = (
    "DIFFERENCE_DISCOVERED",
    "HANDLING_PROPOSED",
    "IMPACT_PREVIEWED",
    "HUMAN_CONFIRMED",
    "RECALCULATED",
    "REPORT_UPDATED",
)
CLOSURE_STATUS_ZH = {
    "DIFFERENCE_DISCOVERED": "已发现，等待提出处理方案",
    "HANDLING_PROPOSED": "已有处理方案，等待影响预览",
    "IMPACT_PREVIEWED": "已展示处理影响，等待人工确认",
    "HUMAN_CONFIRMED": "已确认，等待重新计算",
    "RECALCULATED": "已重新计算，等待更新经营摘要",
    "REPORT_UPDATED": "已闭环并更新经营摘要",
}
REQUIRED_EVENT_FIELDS = {
    "DIFFERENCE_DISCOVERED": ("difference_summary_zh",),
    "HANDLING_PROPOSED": ("handling_zh",),
    "IMPACT_PREVIEWED": ("impact_before_zh", "impact_after_zh"),
    "HUMAN_CONFIRMED": ("decision_zh",),
    "RECALCULATED": ("recalculation_status", "affected_output_labels_zh"),
    "REPORT_UPDATED": ("report_version", "report_update_summary_zh"),
}


class HumanReadableAuditError(ValueError):
    """Fail-closed S09-P3 input, display, or workflow error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise HumanReadableAuditError("MAPPING_REQUIRED", f"{field} 必须是对象。")
    return copy.deepcopy(dict(value))


def _sequence(value: Any, field: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise HumanReadableAuditError("SEQUENCE_REQUIRED", f"{field} 必须是列表。")
    return copy.deepcopy(list(value))


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanReadableAuditError("TEXT_REQUIRED", f"{field} 不能为空。")
    return value.strip()


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise HumanReadableAuditError("BOOLEAN_REQUIRED", f"{field} 必须是布尔值。")
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _plain_rule_text() -> dict[str, dict[str, str]]:
    return {
        "ACCOUNTING_REVENUE": {
            "name_zh": "账面收入转为经营收入",
            "what_zh": "把已登记的账面收入按同一金额带入经营分析视图。",
            "impact_zh": "影响项目收入、毛利和经营进度判断。",
            "action_zh": "核对来源、期间和已审批调整；差一分钱就停止。",
            "owner_summary_zh": "经营收入来自同一套账，不另造第二本账。",
        },
        "ACCOUNTING_COST": {
            "name_zh": "账面成本转为经营成本",
            "what_zh": "把已登记的账面成本按同一金额带入经营分析视图。",
            "impact_zh": "影响项目成本、毛利和亏损风险判断。",
            "action_zh": "核对项目归属、期间和已审批调整；无法守恒就停止。",
            "owner_summary_zh": "经营成本可回到原账核对，不能靠手工补平。",
        },
        "UNBILLED": {
            "what_zh": "业务已经履行，但发票尚未开出。",
            "impact_zh": "可能影响收入进度、开票计划和税务时点判断。",
            "action_zh": "核对合同或交付证据和所属期间，证据不足就等待确认。",
            "owner_summary_zh": "收入进度与开票进度不同步，需要说明原因和预计处理时间。",
        },
        "UNSETTLED": {
            "what_zh": "合同或项目进度与正式结算确认不同步。",
            "impact_zh": "可能影响项目收入、成本和毛利的可靠程度。",
            "action_zh": "核对合同进度和结算状态，不凭经验自动补值。",
            "owner_summary_zh": "项目已推进但结算未完成，相关经营结论仍需谨慎。",
        },
        "UNALLOCATED": {
            "what_zh": "已有成本或资金记录，但缺少可靠的项目归属依据。",
            "impact_zh": "可能低估某个项目成本，或造成公司合计与项目合计不一致。",
            "action_zh": "补充来源记录和归集依据；没有依据时保持待确认。",
            "owner_summary_zh": "有支出尚未可靠归到项目，不能为了报表好看强行分摊。",
        },
        "ADVANCE_PAID": {
            "what_zh": "一方先行支付了本应由另一方承担或后续结算的款项。",
            "impact_zh": "影响项目资金占用、责任归属和后续追偿判断。",
            "action_zh": "核对付款证据、垫付主体和责任方，再决定如何展示。",
            "owner_summary_zh": "项目存在垫付，需要明确谁先付款、谁最终承担。",
        },
        "RETENTION": {
            "what_zh": "合同约定的一部分款项因质保要求暂未收付。",
            "impact_zh": "影响回款、付款和资金占用时间判断。",
            "action_zh": "核对质保条款、到期时间和当前收付状态。",
            "owner_summary_zh": "部分款项因质保暂缓，需关注到期和回收安排。",
        },
        "CROSS_PERIOD": {
            "what_zh": "业务发生时间、法定入账期间与经营观察期间不一致。",
            "impact_zh": "可能改变当期收入、成本、毛利和税务时点判断。",
            "action_zh": "同时说明法定期间和经营期间，任何处理都不能规避监管。",
            "owner_summary_zh": "差异来自期间归属，不能简单挪到更好看的月份。",
        },
        "TAX_RATE": {
            "what_zh": "相关资料使用的税率或税务口径不一致。",
            "impact_zh": "可能影响含税金额、税负和经营毛利比较。",
            "action_zh": "核对税务证据和适用规则版本，只作复核提示，不替代申报判断。",
            "owner_summary_zh": "税率口径存在差异，需要财务按有效依据确认。",
        },
        "BAD_DEBT": {
            "what_zh": "应收款可能无法按原计划收回。",
            "impact_zh": "影响现金回收、项目收益和风险准备判断。",
            "action_zh": "核对应收证据、回收评估和高风险审批，并保留撤销路径。",
            "owner_summary_zh": "部分应收存在回收风险，未经充分证据和审批不能直接核销。",
        },
    }


def build_human_rule_manual() -> dict[str, Any]:
    """Build complete plain-language coverage for all S09-P1/P2 rule types."""

    conversion = s09p2.validate_conversion_policy(s09p2.default_conversion_policy())
    differences = s09p1.validate_difference_dictionary(s09p1.default_difference_dictionary())
    plain = _plain_rule_text()
    rules: list[dict[str, Any]] = []
    for row in conversion["rules"]:
        source_kind = row["source_kind"]
        wording = plain[source_kind]
        rules.append(
            {
                "rule_key": f"TRANSFORM_{source_kind}",
                "rule_kind": "TRANSFORMATION",
                "source_contract_ref": row["rule_ref"],
                "name_zh": wording["name_zh"],
                "what_happened_zh": wording["what_zh"],
                "business_impact_zh": wording["impact_zh"],
                "review_action_zh": wording["action_zh"],
                "finance_review_question_zh": "来源、期间、金额和审批是否都能逐项核对？",
                "owner_summary_zh": wording["owner_summary_zh"],
            }
        )
    for row in differences["types"]:
        code = row["difference_type_code"]
        wording = plain[code]
        rules.append(
            {
                "rule_key": f"DIFFERENCE_{code}",
                "rule_kind": "DIFFERENCE",
                "source_contract_ref": differences["dictionary_ref"],
                "name_zh": row["label_zh"],
                "what_happened_zh": wording["what_zh"],
                "business_impact_zh": wording["impact_zh"],
                "review_action_zh": wording["action_zh"],
                "finance_review_question_zh": "证据、期间、责任和处理结果是否足以支持经营判断？",
                "owner_summary_zh": wording["owner_summary_zh"],
            }
        )
    return validate_human_rule_manual(
        {
            "schema_version": RULE_MANUAL_SCHEMA,
            "manual_ref": "HUMAN-RULE-MANUAL-S09P3-V1",
            "manual_version": "1.0.0",
            "source_policy_refs": [conversion["policy_ref"], differences["dictionary_ref"]],
            "audiences": [
                {
                    "audience": "FINANCE_REVIEWER",
                    "purpose_zh": "逐项核对来源、期间、金额、证据、审批和处理结果。",
                    "reading_level_zh": "财务复核语言",
                },
                {
                    "audience": "OWNER",
                    "purpose_zh": "只看对收入、成本、毛利、现金和风险判断的影响。",
                    "reading_level_zh": "经营决策摘要",
                },
            ],
            "rules": rules,
            "external_human_signoff_claimed": False,
            "formal_report_generation_included": False,
            "raw_root_access_count": 0,
        }
    )


def validate_human_rule_manual(manual: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(manual, "manual")
    if value.get("schema_version") != RULE_MANUAL_SCHEMA:
        raise HumanReadableAuditError("RULE_MANUAL_SCHEMA_INVALID", "规则手册版本不正确。")
    for field in ("manual_ref", "manual_version"):
        _text(value.get(field), field)
    audiences = [_mapping(row, "audiences[]") for row in _sequence(value.get("audiences"), "audiences")]
    audience_codes = []
    for row in audiences:
        code = _text(row.get("audience"), "audience")
        _text(row.get("purpose_zh"), "purpose_zh")
        _text(row.get("reading_level_zh"), "reading_level_zh")
        audience_codes.append(code)
    if tuple(audience_codes) != REQUIRED_AUDIENCES:
        raise HumanReadableAuditError("AUDIENCE_COVERAGE_INVALID", "规则手册必须同时覆盖财务复核与老板摘要。")
    rules = [_mapping(row, "rules[]") for row in _sequence(value.get("rules"), "rules")]
    required_keys = {
        "TRANSFORM_ACCOUNTING_REVENUE",
        "TRANSFORM_ACCOUNTING_COST",
        *(f"DIFFERENCE_{row['difference_type_code']}" for row in s09p1.default_difference_dictionary()["types"]),
    }
    keys: list[str] = []
    for row in rules:
        key = _text(row.get("rule_key"), "rule_key")
        if row.get("rule_kind") not in {"TRANSFORMATION", "DIFFERENCE"}:
            raise HumanReadableAuditError("RULE_KIND_INVALID", "规则类型未登记。")
        for field in (
            "source_contract_ref",
            "name_zh",
            "what_happened_zh",
            "business_impact_zh",
            "review_action_zh",
            "finance_review_question_zh",
            "owner_summary_zh",
        ):
            _text(row.get(field), f"rules.{field}")
        keys.append(key)
    if len(keys) != len(set(keys)) or set(keys) != required_keys:
        raise HumanReadableAuditError("RULE_COVERAGE_INVALID", "两类转换与八类差异必须完整且不重复。")
    if value.get("external_human_signoff_claimed") is not False:
        raise HumanReadableAuditError("UNSUPPORTED_SIGNOFF_CLAIM", "本阶段不得伪造外部人员签字。")
    if value.get("formal_report_generation_included") is not False or value.get("raw_root_access_count") != 0:
        raise HumanReadableAuditError("SCOPE_BOUNDARY_INVALID", "规则手册不得扩大到正式报告或 raw。")
    value["audiences"] = audiences
    value["rules"] = rules
    return value


def review_human_rule_manual(manual: Mapping[str, Any]) -> dict[str, Any]:
    """Record an evidence-based design review without claiming external signoff."""

    checked = validate_human_rule_manual(manual)
    transformations = [row for row in checked["rules"] if row["rule_kind"] == "TRANSFORMATION"]
    differences = [row for row in checked["rules"] if row["rule_kind"] == "DIFFERENCE"]
    unexplained = [
        row["rule_key"]
        for row in checked["rules"]
        if not all(row.get(field) for field in ("what_happened_zh", "business_impact_zh", "review_action_zh"))
    ]
    owner_missing = [row["rule_key"] for row in checked["rules"] if not row.get("owner_summary_zh")]
    return {
        "schema_version": "kmfa.v015.s09p3.rule_manual_review.v1",
        "review_type": "DESIGN_ACCEPTANCE_SELF_REVIEW",
        "external_human_signoff_claimed": False,
        "audience_count": len(checked["audiences"]),
        "transformation_rule_count": len(transformations),
        "difference_rule_count": len(differences),
        "total_rule_count": len(checked["rules"]),
        "unexplained_rule_count": len(unexplained),
        "owner_summary_missing_count": len(owner_missing),
        "finance_review_status": "PASS" if not unexplained else "FAIL",
        "owner_summary_status": "PASS" if not owner_missing else "FAIL",
        "review_status": "PASS" if not unexplained and not owner_missing else "FAIL",
        "review_notes_zh": [
            "财务视角可逐项检查来源、期间、金额、证据、审批和处理结果。",
            "老板视角只保留对收入、成本、毛利、现金和风险判断的摘要。",
            "该记录证明内容结构满足评审要求，不冒充真实业务人员签字。",
        ],
    }


def default_report_display_spec() -> dict[str, Any]:
    return {
        "schema_version": REPORT_SPEC_SCHEMA,
        "spec_ref": "REPORT-DIFFERENCE-DISPLAY-S09P3-V1",
        "spec_version": "1.0.0",
        "decision_relevant_only": True,
        "allowed_item_fields": list(REPORT_ITEM_FIELDS),
        "forbidden_internal_terms": list(FORBIDDEN_REPORT_TERMS),
        "internal_fields_excluded": [
            "difference_ref",
            "difference_type_code",
            "source_refs",
            "rule_refs",
            "stack_trace",
            "debug_payload",
        ],
        "title_must_use_business_language": True,
        "debug_information_allowed": False,
        "formal_report_generation_included": False,
        "raw_root_access_count": 0,
    }


def validate_report_display_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(spec, "spec")
    if value.get("schema_version") != REPORT_SPEC_SCHEMA:
        raise HumanReadableAuditError("REPORT_SPEC_SCHEMA_INVALID", "报告展示规范版本不正确。")
    for field in ("spec_ref", "spec_version"):
        _text(value.get(field), field)
    if tuple(_sequence(value.get("allowed_item_fields"), "allowed_item_fields")) != REPORT_ITEM_FIELDS:
        raise HumanReadableAuditError("REPORT_FIELD_WHITELIST_INVALID", "经营摘要字段白名单发生变化。")
    if tuple(_sequence(value.get("forbidden_internal_terms"), "forbidden_internal_terms")) != FORBIDDEN_REPORT_TERMS:
        raise HumanReadableAuditError("REPORT_TERM_BLOCKLIST_INVALID", "经营摘要技术词阻断表发生变化。")
    for field in ("decision_relevant_only", "title_must_use_business_language"):
        if value.get(field) is not True:
            raise HumanReadableAuditError("REPORT_BUSINESS_GATE_REQUIRED", "经营摘要必须只展示决策相关中文信息。")
    if value.get("debug_information_allowed") is not False:
        raise HumanReadableAuditError("REPORT_DEBUG_FORBIDDEN", "经营摘要不得允许调试信息。")
    if value.get("formal_report_generation_included") is not False or value.get("raw_root_access_count") != 0:
        raise HumanReadableAuditError("REPORT_SCOPE_BOUNDARY_INVALID", "展示规范不得生成正式报告或读取 raw。")
    return value


def _friendly_difference_names(manual: Mapping[str, Any]) -> dict[str, str]:
    checked = validate_human_rule_manual(manual)
    return {
        row["rule_key"].removeprefix("DIFFERENCE_"): row["name_zh"]
        for row in checked["rules"]
        if row["rule_kind"] == "DIFFERENCE"
    }


def build_management_difference_summary(
    differences: Sequence[Mapping[str, Any]],
    *,
    manual: Mapping[str, Any] | None = None,
    spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project only decision-relevant differences into a safe business summary."""

    checked_spec = validate_report_display_spec(spec or default_report_display_spec())
    friendly = _friendly_difference_names(manual or build_human_rule_manual())
    items: list[dict[str, str]] = []
    excluded = 0
    for index, raw in enumerate(_sequence(differences, "differences"), start=1):
        row = _mapping(raw, f"differences[{index}]")
        _text(row.get("difference_ref"), "difference_ref")
        code = _text(row.get("difference_type_code"), "difference_type_code")
        if code not in friendly:
            raise HumanReadableAuditError("UNKNOWN_DIFFERENCE_TYPE", "差异类型未在规则手册登记。")
        affects = _bool(row.get("affects_business_decision"), "affects_business_decision")
        if not affects:
            excluded += 1
            continue
        for field in (
            "plain_reason_zh",
            "business_impact_zh",
            "current_status_zh",
            "owner_action_zh",
        ):
            _text(row.get(field), field)
        item = {
            "title_zh": f"经营提醒：{friendly[code]}",
            "what_changed_zh": row["plain_reason_zh"],
            "business_impact_zh": row["business_impact_zh"],
            "current_status_zh": row["current_status_zh"],
            "recommended_action_zh": row["owner_action_zh"],
        }
        if tuple(item) != REPORT_ITEM_FIELDS:
            raise HumanReadableAuditError("REPORT_OUTPUT_FIELD_DRIFT", "经营摘要输出字段越过白名单。")
        rendered = "\n".join(item.values()).lower()
        matches = [term for term in checked_spec["forbidden_internal_terms"] if term.lower() in rendered]
        if matches:
            raise HumanReadableAuditError("INTERNAL_TERM_IN_BUSINESS_REPORT", "经营摘要含内部技术或调试信息。")
        items.append(item)
    rendered_all = "\n".join(value for item in items for value in item.values()).lower()
    technical_occurrences = sum(rendered_all.count(term.lower()) for term in FORBIDDEN_REPORT_TERMS)
    return {
        "schema_version": "kmfa.v015.s09p3.management_difference_summary.v1",
        "report_kind": "PUBLIC_SAFE_SYNTHETIC_DISPLAY_SAMPLE",
        "input_difference_count": len(_sequence(differences, "differences")),
        "included_difference_count": len(items),
        "excluded_non_decision_difference_count": excluded,
        "technical_term_occurrence_count": technical_occurrences,
        "debug_field_count": 0,
        "internal_reference_field_count": 0,
        "items": items,
        "formal_report_generated": False,
        "raw_root_access_count": 0,
    }


def new_closure_snapshot(
    *, difference_ref: str, business_label_zh: str, initial_report_version: str
) -> dict[str, Any]:
    return {
        "schema_version": CLOSURE_SNAPSHOT_SCHEMA,
        "case_ref": "CLOSURE-" + _text(difference_ref, "difference_ref"),
        "difference_ref": _text(difference_ref, "difference_ref"),
        "business_label_zh": _text(business_label_zh, "business_label_zh"),
        "initial_report_version": _text(initial_report_version, "initial_report_version"),
        "current_report_version": initial_report_version.strip(),
        "current_step_count": 0,
        "current_status_zh": "待发现并登记差异",
        "closure_complete": False,
        "events": [],
        "history_hash": _stable_hash([]),
        "source_or_fact_mutation_performed": False,
        "raw_root_access_count": 0,
    }


def append_closure_event(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    """Append exactly the next closure event and return a new persisted snapshot."""

    state = _mapping(snapshot, "snapshot")
    if state.get("schema_version") != CLOSURE_SNAPSHOT_SCHEMA:
        raise HumanReadableAuditError("CLOSURE_SNAPSHOT_SCHEMA_INVALID", "闭环快照版本不正确。")
    events = [_mapping(row, "events[]") for row in _sequence(state.get("events"), "events")]
    if len(events) >= len(CLOSURE_STEPS):
        raise HumanReadableAuditError("CLOSURE_ALREADY_COMPLETE", "闭环完成后不得覆盖历史。")
    row = _mapping(event, "event")
    if row.get("schema_version") != CLOSURE_EVENT_SCHEMA:
        raise HumanReadableAuditError("CLOSURE_EVENT_SCHEMA_INVALID", "闭环事件版本不正确。")
    expected_step = CLOSURE_STEPS[len(events)]
    if row.get("event_type") != expected_step:
        raise HumanReadableAuditError("CLOSURE_STEP_OUT_OF_ORDER", "闭环必须按发现、处理、预览、确认、重算、更新顺序执行。")
    if row.get("sequence") != len(events) + 1:
        raise HumanReadableAuditError("CLOSURE_SEQUENCE_INVALID", "闭环事件序号必须连续。")
    for field in ("event_ref", "actor_role", "occurred_at", "feedback_zh"):
        _text(row.get(field), field)
    if row["event_ref"] in {existing.get("event_ref") for existing in events}:
        raise HumanReadableAuditError("DUPLICATE_CLOSURE_EVENT", "闭环事件不得重复。")
    if row.get("difference_ref") != state.get("difference_ref"):
        raise HumanReadableAuditError("CLOSURE_CASE_BINDING_MISMATCH", "闭环事件不得串到另一项差异。")
    for field in REQUIRED_EVENT_FIELDS[expected_step]:
        value = row.get(field)
        if field == "affected_output_labels_zh":
            labels = [_text(item, field) for item in _sequence(value, field)]
            if not labels:
                raise HumanReadableAuditError("AFFECTED_OUTPUT_REQUIRED", "重新计算必须说明影响了哪些输出。")
            row[field] = labels
        else:
            _text(value, field)
    if expected_step == "HUMAN_CONFIRMED" and row["actor_role"] not in {"FINANCE_REVIEWER", "OWNER"}:
        raise HumanReadableAuditError("HUMAN_CONFIRMATION_REQUIRED", "确认步骤必须由财务复核人或负责人完成。")
    if expected_step == "RECALCULATED" and row.get("recalculation_status") != "PASS":
        raise HumanReadableAuditError("RECALCULATION_NOT_PASSED", "重新计算未通过时不能继续。")
    if expected_step == "REPORT_UPDATED":
        if row.get("report_version") == state.get("initial_report_version"):
            raise HumanReadableAuditError("REPORT_VERSION_NOT_ADVANCED", "经营摘要更新必须产生新版本。")
        state["current_report_version"] = row["report_version"]
    events.append(row)
    state["events"] = events
    state["current_step_count"] = len(events)
    state["current_status_zh"] = CLOSURE_STATUS_ZH[expected_step]
    state["closure_complete"] = len(events) == len(CLOSURE_STEPS)
    state["history_hash"] = _stable_hash(events)
    state["source_or_fact_mutation_performed"] = False
    state["raw_root_access_count"] = 0
    return state


def restore_closure_snapshot(serialized: str) -> dict[str, Any]:
    """Reload and replay a serialized snapshot to prove refresh persistence."""

    try:
        loaded = json.loads(_text(serialized, "serialized"))
    except json.JSONDecodeError as error:
        raise HumanReadableAuditError("CLOSURE_SERIALIZATION_INVALID", "闭环快照无法读取。") from error
    value = _mapping(loaded, "serialized_snapshot")
    restored = new_closure_snapshot(
        difference_ref=_text(value.get("difference_ref"), "difference_ref"),
        business_label_zh=_text(value.get("business_label_zh"), "business_label_zh"),
        initial_report_version=_text(value.get("initial_report_version"), "initial_report_version"),
    )
    for event in _sequence(value.get("events"), "events"):
        restored = append_closure_event(restored, _mapping(event, "events[]"))
    comparable_fields = (
        "schema_version",
        "case_ref",
        "difference_ref",
        "business_label_zh",
        "initial_report_version",
        "current_report_version",
        "current_step_count",
        "current_status_zh",
        "closure_complete",
        "events",
        "history_hash",
        "source_or_fact_mutation_performed",
        "raw_root_access_count",
    )
    if any(restored.get(field) != value.get(field) for field in comparable_fields):
        raise HumanReadableAuditError("CLOSURE_REFRESH_DRIFT", "刷新后闭环状态或历史发生变化。")
    return restored


def query_closure_history(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    state = _mapping(snapshot, "snapshot")
    events = [_mapping(row, "events[]") for row in _sequence(state.get("events"), "events")]
    return [
        {
            "sequence": row["sequence"],
            "step_zh": CLOSURE_STATUS_ZH[row["event_type"]],
            "feedback_zh": row["feedback_zh"],
            "occurred_at": row["occurred_at"],
        }
        for row in events
    ]


def _closure_event(
    sequence: int,
    event_type: str,
    *,
    actor_role: str,
    feedback_zh: str,
    **payload: Any,
) -> dict[str, Any]:
    return {
        "schema_version": CLOSURE_EVENT_SCHEMA,
        "event_ref": f"SYN-CLOSURE-EVENT-{sequence:02d}",
        "difference_ref": "SYN-DIFF-001",
        "sequence": sequence,
        "event_type": event_type,
        "actor_role": actor_role,
        "occurred_at": f"2026-07-15T1{sequence}:00:00+10:00",
        "feedback_zh": feedback_zh,
        **payload,
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Return deterministic public-safe S09-P3 acceptance evidence."""

    manual = build_human_rule_manual()
    review = review_human_rule_manual(manual)
    report = build_management_difference_summary(
        [
            {
                "difference_ref": "SYN-DIFF-001",
                "difference_type_code": "UNBILLED",
                "affects_business_decision": True,
                "plain_reason_zh": "交付进度已确认，但开票进度尚未同步。",
                "business_impact_zh": "会影响本期收入进度、开票计划和现金安排判断。",
                "current_status_zh": "已完成影响预览和人工确认，重新计算已通过。",
                "owner_action_zh": "确认预计开票时间，并在下次经营复盘检查是否已完成。",
                "source_refs": ["SYN-SOURCE-A", "SYN-SOURCE-B"],
                "debug_payload": {"control": True},
            },
            {
                "difference_ref": "SYN-DIFF-002",
                "difference_type_code": "UNALLOCATED",
                "affects_business_decision": False,
                "plain_reason_zh": "模拟控制项，不影响当前经营判断。",
                "business_impact_zh": "无当前经营影响。",
                "current_status_zh": "保留在内部待办。",
                "owner_action_zh": "无需进入经营摘要。",
            },
        ],
        manual=manual,
    )
    closure = new_closure_snapshot(
        difference_ref="SYN-DIFF-001",
        business_label_zh="开票进度与经营收入不同步",
        initial_report_version="经营差异摘要-v1",
    )
    events = (
        _closure_event(
            1,
            "DIFFERENCE_DISCOVERED",
            actor_role="SYSTEM",
            feedback_zh="已登记差异并说明影响范围。",
            difference_summary_zh="交付进度已确认，但开票进度尚未同步。",
        ),
        _closure_event(
            2,
            "HANDLING_PROPOSED",
            actor_role="FINANCE_REVIEWER",
            feedback_zh="已提出保留经营收入并单列开票进度提醒的方案。",
            handling_zh="不改原账，保留经营收入，并单列开票时间待办。",
        ),
        _closure_event(
            3,
            "IMPACT_PREVIEWED",
            actor_role="SYSTEM",
            feedback_zh="已展示处理前后对收入进度、开票计划和现金安排的影响。",
            impact_before_zh="处理前无法区分经营进度与开票进度。",
            impact_after_zh="处理后经营收入保留，开票风险单独提示。",
        ),
        _closure_event(
            4,
            "HUMAN_CONFIRMED",
            actor_role="FINANCE_REVIEWER",
            feedback_zh="财务复核视角已确认处理方案和影响预览一致。",
            decision_zh="确认按预览方案处理。",
        ),
        _closure_event(
            5,
            "RECALCULATED",
            actor_role="SYSTEM",
            feedback_zh="受影响的项目经营摘要和开票提醒已重新计算且通过。",
            recalculation_status="PASS",
            affected_output_labels_zh=["项目经营摘要", "开票进度提醒"],
        ),
        _closure_event(
            6,
            "REPORT_UPDATED",
            actor_role="SYSTEM",
            feedback_zh="经营摘要已更新为新版本，旧版本仍可查询。",
            report_version="经营差异摘要-v2",
            report_update_summary_zh="新增一条开票进度经营提醒。",
        ),
    )
    for event in events:
        closure = append_closure_event(closure, event)
    restored = restore_closure_snapshot(json.dumps(closure, ensure_ascii=False, sort_keys=True))

    missing_feedback_rejected = False
    try:
        bad = _closure_event(
            1,
            "DIFFERENCE_DISCOVERED",
            actor_role="SYSTEM",
            feedback_zh="",
            difference_summary_zh="模拟差异。",
        )
        append_closure_event(
            new_closure_snapshot(
                difference_ref="SYN-DIFF-001",
                business_label_zh="模拟差异",
                initial_report_version="经营差异摘要-v1",
            ),
            bad,
        )
    except HumanReadableAuditError as error:
        missing_feedback_rejected = error.code == "TEXT_REQUIRED"

    out_of_order_rejected = False
    try:
        append_closure_event(
            new_closure_snapshot(
                difference_ref="SYN-DIFF-001",
                business_label_zh="模拟差异",
                initial_report_version="经营差异摘要-v1",
            ),
            events[1],
        )
    except HumanReadableAuditError as error:
        out_of_order_rejected = error.code == "CLOSURE_STEP_OUT_OF_ORDER"

    return {
        "manual": manual,
        "manual_review": review,
        "report_display_spec": default_report_display_spec(),
        "report_summary": report,
        "closure_snapshot": closure,
        "restored_closure_snapshot": restored,
        "closure_history": query_closure_history(restored),
        "closure_step_count": len(CLOSURE_STEPS),
        "refresh_state_persisted": restored == closure,
        "history_queryable": len(query_closure_history(restored)) == len(CLOSURE_STEPS),
        "missing_feedback_rejected": missing_feedback_rejected,
        "out_of_order_rejected": out_of_order_rejected,
        "raw_root_access_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
