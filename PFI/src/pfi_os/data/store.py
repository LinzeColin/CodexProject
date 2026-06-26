from __future__ import annotations

from pathlib import Path

import pandas as pd

from pfi_os.config import CACHE_DATA_DIR
from pfi_os.data.cleaner import normalize_ohlcv


class DataStore:
    """Local research store.

    Parquet is used when pyarrow is installed; CSV remains as a no-surprise fallback.
    """

    def __init__(self, root: Path | str = CACHE_DATA_DIR, format: str = "parquet"):
        self.root = Path(root)
        self.format = format
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, symbol: str, market: str, interval: str) -> Path:
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        suffix = "parquet" if self.format == "parquet" and _has_pyarrow() else "csv"
        return self.root / market.upper() / interval / f"{safe_symbol}.{suffix}"

    def save_bars(self, df: pd.DataFrame, symbol: str, market: str, interval: str) -> Path:
        path = self._path(symbol, market, interval)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize_ohlcv(df, symbol=symbol, market=market)
        if path.suffix == ".parquet":
            normalized.to_parquet(path, index=False)
        else:
            normalized.to_csv(path, index=False)
        return path

    def load_bars(self, symbol: str, market: str, interval: str) -> pd.DataFrame:
        path = self._path(symbol, market, interval)
        if not path.exists():
            raise FileNotFoundError(f"No cached bars found: {path}")
        raw = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        return normalize_ohlcv(raw, symbol=symbol, market=market)

    def exists(self, symbol: str, market: str, interval: str) -> bool:
        return self._path(symbol, market, interval).exists()

    def query(self, sql: str) -> pd.DataFrame:
        """Run a DuckDB query against this store's Parquet files."""
        try:
            import duckdb
        except ModuleNotFoundError as exc:
            raise RuntimeError("Install pfi_os[data] to use DuckDB queries.") from exc
        return duckdb.connect(":memory:").execute(sql).fetchdf()


def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True
