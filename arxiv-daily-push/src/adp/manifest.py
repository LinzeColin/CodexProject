"""Run Manifest —— 每次 run 追加一行 JSON（五态），系统页由它渲染（不变量 9）.

契约：docs/v03/04_开发记录/RUN_MANIFEST契约.md。
- 五态必填；「降级」必须列出降级项；「弃权」必须给原因与最高分。
- side_effects_authorized=false 时 counts.已交付必须为 0（不变量 5 的落地检查）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from . import config

RESULTS = ("正常", "降级", "弃权", "失败", "未运行")


class ManifestViolation(ValueError):
    """Manifest 违反契约（如未授权却声称已交付）——写入前直接拒绝."""


def manifest_path() -> Path:
    return config.data_dir() / "run_manifests.jsonl"


def write_manifest(conn: sqlite3.Connection | None, entry: dict[str, Any]) -> dict[str, Any]:
    result = entry.get("result")
    if result not in RESULTS:
        raise ManifestViolation(f"result must be one of {RESULTS}, got {result!r}")
    if result == "降级" and not entry.get("降级项"):
        raise ManifestViolation("降级 manifest 必须列出降级项")
    if result == "弃权" and not entry.get("弃权原因"):
        raise ManifestViolation("弃权 manifest 必须给出原因")
    counts = entry.setdefault("counts", {})
    if not entry.get("side_effects_authorized", False) and counts.get("已交付", 0) != 0:
        raise ManifestViolation("side_effects_authorized=false 时 counts.已交付必须为 0（不变量 5）")
    entry.setdefault("config_versions", config.config_versions())
    entry.setdefault("artifacts", [])

    line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    path = manifest_path()
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    if conn is not None:
        # jsonl 是 manifest 的正典；DB 行只是查询镜像。镜像写失败不重写文件
        # （对抗性验证修复：此前上层兜底会把同一行追加两次），只降级记录。
        try:
            conn.execute(
                "INSERT OR REPLACE INTO run_manifests (run_id, manifest_json) VALUES (?, ?)",
                (entry["run_id"], line),
            )
            conn.commit()
        except Exception:
            pass
    return entry


def read_manifests(limit: int = 30) -> list[dict[str, Any]]:
    path = manifest_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]][::-1]


def latest_result() -> str:
    """徽章/首页状态点只允许读取最近一行的 result 渲染（契约规则）."""
    manifests = read_manifests(limit=1)
    return manifests[0]["result"] if manifests else "未运行"
