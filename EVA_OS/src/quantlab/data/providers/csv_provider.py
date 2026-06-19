from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantlab.data.cleaner import normalize_ohlcv
from quantlab.data.models import BarDataRequest
from quantlab.data.providers.base import DataProvider


class CSVProvider(DataProvider):
    name = "csv"

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        data = normalize_ohlcv(pd.read_csv(self.path), symbol=request.symbol, market=request.market)
        if request.start is not None:
            data = data[data["datetime"] >= pd.Timestamp(request.start)]
        if request.end is not None:
            data = data[data["datetime"] <= pd.Timestamp(request.end)]
        return data.reset_index(drop=True)

