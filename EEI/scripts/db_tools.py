from __future__ import annotations

import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def load_env_file() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def database_url() -> str:
    load_env_file()
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def connect_database() -> psycopg.Connection:
    return psycopg.connect(database_url(), connect_timeout=5)


def read_sql(path: Path) -> str:
    chunks: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("-- include:"):
            include_path = ROOT / stripped.removeprefix("-- include:").strip()
            chunks.append(read_sql(include_path))
        else:
            chunks.append(line)
    return "\n".join(chunks) + "\n"
