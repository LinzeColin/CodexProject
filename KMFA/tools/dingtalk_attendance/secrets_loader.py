#!/usr/bin/env python3
"""Local-only configuration loader for KMFA S19."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNTIME_ENV_PATH = ROOT / "metadata" / "dingtalk_attendance" / "private_runtime" / ".env.local"


def load_local_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_runtime_env(env_path: Path | None = DEFAULT_RUNTIME_ENV_PATH) -> dict[str, str]:
    values = dict(os.environ)
    if env_path is not None:
        values.update(load_local_env(env_path))
    return values
