from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import ROOT, read_simple_yaml


class LLMRouter:
    """Single entrypoint for all LLM calls."""

    def __init__(self, provider: str = "stub", model: str = "deterministic-research-writer"):
        self.provider = provider
        self.model = model

    @classmethod
    def from_config(cls, path: str | Path | None = None) -> "LLMRouter":
        config = read_simple_yaml(path or ROOT / "config" / "llm.yaml")
        return cls(provider=str(config.get("provider", "stub")), model=str(config.get("model", "stub")))

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        if self.provider == "stub":
            return self._stub_generate(prompt, context)
        raise NotImplementedError(
            f"Provider {self.provider!r} is not implemented. Add it here, not in business modules."
        )

    def _stub_generate(self, prompt: str, context: dict[str, Any]) -> str:
        signals = context.get("signals", [])
        advice = context.get("advice", [])
        buy_signals = [item for item in signals if item.get("internal_signal") == "buy"]
        risk_logs = context.get("risk_logs", [])
        top_factors = sorted(
            context.get("factors", []),
            key=lambda item: float(item.get("momentum_5d", 0)),
            reverse=True,
        )[:3]
        conclusion = "当前高可信研究条件不足，仅跟踪成交额和强弱排序最靠前的标的。"
        actionable = [item for item in advice if float(item.get("suggested_weight") or 0) > 0]
        if actionable:
            names = "、".join(
                f"{item['name']}（{item['action']}，Volume {float(item['suggested_weight']) * 100:.3f}%）"
                for item in actionable
            )
            conclusion = (
                f"仓位操作建议：{names}。执行前按报告表格检查新闻/公告来源、反方触发条件和 PFIOS 风险闸门；"
                "若任一触发条件不满足，则取消、暂停或观望，并在账户确认后重算Volume。"
            )
        elif buy_signals:
            names = "、".join(str(item["name"]) for item in buy_signals)
            conclusion = f"观望清单：可关注 {names}，但当前未形成明确买卖幅度。"
        factor_text = "；".join(
            f"{item['name']} 涨跌线索 {float(item.get('momentum_5d', 0)) * 100:.3f}%"
            for item in top_factors
        )
        return (
            f"观点：{conclusion}\n"
            f"推论：动量排序显示 {factor_text}。\n"
            f"事实：风控检查结果为 {'；'.join(risk_logs)}"
        )
