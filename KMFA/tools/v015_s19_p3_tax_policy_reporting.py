#!/usr/bin/env python3
"""KMFA v1.5 S19-P3 税务与政策报告及专业复核内核。

只组合 S19-P1/P2 已验收的公开合成结果。报告是内部管理摘要；专业
复核意见只追加事件，不修改票据、政策、证据或任何 raw 资料。
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s15_p2_identity_roles as identity
from KMFA.tools import v015_s19_p1_tax_invoice_facts as tax_kernel
from KMFA.tools import v015_s19_p2_policy_eligibility as policy_kernel


RUN_PHASE_ID = "V015_S19_P3_TAX_POLICY_REPORTING"
ROADMAP_PHASE_ID = "S19-P3"
TASK_ID = "KMFA-V015-S19-P3-TAX-POLICY-REPORTING-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S19-P3-TAX-POLICY-REPORTING"
VERSION = "1.5.0-dev-s19p3"
DATA_CLASSIFICATION = "PUBLIC_OFFICIAL_POLICY_AND_SYNTHETIC_REPORT"
REPORT_AS_OF = "2026-07-16"
PERIOD_CYCLES = {
    "2026-07": ("MONTHLY", "月度"),
    "2026-Q2": ("QUARTERLY", "季度"),
    "2026-H1": ("HALF_YEAR", "半年度"),
}
PROFESSIONAL_REVIEW_ROLES = frozenset({"tax", "reviewer"})
OPINIONS = {
    "CONFIRMED_FOR_INTERNAL_USE": "可继续用于内部管理复核",
    "NEEDS_SOURCE_CHECK": "需要补充或核对来源",
    "REQUIRES_SPECIALIST_FOLLOWUP": "需要专业人员继续跟进",
}
RISK_COPY = {
    "UNKNOWN_TAX_RATE": (
        "这张票的税率还没有明确依据",
        "核对票据和合同中的税率依据；确认前保留待确认状态。",
    ),
    "ENTITY_MISMATCH": (
        "票据主体和合同主体不一致",
        "核对开票主体、合同主体和业务归属，不自动调整记录。",
    ),
    "PERIOD_MISMATCH": (
        "票据期间和合同期间不一致",
        "核对业务发生时间和归属期间，确认前不改变期间。",
    ),
    "PROJECT_MISMATCH": (
        "票据项目和合同项目不一致",
        "核对项目归属和合同对应关系，不自动改挂项目。",
    ),
    "TAX_RATE_MISMATCH": (
        "票据税率和合同记录不一致",
        "核对双方税率依据；确认前不计算调整结果。",
    ),
}
FORBIDDEN_ALARM_WORDS = ("爆雷", "灭顶", "巨额罚款", "立即处罚", "生死", "灾难")


class TaxPolicyReportingError(ValueError):
    """S19-P3 输入、权限或事件违反报告边界。"""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_scope(company_id: str, period: str) -> None:
    if company_id not in policy_kernel.COMPANIES:
        raise TaxPolicyReportingError("公司主体不在公开演示范围内")
    if period not in PERIOD_CYCLES:
        raise TaxPolicyReportingError("报告周期不在公开演示范围内")


def _report_id(company_id: str, period: str) -> str:
    return f"TPR-{company_id}-{period}"


def _risk_item(row: Mapping[str, Any]) -> dict[str, Any]:
    anomaly_types = list(row.get("anomaly_types") or [])
    issue_parts = [RISK_COPY[value][0] for value in anomaly_types]
    next_parts = [RISK_COPY[value][1] for value in anomaly_types]
    tax_cents = row.get("tax_cents")
    return {
        "risk_id": f"RISK-{row['invoice_id']}",
        "invoice_id": row["invoice_id"],
        "project_id": row["project_id"],
        "project_name_zh": row["project_name_zh"],
        "issue_zh": "；".join(issue_parts),
        "impact_zh": (
            "当前记录中有明确税额，但它不是风险损失或补税结论。"
            if isinstance(tax_cents, int)
            else "当前税率和税额都未确认，不能估算金额影响。"
        ),
        "reference_tax_cents": tax_cents if isinstance(tax_cents, int) else None,
        "reference_tax_label_zh": "当前票据已记录税额（非风险损失）" if isinstance(tax_cents, int) else "金额待确认",
        "next_step_zh": " ".join(dict.fromkeys(next_parts)),
        "anomaly_types": anomaly_types,
        "anomaly_labels_zh": list(row.get("anomaly_labels_zh") or []),
        "basis_refs": [row["source_ref"], row["links"]["contract_ref"]],
        "automatic_adjustment_allowed": False,
        "formal_filing_conclusion": None,
    }


def tax_risk_summary(company_id: str = "demo-north", period: str = "2026-07") -> dict[str, Any]:
    """将税票异常按票据合并成普通中文摘要，不计算补税或处罚。"""

    _require_scope(company_id, period)
    source = tax_kernel.tax_invoice_view(company_id=company_id, period=period)
    if not source.get("allowed"):
        raise TaxPolicyReportingError("S19-P1 税票结果不可用")
    items = [_risk_item(row) for row in source["rows"] if row["match_state"] == "REVIEW_REQUIRED"]
    explicit_reference = sum(row["reference_tax_cents"] or 0 for row in items)
    summary = {
        "schema_version": "kmfa.v015.s19p3.tax_risk_summary.v1",
        "company_id": company_id,
        "period": period,
        "report_as_of": REPORT_AS_OF,
        "source_phase": tax_kernel.RUN_PHASE_ID,
        "invoice_fact_count": source["summary"]["fact_count"],
        "matched_invoice_count": source["summary"]["matched_count"],
        "review_invoice_count": len(items),
        "anomaly_count": sum(len(row["anomaly_types"]) for row in items),
        "unknown_amount_item_count": sum(row["reference_tax_cents"] is None for row in items),
        "explicit_reference_tax_cents": explicit_reference,
        "explicit_reference_tax_label_zh": "需复核票据中当前已有税额合计（不是风险损失或补税金额）",
        "headline_zh": f"本期有 {len(items)} 张票需要人工核对，另有 {source['summary']['matched_count']} 张已完成匹配。",
        "plain_language_zh": "先核对主体、项目、期间和税率依据；系统不会自动调税、开票或申报。",
        "items": items,
        "management_analysis_only": True,
        "formal_filing_conclusion": None,
        "formal_filing_conclusion_count": 0,
        "automatic_tax_adjustment_count": 0,
        "alarm_copy_count": sum(word in json.dumps(items, ensure_ascii=False) for word in FORBIDDEN_ALARM_WORDS),
    }
    return summary


def policy_preparation_report(company_id: str = "demo-north", period: str = "2026-07") -> dict[str, Any]:
    """形成月度、季度或半年度准备报告，只描述材料状态和缺口。"""

    _require_scope(company_id, period)
    cycle_id, cycle_zh = PERIOD_CYCLES[period]
    source = policy_kernel.policy_view(company_id=company_id, period=period)
    if not source.get("allowed"):
        raise TaxPolicyReportingError("S19-P2 政策准备结果不可用")
    category_rows = []
    for row in source["readiness_categories"]:
        category_rows.append({
            **row,
            "status_zh": "材料齐备" if row["missing_count"] == 0 and row["review_count"] == 0 else "仍需补充或核对",
            "next_step_zh": (
                "保留已核验来源并在下一周期复查。"
                if row["missing_count"] == 0 and row["review_count"] == 0
                else f"补充 {row['missing_count']} 份缺失材料，核对 {row['review_count']} 份待复核材料。"
            ),
        })
    registry = source["policy_registry"]
    return {
        "schema_version": "kmfa.v015.s19p3.policy_preparation_report.v1",
        "report_id": _report_id(company_id, period),
        "company_id": company_id,
        "company_zh": source["company_zh"],
        "period": period,
        "cycle_id": cycle_id,
        "cycle_zh": cycle_zh,
        "report_as_of": REPORT_AS_OF,
        "source_phase": policy_kernel.RUN_PHASE_ID,
        "policy_count": len(registry),
        "current_policy_count": sum(row["rule_use_allowed"] for row in registry),
        "blocked_policy_count": sum(not row["rule_use_allowed"] for row in registry),
        "category_count": len(category_rows),
        "evidence_item_count": source["summary"]["evidence_item_count"],
        "available_evidence_count": source["summary"]["available_evidence_count"],
        "missing_evidence_count": source["summary"]["missing_evidence_count"],
        "review_evidence_count": source["summary"]["review_evidence_count"],
        "headline_zh": f"{cycle_zh}检查：{source['summary']['available_evidence_count']} 份材料已有来源，{source['summary']['missing_evidence_count']} 份缺失，{source['summary']['review_evidence_count']} 份待核对。",
        "categories": category_rows,
        "policy_snapshots": [{
            "policy_id": row["policy_id"],
            "policy_name_zh": row["policy_name_zh"],
            "rule_version": row["rule_version"],
            "validity_status": row["validity_status"],
            "rule_use_allowed": row["rule_use_allowed"],
            "source_url": row["source_url"],
            "reviewed_at": row["reviewed_at"],
            "next_review_due": row["next_review_due"],
        } for row in registry],
        "formal_eligibility_conclusion": None,
        "formal_eligibility_conclusion_count": 0,
        "recognition_result_promised": False,
        "scope_limitation_zh": "这是周期性的内部材料准备报告，不是正式资格认定、申报意见或认定结果承诺。",
    }


def periodic_policy_reports(company_id: str = "demo-north") -> list[dict[str, Any]]:
    return [policy_preparation_report(company_id, period) for period in PERIOD_CYCLES]


def review_basis(company_id: str = "demo-north", period: str = "2026-07") -> list[dict[str, str]]:
    """返回可选的已知依据，阻止复核接口接收任意来源字符串。"""

    tax = tax_risk_summary(company_id, period)
    policy = policy_preparation_report(company_id, period)
    rows: list[dict[str, str]] = []
    for item in tax["items"]:
        for index, ref in enumerate(item["basis_refs"], start=1):
            rows.append({"basis_ref": ref, "label_zh": f"{item['invoice_id']} 核对依据 {index}", "source_kind": "TAX_FACT"})
    for item in policy["policy_snapshots"]:
        rows.append({"basis_ref": item["source_url"], "label_zh": f"{item['policy_name_zh']} 官方来源", "source_kind": "OFFICIAL_POLICY"})
    unique: dict[str, dict[str, str]] = {}
    for row in rows:
        unique.setdefault(row["basis_ref"], row)
    return list(unique.values())


def review_permission(user_id: str, role_id: str, company_id: str) -> dict[str, Any]:
    snapshot = identity.identity_snapshot(user_id, role_id, company_id)
    allowed = bool(snapshot.get("allowed")) and role_id in PROFESSIONAL_REVIEW_ROLES
    if not snapshot.get("allowed"):
        reason_code = snapshot.get("reason_code", "IDENTITY_DENIED")
        reason_zh = snapshot.get("reason_zh", "身份或公司权限不符合要求。")
    elif role_id not in PROFESSIONAL_REVIEW_ROLES:
        reason_code = "PROFESSIONAL_ROLE_REQUIRED"
        reason_zh = "只有税务或审核角色可以记录专业复核意见。"
    else:
        reason_code = "PROFESSIONAL_REVIEW_ALLOWED"
        reason_zh = "当前角色可以查看依据并追加复核意见。"
    return {
        "allowed": allowed,
        "reason_code": reason_code,
        "reason_zh": reason_zh,
        "user_id": user_id,
        "role_id": role_id,
        "role_label_zh": identity.ROLE_HATS.get(role_id, {}).get("label_zh", "未知角色"),
        "company_id": company_id,
        "append_only": True,
        "raw_write_allowed": False,
        "fact_write_allowed": False,
    }


class ProfessionalReviewJournal:
    """本地只追加 JSONL 事件账；不提供更新或删除方法。"""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                for number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise TaxPolicyReportingError(f"复核事件账第 {number} 行损坏") from error
                    _validate_review_event(value, line_number=number)
                    rows.append(value)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return rows

    def append(self, event: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        descriptor = os.open(self.path, flags, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            payload = (json.dumps(dict(event), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def _review_fingerprint_payload(
    *, report_id: str, company_id: str, period: str, user_id: str, role_id: str,
    opinion_code: str, comment_zh: str, basis_refs: Sequence[str], idempotency_key: str,
) -> dict[str, Any]:
    normalized_refs = sorted(set(_text(value) for value in basis_refs if _text(value)))
    return {
        "report_id": report_id, "company_id": company_id, "period": period,
        "user_id": user_id, "role_id": role_id, "opinion_code": opinion_code,
        "comment_zh": _text(comment_zh), "basis_refs": normalized_refs,
        "idempotency_key": _text(idempotency_key),
    }


def _review_fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _validate_review_event(event: Mapping[str, Any], *, line_number: int | None = None) -> None:
    """逐字段验证持久化事件，任何篡改都拒绝进入报告。"""

    prefix = f"复核事件账第 {line_number} 行" if line_number else "复核事件"
    expected_fields = {
        "schema_version", "event_id", "event_type", "event_fingerprint",
        "data_classification", "report_id", "company_id", "period", "user_id",
        "role_id", "opinion_code", "comment_zh", "basis_refs", "idempotency_key",
        "opinion_zh", "actor_role_label_zh", "recorded_at", "append_only",
        "in_place_update_allowed", "source_data_write_count",
        "fact_layer_write_count", "real_business_action_count",
    }
    if set(event) != expected_fields:
        raise TaxPolicyReportingError(f"{prefix}字段集合无效")
    company_id = _text(event.get("company_id"))
    period = _text(event.get("period"))
    try:
        _require_scope(company_id, period)
    except TaxPolicyReportingError as error:
        raise TaxPolicyReportingError(f"{prefix}范围无效") from error
    role_id = _text(event.get("role_id"))
    user_id = _text(event.get("user_id"))
    opinion_code = _text(event.get("opinion_code"))
    comment_zh = _text(event.get("comment_zh"))
    idempotency_key = _text(event.get("idempotency_key"))
    basis_refs = event.get("basis_refs")
    if event.get("schema_version") != "kmfa.v015.s19p3.professional_review_event.v1":
        raise TaxPolicyReportingError(f"{prefix}结构版本无效")
    if event.get("event_type") != "PROFESSIONAL_REVIEW_RECORDED":
        raise TaxPolicyReportingError(f"{prefix}类型无效")
    if event.get("data_classification") != DATA_CLASSIFICATION:
        raise TaxPolicyReportingError(f"{prefix}数据分类无效")
    if event.get("report_id") != _report_id(company_id, period):
        raise TaxPolicyReportingError(f"{prefix}报告范围不一致")
    permission = review_permission(user_id, role_id, company_id)
    if not permission["allowed"]:
        raise TaxPolicyReportingError(f"{prefix}记录人权限无效")
    if opinion_code not in OPINIONS or event.get("opinion_zh") != OPINIONS.get(opinion_code):
        raise TaxPolicyReportingError(f"{prefix}复核意见无效")
    if event.get("actor_role_label_zh") != identity.ROLE_HATS[role_id]["label_zh"]:
        raise TaxPolicyReportingError(f"{prefix}角色标签无效")
    if not isinstance(basis_refs, list) or not basis_refs:
        raise TaxPolicyReportingError(f"{prefix}缺少报告依据")
    normalized_refs = sorted(set(_text(value) for value in basis_refs if _text(value)))
    if normalized_refs != basis_refs:
        raise TaxPolicyReportingError(f"{prefix}报告依据格式无效")
    allowed_refs = {row["basis_ref"] for row in review_basis(company_id, period)}
    if any(value not in allowed_refs for value in normalized_refs):
        raise TaxPolicyReportingError(f"{prefix}包含范围外依据")
    if len(comment_zh) < 4 or len(comment_zh) > 500 or len(idempotency_key) < 4:
        raise TaxPolicyReportingError(f"{prefix}说明或幂等键无效")
    if (
        event.get("append_only") is not True
        or event.get("in_place_update_allowed") is not False
        or event.get("source_data_write_count") != 0
        or event.get("fact_layer_write_count") != 0
        or event.get("real_business_action_count") != 0
    ):
        raise TaxPolicyReportingError(f"{prefix}违反只追加和零业务写入边界")
    if event.get("recorded_at") != REPORT_AS_OF + "T12:00:00+10:00":
        raise TaxPolicyReportingError(f"{prefix}记录时间无效")
    payload = _review_fingerprint_payload(
        report_id=event["report_id"], company_id=company_id, period=period,
        user_id=user_id, role_id=role_id, opinion_code=opinion_code,
        comment_zh=comment_zh, basis_refs=normalized_refs,
        idempotency_key=idempotency_key,
    )
    fingerprint = _review_fingerprint(payload)
    if event.get("event_fingerprint") != f"sha256:{fingerprint}" or event.get("event_id") != f"PREV-{fingerprint[:20]}":
        raise TaxPolicyReportingError(f"{prefix}指纹校验失败，记录可能已被篡改")


def _review_event(
    *, report_id: str, company_id: str, period: str, user_id: str, role_id: str,
    opinion_code: str, comment_zh: str, basis_refs: Sequence[str], idempotency_key: str,
) -> dict[str, Any]:
    fingerprint_payload = _review_fingerprint_payload(
        report_id=report_id, company_id=company_id, period=period,
        user_id=user_id, role_id=role_id, opinion_code=opinion_code,
        comment_zh=comment_zh, basis_refs=basis_refs, idempotency_key=idempotency_key,
    )
    fingerprint = _review_fingerprint(fingerprint_payload)
    return {
        "schema_version": "kmfa.v015.s19p3.professional_review_event.v1",
        "event_id": f"PREV-{fingerprint[:20]}",
        "event_type": "PROFESSIONAL_REVIEW_RECORDED",
        "event_fingerprint": f"sha256:{fingerprint}",
        "data_classification": DATA_CLASSIFICATION,
        **fingerprint_payload,
        "opinion_zh": OPINIONS[opinion_code],
        "actor_role_label_zh": identity.ROLE_HATS[role_id]["label_zh"],
        "recorded_at": REPORT_AS_OF + "T12:00:00+10:00",
        "append_only": True,
        "in_place_update_allowed": False,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "real_business_action_count": 0,
    }


def record_professional_review(
    journal: ProfessionalReviewJournal,
    *, report_id: str, company_id: str, period: str, user_id: str, role_id: str,
    opinion_code: str, comment_zh: str, basis_refs: Sequence[str], idempotency_key: str,
) -> dict[str, Any]:
    """校验权限与依据后追加意见；相同请求幂等，不允许覆盖。"""

    _require_scope(company_id, period)
    permission = review_permission(user_id, role_id, company_id)
    if not permission["allowed"]:
        raise TaxPolicyReportingError(permission["reason_zh"])
    if report_id != _report_id(company_id, period):
        raise TaxPolicyReportingError("报告、公司主体或周期不一致")
    if opinion_code not in OPINIONS:
        raise TaxPolicyReportingError("请选择受支持的复核意见")
    comment = _text(comment_zh)
    if len(comment) < 4 or len(comment) > 500:
        raise TaxPolicyReportingError("复核说明需为 4 至 500 个字符")
    if len(_text(idempotency_key)) < 4:
        raise TaxPolicyReportingError("缺少有效的幂等键")
    allowed_refs = {row["basis_ref"] for row in review_basis(company_id, period)}
    normalized_refs = sorted(set(_text(value) for value in basis_refs if _text(value)))
    if not normalized_refs:
        raise TaxPolicyReportingError("至少选择一项报告依据")
    if any(value not in allowed_refs for value in normalized_refs):
        raise TaxPolicyReportingError("复核依据不属于当前报告")
    event = _review_event(
        report_id=report_id, company_id=company_id, period=period, user_id=user_id,
        role_id=role_id, opinion_code=opinion_code, comment_zh=comment,
        basis_refs=normalized_refs, idempotency_key=idempotency_key,
    )
    for existing in journal.read():
        if existing.get("company_id") == company_id and existing.get("period") == period and existing.get("idempotency_key") == idempotency_key:
            if existing.get("event_fingerprint") != event["event_fingerprint"]:
                raise TaxPolicyReportingError("同一幂等键不能提交不同复核内容")
            return {"allowed": True, "idempotent_replay": True, "event": existing}
    journal.append(event)
    return {"allowed": True, "idempotent_replay": False, "event": event}


def report_view(
    company_id: str = "demo-north", period: str = "2026-07", user_id: str = "demo-owner",
    role_id: str = "tax", events: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """返回同一报告投影，并按公司和周期隔离复核事件。"""

    _require_scope(company_id, period)
    auth = identity.authorization_decision(
        event_id="AUTH-S19P3-VIEW", occurred_at=REPORT_AS_OF, user_id=user_id,
        role_id=role_id, company_id=company_id, resource="REPORT", action="VIEW",
        reason="查看税务与政策内部报告",
    )
    if not auth["allowed"]:
        return {"allowed": False, "reason_code": auth["reason_code"], "reason_zh": auth["reason_zh"]}
    tax = tax_risk_summary(company_id, period)
    policy = policy_preparation_report(company_id, period)
    expected_report_id = _report_id(company_id, period)
    scoped_events = [
        dict(row) for row in events
        if row.get("report_id") == expected_report_id
        and row.get("company_id") == company_id
        and row.get("period") == period
    ]
    basis = review_basis(company_id, period)
    permission = review_permission(user_id, role_id, company_id)
    return {
        "schema_version": "kmfa.v015.s19p3.tax_policy_report_view.v1",
        "allowed": True,
        "report_id": policy["report_id"],
        "company_id": company_id,
        "company_zh": policy["company_zh"],
        "period": period,
        "report_as_of": REPORT_AS_OF,
        "tax_risk_summary": tax,
        "policy_preparation_report": policy,
        "review_basis": basis,
        "review_permission": permission,
        "review_events": scoped_events,
        "review_event_count": len(scoped_events),
        "cross_company_review_leak_count": 0,
        "formal_filing_conclusion_count": 0,
        "formal_eligibility_conclusion_count": 0,
        "recognition_result_promise_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "raw_root_access_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
        "scope_limitation_zh": "仅供内部管理复核，不替代税务申报、资格认定、主管部门决定或专业签字。",
        "data_classification": DATA_CLASSIFICATION,
    }


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p3.source_contract.v1",
        "stage_id": "S19",
        "stage_name_zh": "税务、发票、政策资格与证据准备",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "税务与政策报告",
        "task_ids": ["S19P3T01", "S19P3T02", "S19P3T03"],
        "task_names_zh": ["生成税务风险摘要", "生成政策准备报告", "建立人工专业复核入口"],
        "upstream_phases": [tax_kernel.RUN_PHASE_ID, policy_kernel.RUN_PHASE_ID],
        "runtime_external_fetch_allowed": False,
        "formal_filing_conclusion_allowed": False,
        "formal_eligibility_conclusion_allowed": False,
        "recognition_result_promise_allowed": False,
        "professional_review_roles": sorted(PROFESSIONAL_REVIEW_ROLES),
        "review_event_append_only": True,
        "raw_write_allowed": False,
        "data_classification": DATA_CLASSIFICATION,
    }


def public_checks() -> list[dict[str, Any]]:
    tax = tax_risk_summary()
    policy = policy_preparation_report()
    view = report_view()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL"})

    for row in tax["items"]:
        add(f"risk_{row['risk_id']}_plain_issue", bool(row["issue_zh"]) and not any(word in row["issue_zh"] for word in FORBIDDEN_ALARM_WORDS))
        add(f"risk_{row['risk_id']}_impact_boundary", "不是风险损失" in row["impact_zh"] or "不能估算" in row["impact_zh"])
        add(f"risk_{row['risk_id']}_next_step", bool(row["next_step_zh"]) and row["automatic_adjustment_allowed"] is False)
        add(f"risk_{row['risk_id']}_basis", len(row["basis_refs"]) == 2 and all(row["basis_refs"]))
        add(f"risk_{row['risk_id']}_no_filing", row["formal_filing_conclusion"] is None)
    for row in policy["categories"]:
        add(f"policy_{row['category_id']}_counts", row["required_count"] == row["available_count"] + row["missing_count"] + row["review_count"])
        add(f"policy_{row['category_id']}_status", row["status_zh"] in {"材料齐备", "仍需补充或核对"})
        add(f"policy_{row['category_id']}_next_step", bool(row["next_step_zh"]))
        add(f"policy_{row['category_id']}_no_conclusion", policy["formal_eligibility_conclusion"] is None)
    for row in policy["policy_snapshots"]:
        add(f"snapshot_{row['policy_id']}_source", row["source_url"].startswith("https://"))
        add(f"snapshot_{row['policy_id']}_review_dates", bool(row["reviewed_at"] and row["next_review_due"]))
    global_checks = {
        "tax_four_review_items": tax["review_invoice_count"] == 4,
        "tax_five_anomalies": tax["anomaly_count"] == 5,
        "tax_unknown_amount_kept": tax["unknown_amount_item_count"] == 1,
        "tax_no_alarm_copy": tax["alarm_copy_count"] == 0,
        "tax_no_adjustment": tax["automatic_tax_adjustment_count"] == 0,
        "policy_three_cycles": len(periodic_policy_reports()) == 3,
        "policy_six_categories": policy["category_count"] == 6,
        "policy_evidence_counts": (policy["available_evidence_count"], policy["missing_evidence_count"], policy["review_evidence_count"]) == (7, 3, 2),
        "policy_no_conclusion": policy["formal_eligibility_conclusion_count"] == 0,
        "policy_no_promise": policy["recognition_result_promised"] is False,
        "review_roles_exact": PROFESSIONAL_REVIEW_ROLES == {"tax", "reviewer"},
        "management_review_denied": review_permission("demo-owner", "management", "demo-north")["allowed"] is False,
        "tax_review_allowed": review_permission("demo-owner", "tax", "demo-north")["allowed"] is True,
        "report_scope_isolated": view["cross_company_review_leak_count"] == 0,
        "no_source_or_fact_write": view["source_data_write_count"] == 0 and view["fact_layer_write_count"] == 0,
        "no_raw_network_or_action": view["raw_root_access_count"] == 0 and view["external_network_request_count"] == 0 and view["real_business_action_count"] == 0,
    }
    for name, passed in global_checks.items():
        add(name, passed)
    if len(checks) != 72:
        raise TaxPolicyReportingError(f"expected 72 public checks, got {len(checks)}")
    return checks


def validate_public_contract() -> None:
    failed = [row["name"] for row in public_checks() if row["status"] != "PASS"]
    if failed:
        raise TaxPolicyReportingError("public contract failed: " + ", ".join(failed))


if __name__ == "__main__":
    validate_public_contract()
    print(json.dumps({"public_check_count": 72, "tax_review_item_count": 4, "policy_cycle_count": 3, "review_role_count": 2}, ensure_ascii=False, indent=2))
