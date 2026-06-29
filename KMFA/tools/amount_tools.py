#!/usr/bin/env python3
"""KMFA S04-P1 strict amount normalization utilities."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class AmountNormalizationError(ValueError):
    """Raised when an amount cannot be safely normalized to integer cents."""


UNIT_MULTIPLIERS = {
    "yuan": Decimal("1"),
    "cny": Decimal("1"),
    "rmb": Decimal("1"),
    "wan_yuan": Decimal("10000"),
    "ten_thousand_yuan": Decimal("10000"),
    "qian_yuan": Decimal("1000"),
    "thousand_yuan": Decimal("1000"),
}
BLANK_MARKERS = {"", "-", "--", "---", "#", "##", "###", "n/a", "na", "null", "none"}
MINUS_CHARS = {"-", "\u2212", "\uff0d", "\u2013", "\u2014"}
NUMERIC_RE = re.compile(r"(?:\d+(?:\.\d+)?|\.\d+)")


def _reject_float(value: Any) -> None:
    if isinstance(value, float):
        raise AmountNormalizationError("business money must not be provided as float")


def _normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    normalized = str(unit).strip().lower().replace("-", "_")
    if normalized in {"", "auto"}:
        return None
    if normalized not in UNIT_MULTIPLIERS:
        raise AmountNormalizationError(f"unsupported amount unit: {unit!r}")
    return normalized


def _extract_text_unit(text: str) -> tuple[str, str | None]:
    if "万元" in text:
        return text.replace("万元", ""), "wan_yuan"
    if "万" in text:
        return text.replace("万", ""), "wan_yuan"
    if "千元" in text:
        return text.replace("千元", ""), "qian_yuan"
    if "元" in text:
        return text.replace("元", ""), "yuan"
    return text, None


def _normalize_text_amount(value: str, unit: str | None) -> tuple[Decimal, str]:
    text = unicodedata.normalize("NFKC", value).strip()
    marker = text.lower().replace(" ", "")
    if marker in BLANK_MARKERS:
        raise AmountNormalizationError("blank, dash, hash, or null amount cannot default to zero")

    is_negative = False
    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1].strip()

    if text and text[0] in MINUS_CHARS:
        is_negative = True
        text = text[1:].strip()
    elif text.startswith("+"):
        text = text[1:].strip()

    text = (
        text.replace("人民币", "")
        .replace("RMB", "")
        .replace("rmb", "")
        .replace("CNY", "")
        .replace("cny", "")
        .replace("￥", "")
        .replace("¥", "")
        .replace(",", "")
        .replace("，", "")
        .strip()
    )
    text, embedded_unit = _extract_text_unit(text)
    explicit_unit = _normalize_unit(unit)
    resolved_unit = embedded_unit or explicit_unit or "yuan"
    if embedded_unit and explicit_unit and embedded_unit != explicit_unit:
        raise AmountNormalizationError(f"conflicting amount units: text={embedded_unit}, unit={explicit_unit}")

    text = text.strip()
    if not text or "#" in text:
        raise AmountNormalizationError("blank or hash amount cannot default to zero")
    if not NUMERIC_RE.fullmatch(text):
        raise AmountNormalizationError(f"invalid amount text: {value!r}")

    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise AmountNormalizationError(f"invalid decimal amount: {value!r}") from exc
    if is_negative:
        amount = -amount
    return amount, resolved_unit


def _normalize_numeric_amount(value: int | Decimal, unit: str | None) -> tuple[Decimal, str]:
    if isinstance(value, bool):
        raise AmountNormalizationError("boolean is not a valid business amount")
    resolved_unit = _normalize_unit(unit) or "yuan"
    if isinstance(value, Decimal):
        return value, resolved_unit
    return Decimal(value), resolved_unit


def normalize_amount_to_cents(value: str | int | Decimal, *, unit: str | None = None) -> int:
    """Normalize an amount to integer cents without float arithmetic."""

    _reject_float(value)
    if isinstance(value, str):
        amount, resolved_unit = _normalize_text_amount(value, unit)
    elif isinstance(value, (int, Decimal)) and not isinstance(value, bool):
        amount, resolved_unit = _normalize_numeric_amount(value, unit)
    else:
        raise AmountNormalizationError(f"unsupported amount type: {type(value).__name__}")

    cents = amount * UNIT_MULTIPLIERS[resolved_unit] * Decimal("100")
    integral_cents = cents.to_integral_value()
    if cents != integral_cents:
        raise AmountNormalizationError(f"amount cannot be represented as integer cents: {value!r}")
    return int(integral_cents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a KMFA business amount to integer cents.")
    parser.add_argument("amount")
    parser.add_argument("--unit", default=None)
    args = parser.parse_args(argv)
    cents = normalize_amount_to_cents(args.amount, unit=args.unit)
    print(json.dumps({"amount_cents": cents}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
