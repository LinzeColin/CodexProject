#!/usr/bin/env python3
"""R6 private state machine for idempotent attendance automation closure."""

from __future__ import annotations

import json
import os
import csv
import fcntl
import hashlib
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT, TIMEZONE
from KMFA.tools.dingtalk_attendance.final_reconciliation import (
    FINAL_RESULT_KIND,
    find_latest_pending_work_date,
    run_final_reconciliation,
)
from KMFA.tools.dingtalk_attendance.identity import (
    IdentityConflictError,
    archive_manifest_paths,
    run_type_from_run_id,
    validate_manifest_identity,
)
from KMFA.tools.dingtalk_attendance.official_report_reconstruction import (
    OFFICIAL_COLUMNS,
    build_reconciliation_certificate,
    build_reconstructed_rows,
    compare_standard_entry,
    validate_reconciliation_certificate,
    write_reconciliation_certificate,
)
from KMFA.tools.dingtalk_attendance.run_attendance import run_attendance


DELIVERY_DISABLED_STATUS = "NOT_SENT_OWNER_DISABLED"
COMPLETE_STATUSES = {"COMPLETED", "RECOVERED_COMPLETE"}
PRIVATE_R6_ROOT = Path("KMFA/metadata/dingtalk_attendance/private_runtime/r6")
REPORT_NAMES = tuple(OFFICIAL_COLUMNS[index] for index in [*range(8, 37), *range(45, 49)])
LEAVE_NAMES = ("事假", "病假", "年假", "调休", "婚假", "产假", "陪产假", "路途假")


class OfficialExportAmbiguousError(RuntimeError):
    pass


class OfficialExportInvalidError(RuntimeError):
    pass


class R6Coordinator:
    """Persist only aggregate, private R6 state and recover from artifact-complete interruptions."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.status_path = root / "运行状态.md"
        self.root.mkdir(parents=True, exist_ok=True)
        self.state = self._load()
        self._write()

    def ensure_slot(
        self,
        *,
        work_date: str,
        run_slot: str,
        trigger_source: str,
        runner: Callable[[], Mapping[str, Any]],
        completed_probe: Callable[[], Mapping[str, Any] | None],
    ) -> dict[str, Any]:
        if run_slot not in {"morning", "evening"}:
            raise ValueError("run_slot must be morning or evening")
        day = self._day(work_date)
        existing = day["slots"].get(run_slot)
        if isinstance(existing, Mapping) and existing.get("status") in COMPLETE_STATUSES:
            return {"status": "IDEMPOTENT_SKIP", "work_date": work_date, "run_slot": run_slot}

        recovered = completed_probe()
        if recovered is not None:
            day["slots"][run_slot] = {
                "status": "RECOVERED_COMPLETE",
                "trigger_source": trigger_source,
                **self._aggregate(recovered),
            }
            self._event(work_date, run_slot, "RECOVERED_COMPLETE")
            self._write()
            return {"status": "RECOVERED_COMPLETE", "work_date": work_date, "run_slot": run_slot}

        day["slots"][run_slot] = {"status": "RUNNING", "trigger_source": trigger_source}
        self._event(work_date, run_slot, "RUNNING")
        self._write()
        try:
            result = dict(runner())
        except Exception as exc:
            day["slots"][run_slot] = {
                "status": "INTERRUPTED",
                "trigger_source": trigger_source,
                "error_type": exc.__class__.__name__,
            }
            self._event(work_date, run_slot, "INTERRUPTED")
            self._write()
            return {"status": "INTERRUPTED", "work_date": work_date, "run_slot": run_slot}

        valid = (
            result.get("status") == "COMPLETED"
            and result.get("notification_status") == DELIVERY_DISABLED_STATUS
        )
        status = "COMPLETED" if valid else "FAILED"
        day["slots"][run_slot] = {
            "status": status,
            "trigger_source": trigger_source,
            **self._aggregate(result),
        }
        self._event(work_date, run_slot, status)
        self._write()
        return {"status": status, "work_date": work_date, "run_slot": run_slot, **self._aggregate(result)}

    def advance_final(
        self,
        *,
        work_date: str,
        export_finder: Callable[[], Path | None],
        certificate_builder: Callable[[Path], Path],
        final_runner: Callable[[Path], Mapping[str, Any]],
        completed_probe: Callable[[], Mapping[str, Any] | None],
        trigger_source: str = "automation",
    ) -> dict[str, Any]:
        day = self._day(work_date)
        existing = day.get("final")
        if isinstance(existing, Mapping) and existing.get("status") in {
            "OFFICIAL_FINAL_RECONCILIATION_PASS",
            "RECOVERED_COMPLETE",
        }:
            return {"status": "IDEMPOTENT_SKIP", "work_date": work_date}

        recovered = completed_probe()
        if recovered is not None:
            result = {
                "status": "RECOVERED_COMPLETE",
                "trigger_source": trigger_source,
                "monthly_written": True,
                **self._aggregate(recovered),
            }
            day["final"] = result
            self._event(work_date, "final", "RECOVERED_COMPLETE")
            self._write()
            return {"status": "RECOVERED_COMPLETE", "work_date": work_date}

        export_path = export_finder()
        if export_path is None:
            day["official_export"] = {"status": "WAITING_OFFICIAL_REPORT"}
            self._event(work_date, "final", "WAITING_OFFICIAL_REPORT")
            self._write()
            return {
                "status": "WAITING_OFFICIAL_REPORT",
                "work_date": work_date,
                "next_action": "AUTOMATIC_BROWSER_EXPORT_OR_NEXT_NATURAL_TRIGGER",
            }

        day["official_export"] = {"status": "FOUND", "file_name": export_path.name}
        day["final"] = {"status": "BUILDING_CERTIFICATE", "trigger_source": trigger_source}
        self._write()
        try:
            certificate_path = certificate_builder(export_path)
            day["final"] = {"status": "RUNNING_FINAL", "trigger_source": trigger_source}
            self._write()
            result = dict(final_runner(certificate_path))
        except Exception as exc:
            day["final"] = {
                "status": "INTERRUPTED",
                "trigger_source": trigger_source,
                "error_type": exc.__class__.__name__,
            }
            self._event(work_date, "final", "INTERRUPTED")
            self._write()
            return {"status": "INTERRUPTED", "work_date": work_date}

        valid = result.get("status") == "OFFICIAL_FINAL_RECONCILIATION_PASS"
        final_status = "OFFICIAL_FINAL_RECONCILIATION_PASS" if valid else "FAILED"
        day["final"] = {
            "status": final_status,
            "trigger_source": trigger_source,
            "monthly_written": bool(result.get("monthly_written", valid)),
            **self._aggregate(result),
        }
        self._event(work_date, "final", final_status)
        self._write()
        return {"status": final_status, "work_date": work_date, **self._aggregate(result)}

    def record_final_success(
        self,
        *,
        work_date: str,
        trigger_source: str,
        result: Mapping[str, Any],
    ) -> None:
        self._day(work_date)["final"] = {
            "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
            "trigger_source": trigger_source,
            **self._aggregate(result),
        }
        self._event(work_date, "final", "OFFICIAL_FINAL_RECONCILIATION_PASS")
        self._write()

    def acceptance_summary(self) -> dict[str, Any]:
        completed: list[str] = []
        for work_date, day in sorted(self.state["work_dates"].items()):
            slots = day.get("slots", {})
            final = day.get("final", {})
            if not isinstance(slots, Mapping) or not isinstance(final, Mapping):
                continue
            if all(
                isinstance(slots.get(slot), Mapping)
                and slots[slot].get("status") in COMPLETE_STATUSES
                and slots[slot].get("trigger_source") == "automation"
                for slot in ("morning", "evening")
            ) and (
                final.get("status") in {"OFFICIAL_FINAL_RECONCILIATION_PASS", "RECOVERED_COMPLETE"}
                and final.get("trigger_source") == "automation"
                and int(final.get("differing_required_cells", 0)) == 0
                and final.get("monthly_written") is True
                and final.get("actual_workday") is True
            ):
                completed.append(work_date)
        return {
            "natural_completed_work_days": len(completed),
            "natural_completed_dates": completed,
            "target_work_days": 5,
        }

    def _day(self, work_date: str) -> dict[str, Any]:
        datetime.strptime(work_date, "%Y-%m-%d")
        return self.state["work_dates"].setdefault(work_date, {"slots": {}})

    def _load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "work_dates": {}, "events": []}
        if not isinstance(payload, dict) or not isinstance(payload.get("work_dates"), dict):
            return {"schema_version": 1, "work_dates": {}, "events": []}
        payload.setdefault("events", [])
        return payload

    def _event(self, work_date: str, phase: str, status: str) -> None:
        self.state["events"].append(
            {
                "work_date": work_date,
                "phase": phase,
                "status": status,
                "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            }
        )
        self.state["events"] = self.state["events"][-200:]

    @staticmethod
    def _aggregate(result: Mapping[str, Any]) -> dict[str, Any]:
        allowed = (
            "notification_status",
            "member_count",
            "official_people",
            "dws_people",
            "matched_people",
            "compared_columns",
            "compared_cells",
            "missing_people",
            "extra_people",
            "missing_required_columns",
            "missing_required_cells",
            "differing_required_cells",
            "monthly_written",
            "actual_workday",
            "run_id",
        )
        return {key: result[key] for key in allowed if key in result}

    def _write(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.state_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(temp, 0o600)
        os.replace(temp, self.state_path)
        summary = self.acceptance_summary()
        lines = [
            "# KMFA 钉钉考勤 R6 运行状态",
            "",
            f"- 自然运行已完成工作日：{summary['natural_completed_work_days']} / {summary['target_work_days']}",
            f"- 已完成日期：{', '.join(summary['natural_completed_dates']) or '无'}",
            "- 发送状态：硬关闭",
            "",
            "| 工作日期 | 晨间 | 晚间 | 官方最终核对 | 月累计单写 |",
            "|---|---|---|---|---|",
        ]
        for work_date, day in sorted(self.state["work_dates"].items()):
            slots = day.get("slots", {})
            final = day.get("final", {})
            lines.append(
                "| {date} | {morning} | {evening} | {final} | {monthly} |".format(
                    date=work_date,
                    morning=(slots.get("morning", {}) or {}).get("status", "PENDING"),
                    evening=(slots.get("evening", {}) or {}).get("status", "PENDING"),
                    final=(final or {}).get("status", "PENDING"),
                    monthly="YES" if (final or {}).get("monthly_written") is True else "NO",
                )
            )
        status_temp = self.status_path.with_suffix(".md.tmp")
        status_temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(status_temp, 0o600)
        os.replace(status_temp, self.status_path)


def parse_official_csv(path: Path, *, work_date: str) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [list(row) for row in csv.reader(handle)]
    if len(rows) != 48 or max((len(row) for row in rows), default=0) != 49:
        raise OfficialExportInvalidError("official workbook must contain 48 rows and 49 columns")
    normalized: list[list[Any]] = []
    for row in rows:
        padded = [*row, *([""] * (49 - len(row)))]
        normalized.append([None if value == "" else value for value in padded[:49]])
    if work_date not in str(normalized[0][0] or ""):
        raise OfficialExportInvalidError("official workbook title does not match target work date")
    user_ids = [str(row[5]) for row in normalized[4:] if row[5] not in (None, "")]
    if len(user_ids) != 44 or len(set(user_ids)) != 44:
        raise OfficialExportInvalidError("official workbook must contain 44 unique UserId rows")
    return {
        "input_name": path.name,
        "sheet_name": "每日统计",
        "address": "A1:AW48",
        "values": normalized,
        "formulas": [[None] * 49 for _ in normalized],
    }


def _soffice_binary() -> str:
    binary = shutil.which("soffice")
    if not binary:
        raise OfficialExportInvalidError("soffice is required to read official XLS/XLSX exports")
    return binary


def workbook_to_standard(path: Path, *, work_date: str) -> dict[str, Any]:
    if path.suffix.lower() not in {".xls", ".xlsx"}:
        raise OfficialExportInvalidError("official export must be XLS or XLSX")
    with tempfile.TemporaryDirectory(prefix="kmfa-official-") as tmpdir:
        completed = subprocess.run(
            [_soffice_binary(), "--headless", "--convert-to", "csv", "--outdir", tmpdir, str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        csv_paths = list(Path(tmpdir).glob("*.csv"))
        if completed.returncode != 0 or len(csv_paths) != 1:
            raise OfficialExportInvalidError("official workbook conversion failed")
        return parse_official_csv(csv_paths[0], work_date=work_date)


def find_official_export(
    *,
    work_date: str,
    search_roots: list[Path],
    validator: Callable[[Path], bool],
) -> Path | None:
    compact = work_date.replace("-", "")
    candidates: list[Path] = []
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in root.iterdir():
            if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"} and compact in path.name:
                try:
                    if validator(path):
                        candidates.append(path)
                except (OSError, OfficialExportInvalidError):
                    continue
    if not candidates:
        return None
    by_hash: dict[str, list[Path]] = {}
    for path in candidates:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        by_hash.setdefault(digest, []).append(path)
    if len(by_hash) != 1:
        raise OfficialExportAmbiguousError("multiple different official exports match the same work date")
    return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))


def _run_dws_readonly(args: list[str]) -> dict[str, Any]:
    allowlist = (
        ("attendance", "report", "columns"),
        ("attendance", "report", "query-data"),
        ("attendance", "report", "query-leave"),
        ("attendance", "approve", "list"),
        ("attendance", "group", "search"),
        ("attendance", "group", "filtered-get"),
        ("contact", "user", "get"),
    )
    if not any(tuple(args[: len(prefix)]) == prefix for prefix in allowlist):
        raise RuntimeError("command outside R6 read-only DWS allowlist")
    completed = subprocess.run(
        ["dws", *args, "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"DWS read-only command failed: {' '.join(args[:3])} exit={completed.returncode}")
    payload = json.loads(completed.stdout)
    if payload.get("success") is not True:
        raise RuntimeError(f"DWS read-only business failure: {' '.join(args[:3])}")
    return payload


def _batches(values: list[str], size: int = 20) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def collect_reconstruction_source(
    standard: Mapping[str, Any],
    *,
    work_date: str,
    runner: Callable[[list[str]], dict[str, Any]] = _run_dws_readonly,
) -> dict[str, Any]:
    rows = standard.get("values")
    if not isinstance(rows, list):
        raise OfficialExportInvalidError("official standard values are missing")
    users = [str(row[5]) for row in rows[4:] if isinstance(row, list) and len(row) == 49]
    if len(users) != 44 or len(set(users)) != 44:
        raise OfficialExportInvalidError("official standard must contain 44 unique users")

    columns_payload = runner(["attendance", "report", "columns"])
    column_rows = columns_payload.get("result") or []
    name_to_id = {
        str(row.get("name")): str(row.get("id"))
        for row in column_rows
        if isinstance(row, Mapping) and row.get("name") is not None and row.get("id") is not None
    }
    missing = [name for name in REPORT_NAMES if name not in name_to_id]
    if missing:
        raise RuntimeError("official DWS report columns are incomplete")
    column_ids = [name_to_id[name] for name in REPORT_NAMES]
    source: dict[str, Any] = {
        "dates": [work_date],
        "user_count": len(users),
        "report_column_names": list(REPORT_NAMES),
        "report_column_ids": column_ids,
        "report_query_data": {work_date: []},
        "report_query_leave": {work_date: []},
        "user_profiles": [],
        "approval_records": [],
        "attendance_groups": [],
    }
    for batch in _batches(users):
        joined = ",".join(batch)
        source["report_query_data"][work_date].append(
            runner(
                [
                    "attendance",
                    "report",
                    "query-data",
                    "--users",
                    joined,
                    "--columns",
                    ",".join(column_ids),
                    "--start",
                    f"{work_date} 00:00:00",
                    "--end",
                    f"{work_date} 23:59:59",
                ]
            )
        )
        source["report_query_leave"][work_date].append(
            runner(
                [
                    "attendance",
                    "report",
                    "query-leave",
                    "--users",
                    joined,
                    "--leave-names",
                    ",".join(LEAVE_NAMES),
                    "--start",
                    f"{work_date} 00:00:00",
                    "--end",
                    f"{work_date} 23:59:59",
                ]
            )
        )
        source["user_profiles"].append(runner(["contact", "user", "get", "--ids", joined]))
        source["approval_records"].append(
            runner(
                [
                    "attendance",
                    "approve",
                    "list",
                    "--users",
                    joined,
                    "--types",
                    "overtime,trip,leave,patch",
                    "--start",
                    work_date,
                    "--end",
                    work_date,
                ]
            )
        )

    group_search = runner(["attendance", "group", "search", "--page", "1", "--limit", "200"])
    source["attendance_groups"].append(group_search)
    group_result = group_search.get("result") or {}
    groups = group_result.get("items", []) if isinstance(group_result, Mapping) else group_result
    for group in groups or []:
        if isinstance(group, Mapping) and group.get("id") is not None:
            source["attendance_groups"].append(
                runner(
                    [
                        "attendance",
                        "group",
                        "filtered-get",
                        "--group-id",
                        str(group["id"]),
                        "--member",
                    ]
                )
            )
    return source


def build_automatic_certificate(
    export_path: Path,
    *,
    work_date: str,
    private_root: Path,
    dws_runner: Callable[[list[str]], dict[str, Any]] = _run_dws_readonly,
) -> Path:
    standard = workbook_to_standard(export_path, work_date=work_date)
    digest = hashlib.sha256(export_path.read_bytes()).hexdigest()
    evidence_dir = private_root / "official" / work_date
    evidence_dir.mkdir(parents=True, exist_ok=True)
    frozen = evidence_dir / f"official_{digest}{export_path.suffix.lower()}"
    if not frozen.exists():
        shutil.copy2(export_path, frozen)
        os.chmod(frozen, 0o600)
    standard_path = evidence_dir / "standard.private.json"
    standard_path.write_text(json.dumps(standard, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(standard_path, 0o600)
    source = collect_reconstruction_source(standard, work_date=work_date, runner=dws_runner)
    source_path = evidence_dir / "source.private.json"
    source_path.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(source_path, 0o600)
    comparison = compare_standard_entry(
        standard,
        build_reconstructed_rows(source, work_date=work_date),
        work_date=work_date,
    )
    comparison_path = evidence_dir / "comparison.private.json"
    comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(comparison_path, 0o600)
    certificate = build_reconciliation_certificate(comparison, official_sha256=digest)
    certificate["actual_workday"] = any(
        isinstance(row, list) and len(row) == 49 and row[8] not in (None, "")
        for row in standard["values"][4:]
    )
    errors = validate_reconciliation_certificate(certificate, expected_work_date=work_date)
    if errors:
        raise RuntimeError("official reconciliation failed: " + ", ".join(errors))
    return write_reconciliation_certificate(certificate, evidence_dir)


def _completed_reminder_probe(*, work_date: str, run_slot: str, archive_root: Path) -> dict[str, Any] | None:
    month_dir = archive_root / work_date[:7].replace("-", "")
    for path in sorted(archive_manifest_paths(month_dir), reverse=True):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            identity = validate_manifest_identity(manifest)
            run_id = str(manifest.get("run_id") or path.name.removesuffix(".manifest.json"))
            stats = manifest.get("stats") or {}
            receipt_path = manifest.get("dispatch_receipt")
            receipt = json.loads(Path(str(receipt_path)).read_text(encoding="utf-8")) if receipt_path else {}
        except (OSError, json.JSONDecodeError, IdentityConflictError):
            continue
        if (
            identity["identity_source"] == "skill_id"
            and run_type_from_run_id(run_id) == run_slot
            and str(manifest.get("work_date") or "") == work_date
            and stats.get("official_report_parity_status") == "PASS"
            and receipt.get("notification_status") == DELIVERY_DISABLED_STATUS
        ):
            return {"member_count": int(stats.get("member_count") or 0), "run_id": run_id}
    return None


def _completed_final_probe(*, work_date: str, archive_root: Path) -> dict[str, Any] | None:
    month_dir = archive_root / work_date[:7].replace("-", "")
    for path in sorted(archive_manifest_paths(month_dir), reverse=True):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            identity = validate_manifest_identity(manifest)
            certificate = manifest.get("official_reconciliation_certificate")
        except (OSError, json.JSONDecodeError, IdentityConflictError):
            continue
        if (
            identity["identity_source"] == "skill_id"
            and manifest.get("result_kind") == FINAL_RESULT_KIND
            and str(manifest.get("work_date") or "") == work_date
            and manifest.get("monthly_rollup_eligible") is True
            and isinstance(certificate, Mapping)
            and not validate_reconciliation_certificate(certificate, expected_work_date=work_date)
        ):
            return {
                "run_id": str(manifest.get("run_id") or ""),
                "monthly_written": True,
                "actual_workday": certificate.get("actual_workday") is True,
                **{
                    key: certificate[key]
                    for key in (
                        "official_people",
                        "dws_people",
                        "matched_people",
                        "compared_columns",
                        "compared_cells",
                        "missing_people",
                        "extra_people",
                        "missing_required_columns",
                        "missing_required_cells",
                        "differing_required_cells",
                    )
                },
            }
    return None


def _slot_runner(*, run_slot: str) -> dict[str, Any]:
    result = run_attendance(run_type=run_slot, timezone=TIMEZONE, allow_dws_commands=True)
    stats = result.get("collection_stats") or {}
    return {
        "status": result.get("status"),
        "notification_status": result.get("notification_status"),
        "member_count": int(stats.get("member_count") or 0),
        "run_id": str((result.get("run_plan") or {}).get("run_id") or ""),
    }


def _final_runner(*, work_date: str, certificate_path: Path) -> dict[str, Any]:
    result = run_final_reconciliation(
        work_date=work_date,
        timezone=TIMEZONE,
        allow_dws_commands=True,
        independent_evidence_path=certificate_path,
    )
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    return {
        "status": result.get("status"),
        "notification_status": result.get("notification_status"),
        "monthly_written": result.get("status") == "OFFICIAL_FINAL_RECONCILIATION_PASS",
        "actual_workday": certificate.get("actual_workday") is True,
        "run_id": Path(str(result.get("archive_manifest") or "")).name.removesuffix(".manifest.json"),
        **{
            key: certificate[key]
            for key in (
                "official_people",
                "dws_people",
                "matched_people",
                "compared_columns",
                "compared_cells",
                "missing_people",
                "extra_people",
                "missing_required_columns",
                "missing_required_cells",
                "differing_required_cells",
            )
        },
    }


def run_automatic_cycle(
    *,
    run_slot: str,
    trigger_source: str,
    resume_final_only: bool = False,
    private_root: Path = PRIVATE_R6_ROOT,
    archive_root: Path = Path(ONEDRIVE_ROOT),
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(ZoneInfo(TIMEZONE))
    today = current.date().isoformat()
    coordinator = R6Coordinator(private_root)
    results: dict[str, Any] = {"run_slot": run_slot, "trigger_source": trigger_source}
    if run_slot == "morning":
        pending = find_latest_pending_work_date(onedrive_root=archive_root, timezone=TIMEZONE, now=current)
        if pending:
            search_roots = [Path.home() / "Downloads", private_root / "export_inbox"]
            results["final"] = coordinator.advance_final(
                work_date=pending,
                trigger_source=trigger_source,
                export_finder=lambda: find_official_export(
                    work_date=pending,
                    search_roots=search_roots,
                    validator=lambda path: _workbook_is_valid(path, work_date=pending),
                ),
                certificate_builder=lambda path: build_automatic_certificate(
                    path,
                    work_date=pending,
                    private_root=private_root,
                ),
                final_runner=lambda certificate: _final_runner(
                    work_date=pending,
                    certificate_path=certificate,
                ),
                completed_probe=lambda: _completed_final_probe(work_date=pending, archive_root=archive_root),
            )
        else:
            results["final"] = {"status": "NO_PENDING_FINAL_RECONCILIATION"}
    if not resume_final_only:
        results["reminder"] = coordinator.ensure_slot(
            work_date=today,
            run_slot=run_slot,
            trigger_source=trigger_source,
            runner=lambda: _slot_runner(run_slot=run_slot),
            completed_probe=lambda: _completed_reminder_probe(
                work_date=today,
                run_slot=run_slot,
                archive_root=archive_root,
            ),
        )
    results["acceptance"] = coordinator.acceptance_summary()
    results["status"] = _cycle_status(results)
    return results


def _workbook_is_valid(path: Path, *, work_date: str) -> bool:
    workbook_to_standard(path, work_date=work_date)
    return True


def _cycle_status(results: Mapping[str, Any]) -> str:
    statuses = [
        value.get("status")
        for key, value in results.items()
        if key in {"final", "reminder"} and isinstance(value, Mapping)
    ]
    if any(status in {"FAILED", "INTERRUPTED"} for status in statuses):
        return "FAILED"
    if "WAITING_OFFICIAL_REPORT" in statuses:
        return "WAITING_OFFICIAL_REPORT"
    return "COMPLETED"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the R6 automatic attendance closure cycle.")
    parser.add_argument("--run-slot", choices=("morning", "evening"), required=True)
    parser.add_argument("--trigger-source", choices=("automation", "manual"), default="manual")
    parser.add_argument("--automation-id", choices=("kmfa", "kmfa-3"))
    parser.add_argument("--resume-final-only", action="store_true")
    parser.add_argument("--allow-dws-commands", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_dws_commands:
        print(json.dumps({"status": "DWS_AUTH_REQUIRED"}, ensure_ascii=False))
        return 2
    expected_id = "kmfa" if args.run_slot == "morning" else "kmfa-3"
    if args.trigger_source == "automation" and args.automation_id != expected_id:
        print(json.dumps({"status": "AUTOMATION_ID_MISMATCH"}, ensure_ascii=False))
        return 2
    PRIVATE_R6_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = PRIVATE_R6_ROOT / "cycle.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"status": "ALREADY_RUNNING"}, ensure_ascii=False))
            return 0
        result = run_automatic_cycle(
            run_slot=args.run_slot,
            trigger_source=args.trigger_source,
            resume_final_only=args.resume_final_only,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
