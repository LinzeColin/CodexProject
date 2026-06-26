from __future__ import annotations

import math

import pandas as pd

from pfi_os.indicators import bollinger_bands, macd, rsi, sma
from pfi_os.strategies.base import Strategy, StrategyResult


class AlipayStrategy(Strategy):
    strategy_id = "alipay"
    description = "Buy integer CNY amounts on same-day drawdowns and scale out on profitable up days."

    def __init__(
        self,
        buy_base_amount: float = 100_000.0,
        initial_cash: float = 100_000.0,
        sell_25_return: float = 0.10,
        sell_50_return: float = 0.15,
        sell_100_return: float = 0.20,
        signal_time: str = "14:30",
    ):
        if buy_base_amount <= 0:
            raise ValueError("buy_base_amount must be positive")
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not (0 < sell_25_return < sell_50_return < sell_100_return):
            raise ValueError("sell thresholds must satisfy 0 < 25% < 50% < 100% thresholds")
        super().__init__(
            buy_base_amount=buy_base_amount,
            initial_cash=initial_cash,
            sell_25_return=sell_25_return,
            sell_50_return=sell_50_return,
            sell_100_return=sell_100_return,
            signal_time=signal_time,
            same_day_buy_sell=False,
        )
        self.buy_base_amount = float(buy_base_amount)
        self.initial_cash = float(initial_cash)
        self.sell_25_return = float(sell_25_return)
        self.sell_50_return = float(sell_50_return)
        self.sell_100_return = float(sell_100_return)
        self.signal_time = signal_time

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        frame = data.copy().sort_values("datetime").reset_index(drop=True)
        frame["datetime"] = pd.to_datetime(frame["datetime"])
        close = frame["close"].astype(float)
        session_dates = frame["datetime"].dt.date
        previous_close_by_session = close.groupby(session_dates).last().shift(1)
        previous_close = session_dates.map(previous_close_by_session).astype(float)
        daily_return = (close / previous_close - 1.0).replace([float("inf"), -float("inf")], 0.0).fillna(0.0)
        eligible = self._eligible_signal_rows(frame["datetime"], session_dates)

        cash = self.initial_cash
        quantity = 0.0
        avg_cost = 0.0
        target_weights = []
        order_values = []
        sell_fractions = []
        actions = []
        reasons = []
        position_returns = []

        for price, day_return, is_eligible in zip(close, daily_return, eligible):
            position_return = (price / avg_cost - 1.0) if quantity > 0 and avg_cost > 0 else 0.0
            order_value = 0.0
            sell_fraction = 0.0
            action = "HOLD"
            reason = "Not the 14:30 decision row." if not is_eligible else "No rule triggered."

            if not is_eligible:
                pass
            elif day_return > 0 and quantity > 0:
                sell_fraction = self._sell_fraction(position_return)
                if sell_fraction > 0:
                    action = "SELL"
                    reason = f"Up day and position return reached {position_return:.2%}; sell {sell_fraction:.0%}."
                    sell_qty = quantity * sell_fraction
                    cash += sell_qty * price
                    quantity -= sell_qty
                    if quantity <= 1e-8:
                        quantity = 0.0
                        avg_cost = 0.0
            elif day_return < 0:
                order_value = math.floor(abs(float(day_return)) * self.buy_base_amount)
                if order_value >= 1 and cash >= order_value:
                    action = "BUY"
                    reason = f"Down day {day_return:.2%}; buy integer amount {order_value:.0f}."
                    buy_qty = order_value / price
                    previous_value = quantity * avg_cost
                    quantity += buy_qty
                    avg_cost = (previous_value + order_value) / quantity if quantity else 0.0
                    cash -= order_value
                elif order_value >= 1:
                    reason = f"Down day {day_return:.2%}, but cash is insufficient for {order_value:.0f}."
                    order_value = 0.0

            equity_proxy = cash + quantity * price
            target_weight = quantity * price / equity_proxy if equity_proxy else 0.0
            target_weights.append(target_weight)
            order_values.append(float(order_value))
            sell_fractions.append(float(sell_fraction))
            actions.append(action)
            reasons.append(reason)
            position_returns.append(float(position_return))

        signals = frame[["datetime", "symbol", "market", "close"]].copy()
        signals["target_weight"] = pd.Series(target_weights, index=signals.index).fillna(0.0).clip(0.0, 1.0)
        signals["signal"] = signals["target_weight"].diff().fillna(signals["target_weight"])
        signals["order_value"] = order_values
        signals["sell_fraction"] = sell_fractions
        signals["action"] = actions
        signals["daily_return"] = daily_return
        signals["position_return"] = position_returns
        signals["signal_time"] = self.signal_time
        signals["reason"] = reasons
        metadata = self.metadata()
        metadata["execution_assumption"] = (
            "Uses the first available bar at or after 14:30 for intraday data; uses daily close as a proxy when intraday bars are unavailable."
        )
        metadata["position_return_assumption"] = "Position return is approximated as current close divided by weighted average buy cost minus one."
        metadata["daily_return_assumption"] = "Daily return is current price divided by the previous trading session close minus one."
        return StrategyResult(signals=signals, metadata=metadata)

    def _sell_fraction(self, position_return: float) -> float:
        if position_return >= self.sell_100_return:
            return 1.0
        if position_return >= self.sell_50_return:
            return 0.5
        if position_return >= self.sell_25_return:
            return 0.25
        return 0.0

    def _eligible_signal_rows(self, datetimes: pd.Series, session_dates: pd.Series) -> pd.Series:
        times = datetimes.dt.strftime("%H:%M")
        has_intraday_time = datetimes.dt.time.astype(str).ne("00:00:00").any()
        if not has_intraday_time:
            return pd.Series(True, index=datetimes.index)
        after_signal_time = times >= self.signal_time
        eligible = pd.Series(False, index=datetimes.index)
        for session_date, group_index in session_dates.groupby(session_dates).groups.items():
            del session_date
            session_after_time = [index for index in group_index if bool(after_signal_time.loc[index])]
            if session_after_time:
                eligible.loc[session_after_time[0]] = True
        return eligible


class AlipayEnhancedStrategy(Strategy):
    strategy_id = "alipay_enhanced"
    description = "Buy-dips-sell-rallies strategy with technical filters, trend participation, and delayed selling in strong uptrends."

    def __init__(
        self,
        buy_base_amount: float = 100_000.0,
        initial_cash: float = 100_000.0,
        sell_25_return: float = 0.10,
        sell_50_return: float = 0.15,
        sell_100_return: float = 0.20,
        signal_time: str = "14:30",
        rsi_window: int = 14,
        rsi_oversold: float = 35.0,
        rsi_overbought: float = 72.0,
        fast_ma_window: int = 20,
        slow_ma_window: int = 60,
        bollinger_window: int = 20,
        bollinger_std: float = 2.0,
        oversold_buy_multiplier: float = 1.5,
        weak_trend_buy_multiplier: float = 0.6,
        trend_buy_multiplier: float = 0.35,
        max_position_weight: float = 0.95,
        trend_hold_buffer: float = 0.05,
    ):
        if buy_base_amount <= 0:
            raise ValueError("buy_base_amount must be positive")
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not (0 < sell_25_return < sell_50_return < sell_100_return):
            raise ValueError("sell thresholds must satisfy 0 < 25% < 50% < 100% thresholds")
        if fast_ma_window >= slow_ma_window:
            raise ValueError("fast_ma_window must be smaller than slow_ma_window")
        if not (0 < max_position_weight <= 1):
            raise ValueError("max_position_weight must be between 0 and 1")
        super().__init__(
            buy_base_amount=buy_base_amount,
            initial_cash=initial_cash,
            sell_25_return=sell_25_return,
            sell_50_return=sell_50_return,
            sell_100_return=sell_100_return,
            signal_time=signal_time,
            rsi_window=rsi_window,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            fast_ma_window=fast_ma_window,
            slow_ma_window=slow_ma_window,
            bollinger_window=bollinger_window,
            bollinger_std=bollinger_std,
            oversold_buy_multiplier=oversold_buy_multiplier,
            weak_trend_buy_multiplier=weak_trend_buy_multiplier,
            trend_buy_multiplier=trend_buy_multiplier,
            max_position_weight=max_position_weight,
            trend_hold_buffer=trend_hold_buffer,
            same_day_buy_sell=False,
        )
        self.buy_base_amount = float(buy_base_amount)
        self.initial_cash = float(initial_cash)
        self.sell_25_return = float(sell_25_return)
        self.sell_50_return = float(sell_50_return)
        self.sell_100_return = float(sell_100_return)
        self.signal_time = signal_time
        self.rsi_window = int(rsi_window)
        self.rsi_oversold = float(rsi_oversold)
        self.rsi_overbought = float(rsi_overbought)
        self.fast_ma_window = int(fast_ma_window)
        self.slow_ma_window = int(slow_ma_window)
        self.bollinger_window = int(bollinger_window)
        self.bollinger_std = float(bollinger_std)
        self.oversold_buy_multiplier = float(oversold_buy_multiplier)
        self.weak_trend_buy_multiplier = float(weak_trend_buy_multiplier)
        self.trend_buy_multiplier = float(trend_buy_multiplier)
        self.max_position_weight = float(max_position_weight)
        self.trend_hold_buffer = float(trend_hold_buffer)

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        frame = data.copy().sort_values("datetime").reset_index(drop=True)
        frame["datetime"] = pd.to_datetime(frame["datetime"])
        close = frame["close"].astype(float)
        session_dates = frame["datetime"].dt.date
        previous_close_by_session = close.groupby(session_dates).last().shift(1)
        previous_close = session_dates.map(previous_close_by_session).astype(float)
        daily_return = (close / previous_close - 1.0).replace([float("inf"), -float("inf")], 0.0).fillna(0.0)
        eligible = AlipayStrategy(signal_time=self.signal_time)._eligible_signal_rows(frame["datetime"], session_dates)

        indicators = self._indicator_frame(frame)
        cash = self.initial_cash
        quantity = 0.0
        avg_cost = 0.0
        target_weights = []
        order_values = []
        sell_fractions = []
        actions = []
        reasons = []
        position_returns = []

        for index, price in enumerate(close):
            price = float(price)
            day_return = float(daily_return.iloc[index])
            row = indicators.iloc[index]
            strong_trend = bool(row["strong_trend"])
            weak_trend = bool(row["weak_trend"])
            oversold = bool(row["oversold"])
            overbought = bool(row["overbought"])
            position_return = (price / avg_cost - 1.0) if quantity > 0 and avg_cost > 0 else 0.0
            equity_proxy = cash + quantity * price
            current_position_value = quantity * price
            max_position_value = equity_proxy * self.max_position_weight
            buy_capacity = max(0.0, min(cash, max_position_value - current_position_value))
            order_value = 0.0
            sell_fraction = 0.0
            action = "HOLD"
            reason = "Not the 14:30 decision row." if not bool(eligible.iloc[index]) else "No rule triggered."

            if not bool(eligible.iloc[index]):
                pass
            elif day_return > 0:
                if quantity > 0:
                    sell_fraction = self._sell_fraction(position_return, strong_trend=strong_trend, overbought=overbought, weak_trend=weak_trend)
                    if sell_fraction > 0:
                        action = "SELL"
                        reason = (
                            f"Up day, position return {position_return:.2%}; "
                            f"trend strong={strong_trend}, overbought={overbought}; sell {sell_fraction:.0%}."
                        )
                        sell_qty = quantity * sell_fraction
                        cash += sell_qty * price
                        quantity -= sell_qty
                        if quantity <= 1e-8:
                            quantity = 0.0
                            avg_cost = 0.0
                if action == "HOLD" and strong_trend and not overbought and buy_capacity >= 1:
                    order_value = self._trend_buy_amount(day_return, buy_capacity)
                    if order_value >= 1:
                        action = "BUY"
                        reason = f"Strong trend participation; buy integer amount {order_value:.0f}."
                        quantity, avg_cost, cash = self._apply_buy(quantity, avg_cost, cash, order_value, price)
            elif day_return < 0:
                order_value = self._dip_buy_amount(day_return, oversold=oversold, weak_trend=weak_trend, buy_capacity=buy_capacity)
                if order_value >= 1:
                    action = "BUY"
                    reason = (
                        f"Down day {day_return:.2%}; oversold={oversold}, weak trend={weak_trend}; "
                        f"buy integer amount {order_value:.0f}."
                    )
                    quantity, avg_cost, cash = self._apply_buy(quantity, avg_cost, cash, order_value, price)
                elif abs(day_return) > 0:
                    reason = f"Down day {day_return:.2%}, but position cap or cash prevents buying."

            equity_proxy = cash + quantity * price
            target_weight = quantity * price / equity_proxy if equity_proxy else 0.0
            target_weights.append(target_weight)
            order_values.append(float(order_value))
            sell_fractions.append(float(sell_fraction))
            actions.append(action)
            reasons.append(reason)
            position_returns.append(float(position_return))

        signals = frame[["datetime", "symbol", "market", "close"]].copy()
        signals["target_weight"] = pd.Series(target_weights, index=signals.index).fillna(0.0).clip(0.0, 1.0)
        signals["signal"] = signals["target_weight"].diff().fillna(signals["target_weight"])
        signals["order_value"] = order_values
        signals["sell_fraction"] = sell_fractions
        signals["action"] = actions
        signals["daily_return"] = daily_return
        signals["position_return"] = position_returns
        signals["rsi"] = indicators["rsi"]
        signals["fast_ma"] = indicators["fast_ma"]
        signals["slow_ma"] = indicators["slow_ma"]
        signals["macd_hist"] = indicators["macd_hist"]
        signals["strong_trend"] = indicators["strong_trend"]
        signals["oversold"] = indicators["oversold"]
        signals["overbought"] = indicators["overbought"]
        signals["signal_time"] = self.signal_time
        signals["reason"] = reasons
        metadata = self.metadata()
        metadata["execution_assumption"] = (
            "Research-only A-share 14:30 proxy. The enhanced version combines dip buying, RSI/Bollinger oversold filters, "
            "MA/MACD trend participation, position cap, and delayed selling in strong trends."
        )
        metadata["position_return_assumption"] = "Position return is approximated as current close divided by weighted average buy cost minus one."
        metadata["daily_return_assumption"] = "Daily return is current price divided by the previous trading session close minus one."
        return StrategyResult(signals=signals, metadata=metadata)

    def _indicator_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        close = frame["close"].astype(float)
        fast_ma = sma(close, self.fast_ma_window)
        slow_ma = sma(close, self.slow_ma_window)
        rsi_value = rsi(close, self.rsi_window).fillna(50.0)
        macd_frame = macd(close)
        bands = bollinger_bands(close, self.bollinger_window, self.bollinger_std)
        strong_trend = (close > slow_ma) & (fast_ma > slow_ma) & (macd_frame["macd_hist"] > 0)
        weak_trend = (close < slow_ma) & (fast_ma < slow_ma)
        oversold = (rsi_value <= self.rsi_oversold) | (close <= bands["bb_lower"])
        overbought = rsi_value >= self.rsi_overbought
        return pd.DataFrame(
            {
                "rsi": rsi_value,
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "macd_hist": macd_frame["macd_hist"].fillna(0.0),
                "strong_trend": strong_trend.fillna(False),
                "weak_trend": weak_trend.fillna(False),
                "oversold": oversold.fillna(False),
                "overbought": overbought.fillna(False),
            }
        )

    def _dip_buy_amount(self, day_return: float, oversold: bool, weak_trend: bool, buy_capacity: float) -> float:
        multiplier = 1.0
        if oversold:
            multiplier *= self.oversold_buy_multiplier
        if weak_trend:
            multiplier *= self.weak_trend_buy_multiplier
        raw = math.floor(abs(float(day_return)) * self.buy_base_amount * multiplier)
        return float(max(0, math.floor(min(raw, buy_capacity))))

    def _trend_buy_amount(self, day_return: float, buy_capacity: float) -> float:
        raw = math.floor(max(float(day_return), 0.001) * self.buy_base_amount * self.trend_buy_multiplier)
        return float(max(0, math.floor(min(raw, buy_capacity))))

    def _sell_fraction(self, position_return: float, *, strong_trend: bool, overbought: bool, weak_trend: bool) -> float:
        if strong_trend and not overbought and not weak_trend:
            if position_return >= self.sell_100_return + self.trend_hold_buffer:
                return 0.5
            if position_return >= self.sell_50_return + self.trend_hold_buffer:
                return 0.25
            return 0.0
        if position_return >= self.sell_100_return:
            return 1.0
        if position_return >= self.sell_50_return:
            return 0.5
        if position_return >= self.sell_25_return:
            return 0.25
        return 0.0

    @staticmethod
    def _apply_buy(quantity: float, avg_cost: float, cash: float, order_value: float, price: float) -> tuple[float, float, float]:
        buy_qty = order_value / price
        previous_value = quantity * avg_cost
        quantity += buy_qty
        avg_cost = (previous_value + order_value) / quantity if quantity else 0.0
        cash -= order_value
        return quantity, avg_cost, cash
