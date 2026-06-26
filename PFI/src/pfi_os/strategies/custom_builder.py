from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.indicators import atr, rsi, sma
from pfi_os.storage import locked_json_update, read_json_state
from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


CUSTOM_STRATEGY_SPEC_DIR = DATA_DIR / "strategyLibrary"
CUSTOM_STRATEGY_SPEC_PATH = CUSTOM_STRATEGY_SPEC_DIR / "CustomStrategySpecs.json"
CUSTOM_STRATEGY_SPEC_HISTORY_PATH = CUSTOM_STRATEGY_SPEC_DIR / "CustomStrategySpecHistory.json"


@dataclass(frozen=True)
class CustomStrategySpec:
    strategy_id: str
    version: str
    display_name: str
    display_name_en: str
    logic_key: str
    indicator_keys: tuple[str, ...]
    settings: dict[str, dict[str, float]]
    category: str
    return_source: str
    return_source_en: str
    thesis: str
    thesis_en: str
    failure: str
    failure_en: str
    parameter_notes: str
    parameter_notes_en: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["indicator_keys"] = list(self.indicator_keys)
        return payload

    def to_row(self) -> dict[str, object]:
        return {
            "策略编号 Strategy Id": self.strategy_id,
            "名称 Name": self.display_name,
            "英文名称 English Name": self.display_name_en,
            "版本 Version": self.version,
            "逻辑 Logic": self.logic_key,
            "指标 Indicators": ", ".join(self.indicator_keys),
            "类别 Category": self.category,
            "收益来源 Return Sources": self.return_source,
        }


class CustomNoCodeStrategy(Strategy):
    description = "No-code custom strategy generated from PFIOS strategy settings."

    def __init__(self, spec: CustomStrategySpec | dict[str, Any], weight: float = 1.0):
        self.spec = custom_strategy_spec_from_payload(spec)
        if not 0.0 <= float(weight) <= 1.0:
            raise ValueError("weight must be between 0 and 1")
        self.strategy_id = self.spec.strategy_id
        self.version = self.spec.version
        self.description = f"No-code custom strategy: {self.spec.display_name_en}. Research only."
        self.weight = float(weight)
        super().__init__(
            logic_key=self.spec.logic_key,
            indicator_keys=list(self.spec.indicator_keys),
            settings=self.spec.settings,
            weight=self.weight,
        )

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        frame = data.copy().sort_values("datetime").reset_index(drop=True)
        _validate_market_frame(frame)
        close = pd.to_numeric(frame["close"], errors="coerce")
        high = pd.to_numeric(frame["high"], errors="coerce") if "high" in frame.columns else close
        low = pd.to_numeric(frame["low"], errors="coerce") if "low" in frame.columns else close
        volume = pd.to_numeric(frame["volume"], errors="coerce") if "volume" in frame.columns else pd.Series(1.0, index=frame.index)
        indicator_keys = set(self.spec.indicator_keys)
        primary_entries: list[pd.Series] = []
        exits: list[pd.Series] = []
        entry_filters: list[pd.Series] = []
        extra_columns: dict[str, pd.Series] = {}
        logic_key = self.spec.logic_key

        if "moving_average" in indicator_keys:
            values = self.spec.settings.get("moving_average", {})
            short_window = max(2, _int_setting(values, "short_window", 20))
            long_window = max(short_window + 1, _int_setting(values, "long_window", 60))
            short_ma = sma(close, short_window)
            long_ma = sma(close, long_window)
            extra_columns["short_ma"] = short_ma
            extra_columns["long_ma"] = long_ma
            if logic_key == "mean_reversion":
                primary_entries.append(close < short_ma)
                exits.append(close >= short_ma)
            else:
                primary_entries.append(short_ma > long_ma)
                exits.append(short_ma < long_ma)

        if "rsi" in indicator_keys:
            values = self.spec.settings.get("rsi", {})
            window = max(2, _int_setting(values, "window", 14))
            entry = _float_setting(values, "entry", 30.0)
            exit_ = _float_setting(values, "exit", 55.0)
            rsi_value = rsi(close, window)
            extra_columns["rsi"] = rsi_value
            if logic_key == "mean_reversion":
                primary_entries.append(rsi_value < entry)
                exits.append(rsi_value > exit_)
            else:
                primary_entries.append(rsi_value > max(50.0, exit_))
                exits.append(rsi_value < min(50.0, entry))

        if "bollinger" in indicator_keys:
            values = self.spec.settings.get("bollinger", {})
            window = max(5, _int_setting(values, "window", 20))
            std_multiplier = max(0.5, _float_setting(values, "std_multiplier", 2.0))
            exit_z = _float_setting(values, "exit_z", 0.0)
            middle = close.rolling(window, min_periods=window).mean()
            std = close.rolling(window, min_periods=window).std(ddof=0)
            z_score = (close - middle) / std.replace(0, pd.NA)
            upper = middle + std_multiplier * std
            lower = middle - std_multiplier * std
            extra_columns["middle_band"] = middle
            extra_columns["upper_band"] = upper
            extra_columns["lower_band"] = lower
            extra_columns["z_score"] = z_score
            if logic_key == "mean_reversion":
                primary_entries.append(z_score <= -std_multiplier)
                exits.append(z_score >= exit_z)
            else:
                primary_entries.append(close > upper)
                exits.append(close < middle)

        if "breakout_channel" in indicator_keys:
            values = self.spec.settings.get("breakout_channel", {})
            lookback = max(5, _int_setting(values, "lookback", 55))
            exit_lookback = max(2, _int_setting(values, "exit_lookback", 20))
            rolling_high = high.rolling(lookback, min_periods=lookback).max().shift(1)
            rolling_low = low.rolling(exit_lookback, min_periods=exit_lookback).min().shift(1)
            extra_columns["rolling_high"] = rolling_high
            extra_columns["rolling_low"] = rolling_low
            primary_entries.append(close > rolling_high)
            exits.append(close < rolling_low)

        if "momentum" in indicator_keys:
            values = self.spec.settings.get("momentum", {})
            lookback = max(5, _int_setting(values, "lookback", 60))
            minimum_return = _float_setting(values, "minimum_return", 0.02)
            momentum = close.pct_change(lookback)
            extra_columns["momentum"] = momentum
            primary_entries.append(momentum >= minimum_return)
            exits.append(momentum <= 0.0)

        if "volume_filter" in indicator_keys:
            values = self.spec.settings.get("volume_filter", {})
            window = max(2, _int_setting(values, "window", 20))
            minimum_ratio = max(0.0, _float_setting(values, "minimum_ratio", 1.2))
            volume_ratio = volume / volume.rolling(window, min_periods=window).mean().replace(0, pd.NA)
            extra_columns["volume_ratio"] = volume_ratio
            entry_filters.append(volume_ratio >= minimum_ratio)

        if "atr_risk" in indicator_keys:
            values = self.spec.settings.get("atr_risk", {})
            window = max(2, _int_setting(values, "window", 14))
            stop_multiplier = max(0.1, _float_setting(values, "stop_multiplier", 2.5))
            atr_value = atr(frame.assign(high=high, low=low, close=close), window)
            trailing_stop = close.rolling(window, min_periods=window).max() - stop_multiplier * atr_value
            extra_columns["atr"] = atr_value
            extra_columns["atr_trailing_stop"] = trailing_stop
            exits.append(close < trailing_stop)

        entry = _combine_entries(primary_entries, logic_key, frame.index)
        for entry_filter in entry_filters:
            entry = entry & entry_filter.fillna(False)
        exit_signal = _combine_exits(exits, frame.index)
        target = self._position_from_entry_exit(entry.fillna(False), exit_signal.fillna(False), frame.index)
        signals = finalize_signal_frame(frame, target * self.weight)
        for column, values in extra_columns.items():
            signals[column] = values
        return StrategyResult(signals=signals, metadata=self.metadata())

    def metadata(self) -> dict[str, Any]:
        metadata = super().metadata()
        metadata["custom_strategy_spec"] = self.spec.to_dict()
        return metadata

    @staticmethod
    def _position_from_entry_exit(entry: pd.Series, exit_signal: pd.Series, index: pd.Index) -> pd.Series:
        invested = False
        values: list[float] = []
        for enter, exit_ in zip(entry.reindex(index).fillna(False), exit_signal.reindex(index).fillna(False)):
            if bool(exit_):
                invested = False
            if bool(enter):
                invested = True
            values.append(1.0 if invested else 0.0)
        return pd.Series(values, index=index)


def custom_strategy_spec_from_payload(payload: CustomStrategySpec | dict[str, Any]) -> CustomStrategySpec:
    if isinstance(payload, CustomStrategySpec):
        return payload
    required = {
        "strategy_id",
        "version",
        "display_name",
        "display_name_en",
        "logic_key",
        "indicator_keys",
        "settings",
        "category",
        "return_source",
        "return_source_en",
        "thesis",
        "thesis_en",
        "failure",
        "failure_en",
        "parameter_notes",
        "parameter_notes_en",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Custom strategy spec missing fields: {', '.join(missing)}")
    return CustomStrategySpec(
        strategy_id=str(payload["strategy_id"]).strip(),
        version=str(payload["version"]).strip() or "0.1.0",
        display_name=str(payload["display_name"]).strip(),
        display_name_en=str(payload["display_name_en"]).strip(),
        logic_key=str(payload["logic_key"]).strip(),
        indicator_keys=tuple(str(item).strip() for item in payload.get("indicator_keys", ()) if str(item).strip()),
        settings=_clean_settings(payload.get("settings", {})),
        category=str(payload["category"]).strip(),
        return_source=str(payload["return_source"]).strip(),
        return_source_en=str(payload["return_source_en"]).strip(),
        thesis=str(payload["thesis"]).strip(),
        thesis_en=str(payload["thesis_en"]).strip(),
        failure=str(payload["failure"]).strip(),
        failure_en=str(payload["failure_en"]).strip(),
        parameter_notes=str(payload["parameter_notes"]).strip(),
        parameter_notes_en=str(payload["parameter_notes_en"]).strip(),
    )


def load_custom_strategy_specs(path: Path | str = CUSTOM_STRATEGY_SPEC_PATH) -> list[CustomStrategySpec]:
    spec_path = Path(path)
    payload = read_json_state(spec_path, {}, expected_type=dict)
    if not isinstance(payload, dict):
        return []
    specs = []
    for item in payload.values():
        if isinstance(item, dict):
            try:
                specs.append(custom_strategy_spec_from_payload(item))
            except ValueError:
                continue
    return sorted(specs, key=lambda spec: (spec.display_name_en, spec.strategy_id))


def get_custom_strategy_spec(
    strategy_id: str,
    path: Path | str = CUSTOM_STRATEGY_SPEC_PATH,
    default: dict[str, Any] | CustomStrategySpec | None = None,
) -> CustomStrategySpec:
    for spec in load_custom_strategy_specs(path):
        if spec.strategy_id == strategy_id:
            return spec
    if default is not None:
        return custom_strategy_spec_from_payload(default)
    raise KeyError(f"Custom strategy spec not found: {strategy_id}")


def save_custom_strategy_spec(spec: CustomStrategySpec | dict[str, Any], path: Path | str = CUSTOM_STRATEGY_SPEC_PATH) -> Path:
    clean_spec = custom_strategy_spec_from_payload(spec)
    spec_path = Path(path)

    def update_specs(payload: dict[str, Any]) -> dict[str, Any]:
        clean_payload = {str(key): value for key, value in payload.items() if isinstance(value, dict)}
        clean_payload[clean_spec.strategy_id] = clean_spec.to_dict()
        return clean_payload

    return locked_json_update(spec_path, {}, update_specs, expected_type=dict, sort_keys=True)


def save_custom_strategy_spec_revision(
    previous_spec: CustomStrategySpec,
    updated_spec: CustomStrategySpec | dict[str, Any],
    change_summary: str,
    risk_notes: str = "",
    path: Path | str = CUSTOM_STRATEGY_SPEC_PATH,
    history_path: Path | str = CUSTOM_STRATEGY_SPEC_HISTORY_PATH,
) -> tuple[Path, Path]:
    clean_updated = custom_strategy_spec_from_payload(updated_spec)
    spec_path = save_custom_strategy_spec(clean_updated, path=path)
    history_file = append_custom_strategy_spec_history(
        previous_spec=previous_spec,
        updated_spec=clean_updated,
        change_summary=change_summary,
        risk_notes=risk_notes,
        history_path=history_path,
    )
    return spec_path, history_file


def append_custom_strategy_spec_history(
    previous_spec: CustomStrategySpec,
    updated_spec: CustomStrategySpec,
    change_summary: str,
    risk_notes: str = "",
    history_path: Path | str = CUSTOM_STRATEGY_SPEC_HISTORY_PATH,
) -> Path:
    history_file = Path(history_path)
    record = {
        "strategy_id": updated_spec.strategy_id,
        "previous_version": previous_spec.version,
        "version": updated_spec.version,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "change_summary": str(change_summary or "").strip(),
        "risk_notes": str(risk_notes or "").strip(),
        "previous_spec": previous_spec.to_dict(),
        "updated_spec": updated_spec.to_dict(),
    }
    return locked_json_update(history_file, [], lambda current: [item for item in current if isinstance(item, dict)] + [record], expected_type=list, sort_keys=True)


def load_custom_strategy_spec_history(path: Path | str = CUSTOM_STRATEGY_SPEC_HISTORY_PATH) -> list[dict[str, Any]]:
    history_path = Path(path)
    payload = read_json_state(history_path, [], expected_type=list)
    return payload if isinstance(payload, list) else []


def custom_strategy_spec_history_rows(path: Path | str = CUSTOM_STRATEGY_SPEC_HISTORY_PATH) -> list[dict[str, object]]:
    rows = []
    for record in load_custom_strategy_spec_history(path):
        rows.append(
            {
                "策略编号 Strategy Id": record.get("strategy_id", ""),
                "原版本 Previous Version": record.get("previous_version", ""),
                "新版本 New Version": record.get("version", ""),
                "修改时间 Changed At": record.get("changed_at", ""),
                "修改说明 Change Summary": record.get("change_summary", ""),
                "风险说明 Risk Notes": record.get("risk_notes", ""),
            }
        )
    return rows


def next_strategy_version(version: str) -> str:
    parts = str(version or "0.1.0").strip().split(".")
    if len(parts) != 3:
        return "0.1.1"
    try:
        major, minor, patch = [int(part) for part in parts]
    except ValueError:
        return "0.1.1"
    return f"{major}.{minor}.{patch + 1}"


def custom_strategy_spec_rows(path: Path | str = CUSTOM_STRATEGY_SPEC_PATH) -> list[dict[str, object]]:
    return [spec.to_row() for spec in load_custom_strategy_specs(path)]


def _validate_market_frame(frame: pd.DataFrame) -> None:
    required = {"datetime", "symbol", "market", "close"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Custom strategy data missing columns: {', '.join(missing)}")


def _combine_entries(entries: list[pd.Series], logic_key: str, index: pd.Index) -> pd.Series:
    if not entries:
        return pd.Series(False, index=index)
    prepared = [entry.reindex(index).fillna(False).astype(bool) for entry in entries]
    if logic_key == "mean_reversion":
        combined = prepared[0]
        for entry in prepared[1:]:
            combined = combined | entry
        return combined
    combined = prepared[0]
    for entry in prepared[1:]:
        combined = combined & entry
    return combined


def _combine_exits(exits: list[pd.Series], index: pd.Index) -> pd.Series:
    if not exits:
        return pd.Series(False, index=index)
    combined = exits[0].reindex(index).fillna(False).astype(bool)
    for exit_signal in exits[1:]:
        combined = combined | exit_signal.reindex(index).fillna(False).astype(bool)
    return combined


def _clean_settings(settings: Any) -> dict[str, dict[str, float]]:
    if not isinstance(settings, dict):
        return {}
    clean: dict[str, dict[str, float]] = {}
    for group, values in settings.items():
        if not isinstance(values, dict):
            continue
        clean[str(group)] = {str(key): _float_setting(values, str(key), 0.0) for key in values}
    return clean


def _int_setting(values: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(float(values.get(key, default)))
    except (TypeError, ValueError):
        return default


def _float_setting(values: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default
