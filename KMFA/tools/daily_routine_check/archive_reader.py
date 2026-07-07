from __future__ import annotations

import csv
import io
import stat
import zipfile
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
        self.zip_path = self._resolve_zip_path(self.input_root)
        self._zip_names_cache: list[str] | None = None
        self._zip_error_code: str | None = None
        self._zip_error_detail: str | None = None

    @staticmethod
    def _resolve_zip_path(input_root: Path) -> Path:
        if input_root.suffix.lower() == ".zip":
            return input_root
        return input_root.with_suffix(".zip")

    def _should_use_zip(self) -> bool:
        if self.input_root.suffix.lower() == ".zip":
            return True
        return not self.input_root.is_dir() and self.zip_path.exists()

    def _path_is_dataless(self, path: Path) -> bool:
        try:
            flags = getattr(path.stat(), "st_flags", 0)
        except OSError:
            return False
        return bool(flags & getattr(stat, "SF_DATALESS", 0))

    def _zip_names(self) -> list[str]:
        if self._zip_names_cache is not None:
            return self._zip_names_cache
        self._zip_names_cache = []
        self._zip_error_code = None
        self._zip_error_detail = None
        if not self.zip_path.exists():
            self._zip_error_code = "ZIP_INPUT_MISSING"
            self._zip_error_detail = f"{self.zip_path} does not exist"
            return self._zip_names_cache
        if self._path_is_dataless(self.zip_path):
            self._zip_error_code = "ZIP_INPUT_UNREADABLE"
            self._zip_error_detail = f"{self.zip_path} is a OneDrive dataless placeholder; hydrate or replace it before live checks"
            return self._zip_names_cache
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                self._zip_names_cache = zf.namelist()
        except (zipfile.BadZipFile, OSError) as exc:
            self._zip_error_code = "ZIP_INPUT_UNREADABLE"
            self._zip_error_detail = f"{self.zip_path} is not a readable zip: {exc}"
        return self._zip_names_cache

    def zip_error_code(self) -> str | None:
        self._zip_names()
        return self._zip_error_code

    def zip_error_detail(self) -> str:
        self._zip_names()
        return self._zip_error_detail or ""

    def find_zip_member(self, group_name: str, relative_path: str) -> str | None:
        suffix = f"{group_name}/{relative_path}".replace("\\", "/")
        matches = [name for name in self._zip_names() if name.rstrip("/").endswith(suffix)]
        if not matches:
            return None
        return sorted(matches, key=lambda item: (len(item), item))[0]

    def _read_zip_csv(self, member: str) -> Iterable[dict[str, str]]:
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                with zf.open(member) as raw:
                    text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                    yield from csv.DictReader(text)
        except (KeyError, zipfile.BadZipFile, OSError):
            return

    def group_path(self, group_name: str) -> Path:
        return self.input_root / group_name

    def read_messages(self, group_name: str) -> list[SourceMessage]:
        if self._should_use_zip():
            member = self.find_zip_member(group_name, "chat_records/chat_records.csv")
            if not member:
                return []
            return self._messages_from_rows(self._read_zip_csv(member), group_name)

        path = self.group_path(group_name) / "chat_records" / "chat_records.csv"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return self._messages_from_rows(csv.DictReader(f), group_name)

    def _messages_from_rows(self, rows: Iterable[dict[str, str]], group_name: str) -> list[SourceMessage]:
        out: list[SourceMessage] = []
        for row in rows:
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
        if self._should_use_zip():
            zip_error = self.zip_error_code()
            if zip_error:
                return [{
                    "issue_type": "SOURCE_MISSING",
                    "issue_code": zip_error,
                    "group_name": group_name,
                    "check_date": check_date.isoformat(),
                    "path": str(self.zip_path),
                    "detail": self.zip_error_detail(),
                }]
            chat_member = self.find_zip_member(group_name, "chat_records/chat_records.csv")
            manifest_member = self.find_zip_member(group_name, "_manifest/manifest.csv")
            if not chat_member:
                return [{
                    "issue_type": "SOURCE_MISSING",
                    "issue_code": "SOURCE_MISSING_ZIP_CHAT_RECORDS",
                    "group_name": group_name,
                    "check_date": check_date.isoformat(),
                    "path": f"zip://{self.zip_path}!/*/{group_name}/chat_records/chat_records.csv",
                }]
            issues: list[dict[str, str]] = []
            if not manifest_member:
                issues.append({
                    "issue_type": "SOURCE_MISSING",
                    "issue_code": "SOURCE_MISSING_ZIP_MANIFEST",
                    "group_name": group_name,
                    "check_date": check_date.isoformat(),
                    "path": f"zip://{self.zip_path}!/*/{group_name}/_manifest/manifest.csv",
                })
            messages = self.read_messages(group_name)
            if not messages:
                issues.append({
                    "issue_type": "SOURCE_MISSING",
                    "issue_code": "SOURCE_EMPTY_ZIP_CHAT_RECORDS",
                    "group_name": group_name,
                    "check_date": check_date.isoformat(),
                    "path": f"zip://{self.zip_path}!/{chat_member}",
                })
                return issues
            latest_message_time = max(msg.message_time for msg in messages)
            if latest_message_time.date() < check_date:
                issues.append({
                    "issue_type": "SOURCE_STALE",
                    "issue_code": "SOURCE_ZIP_CHAT_RECORDS_STALE",
                    "group_name": group_name,
                    "latest_message_date": latest_message_time.date().isoformat(),
                    "check_date": check_date.isoformat(),
                    "path": f"zip://{self.zip_path}!/{chat_member}",
                })
            return issues

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
        if self._should_use_zip():
            member = self.find_zip_member(group_name, "_manifest/manifest.csv")
            if not member:
                return []
            group_prefix = member.rsplit("/_manifest/manifest.csv", 1)[0]
            return self._files_from_rows(self._read_zip_csv(member), group_name, group_prefix)

        path = self.group_path(group_name) / "_manifest" / "manifest.csv"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return self._files_from_rows(csv.DictReader(f), group_name)

    def _files_from_rows(
        self,
        rows: Iterable[dict[str, str]],
        group_name: str,
        zip_group_prefix: str | None = None,
    ) -> list[SourceFile]:
        out: list[SourceFile] = []
        for row in rows:
            output_path = row.get("output_path") or ""
            if zip_group_prefix and output_path:
                absolute_path = f"zip://{self.zip_path}!/{zip_group_prefix}/{output_path}"
            else:
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
