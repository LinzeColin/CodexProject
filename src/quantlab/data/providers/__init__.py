from quantlab.data.providers.csv_provider import CSVProvider
from quantlab.data.providers.sample_provider import SampleDataProvider

try:
    from quantlab.data.providers.alpha_vantage import AlphaVantageProvider
except Exception:  # pragma: no cover
    AlphaVantageProvider = None

try:
    from quantlab.data.providers.tushare_provider import TushareProvider
except Exception:  # pragma: no cover
    TushareProvider = None

try:
    from quantlab.data.providers.akshare_provider import AKShareProvider
except Exception:  # pragma: no cover
    AKShareProvider = None

try:
    from quantlab.data.providers.yahoo_finance import YahooFinanceProvider
except Exception:  # pragma: no cover
    YahooFinanceProvider = None

try:
    from quantlab.data.providers.polygon_provider import PolygonProvider
except Exception:  # pragma: no cover
    PolygonProvider = None

try:
    from quantlab.data.providers.moomoo_provider import MoomooProvider
except Exception:  # pragma: no cover
    MoomooProvider = None

__all__ = [
    "CSVProvider",
    "SampleDataProvider",
    "AlphaVantageProvider",
    "TushareProvider",
    "AKShareProvider",
    "YahooFinanceProvider",
    "PolygonProvider",
    "MoomooProvider",
]
