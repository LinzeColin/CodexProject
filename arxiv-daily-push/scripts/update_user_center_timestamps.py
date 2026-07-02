#!/usr/bin/env python3
"""Update and validate concrete owner-center Markdown timestamps."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Australia/Sydney")
TIMESTAMP_RE = re.compile(
    r"^更新时间：(?P<value>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) Australia/Sydney$"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def user_center_files() -> list[Path]:
    return sorted((repo_root() / "用户中心").glob("*.md"))


def current_timestamp() -> str:
    now = datetime.now(TIMEZONE).replace(microsecond=0)
    return f"更新时间：{now:%Y-%m-%d %H:%M:%S} Australia/Sydney"


def replace_or_insert_timestamp(text: str, timestamp_line: str) -> str:
    lines = [
        line
        for line in text.splitlines()
        if not (line.startswith("更新时间：") or line.startswith("更新时间来源："))
    ]

    if lines and lines[0].startswith("# "):
        if len(lines) == 1:
            lines.append("")
        elif lines[1] != "":
            lines.insert(1, "")
        lines.insert(2, timestamp_line)
    else:
        lines.insert(0, timestamp_line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def validate_timestamp(path: Path, now: datetime) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    timestamp_lines = [line for line in lines if line.startswith("更新时间")]
    if len(timestamp_lines) != 1:
        return [f"{path}: expected exactly one 更新时间 line, found {len(timestamp_lines)}"]

    if not lines or not lines[0].startswith("# "):
        return [f"{path}: expected first line to be an H1 heading"]
    if len(lines) < 3 or lines[1] != "" or not lines[2].startswith("更新时间"):
        return [f"{path}: expected 更新时间 line immediately under H1"]

    match = TIMESTAMP_RE.match(timestamp_lines[0])
    if not match:
        return [f"{path}: invalid timestamp format: {timestamp_lines[0]}"]

    value = datetime.strptime(match.group("value"), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=TIMEZONE
    )
    if value > now + timedelta(seconds=120):
        errors.append(f"{path}: timestamp is in the future: {timestamp_lines[0]}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write current timestamps")
    parser.add_argument("--check", action="store_true", help="validate timestamps")
    args = parser.parse_args()

    if not args.write and not args.check:
        parser.error("use --write or --check")

    files = user_center_files()
    if args.write:
        line = current_timestamp()
        for path in files:
            text = path.read_text(encoding="utf-8")
            path.write_text(replace_or_insert_timestamp(text, line), encoding="utf-8")
        print(f"updated {len(files)} files: {line}")

    if args.check:
        now = datetime.now(TIMEZONE).replace(microsecond=0)
        errors = [error for path in files for error in validate_timestamp(path, now)]
        if errors:
            print("\n".join(errors))
            return 1
        print(f"validated {len(files)} user-center timestamps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
