from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


_TOKEN_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_AMOUNT_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_DIRECTIONS = {"inflow", "outflow", "neutral"}
_NET_WORTH_EFFECTS = {"increase", "decrease", "neutral", "composition_only", "reversal"}
_CASH_EFFECTS = {"inflow", "outflow", "neutral", "mixed"}


@dataclass(frozen=True)
class NormalizedTransaction:
    normalized_transaction_id: str
    raw_record_id: str
    source_id: str
    account_ref: str
    source_record_hash: str
    amount: str
    currency: str
    direction: str
    transaction_time: str
    posted_at: str
    effective_at: str
    imported_at: str
    link_reference: str | None = None
    normalization_version: str = "1"

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.normalized_transaction_id, "normalized_transaction_id"),
            (self.raw_record_id, "raw_record_id"),
            (self.source_id, "source_id"),
            (self.account_ref, "account_ref"),
        ):
            _require_token(value, field_name)
        if not self.normalized_transaction_id.startswith("normalized_transaction_"):
            raise ValueError("normalized_transaction_id must use normalized_transaction_ prefix")
        _require_hash(self.source_record_hash, "source_record_hash")
        _require_amount(self.amount)
        if not _CURRENCY_RE.fullmatch(self.currency):
            raise ValueError("currency must be a three-letter uppercase code")
        if self.direction not in _DIRECTIONS:
            raise ValueError(f"unsupported direction: {self.direction}")
        for value, field_name in (
            (self.transaction_time, "transaction_time"),
            (self.posted_at, "posted_at"),
            (self.effective_at, "effective_at"),
            (self.imported_at, "imported_at"),
        ):
            _require_rfc3339(value, field_name)
        if self.link_reference is not None:
            _require_token(self.link_reference, "link_reference")
        _require_version(self.normalization_version, "normalization_version")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "normalized_transaction_id": self.normalized_transaction_id,
            "raw_record_id": self.raw_record_id,
            "source_id": self.source_id,
            "account_ref": self.account_ref,
            "source_record_hash": self.source_record_hash,
            "amount": self.amount,
            "currency": self.currency,
            "direction": self.direction,
            "transaction_time": self.transaction_time,
            "posted_at": self.posted_at,
            "effective_at": self.effective_at,
            "imported_at": self.imported_at,
            "normalization_version": self.normalization_version,
        }
        if self.link_reference is not None:
            payload["link_reference"] = self.link_reference
        return payload


@dataclass(frozen=True)
class InterconnectionGroup:
    interconnection_group_id: str
    normalized_transaction_ids: tuple[str, ...]
    grouping_rule_id: str
    rule_version: str
    rule_hash: str
    reason_codes: tuple[str, ...]
    created_at: str
    link_reference_hash: str | None = None

    def __post_init__(self) -> None:
        _require_token(self.interconnection_group_id, "interconnection_group_id")
        if not self.interconnection_group_id.startswith("interconnection_group_"):
            raise ValueError("interconnection_group_id must use interconnection_group_ prefix")
        normalized_ids = tuple(sorted(set(self.normalized_transaction_ids)))
        if not normalized_ids or len(normalized_ids) != len(self.normalized_transaction_ids):
            raise ValueError("normalized_transaction_ids must be non-empty and unique")
        for item in normalized_ids:
            _require_token(item, "normalized_transaction_id")
        object.__setattr__(self, "normalized_transaction_ids", normalized_ids)
        _require_token(self.grouping_rule_id, "grouping_rule_id")
        _require_version(self.rule_version, "rule_version")
        _require_hash(self.rule_hash, "rule_hash")
        reasons = tuple(sorted(set(self.reason_codes)))
        if not reasons:
            raise ValueError("reason_codes must not be empty")
        for item in reasons:
            _require_token(item, "reason_code")
        object.__setattr__(self, "reason_codes", reasons)
        _require_rfc3339(self.created_at, "created_at")
        if self.link_reference_hash is not None:
            _require_hash(self.link_reference_hash, "link_reference_hash")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "interconnection_group_id": self.interconnection_group_id,
            "normalized_transaction_ids": list(self.normalized_transaction_ids),
            "grouping_rule_id": self.grouping_rule_id,
            "rule_version": self.rule_version,
            "rule_hash": self.rule_hash,
            "reason_codes": list(self.reason_codes),
            "created_at": self.created_at,
        }
        if self.link_reference_hash is not None:
            payload["link_reference_hash"] = self.link_reference_hash
        return payload


@dataclass(frozen=True)
class ImpactFlags:
    net_worth_effect: str
    cash_effect: str
    living_consumption_included: bool
    activity_outflow_included: bool
    investment_allocation_included: bool
    requires_offset_event_id: bool
    fee_tax_requires_separate_event: bool

    def __post_init__(self) -> None:
        if self.net_worth_effect not in _NET_WORTH_EFFECTS:
            raise ValueError(f"unsupported net_worth_effect: {self.net_worth_effect}")
        if self.cash_effect not in _CASH_EFFECTS:
            raise ValueError(f"unsupported cash_effect: {self.cash_effect}")
        for value, field_name in (
            (self.living_consumption_included, "living_consumption_included"),
            (self.activity_outflow_included, "activity_outflow_included"),
            (self.investment_allocation_included, "investment_allocation_included"),
            (self.requires_offset_event_id, "requires_offset_event_id"),
            (self.fee_tax_requires_separate_event, "fee_tax_requires_separate_event"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{field_name} must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_worth_effect": self.net_worth_effect,
            "cash_effect": self.cash_effect,
            "living_consumption_included": self.living_consumption_included,
            "activity_outflow_included": self.activity_outflow_included,
            "investment_allocation_included": self.investment_allocation_included,
            "requires_offset_event_id": self.requires_offset_event_id,
            "fee_tax_requires_separate_event": self.fee_tax_requires_separate_event,
        }


@dataclass(frozen=True)
class EconomicEvent:
    economic_event_id: str
    interconnection_group_id: str
    raw_record_ids: tuple[str, ...]
    normalized_transaction_ids: tuple[str, ...]
    event_type: str
    event_time: str
    currencies: tuple[str, ...]
    policy_version: str
    policy_hash: str
    impact_flags: ImpactFlags
    offset_economic_event_id: str | None = None
    status: str = "candidate"

    def __post_init__(self) -> None:
        _require_token(self.economic_event_id, "economic_event_id")
        if not self.economic_event_id.startswith("economic_event_"):
            raise ValueError("economic_event_id must use economic_event_ prefix")
        _require_token(self.interconnection_group_id, "interconnection_group_id")
        _require_unique_tokens(self.raw_record_ids, "raw_record_ids")
        _require_unique_tokens(self.normalized_transaction_ids, "normalized_transaction_ids")
        object.__setattr__(self, "raw_record_ids", tuple(sorted(self.raw_record_ids)))
        object.__setattr__(self, "normalized_transaction_ids", tuple(sorted(self.normalized_transaction_ids)))
        _require_token(self.event_type, "event_type")
        _require_rfc3339(self.event_time, "event_time")
        currencies = tuple(sorted(set(self.currencies)))
        if not currencies or len(currencies) != len(self.currencies):
            raise ValueError("currencies must be non-empty and unique")
        if not all(_CURRENCY_RE.fullmatch(item) for item in currencies):
            raise ValueError("currencies must use three-letter uppercase codes")
        object.__setattr__(self, "currencies", currencies)
        _require_version(self.policy_version, "policy_version")
        _require_hash(self.policy_hash, "policy_hash")
        if self.impact_flags.requires_offset_event_id:
            if self.offset_economic_event_id is None:
                raise ValueError("offset_economic_event_id is required by event policy")
            _require_token(self.offset_economic_event_id, "offset_economic_event_id")
            if not self.offset_economic_event_id.startswith("economic_event_"):
                raise ValueError("offset_economic_event_id must use economic_event_ prefix")
        elif self.offset_economic_event_id is not None:
            raise ValueError("offset_economic_event_id is only allowed when required by event policy")
        if self.status != "candidate":
            raise ValueError("new economic events must have candidate status")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "economic_event_id": self.economic_event_id,
            "interconnection_group_id": self.interconnection_group_id,
            "raw_record_ids": list(self.raw_record_ids),
            "normalized_transaction_ids": list(self.normalized_transaction_ids),
            "event_type": self.event_type,
            "event_time": self.event_time,
            "currencies": list(self.currencies),
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "impact_flags": self.impact_flags.to_dict(),
            "status": self.status,
        }
        if self.offset_economic_event_id is not None:
            payload["offset_economic_event_id"] = self.offset_economic_event_id
        return payload


@dataclass(frozen=True)
class LedgerPosting:
    normalized_transaction_id: str
    account_ref: str
    direction: str
    amount: str
    currency: str

    def __post_init__(self) -> None:
        _require_token(self.normalized_transaction_id, "normalized_transaction_id")
        _require_token(self.account_ref, "account_ref")
        if self.direction not in _DIRECTIONS:
            raise ValueError(f"unsupported direction: {self.direction}")
        _require_amount(self.amount)
        if not _CURRENCY_RE.fullmatch(self.currency):
            raise ValueError("currency must be a three-letter uppercase code")

    def to_dict(self) -> dict[str, str]:
        return {
            "normalized_transaction_id": self.normalized_transaction_id,
            "account_ref": self.account_ref,
            "direction": self.direction,
            "amount": self.amount,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class LedgerEvent:
    ledger_event_id: str
    idempotency_key: str
    raw_record_ids: tuple[str, ...]
    normalized_transaction_ids: tuple[str, ...]
    interconnection_group_id: str
    economic_event_id: str
    event_type: str
    occurred_at: str
    postings: tuple[LedgerPosting, ...]
    impact_flags: ImpactFlags
    policy_version: str
    offset_economic_event_id: str | None = None
    status: str = "candidate"

    def __post_init__(self) -> None:
        _require_token(self.ledger_event_id, "ledger_event_id")
        if not self.ledger_event_id.startswith("ledger_event_"):
            raise ValueError("ledger_event_id must use ledger_event_ prefix")
        _require_hash(self.idempotency_key, "idempotency_key")
        _require_unique_tokens(self.raw_record_ids, "raw_record_ids")
        _require_unique_tokens(self.normalized_transaction_ids, "normalized_transaction_ids")
        object.__setattr__(self, "raw_record_ids", tuple(sorted(self.raw_record_ids)))
        object.__setattr__(self, "normalized_transaction_ids", tuple(sorted(self.normalized_transaction_ids)))
        _require_token(self.interconnection_group_id, "interconnection_group_id")
        _require_token(self.economic_event_id, "economic_event_id")
        _require_token(self.event_type, "event_type")
        _require_rfc3339(self.occurred_at, "occurred_at")
        postings = tuple(sorted(self.postings, key=lambda item: item.normalized_transaction_id))
        posting_ids = tuple(item.normalized_transaction_id for item in postings)
        if not postings or len(posting_ids) != len(set(posting_ids)):
            raise ValueError("postings must be non-empty with unique normalized transaction ids")
        if posting_ids != tuple(sorted(self.normalized_transaction_ids)):
            raise ValueError("postings must cover every normalized_transaction_id exactly once")
        object.__setattr__(self, "postings", postings)
        _require_version(self.policy_version, "policy_version")
        if self.impact_flags.requires_offset_event_id:
            if self.offset_economic_event_id is None:
                raise ValueError("offset_economic_event_id is required by event policy")
            _require_token(self.offset_economic_event_id, "offset_economic_event_id")
        elif self.offset_economic_event_id is not None:
            raise ValueError("offset_economic_event_id is only allowed when required by event policy")
        if self.status != "candidate":
            raise ValueError("new ledger events must have candidate status")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ledger_event_id": self.ledger_event_id,
            "idempotency_key": self.idempotency_key,
            "raw_record_ids": list(self.raw_record_ids),
            "normalized_transaction_ids": list(self.normalized_transaction_ids),
            "interconnection_group_id": self.interconnection_group_id,
            "economic_event_id": self.economic_event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "postings": [item.to_dict() for item in self.postings],
            "impact_flags": self.impact_flags.to_dict(),
            "policy_version": self.policy_version,
            "status": self.status,
        }
        if self.offset_economic_event_id is not None:
            payload["offset_economic_event_id"] = self.offset_economic_event_id
        return payload


def _require_amount(value: str) -> None:
    if not isinstance(value, str) or not _AMOUNT_RE.fullmatch(value):
        raise ValueError("amount must be a positive canonical decimal string with at most six places")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("amount must be decimal") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError("amount must be greater than zero")


def _require_hash(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be sha256:<64 lowercase hex>")


def _require_rfc3339(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    clean = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _require_token(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase namespaced token")


def _require_unique_tokens(values: tuple[str, ...], field_name: str) -> None:
    if not values or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be non-empty and unique")
    for value in values:
        _require_token(value, field_name)


def _require_version(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be non-empty without whitespace")
