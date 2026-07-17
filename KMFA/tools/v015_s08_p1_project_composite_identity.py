#!/usr/bin/env python3
"""KMFA v1.5 S08-P1 project composite identity kernel.

The kernel keeps the original evidence, derives explainable normalized names,
renormalizes weights over comparable evidence, and never lets amount evidence
or a low-coverage match decide an automatic merge by itself.
"""

from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY"
ROADMAP_PHASE_ID = "S08-P1"
TASK_ID = "KMFA-V015-S08-P1-PROJECT-COMPOSITE-IDENTITY-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S08-P1-PROJECT-COMPOSITE-IDENTITY"
VERSION = "1.5.0-dev-s08p1"
SCHEMA_VERSION = "kmfa.v015.s08p1.project_composite_identity.v1"

COMPONENT_WEIGHTS_BPS = {
    "contract_number": 2000,
    "project_name": 1800,
    "counterparty": 1500,
    "company_entity": 1000,
    "time_evidence": 1200,
    "amount_evidence": 1200,
    "responsible_person": 600,
    "source_version": 700,
}
TIME_SUBWEIGHTS_BPS = {
    "occurrence_date": 400,
    "start_date": 400,
    "finish_date": 400,
}
AMOUNT_SUBWEIGHTS_BPS = {
    "contract_amount_cents": 400,
    "settlement_amount_cents": 400,
    "invoice_amount_cents": 400,
}
PRIMARY_COMPONENTS = frozenset({"contract_number", "project_name", "counterparty", "company_entity"})
ANCHOR_COMPONENTS = frozenset({"contract_number", "project_name"})
HARD_CONFLICT_COMPONENTS = frozenset({"contract_number", "company_entity"})
AUXILIARY_COMPONENTS = frozenset({"time_evidence", "amount_evidence"})

AUTO_MATCH_SIMILARITY_BPS = 8500
MIN_AUTO_COVERAGE_BPS = 6000
MIN_AUTO_PRIMARY_MATCH_COUNT = 2

NAME_CATEGORIES = frozenset({"project_name", "counterparty", "company_entity"})
LEGAL_SUFFIXES = (
    "股份有限公司",
    "有限责任公司",
    "有限公司",
)
BRACKET_CHARACTERS = str.maketrans({"(": "", ")": "", "（": "", "）": "", "[": "", "]": "", "【": "", "】": ""})
NAME_SEPARATOR_RE = re.compile(r"[\s·•_\-—]+")
CONTRACT_SEPARATOR_RE = re.compile(r"[\s_—]+")


class ProjectIdentityError(ValueError):
    """Fail-closed project identity validation error."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


@dataclass(frozen=True)
class NameRule:
    rule_id: str
    rule_kind: str
    source_name: str
    target_name: str
    explanation_zh: str


DEFAULT_NAME_RULES = (
    NameRule("NAME-ABBR-001", "abbreviation", "星河改造", "星河能源系统改造项目", "将已登记简称展开为标准项目名。"),
    NameRule("NAME-TYPO-001", "curated_typo", "星河能原系统改造项目", "星河能源系统改造项目", "修正已登记且经过复核的错别字。"),
    NameRule("NAME-HISTORY-001", "historical_name", "星河能源一期升级工程", "星河能源系统改造项目", "将已登记历史名称映射到当前标准名称。"),
)


def _require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ProjectIdentityError("TEXT_REQUIRED", f"{field_name} 不能为空。")
    text = str(value).strip()
    if not text:
        raise ProjectIdentityError("TEXT_REQUIRED", f"{field_name} 不能为空。")
    return text


def _base_normalize_name(raw_name: str, category: str) -> tuple[str, list[dict[str, str]]]:
    if category not in NAME_CATEGORIES:
        raise ProjectIdentityError("NAME_CATEGORY_REQUIRED", "名称类别必须是项目名、对手方或公司主体。")
    _require_text(raw_name, "名称")
    value = str(raw_name)
    steps: list[dict[str, str]] = []

    def apply_step(kind: str, after: str, explanation: str) -> None:
        nonlocal value
        if after != value:
            steps.append({"kind": kind, "before": value, "after": after, "explanation_zh": explanation})
            value = after

    apply_step("outer_whitespace", value.strip(), "去除标准名称首尾空格；原始名称仍完整保留。")
    apply_step("unicode_width", unicodedata.normalize("NFKC", value), "统一全角和半角字符。")
    apply_step("letter_case", value.casefold(), "统一英文字母大小写。")
    apply_step("brackets", value.translate(BRACKET_CHARACTERS), "去除括号符号但保留括号内文字。")
    apply_step("spacing", NAME_SEPARATOR_RE.sub("", value), "去除名称中的空格和无语义分隔符。")
    if category in {"counterparty", "company_entity"}:
        for suffix in LEGAL_SUFFIXES:
            if value.endswith(suffix) and len(value) > len(suffix):
                apply_step("legal_suffix", value[: -len(suffix)], f"移除已登记公司法律后缀“{suffix}”。")
                break
    if not value:
        raise ProjectIdentityError("EMPTY_NORMALIZED_NAME", "名称标准化后不能为空。")
    return value, steps


def normalize_name(
    raw_name: str,
    *,
    category: str,
    rules: Sequence[NameRule] = DEFAULT_NAME_RULES,
) -> dict[str, Any]:
    """Return an explainable normalized name while preserving the original."""

    _require_text(raw_name, "名称")
    original = str(raw_name)
    canonical, steps = _base_normalize_name(original, category)
    candidates: list[tuple[NameRule, str]] = []
    for rule in rules:
        source, _ = _base_normalize_name(rule.source_name, category)
        if source == canonical:
            target, _ = _base_normalize_name(rule.target_name, category)
            candidates.append((rule, target))
    targets = {target for _, target in candidates}
    if len(targets) > 1:
        raise ProjectIdentityError("AMBIGUOUS_NAME_RULES", "同一名称命中多个不同标准名称，必须人工确认。")
    applied_rule_ids: list[str] = []
    if candidates:
        rule, target = candidates[0]
        if target != canonical:
            steps.append(
                {
                    "kind": rule.rule_kind,
                    "before": canonical,
                    "after": target,
                    "explanation_zh": rule.explanation_zh,
                }
            )
            canonical = target
        applied_rule_ids = sorted({candidate.rule_id for candidate, _ in candidates})
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_name": original,
        "standard_name": canonical,
        "category": category,
        "raw_name_preserved": True,
        "irreversible_overwrite_performed": False,
        "applied_rule_ids": applied_rule_ids,
        "transformation_count": len(steps),
        "transformations": steps,
        "explanation_zh": "原始名称保持不变；标准名称由列出的转换步骤派生。",
    }


def _normalize_contract_number(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    text = unicodedata.normalize("NFKC", str(value)).strip().upper()
    return CONTRACT_SEPARATOR_RE.sub("-", text)


def _normalize_simple_text(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return NAME_SEPARATOR_RE.sub("", unicodedata.normalize("NFKC", str(value)).strip().casefold())


def _normalize_date_map(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProjectIdentityError("TIME_EVIDENCE_MAPPING_REQUIRED", "时间证据必须按日期类型提供。")
    unknown = set(value) - set(TIME_SUBWEIGHTS_BPS)
    if unknown:
        raise ProjectIdentityError("UNKNOWN_TIME_FIELD", "时间证据包含未登记字段。")
    result: dict[str, str] = {}
    for key in TIME_SUBWEIGHTS_BPS:
        raw = value.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        text = str(raw).strip()
        try:
            normalized = date.fromisoformat(text).isoformat()
        except ValueError as error:
            raise ProjectIdentityError("INVALID_ISO_DATE", f"{key} 必须是有效 ISO 日期。") from error
        result[key] = normalized
    if "start_date" in result and "finish_date" in result and result["start_date"] > result["finish_date"]:
        raise ProjectIdentityError("INVALID_PROJECT_PERIOD", "开工日期不能晚于完工日期。")
    return result


def _normalize_amount_map(value: Any) -> dict[str, int]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProjectIdentityError("AMOUNT_EVIDENCE_MAPPING_REQUIRED", "金额证据必须按金额类型提供。")
    unknown = set(value) - set(AMOUNT_SUBWEIGHTS_BPS)
    if unknown:
        raise ProjectIdentityError("UNKNOWN_AMOUNT_FIELD", "金额证据包含未登记字段。")
    result: dict[str, int] = {}
    for key in AMOUNT_SUBWEIGHTS_BPS:
        raw = value.get(key)
        if raw is None:
            continue
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise ProjectIdentityError("INTEGER_CENTS_REQUIRED", f"{key} 必须使用整数分，禁止浮点金额。")
        result[key] = raw
    return result


def build_project_evidence(
    *,
    record_ref: str,
    evidence: Mapping[str, Any],
    name_rules: Sequence[NameRule] = DEFAULT_NAME_RULES,
) -> dict[str, Any]:
    """Normalize one project record without mutating or overwriting its input."""

    if not isinstance(evidence, Mapping):
        raise ProjectIdentityError("EVIDENCE_MAPPING_REQUIRED", "项目证据必须是字段映射。")
    unknown = set(evidence) - set(COMPONENT_WEIGHTS_BPS)
    if unknown:
        raise ProjectIdentityError("UNKNOWN_EVIDENCE_COMPONENT", "项目证据包含未登记组件。")
    normalized: dict[str, Any] = {
        "contract_number": _normalize_contract_number(evidence.get("contract_number")),
        "project_name": None,
        "counterparty": None,
        "company_entity": None,
        "time_evidence": _normalize_date_map(evidence.get("time_evidence")),
        "amount_evidence": _normalize_amount_map(evidence.get("amount_evidence")),
        "responsible_person": _normalize_simple_text(evidence.get("responsible_person")),
        "source_version": _normalize_simple_text(evidence.get("source_version")),
    }
    for field in ("project_name", "counterparty", "company_entity"):
        raw = evidence.get(field)
        if raw is not None and str(raw).strip() != "":
            normalized[field] = normalize_name(str(raw), category=field, rules=name_rules)
    present = [
        key
        for key, value in normalized.items()
        if value not in (None, {}, "")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_ref": _require_text(record_ref, "record_ref"),
        "original_evidence": copy.deepcopy(dict(evidence)),
        "normalized_evidence": normalized,
        "present_components": present,
        "missing_components": [key for key in COMPONENT_WEIGHTS_BPS if key not in present],
        "original_evidence_preserved": True,
        "source_mutation_performed": False,
    }


def _comparable_value(profile: Mapping[str, Any], component: str) -> Any:
    value = profile["normalized_evidence"].get(component)
    if component in NAME_CATEGORIES and value:
        return value["standard_name"]
    return value


def _compare_group(
    authority: Mapping[str, Any],
    candidate: Mapping[str, Any],
    subweights: Mapping[str, int],
) -> dict[str, Any]:
    compared: list[str] = []
    matched: list[str] = []
    mismatched: list[str] = []
    available_weight = 0
    matched_weight = 0
    for field, weight in subweights.items():
        left = authority.get(field)
        right = candidate.get(field)
        if left is None or right is None:
            continue
        compared.append(field)
        available_weight += weight
        if left == right:
            matched.append(field)
            matched_weight += weight
        else:
            mismatched.append(field)
    if not compared:
        status = "unavailable"
    elif not mismatched:
        status = "match"
    elif matched:
        status = "partial_match"
    else:
        status = "mismatch"
    return {
        "status": status,
        "compared_fields": compared,
        "matched_fields": matched,
        "mismatched_fields": mismatched,
        "available_weight_bps": available_weight,
        "matched_weight_bps": matched_weight,
    }


def score_project_match(
    authority_profile: Mapping[str, Any],
    candidate_profile: Mapping[str, Any],
) -> dict[str, Any]:
    """Score two profiles and fail closed on weak or conflicting evidence."""

    comparisons: dict[str, dict[str, Any]] = {}
    for component, weight in COMPONENT_WEIGHTS_BPS.items():
        left = _comparable_value(authority_profile, component)
        right = _comparable_value(candidate_profile, component)
        if component == "time_evidence":
            comparison = _compare_group(left or {}, right or {}, TIME_SUBWEIGHTS_BPS)
        elif component == "amount_evidence":
            comparison = _compare_group(left or {}, right or {}, AMOUNT_SUBWEIGHTS_BPS)
        elif left is None or right is None:
            comparison = {
                "status": "unavailable",
                "available_weight_bps": 0,
                "matched_weight_bps": 0,
            }
        else:
            matched = left == right
            comparison = {
                "status": "match" if matched else "mismatch",
                "available_weight_bps": weight,
                "matched_weight_bps": weight if matched else 0,
            }
        comparisons[component] = comparison

    available_weight = sum(row["available_weight_bps"] for row in comparisons.values())
    matched_weight = sum(row["matched_weight_bps"] for row in comparisons.values())
    similarity = matched_weight * 10000 // available_weight if available_weight else 0
    matched_primary = sorted(
        component
        for component in PRIMARY_COMPONENTS
        if comparisons[component]["status"] == "match"
    )
    hard_conflicts = sorted(
        component
        for component in HARD_CONFLICT_COMPONENTS
        if comparisons[component]["status"] == "mismatch"
    )
    matched_components = sorted(
        component
        for component, row in comparisons.items()
        if row["matched_weight_bps"] > 0
    )
    mismatched_components = sorted(
        component
        for component, row in comparisons.items()
        if row["status"] in {"mismatch", "partial_match"}
    )
    missing_components = sorted(
        component
        for component, row in comparisons.items()
        if row["status"] == "unavailable"
    )
    amount_only = bool(matched_weight) and set(matched_components) <= {"amount_evidence"}
    reasons: list[str] = []
    if not available_weight:
        reasons.append("没有可比较证据。")
    if available_weight < MIN_AUTO_COVERAGE_BPS:
        reasons.append("可比较证据覆盖不足。")
    if similarity < AUTO_MATCH_SIMILARITY_BPS:
        reasons.append("综合相似度不足。")
    if not (set(matched_primary) & ANCHOR_COMPONENTS):
        reasons.append("合同号或项目名均未形成匹配锚点。")
    if len(matched_primary) < MIN_AUTO_PRIMARY_MATCH_COUNT:
        reasons.append("主要身份字段匹配数量不足。")
    if hard_conflicts:
        reasons.append("合同号或公司主体存在硬冲突。")
    if amount_only:
        reasons.append("金额只能辅助判断，不能单独决定项目身份。")

    manual_review = bool(reasons)
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_record_ref": authority_profile["record_ref"],
        "candidate_record_ref": candidate_profile["record_ref"],
        "component_comparisons": comparisons,
        "configured_weight_total_bps": sum(COMPONENT_WEIGHTS_BPS.values()),
        "available_weight_bps": available_weight,
        "matched_weight_bps": matched_weight,
        "renormalized_similarity_bps": similarity,
        "missing_weight_renormalized": available_weight < 10000,
        "matched_components": matched_components,
        "mismatched_components": mismatched_components,
        "missing_components": missing_components,
        "matched_primary_components": matched_primary,
        "hard_conflict_components": hard_conflicts,
        "amount_evidence_auxiliary_only": True,
        "amount_alone_decided_match": False,
        "manual_review_required": manual_review,
        "manual_review_reasons_zh": reasons,
        "match_decision": "MANUAL_CONFIRMATION" if manual_review else "AUTO_MATCH",
        "auto_merge_allowed": not manual_review,
        "source_mutation_performed": False,
    }


def _authority_fixture() -> dict[str, Any]:
    return {
        "contract_number": "HT-2026-001",
        "project_name": "星河能源系统改造项目",
        "counterparty": "北辰建设有限公司",
        "company_entity": "海岳工程有限公司",
        "time_evidence": {
            "occurrence_date": "2026-01-10",
            "start_date": "2026-02-01",
            "finish_date": "2026-06-30",
        },
        "amount_evidence": {
            "contract_amount_cents": 125000000,
            "settlement_amount_cents": 123000000,
            "invoice_amount_cents": 90000000,
        },
        "responsible_person": "张示例",
        "source_version": "SOURCE-V3",
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Return deterministic public-safe fixtures for all three S08-P1 tasks."""

    authority_values = _authority_fixture()
    authority = build_project_evidence(record_ref="SYN-AUTHORITY", evidence=authority_values)

    missing_contract_values = dict(authority_values)
    missing_contract_values.pop("contract_number")
    missing_contract_values["project_name"] = " 星河能源（系统） 改造项目 "
    missing_contract_values["counterparty"] = "北辰建设有限责任公司"
    missing_contract_values["company_entity"] = "海岳工程有限责任公司"
    missing_contract = build_project_evidence(record_ref="SYN-MISSING-CONTRACT", evidence=missing_contract_values)

    low_coverage_values = {
        key: authority_values[key]
        for key in ("project_name", "counterparty", "company_entity", "time_evidence")
    }
    low_coverage = build_project_evidence(record_ref="SYN-LOW-COVERAGE", evidence=low_coverage_values)

    time_amount_conflict_values = dict(missing_contract_values)
    time_amount_conflict_values["time_evidence"] = {
        "occurrence_date": "2025-01-10",
        "start_date": "2025-02-01",
        "finish_date": "2025-06-30",
    }
    time_amount_conflict_values["amount_evidence"] = {
        "contract_amount_cents": 225000000,
        "settlement_amount_cents": 223000000,
        "invoice_amount_cents": 190000000,
    }
    time_amount_conflict = build_project_evidence(
        record_ref="SYN-TIME-AMOUNT-CONFLICT", evidence=time_amount_conflict_values
    )

    company_conflict_values = dict(authority_values)
    company_conflict_values["company_entity"] = "云岚工程有限公司"
    company_conflict = build_project_evidence(record_ref="SYN-COMPANY-CONFLICT", evidence=company_conflict_values)

    amount_only_values = {"amount_evidence": dict(authority_values["amount_evidence"])}
    amount_only_authority = build_project_evidence(record_ref="SYN-AMOUNT-ONLY-A", evidence=amount_only_values)
    amount_only_candidate = build_project_evidence(record_ref="SYN-AMOUNT-ONLY-B", evidence=amount_only_values)

    name_inputs = (
        ("project_name", " 星河能源（系统） 改造项目 "),
        ("project_name", "星河改造"),
        ("project_name", "星河能原系统改造项目"),
        ("project_name", "星河能源一期升级工程"),
        ("counterparty", "北辰建设有限责任公司"),
        ("project_name", "ＡＬＰＨＡ 项目"),
    )
    name_fixtures = [normalize_name(raw, category=category) for category, raw in name_inputs]
    matches = {
        "missing_contract_renormalized": score_project_match(authority, missing_contract),
        "low_coverage_fail_closed": score_project_match(authority, low_coverage),
        "same_name_time_amount_conflict": score_project_match(authority, time_amount_conflict),
        "company_conflict": score_project_match(authority, company_conflict),
        "amount_only": score_project_match(amount_only_authority, amount_only_candidate),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "component_weights_bps": dict(COMPONENT_WEIGHTS_BPS),
        "configured_weight_total_bps": sum(COMPONENT_WEIGHTS_BPS.values()),
        "decision_policy": {
            "auto_match_similarity_bps": AUTO_MATCH_SIMILARITY_BPS,
            "minimum_auto_coverage_bps": MIN_AUTO_COVERAGE_BPS,
            "minimum_auto_primary_match_count": MIN_AUTO_PRIMARY_MATCH_COUNT,
            "hard_conflict_components": sorted(HARD_CONFLICT_COMPONENTS),
            "amount_evidence_auxiliary_only": True,
        },
        "name_fixtures": name_fixtures,
        "match_cases": matches,
    }
