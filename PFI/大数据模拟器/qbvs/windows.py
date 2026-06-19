from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from qbvs.backtest import normalize_ohlcv


@dataclass(frozen=True)
class WindowedFrame:
    label: str
    frame: pd.DataFrame


def rolling_windows(
    data: pd.DataFrame,
    lengths: Iterable[int] = (252, 504, 756, 1260),
    step: int = 63,
    min_bars: int = 120,
) -> list[WindowedFrame]:
    frame = normalize_ohlcv(data)
    output: list[WindowedFrame] = []
    for length in lengths:
        if length < min_bars:
            continue
        if len(frame) < min_bars:
            continue
        start_indexes = range(0, max(1, len(frame) - length + 1), max(1, step))
        for start in start_indexes:
            end = min(start + length, len(frame))
            if end - start < min_bars:
                continue
            window = frame.iloc[start:end].reset_index(drop=True)
            start_date = pd.Timestamp(window["datetime"].iloc[0]).date()
            end_date = pd.Timestamp(window["datetime"].iloc[-1]).date()
            label = f"rolling_{length}d_{start_date}_{end_date}"
            output.append(WindowedFrame(label=label, frame=window))
    return output


def load_event_windows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"event_id", "start", "end"}
    for row in rows:
        missing = required - set(row)
        if missing:
            raise ValueError(f"event window row missing fields: {missing}")
    return rows


def event_windows(data: pd.DataFrame, events: Iterable[dict[str, str]], min_bars: int = 30) -> list[WindowedFrame]:
    frame = normalize_ohlcv(data)
    output: list[WindowedFrame] = []
    for event in events:
        start = pd.Timestamp(event["start"])
        end = pd.Timestamp(event["end"])
        mask = (frame["datetime"] >= start) & (frame["datetime"] <= end)
        window = frame.loc[mask].reset_index(drop=True)
        if len(window) < min_bars:
            continue
        name = event.get("name", event["event_id"])
        label = f"event_{event['event_id']}_{name}_{start.date()}_{end.date()}"
        output.append(WindowedFrame(label=label, frame=window))
    return output
