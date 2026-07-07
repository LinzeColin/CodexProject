from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from .models import SourceFile, SourceMessage


DT_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]


def parse_dt(value: str) -> datetime:
    value = (value or "").strip()
    for fmt in DT_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported datetime: {value!r}")


class DwsArchiveReader:
    def __init__(self, input_root: str | Path):
        self.input_root = Path(input_root).expanduser()

    def group_path(self, group_name: str) -> Path:
        return self.input_root / group_name

    def read_messages(self, group_name: str) -> list[SourceMessage]:
        path = self.group_path(group_name) / "chat_records" / "chat_records.csv"
        if not path.exists():
            return []
        out: list[SourceMessage] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    out.append(SourceMessage(
                        group_name=row.get("group_name") or group_name,
                        message_id=row.get("open_message_id") or row.get("message_id") or "",
                        message_time=parse_dt(row.get("message_time", "")),
                        sender_name=row.get("sender_name", ""),
                        content=row.get("content", ""),
                        resource_count=int(row.get("resource_count") or 0),
                        resource_types=tuple(x for x in (row.get("resource_types") or "").split(",") if x),
                    ))
                except Exception:
                    continue
        return out

    def inspect_group_sources(self, group_name: str, check_date: date) -> list[dict[str, str]]:
        group_dir = self.group_path(group_name)
        chat_path = group_dir / "chat_records" / "chat_records.csv"
        manifest_path = group_dir / "_manifest" / "manifest.csv"
        if not group_dir.exists():
            return [{
                "issue_type": "SOURCE_MISSING",
                "issue_code": "SOURCE_MISSING_GROUP",
                "group_name": group_name,
                "check_date": check_date.isoformat(),
                "path": str(group_dir),
            }]
        if not chat_path.exists():
            return [{
                "issue_type": "SOURCE_MISSING",
                "issue_code": "SOURCE_MISSING_CHAT_RECORDS",
                "group_name": group_name,
                "check_date": check_date.isoformat(),
                "path": str(chat_path),
            }]

        issues: list[dict[str, str]] = []
        if not manifest_path.exists():
            issues.append({
                "issue_type": "SOURCE_MISSING",
                "issue_code": "SOURCE_MISSING_MANIFEST",
                "group_name": group_name,
                "check_date": check_date.isoformat(),
                "path": str(manifest_path),
            })

        messages = self.read_messages(group_name)
        if not messages:
            issues.append({
                "issue_type": "SOURCE_MISSING",
                "issue_code": "SOURCE_EMPTY_CHAT_RECORDS",
                "group_name": group_name,
                "check_date": check_date.isoformat(),
                "path": str(chat_path),
            })
            return issues

        latest_message_time = max(msg.message_time for msg in messages)
        if latest_message_time.date() < check_date:
            issues.append({
                "issue_type": "SOURCE_STALE",
                "issue_code": "SOURCE_CHAT_RECORDS_STALE",
                "group_name": group_name,
                "latest_message_date": latest_message_time.date().isoformat(),
                "check_date": check_date.isoformat(),
                "path": str(chat_path),
            })
        return issues

    def read_files(self, group_name: str) -> list[SourceFile]:
        path = self.group_path(group_name) / "_manifest" / "manifest.csv"
        if not path.exists():
            return []
        out: list[SourceFile] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                output_path = row.get("output_path") or ""
                absolute_path = str(self.group_path(group_name) / output_path) if output_path else ""
                try:
                    out.append(SourceFile(
                        group_name=row.get("group_name") or group_name,
                        message_id=row.get("message_id") or "",
                        message_time=parse_dt(row.get("message_time", "")),
                        sender_name=row.get("sender_name", ""),
                        resource_type=row.get("resource_type", ""),
                        output_path=output_path,
                        absolute_path=absolute_path,
                        sha256=row.get("sha256", ""),
                        status=row.get("status", ""),
                    ))
                except Exception:
                    continue
        return out
