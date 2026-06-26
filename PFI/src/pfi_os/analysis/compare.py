from __future__ import annotations

import pandas as pd

from pfi_os.backtest import BacktestResult


def compare_results(results: dict[str, BacktestResult]) -> pd.DataFrame:
    rows = []
    for name, result in results.items():
        row = {"name": name}
        row.update(result.metrics)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False, na_position="last")
