from src.collectors.base import CSVCollector


class WatchlistCollector(CSVCollector):
    source_name = "Moomoo Watchlist"


class WatchlistSnapshotCollector(CSVCollector):
    source_name = "Moomoo Watchlist Snapshot"
