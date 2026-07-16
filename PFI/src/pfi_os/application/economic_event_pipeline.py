from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from pfi_os.domain.economic_events import (
    EconomicEvent,
    ImpactFlags,
    InterconnectionGroup,
    LedgerEvent,
    LedgerPosting,
    NormalizedTransaction,
)


VERSION = "v0.2.5"
STAGE = 3
PHASE_ID = "V025-S3-P3.2"
TASK_IDS = ("S3-P2-T1", "S3-P2-T2", "S3-P2-T3", "S3-P2-T4")
CONTRACT_ID = "PFI-V025-STAGE3-PHASE32-NORMALIZED-EVENT"
ACCEPTANCE_ID = "ACC-PFI-V025-S3-P32-NORMALIZED-EVENT"

PFI_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = PFI_ROOT / "config" / "schemas" / "v025"
POLICY_PATH = PFI_ROOT / "config" / "event_types" / "v025_phase_3_2_event_policy.json"
SCHEMA_FILES = (
    "normalized_transaction.schema.json",
    "interconnection_group.schema.json",
    "economic_event.schema.json",
    "ledger_event.schema.json",
)
_IMPACT_FIELDS = (
    "net_worth_effect",
    "cash_effect",
    "living_consumption_included",
    "activity_outflow_included",
    "investment_allocation_included",
    "requires_offset_event_id",
    "fee_tax_requires_separate_event",
)


def build_phase32_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3Phase32ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "task_ids": list(TASK_IDS),
        "current_phase_only": True,
        "real_financial_data_read": False,
        "real_financial_data_mutated": False,
        "contract_test_values_used": True,
        "financial_fixture_fallback_used": False,
        "production_financial_acceptance_claimed": False,
        "database_changed": False,
        "finder_used": False,
        "risk_tier": "T3_FINANCIAL_EVENT_POLICY_PRIVACY",
        "explicitly_not_done": [
            "Phase 3.3",
            "real-data duplicate import or reconciliation",
            "review queue persistence",
            "database migration",
            "GitHub push",
            "canonical App install",
            "Stage 3 whole-stage acceptance",
        ],
    }


def load_phase32_policy(path: Path | str = POLICY_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Phase 3.2 policy must be a JSON object")
    if payload.get("source_name_inference") is not False:
        raise ValueError("source-name inference is forbidden")
    if payload.get("amount_time_heuristic_grouping") is not False:
        raise ValueError("amount/time heuristic grouping is forbidden")
    if payload.get("unknown_event_type_policy") != "review_required_no_publication":
        raise ValueError("unknown event types must require review without publication")
    if payload.get("event_time_strategy") != "earliest_transaction_time":
        raise ValueError("event_time_strategy must be earliest_transaction_time")
    if payload.get("same_economic_event_per_metric_max_count") != 1:
        raise ValueError("same economic event must count at most once per metric")

    grouping_rules = payload.get("grouping_rules")
    if not isinstance(grouping_rules, dict) or set(grouping_rules) != {
        "explicit_link_reference_exact",
        "singleton_normalized_transaction",
    }:
        raise ValueError("grouping_rules must define only the two explicit Phase 3.2 rules")
    for rule_id, rule in grouping_rules.items():
        if not isinstance(rule, dict) or not isinstance(rule.get("version"), str):
            raise ValueError(f"grouping rule {rule_id} must declare a version")
        for forbidden_basis in ("uses_amount", "uses_time_proximity", "uses_source_name"):
            if rule.get(forbidden_basis) is not False:
                raise ValueError(f"grouping rule {rule_id} must set {forbidden_basis}=false")

    event_types = payload.get("event_types")
    if not isinstance(event_types, dict) or not event_types:
        raise ValueError("event_types must be a non-empty object")
    for event_type, flags in event_types.items():
        if not isinstance(event_type, str) or not isinstance(flags, dict):
            raise ValueError("event type policies must be named objects")
        if set(flags) != set(_IMPACT_FIELDS):
            raise ValueError(f"event type {event_type} must define the complete impact flag set")
        ImpactFlags(**flags)
    return payload


def normalize_transaction(
    *,
    raw_record_id: str,
    source_id: str,
    account_ref: str,
    source_record_hash: str,
    amount: str,
    currency: str,
    direction: str,
    transaction_time: str,
    posted_at: str,
    effective_at: str,
    imported_at: str,
    link_reference: str | None = None,
    normalization_version: str = "1",
) -> NormalizedTransaction:
    identity = _stable_id(
        "normalized_transaction",
        source_id,
        raw_record_id,
        source_record_hash,
        normalization_version,
    )
    return NormalizedTransaction(
        normalized_transaction_id=identity,
        raw_record_id=raw_record_id,
        source_id=source_id,
        account_ref=account_ref,
        source_record_hash=source_record_hash,
        amount=amount,
        currency=currency,
        direction=direction,
        transaction_time=transaction_time,
        posted_at=posted_at,
        effective_at=effective_at,
        imported_at=imported_at,
        link_reference=link_reference,
        normalization_version=normalization_version,
    )


def build_interconnection_groups(
    transactions: Iterable[NormalizedTransaction],
    *,
    policy: Mapping[str, Any],
    created_at: str,
) -> tuple[InterconnectionGroup, ...]:
    items = tuple(transactions)
    _require_unique_transactions(items)
    _require_rfc3339(created_at, "created_at")
    if policy.get("source_name_inference") is not False or policy.get("amount_time_heuristic_grouping") is not False:
        raise ValueError("grouping policy must prohibit source-name and amount/time inference")
    rules = policy.get("grouping_rules")
    if not isinstance(rules, Mapping):
        raise ValueError("grouping_rules are required")

    buckets: dict[tuple[str, str], list[NormalizedTransaction]] = {}
    for transaction in items:
        key = (
            ("linked", transaction.link_reference)
            if transaction.link_reference is not None
            else ("singleton", transaction.normalized_transaction_id)
        )
        buckets.setdefault(key, []).append(transaction)

    groups: list[InterconnectionGroup] = []
    for (basis, grouping_value), members in buckets.items():
        if basis == "linked":
            rule_id = "explicit_link_reference_exact"
            link_reference_hash = _sha256_text(grouping_value)
        else:
            rule_id = "singleton_normalized_transaction"
            link_reference_hash = None
        rule = rules.get(rule_id)
        if not isinstance(rule, Mapping) or not isinstance(rule.get("version"), str):
            raise ValueError(f"missing grouping rule: {rule_id}")
        rule_hash = _payload_hash(rule)
        member_ids = tuple(sorted(item.normalized_transaction_id for item in members))
        group_id = _stable_id("interconnection_group", rule_id, rule_hash, *member_ids)
        groups.append(
            InterconnectionGroup(
                interconnection_group_id=group_id,
                normalized_transaction_ids=member_ids,
                grouping_rule_id=rule_id,
                rule_version=str(rule["version"]),
                rule_hash=rule_hash,
                reason_codes=(rule_id,),
                created_at=created_at,
                link_reference_hash=link_reference_hash,
            )
        )
    return tuple(sorted(groups, key=lambda item: item.interconnection_group_id))


def build_economic_event(
    group: InterconnectionGroup,
    transactions: Iterable[NormalizedTransaction],
    *,
    event_type: str,
    policy: Mapping[str, Any],
    offset_economic_event_id: str | None = None,
) -> EconomicEvent:
    items = tuple(transactions)
    _require_unique_transactions(items)
    item_ids = tuple(sorted(item.normalized_transaction_id for item in items))
    if item_ids != group.normalized_transaction_ids:
        raise ValueError("transactions must exactly match the interconnection group")
    event_types = policy.get("event_types")
    if not isinstance(event_types, Mapping) or event_type not in event_types:
        raise ValueError("unregistered event_type is review_required and cannot be published")
    flags_payload = event_types[event_type]
    if not isinstance(flags_payload, Mapping) or set(flags_payload) != set(_IMPACT_FIELDS):
        raise ValueError("event policy must contain the complete impact flag set")
    flags = ImpactFlags(**dict(flags_payload))
    if policy.get("event_time_strategy") != "earliest_transaction_time":
        raise ValueError("unsupported event_time_strategy")
    earliest = min(items, key=lambda item: _require_rfc3339(item.transaction_time, "transaction_time"))
    policy_version = str(policy.get("policy_version", ""))
    policy_hash = _payload_hash(policy)
    event_id = _stable_id(
        "economic_event",
        group.interconnection_group_id,
        event_type,
        policy_version,
        policy_hash,
        offset_economic_event_id or "no_offset",
    )
    return EconomicEvent(
        economic_event_id=event_id,
        interconnection_group_id=group.interconnection_group_id,
        raw_record_ids=tuple(sorted(item.raw_record_id for item in items)),
        normalized_transaction_ids=item_ids,
        event_type=event_type,
        event_time=earliest.transaction_time,
        currencies=tuple(sorted({item.currency for item in items})),
        policy_version=policy_version,
        policy_hash=policy_hash,
        impact_flags=flags,
        offset_economic_event_id=offset_economic_event_id,
    )


def publish_ledger_event(
    event: EconomicEvent,
    transactions: Iterable[NormalizedTransaction],
) -> LedgerEvent:
    items = tuple(transactions)
    _require_unique_transactions(items)
    item_ids = tuple(sorted(item.normalized_transaction_id for item in items))
    if item_ids != event.normalized_transaction_ids:
        raise ValueError("transactions must exactly match the economic event")
    raw_ids = tuple(sorted(item.raw_record_id for item in items))
    if raw_ids != event.raw_record_ids:
        raise ValueError("raw lineage must exactly match the economic event")
    postings = tuple(
        LedgerPosting(
            normalized_transaction_id=item.normalized_transaction_id,
            account_ref=item.account_ref,
            direction=item.direction,
            amount=item.amount,
            currency=item.currency,
        )
        for item in sorted(items, key=lambda item: item.normalized_transaction_id)
    )
    idempotency_payload = {
        "economic_event_id": event.economic_event_id,
        "interconnection_group_id": event.interconnection_group_id,
        "raw_record_ids": list(raw_ids),
        "normalized_transaction_ids": list(item_ids),
        "event_type": event.event_type,
        "occurred_at": event.event_time,
        "policy_version": event.policy_version,
        "policy_hash": event.policy_hash,
        "impact_flags": event.impact_flags.to_dict(),
        "offset_economic_event_id": event.offset_economic_event_id,
        "postings": [item.to_dict() for item in postings],
    }
    idempotency_key = _payload_hash(idempotency_payload)
    return LedgerEvent(
        ledger_event_id=_stable_id("ledger_event", idempotency_key),
        idempotency_key=idempotency_key,
        raw_record_ids=raw_ids,
        normalized_transaction_ids=item_ids,
        interconnection_group_id=event.interconnection_group_id,
        economic_event_id=event.economic_event_id,
        event_type=event.event_type,
        occurred_at=event.event_time,
        postings=postings,
        impact_flags=event.impact_flags,
        policy_version=event.policy_version,
        offset_economic_event_id=event.offset_economic_event_id,
    )


def build_schema_inventory(schema_root: Path | str = SCHEMA_ROOT) -> dict[str, Any]:
    root = Path(schema_root)
    hashes: dict[str, str] = {}
    for filename in SCHEMA_FILES:
        schema = json.loads((root / filename).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        hashes[filename] = "sha256:" + hashlib.sha256((root / filename).read_bytes()).hexdigest()
    return {
        "schema": "PFIV025Stage3Phase32SchemaInventoryV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "schema_count": len(hashes),
        "schemas": hashes,
        "real_financial_data_read": False,
    }


def build_event_type_matrix(policy_path: Path | str = POLICY_PATH) -> dict[str, Any]:
    policy = load_phase32_policy(policy_path)
    event_types = [
        {"event_type": event_type, "impact_flags": dict(policy["event_types"][event_type])}
        for event_type in sorted(policy["event_types"])
    ]
    return {
        "schema": "PFIV025Stage3Phase32EventTypeMatrixV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "policy_version": policy["policy_version"],
        "policy_hash": _payload_hash(policy),
        "event_type_count": len(event_types),
        "event_types": event_types,
        "unknown_event_type_policy": policy["unknown_event_type_policy"],
        "same_economic_event_per_metric_max_count": policy["same_economic_event_per_metric_max_count"],
        "financial_values_emitted": 0,
    }


def build_lineage_samples_redacted() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3Phase32RedactedLineageV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "lineage_order": [
            "raw_record_id_hash",
            "normalized_transaction_id",
            "interconnection_group_id",
            "economic_event_id",
            "ledger_event_id",
            "idempotency_key",
        ],
        "redacted_sample": {
            "raw_record_id_hash": "sha256:" + "0" * 64,
            "normalized_transaction_id": "normalized_transaction_redacted",
            "interconnection_group_id": "interconnection_group_redacted",
            "economic_event_id": "economic_event_redacted",
            "ledger_event_id": "ledger_event_redacted",
            "idempotency_key": "sha256:" + "0" * 64,
        },
        "financial_values_emitted": 0,
        "private_identifiers_emitted": 0,
        "real_financial_data_read": False,
    }


def _require_unique_transactions(items: tuple[NormalizedTransaction, ...]) -> None:
    if not items:
        raise ValueError("transactions must not be empty")
    identifiers = tuple(item.normalized_transaction_id for item in items)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("normalized_transaction_id values must be unique")


def _require_rfc3339(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} is required")
    clean = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"
