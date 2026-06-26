from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from pfi_os.data.models import BarDataRequest


class DataProvider(ABC):
    name = "base"

    @abstractmethod
    def get_bars(self, request: BarDataRequest) -> pd.DataFrame:
        raise NotImplementedError
