from __future__ import annotations

from pathlib import Path

from src.data_io import read_csv
from src.models import CollectorResult


class CSVCollector:
    source_name = "Local CSV"
    source_url = "file://local"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self) -> CollectorResult:
        rows = read_csv(self.path)
        return CollectorResult.ok(
            source_name=self.source_name,
            source_url=self.path.resolve().as_uri(),
            parsed_data=rows,
        )
