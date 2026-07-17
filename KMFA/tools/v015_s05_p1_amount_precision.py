#!/usr/bin/env python3
"""Financial-grade amount, rounding, and unit contracts for KMFA v1.5 S05-P1.

The module is deliberately independent from raw files and locale-specific
parsers.  Every unit is explicit, floats are rejected, fractional-cent results
require a named rounding rule at its registered finalization point, and public
serialization contains integer cents only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from types import MappingProxyType
from typing import Any, Mapping


RUN_PHASE_ID = "V015_S05_P1_AMOUNT_PRECISION"
TASK_ID = "KMFA-V015-S05-P1-AMOUNT-PRECISION-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S05-P1-AMOUNT-PRECISION"
VERSION = "1.5.0-dev-s05p1"

MONEY_DIMENSION = "MONEY_CNY"
QUANTITY_DIMENSION = "QUANTITY_MASS_KG"
COUNT_DIMENSION = "QUANTITY_COUNT"
_NUMBER_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$")


class AmountPrecisionError(ValueError):
    """Fail-closed amount error carrying a stable route/action."""

    def __init__(self, code: str, message: str, *, action: str = "BLOCK_CALCULATION") -> None:
        super().__init__(message)
        self.code = code
        self.action = action


@dataclass(frozen=True)
class UnitDefinition:
    unit_id: str
    dimension: str
    scale_to_base: Decimal
    symbols: tuple[str, ...]


UNIT_DEFINITIONS = (
    UnitDefinition("fen", MONEY_DIMENSION, Decimal("0.01"), ("fen", "分")),
    UnitDefinition("yuan", MONEY_DIMENSION, Decimal("1"), ("yuan", "元", "CNY", "RMB")),
    UnitDefinition("wan_yuan", MONEY_DIMENSION, Decimal("10000"), ("wan_yuan", "万元")),
    UnitDefinition("count", COUNT_DIMENSION, Decimal("1"), ("count", "unit", "个", "件")),
    UnitDefinition("kg", QUANTITY_DIMENSION, Decimal("1"), ("kg", "公斤", "千克")),
    UnitDefinition("tonne", QUANTITY_DIMENSION, Decimal("1000"), ("tonne", "ton", "吨")),
)


def _unit_lookup() -> dict[str, UnitDefinition]:
    lookup: dict[str, UnitDefinition] = {}
    for definition in UNIT_DEFINITIONS:
        for symbol in definition.symbols:
            key = symbol.strip().lower()
            if key in lookup:
                raise RuntimeError(f"duplicate unit alias: {symbol}")
            lookup[key] = definition
    return lookup


UNIT_LOOKUP: Mapping[str, UnitDefinition] = MappingProxyType(_unit_lookup())


@dataclass(frozen=True)
class RoundingRule:
    rule_id: str
    domain: str
    point: str
    quantum_cents: int
    mode: str


ROUNDING_RULES: Mapping[str, RoundingRule] = MappingProxyType({
    "SOURCE_EXACT_CENT": RoundingRule(
        "SOURCE_EXACT_CENT", "SOURCE_FIELD", "SOURCE_INGEST", 1, "EXACT"
    ),
    "TAX_HALF_UP_CENT": RoundingRule(
        "TAX_HALF_UP_CENT", "TAX", "TAX_FINALIZATION", 1, "ROUND_HALF_UP"
    ),
    "ALLOCATION_HALF_UP_CENT": RoundingRule(
        "ALLOCATION_HALF_UP_CENT", "ALLOCATION", "ALLOCATION_FINALIZATION", 1, "ROUND_HALF_UP"
    ),
    "REPORT_HALF_EVEN_YUAN": RoundingRule(
        "REPORT_HALF_EVEN_YUAN", "REPORT", "REPORT_PRESENTATION", 100, "ROUND_HALF_EVEN"
    ),
})


def _as_decimal(value: str | int | Decimal, field: str) -> Decimal:
    if isinstance(value, bool):
        raise AmountPrecisionError("BOOLEAN_NOT_NUMERIC", f"{field} cannot be boolean")
    if isinstance(value, float):
        raise AmountPrecisionError("FLOAT_MONEY_FORBIDDEN", f"{field} cannot be float")
    if isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, str):
        text = value.strip()
        if not _NUMBER_RE.fullmatch(text):
            raise AmountPrecisionError("INVALID_DECIMAL_TEXT", f"{field} must be canonical decimal text")
        try:
            decimal_value = Decimal(text)
        except InvalidOperation as error:
            raise AmountPrecisionError("INVALID_DECIMAL_TEXT", f"{field} is invalid") from error
    else:
        raise AmountPrecisionError("UNSUPPORTED_NUMERIC_TYPE", f"{field} has unsupported type")
    if not decimal_value.is_finite():
        raise AmountPrecisionError("NON_FINITE_VALUE", f"{field} must be finite")
    return decimal_value


def resolve_unit(unit: str | None, *, expected_dimension: str | None = None) -> UnitDefinition:
    if unit is None or not str(unit).strip():
        raise AmountPrecisionError(
            "UNIT_MISSING",
            "unit is required and cannot be inferred",
            action="MANUAL_CONFIRMATION",
        )
    definition = UNIT_LOOKUP.get(str(unit).strip().lower())
    if definition is None:
        raise AmountPrecisionError(
            "UNIT_UNKNOWN",
            f"unit is not registered: {unit}",
            action="MANUAL_CONFIRMATION",
        )
    if expected_dimension is not None and definition.dimension != expected_dimension:
        raise AmountPrecisionError("UNIT_DIMENSION_MISMATCH", "unit dimension does not match calculation")
    return definition


def convert_unit(
    value: str | int | Decimal,
    *,
    from_unit: str | None,
    to_unit: str | None,
    expected_dimension: str | None = None,
) -> Decimal:
    """Convert between registered units without rounding or float arithmetic."""

    source = resolve_unit(from_unit, expected_dimension=expected_dimension)
    target = resolve_unit(to_unit, expected_dimension=expected_dimension)
    if source.dimension != target.dimension:
        raise AmountPrecisionError("UNIT_DIMENSION_MISMATCH", "cross-dimension conversion is forbidden")
    number = _as_decimal(value, "value")
    with localcontext() as context:
        context.prec = 80
        return number * source.scale_to_base / target.scale_to_base


def _round_decimal_cents(value_cents: Decimal, *, rule_id: str, point: str) -> int:
    rule = ROUNDING_RULES.get(rule_id)
    if rule is None:
        raise AmountPrecisionError(
            "ROUNDING_RULE_UNKNOWN",
            f"rounding rule is not registered: {rule_id}",
            action="MANUAL_CONFIRMATION",
        )
    if point != rule.point:
        raise AmountPrecisionError(
            "ROUNDING_POINT_MISMATCH",
            f"rule {rule_id} is registered only at {rule.point}",
        )
    quantum = Decimal(rule.quantum_cents)
    with localcontext() as context:
        context.prec = 80
        quotient = value_cents / quantum
        if rule.mode == "EXACT":
            rounded_quotient = quotient.to_integral_value()
            if quotient != rounded_quotient:
                raise AmountPrecisionError("FRACTIONAL_CENT", "source value is not exact at registered quantum")
        elif rule.mode == "ROUND_HALF_UP":
            rounded_quotient = quotient.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        elif rule.mode == "ROUND_HALF_EVEN":
            rounded_quotient = quotient.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        else:
            raise AmountPrecisionError("ROUNDING_MODE_UNKNOWN", "registered rounding mode is unsupported")
        rounded_cents = rounded_quotient * quantum
    if rounded_cents != rounded_cents.to_integral_value():
        raise AmountPrecisionError("NON_INTEGER_CENT_OUTPUT", "rounding rule did not produce integer cents")
    return int(rounded_cents)


@dataclass(frozen=True, order=True)
class Money:
    """Canonical CNY money stored and serialized as signed integer cents."""

    cents: int
    currency: str = "CNY"

    def __post_init__(self) -> None:
        if isinstance(self.cents, bool) or not isinstance(self.cents, int):
            raise AmountPrecisionError("INTEGER_CENTS_REQUIRED", "Money.cents must be an integer")
        if self.currency != "CNY":
            raise AmountPrecisionError("CURRENCY_UNSUPPORTED", "only CNY is registered")

    @classmethod
    def from_value(
        cls,
        value: str | int | Decimal,
        *,
        unit: str | None,
        rounding_rule_id: str | None = None,
        rounding_point: str | None = None,
    ) -> "Money":
        unit_definition = resolve_unit(unit, expected_dimension=MONEY_DIMENSION)
        number = _as_decimal(value, "amount")
        with localcontext() as context:
            context.prec = 80
            exact_cents = number * unit_definition.scale_to_base * Decimal(100)
        integral = exact_cents.to_integral_value()
        if exact_cents == integral and rounding_rule_id is None and rounding_point is None:
            return cls(int(integral))
        if rounding_rule_id is None or rounding_point is None:
            raise AmountPrecisionError(
                "EXPLICIT_ROUNDING_REQUIRED",
                "fractional-cent or rounded output requires both rule and registered point",
                action="MANUAL_CONFIRMATION",
            )
        return cls(_round_decimal_cents(exact_cents, rule_id=rounding_rule_id, point=rounding_point))

    def __add__(self, other: object) -> "Money":
        if not isinstance(other, Money) or other.currency != self.currency:
            return NotImplemented
        return Money(self.cents + other.cents, self.currency)

    def __sub__(self, other: object) -> "Money":
        if not isinstance(other, Money) or other.currency != self.currency:
            return NotImplemented
        return Money(self.cents - other.cents, self.currency)

    def to_public_dict(self) -> dict[str, Any]:
        return {"amount_cents": self.cents, "currency": self.currency}


@dataclass(frozen=True)
class PreciseMoneyCalculation:
    """Unrounded intermediate result that cannot masquerade as Money."""

    exact_cents: Decimal
    operation: str

    def __post_init__(self) -> None:
        if not isinstance(self.exact_cents, Decimal):
            raise AmountPrecisionError(
                "DECIMAL_INTERMEDIATE_REQUIRED",
                "PreciseMoneyCalculation.exact_cents must be Decimal",
            )
        if not self.exact_cents.is_finite():
            raise AmountPrecisionError("NON_FINITE_VALUE", "exact cents must be finite")
        if self.operation not in {"MULTIPLY", "DIVIDE"}:
            raise AmountPrecisionError("OPERATION_UNSUPPORTED", "precise operation is not registered")

    def finalize(self, *, rounding_rule_id: str, rounding_point: str) -> Money:
        return Money(
            _round_decimal_cents(
                self.exact_cents,
                rule_id=rounding_rule_id,
                point=rounding_point,
            )
        )


def multiply_money(money: Money, factor: str | int | Decimal) -> PreciseMoneyCalculation:
    decimal_factor = _as_decimal(factor, "factor")
    with localcontext() as context:
        context.prec = 80
        return PreciseMoneyCalculation(Decimal(money.cents) * decimal_factor, "MULTIPLY")


def divide_money(money: Money, divisor: str | int | Decimal) -> PreciseMoneyCalculation:
    decimal_divisor = _as_decimal(divisor, "divisor")
    if decimal_divisor == 0:
        raise AmountPrecisionError("DIVISION_BY_ZERO", "money divisor cannot be zero")
    with localcontext() as context:
        context.prec = 80
        return PreciseMoneyCalculation(Decimal(money.cents) / decimal_divisor, "DIVIDE")


def difference_cents(left: Money, right: Money) -> int:
    if left.currency != right.currency:
        raise AmountPrecisionError("CURRENCY_MISMATCH", "cannot compare different currencies")
    return left.cents - right.cents


def public_contract_summary() -> dict[str, Any]:
    money_units = [row for row in UNIT_DEFINITIONS if row.dimension == MONEY_DIMENSION]
    quantity_units = [row for row in UNIT_DEFINITIONS if row.dimension != MONEY_DIMENSION]
    return {
        "schema_version": "kmfa.v015.s05p1.amount_precision_contract.v1",
        "phase_id": RUN_PHASE_ID,
        "canonical_storage": "SIGNED_INTEGER_CENTS",
        "currency": "CNY",
        "float_money_allowed": False,
        "implicit_intermediate_rounding_allowed": False,
        "explicit_unit_required": True,
        "money_unit_count": len(money_units),
        "quantity_unit_count": len(quantity_units),
        "rounding_rule_count": len(ROUNDING_RULES),
        "rounding_points": sorted({rule.point for rule in ROUNDING_RULES.values()}),
        "unknown_unit_action": "MANUAL_CONFIRMATION",
        "unknown_rounding_rule_action": "MANUAL_CONFIRMATION",
        "raw_root_access_count": 0,
        "public_safe": True,
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
