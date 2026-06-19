from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = {
    "asset_code",
    "asset_name",
    "platform",
    "current_amount",
    "current_weight",
    "cost_basis",
    "unrealized_pnl",
    "as_of",
    "source_note",
}


@dataclass(frozen=True)
class ImportResult:
    rows: list[dict[str, object]]
    warnings: list[str]


def _to_float(value: str, field: str) -> float:
    raw = (value or "").strip().replace(",", "")
    if raw.endswith("%"):
        return float(raw[:-1]) / 100.0
    if raw == "":
        return 0.0
    parsed = float(raw)
    if field == "current_weight" and parsed > 1:
        return parsed / 100.0
    return parsed


def read_positions_csv(path: Path) -> ImportResult:
    if not path.exists():
        raise FileNotFoundError(f"Alipay CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"Alipay CSV missing required columns: {', '.join(missing)}")

        rows: list[dict[str, object]] = []
        for line_no, raw in enumerate(reader, start=2):
            asset_code = (raw["asset_code"] or "").strip()
            if not asset_code:
                raise ValueError(f"Line {line_no}: asset_code is required")
            rows.append(
                {
                    "asset_code": asset_code,
                    "asset_name": (raw["asset_name"] or "").strip(),
                    "platform": (raw["platform"] or "Alipay").strip(),
                    "current_amount": _to_float(raw["current_amount"], "current_amount"),
                    "current_weight": _to_float(raw["current_weight"], "current_weight"),
                    "cost_basis": _to_float(raw["cost_basis"], "cost_basis"),
                    "unrealized_pnl": _to_float(raw["unrealized_pnl"], "unrealized_pnl"),
                    "as_of": (raw["as_of"] or "").strip(),
                    "source_note": (raw["source_note"] or "").strip(),
                }
            )

    warnings: list[str] = []
    weight_sum = sum(float(row["current_weight"]) for row in rows)
    if rows and abs(weight_sum - 1.0) > 0.02:
        warnings.append(f"Current weights sum to {weight_sum:.2%}, outside +/-2.00% tolerance")
    return ImportResult(rows=rows, warnings=warnings)
