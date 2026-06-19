#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.db_health import check_database  # noqa: E402


def command_path(command: str) -> str | None:
    return shutil.which(command)


def git_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def file_status(path: str) -> str:
    return "present" if (ROOT / path).exists() else "missing"


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    database = check_database(database_url)
    tools = {
        "git": command_path("git"),
        "python": command_path("python"),
        "node": command_path("node"),
        "npm": command_path("npm"),
        "docker": command_path("docker"),
        "psql": command_path("psql"),
        "postgres": command_path("postgres"),
        "initdb": command_path("initdb"),
    }
    required_files = {
        "Makefile": file_status("Makefile"),
        "pyproject.toml": file_status("pyproject.toml"),
        "uv.lock": file_status("uv.lock"),
        "package.json": file_status("package.json"),
        "pnpm-lock.yaml": file_status("pnpm-lock.yaml"),
        "docker-compose.yml": file_status("docker-compose.yml"),
        ".env.example": file_status(".env.example"),
    }
    payload = {
        "product": "Enterprise Ecosystem Intelligence",
        "product_name_zh": "商域图谱",
        "gate": "G1",
        "git_clean": git_clean(),
        "tools": tools,
        "files": required_files,
        "database": {
            "configured": bool(database_url),
            "status": database.status,
            "detail": database.detail,
        },
        "g1_ready": bool(tools["docker"]) and database.ok,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
