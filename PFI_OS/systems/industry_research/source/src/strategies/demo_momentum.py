from __future__ import annotations


def generate_signals(
    factors: list[dict[str, object]],
    min_return: float = 0.003,
    min_volume_ratio: float = 1.0,
) -> list[dict[str, object]]:
    signals: list[dict[str, object]] = []
    for item in factors:
        momentum = float(item.get("momentum_5d", 0))
        volume_ratio = float(item.get("volume_ratio_5d", 0))
        has_price = item.get("close") not in {"", None}
        tradable_research_asset = item.get("asset_class") not in {"FX", ""}
        internal_signal = "buy" if has_price and tradable_research_asset and momentum >= min_return and volume_ratio >= min_volume_ratio else "watch"
        if momentum < 0:
            internal_signal = "avoid"
        target_weight = _target_weight(internal_signal, momentum, volume_ratio)
        if item.get("validation_result") == "desktop_snapshot":
            reason = f"自选页快照涨跌 {momentum * 100:.3f}%，量能假设倍率 {volume_ratio:.3f}"
        else:
            reason = f"5日动量 {momentum * 100:.3f}%，成交量倍率 {volume_ratio:.3f}"
        signals.append(
            {
                "date": item["date"],
                "symbol": item["symbol"],
                "name": item["name"],
                "industry": item["industry"],
                "asset_class": item.get("asset_class", ""),
                "research_group": item.get("research_group", item["industry"]),
                "signal": _signal_label(internal_signal),
                "internal_signal": internal_signal,
                "reason": reason,
                "target_weight": target_weight,
            }
        )
    return signals


def _target_weight(internal_signal: str, momentum: float, volume_ratio: float) -> float:
    if internal_signal != "buy":
        return 0.0
    base = 0.03
    if momentum >= 0.01:
        base += 0.015
    if momentum >= 0.025:
        base += 0.015
    if momentum >= 0.05:
        base -= 0.01
    if volume_ratio >= 1.2:
        base += 0.01
    return round(max(0.02, min(base, 0.07)), 6)


def _signal_label(internal_signal: str) -> str:
    return {
        "buy": "承接观察",
        "watch": "观察",
        "avoid": "风险观察",
    }.get(internal_signal, "观察")
