from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.config import ROOT, read_simple_yaml


def load_risk_rules(path: str | Path | None = None) -> dict[str, object]:
    return read_simple_yaml(path or ROOT / "config" / "risk_rules.yaml")


def evaluate_risk(
    proposed_positions: list[dict[str, object]],
    rules: dict[str, object] | None = None,
) -> tuple[list[dict[str, object]], list[str]]:
    rules = rules or load_risk_rules()
    adjusted = []
    logs: list[str] = []
    industry_weights: dict[str, float] = defaultdict(float)
    blacklist = set(rules.get("blacklist_symbols", []))
    max_asset = float(rules.get("max_single_asset_weight", 1))

    for position in proposed_positions:
        symbol = str(position["symbol"])
        weight = float(position.get("target_weight", 0))
        if symbol in blacklist:
            logs.append(f"{symbol} 在黑名单内，目标仓位降为 0。")
            weight = 0.0
        if weight > max_asset:
            logs.append(f"{symbol} 超过单标的上限 {max_asset:.0%}，已裁剪。")
            weight = max_asset
        updated = dict(position)
        updated["risk_adjusted_weight"] = round(weight, 6)
        industry_weights[str(position["industry"])] += weight
        adjusted.append(updated)

    max_industry = float(rules.get("max_single_industry_weight", 1))
    for industry, weight in industry_weights.items():
        if weight > max_industry:
            logs.append(f"{industry} 行业权重 {weight:.2%} 超过上限 {max_industry:.0%}，需要组合层二次优化。")
    if not logs:
        logs.append("未触发硬性风控约束。")
    return adjusted, logs
