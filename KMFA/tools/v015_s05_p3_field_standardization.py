#!/usr/bin/env python3
"""KMFA v1.5 S05-P3 public-safe field standardization contracts.

The module defines a deterministic standard field dictionary, versioned alias
rules with curated confidence, and fail-closed value semantics.  It never
reads source workbooks or the private raw inbox.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable


RUN_PHASE_ID = "V015_S05_P3_FIELD_STANDARDIZATION"
TASK_ID = "KMFA-V015-S05-P3-FIELD-STANDARDIZATION-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S05-P3-FIELD-STANDARDIZATION"
VERSION = "1.5.0-dev-s05p3"
DICTIONARY_VERSION = "1.0.0"
MAPPING_VERSION = "1.0.0"

DOMAINS = (
    "PROJECT",
    "CUSTOMER",
    "CONTRACT",
    "COST",
    "INVOICE",
    "COLLECTION",
    "ACCOUNT",
    "POLICY",
)
DATA_TYPES = {"OPAQUE_TEXT", "NORMALIZED_TEXT", "STATUS_CODE", "INTEGER_CENTS", "ISO_DATE", "VERSION_TEXT"}
UNITS = {"NONE", "CNY_CENT", "DAY", "VERSION_TAG"}
SOURCE_CLASSES = {
    "PROJECT_MASTER",
    "CUSTOMER_MASTER",
    "CONTRACT_REGISTER",
    "COST_REGISTER",
    "INVOICE_REGISTER",
    "COLLECTION_REGISTER",
    "ACCOUNT_MASTER",
    "POLICY_REGISTER",
}
ALIAS_TYPES = {"CANONICAL", "ABBREVIATION", "TYPO", "HISTORICAL", "TEMPLATE_VARIANT"}


class FieldContractError(ValueError):
    """A stable fail-closed error for dictionary or mapping contract failures."""

    def __init__(self, code: str, message: str, action: str = "QUALITY_QUEUE") -> None:
        super().__init__(message)
        self.code = code
        self.action = action


@dataclass(frozen=True)
class FieldDefinition:
    field_id: str
    domain: str
    canonical_name: str
    chinese_name: str
    definition_zh: str
    data_type: str
    unit: str
    source_classes: tuple[str, ...]
    required_when: str
    storage_format: str
    display_format: str
    critical: bool
    version: str = DICTIONARY_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "domain": self.domain,
            "canonical_name": self.canonical_name,
            "chinese_name": self.chinese_name,
            "definition_zh": self.definition_zh,
            "data_type": self.data_type,
            "unit": self.unit,
            "source_classes": list(self.source_classes),
            "required_when": self.required_when,
            "storage_format": self.storage_format,
            "display_format": self.display_format,
            "critical": self.critical,
            "version": self.version,
        }


def _field(
    field_id: str,
    domain: str,
    chinese_name: str,
    definition_zh: str,
    data_type: str,
    unit: str,
    source_class: str,
    required_when: str,
    storage_format: str,
    display_format: str,
    critical: bool,
) -> FieldDefinition:
    return FieldDefinition(
        field_id=field_id,
        domain=domain,
        canonical_name=field_id,
        chinese_name=chinese_name,
        definition_zh=definition_zh,
        data_type=data_type,
        unit=unit,
        source_classes=(source_class,),
        required_when=required_when,
        storage_format=storage_format,
        display_format=display_format,
        critical=critical,
    )


STANDARD_FIELDS = (
    _field("project_id", "PROJECT", "项目标识", "在 KMFA 内稳定且不承载业务含义的项目标识。", "OPAQUE_TEXT", "NONE", "PROJECT_MASTER", "每条项目主记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("project_name", "PROJECT", "项目名称", "经去除异常空白后的项目正式名称。", "NORMALIZED_TEXT", "NONE", "PROJECT_MASTER", "项目进入业务流程时必填", "NFKC_TRIMMED_TEXT", "TEXT", False),
    _field("project_status", "PROJECT", "项目状态", "项目在受控生命周期中的当前状态代码。", "STATUS_CODE", "NONE", "PROJECT_MASTER", "项目已登记时必填", "UPPER_SNAKE_CASE", "STATUS_LABEL", False),
    _field("customer_id", "CUSTOMER", "客户标识", "在 KMFA 内稳定且不承载业务含义的客户标识。", "OPAQUE_TEXT", "NONE", "CUSTOMER_MASTER", "每条客户主记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("customer_name", "CUSTOMER", "客户名称", "经去除异常空白后的客户正式名称。", "NORMALIZED_TEXT", "NONE", "CUSTOMER_MASTER", "客户参与合同时必填", "NFKC_TRIMMED_TEXT", "TEXT", False),
    _field("customer_status", "CUSTOMER", "客户状态", "客户在受控生命周期中的当前状态代码。", "STATUS_CODE", "NONE", "CUSTOMER_MASTER", "客户已登记时必填", "UPPER_SNAKE_CASE", "STATUS_LABEL", False),
    _field("contract_id", "CONTRACT", "合同标识", "在 KMFA 内稳定且不承载业务含义的合同标识。", "OPAQUE_TEXT", "NONE", "CONTRACT_REGISTER", "每条合同记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("contract_number", "CONTRACT", "合同编号", "由业务确认并按原字符语义保存的合同编号。", "OPAQUE_TEXT", "NONE", "CONTRACT_REGISTER", "正式合同记录必填", "NFKC_NO_WHITESPACE", "AS_STORED", True),
    _field("contract_amount_cents", "CONTRACT", "合同金额分", "合同含税或不含税口径明确后的整数分金额。", "INTEGER_CENTS", "CNY_CENT", "CONTRACT_REGISTER", "合同金额口径已确认时必填", "SIGNED_INTEGER_CENTS", "CNY_2DP", True),
    _field("cost_id", "COST", "成本标识", "在 KMFA 内稳定且不承载业务含义的成本记录标识。", "OPAQUE_TEXT", "NONE", "COST_REGISTER", "每条成本记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("cost_category", "COST", "成本类别", "成本在受控分类字典中的类别代码。", "STATUS_CODE", "NONE", "COST_REGISTER", "成本进入核算时必填", "UPPER_SNAKE_CASE", "CATEGORY_LABEL", False),
    _field("cost_amount_cents", "COST", "成本金额分", "按已确认成本口径保存的整数分金额。", "INTEGER_CENTS", "CNY_CENT", "COST_REGISTER", "成本进入核算时必填", "SIGNED_INTEGER_CENTS", "CNY_2DP", True),
    _field("invoice_id", "INVOICE", "发票标识", "在 KMFA 内稳定且不承载业务含义的发票记录标识。", "OPAQUE_TEXT", "NONE", "INVOICE_REGISTER", "每条发票记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("invoice_date", "INVOICE", "开票日期", "依据已登记日期口径标准化的发票开具日期。", "ISO_DATE", "DAY", "INVOICE_REGISTER", "已开票记录必填", "YYYY-MM-DD", "YYYY-MM-DD", True),
    _field("invoice_amount_cents", "INVOICE", "发票金额分", "按已确认发票口径保存的整数分金额。", "INTEGER_CENTS", "CNY_CENT", "INVOICE_REGISTER", "已开票记录必填", "SIGNED_INTEGER_CENTS", "CNY_2DP", True),
    _field("collection_id", "COLLECTION", "回款标识", "在 KMFA 内稳定且不承载业务含义的回款记录标识。", "OPAQUE_TEXT", "NONE", "COLLECTION_REGISTER", "每条回款记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("collection_date", "COLLECTION", "回款日期", "依据已登记日期口径标准化的到账日期。", "ISO_DATE", "DAY", "COLLECTION_REGISTER", "已到账记录必填", "YYYY-MM-DD", "YYYY-MM-DD", True),
    _field("collection_amount_cents", "COLLECTION", "回款金额分", "按已确认到账口径保存的整数分金额。", "INTEGER_CENTS", "CNY_CENT", "COLLECTION_REGISTER", "已到账记录必填", "SIGNED_INTEGER_CENTS", "CNY_2DP", True),
    _field("account_id", "ACCOUNT", "账户标识", "在 KMFA 内稳定且不暴露账号明文的账户标识。", "OPAQUE_TEXT", "NONE", "ACCOUNT_MASTER", "每条账户主记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("account_name", "ACCOUNT", "账户名称", "经去除异常空白后的账户展示名称。", "NORMALIZED_TEXT", "NONE", "ACCOUNT_MASTER", "账户进入资金视图时必填", "NFKC_TRIMMED_TEXT", "TEXT", False),
    _field("account_status", "ACCOUNT", "账户状态", "账户在受控生命周期中的当前状态代码。", "STATUS_CODE", "NONE", "ACCOUNT_MASTER", "账户已登记时必填", "UPPER_SNAKE_CASE", "STATUS_LABEL", False),
    _field("policy_id", "POLICY", "政策标识", "在 KMFA 内稳定且不承载政策内容的政策标识。", "OPAQUE_TEXT", "NONE", "POLICY_REGISTER", "每条政策记录必填", "OPAQUE_TEXT", "AS_STORED", True),
    _field("policy_name", "POLICY", "政策名称", "经去除异常空白后的政策正式名称。", "NORMALIZED_TEXT", "NONE", "POLICY_REGISTER", "政策启用时必填", "NFKC_TRIMMED_TEXT", "TEXT", False),
    _field("policy_version", "POLICY", "政策版本", "用于绑定政策生效内容的显式版本标识。", "VERSION_TEXT", "VERSION_TAG", "POLICY_REGISTER", "政策启用时必填", "VERSION_TEXT", "VERSION_TEXT", True),
)


def validate_field_dictionary(fields: Iterable[FieldDefinition] = STANDARD_FIELDS) -> tuple[FieldDefinition, ...]:
    values = tuple(fields)
    ids: set[str] = set()
    names: set[str] = set()
    domains: set[str] = set()
    for item in values:
        if item.field_id in ids or item.canonical_name in names:
            raise FieldContractError("DUPLICATE_FIELD", f"duplicate field: {item.field_id}")
        ids.add(item.field_id)
        names.add(item.canonical_name)
        domains.add(item.domain)
        if item.domain not in DOMAINS or item.data_type not in DATA_TYPES or item.unit not in UNITS:
            raise FieldContractError("INVALID_FIELD_CONTRACT", f"invalid contract for {item.field_id}")
        if not item.source_classes or any(source not in SOURCE_CLASSES for source in item.source_classes):
            raise FieldContractError("INVALID_FIELD_SOURCE", f"invalid source class for {item.field_id}")
        required = (item.chinese_name, item.definition_zh, item.required_when, item.storage_format, item.display_format, item.version)
        if any(not value.strip() for value in required) or not re.search(r"[\u4e00-\u9fff]", item.definition_zh):
            raise FieldContractError("INCOMPLETE_FIELD_DEFINITION", f"incomplete definition: {item.field_id}")
        if item.data_type == "INTEGER_CENTS" and (item.unit != "CNY_CENT" or item.storage_format != "SIGNED_INTEGER_CENTS"):
            raise FieldContractError("INVALID_AMOUNT_FORMAT", f"invalid amount format: {item.field_id}")
        if item.data_type == "ISO_DATE" and (item.unit != "DAY" or item.storage_format != "YYYY-MM-DD"):
            raise FieldContractError("INVALID_DATE_FORMAT", f"invalid date format: {item.field_id}")
    if domains != set(DOMAINS):
        raise FieldContractError("MISSING_DOMAIN", "all eight field domains must be defined")
    if any(field.critical and not field.definition_zh for field in values):
        raise FieldContractError("UNDEFINED_CRITICAL_FIELD", "critical fields require definitions")
    return values


FIELD_BY_ID = {field.field_id: field for field in validate_field_dictionary()}


def normalize_alias_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    return re.sub(r"[\s_\-—–/／\\:：,，.。()（）\[\]【】]+", "", text)


@dataclass(frozen=True)
class AliasRule:
    alias_id: str
    alias_text: str
    canonical_field_id: str
    template_class: str
    alias_type: str
    confidence_bps: int
    version: str = MAPPING_VERSION
    effective_from: str = "2026-07-15"
    evidence_level: str = "CURATED_PUBLIC_SAFE"

    @property
    def alias_key(self) -> str:
        return normalize_alias_key(self.alias_text)

    @property
    def confidence_band(self) -> str:
        if self.confidence_bps >= 9900:
            return "EXACT"
        if self.confidence_bps >= 8000:
            return "REVIEW"
        return "BLOCKED"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "alias_id": self.alias_id,
            "alias_text": self.alias_text,
            "alias_key": self.alias_key,
            "canonical_field_id": self.canonical_field_id,
            "template_class": self.template_class,
            "alias_type": self.alias_type,
            "confidence_bps": self.confidence_bps,
            "confidence_band": self.confidence_band,
            "version": self.version,
            "effective_from": self.effective_from,
            "evidence_level": self.evidence_level,
        }


_BASE_ALIASES = (
    ("项目编码", "project_id"), ("项目名称", "project_name"), ("项目状态", "project_status"),
    ("客户编码", "customer_id"), ("客户名称", "customer_name"), ("客户状态", "customer_status"),
    ("合同标识", "contract_id"), ("合同编号", "contract_number"), ("合同金额分", "contract_amount_cents"),
    ("成本标识", "cost_id"), ("成本类别", "cost_category"), ("成本金额分", "cost_amount_cents"),
    ("发票标识", "invoice_id"), ("开票日期", "invoice_date"), ("发票金额分", "invoice_amount_cents"),
    ("回款标识", "collection_id"), ("回款日期", "collection_date"), ("回款金额分", "collection_amount_cents"),
    ("账户标识", "account_id"), ("账户名称", "account_name"), ("账户状态", "account_status"),
    ("政策标识", "policy_id"), ("政策名称", "policy_name"), ("政策版本", "policy_version"),
)

ALIAS_RULES = tuple(
    AliasRule(f"ALIAS-S05P3-{index:03d}", alias, field_id, "GENERIC", "CANONICAL", 10000)
    for index, (alias, field_id) in enumerate(_BASE_ALIASES, start=1)
) + (
    AliasRule("ALIAS-S05P3-025", "项目号", "project_id", "PROJECT_REGISTER", "ABBREVIATION", 9950),
    AliasRule("ALIAS-S05P3-026", "客商名称", "customer_name", "CUSTOMER_MASTER", "HISTORICAL", 9000),
    AliasRule("ALIAS-S05P3-027", "合同編号", "contract_number", "CONTRACT_REGISTER", "TYPO", 9000),
    AliasRule("ALIAS-S05P3-028", "含税金额", "contract_amount_cents", "CONTRACT_REGISTER", "TEMPLATE_VARIANT", 8500),
    AliasRule("ALIAS-S05P3-029", "成本额", "cost_amount_cents", "COST_REGISTER", "ABBREVIATION", 9500),
    AliasRule("ALIAS-S05P3-030", "开票日", "invoice_date", "INVOICE_REGISTER", "ABBREVIATION", 9950),
    AliasRule("ALIAS-S05P3-031", "收款金额", "collection_amount_cents", "COLLECTION_REGISTER", "HISTORICAL", 9950),
    AliasRule("ALIAS-S05P3-032", "政策版本号", "policy_version", "POLICY_REGISTER", "TEMPLATE_VARIANT", 9950),
    AliasRule("ALIAS-S05P3-033", "金额", "contract_amount_cents", "CONTRACT_REGISTER", "TEMPLATE_VARIANT", 9900),
    AliasRule("ALIAS-S05P3-034", "金额", "cost_amount_cents", "COST_REGISTER", "TEMPLATE_VARIANT", 9900),
    AliasRule("ALIAS-S05P3-035", "金额", "invoice_amount_cents", "INVOICE_REGISTER", "TEMPLATE_VARIANT", 9900),
    AliasRule("ALIAS-S05P3-036", "金额", "collection_amount_cents", "COLLECTION_REGISTER", "TEMPLATE_VARIANT", 9900),
)


@dataclass(frozen=True)
class MappingDecision:
    status: str
    alias_key: str
    canonical_field_id: str | None
    rule_id: str | None
    confidence_bps: int | None
    confidence_band: str | None
    version: str
    action: str

    def to_public_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class AliasRegistry:
    def __init__(self, rules: Iterable[AliasRule] = ALIAS_RULES) -> None:
        self.rules = tuple(rules)
        self._index: dict[tuple[str, str, str], AliasRule] = {}
        for rule in self.rules:
            if rule.canonical_field_id not in FIELD_BY_ID or rule.alias_type not in ALIAS_TYPES:
                raise FieldContractError("INVALID_ALIAS_RULE", f"invalid alias rule: {rule.alias_id}")
            if not rule.alias_key or not 0 <= rule.confidence_bps <= 10000:
                raise FieldContractError("INVALID_ALIAS_RULE", f"invalid alias rule: {rule.alias_id}")
            key = (rule.version, rule.template_class, rule.alias_key)
            existing = self._index.get(key)
            if existing and existing.canonical_field_id != rule.canonical_field_id:
                raise FieldContractError("ALIAS_COLLISION", f"alias collision: {rule.alias_text}", "MANUAL_CONFIRMATION")
            self._index[key] = rule

    def resolve(self, alias: Any, *, template_class: str | None = None, version: str = MAPPING_VERSION) -> MappingDecision:
        key = normalize_alias_key(alias)
        if not key:
            raise FieldContractError("BLANK_ALIAS", "field alias is blank", "QUALITY_QUEUE")
        matches = [rule for rule in self.rules if rule.version == version and rule.alias_key == key]
        if template_class:
            selected = self._index.get((version, template_class, key)) or self._index.get((version, "GENERIC", key))
        else:
            generic = self._index.get((version, "GENERIC", key))
            selected = generic if generic else (matches[0] if len(matches) == 1 else None)
        if selected is None:
            status = "AMBIGUOUS" if len({rule.canonical_field_id for rule in matches}) > 1 else "UNREGISTERED"
            action = "MANUAL_CONFIRMATION" if status == "AMBIGUOUS" else "QUALITY_QUEUE"
            return MappingDecision(status, key, None, None, None, None, version, action)
        status = "AUTO_MAPPED" if selected.confidence_band == "EXACT" else (
            "MANUAL_CONFIRMATION" if selected.confidence_band == "REVIEW" else "BLOCKED"
        )
        action = "ACCEPT" if status == "AUTO_MAPPED" else (
            "MANUAL_CONFIRMATION" if status == "MANUAL_CONFIRMATION" else "QUALITY_QUEUE"
        )
        return MappingDecision(
            status, key, selected.canonical_field_id, selected.alias_id,
            selected.confidence_bps, selected.confidence_band, version, action,
        )


class ValueSemantic(str, Enum):
    PRESENT = "PRESENT"
    ZERO = "ZERO"
    BLANK = "BLANK"
    DASH = "DASH"
    UNKNOWN_VALUE = "UNKNOWN_VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PARSE_FAILED = "PARSE_FAILED"


SPECIAL_VALUE_SEMANTICS = {
    ValueSemantic.ZERO: "已观测到的数值零，不等于缺失。",
    ValueSemantic.BLANK: "空值或仅含空白，必须进入质量队列。",
    ValueSemantic.DASH: "横线占位符，含义未确认前不得派生。",
    ValueSemantic.UNKNOWN_VALUE: "来源明确声明未知，不得猜测或转零。",
    ValueSemantic.NOT_APPLICABLE: "字段不适用，不是零且不得参与数值派生。",
    ValueSemantic.PARSE_FAILED: "存在原始表示但解析失败，必须阻断派生。",
}


@dataclass(frozen=True)
class ClassifiedValue:
    field_id: str
    semantic: ValueSemantic
    normalized_value: Any
    derivation_allowed: bool
    action: str
    is_zero: bool

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "semantic": self.semantic.value,
            "normalized_value": self.normalized_value,
            "derivation_allowed": self.derivation_allowed,
            "action": self.action,
            "is_zero": self.is_zero,
        }


_DASH_MARKERS = {"-", "--", "---", "—", "–"}
_UNKNOWN_MARKERS = {"未知", "不详", "unknown"}
_NOT_APPLICABLE_MARKERS = {"不适用", "n/a", "na", "not applicable"}


def _special(field_id: str, semantic: ValueSemantic, action: str = "BLOCK_DERIVATION") -> ClassifiedValue:
    return ClassifiedValue(field_id, semantic, None, False, action, False)


def classify_value(field_id: str, value: Any, *, parse_failed: bool = False) -> ClassifiedValue:
    field = FIELD_BY_ID.get(field_id)
    if field is None:
        raise FieldContractError("UNDEFINED_FIELD", f"field is not defined: {field_id}", "BLOCK_DERIVATION")
    if parse_failed:
        return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
    if value is None:
        return _special(field_id, ValueSemantic.BLANK, "QUALITY_QUEUE")
    if isinstance(value, bool):
        return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")

    text = unicodedata.normalize("NFKC", str(value)).strip()
    marker = re.sub(r"\s+", " ", text).casefold()
    if not marker:
        return _special(field_id, ValueSemantic.BLANK, "QUALITY_QUEUE")
    if marker in _DASH_MARKERS:
        return _special(field_id, ValueSemantic.DASH)
    if marker in _UNKNOWN_MARKERS:
        return _special(field_id, ValueSemantic.UNKNOWN_VALUE, "MANUAL_CONFIRMATION")
    if marker in _NOT_APPLICABLE_MARKERS:
        return _special(field_id, ValueSemantic.NOT_APPLICABLE)

    if field.data_type == "INTEGER_CENTS":
        if isinstance(value, float):
            return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
        try:
            number = Decimal(text) if not isinstance(value, (int, Decimal)) else Decimal(value)
        except Exception:
            return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
        if not number.is_finite() or number != number.to_integral_value():
            return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
        cents = int(number)
        semantic = ValueSemantic.ZERO if cents == 0 else ValueSemantic.PRESENT
        return ClassifiedValue(field_id, semantic, cents, True, "ACCEPT", cents == 0)

    if field.data_type == "ISO_DATE":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
        try:
            date.fromisoformat(text)
        except ValueError:
            return _special(field_id, ValueSemantic.PARSE_FAILED, "QUALITY_QUEUE")
        return ClassifiedValue(field_id, ValueSemantic.PRESENT, text, True, "ACCEPT", False)

    normalized = re.sub(r"\s+", " ", text)
    if field.data_type == "STATUS_CODE":
        normalized = normalized.upper().replace(" ", "_")
    return ClassifiedValue(field_id, ValueSemantic.PRESENT, normalized, True, "ACCEPT", False)


def semantic_contract() -> list[dict[str, Any]]:
    return [
        {
            "semantic": semantic.value,
            "definition_zh": definition,
            "normalized_to_zero": semantic is ValueSemantic.ZERO,
            "derivation_allowed": semantic is ValueSemantic.ZERO,
            "default_action": "ACCEPT" if semantic is ValueSemantic.ZERO else "BLOCK_DERIVATION",
        }
        for semantic, definition in SPECIAL_VALUE_SEMANTICS.items()
    ]
