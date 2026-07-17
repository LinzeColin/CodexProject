#!/usr/bin/env python3
"""KMFA v1.5 S10-P2 versioned file-source adapters.

The module sits after S10-P1 safe file inspection. It requires an explicit
source template and mapping version, maps headers without guessing, preserves
source hierarchy on every adapted record, and quarantines ambiguous sheets or
rows without mutating the source.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


VERSION = "1.5.0-dev-s10p2"
RUN_PHASE_ID = "V015_S10_P2_SOURCE_ADAPTERS"
ROADMAP_PHASE_ID = "S10-P2"
TASK_ID = "KMFA-V015-S10-P2-SOURCE-ADAPTERS-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S10-P2-SOURCE-ADAPTERS"

SOURCE_SYSTEM_LABELS_ZH = {
    "REDCIRCLE": "红圈",
    "KINGDEE": "金蝶",
    "WPS": "WPS",
    "BANK": "银行",
    "TAX_EINVOICE": "税务/数电票",
    "CONTRACT_LEDGER": "合同台账",
}

FILE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PERIOD_RE = re.compile(r"^\d{4}(?:-(?:0[1-9]|1[0-2]))?$")
OPAQUE_ID_RE = re.compile(r"^(?:ENTITY|BANK|ACCOUNT)::[A-Z0-9][A-Z0-9_-]{1,63}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_INSPECTION_FORMATS = {"EXCEL_XLSX", "EXCEL_XLS", "CSV", "WPS_OLE"}
FORBIDDEN_PLACEHOLDER_TOKENS = ("TO_BE_", "UNKNOWN", "待确认", "不明")


class SourceAdapterError(RuntimeError):
    def __init__(self, code: str, detail_zh: str):
        super().__init__(f"{code}: {detail_zh}")
        self.code = code
        self.detail_zh = detail_zh


@dataclass(frozen=True)
class FieldSpec:
    canonical_field: str
    aliases: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class TemplateSpec:
    template_id: str
    source_system: str
    export_type: str
    mapping_version: str
    fields: tuple[FieldSpec, ...]
    required_context: tuple[str, ...] = ("entity_id", "period")


@dataclass(frozen=True)
class MappingPlan:
    template: TemplateSpec
    header_by_canonical: Mapping[str, str]
    public_summary: Mapping[str, Any]


def _f(canonical_field: str, *aliases: str, required: bool = True) -> FieldSpec:
    return FieldSpec(canonical_field, tuple(aliases), required)


def _t(
    template_id: str,
    source_system: str,
    export_type: str,
    fields: Sequence[FieldSpec],
    *,
    required_context: Sequence[str] = ("entity_id", "period"),
) -> TemplateSpec:
    return TemplateSpec(
        template_id=template_id,
        source_system=source_system,
        export_type=export_type,
        mapping_version="1.0.0",
        fields=tuple(fields),
        required_context=tuple(required_context),
    )


TEMPLATES = (
    _t(
        "redcircle.operating.v1",
        "REDCIRCLE",
        "operating",
        (
            _f("project_ref", "项目编号", "项目编码", "项目ID"),
            _f("project_name", "项目名称", "项目名"),
            _f("revenue_amount", "收入金额", "营业收入", required=False),
            _f("cost_amount", "成本金额", "营业成本", required=False),
        ),
    ),
    _t(
        "redcircle.contract.v1",
        "REDCIRCLE",
        "contract",
        (
            _f("contract_ref", "合同编号", "合同编码", "合同号"),
            _f("project_ref", "项目编号", "项目编码", required=False),
            _f("counterparty_ref", "客户编号", "对方单位编码", "相对方编号"),
            _f("contract_amount", "合同金额", "含税合同额"),
            _f("sign_date", "签订日期", "合同签署日期", required=False),
        ),
    ),
    _t(
        "redcircle.collection.v1",
        "REDCIRCLE",
        "collection",
        (
            _f("collection_date", "回款日期", "收款日期"),
            _f("project_ref", "项目编号", "项目编码"),
            _f("payer_ref", "付款方编号", "客户编号", "付款单位编码"),
            _f("collection_amount", "回款金额", "收款金额"),
            _f("account_ref", "收款账户编号", "银行账户编号", required=False),
        ),
    ),
    _t(
        "redcircle.finance.v1",
        "REDCIRCLE",
        "finance",
        (
            _f("voucher_ref", "凭证号", "凭证编号"),
            _f("transaction_date", "记账日期", "业务日期"),
            _f("account_subject", "会计科目", "科目名称"),
            _f("debit_amount", "借方金额", "借方"),
            _f("credit_amount", "贷方金额", "贷方"),
        ),
    ),
    _t(
        "kingdee.balance.v1",
        "KINGDEE",
        "balance",
        (
            _f("account_code", "科目编码", "科目代码"),
            _f("account_name", "科目名称", "会计科目"),
            _f("opening_balance", "期初余额"),
            _f("period_debit", "本期借方", "借方发生额"),
            _f("period_credit", "本期贷方", "贷方发生额"),
            _f("closing_balance", "期末余额"),
        ),
    ),
    _t(
        "kingdee.voucher.v1",
        "KINGDEE",
        "voucher",
        (
            _f("voucher_date", "凭证日期", "记账日期"),
            _f("voucher_ref", "凭证号", "凭证字号"),
            _f("account_code", "科目编码", "科目代码"),
            _f("account_name", "科目名称", "会计科目"),
            _f("debit_amount", "借方金额", "借方"),
            _f("credit_amount", "贷方金额", "贷方"),
            _f("summary", "摘要", "凭证摘要", required=False),
        ),
    ),
    _t(
        "kingdee.counterparty.v1",
        "KINGDEE",
        "counterparty",
        (
            _f("counterparty_ref", "往来单位编码", "核算项目编码"),
            _f("counterparty_name", "往来单位名称", "核算项目名称"),
            _f("opening_balance", "期初余额"),
            _f("period_debit", "本期借方", "借方发生额"),
            _f("period_credit", "本期贷方", "贷方发生额"),
            _f("closing_balance", "期末余额"),
        ),
    ),
    _t(
        "kingdee.report.v1",
        "KINGDEE",
        "report",
        (
            _f("report_item", "报表项目", "项目名称"),
            _f("current_amount", "本期金额", "本期数"),
            _f("prior_amount", "上期金额", "上期数", required=False),
        ),
    ),
    _t(
        "wps.collection.v1",
        "WPS",
        "collection",
        (
            _f("collection_date", "回款日期", "收款日期"),
            _f("project_ref", "项目编号", "项目编码"),
            _f("customer_ref", "客户编号", "客户编码"),
            _f("collection_amount", "回款金额", "收款金额"),
            _f("receipt_status", "回款状态", "收款状态", required=False),
        ),
    ),
    _t(
        "wps.receivable-aging.v1",
        "WPS",
        "receivable_aging",
        (
            _f("customer_ref", "客户编号", "客户编码"),
            _f("project_ref", "项目编号", "项目编码"),
            _f("receivable_amount", "应收金额", "应收余额"),
            _f("aging_bucket", "账龄区间", "账龄"),
            _f("overdue_days", "逾期天数", required=False),
        ),
    ),
    _t(
        "wps.project-status.v1",
        "WPS",
        "production_project_status",
        (
            _f("project_ref", "项目编号", "项目编码"),
            _f("production_status", "生产状态", "项目状态"),
            _f("planned_finish_date", "计划完成日期", "计划完工日期"),
            _f("actual_progress_rate", "实际进度", "完成比例"),
            _f("responsible_team_ref", "责任团队编号", "负责部门编码", required=False),
        ),
    ),
    _t(
        "wps.deposit.v1",
        "WPS",
        "deposit",
        (
            _f("deposit_ref", "押金编号", "保证金编号"),
            _f("project_ref", "项目编号", "项目编码"),
            _f("counterparty_ref", "相对方编号", "客户编号"),
            _f("deposit_amount", "押金金额", "保证金金额"),
            _f("deposit_status", "押金状态", "保证金状态", required=False),
        ),
    ),
    _t(
        "bank.statement.v1",
        "BANK",
        "statement",
        (
            _f("transaction_date", "交易日期", "记账日期"),
            _f("counterparty_ref", "对方户名", "交易对手", "对方名称"),
            _f("income_amount", "收入金额", "贷方发生额"),
            _f("expense_amount", "支出金额", "借方发生额"),
            _f("balance_amount", "账户余额", "余额"),
            _f("transaction_ref", "交易流水号", "银行流水号", required=False),
        ),
        required_context=("entity_id", "bank_id", "account_id", "period"),
    ),
    _t(
        "tax-einvoice.invoice.v1",
        "TAX_EINVOICE",
        "invoice",
        (
            _f("invoice_ref", "发票号码", "数电票号码"),
            _f("invoice_date", "开票日期", "发票日期"),
            _f("seller_ref", "销售方税号", "销方识别号"),
            _f("buyer_ref", "购买方税号", "购方识别号"),
            _f("amount_ex_tax", "不含税金额", "金额"),
            _f("tax_amount", "税额"),
            _f("total_amount", "价税合计", "含税金额"),
        ),
    ),
    _t(
        "contract-ledger.contract.v1",
        "CONTRACT_LEDGER",
        "contract",
        (
            _f("contract_ref", "合同编号", "合同号"),
            _f("counterparty_ref", "相对方编号", "合同对方编码"),
            _f("sign_date", "签订日期", "合同日期"),
            _f("contract_amount", "合同金额", "含税合同额"),
            _f("project_ref", "项目编号", "项目编码", required=False),
        ),
    ),
)

TEMPLATE_BY_ID = {template.template_id: template for template in TEMPLATES}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_header(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"[\s_\-—–:：/\\]+", "", text).casefold()


def _require_text(value: Any, code: str, detail_zh: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SourceAdapterError(code, detail_zh)
    return text


def _placeholder(value: str) -> bool:
    upper = value.upper()
    return any(token.upper() in upper for token in FORBIDDEN_PLACEHOLDER_TOKENS)


def validate_template_registry() -> dict[str, int]:
    if len(TEMPLATE_BY_ID) != len(TEMPLATES):
        raise SourceAdapterError("DUPLICATE_TEMPLATE_ID", "来源模板编号必须唯一。")
    counts = {system: 0 for system in SOURCE_SYSTEM_LABELS_ZH}
    for template in TEMPLATES:
        if template.source_system not in counts:
            raise SourceAdapterError("UNKNOWN_TEMPLATE_SOURCE_SYSTEM", "来源模板使用了未知系统。")
        if not SEMVER_RE.fullmatch(template.mapping_version):
            raise SourceAdapterError("MAPPING_VERSION_INVALID", "字段映射版本必须为三段数字。")
        counts[template.source_system] += 1
        seen_aliases: dict[str, str] = {}
        seen_fields: set[str] = set()
        for field in template.fields:
            if field.canonical_field in seen_fields:
                raise SourceAdapterError("DUPLICATE_CANONICAL_FIELD", "同一模板不能重复定义标准字段。")
            seen_fields.add(field.canonical_field)
            if not field.aliases:
                raise SourceAdapterError("EMPTY_FIELD_ALIASES", "每个字段必须至少登记一个明确表头。")
            for alias in field.aliases:
                normalized = _normalize_header(alias)
                if not normalized:
                    raise SourceAdapterError("EMPTY_FIELD_ALIAS", "字段别名不能为空。")
                owner = seen_aliases.get(normalized)
                if owner and owner != field.canonical_field:
                    raise SourceAdapterError("AMBIGUOUS_REGISTERED_ALIAS", "同一表头不能映射到两个标准字段。")
                seen_aliases[normalized] = field.canonical_field
    expected = {"REDCIRCLE": 4, "KINGDEE": 4, "WPS": 4, "BANK": 1, "TAX_EINVOICE": 1, "CONTRACT_LEDGER": 1}
    if counts != expected:
        raise SourceAdapterError("TEMPLATE_COVERAGE_DRIFT", "来源模板覆盖数量与 S10-P2 合同不一致。")
    return counts


TEMPLATE_COUNTS = validate_template_registry()


def template_registry_public_safe() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p2.source_adapter_registry.v1",
        "source_system_count": len(SOURCE_SYSTEM_LABELS_ZH),
        "adapter_template_count": len(TEMPLATES),
        "mapping_versioned_template_count": len(TEMPLATES),
        "automatic_login_allowed": False,
        "live_connector_call_allowed": False,
        "credential_storage_allowed": False,
        "templates": [
            {
                "template_id": template.template_id,
                "source_system": template.source_system,
                "source_system_label_zh": SOURCE_SYSTEM_LABELS_ZH[template.source_system],
                "export_type": template.export_type,
                "mapping_version": template.mapping_version,
                "required_context": list(template.required_context),
                "fields": [
                    {
                        "canonical_field": field.canonical_field,
                        "aliases": list(field.aliases),
                        "required": field.required,
                    }
                    for field in template.fields
                ],
            }
            for template in TEMPLATES
        ],
    }


def mapping_version_policy_public_safe() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p2.mapping_version_policy.v1",
        "template_selection": "EXPLICIT_ONLY",
        "unknown_template_action": "QUARANTINE",
        "unknown_mapping_version_action": "QUARANTINE",
        "ambiguous_header_action": "QUARANTINE",
        "missing_required_header_action": "QUARANTINE",
        "unregistered_header_action": "RETAIN_AS_UNMAPPED_WITH_HASH_ONLY",
        "guess_field_meaning_allowed": False,
        "mapping_change_requires_new_version": True,
        "historical_mapping_replay_supported": True,
    }


def source_hierarchy_policy_public_safe() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p2.source_hierarchy_policy.v1",
        "base_required_context": ["source_system", "template_id", "mapping_version", "entity_id", "period", "sheet_id"],
        "bank_required_context": ["bank_id", "account_id"],
        "period_pattern": PERIOD_RE.pattern,
        "account_binding_required": True,
        "unknown_entity_action": "QUARANTINE",
        "unknown_bank_action": "QUARANTINE",
        "unknown_account_action": "QUARANTINE",
        "account_entity_or_bank_mismatch_action": "QUARANTINE",
        "sheet_isolation": True,
        "row_isolation": True,
        "source_mutation_allowed": False,
        "raw_root_access_count": 0,
    }


def _get_template(template_id: Any, mapping_version: Any, source_system: str) -> TemplateSpec:
    template_key = _require_text(template_id, "TEMPLATE_ID_REQUIRED", "必须明确选择来源模板。")
    template = TEMPLATE_BY_ID.get(template_key)
    if template is None:
        raise SourceAdapterError("UNKNOWN_TEMPLATE", "模板未登记，不能猜测字段含义。")
    version = _require_text(mapping_version, "MAPPING_VERSION_REQUIRED", "必须明确提供字段映射版本。")
    if version != template.mapping_version:
        raise SourceAdapterError("UNSUPPORTED_MAPPING_VERSION", "字段映射版本未登记，不能自动套用。")
    if template.source_system != source_system:
        raise SourceAdapterError("SOURCE_SYSTEM_TEMPLATE_MISMATCH", "来源系统与所选模板不一致。")
    return template


def compile_header_mapping(
    *,
    source_system: str,
    template_id: str,
    mapping_version: str,
    headers: Sequence[Any],
) -> MappingPlan:
    template = _get_template(template_id, mapping_version, source_system)
    if not headers:
        raise SourceAdapterError("SOURCE_HEADERS_REQUIRED", "来源表没有可映射的表头。")
    normalized_headers: dict[str, str] = {}
    for header in headers:
        original = _require_text(header, "BLANK_SOURCE_HEADER", "来源表头不能为空。")
        normalized = _normalize_header(original)
        if normalized in normalized_headers:
            raise SourceAdapterError("DUPLICATE_NORMALIZED_HEADER", "来源表包含规范化后重复的表头。")
        normalized_headers[normalized] = original

    bindings: dict[str, str] = {}
    used_headers: set[str] = set()
    for field in template.fields:
        aliases = {_normalize_header(alias) for alias in field.aliases}
        matches = [original for normalized, original in normalized_headers.items() if normalized in aliases]
        if len(matches) > 1:
            raise SourceAdapterError("AMBIGUOUS_SOURCE_FIELD", f"标准字段 {field.canonical_field} 同时命中多个来源表头。")
        if not matches:
            if field.required:
                raise SourceAdapterError("REQUIRED_SOURCE_FIELD_MISSING", f"缺少必需字段 {field.canonical_field}。")
            continue
        bindings[field.canonical_field] = matches[0]
        used_headers.add(matches[0])

    unmapped = [header for header in normalized_headers.values() if header not in used_headers]
    summary = {
        "template_id": template.template_id,
        "source_system": template.source_system,
        "export_type": template.export_type,
        "mapping_version": template.mapping_version,
        "source_header_count": len(normalized_headers),
        "mapped_field_count": len(bindings),
        "required_field_count": sum(field.required for field in template.fields),
        "unmapped_header_count": len(unmapped),
        "unmapped_header_hashes": [_hash_text("S10-P2:unmapped:" + value) for value in unmapped],
        "plaintext_unmapped_header_persisted": False,
        "field_meaning_guessed": False,
    }
    return MappingPlan(template, bindings, summary)


def _validate_context(
    template: TemplateSpec,
    context: Mapping[str, Any],
    account_bindings: Mapping[str, Mapping[str, str]],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for field in template.required_context:
        normalized[field] = _require_text(
            context.get(field),
            f"{field.upper()}_REQUIRED",
            f"来源层级缺少 {field}，该工作表必须隔离。",
        )
        if _placeholder(normalized[field]):
            raise SourceAdapterError(f"{field.upper()}_UNCONFIRMED", f"{field} 尚未确认，不能自动处理。")
    entity_id = normalized["entity_id"]
    if not OPAQUE_ID_RE.fullmatch(entity_id) or not entity_id.startswith("ENTITY::"):
        raise SourceAdapterError("ENTITY_ID_INVALID", "公司主体必须使用已登记的匿名编号。")
    if not PERIOD_RE.fullmatch(normalized["period"]):
        raise SourceAdapterError("PERIOD_INVALID", "期间必须为 YYYY 或 YYYY-MM。")
    if template.source_system == "BANK":
        bank_id = normalized["bank_id"]
        account_id = normalized["account_id"]
        if not OPAQUE_ID_RE.fullmatch(bank_id) or not bank_id.startswith("BANK::"):
            raise SourceAdapterError("BANK_ID_INVALID", "银行必须使用已登记的匿名编号。")
        if not OPAQUE_ID_RE.fullmatch(account_id) or not account_id.startswith("ACCOUNT::"):
            raise SourceAdapterError("ACCOUNT_ID_INVALID", "账户必须使用已登记的匿名编号。")
        binding = account_bindings.get(account_id)
        if binding is None:
            raise SourceAdapterError("ACCOUNT_SUBJECT_UNKNOWN", "账户没有确认所属公司和银行，必须隔离。")
        if binding.get("entity_id") != entity_id or binding.get("bank_id") != bank_id:
            raise SourceAdapterError("ACCOUNT_SUBJECT_BINDING_MISMATCH", "账户与公司或银行归属不一致，必须隔离。")
    return normalized


def _missing_value(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def adapt_sheet(
    *,
    source_system: str,
    sheet: Mapping[str, Any],
    account_bindings: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    sheet_id = _require_text(sheet.get("sheet_id"), "SHEET_ID_REQUIRED", "每个工作表必须有稳定编号。")
    plan = compile_header_mapping(
        source_system=source_system,
        template_id=str(sheet.get("template_id") or ""),
        mapping_version=str(sheet.get("mapping_version") or ""),
        headers=list(sheet.get("headers") or []),
    )
    context = _validate_context(plan.template, dict(sheet.get("context") or {}), account_bindings)
    rows = list(sheet.get("rows") or [])
    if not rows:
        raise SourceAdapterError("SOURCE_ROWS_REQUIRED", "来源工作表没有可处理的数据行。")

    required_fields = {field.canonical_field for field in plan.template.fields if field.required}
    records: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=2):
        if not isinstance(row, Mapping):
            quarantined.append({"sheet_id": sheet_id, "source_row_number": row_index, "reason_code": "SOURCE_ROW_INVALID"})
            continue
        canonical = {
            field: row.get(source_header)
            for field, source_header in plan.header_by_canonical.items()
        }
        missing = sorted(field for field in required_fields if _missing_value(canonical.get(field)))
        if missing:
            quarantined.append(
                {
                    "sheet_id": sheet_id,
                    "source_row_number": row_index,
                    "reason_code": "REQUIRED_SOURCE_VALUE_MISSING",
                    "missing_canonical_fields": missing,
                }
            )
            continue
        record = {
            "schema_version": "kmfa.v015.s10p2.adapted_record.v1",
            "source_system": source_system,
            "export_type": plan.template.export_type,
            "template_id": plan.template.template_id,
            "mapping_version": plan.template.mapping_version,
            "sheet_id": sheet_id,
            "source_row_number": row_index,
            "entity_id": context["entity_id"],
            "period": context["period"],
            "bank_id": context.get("bank_id", "NOT_APPLICABLE"),
            "account_id": context.get("account_id", "NOT_APPLICABLE"),
            "canonical_values": canonical,
            "source_mutation_performed": False,
        }
        record["record_ref"] = "ADAPTED::" + _hash_text(
            _canonical_json(
                {
                    "source_system": source_system,
                    "template_id": plan.template.template_id,
                    "mapping_version": plan.template.mapping_version,
                    "sheet_id": sheet_id,
                    "source_row_number": row_index,
                    "entity_id": context["entity_id"],
                    "period": context["period"],
                }
            )
        ).removeprefix("sha256:")[:24]
        records.append(record)
    return {
        "sheet_id": sheet_id,
        "template_id": plan.template.template_id,
        "mapping_version": plan.template.mapping_version,
        "context": context,
        "mapping_summary": dict(plan.public_summary),
        "records": records,
        "quarantined": quarantined,
        "source_mutation_performed": False,
    }


def _validate_inspection(inspection: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(inspection)
    if value.get("inspection_status") != "SAFE_TO_PREVIEW":
        raise SourceAdapterError("S10_P1_INSPECTION_REQUIRED", "文件必须先通过 S10-P1 安全识别。")
    if not FILE_HASH_RE.fullmatch(str(value.get("file_hash") or "")):
        raise SourceAdapterError("FILE_HASH_INVALID", "文件 hash 必须来自 S10-P1 安全识别。")
    if value.get("format_code") not in ALLOWED_INSPECTION_FORMATS:
        raise SourceAdapterError("ADAPTER_FILE_FORMAT_UNSUPPORTED", "来源适配仅处理表格型导出文件。")
    if value.get("raw_root_access_count") not in (None, 0):
        raise SourceAdapterError("RAW_BOUNDARY_VIOLATION", "来源适配不得访问 raw inbox。")
    return value


def adapt_workbook(
    inspection: Mapping[str, Any],
    *,
    source_system: str,
    sheets: Sequence[Mapping[str, Any]],
    account_bindings: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    """Adapt an inspected export workbook and isolate bad sheets/rows."""

    checked = _validate_inspection(inspection)
    if source_system not in SOURCE_SYSTEM_LABELS_ZH:
        raise SourceAdapterError("SOURCE_SYSTEM_UNSUPPORTED", "来源系统没有登记适配器。")
    if not sheets:
        raise SourceAdapterError("WORKBOOK_SHEETS_REQUIRED", "导出文件至少需要一个工作表。")
    bindings = dict(account_bindings or {})
    sheet_ids: set[str] = set()
    adapted_sheets: list[dict[str, Any]] = []
    quarantined_sheets: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    quarantined_rows: list[dict[str, Any]] = []
    for position, sheet in enumerate(sheets, start=1):
        candidate_id = str(sheet.get("sheet_id") or f"SHEET-{position}")
        if candidate_id in sheet_ids:
            quarantined_sheets.append({"sheet_id": candidate_id, "reason_code": "DUPLICATE_SHEET_ID"})
            continue
        sheet_ids.add(candidate_id)
        try:
            adapted = adapt_sheet(source_system=source_system, sheet=sheet, account_bindings=bindings)
        except SourceAdapterError as error:
            quarantined_sheets.append({"sheet_id": candidate_id, "reason_code": error.code})
            continue
        adapted_sheets.append(
            {
                "sheet_id": adapted["sheet_id"],
                "template_id": adapted["template_id"],
                "mapping_version": adapted["mapping_version"],
                "entity_id": adapted["context"]["entity_id"],
                "period": adapted["context"]["period"],
                "bank_id": adapted["context"].get("bank_id", "NOT_APPLICABLE"),
                "account_id": adapted["context"].get("account_id", "NOT_APPLICABLE"),
                "mapping_summary": adapted["mapping_summary"],
            }
        )
        records.extend(adapted["records"])
        quarantined_rows.extend(adapted["quarantined"])
    status = "READY" if records and not quarantined_sheets and not quarantined_rows else "PARTIAL"
    if not records:
        status = "QUARANTINED"
    return {
        "schema_version": "kmfa.v015.s10p2.adaptation_result.v1",
        "file_hash": checked["file_hash"],
        "format_code": checked["format_code"],
        "source_system": source_system,
        "source_system_label_zh": SOURCE_SYSTEM_LABELS_ZH[source_system],
        "adaptation_status": status,
        "sheet_count": len(sheets),
        "adapted_sheet_count": len(adapted_sheets),
        "quarantined_sheet_count": len(quarantined_sheets),
        "adapted_record_count": len(records),
        "quarantined_row_count": len(quarantined_rows),
        "adapted_sheets": adapted_sheets,
        "quarantined_sheets": quarantined_sheets,
        "records": records,
        "quarantined_rows": quarantined_rows,
        "automatic_login_performed": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "business_execution_performed": False,
    }


CHECK_IDS = (
    "registry_valid",
    "source_system_count_6",
    "template_count_15",
    "redcircle_template_count_4",
    "kingdee_template_count_4",
    "wps_template_count_4",
    "auxiliary_template_count_3",
    "all_templates_versioned",
    "automatic_login_disabled",
    "live_connector_disabled",
    "credential_storage_disabled",
    "raw_access_zero",
    "source_mutation_false",
    "all_template_samples_adapted",
    "all_mapping_versions_bound",
    "all_hierarchy_context_complete",
    "redcircle_four_exports_adapted",
    "kingdee_four_exports_adapted",
    "wps_four_exports_adapted",
    "bank_tax_contract_adapted",
    "multi_sheet_supported",
    "multi_entity_supported",
    "multi_bank_supported",
    "multi_account_supported",
    "unknown_account_quarantined",
    "account_binding_mismatch_quarantined",
    "unknown_mapping_version_quarantined",
    "missing_required_header_quarantined",
    "ambiguous_header_quarantined",
    "unknown_header_not_guessed",
    "missing_period_quarantined",
    "invalid_period_quarantined",
    "source_template_mismatch_quarantined",
    "missing_entity_quarantined",
    "missing_bank_quarantined",
    "missing_account_quarantined",
    "bad_sheet_isolated",
    "bad_row_isolated",
    "invalid_file_hash_rejected",
    "pdf_source_rejected",
    "unsafe_inspection_rejected",
    "public_verification_contains_no_business_values",
)


def _inspection(*, format_code: str = "EXCEL_XLSX", safe: bool = True, valid_hash: bool = True) -> dict[str, Any]:
    digest = hashlib.sha256(b"synthetic-s10-p2-export").hexdigest() if valid_hash else "bad"
    return {
        "inspection_status": "SAFE_TO_PREVIEW" if safe else "QUARANTINED",
        "file_hash": "sha256:" + digest,
        "format_code": format_code,
        "raw_root_access_count": 0,
    }


def _sample_sheet(template: TemplateSpec, *, sheet_id: str = "SHEET-1", context: Mapping[str, str] | None = None) -> dict[str, Any]:
    headers = [field.aliases[0] for field in template.fields]
    row = {header: f"SYNTHETIC::{index}" for index, header in enumerate(headers, start=1)}
    base_context = {"entity_id": "ENTITY::SYNTHETIC_A", "period": "2026-06"}
    if template.source_system == "BANK":
        base_context.update({"bank_id": "BANK::SYNTHETIC_A", "account_id": "ACCOUNT::SYNTHETIC_A"})
    base_context.update(dict(context or {}))
    return {
        "sheet_id": sheet_id,
        "template_id": template.template_id,
        "mapping_version": template.mapping_version,
        "headers": headers,
        "rows": [row],
        "context": base_context,
    }


def _reason(result: Mapping[str, Any]) -> str | None:
    rows = list(result.get("quarantined_rows") or [])
    sheets = list(result.get("quarantined_sheets") or [])
    if sheets:
        return str(sheets[0].get("reason_code"))
    if rows:
        return str(rows[0].get("reason_code"))
    return None


def _raises_code(fn, code: str) -> bool:
    try:
        fn()
    except SourceAdapterError as error:
        return error.code == code
    return False


def public_verification() -> dict[str, Any]:
    """Run deterministic synthetic adapter checks without reading private data."""

    account_bindings = {
        "ACCOUNT::SYNTHETIC_A": {"entity_id": "ENTITY::SYNTHETIC_A", "bank_id": "BANK::SYNTHETIC_A"},
        "ACCOUNT::SYNTHETIC_B": {"entity_id": "ENTITY::SYNTHETIC_B", "bank_id": "BANK::SYNTHETIC_B"},
    }
    outcomes: dict[str, dict[str, Any]] = {}
    for template in TEMPLATES:
        outcomes[template.template_id] = adapt_workbook(
            _inspection(),
            source_system=template.source_system,
            sheets=[_sample_sheet(template)],
            account_bindings=account_bindings,
        )

    wps_template = TEMPLATE_BY_ID["wps.collection.v1"]
    multi_wps = adapt_workbook(
        _inspection(),
        source_system="WPS",
        sheets=[
            _sample_sheet(wps_template, sheet_id="SHEET-A", context={"entity_id": "ENTITY::SYNTHETIC_A"}),
            _sample_sheet(wps_template, sheet_id="SHEET-B", context={"entity_id": "ENTITY::SYNTHETIC_B"}),
        ],
    )
    bank_template = TEMPLATE_BY_ID["bank.statement.v1"]
    multi_bank = adapt_workbook(
        _inspection(),
        source_system="BANK",
        sheets=[
            _sample_sheet(bank_template, sheet_id="BANK-A"),
            _sample_sheet(
                bank_template,
                sheet_id="BANK-B",
                context={"entity_id": "ENTITY::SYNTHETIC_B", "bank_id": "BANK::SYNTHETIC_B", "account_id": "ACCOUNT::SYNTHETIC_B"},
            ),
        ],
        account_bindings=account_bindings,
    )
    unknown_account = adapt_workbook(
        _inspection(),
        source_system="BANK",
        sheets=[_sample_sheet(bank_template, context={"account_id": "ACCOUNT::NOT_REGISTERED"})],
        account_bindings=account_bindings,
    )
    mismatch_account = adapt_workbook(
        _inspection(),
        source_system="BANK",
        sheets=[_sample_sheet(bank_template, context={"entity_id": "ENTITY::SYNTHETIC_B"})],
        account_bindings=account_bindings,
    )
    version_bad = _sample_sheet(wps_template)
    version_bad["mapping_version"] = "9.9.9"
    version_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[version_bad])
    missing_header = _sample_sheet(wps_template)
    missing_header["headers"] = missing_header["headers"][1:]
    missing_header["rows"] = [{key: value for key, value in missing_header["rows"][0].items() if key in missing_header["headers"]}]
    missing_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[missing_header])
    ambiguous = _sample_sheet(wps_template)
    ambiguous["headers"] = [*ambiguous["headers"], wps_template.fields[0].aliases[1]]
    ambiguous["rows"][0][wps_template.fields[0].aliases[1]] = "SYNTHETIC::DUPLICATE"
    ambiguous_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[ambiguous])
    unknown_header = _sample_sheet(wps_template)
    unknown_header["headers"].append("未登记测试列")
    unknown_header["rows"][0]["未登记测试列"] = "SYNTHETIC::UNMAPPED"
    unknown_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[unknown_header])
    missing_period = _sample_sheet(wps_template)
    missing_period["context"]["period"] = ""
    missing_period_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[missing_period])
    invalid_period = _sample_sheet(wps_template)
    invalid_period["context"]["period"] = "2026-13"
    invalid_period_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[invalid_period])
    mismatch_source = _sample_sheet(wps_template)
    mismatch_source_result = adapt_workbook(_inspection(), source_system="REDCIRCLE", sheets=[mismatch_source])
    missing_entity = _sample_sheet(wps_template)
    missing_entity["context"]["entity_id"] = ""
    missing_entity_result = adapt_workbook(_inspection(), source_system="WPS", sheets=[missing_entity])
    missing_bank = _sample_sheet(bank_template)
    missing_bank["context"]["bank_id"] = ""
    missing_bank_result = adapt_workbook(_inspection(), source_system="BANK", sheets=[missing_bank], account_bindings=account_bindings)
    missing_account = _sample_sheet(bank_template)
    missing_account["context"]["account_id"] = ""
    missing_account_result = adapt_workbook(_inspection(), source_system="BANK", sheets=[missing_account], account_bindings=account_bindings)
    bad_sheet = _sample_sheet(wps_template, sheet_id="BAD")
    bad_sheet["mapping_version"] = "9.9.9"
    isolated = adapt_workbook(
        _inspection(),
        source_system="WPS",
        sheets=[_sample_sheet(wps_template, sheet_id="GOOD"), bad_sheet],
    )
    bad_row = _sample_sheet(wps_template)
    required_header = wps_template.fields[0].aliases[0]
    bad_row["rows"].append({**bad_row["rows"][0], required_header: ""})
    row_isolated = adapt_workbook(_inspection(), source_system="WPS", sheets=[bad_row])

    registry = template_registry_public_safe()
    hierarchy = source_hierarchy_policy_public_safe()
    version_policy = mapping_version_policy_public_safe()
    redcircle_ids = [template.template_id for template in TEMPLATES if template.source_system == "REDCIRCLE"]
    kingdee_ids = [template.template_id for template in TEMPLATES if template.source_system == "KINGDEE"]
    wps_ids = [template.template_id for template in TEMPLATES if template.source_system == "WPS"]
    aux_ids = [template.template_id for template in TEMPLATES if template.source_system in {"BANK", "TAX_EINVOICE", "CONTRACT_LEDGER"}]
    checks = [
        validate_template_registry() == TEMPLATE_COUNTS,
        registry["source_system_count"] == 6,
        registry["adapter_template_count"] == 15,
        TEMPLATE_COUNTS["REDCIRCLE"] == 4,
        TEMPLATE_COUNTS["KINGDEE"] == 4,
        TEMPLATE_COUNTS["WPS"] == 4,
        sum(TEMPLATE_COUNTS[key] for key in ("BANK", "TAX_EINVOICE", "CONTRACT_LEDGER")) == 3,
        all(SEMVER_RE.fullmatch(template.mapping_version) for template in TEMPLATES),
        registry["automatic_login_allowed"] is False,
        registry["live_connector_call_allowed"] is False,
        registry["credential_storage_allowed"] is False,
        hierarchy["raw_root_access_count"] == 0,
        hierarchy["source_mutation_allowed"] is False,
        all(value["adapted_record_count"] == 1 for value in outcomes.values()),
        all(value["adapted_sheets"][0]["mapping_version"] == "1.0.0" for value in outcomes.values()),
        all(value["adapted_sheets"][0]["entity_id"].startswith("ENTITY::") for value in outcomes.values()),
        all(outcomes[key]["adaptation_status"] == "READY" for key in redcircle_ids),
        all(outcomes[key]["adaptation_status"] == "READY" for key in kingdee_ids),
        all(outcomes[key]["adaptation_status"] == "READY" for key in wps_ids),
        all(outcomes[key]["adaptation_status"] == "READY" for key in aux_ids),
        multi_wps["adapted_sheet_count"] == 2,
        len({row["entity_id"] for row in multi_wps["adapted_sheets"]}) == 2,
        len({row["bank_id"] for row in multi_bank["adapted_sheets"]}) == 2,
        len({row["account_id"] for row in multi_bank["adapted_sheets"]}) == 2,
        _reason(unknown_account) == "ACCOUNT_SUBJECT_UNKNOWN",
        _reason(mismatch_account) == "ACCOUNT_SUBJECT_BINDING_MISMATCH",
        _reason(version_result) == "UNSUPPORTED_MAPPING_VERSION",
        _reason(missing_result) == "REQUIRED_SOURCE_FIELD_MISSING",
        _reason(ambiguous_result) == "AMBIGUOUS_SOURCE_FIELD",
        unknown_result["adapted_sheets"][0]["mapping_summary"]["unmapped_header_count"] == 1 and version_policy["guess_field_meaning_allowed"] is False,
        _reason(missing_period_result) == "PERIOD_REQUIRED",
        _reason(invalid_period_result) == "PERIOD_INVALID",
        _reason(mismatch_source_result) == "SOURCE_SYSTEM_TEMPLATE_MISMATCH",
        _reason(missing_entity_result) == "ENTITY_ID_REQUIRED",
        _reason(missing_bank_result) == "BANK_ID_REQUIRED",
        _reason(missing_account_result) == "ACCOUNT_ID_REQUIRED",
        isolated["adapted_record_count"] == 1 and isolated["quarantined_sheet_count"] == 1,
        row_isolated["adapted_record_count"] == 1 and row_isolated["quarantined_row_count"] == 1,
        _raises_code(lambda: adapt_workbook(_inspection(valid_hash=False), source_system="WPS", sheets=[_sample_sheet(wps_template)]), "FILE_HASH_INVALID"),
        _raises_code(lambda: adapt_workbook(_inspection(format_code="PDF"), source_system="WPS", sheets=[_sample_sheet(wps_template)]), "ADAPTER_FILE_FORMAT_UNSUPPORTED"),
        _raises_code(lambda: adapt_workbook(_inspection(safe=False), source_system="WPS", sheets=[_sample_sheet(wps_template)]), "S10_P1_INSPECTION_REQUIRED"),
        all("SYNTHETIC::" not in _canonical_json(value["adapted_sheets"]) for value in outcomes.values()),
    ]
    if len(checks) != len(CHECK_IDS):
        raise SourceAdapterError("PUBLIC_CHECK_COUNT_DRIFT", "公开验证数量与编号不一致。")
    rows = [
        {"check_id": check_id, "status": "PASS" if passed else "FAIL"}
        for check_id, passed in zip(CHECK_IDS, checks)
    ]
    failed = sum(row["status"] == "FAIL" for row in rows)
    return {
        "schema_version": "kmfa.v015.s10p2.public_verification.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed},
        "checks": rows,
        "source_system_count": len(SOURCE_SYSTEM_LABELS_ZH),
        "adapter_template_count": len(TEMPLATES),
        "redcircle_template_count": TEMPLATE_COUNTS["REDCIRCLE"],
        "kingdee_template_count": TEMPLATE_COUNTS["KINGDEE"],
        "wps_template_count": TEMPLATE_COUNTS["WPS"],
        "auxiliary_template_count": 3,
        "mapping_versioned_template_count": len(TEMPLATES),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "automatic_login_performed": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "source_mutation_performed": False,
        "s10_p3_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def main() -> int:
    result = public_verification()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["accounting"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
