from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json, locked_json_update, read_json_state


STRATEGY_PROFILE_DOC_DIR = PROJECT_ROOT / "docs" / "strategyProfiles"
STRATEGY_LIBRARY_DATA_DIR = PROJECT_ROOT / "data" / "strategyLibrary"
STRATEGY_PROFILE_OVERRIDE_PATH = STRATEGY_LIBRARY_DATA_DIR / "StrategyProfileOverrides.json"
STRATEGY_ORDER_PATH = STRATEGY_LIBRARY_DATA_DIR / "StrategyOrder.json"
BUILT_IN_STRATEGY_PARAMETER_PATH = STRATEGY_LIBRARY_DATA_DIR / "BuiltInStrategyParameters.json"
STRATEGY_PROFILE_EDITABLE_FIELDS = (
    "display_name",
    "display_name_en",
    "category",
    "category_en",
    "thesis",
    "thesis_en",
    "earnings",
    "earnings_en",
    "persistence",
    "persistence_en",
    "failure",
    "failure_en",
    "default_parameter_note",
    "default_parameter_note_en",
    "approval_note",
    "approval_note_en",
    "primary_sources",
)


@dataclass(frozen=True)
class ReturnSource:
    source: str
    source_en: str
    explanation: str
    explanation_en: str
    example: str
    example_en: str


@dataclass(frozen=True)
class StrategyProfile:
    strategy_id: str
    display_name: str
    display_name_en: str
    category: str
    category_en: str
    thesis: str
    thesis_en: str
    earnings: str
    earnings_en: str
    persistence: str
    persistence_en: str
    failure: str
    failure_en: str
    default_parameter_note: str
    default_parameter_note_en: str
    approval_note: str
    approval_note_en: str
    primary_sources: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyProfileCandidate:
    strategy_id: str
    display_name: str
    display_name_en: str
    version: str
    category: str
    thesis: str
    return_source: str
    failure: str
    parameter_notes: str
    approval_status: str
    quality_status: str
    quality_score: int
    missing_items: tuple[str, ...]
    path: str

    def to_row(self) -> dict[str, object]:
        return {
            "策略编号 Strategy Id": self.strategy_id,
            "名称 Name": self.display_name,
            "英文名称 English Name": self.display_name_en,
            "版本 Version": self.version,
            "类别 Category": self.category,
            "收益来源 Return Source": self.return_source,
            "质量状态 Quality Status": self.quality_status,
            "质量分数 Quality Score": self.quality_score,
            "缺失项 Missing Items": ", ".join(self.missing_items),
            "审批状态 Approval Status": self.approval_status,
            "路径 Path": self.path,
        }


RETURN_SOURCE_TAXONOMY = (
    ReturnSource(
        "风险溢价",
        "Risk Premium",
        "承担别人不愿承担的风险",
        "Taking risks that other participants are unwilling to take",
        "小盘、价值、波动率、期限结构",
        "Size, value, volatility, term structure",
    ),
    ReturnSource(
        "行为偏差",
        "Behavioral Bias",
        "利用市场参与者非理性",
        "Using irrational market participant behavior",
        "追涨杀跌、反应不足、过度反应",
        "Trend chasing, underreaction, overreaction",
    ),
    ReturnSource(
        "信息优势",
        "Information Advantage",
        "更快、更系统地处理信息",
        "Processing information faster or more systematically",
        "公告、财报、新闻、产业链数据",
        "Announcements, earnings, news, supply chain data",
    ),
    ReturnSource(
        "结构性约束",
        "Structural Constraint",
        "利用机构限制或市场制度",
        "Using institutional limits or market rules",
        "指数调仓、资金流、期货展期",
        "Index rebalancing, fund flows, futures roll",
    ),
    ReturnSource(
        "执行优势",
        "Execution Advantage",
        "更低成本、更优成交",
        "Lower cost or better execution",
        "拆单、限价、滑点控制",
        "Order splitting, limit orders, slippage control",
    ),
    ReturnSource(
        "组合优势",
        "Portfolio Advantage",
        "不靠单笔，而靠组合稳定性",
        "Relying on portfolio stability rather than one trade",
        "多因子、多资产、多策略分散",
        "Multi-factor, multi-asset, multi-strategy diversification",
    ),
)


STRATEGY_PROFILES = {
    "ma_crossover": StrategyProfile(
        strategy_id="ma_crossover",
        display_name="均线交叉",
        display_name_en="Moving Average Crossover",
        category="趋势跟随",
        category_en="Trend Following",
        thesis="短期均线高于长期均线时，价格趋势可能已经转强。",
        thesis_en="When the short moving average is above the long moving average, price trend may have strengthened.",
        earnings="主要尝试赚趋势延续和反应不足的钱，属于行为偏差与部分风险溢价。",
        earnings_en="It mainly attempts to earn from trend persistence and underreaction, linked to behavioral bias and some risk premium.",
        persistence="部分投资者反应慢、资金调仓有约束，价格趋势可能阶段性延续。",
        persistence_en="Some investors react slowly and capital rebalancing is constrained, so price trends may persist for periods.",
        failure="震荡市场、快速反转、低趋势强度和高交易成本环境下容易失效。",
        failure_en="It can fail in choppy markets, fast reversals, weak trend regimes, and high-cost environments.",
        default_parameter_note="核心参数是短均线和长均线，短均线必须小于长均线。",
        default_parameter_note_en="Core parameters are short and long moving averages; short window must be smaller than long window.",
        approval_note="内置策略已默认审批，但参数调整仍应经过报告复核。",
        approval_note_en="Built-in strategy is approved by default, but parameter changes should still be reviewed through reports.",
        primary_sources=("行为偏差", "风险溢价"),
    ),
    "breakout": StrategyProfile(
        strategy_id="breakout",
        display_name="突破策略",
        display_name_en="Breakout",
        category="趋势跟随",
        category_en="Trend Following",
        thesis="价格突破前期高点可能代表趋势确认，跌破退出区间则降低暴露。",
        thesis_en="A break above prior highs may confirm trend strength, while a break below the exit range reduces exposure.",
        earnings="主要尝试赚趋势启动后的延续收益，属于行为偏差与风险溢价。",
        earnings_en="It attempts to earn from continuation after trend initiation, linked to behavioral bias and risk premium.",
        persistence="止损、追涨资金和机构调仓可能让突破后的趋势继续扩散。",
        persistence_en="Stop losses, trend-following flows, and institutional rebalancing can extend post-breakout moves.",
        failure="假突破、区间震荡、流动性突然恶化和高滑点环境下容易失效。",
        failure_en="It can fail during false breakouts, range-bound markets, liquidity shocks, and high-slippage environments.",
        default_parameter_note="核心参数是突破观察窗口和退出窗口，退出窗口通常短于突破窗口。",
        default_parameter_note_en="Core parameters are breakout lookback and exit lookback; exit lookback is usually shorter.",
        approval_note="内置策略已默认审批，但突破类策略尤其需要检查滑点和交易成本。",
        approval_note_en="Built-in strategy is approved by default, but breakout strategies especially require slippage and cost review.",
        primary_sources=("行为偏差", "风险溢价"),
    ),
    "rsi_reversion": StrategyProfile(
        strategy_id="rsi_reversion",
        display_name="RSI 均值回归",
        display_name_en="RSI Mean Reversion",
        category="均值回归",
        category_en="Mean Reversion",
        thesis="短期超卖后价格可能因情绪修复或流动性恢复而反弹。",
        thesis_en="After short-term oversold conditions, price may rebound as sentiment or liquidity normalizes.",
        earnings="主要尝试赚短期过度反应后均值回归的钱，属于行为偏差。",
        earnings_en="It attempts to earn from mean reversion after short-term overreaction, linked to behavioral bias.",
        persistence="情绪化交易、止损拥挤和短期流动性冲击可能造成价格短期偏离。",
        persistence_en="Emotional trading, crowded stop-loss behavior, and short-term liquidity shocks can create temporary dislocations.",
        failure="单边趋势、基本面突变和流动性断裂环境下容易失效。",
        failure_en="It can fail in one-way trends, fundamental regime changes, and liquidity breaks.",
        default_parameter_note="核心参数是 RSI 窗口、入场阈值和退出阈值。",
        default_parameter_note_en="Core parameters are RSI window, entry threshold, and exit threshold.",
        approval_note="内置策略已默认审批，但均值回归策略必须重点检查单边下跌风险。",
        approval_note_en="Built-in strategy is approved by default, but mean-reversion strategies must focus on one-way downside risk.",
        primary_sources=("行为偏差",),
    ),
    "bollinger_reversion": StrategyProfile(
        strategy_id="bollinger_reversion",
        display_name="布林带均值回归",
        display_name_en="Bollinger Reversion",
        category="均值回归",
        category_en="Mean Reversion",
        thesis="价格跌破下轨可能代表短期超卖，回到中轨附近时风险收益开始下降。",
        thesis_en="A close below the lower band may indicate short-term oversold pressure, while return toward the middle band reduces the risk-reward edge.",
        earnings="主要尝试赚价格短期过度偏离后的均值回归收益，属于行为偏差。",
        earnings_en="It attempts to earn from mean reversion after short-term price dislocation, linked to behavioral bias.",
        persistence="短期恐慌卖出、止损拥挤和流动性冲击可能造成价格偏离合理波动区间。",
        persistence_en="Short-term panic selling, crowded stop-losses, and liquidity shocks can push prices outside normal volatility bands.",
        failure="趋势性下跌、波动率急剧扩张、基本面恶化和流动性断裂时容易失效。",
        failure_en="It can fail during persistent downtrends, volatility expansion, fundamental deterioration, and liquidity breaks.",
        default_parameter_note="核心参数是均线窗口、标准差倍数和退出 Z 值；窗口过短容易噪声化。",
        default_parameter_note_en="Core parameters are moving window, standard-deviation multiplier, and exit z-score; too short a window can amplify noise.",
        approval_note="内置策略已默认审批，但必须重点检查单边下跌和波动率扩张风险。",
        approval_note_en="Built-in strategy is approved by default, but one-way downside and volatility expansion risks must be reviewed.",
        primary_sources=("行为偏差",),
    ),
    "momentum_rotation": StrategyProfile(
        strategy_id="momentum_rotation",
        display_name="动量轮动",
        display_name_en="Momentum Rotation",
        category="组合轮动",
        category_en="Portfolio Rotation",
        thesis="相对强势资产可能在一段时间内继续强势，组合分散可降低单标的依赖。",
        thesis_en="Relatively strong assets may remain strong for a period, while diversification reduces single-symbol dependence.",
        earnings="主要尝试赚相对强势资产延续和组合分散的钱，属于行为偏差、风险溢价和组合优势。",
        earnings_en="It attempts to earn from relative strength persistence and diversification, linked to behavioral bias, risk premium, and portfolio advantage.",
        persistence="资金流、机构再平衡和投资者反应不足可能让强势资产继续强势一段时间。",
        persistence_en="Fund flows, institutional rebalancing, and investor underreaction can keep strong assets strong for some time.",
        failure="风格急剧反转、相关性同时上升和样本外资产关系变化时容易失效。",
        failure_en="It can fail during sharp factor reversals, rising correlations, and out-of-sample changes in asset relationships.",
        default_parameter_note="核心参数是动量回看窗口和持有资产数量。",
        default_parameter_note_en="Core parameters are momentum lookback window and number of selected assets.",
        approval_note="内置策略已默认审批，但组合轮动必须检查资产池、再平衡成本和相关性。",
        approval_note_en="Built-in strategy is approved by default, but portfolio rotation must review universe, rebalancing costs, and correlations.",
        primary_sources=("行为偏差", "风险溢价", "组合优势"),
    ),
    "alipay": StrategyProfile(
        strategy_id="alipay",
        display_name="追跌杀涨",
        display_name_en="Buy Dips Sell Rallies",
        category="行为交易",
        category_en="Behavioral Execution",
        thesis="收盘前价格相对上一交易日收盘下跌时，用固定公式分批补入；上涨且持仓收益达到阈值时按最高档分批卖出。",
        thesis_en="Near the pre-close decision point, the strategy adds on declines versus the previous close and scales out on profitable up days using the highest reached threshold.",
        earnings="主要尝试赚短期过度反应修复和纪律化执行的钱，属于行为偏差与执行优势；不是预测型策略，必须用真实数据、成本和回撤验证。",
        earnings_en="It mainly attempts to earn from short-term overreaction repair and disciplined execution, linked to behavioral bias and execution advantage; it is not a predictive strategy and must be validated with real data, costs, and drawdowns.",
        persistence="尾盘流动性、情绪交易、止损拥挤和散户追涨杀跌可能让短期价格偏离延续到可执行窗口，但这种规律不保证长期稳定。",
        persistence_en="Pre-close liquidity, emotional trading, crowded stop-loss behavior, and retail chasing can create short-term dislocations near the execution window, but persistence is not guaranteed.",
        failure="持续单边下跌、基本面恶化、隔夜跳空、流动性不足、手续费和滑点升高、资金不足或 T+1 限制导致无法按预期卖出时容易失效。",
        failure_en="It can fail during persistent downtrends, fundamental deterioration, overnight gaps, weak liquidity, higher fees and slippage, insufficient cash, or T+1 constraints that prevent expected exits.",
        default_parameter_note="默认补仓基准金额为 100000；买入金额为 floor(abs(当前价/上一交易日收盘价-1)*补仓基准金额)；持仓收益率约按 当前价/加权平均买入成本-1 计算；10% 卖 1/4，15% 卖 1/2，20% 全卖；A 股默认 14:30。",
        default_parameter_note_en="Default buy base amount is 100000; buy amount is floor(abs(current price / previous session close - 1) * buy base amount); position return is approximated as current price / weighted average buy cost - 1; sell 1/4 at 10%, 1/2 at 15%, and all at 20%; A-share signal time defaults to 14:30.",
        approval_note="内置策略已默认审批，但任何阈值、金额公式或持仓收益率口径修改都应重新确认；该策略只研究不实盘。",
        approval_note_en="Built-in strategy is approved by default, but any threshold, buy formula, or position-return definition change should be reconfirmed; this strategy is research-only.",
        primary_sources=("行为偏差", "执行优势"),
    ),
    "alipay_enhanced": StrategyProfile(
        strategy_id="alipay_enhanced",
        display_name="追跌杀涨增强",
        display_name_en="Buy Dips Sell Rallies Enhanced",
        category="行为交易 + 技术过滤",
        category_en="Behavioral Execution With Technical Filters",
        thesis="在原追跌杀涨下跌补入规则上，加入 RSI、布林带、均线和 MACD。下跌时仍低吸，超卖时提高买入金额；趋势转强时允许小额参与上涨；强趋势未超买时延迟卖出，减少上涨卖飞。",
        thesis_en="The enhanced version keeps buy-dips-sell-rallies dip buying and adds RSI, Bollinger Bands, moving averages, and MACD. It increases dip buys during oversold conditions, allows small trend participation when momentum strengthens, and delays selling during strong non-overbought trends to reduce premature exits.",
        earnings="收益来源包括短期过度反应修复、趋势延续中的反应不足，以及纪律化执行，属于行为偏差、风险溢价和执行优势的组合。",
        earnings_en="Return sources include short-term overreaction repair, underreaction during trend continuation, and disciplined execution, combining behavioral bias, risk premium, and execution advantage.",
        persistence="部分市场参与者在下跌时情绪化卖出、上涨趋势中反应不足；技术过滤尝试区分低吸机会和弱趋势陷阱，并在强趋势里提高持仓参与度。",
        persistence_en="Some participants sell emotionally during declines and underreact during uptrends. Technical filters attempt to separate dip-buying opportunities from weak-trend traps while increasing participation in strong trends.",
        failure="持续单边下跌、假突破、技术指标滞后、快速 V 型反转、成交流动性不足、成本升高、资金不足或 T+1 限制下仍可能失效。",
        failure_en="It can still fail during persistent downtrends, false breakouts, lagging indicators, fast V-shaped reversals, weak liquidity, higher costs, insufficient cash, or T+1 constraints.",
        default_parameter_note="核心参数包括补仓基准金额、卖出阈值、RSI 超卖/超买阈值、快慢均线、布林带、超卖买入倍数、弱趋势买入折扣、趋势参与买入倍数、最大仓位和强趋势延迟卖出缓冲。",
        default_parameter_note_en="Core parameters include buy base amount, sell thresholds, RSI oversold/overbought levels, fast/slow moving averages, Bollinger settings, oversold buy multiplier, weak-trend buy discount, trend participation multiplier, max position weight, and strong-trend sell-delay buffer.",
        approval_note="内置策略已默认审批用于研究；参数调整后仍应复核买入持有对比、成本压力、最大回撤和市场环境分层。",
        approval_note_en="Built-in strategy is approved for research; after parameter changes, review buy-and-hold comparison, cost stress, maximum drawdown, and market-regime breakdown.",
        primary_sources=("行为偏差", "风险溢价", "执行优势"),
    ),
}


DEFAULT_STRATEGY_PROFILE = StrategyProfile(
    strategy_id="unknown",
    display_name="未定义策略",
    display_name_en="Undefined Strategy",
    category="待定义",
    category_en="To Be Defined",
    thesis="当前策略研究假设未显式定义，需要在策略审批前补充。",
    thesis_en="The strategy thesis is not explicitly defined and should be completed before strategy approval.",
    earnings="当前策略收益来源未显式定义，需要在策略审批前补充研究假设。",
    earnings_en="The return source is not explicitly defined and should be completed before strategy approval.",
    persistence="当前长期存在理由未显式定义，需要用经济逻辑、行为逻辑或制度约束补充。",
    persistence_en="The persistence rationale is not explicitly defined and should be supported by economic logic, behavioral logic, or structural constraints.",
    failure="当前失效环境未显式定义，需要补充市场状态、波动、流动性和成本边界。",
    failure_en="The failure regime is not explicitly defined and should include market regime, volatility, liquidity, and cost boundaries.",
    default_parameter_note="参数规则未定义。",
    default_parameter_note_en="Parameter rules are not defined.",
    approval_note="未知策略必须先提交策略修改审批/确认。",
    approval_note_en="Unknown strategies must go through strategy change approval or confirmation first.",
    primary_sources=(),
)


DEFAULT_STRATEGY_ORDER = (
    "ma_crossover",
    "rsi_reversion",
    "bollinger_reversion",
    "breakout",
    "alipay",
    "alipay_enhanced",
    "momentum_rotation",
)

DEFAULT_BUILT_IN_STRATEGY_PARAMETERS: dict[str, dict[str, object]] = {
    "ma_crossover": {"short_window": 20, "long_window": 60},
    "rsi_reversion": {"window": 14, "entry": 30.0, "exit": 55.0},
    "bollinger_reversion": {"window": 20, "num_std": 2.0, "exit_z": 0.0},
    "breakout": {"lookback": 55, "exit_lookback": 20},
    "alipay": {
        "buy_base_amount": 100_000.0,
        "sell_25_return": 0.10,
        "sell_50_return": 0.15,
        "sell_100_return": 0.20,
        "signal_time": "14:30",
    },
    "alipay_enhanced": {
        "buy_base_amount": 100_000.0,
        "sell_25_return": 0.10,
        "sell_50_return": 0.15,
        "sell_100_return": 0.20,
        "signal_time": "14:30",
        "rsi_window": 14,
        "rsi_oversold": 35.0,
        "rsi_overbought": 72.0,
        "fast_ma_window": 20,
        "slow_ma_window": 60,
        "bollinger_window": 20,
        "bollinger_std": 2.0,
        "oversold_buy_multiplier": 1.5,
        "weak_trend_buy_multiplier": 0.6,
        "trend_buy_multiplier": 0.35,
        "max_position_weight": 0.95,
        "trend_hold_buffer": 0.05,
    },
    "momentum_rotation": {"lookback": 126, "top_n": 3},
}


def get_strategy_profile(strategy_id: str, override_path: Path | str = STRATEGY_PROFILE_OVERRIDE_PATH) -> StrategyProfile:
    profile = STRATEGY_PROFILES.get(strategy_id)
    if profile is None:
        return DEFAULT_STRATEGY_PROFILE
    override = load_strategy_profile_overrides(override_path).get(strategy_id, {})
    return apply_strategy_profile_override(profile, override)


def load_strategy_profile_overrides(path: Path | str = STRATEGY_PROFILE_OVERRIDE_PATH) -> dict[str, dict[str, object]]:
    override_path = Path(path)
    payload = read_json_state(override_path, {}, expected_type=dict)
    if not isinstance(payload, dict):
        return {}
    return {
        str(strategy_id): {str(key): value for key, value in values.items() if key in STRATEGY_PROFILE_EDITABLE_FIELDS}
        for strategy_id, values in payload.items()
        if isinstance(values, dict)
    }


def save_strategy_profile_override(strategy_id: str, payload: dict[str, object], path: Path | str = STRATEGY_PROFILE_OVERRIDE_PATH) -> Path:
    if strategy_id not in STRATEGY_PROFILES:
        raise ValueError(f"Unknown built-in strategy id: {strategy_id}")
    override_path = Path(path)
    clean_payload = _clean_strategy_profile_override_payload(payload)

    def update_overrides(current: dict[str, object]) -> dict[str, dict[str, object]]:
        overrides = {
            str(current_strategy_id): {str(key): value for key, value in values.items() if key in STRATEGY_PROFILE_EDITABLE_FIELDS}
            for current_strategy_id, values in current.items()
            if isinstance(values, dict)
        }
        overrides[strategy_id] = clean_payload
        return overrides

    return locked_json_update(override_path, {}, update_overrides, expected_type=dict, sort_keys=True)


def apply_strategy_profile_override(profile: StrategyProfile, payload: dict[str, object]) -> StrategyProfile:
    if not payload:
        return profile
    base = profile.to_dict()
    clean_payload = _clean_strategy_profile_override_payload(payload)
    base.update(clean_payload)
    base["strategy_id"] = profile.strategy_id
    base["primary_sources"] = tuple(str(item).strip() for item in base.get("primary_sources", ()) if str(item).strip())
    return StrategyProfile(**base)


def ordered_strategy_ids(order_path: Path | str = STRATEGY_ORDER_PATH) -> list[str]:
    saved_order = load_strategy_order(order_path)
    return _clean_strategy_order(saved_order)


def load_strategy_order(path: Path | str = STRATEGY_ORDER_PATH) -> list[str]:
    order_path = Path(path)
    payload = read_json_state(order_path, list(DEFAULT_STRATEGY_ORDER), expected_type=(dict, list))
    if isinstance(payload, dict):
        payload = payload.get("strategy_order", [])
    if not isinstance(payload, list):
        return list(DEFAULT_STRATEGY_ORDER)
    return [str(item).strip() for item in payload if str(item).strip()]


def save_strategy_order(order: list[str] | tuple[str, ...], path: Path | str = STRATEGY_ORDER_PATH) -> Path:
    order_path = Path(path)
    clean_order = _clean_strategy_order(order)
    return atomic_write_json(order_path, {"strategy_order": clean_order})


def move_strategy_order_item(strategy_id: str, direction: str, path: Path | str = STRATEGY_ORDER_PATH) -> Path:
    if direction not in {"up", "down"}:
        raise ValueError("direction must be 'up' or 'down'")
    order_path = Path(path)

    def update_order(payload: dict[str, object] | list[str]) -> dict[str, list[str]]:
        raw_order = payload.get("strategy_order", []) if isinstance(payload, dict) else payload
        order = _clean_strategy_order([str(item).strip() for item in raw_order if str(item).strip()] if isinstance(raw_order, list) else [])
        if strategy_id not in order:
            raise ValueError(f"Unknown built-in strategy id: {strategy_id}")
        index = order.index(strategy_id)
        if direction == "up" and index > 0:
            order[index - 1], order[index] = order[index], order[index - 1]
        elif direction == "down" and index < len(order) - 1:
            order[index + 1], order[index] = order[index], order[index + 1]
        return {"strategy_order": order}

    return locked_json_update(order_path, {"strategy_order": list(DEFAULT_STRATEGY_ORDER)}, update_order, expected_type=(dict, list))


def load_built_in_strategy_parameter_overrides(
    path: Path | str = BUILT_IN_STRATEGY_PARAMETER_PATH,
) -> dict[str, dict[str, object]]:
    parameter_path = Path(path)
    payload = read_json_state(parameter_path, {}, expected_type=dict)
    if not isinstance(payload, dict):
        return {}
    raw_overrides = payload.get("strategy_parameters", payload)
    if not isinstance(raw_overrides, dict):
        return {}
    overrides: dict[str, dict[str, object]] = {}
    for strategy_id, values in raw_overrides.items():
        normalized_id = str(strategy_id).strip()
        if normalized_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS or not isinstance(values, dict):
            continue
        allowed_keys = DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[normalized_id]
        overrides[normalized_id] = {
            str(key): value
            for key, value in values.items()
            if str(key) in allowed_keys
        }
    return overrides


def get_built_in_strategy_parameters(
    strategy_id: str,
    path: Path | str = BUILT_IN_STRATEGY_PARAMETER_PATH,
) -> dict[str, object]:
    if strategy_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS:
        raise ValueError(f"Unknown built-in strategy id: {strategy_id}")
    defaults = dict(DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[strategy_id])
    overrides = load_built_in_strategy_parameter_overrides(path).get(strategy_id, {})
    try:
        return clean_built_in_strategy_parameters(strategy_id, {**defaults, **overrides})
    except ValueError:
        return dict(DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[strategy_id])


def save_built_in_strategy_parameters(
    strategy_id: str,
    payload: dict[str, object],
    path: Path | str = BUILT_IN_STRATEGY_PARAMETER_PATH,
) -> Path:
    clean_payload = clean_built_in_strategy_parameters(strategy_id, payload)
    parameter_path = Path(path)

    def update_parameters(current: dict[str, object]) -> dict[str, dict[str, object]]:
        raw_overrides = current.get("strategy_parameters", current)
        overrides = _clean_builtin_parameter_overrides(raw_overrides if isinstance(raw_overrides, dict) else {})
        overrides[strategy_id] = clean_payload
        return {"strategy_parameters": overrides}

    return locked_json_update(parameter_path, {}, update_parameters, expected_type=dict, sort_keys=True)


def reset_built_in_strategy_parameters(
    strategy_id: str,
    path: Path | str = BUILT_IN_STRATEGY_PARAMETER_PATH,
) -> Path:
    if strategy_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS:
        raise ValueError(f"Unknown built-in strategy id: {strategy_id}")
    parameter_path = Path(path)

    def reset_parameters(current: dict[str, object]) -> dict[str, dict[str, object]]:
        raw_overrides = current.get("strategy_parameters", current)
        overrides = _clean_builtin_parameter_overrides(raw_overrides if isinstance(raw_overrides, dict) else {})
        overrides.pop(strategy_id, None)
        return {"strategy_parameters": overrides}

    return locked_json_update(parameter_path, {}, reset_parameters, expected_type=dict, sort_keys=True)


def _clean_builtin_parameter_overrides(raw_overrides: dict[str, object]) -> dict[str, dict[str, object]]:
    overrides: dict[str, dict[str, object]] = {}
    for strategy_id, values in raw_overrides.items():
        normalized_id = str(strategy_id).strip()
        if normalized_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS or not isinstance(values, dict):
            continue
        allowed_keys = DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[normalized_id]
        clean_values = {str(key): value for key, value in values.items() if str(key) in allowed_keys}
        if clean_values:
            overrides[normalized_id] = clean_values
    return overrides


def built_in_strategy_parameter_rows(
    strategy_id: str | None = None,
    path: Path | str = BUILT_IN_STRATEGY_PARAMETER_PATH,
) -> list[dict[str, object]]:
    strategy_ids = [strategy_id] if strategy_id else ordered_strategy_ids()
    rows: list[dict[str, object]] = []
    for current_strategy_id in strategy_ids:
        if current_strategy_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS:
            continue
        defaults = DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[current_strategy_id]
        current = get_built_in_strategy_parameters(current_strategy_id, path=path)
        for parameter_name, default_value in defaults.items():
            current_value = current.get(parameter_name, default_value)
            rows.append(
                {
                    "策略编号 Strategy Id": current_strategy_id,
                    "策略名称 Strategy Name": get_strategy_profile(current_strategy_id).display_name,
                    "参数 Parameter": parameter_name,
                    "系统默认值 System Default": default_value,
                    "当前默认值 Current Default": current_value,
                    "是否已修改 Modified": "是" if current_value != default_value else "否",
                }
            )
    return rows


def clean_built_in_strategy_parameters(strategy_id: str, payload: dict[str, object]) -> dict[str, object]:
    if strategy_id not in DEFAULT_BUILT_IN_STRATEGY_PARAMETERS:
        raise ValueError(f"Unknown built-in strategy id: {strategy_id}")
    defaults = DEFAULT_BUILT_IN_STRATEGY_PARAMETERS[strategy_id]
    values = {**defaults, **{key: value for key, value in payload.items() if key in defaults}}
    if strategy_id == "ma_crossover":
        clean = {
            "short_window": _int_param(values, "short_window"),
            "long_window": _int_param(values, "long_window"),
        }
        if clean["short_window"] < 2:
            raise ValueError("short_window must be at least 2")
        if clean["long_window"] <= clean["short_window"]:
            raise ValueError("long_window must be greater than short_window")
        return clean
    if strategy_id == "rsi_reversion":
        clean = {
            "window": _int_param(values, "window"),
            "entry": _float_param(values, "entry"),
            "exit": _float_param(values, "exit"),
        }
        if clean["window"] < 2:
            raise ValueError("window must be at least 2")
        if not (1.0 <= clean["entry"] < clean["exit"] <= 99.0):
            raise ValueError("RSI thresholds must satisfy 1 <= entry < exit <= 99")
        return clean
    if strategy_id == "bollinger_reversion":
        clean = {
            "window": _int_param(values, "window"),
            "num_std": _float_param(values, "num_std"),
            "exit_z": _float_param(values, "exit_z"),
        }
        if clean["window"] < 5:
            raise ValueError("window must be at least 5")
        if not (0.5 <= clean["num_std"] <= 5.0):
            raise ValueError("num_std must be between 0.5 and 5.0")
        if not (-2.0 <= clean["exit_z"] <= 2.0):
            raise ValueError("exit_z must be between -2.0 and 2.0")
        return clean
    if strategy_id == "breakout":
        clean = {
            "lookback": _int_param(values, "lookback"),
            "exit_lookback": _int_param(values, "exit_lookback"),
        }
        if clean["lookback"] < 5:
            raise ValueError("lookback must be at least 5")
        if clean["exit_lookback"] < 2:
            raise ValueError("exit_lookback must be at least 2")
        return clean
    if strategy_id == "alipay":
        clean = {
            "buy_base_amount": _float_param(values, "buy_base_amount"),
            "sell_25_return": _float_param(values, "sell_25_return"),
            "sell_50_return": _float_param(values, "sell_50_return"),
            "sell_100_return": _float_param(values, "sell_100_return"),
            "signal_time": _time_param(values, "signal_time"),
        }
        _validate_buy_dips_sell_thresholds(clean)
        return clean
    if strategy_id == "alipay_enhanced":
        clean = {
            "buy_base_amount": _float_param(values, "buy_base_amount"),
            "sell_25_return": _float_param(values, "sell_25_return"),
            "sell_50_return": _float_param(values, "sell_50_return"),
            "sell_100_return": _float_param(values, "sell_100_return"),
            "signal_time": _time_param(values, "signal_time"),
            "rsi_window": _int_param(values, "rsi_window"),
            "rsi_oversold": _float_param(values, "rsi_oversold"),
            "rsi_overbought": _float_param(values, "rsi_overbought"),
            "fast_ma_window": _int_param(values, "fast_ma_window"),
            "slow_ma_window": _int_param(values, "slow_ma_window"),
            "bollinger_window": _int_param(values, "bollinger_window"),
            "bollinger_std": _float_param(values, "bollinger_std"),
            "oversold_buy_multiplier": _float_param(values, "oversold_buy_multiplier"),
            "weak_trend_buy_multiplier": _float_param(values, "weak_trend_buy_multiplier"),
            "trend_buy_multiplier": _float_param(values, "trend_buy_multiplier"),
            "max_position_weight": _float_param(values, "max_position_weight"),
            "trend_hold_buffer": _float_param(values, "trend_hold_buffer"),
        }
        _validate_buy_dips_sell_thresholds(clean)
        if clean["rsi_window"] < 2:
            raise ValueError("rsi_window must be at least 2")
        if not (1.0 <= clean["rsi_oversold"] < clean["rsi_overbought"] <= 99.0):
            raise ValueError("RSI thresholds must satisfy 1 <= oversold < overbought <= 99")
        if clean["fast_ma_window"] < 2 or clean["slow_ma_window"] <= clean["fast_ma_window"]:
            raise ValueError("fast_ma_window must be at least 2 and smaller than slow_ma_window")
        if clean["bollinger_window"] < 5:
            raise ValueError("bollinger_window must be at least 5")
        if not (0.5 <= clean["bollinger_std"] <= 5.0):
            raise ValueError("bollinger_std must be between 0.5 and 5.0")
        if not (1.0 <= clean["oversold_buy_multiplier"] <= 3.0):
            raise ValueError("oversold_buy_multiplier must be between 1.0 and 3.0")
        if not (0.1 <= clean["weak_trend_buy_multiplier"] <= 1.0):
            raise ValueError("weak_trend_buy_multiplier must be between 0.1 and 1.0")
        if not (0.0 <= clean["trend_buy_multiplier"] <= 1.0):
            raise ValueError("trend_buy_multiplier must be between 0.0 and 1.0")
        if not (0.0 < clean["max_position_weight"] <= 1.0):
            raise ValueError("max_position_weight must be between 0 and 1")
        if not (0.0 <= clean["trend_hold_buffer"] <= 0.20):
            raise ValueError("trend_hold_buffer must be between 0 and 0.20")
        return clean
    clean = {
        "lookback": _int_param(values, "lookback"),
        "top_n": _int_param(values, "top_n"),
    }
    if clean["lookback"] < 5:
        raise ValueError("lookback must be at least 5")
    if clean["top_n"] < 1:
        raise ValueError("top_n must be at least 1")
    return clean


def _int_param(values: dict[str, object], key: str) -> int:
    return int(float(values[key]))


def _float_param(values: dict[str, object], key: str) -> float:
    return float(values[key])


def _time_param(values: dict[str, object], key: str) -> str:
    value = str(values[key]).strip()
    if not re_match_time(value):
        raise ValueError(f"{key} must use HH:MM format")
    return value


def re_match_time(value: str) -> bool:
    parts = value.split(":")
    if len(parts) != 2:
        return False
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _validate_buy_dips_sell_thresholds(clean: dict[str, object]) -> None:
    if float(clean["buy_base_amount"]) <= 0:
        raise ValueError("buy_base_amount must be positive")
    if not (0.0 < float(clean["sell_25_return"]) < float(clean["sell_50_return"]) < float(clean["sell_100_return"]) <= 1.0):
        raise ValueError("sell thresholds must satisfy 0 < 25% < 50% < 100% <= 1")


def _clean_strategy_order(order: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    clean_order: list[str] = []
    for strategy_id in order:
        normalized = str(strategy_id).strip()
        if normalized in STRATEGY_PROFILES and normalized not in seen:
            clean_order.append(normalized)
            seen.add(normalized)
    for strategy_id in DEFAULT_STRATEGY_ORDER:
        if strategy_id in STRATEGY_PROFILES and strategy_id not in seen:
            clean_order.append(strategy_id)
            seen.add(strategy_id)
    for strategy_id in STRATEGY_PROFILES:
        if strategy_id not in seen:
            clean_order.append(strategy_id)
            seen.add(strategy_id)
    return clean_order


def editable_strategy_profile_payload(profile: StrategyProfile) -> dict[str, object]:
    return {field: profile.to_dict()[field] for field in STRATEGY_PROFILE_EDITABLE_FIELDS}


def _clean_strategy_profile_override_payload(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for field in STRATEGY_PROFILE_EDITABLE_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field == "primary_sources":
            if isinstance(value, str):
                sources = [item.strip() for item in value.replace("，", ",").split(",")]
            else:
                sources = [str(item).strip() for item in value or []]
            clean[field] = tuple(source for source in sources if source)
        else:
            clean[field] = str(value or "").strip()
    return clean


def strategy_profile_rows(order_path: Path | str = STRATEGY_ORDER_PATH) -> list[dict[str, object]]:
    rows = []
    for index, strategy_id in enumerate(ordered_strategy_ids(order_path), start=1):
        profile = get_strategy_profile(strategy_id)
        rows.append(
            {
                "顺序 Order": index,
                "策略编号 Strategy Id": profile.strategy_id,
                "名称 Name": profile.display_name,
                "英文名称 English Name": profile.display_name_en,
                "类别 Category": profile.category,
                "收益来源 Return Sources": ", ".join(profile.primary_sources),
                "默认参数设置 Parameter Settings": profile.default_parameter_note,
            }
        )
    return rows


def collect_strategy_profile_candidates(profile_dir: Path | str = STRATEGY_PROFILE_DOC_DIR) -> list[StrategyProfileCandidate]:
    root = Path(profile_dir)
    if not root.exists():
        return []
    candidates = []
    for path in sorted(root.glob("*.md")):
        candidates.append(parse_strategy_profile_candidate(path))
    return candidates


def strategy_profile_candidate_rows(profile_dir: Path | str = STRATEGY_PROFILE_DOC_DIR) -> list[dict[str, object]]:
    return [candidate.to_row() for candidate in collect_strategy_profile_candidates(profile_dir)]


def parse_strategy_profile_candidate(path: Path | str) -> StrategyProfileCandidate:
    profile_path = Path(path)
    text = profile_path.read_text(encoding="utf-8")
    title = _first_heading(text)
    strategy_id = _inline_value(text, "策略编号") or _inline_value(text, "Strategy Id") or profile_path.stem
    version = _inline_value(text, "版本") or _inline_value(text, "Version") or ""
    category = _inline_value(text, "类别") or _inline_value(text, "Category") or ""
    display_name, display_name_en = _split_candidate_title(title, strategy_id)
    thesis = _section_value(text, "研究假设") or _section_value(text, "Research Thesis")
    return_source = _section_value(text, "收益来源") or _section_value(text, "Return Source")
    failure = _section_value(text, "失效环境") or _section_value(text, "Failure Regime")
    parameter_notes = (
        _section_value(text, "参数设置")
        or _section_value(text, "Parameter Settings")
        or _section_value(text, "参数说明")
        or _section_value(text, "Parameter Notes")
    )
    quality_status, quality_score, missing_items = evaluate_strategy_profile_candidate_quality(
        {
            "strategy_id": strategy_id,
            "display_name": display_name,
            "display_name_en": display_name_en,
            "version": version,
            "category": category,
            "thesis": thesis,
            "return_source": return_source,
            "failure": failure,
            "parameter_notes": parameter_notes,
        }
    )
    return StrategyProfileCandidate(
        strategy_id=strategy_id,
        display_name=display_name,
        display_name_en=display_name_en,
        version=version,
        category=category,
        thesis=thesis,
        return_source=return_source,
        failure=failure,
        parameter_notes=parameter_notes,
        approval_status=_extract_approval_status(text),
        quality_status=quality_status,
        quality_score=quality_score,
        missing_items=missing_items,
        path=str(profile_path),
    )


def evaluate_strategy_profile_candidate_quality(payload: dict[str, str]) -> tuple[str, int, tuple[str, ...]]:
    checks = [
        ("策略编号 Strategy Id", payload.get("strategy_id", "")),
        ("中文名称 Chinese Name", payload.get("display_name", "")),
        ("英文名称 English Name", payload.get("display_name_en", "")),
        ("版本 Version", payload.get("version", "")),
        ("类别 Category", payload.get("category", "")),
        ("研究假设 Research Thesis", payload.get("thesis", "")),
        ("收益来源 Return Source", payload.get("return_source", "")),
        ("失效环境 Failure Regime", payload.get("failure", "")),
        ("参数设置 Parameter Settings", payload.get("parameter_notes", "")),
    ]
    missing = tuple(label for label, value in checks if _is_missing_candidate_value(value))
    score = int(round((len(checks) - len(missing)) / len(checks) * 100))
    return ("ReadyForReview" if not missing else "Incomplete", score, missing)


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _inline_value(text: str, label: str) -> str:
    prefix = f"{label}："
    alt_prefix = f"{label}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return _clean_inline_value(stripped[len(prefix) :])
        if stripped.startswith(alt_prefix):
            return _clean_inline_value(stripped[len(alt_prefix) :])
    return ""


def _clean_inline_value(value: str) -> str:
    return value.strip().strip("`").strip()


def _section_value(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = index + 1
            break
    if start is None:
        return ""
    values = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            values.append(line.strip())
    return "\n".join(values).strip()


def _extract_approval_status(text: str) -> str:
    status = _section_value(text, "审批状态") or _section_value(text, "Approval Status")
    for candidate in ["Approved", "Pending", "Rejected", "Review"]:
        if candidate in status:
            return candidate
    return "Pending" if status else ""


def _is_missing_candidate_value(value: str) -> bool:
    normalized = " ".join(str(value or "").strip().split()).lower()
    if not normalized:
        return True
    placeholders = [
        "请补充",
        "describe parameter meaning",
        "to be defined",
        "待定义",
    ]
    return any(placeholder in normalized for placeholder in placeholders)


def _split_candidate_title(title: str, strategy_id: str) -> tuple[str, str]:
    if not title:
        return strategy_id, strategy_id.replace("_", " ").title()
    parts = title.split()
    first_english = next((index for index, part in enumerate(parts) if part[:1].isascii() and part[:1].isalpha()), len(parts))
    if first_english == 0:
        return title, title
    if first_english == len(parts):
        return title, ""
    return " ".join(parts[:first_english]), " ".join(parts[first_english:])
