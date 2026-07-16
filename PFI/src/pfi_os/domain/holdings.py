"""Traceable holding and cost-basis contracts for PFI v0.2.5 Stage 4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import re


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_COST_BASIS_METHODS = frozenset(
    {"source_reported", "specific_identification", "fifo", "weighted_average"}
)
_TRANSACTION_LINK_STATUSES = frozenset({"linked", "source_snapshot_only"})


def require_decimal(name: str, value: object, *, non_negative: bool = False) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if non_negative and value < 0:
        raise ValueError(f"{name} must be non-negative")


def require_aware_datetime(name: str, value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")


def require_sha256(name: str, value: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")


def require_currency(name: str, value: str) -> None:
    if not _CURRENCY_RE.fullmatch(value):
        raise ValueError(f"{name} must be a three-letter uppercase currency code")


@dataclass(frozen=True, slots=True)
class HoldingSnapshot:
    """A source-proven position snapshot with an explicit cost-basis policy.

    Runtime references are opaque. They must not be copied into tracked public
    evidence. A ready snapshot either links to explicit economic-event ids or
    declares that the source snapshot is the only quantity lineage; neither
    mode permits transaction-based quantity inference.
    """

    snapshot_id: str
    account_ref: str
    instrument_ref: str
    source_id: str
    quantity: Decimal
    acquisition_cost_ex_fees: Decimal
    capitalized_fee_total: Decimal
    original_currency: str
    cost_basis_method: str
    transaction_link_status: str
    transaction_event_ids: tuple[str, ...]
    quantity_as_of: datetime
    source_record_count: int
    source_content_hash: str

    def __post_init__(self) -> None:
        for name in ("snapshot_id", "account_ref", "instrument_ref"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must not be empty")
        if self.source_id != "SRC-HOLDINGS":
            raise ValueError("source_id must be SRC-HOLDINGS")
        require_decimal("quantity", self.quantity)
        require_decimal("acquisition_cost_ex_fees", self.acquisition_cost_ex_fees)
        require_decimal("capitalized_fee_total", self.capitalized_fee_total, non_negative=True)
        require_currency("original_currency", self.original_currency)
        if self.cost_basis_method not in _COST_BASIS_METHODS:
            raise ValueError(
                "cost_basis_method must be source_reported, specific_identification, "
                "fifo or weighted_average"
            )
        if self.transaction_link_status not in _TRANSACTION_LINK_STATUSES:
            raise ValueError("transaction_link_status must be linked or source_snapshot_only")
        if not isinstance(self.transaction_event_ids, tuple):
            raise TypeError("transaction_event_ids must be a tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.transaction_event_ids):
            raise ValueError("transaction_event_ids must contain only non-empty opaque ids")
        if len(set(self.transaction_event_ids)) != len(self.transaction_event_ids):
            raise ValueError("transaction_event_ids must not contain duplicates")
        if self.transaction_link_status == "linked" and not self.transaction_event_ids:
            raise ValueError("transaction_event_ids are required when transaction_link_status is linked")
        if self.transaction_link_status == "source_snapshot_only" and self.transaction_event_ids:
            raise ValueError(
                "transaction_event_ids must be empty when transaction_link_status is source_snapshot_only"
            )
        require_aware_datetime("quantity_as_of", self.quantity_as_of)
        if isinstance(self.source_record_count, bool) or not isinstance(self.source_record_count, int):
            raise TypeError("source_record_count must be an integer")
        if self.source_record_count < 1:
            raise ValueError("source_record_count must be positive")
        require_sha256("source_content_hash", self.source_content_hash)

    @property
    def cost_basis_original(self) -> Decimal:
        """Return the explicit fee-inclusive cost basis without rounding."""

        return self.acquisition_cost_ex_fees + self.capitalized_fee_total
