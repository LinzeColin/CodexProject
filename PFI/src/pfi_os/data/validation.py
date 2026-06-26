from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from pfi_os.config import report_date_dir
from pfi_os.data.models import BarDataRequest
from pfi_os.data.providers.factory import make_provider


@dataclass(frozen=True)
class CrossSourceValidationResult:
    symbol: str
    market: str
    interval: str
    providers: tuple[str, ...]
    overlap_rows: int
    max_close_diff_pct: float
    mean_close_diff_pct: float
    status: str
    details: pd.DataFrame

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["details"] = self.details.to_dict(orient="records") if not self.details.empty else []
        return payload


def validate_close_across_sources(
    provider_names: list[str],
    request: BarDataRequest,
    tolerance_pct: float = 0.01,
) -> CrossSourceValidationResult:
    if len(provider_names) < 2:
        raise ValueError("At least two providers are required for cross-source validation.")

    frames = []
    for provider_name in provider_names:
        provider = make_provider(provider_name)
        data = provider.get_bars(request)
        if data.empty:
            continue
        frame = data[["datetime", "close"]].copy()
        frame["datetime"] = pd.to_datetime(frame["datetime"]).dt.normalize()
        frame = frame.rename(columns={"close": provider.name})
        frames.append(frame)

    if len(frames) < 2:
        return CrossSourceValidationResult(
            symbol=request.symbol,
            market=request.market,
            interval=request.interval,
            providers=tuple(provider_names),
            overlap_rows=0,
            max_close_diff_pct=0.0,
            mean_close_diff_pct=0.0,
            status="InsufficientData",
            details=pd.DataFrame(),
        )

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="datetime", how="inner")
    provider_columns = [col for col in merged.columns if col != "datetime"]
    if merged.empty:
        return CrossSourceValidationResult(
            symbol=request.symbol,
            market=request.market,
            interval=request.interval,
            providers=tuple(provider_columns),
            overlap_rows=0,
            max_close_diff_pct=0.0,
            mean_close_diff_pct=0.0,
            status="NoOverlap",
            details=merged,
        )

    max_price = merged[provider_columns].max(axis=1)
    min_price = merged[provider_columns].min(axis=1)
    reference = merged[provider_columns].mean(axis=1).replace(0, pd.NA)
    merged["close_diff_pct"] = ((max_price - min_price) / reference).fillna(0.0)
    max_diff = float(merged["close_diff_pct"].max())
    mean_diff = float(merged["close_diff_pct"].mean())
    status = "Pass" if max_diff <= tolerance_pct else "Review"
    return CrossSourceValidationResult(
        symbol=request.symbol,
        market=request.market,
        interval=request.interval,
        providers=tuple(provider_columns),
        overlap_rows=int(len(merged)),
        max_close_diff_pct=max_diff,
        mean_close_diff_pct=mean_diff,
        status=status,
        details=merged,
    )


def save_cross_source_validation_result(result: CrossSourceValidationResult, output_dir: Path | str | None = None) -> Path:
    root = Path(output_dir) if output_dir is not None else report_date_dir() / "CrossValidation"
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    provider_slug = "_".join(result.providers) if result.providers else "providers"
    path = root / f"CrossValidation_{result.market}_{result.symbol}_{provider_slug}_{timestamp}.json"
    path.write_text(json.dumps(result.to_payload(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path
