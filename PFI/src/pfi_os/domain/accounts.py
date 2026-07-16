"""Account and liability snapshot contracts for PFI v0.2.5 Stage 4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import re


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_decimal(name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")


def _require_lineage(
    *,
    source_ids: tuple[str, ...],
    coverage_start: date,
    coverage_end: date,
    data_as_of: date,
    source_content_hash: str,
) -> None:
    if not source_ids or any(not item.strip() for item in source_ids):
        raise ValueError("source_ids must contain at least one non-empty source id")
    if coverage_start > coverage_end:
        raise ValueError("coverage_start must be on or before coverage_end")
    if data_as_of < coverage_end:
        raise ValueError("data_as_of must be on or after coverage_end")
    if not _SHA256_RE.fullmatch(source_content_hash):
        raise ValueError("source_content_hash must be a sha256 digest")


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """A source-proven opening/closing balance or liability snapshot.

    ``account_ref`` is an opaque runtime reference. It must not be copied into
    tracked public evidence; Phase 4.1 reports aggregate source state only.
    """

    snapshot_id: str
    snapshot_kind: str
    account_ref: str
    source_id: str
    currency: str
    opening_balance: Decimal
    closing_balance: Decimal
    coverage_start: date
    coverage_end: date
    data_as_of: date
    source_record_count: int
    source_content_hash: str

    def __post_init__(self) -> None:
        if self.snapshot_kind not in {"cash_account", "liability"}:
            raise ValueError("snapshot_kind must be cash_account or liability")
        expected_source = {
            "cash_account": "SRC-ACCOUNT-BALANCES",
            "liability": "SRC-LIABILITIES",
        }[self.snapshot_kind]
        if self.source_id != expected_source:
            raise ValueError(f"source_id must be {expected_source} for {self.snapshot_kind}")
        for name in ("snapshot_id", "account_ref", "source_id", "currency"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must not be empty")
        _require_decimal("opening_balance", self.opening_balance)
        _require_decimal("closing_balance", self.closing_balance)
        if self.source_record_count < 1:
            raise ValueError("source_record_count must be positive")
        _require_lineage(
            source_ids=(self.source_id,),
            coverage_start=self.coverage_start,
            coverage_end=self.coverage_end,
            data_as_of=self.data_as_of,
            source_content_hash=self.source_content_hash,
        )


@dataclass(frozen=True, slots=True)
class CashReconciliationInput:
    """Complete evidence required before the cash formula may run."""

    opening_balance: Decimal
    confirmed_net_flows: Decimal
    adjustments: Decimal
    observed_closing_balance: Decimal
    currency: str
    source_ids: tuple[str, ...]
    coverage_start: date
    coverage_end: date
    data_as_of: date
    source_content_hash: str

    def __post_init__(self) -> None:
        for name in (
            "opening_balance",
            "confirmed_net_flows",
            "adjustments",
            "observed_closing_balance",
        ):
            _require_decimal(name, getattr(self, name))
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("currency must be a three-letter uppercase code")
        _require_lineage(
            source_ids=self.source_ids,
            coverage_start=self.coverage_start,
            coverage_end=self.coverage_end,
            data_as_of=self.data_as_of,
            source_content_hash=self.source_content_hash,
        )
