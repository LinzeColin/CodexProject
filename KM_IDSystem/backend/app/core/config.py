import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("OPME_DATA_DIR", ROOT_DIR / "data")).expanduser()
REPORT_DIR = Path(os.environ.get("OPME_REPORT_DIR", ROOT_DIR / "reports")).expanduser()
SAMPLE_DIR = ROOT_DIR / "samples"

DATABASE_PATH = Path(os.environ.get("OPME_DATABASE_PATH", DATA_DIR / "wuhan_kaiming.sqlite")).expanduser()

APP_NAME = "武汉开明智能工业运维助手"
APP_VERSION = "1.0.0"


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

