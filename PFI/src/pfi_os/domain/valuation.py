"""Point-in-time price and FX contracts for PFI v0.2.5 Stage 4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pfi_os.domain.holdings import (
    require_aware_datetime,
    require_currency,
    require_decimal,
    require_sha256,
)


@dataclass(frozen=True, slots=True)
class MarketPriceSnapshot:
    snapshot_id: str
    instrument_ref: str
    source_id: str
    price: Decimal
    currency: str
    price_as_of: datetime
    source_content_hash: str

    def __post_init__(self) -> None:
        for name in ("snapshot_id", "instrument_ref"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must not be empty")
        if self.source_id != "SRC-MARKET-PRICES":
            raise ValueError("source_id must be SRC-MARKET-PRICES")
        require_decimal("price", self.price)
        if self.price <= 0:
            raise ValueError("price must be positive")
        require_currency("currency", self.currency)
        require_aware_datetime("price_as_of", self.price_as_of)
        require_sha256("source_content_hash", self.source_content_hash)

@dataclass(frozen=True, slots=True)
class FxRateSnapshot:
    snapshot_id: str
    source_id: str
    base_currency: str
    quote_currency: str
    direction: str
    rate: Decimal
    fx_effective_at: datetime
    source_content_hash: str

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id must not be empty")
        if self.source_id != "SRC-FX-SNAPSHOT":
            raise ValueError("source_id must be SRC-FX-SNAPSHOT")
        require_currency("base_currency", self.base_currency)
        require_currency("quote_currency", self.quote_currency)
        if self.quote_currency != "CNY":
            raise ValueError("quote_currency must be CNY")
        expected_direction = f"{self.base_currency}_TO_CNY"
        if self.direction != expected_direction:
            raise ValueError(f"direction must be {expected_direction}")
        require_decimal("rate", self.rate)
        if self.rate <= 0:
            raise ValueError("rate must be positive")
        require_aware_datetime("fx_effective_at", self.fx_effective_at)
        require_sha256("source_content_hash", self.source_content_hash)
