#!/usr/bin/env python3
"""KMFA v1.5 S08-P2 company, account, and counterparty hierarchy kernel.

The kernel is deliberately fail closed: funds without a known company entity
cannot be aggregated, account aliases cannot cross company boundaries, and
counterparties with the same name are never force-merged.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY"
ROADMAP_PHASE_ID = "S08-P2"
TASK_ID = "KMFA-V015-S08-P2-BUSINESS-ENTITY-HIERARCHY-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S08-P2-BUSINESS-ENTITY-HIERARCHY"
VERSION = "1.5.0-dev-s08p2"
SCHEMA_VERSION = "kmfa.v015.s08p2.business_entity_hierarchy.v1"

ENTITY_RELATIONSHIP_TYPES = frozenset({"PARENT_OF", "OPERATES_FOR", "AFFILIATED_WITH"})
COUNTERPARTY_ROLES = frozenset({"CUSTOMER", "OWNER", "SUPPLIER", "SUBCONTRACTOR"})
COUNTERPARTY_RELATIONSHIP_TYPES = frozenset(
    {"CUSTOMER_OF", "OWNER_FOR", "SUPPLIER_TO", "SUBCONTRACTOR_FOR"}
)
REF_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,63}$")
ALIAS_SEPARATOR_RE = re.compile(r"[\s_\-—]+")


class BusinessEntityError(ValueError):
    """Fail-closed validation error with a stable machine-readable code."""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _text(value: Any, field: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise BusinessEntityError("TEXT_REQUIRED", f"{field} 不能为空。")
    return text


def _ref(value: Any, field: str) -> str:
    text = _text(value, field).upper()
    if not REF_RE.fullmatch(text):
        raise BusinessEntityError("INVALID_REFERENCE", f"{field} 格式无效。")
    return text


def _cents(value: Any, field: str = "amount_cents") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BusinessEntityError("INTEGER_CENTS_REQUIRED", f"{field} 必须使用整数分。")
    return value


def _alias(value: Any) -> str:
    text = unicodedata.normalize("NFKC", _text(value, "alias")).casefold()
    normalized = ALIAS_SEPARATOR_RE.sub("", text)
    if not normalized:
        raise BusinessEntityError("EMPTY_ALIAS", "别名标准化后不能为空。")
    return normalized


def _entity_refs(registry: Mapping[str, Any]) -> set[str]:
    return {_ref(row.get("company_entity_ref"), "company_entity_ref") for row in registry.get("entities", [])}


def build_company_registry(
    entities: Sequence[Mapping[str, Any]],
    relationships: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a public-safe company dimension and validate its relationship graph."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in entities:
        entity_ref = _ref(source.get("company_entity_ref"), "company_entity_ref")
        if entity_ref in seen:
            raise BusinessEntityError("DUPLICATE_COMPANY_ENTITY", "公司主体编号不能重复。")
        seen.add(entity_ref)
        status = _text(source.get("status", "ACTIVE"), "status").upper()
        if status not in {"ACTIVE", "INACTIVE"}:
            raise BusinessEntityError("INVALID_ENTITY_STATUS", "公司主体状态必须是 ACTIVE 或 INACTIVE。")
        rows.append(
            {
                "company_entity_ref": entity_ref,
                "display_name": _text(source.get("display_name"), "display_name"),
                "status": status,
            }
        )
    if not rows:
        raise BusinessEntityError("COMPANY_ENTITY_REQUIRED", "至少需要一个公司主体。")

    relation_rows: list[dict[str, str]] = []
    relation_keys: set[tuple[str, str, str]] = set()
    parent_edges: dict[str, set[str]] = {entity_ref: set() for entity_ref in seen}
    for source in relationships:
        from_ref = _ref(source.get("from_company_entity_ref"), "from_company_entity_ref")
        to_ref = _ref(source.get("to_company_entity_ref"), "to_company_entity_ref")
        relationship_type = _text(source.get("relationship_type"), "relationship_type").upper()
        if from_ref not in seen or to_ref not in seen:
            raise BusinessEntityError("UNKNOWN_RELATIONSHIP_ENTITY", "主体关系引用了未登记公司。")
        if from_ref == to_ref:
            raise BusinessEntityError("SELF_RELATIONSHIP_FORBIDDEN", "公司主体不能指向自身。")
        if relationship_type not in ENTITY_RELATIONSHIP_TYPES:
            raise BusinessEntityError("UNKNOWN_ENTITY_RELATIONSHIP", "主体关系类型未登记。")
        key = (from_ref, relationship_type, to_ref)
        if key in relation_keys:
            raise BusinessEntityError("DUPLICATE_ENTITY_RELATIONSHIP", "公司主体关系不能重复。")
        relation_keys.add(key)
        relation_rows.append(
            {
                "from_company_entity_ref": from_ref,
                "relationship_type": relationship_type,
                "to_company_entity_ref": to_ref,
            }
        )
        if relationship_type == "PARENT_OF":
            parent_edges[from_ref].add(to_ref)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise BusinessEntityError("COMPANY_HIERARCHY_CYCLE", "公司上下级关系不能成环。")
        if node in visited:
            return
        visiting.add(node)
        for child in parent_edges[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for entity_ref in sorted(seen):
        visit(entity_ref)

    return {
        "schema_version": SCHEMA_VERSION,
        "company_entity_count": len(rows),
        "company_relationship_count": len(relation_rows),
        "entities": sorted(rows, key=lambda row: row["company_entity_ref"]),
        "relationships": sorted(
            relation_rows,
            key=lambda row: (
                row["from_company_entity_ref"],
                row["relationship_type"],
                row["to_company_entity_ref"],
            ),
        ),
    }


def assign_record_entity(
    *, record_ref: Any, company_entity_ref: Any, registry: Mapping[str, Any]
) -> dict[str, Any]:
    """Assign one record to a company or explicitly route it to confirmation."""

    record = _ref(record_ref, "record_ref")
    if company_entity_ref is None or str(company_entity_ref).strip() == "":
        return {
            "record_ref": record,
            "company_entity_ref": None,
            "assignment_status": "REQUIRES_CONFIRMATION",
            "reason_code": "MISSING_COMPANY_ENTITY",
            "funds_aggregation_allowed": False,
        }
    entity_ref = _ref(company_entity_ref, "company_entity_ref")
    if entity_ref not in _entity_refs(registry):
        return {
            "record_ref": record,
            "company_entity_ref": None,
            "provided_company_entity_ref": entity_ref,
            "assignment_status": "REQUIRES_CONFIRMATION",
            "reason_code": "UNKNOWN_COMPANY_ENTITY",
            "funds_aggregation_allowed": False,
        }
    return {
        "record_ref": record,
        "company_entity_ref": entity_ref,
        "assignment_status": "ASSIGNED",
        "reason_code": "KNOWN_COMPANY_ENTITY",
        "funds_aggregation_allowed": True,
    }


def aggregate_funds(
    records: Sequence[Mapping[str, Any]], registry: Mapping[str, Any]
) -> dict[str, Any]:
    """Aggregate integer cents only after every record has a known company."""

    prepared: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    rejected: list[str] = []
    for source in records:
        record_ref = _ref(source.get("record_ref"), "record_ref")
        if record_ref in seen:
            raise BusinessEntityError("DUPLICATE_FUNDS_RECORD", "资金记录编号不能重复。")
        seen.add(record_ref)
        assignment = assign_record_entity(
            record_ref=record_ref,
            company_entity_ref=source.get("company_entity_ref"),
            registry=registry,
        )
        amount = _cents(source.get("amount_cents"))
        if not assignment["funds_aggregation_allowed"]:
            rejected.append(record_ref)
        else:
            prepared.append((record_ref, assignment["company_entity_ref"], amount))
    if rejected:
        raise BusinessEntityError(
            "ENTITY_REQUIRED_FOR_FUNDS_AGGREGATION",
            "存在主体缺失或未知的资金记录，整批不得汇总：" + ",".join(sorted(rejected)),
        )
    totals: dict[str, int] = {}
    for _, entity_ref, amount in prepared:
        totals[entity_ref] = totals.get(entity_ref, 0) + amount
    return {
        "record_count": len(prepared),
        "amount_unit": "integer_cents",
        "total_amount_cents": sum(amount for _, _, amount in prepared),
        "company_totals": [
            {"company_entity_ref": entity_ref, "amount_cents": totals[entity_ref]}
            for entity_ref in sorted(totals)
        ],
        "all_records_have_known_company_entity": True,
        "partial_aggregation_performed": False,
    }


def _masked_account(value: Any) -> str:
    digits = re.sub(r"[\s-]+", "", _text(value, "full_account_number"))
    if not digits.isdigit() or not 8 <= len(digits) <= 32:
        raise BusinessEntityError("INVALID_FULL_ACCOUNT_NUMBER", "完整账号必须是 8 至 32 位数字。")
    return "****" + digits[-4:]


def build_account_directory(
    company_registry: Mapping[str, Any],
    banks: Sequence[Mapping[str, Any]],
    accounts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build entity -> bank -> account hierarchy without returning full numbers."""

    entity_refs = _entity_refs(company_registry)
    bank_rows: list[dict[str, str]] = []
    bank_refs: set[str] = set()
    for source in banks:
        bank_ref = _ref(source.get("bank_ref"), "bank_ref")
        if bank_ref in bank_refs:
            raise BusinessEntityError("DUPLICATE_BANK", "银行编号不能重复。")
        bank_refs.add(bank_ref)
        bank_rows.append({"bank_ref": bank_ref, "display_name": _text(source.get("display_name"), "display_name")})
    if not bank_rows:
        raise BusinessEntityError("BANK_REQUIRED", "至少需要一个银行。")

    account_rows: list[dict[str, Any]] = []
    account_refs: set[str] = set()
    alias_index: dict[str, set[str]] = {}
    for source in accounts:
        account_ref = _ref(source.get("account_ref"), "account_ref")
        if account_ref in account_refs:
            raise BusinessEntityError("DUPLICATE_ACCOUNT", "账户编号不能重复。")
        account_refs.add(account_ref)
        company_ref = _ref(source.get("company_entity_ref"), "company_entity_ref")
        bank_ref = _ref(source.get("bank_ref"), "bank_ref")
        if company_ref not in entity_refs:
            raise BusinessEntityError("UNKNOWN_ACCOUNT_COMPANY_ENTITY", "账户必须归属已登记公司主体。")
        if bank_ref not in bank_refs:
            raise BusinessEntityError("UNKNOWN_ACCOUNT_BANK", "账户必须归属已登记银行。")
        aliases = sorted({_alias(value) for value in source.get("aliases", [])})
        aliases = sorted(set(aliases) | {_alias(account_ref)})
        for value in aliases:
            alias_index.setdefault(value, set()).add(account_ref)
        account_rows.append(
            {
                "account_ref": account_ref,
                "company_entity_ref": company_ref,
                "bank_ref": bank_ref,
                "masked_account": _masked_account(source.get("full_account_number")),
                "aliases": aliases,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "hierarchy": "COMPANY_ENTITY_TO_BANK_TO_ACCOUNT",
        "bank_count": len(bank_rows),
        "account_count": len(account_rows),
        "masked_account_count": len(account_rows),
        "public_full_account_value_count": 0,
        "private_full_value_storage_required": True,
        "banks": sorted(bank_rows, key=lambda row: row["bank_ref"]),
        "accounts": sorted(account_rows, key=lambda row: row["account_ref"]),
        "alias_index": [
            {"alias": value, "account_refs": sorted(refs)} for value, refs in sorted(alias_index.items())
        ],
    }


def resolve_account_alias(
    alias: Any,
    directory: Mapping[str, Any],
    *,
    expected_company_entity_ref: Any = None,
) -> dict[str, Any]:
    """Resolve an alias, treating an entity mismatch as a high-risk failure."""

    normalized = _alias(alias)
    accounts = {row["account_ref"]: row for row in directory.get("accounts", [])}
    indexed = {
        row["alias"]: list(row.get("account_refs", [])) for row in directory.get("alias_index", [])
    }
    candidates = [ref for ref in indexed.get(normalized, []) if ref in accounts]
    expected = None
    if expected_company_entity_ref is not None and str(expected_company_entity_ref).strip():
        expected = _ref(expected_company_entity_ref, "expected_company_entity_ref")
    if not candidates:
        return {
            "alias": normalized,
            "expected_company_entity_ref": expected,
            "status": "REQUIRES_CONFIRMATION",
            "reason_code": "ACCOUNT_ALIAS_NOT_FOUND",
            "resolved_account_ref": None,
            "cross_entity_mismatch": False,
            "funds_aggregation_allowed": False,
        }
    if expected:
        owned = [ref for ref in candidates if accounts[ref]["company_entity_ref"] == expected]
        if len(owned) == 1:
            return {
                "alias": normalized,
                "expected_company_entity_ref": expected,
                "status": "RESOLVED",
                "reason_code": "ALIAS_AND_ENTITY_MATCH",
                "resolved_account_ref": owned[0],
                "cross_entity_mismatch": False,
                "funds_aggregation_allowed": True,
            }
        if not owned:
            return {
                "alias": normalized,
                "expected_company_entity_ref": expected,
                "status": "HIGH_RISK_CROSS_ENTITY_MISMATCH",
                "reason_code": "ACCOUNT_BELONGS_TO_OTHER_COMPANY_ENTITY",
                "resolved_account_ref": None,
                "cross_entity_mismatch": True,
                "funds_aggregation_allowed": False,
            }
        reason = "MULTIPLE_ACCOUNTS_IN_EXPECTED_ENTITY"
    else:
        if len(candidates) == 1:
            return {
                "alias": normalized,
                "expected_company_entity_ref": None,
                "status": "RESOLVED",
                "reason_code": "UNIQUE_ACCOUNT_ALIAS",
                "resolved_account_ref": candidates[0],
                "cross_entity_mismatch": False,
                "funds_aggregation_allowed": True,
            }
        reason = "AMBIGUOUS_ACCOUNT_ALIAS"
    return {
        "alias": normalized,
        "expected_company_entity_ref": expected,
        "status": "REQUIRES_CONFIRMATION",
        "reason_code": reason,
        "resolved_account_ref": None,
        "cross_entity_mismatch": False,
        "funds_aggregation_allowed": False,
    }


def build_counterparty_master(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build multi-role counterparty masters without name-based forced merging."""

    rows: list[dict[str, Any]] = []
    refs: set[str] = set()
    name_index: dict[str, set[str]] = {}
    for source in records:
        counterparty_ref = _ref(source.get("counterparty_ref"), "counterparty_ref")
        if counterparty_ref in refs:
            raise BusinessEntityError("DUPLICATE_COUNTERPARTY", "对手方编号不能重复。")
        refs.add(counterparty_ref)
        canonical_name = _text(source.get("canonical_name"), "canonical_name")
        roles = sorted({_text(value, "role").upper() for value in source.get("roles", [])})
        if not roles or set(roles) - COUNTERPARTY_ROLES:
            raise BusinessEntityError("INVALID_COUNTERPARTY_ROLE", "对手方至少需要一个已登记角色。")
        historical_names = sorted({_text(value, "historical_name") for value in source.get("historical_names", [])})
        relationships: list[dict[str, str]] = []
        for relation in source.get("relationships", []):
            relation_type = _text(relation.get("relationship_type"), "relationship_type").upper()
            if relation_type not in COUNTERPARTY_RELATIONSHIP_TYPES:
                raise BusinessEntityError("INVALID_COUNTERPARTY_RELATIONSHIP", "对手方关系类型未登记。")
            relationships.append(
                {
                    "relationship_type": relation_type,
                    "related_company_entity_ref": _ref(
                        relation.get("related_company_entity_ref"), "related_company_entity_ref"
                    ),
                }
            )
        relationships.sort(key=lambda row: (row["relationship_type"], row["related_company_entity_ref"]))
        for name in [canonical_name, *historical_names]:
            name_index.setdefault(_alias(name), set()).add(counterparty_ref)
        rows.append(
            {
                "counterparty_ref": counterparty_ref,
                "canonical_name": canonical_name,
                "roles": roles,
                "historical_names": historical_names,
                "relationships": relationships,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "counterparty_master_count": len(rows),
        "multi_role_counterparty_count": sum(len(row["roles"]) > 1 for row in rows),
        "historical_name_count": sum(len(row["historical_names"]) for row in rows),
        "forced_merge_count": 0,
        "masters": sorted(rows, key=lambda row: row["counterparty_ref"]),
        "name_index": [
            {"normalized_name": name, "counterparty_refs": sorted(values)}
            for name, values in sorted(name_index.items())
        ],
    }


def resolve_counterparty_name(name: Any, master: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _alias(name)
    indexed = {
        row["normalized_name"]: list(row.get("counterparty_refs", []))
        for row in master.get("name_index", [])
    }
    candidates = indexed.get(normalized, [])
    if len(candidates) == 1:
        return {
            "normalized_name": normalized,
            "status": "RESOLVED",
            "reason_code": "UNIQUE_CURRENT_OR_HISTORICAL_NAME",
            "resolved_counterparty_ref": candidates[0],
            "forced_merge_performed": False,
        }
    return {
        "normalized_name": normalized,
        "status": "REQUIRES_CONFIRMATION",
        "reason_code": "NAME_NOT_FOUND" if not candidates else "SAME_NAME_MULTIPLE_MASTERS",
        "resolved_counterparty_ref": None,
        "candidate_count": len(candidates),
        "forced_merge_performed": False,
    }


def synthetic_acceptance_cases() -> dict[str, Any]:
    """Return deterministic, public-safe fixtures for all three TaskPack tasks."""

    companies = build_company_registry(
        [
            {"company_entity_ref": "ENT-HOLD", "display_name": "示例控股主体"},
            {"company_entity_ref": "ENT-OPS-A", "display_name": "示例运营主体甲"},
            {"company_entity_ref": "ENT-OPS-B", "display_name": "示例运营主体乙"},
        ],
        [
            {
                "from_company_entity_ref": "ENT-HOLD",
                "relationship_type": "PARENT_OF",
                "to_company_entity_ref": "ENT-OPS-A",
            },
            {
                "from_company_entity_ref": "ENT-HOLD",
                "relationship_type": "PARENT_OF",
                "to_company_entity_ref": "ENT-OPS-B",
            },
        ],
    )
    assignments = [
        assign_record_entity(record_ref="REC-ASSIGNED", company_entity_ref="ENT-OPS-A", registry=companies),
        assign_record_entity(record_ref="REC-MISSING", company_entity_ref=None, registry=companies),
        assign_record_entity(record_ref="REC-UNKNOWN", company_entity_ref="ENT-UNKNOWN", registry=companies),
    ]
    valid_aggregation = aggregate_funds(
        [
            {"record_ref": "FUND-A-001", "company_entity_ref": "ENT-OPS-A", "amount_cents": 12000},
            {"record_ref": "FUND-A-002", "company_entity_ref": "ENT-OPS-A", "amount_cents": -2000},
            {"record_ref": "FUND-B-001", "company_entity_ref": "ENT-OPS-B", "amount_cents": 8000},
        ],
        companies,
    )
    try:
        aggregate_funds(
            [{"record_ref": "FUND-UNKNOWN", "company_entity_ref": None, "amount_cents": 1}],
            companies,
        )
    except BusinessEntityError as error:
        rejected_aggregation = {
            "status": "REJECTED",
            "error_code": error.code,
            "partial_aggregation_performed": False,
        }
    else:  # pragma: no cover - safety alarm
        raise AssertionError("unknown-entity funds unexpectedly aggregated")

    accounts = build_account_directory(
        companies,
        [
            {"bank_ref": "BANK-ALPHA", "display_name": "示例银行甲"},
            {"bank_ref": "BANK-BETA", "display_name": "示例银行乙"},
        ],
        [
            {
                "account_ref": "ACCOUNT-A-PRIMARY",
                "company_entity_ref": "ENT-OPS-A",
                "bank_ref": "BANK-ALPHA",
                "full_account_number": "9" * 8 + "1001",
                "aliases": ["shared main", "primary settlement"],
            },
            {
                "account_ref": "ACCOUNT-A-TAX",
                "company_entity_ref": "ENT-OPS-A",
                "bank_ref": "BANK-BETA",
                "full_account_number": "9" * 8 + "1002",
                "aliases": ["tax reserve"],
            },
            {
                "account_ref": "ACCOUNT-B-PRIMARY",
                "company_entity_ref": "ENT-OPS-B",
                "bank_ref": "BANK-ALPHA",
                "full_account_number": "9" * 8 + "2001",
                "aliases": ["shared main", "branch settlement"],
            },
        ],
    )
    account_cases = {
        "same_entity_resolved": resolve_account_alias(
            "shared main", accounts, expected_company_entity_ref="ENT-OPS-A"
        ),
        "cross_entity_high_risk": resolve_account_alias(
            "tax reserve", accounts, expected_company_entity_ref="ENT-OPS-B"
        ),
        "ambiguous_requires_confirmation": resolve_account_alias("shared main", accounts),
    }

    counterparties = build_counterparty_master(
        [
            {
                "counterparty_ref": "CP-ALPHA",
                "canonical_name": "示例协作方",
                "roles": ["CUSTOMER", "OWNER"],
                "historical_names": ["示例旧客户"],
                "relationships": [
                    {"relationship_type": "CUSTOMER_OF", "related_company_entity_ref": "ENT-OPS-A"},
                    {"relationship_type": "OWNER_FOR", "related_company_entity_ref": "ENT-OPS-A"},
                ],
            },
            {
                "counterparty_ref": "CP-BETA",
                "canonical_name": "示例协作方",
                "roles": ["SUPPLIER", "SUBCONTRACTOR"],
                "historical_names": ["示例旧供应商"],
                "relationships": [
                    {"relationship_type": "SUPPLIER_TO", "related_company_entity_ref": "ENT-OPS-B"},
                    {"relationship_type": "SUBCONTRACTOR_FOR", "related_company_entity_ref": "ENT-OPS-B"},
                ],
            },
        ]
    )
    counterparty_cases = {
        "historical_name_resolved": resolve_counterparty_name("示例旧客户", counterparties),
        "same_name_not_force_merged": resolve_counterparty_name("示例协作方", counterparties),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "company_registry": companies,
        "entity_assignment_cases": assignments,
        "valid_funds_aggregation": valid_aggregation,
        "unknown_entity_funds_aggregation": rejected_aggregation,
        "account_directory": accounts,
        "account_resolution_cases": account_cases,
        "counterparty_master": counterparties,
        "counterparty_resolution_cases": counterparty_cases,
        "raw_root_access_count": 0,
        "private_business_values_published": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "BusinessEntityError",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "TASK_ID",
    "VERSION",
    "aggregate_funds",
    "assign_record_entity",
    "build_account_directory",
    "build_company_registry",
    "build_counterparty_master",
    "resolve_account_alias",
    "resolve_counterparty_name",
    "synthetic_acceptance_cases",
]
