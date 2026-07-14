#!/usr/bin/env python3
"""R6 private state machine for idempotent attendance automation closure."""

from __future__ import annotations

import json
import os
import csv
import fcntl
import hashlib
import re
import shutil
import subprocess
import tempfile
import tomllib
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT, TIMEZONE
from KMFA.tools.dingtalk_attendance.collection_integrity import (
    realtime_reminder_integrity_failure_reason,
)
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
REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATHS = {
    "morning": REPO_ROOT / "KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md",
    "evening": REPO_ROOT / "KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md",
}
PROMPT_RELATIVE_PATHS = {
    "morning": Path("KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md"),
    "evening": Path("KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md"),
}
ATTENDANCE_RUNTIME_STATIC_PATHS = (
    Path("KMFA/kmfa-dingtalk-attendance-skill/规则清单.md"),
    PROMPT_RELATIVE_PATHS["morning"],
    PROMPT_RELATIVE_PATHS["evening"],
    Path("KMFA/metadata/dingtalk_attendance/attendance_database_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/codex_automation/morning_1035.prompt.md"),
    Path("KMFA/metadata/dingtalk_attendance/codex_automation/evening_2000.prompt.md"),
    Path("KMFA/metadata/dingtalk_attendance/notification_channel_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/notification_policy.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/notification_targets_manifest.json"),
    Path("KMFA/metadata/dingtalk_attendance/onedrive_storage_manifest.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/report_policy.yaml"),
    Path("KMFA/metadata/dingtalk_attendance/retention_policy.yaml"),
)
ATTENDANCE_RUNTIME_SCOPE_PATHS = (
    Path("KMFA/tools/dingtalk_attendance"),
    *ATTENDANCE_RUNTIME_STATIC_PATHS,
)
AUTOMATION_IDS = {"morning": "kmfa", "evening": "kmfa-3"}
REPORT_NAMES = tuple(OFFICIAL_COLUMNS[index] for index in [*range(8, 37), *range(45, 49)])
LEAVE_NAMES = ("事假", "病假", "年假", "调休", "婚假", "产假", "陪产假", "路途假")


class OfficialExportAmbiguousError(RuntimeError):
    pass


class OfficialExportInvalidError(RuntimeError):
    pass


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.rstrip("\n").encode("utf-8")).hexdigest()


def _default_attendance_runtime_paths(repo_root: Path) -> tuple[Path, ...]:
    tool_root = repo_root / "KMFA/tools/dingtalk_attendance"
    tool_paths = sorted(
        path.relative_to(repo_root)
        for path in tool_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return tuple(sorted({*tool_paths, *ATTENDANCE_RUNTIME_STATIC_PATHS}, key=lambda path: path.as_posix()))


def attendance_runtime_fingerprint(
    *,
    repo_root: Path = REPO_ROOT,
    live_prompts: Mapping[str, str],
    relative_paths: tuple[str | Path, ...] | None = None,
) -> str:
    """Hash only attendance runtime code, rules/config, and active prompts."""

    selected = (
        tuple(Path(path) for path in relative_paths)
        if relative_paths is not None
        else _default_attendance_runtime_paths(repo_root)
    )
    digest = hashlib.sha256(b"kmfa-attendance-runtime-fingerprint-v1\0")
    for relative in sorted(selected, key=lambda path: path.as_posix()):
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"attendance runtime path must be repo-relative: {relative}")
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"attendance runtime input is missing: {relative.as_posix()}")
        digest.update(b"repo-file\0")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    for slot in ("morning", "evening"):
        if slot not in live_prompts:
            raise ValueError(f"live prompt is missing for {slot}")
        digest.update(b"live-prompt\0")
        digest.update(slot.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(live_prompts[slot]).rstrip("\n").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def current_runtime_identity(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    tracked_clean = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--"], cwd=repo_root, check=False
    ).returncode == 0
    identity: dict[str, Any] = {
        "git_commit": commit,
        "tracked_tree_state": "CLEAN" if tracked_clean else "DIRTY",
    }
    mirrors_match = True
    live_prompts: dict[str, str] = {}
    for slot, automation_id in AUTOMATION_IDS.items():
        repo_prompt = (repo_root / PROMPT_RELATIVE_PATHS[slot]).read_text(encoding="utf-8").rstrip("\n")
        config_path = Path.home() / ".codex" / "automations" / automation_id / "automation.toml"
        live_prompt = repo_prompt
        try:
            live_prompt = str(tomllib.loads(config_path.read_text(encoding="utf-8"))["prompt"]).rstrip("\n")
        except (OSError, KeyError, tomllib.TOMLDecodeError):
            mirrors_match = False
        mirrors_match = mirrors_match and live_prompt == repo_prompt
        live_prompts[slot] = live_prompt
        identity[f"{slot}_prompt_sha256"] = _sha256_text(live_prompt)
    identity["prompt_mirrors_match"] = mirrors_match
    attendance_status = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *(path.as_posix() for path in ATTENDANCE_RUNTIME_SCOPE_PATHS)],
        cwd=repo_root,
        text=True,
    )
    identity["attendance_runtime_tree_state"] = "CLEAN" if not attendance_status.strip() else "DIRTY"
    identity["attendance_runtime_fingerprint"] = attendance_runtime_fingerprint(
        repo_root=repo_root,
        live_prompts=live_prompts,
    )
    return identity


def _message_text(payload: Mapping[str, Any]) -> str:
    return "".join(
        str(part.get("text") or part.get("input_text") or "")
        for part in (payload.get("content") or [])
        if isinstance(part, Mapping)
    )


def read_automation_task_evidence(
    path: Path,
    *,
    expected_automation_id: str,
    expected_prompt_sha256: str,
    expected_cwd: Path,
) -> dict[str, Any]:
    rejected = {
        "verified": False,
        "task_id": "",
        "thread_source": "unknown",
        "automation_id": expected_automation_id,
        "triggered_at": "",
        "prompt_sha256": "",
    }
    try:
        with path.open(encoding="utf-8") as handle:
            first = json.loads(next(handle))
            meta = first.get("payload") or {}
            evidence = {
                **rejected,
                "task_id": str(meta.get("id") or meta.get("session_id") or ""),
                "thread_source": str(meta.get("thread_source") or "unknown"),
                "triggered_at": str(meta.get("timestamp") or ""),
            }
            wrapped_prompt = ""
            wrapper_automation_id = ""
            marker = "Use $kmfa-dingtalk-attendance-skill."
            for line in handle:
                row = json.loads(line)
                payload = row.get("payload") or {}
                if row.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
                    text = _message_text(payload)
                    match = re.search(r"(?m)^Automation ID:\s*([^\s]+)\s*$", text)
                    if marker in text and match:
                        wrapper_automation_id = match.group(1)
                        wrapped_prompt = text[text.index(marker) :].rstrip("\n")
                        break
    except (OSError, StopIteration, json.JSONDecodeError, TypeError):
        return rejected
    evidence["automation_id"] = wrapper_automation_id or expected_automation_id
    evidence["prompt_sha256"] = _sha256_text(wrapped_prompt) if wrapped_prompt else ""
    evidence["verified"] = bool(
        first.get("type") == "session_meta"
        and evidence["task_id"]
        and evidence["thread_source"] == "automation"
        and evidence["automation_id"] == expected_automation_id
        and Path(str(meta.get("cwd") or "")) == expected_cwd
        and evidence["prompt_sha256"] == expected_prompt_sha256
        and evidence["triggered_at"]
    )
    return evidence


def discover_automation_task_evidence(
    *,
    automation_id: str,
    prompt_sha256: str,
    expected_cwd: Path = REPO_ROOT,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    current_thread_id = str(os.environ.get("CODEX_THREAD_ID") or "")
    if not current_thread_id:
        return {
            "verified": False,
            "task_id": "",
            "thread_source": "unverified",
            "automation_id": automation_id,
            "triggered_at": "",
            "prompt_sha256": prompt_sha256,
        }
    candidates: list[Path] = []
    for root in (codex_home / "sessions", codex_home / "archived_sessions"):
        if root.is_dir():
            candidates.extend(root.rglob("*.jsonl"))
    candidates.sort(key=lambda item: item.stat().st_mtime_ns, reverse=True)
    for path in candidates[:200]:
        evidence = read_automation_task_evidence(
            path,
            expected_automation_id=automation_id,
            expected_prompt_sha256=prompt_sha256,
            expected_cwd=expected_cwd,
        )
        if not evidence["verified"]:
            continue
        if evidence["task_id"] != current_thread_id:
            continue
        try:
            triggered = datetime.fromisoformat(evidence["triggered_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        age = current - triggered.astimezone(timezone.utc)
        if -timedelta(minutes=5) <= age <= timedelta(hours=6):
            return evidence
    return {
        "verified": False,
        "task_id": "",
        "thread_source": "unverified",
        "automation_id": automation_id,
        "triggered_at": "",
        "prompt_sha256": prompt_sha256,
    }


class R6Coordinator:
    """Persist only aggregate, private R6 state and recover from artifact-complete interruptions."""

    def __init__(self, root: Path, *, runtime_identity: Mapping[str, Any] | None = None) -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.status_path = root / "运行状态.md"
        self.root.mkdir(parents=True, exist_ok=True)
        self.state = self._load()
        self.runtime_identity = dict(runtime_identity or self.state.get("runtime_identity") or {})
        previous_identity = self.state.get("runtime_identity") or {}
        previous_fingerprint = str(previous_identity.get("attendance_runtime_fingerprint") or "")
        current_fingerprint = str(self.runtime_identity.get("attendance_runtime_fingerprint") or "")
        runtime_changed = bool(
            runtime_identity is not None
            and previous_identity
            and previous_fingerprint != current_fingerprint
        )
        self.state["schema_version"] = 4
        self.state["runtime_identity"] = self.runtime_identity
        self.state["validation_policy"] = "AFFECTED_COMPONENTS_ONLY_NO_GLOBAL_RESET"
        self.state.setdefault("runtime_transitions", [])
        if runtime_changed:
            self.state["runtime_transitions"].append(
                {
                    "previous_attendance_runtime_fingerprint": previous_fingerprint,
                    "current_attendance_runtime_fingerprint": current_fingerprint,
                    "revalidation_scope": "CHANGED_COMPONENTS_ONLY",
                    "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
            )
            self.state["runtime_transitions"] = self.state["runtime_transitions"][-50:]
        self._write()

    def ensure_slot(
        self,
        *,
        work_date: str,
        run_slot: str,
        trigger_source: str,
        task_evidence: Mapping[str, Any] | None = None,
        runner: Callable[[], Mapping[str, Any]],
        completed_probe: Callable[[], Mapping[str, Any] | None],
    ) -> dict[str, Any]:
        if run_slot not in {"morning", "evening"}:
            raise ValueError("run_slot must be morning or evening")
        day = self._day(work_date)
        existing = day["slots"].get(run_slot)
        if isinstance(existing, Mapping) and existing.get("status") in COMPLETE_STATUSES:
            recovered = completed_probe()
            if isinstance(recovered, Mapping):
                existing_record = dict(existing)
                existing_record.update(self._aggregate(recovered))
                day["slots"][run_slot] = existing_record
                self._write()
            return {
                "status": "IDEMPOTENT_SKIP",
                "work_date": work_date,
                "run_slot": run_slot,
                **self._aggregate(day["slots"][run_slot]),
            }

        current_evidence = self._normalize_task_evidence(task_evidence, trigger_source=trigger_source)
        recovered = completed_probe()
        if recovered is not None:
            original_evidence = self._recovery_evidence(existing, recovered, fallback=current_evidence)
            day["slots"][run_slot] = {
                "status": "RECOVERED_COMPLETE",
                "trigger_source": original_evidence["thread_source"],
                "task_evidence": original_evidence,
                "runtime_identity": self.runtime_identity,
                **self._aggregate(recovered),
            }
            self._event(work_date, run_slot, "RECOVERED_COMPLETE")
            self._write()
            return {"status": "RECOVERED_COMPLETE", "work_date": work_date, "run_slot": run_slot}

        day["slots"][run_slot] = {
            "status": "RUNNING",
            "trigger_source": current_evidence["thread_source"],
            "declared_trigger_source": trigger_source,
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
        }
        self._event(work_date, run_slot, "RUNNING")
        self._write()
        try:
            result = dict(runner())
        except Exception as exc:
            day["slots"][run_slot] = {
                "status": "INTERRUPTED",
                "trigger_source": current_evidence["thread_source"],
                "declared_trigger_source": trigger_source,
                "task_evidence": current_evidence,
                "runtime_identity": self.runtime_identity,
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
            "trigger_source": current_evidence["thread_source"],
            "declared_trigger_source": trigger_source,
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
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
        task_evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        day = self._day(work_date)
        existing = day.get("final")
        if isinstance(existing, Mapping) and existing.get("status") in {
            "OFFICIAL_FINAL_RECONCILIATION_PASS",
            "RECOVERED_COMPLETE",
        }:
            return {"status": "IDEMPOTENT_SKIP", "work_date": work_date}

        current_evidence = self._normalize_task_evidence(task_evidence, trigger_source=trigger_source)
        try:
            recovered = completed_probe()
        except Exception as exc:
            return self.record_final_failure(
                work_date=work_date,
                trigger_source=trigger_source,
                task_evidence=current_evidence,
                error_type=exc.__class__.__name__,
            )
        if recovered is not None:
            original_evidence = self._recovery_evidence(existing, recovered, fallback=current_evidence)
            result = {
                "status": "RECOVERED_COMPLETE",
                "trigger_source": original_evidence["thread_source"],
                "task_evidence": original_evidence,
                "runtime_identity": self.runtime_identity,
                "monthly_written": True,
                **self._aggregate(recovered),
            }
            day["final"] = result
            self._event(work_date, "final", "RECOVERED_COMPLETE")
            self._write()
            return {"status": "RECOVERED_COMPLETE", "work_date": work_date}

        try:
            export_path = export_finder()
        except Exception as exc:
            day["official_export"] = {"status": "FAILED", "error_type": exc.__class__.__name__}
            return self.record_final_failure(
                work_date=work_date,
                trigger_source=trigger_source,
                task_evidence=current_evidence,
                error_type=exc.__class__.__name__,
            )
        if export_path is None:
            day["official_export"] = {"status": "WAITING_OFFICIAL_REPORT"}
            day["final"] = {
                "status": "WAITING_OFFICIAL_REPORT",
                "trigger_source": current_evidence["thread_source"],
                "task_evidence": current_evidence,
                "runtime_identity": self.runtime_identity,
            }
            self._event(work_date, "final", "WAITING_OFFICIAL_REPORT")
            self._write()
            return {
                "status": "WAITING_OFFICIAL_REPORT",
                "work_date": work_date,
                "next_action": "AUTOMATIC_BROWSER_EXPORT_OR_NEXT_NATURAL_TRIGGER",
            }

        day["official_export"] = {"status": "FOUND", "file_name": export_path.name}
        day["final"] = {
            "status": "BUILDING_CERTIFICATE",
            "trigger_source": current_evidence["thread_source"],
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
        }
        self._write()
        try:
            certificate_path = certificate_builder(export_path)
            day["final"] = {
                "status": "RUNNING_FINAL",
                "trigger_source": current_evidence["thread_source"],
                "task_evidence": current_evidence,
                "runtime_identity": self.runtime_identity,
            }
            self._write()
            result = dict(final_runner(certificate_path))
        except Exception as exc:
            return self.record_final_failure(
                work_date=work_date,
                trigger_source=trigger_source,
                task_evidence=current_evidence,
                error_type=exc.__class__.__name__,
            )

        valid = result.get("status") == "OFFICIAL_FINAL_RECONCILIATION_PASS"
        final_status = "OFFICIAL_FINAL_RECONCILIATION_PASS" if valid else "FAILED"
        day["final"] = {
            "status": final_status,
            "trigger_source": current_evidence["thread_source"],
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
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
        task_evidence: Mapping[str, Any] | None = None,
        result: Mapping[str, Any],
    ) -> None:
        current_evidence = self._normalize_task_evidence(task_evidence, trigger_source=trigger_source)
        self._day(work_date)["final"] = {
            "status": "OFFICIAL_FINAL_RECONCILIATION_PASS",
            "trigger_source": current_evidence["thread_source"],
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
            **self._aggregate(result),
        }
        self._event(work_date, "final", "OFFICIAL_FINAL_RECONCILIATION_PASS")
        self._write()

    def record_final_failure(
        self,
        *,
        work_date: str,
        trigger_source: str,
        task_evidence: Mapping[str, Any] | None,
        error_type: str,
    ) -> dict[str, Any]:
        current_evidence = self._normalize_task_evidence(task_evidence, trigger_source=trigger_source)
        self._day(work_date)["final"] = {
            "status": "FAILED",
            "trigger_source": current_evidence["thread_source"],
            "task_evidence": current_evidence,
            "runtime_identity": self.runtime_identity,
            "error_type": error_type,
        }
        self._event(work_date, "final", "FAILED")
        self._write()
        return {"status": "FAILED", "work_date": work_date, "error_type": error_type}

    def acceptance_summary(self) -> dict[str, Any]:
        natural_success_dates: dict[str, list[str]] = {"morning": [], "evening": []}
        final_pass_dates: list[str] = []
        final_waiting_dates: list[str] = []
        final_failed_dates: list[str] = []
        delivery_status_counts: dict[str, int] = {}
        for work_date, day in sorted(self.state["work_dates"].items()):
            slots = day.get("slots", {})
            final = day.get("final", {})
            if isinstance(slots, Mapping):
                for slot in ("morning", "evening"):
                    record = slots.get(slot)
                    if not isinstance(record, Mapping):
                        continue
                    if record.get("status") in COMPLETE_STATUSES and self._is_natural_record(
                        record, run_slot=slot
                    ):
                        natural_success_dates[slot].append(work_date)
                        notification_status = str(record.get("notification_status") or "UNKNOWN")
                        delivery_status_counts[notification_status] = (
                            delivery_status_counts.get(notification_status, 0) + 1
                        )
            if not isinstance(final, Mapping):
                continue
            final_status = str(final.get("status") or "")
            if final_status == "WAITING_OFFICIAL_REPORT":
                final_waiting_dates.append(work_date)
            elif final_status in {"FAILED", "INTERRUPTED", "OFFICIAL_FINAL_RECONCILIATION_BLOCKED"}:
                final_failed_dates.append(work_date)
            elif (
                final_status in {"OFFICIAL_FINAL_RECONCILIATION_PASS", "RECOVERED_COMPLETE"}
                and self._is_natural_record(final, run_slot="morning")
                and int(final.get("differing_required_cells", 0)) == 0
                and final.get("monthly_written") is True
                and final.get("actual_workday") is True
            ):
                final_pass_dates.append(work_date)
                notification_status = str(final.get("notification_status") or "UNKNOWN")
                delivery_status_counts[notification_status] = delivery_status_counts.get(notification_status, 0) + 1
        return {
            "morning": {
                "natural_success_count": len(natural_success_dates["morning"]),
                "natural_success_dates": natural_success_dates["morning"],
            },
            "evening": {
                "natural_success_count": len(natural_success_dates["evening"]),
                "natural_success_dates": natural_success_dates["evening"],
            },
            "final_reconciliation": {
                "pass_count": len(final_pass_dates),
                "pass_dates": final_pass_dates,
                "waiting_count": len(final_waiting_dates),
                "waiting_dates": final_waiting_dates,
                "failed_count": len(final_failed_dates),
                "failed_dates": final_failed_dates,
            },
            "delivery": {
                "status_counts": dict(sorted(delivery_status_counts.items())),
                "owner_disabled_count": delivery_status_counts.get(DELIVERY_DISABLED_STATUS, 0),
                "sent_count": delivery_status_counts.get("SENT", 0),
                "failed_count": delivery_status_counts.get("FAILED", 0),
            },
            "runtime_revalidation_policy": "AFFECTED_COMPONENTS_ONLY_NO_GLOBAL_RESET",
        }

    def _day(self, work_date: str) -> dict[str, Any]:
        datetime.strptime(work_date, "%Y-%m-%d")
        return self.state["work_dates"].setdefault(work_date, {"slots": {}})

    def _load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 4, "runtime_identity": {}, "work_dates": {}, "events": []}
        if not isinstance(payload, dict) or not isinstance(payload.get("work_dates"), dict):
            return {"schema_version": 4, "runtime_identity": {}, "work_dates": {}, "events": []}
        payload.setdefault("events", [])
        payload.setdefault("runtime_identity", {})
        return payload

    def _normalize_task_evidence(
        self,
        evidence: Mapping[str, Any] | None,
        *,
        trigger_source: str,
    ) -> dict[str, Any]:
        source = dict(evidence or {})
        return {
            "verified": source.get("verified") is True,
            "task_id": str(source.get("task_id") or ""),
            "thread_source": str(source.get("thread_source") or trigger_source or "unknown"),
            "automation_id": str(source.get("automation_id") or ""),
            "triggered_at": str(source.get("triggered_at") or ""),
            "prompt_sha256": str(source.get("prompt_sha256") or ""),
        }

    def _recovery_evidence(
        self,
        existing: Any,
        recovered: Mapping[str, Any],
        *,
        fallback: Mapping[str, Any],
    ) -> dict[str, Any]:
        if isinstance(existing, Mapping) and isinstance(existing.get("task_evidence"), Mapping):
            return self._normalize_task_evidence(
                existing["task_evidence"], trigger_source=str(existing.get("trigger_source") or "unknown")
            )
        if isinstance(recovered.get("task_evidence"), Mapping):
            return self._normalize_task_evidence(
                recovered["task_evidence"], trigger_source=str(recovered.get("trigger_source") or "unknown")
            )
        if recovered.get("trigger_source"):
            return self._normalize_task_evidence(
                {"thread_source": recovered["trigger_source"], "verified": False},
                trigger_source=str(recovered["trigger_source"]),
            )
        return self._normalize_task_evidence(
            {"thread_source": "unknown", "verified": False},
            trigger_source="unknown",
        )

    def _is_natural_record(self, record: Mapping[str, Any], *, run_slot: str) -> bool:
        evidence = record.get("task_evidence") or {}
        record_identity = record.get("runtime_identity") or {}
        record_fingerprint = str(record_identity.get("attendance_runtime_fingerprint") or "")
        record_prompt_sha256 = str(record_identity.get(f"{run_slot}_prompt_sha256") or "")
        return bool(
            record_fingerprint
            and isinstance(record_identity, Mapping)
            and record_identity.get("attendance_runtime_tree_state") == "CLEAN"
            and record_identity.get("prompt_mirrors_match") is True
            and isinstance(evidence, Mapping)
            and evidence.get("verified") is True
            and evidence.get("thread_source") == "automation"
            and evidence.get("automation_id") == AUTOMATION_IDS[run_slot]
            and record_prompt_sha256
            and evidence.get("prompt_sha256") == record_prompt_sha256
            and evidence.get("task_id")
            and evidence.get("triggered_at")
        )

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
            "integrity_error",
            "error_code",
            "realtime_integrity_status",
            "realtime_expected_count",
            "realtime_coverage_count",
            "query_failure_count",
            "parse_failure_count",
            "command_failure_count",
            "archive_generated",
        )
        aggregate = {key: result[key] for key in allowed if key in result}
        coverage = result.get("coverage_stats")
        if isinstance(coverage, Mapping):
            allowed_coverage = (
                "expected_people",
                "queried_people",
                "successful_people",
                "missing_people",
                "failed_batch_index",
                "failed_batch_expected",
                "failed_batch_actual",
                "query_failure_count",
                "parse_failure_count",
            )
            aggregate["coverage_stats"] = {
                key: coverage[key]
                for key in allowed_coverage
                if key in coverage and (coverage[key] is None or isinstance(coverage[key], int))
            }
        return aggregate

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
            f"- 当前 Git commit：{self.runtime_identity.get('git_commit') or 'UNKNOWN'}",
            f"- Attendance runtime fingerprint：{self.runtime_identity.get('attendance_runtime_fingerprint') or 'UNKNOWN'}",
            "- 本机计划：晨间 10:45；晚间 20:00（仅记录实际计划，未修改 scheduler）",
            "- 晨间自然成功：{count}（{dates}）".format(
                count=summary["morning"]["natural_success_count"],
                dates=", ".join(summary["morning"]["natural_success_dates"]) or "无",
            ),
            "- 晚间自然成功：{count}（{dates}）".format(
                count=summary["evening"]["natural_success_count"],
                dates=", ".join(summary["evening"]["natural_success_dates"]) or "无",
            ),
            "- 事后核验通过：{count}（{dates}）".format(
                count=summary["final_reconciliation"]["pass_count"],
                dates=", ".join(summary["final_reconciliation"]["pass_dates"]) or "无",
            ),
            "- 事后核验等待：{dates}".format(
                dates=", ".join(summary["final_reconciliation"]["waiting_dates"]) or "无",
            ),
            "- 发送状态：owner disabled {disabled}；sent {sent}；failed {failed}".format(
                disabled=summary["delivery"]["owner_disabled_count"],
                sent=summary["delivery"]["sent_count"],
                failed=summary["delivery"]["failed_count"],
            ),
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
        detail_lines: list[str] = []
        for work_date, day in sorted(self.state["work_dates"].items()):
            for run_slot, slot in sorted((day.get("slots") or {}).items()):
                if not isinstance(slot, Mapping) or not slot.get("error_code"):
                    continue
                coverage = slot.get("coverage_stats") or {}
                detail_lines.append(
                    "- {date} {slot_name}：{code}；{detail}；期望人数 {expected}，已查询 {queried}，"
                    "成功 {successful}，缺失 {missing}，查询失败 {query_failed}，解析失败 {parse_failed}".format(
                        date=work_date,
                        slot_name=run_slot,
                        code=slot.get("error_code"),
                        detail=slot.get("integrity_error") or "无错误详情",
                        expected=coverage.get("expected_people", "UNKNOWN"),
                        queried=coverage.get("queried_people", "UNKNOWN"),
                        successful=coverage.get("successful_people", "UNKNOWN"),
                        missing=coverage.get("missing_people", "UNKNOWN"),
                        query_failed=coverage.get("query_failure_count", "UNKNOWN"),
                        parse_failed=coverage.get("parse_failure_count", "UNKNOWN"),
                    )
                )
        if detail_lines:
            lines.extend(["", "## 实时提醒完整性错误", "", *detail_lines])
        status_temp = self.status_path.with_suffix(".md.tmp")
        status_temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(status_temp, 0o600)
        os.replace(status_temp, self.status_path)


def merge_official_header_rows(primary: list[str], secondary: list[str]) -> list[str]:
    if len(primary) != len(OFFICIAL_COLUMNS) or len(secondary) != len(OFFICIAL_COLUMNS):
        raise OfficialExportInvalidError("official merged header must contain exactly 49 columns")
    resolved = [
        str(secondary[index]).strip() or str(primary[index]).strip()
        for index in range(len(OFFICIAL_COLUMNS))
    ]
    if tuple(resolved) != OFFICIAL_COLUMNS:
        mismatches = [
            OFFICIAL_COLUMNS[index]
            for index, value in enumerate(resolved)
            if value != OFFICIAL_COLUMNS[index]
        ]
        raise OfficialExportInvalidError(
            "official merged header does not match required fields: " + ", ".join(mismatches)
        )
    return resolved


def parse_official_csv(path: Path, *, work_date: str) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [list(row) for row in csv.reader(handle)]
    if len(rows) < 5 or max((len(row) for row in rows), default=0) != 49:
        raise OfficialExportInvalidError("official workbook must contain the complete 49-column report")
    merge_official_header_rows(rows[2], rows[3])
    normalized: list[list[Any]] = []
    for row in rows:
        padded = [*row, *([""] * (49 - len(row)))]
        normalized.append([None if value == "" else value for value in padded[:49]])
    if work_date not in str(normalized[0][0] or ""):
        raise OfficialExportInvalidError("official workbook title does not match target work date")
    user_ids = [str(row[5]) for row in normalized[4:] if row[5] not in (None, "")]
    if not user_ids or len(set(user_ids)) != len(user_ids):
        raise OfficialExportInvalidError("official workbook must contain a non-empty unique UserId set")
    return {
        "input_name": path.name,
        "sheet_name": "每日统计",
        "address": f"A1:AW{len(normalized)}",
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
    users = [
        str(row[5])
        for row in rows[4:]
        if isinstance(row, list) and len(row) == 49 and row[5] not in (None, "")
    ]
    if not users or len(set(users)) != len(users):
        raise OfficialExportInvalidError("official standard must contain a non-empty unique user set")

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
            and realtime_reminder_integrity_failure_reason(stats, run_type=run_slot) is None
            and receipt.get("notification_status") == DELIVERY_DISABLED_STATUS
        ):
            return {
                "notification_status": DELIVERY_DISABLED_STATUS,
                "member_count": int(stats.get("member_count") or 0),
                "run_id": run_id,
                "realtime_integrity_status": stats.get("realtime_reminder_integrity_status"),
                "realtime_expected_count": int(stats.get("realtime_reminder_expected_count") or 0),
                "realtime_coverage_count": int(stats.get("realtime_reminder_coverage_count") or 0),
                "query_failure_count": int(stats.get("realtime_reminder_query_failure_count") or 0),
                "parse_failure_count": int(stats.get("realtime_reminder_parse_failure_count") or 0),
                "command_failure_count": int(stats.get("command_failure_count") or 0),
                "archive_generated": True,
            }
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
    archive_status = result.get("onedrive_archive_status") or {}
    return {
        "status": result.get("status"),
        "notification_status": result.get("notification_status"),
        "member_count": int(stats.get("member_count") or 0),
        "run_id": str((result.get("run_plan") or {}).get("run_id") or ""),
        "realtime_integrity_status": stats.get("realtime_reminder_integrity_status"),
        "realtime_expected_count": int(stats.get("realtime_reminder_expected_count") or 0),
        "realtime_coverage_count": int(stats.get("realtime_reminder_coverage_count") or 0),
        "query_failure_count": int(stats.get("realtime_reminder_query_failure_count") or 0),
        "parse_failure_count": int(stats.get("realtime_reminder_parse_failure_count") or 0),
        "command_failure_count": int(stats.get("command_failure_count") or 0),
        "archive_generated": bool(
            isinstance(archive_status, Mapping)
            and archive_status.get("status") == "WRITTEN"
            and archive_status.get("archive_manifest")
        ),
        **{
            key: result[key]
            for key in ("integrity_error", "error_code", "coverage_stats")
            if key in result
        },
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
    task_evidence: Mapping[str, Any] | None = None,
    runtime_identity: Mapping[str, Any] | None = None,
    resume_final_only: bool = False,
    private_root: Path = PRIVATE_R6_ROOT,
    archive_root: Path = Path(ONEDRIVE_ROOT),
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(ZoneInfo(TIMEZONE))
    today = current.date().isoformat()
    identity = dict(runtime_identity or current_runtime_identity())
    evidence = dict(
        task_evidence
        or discover_automation_task_evidence(
            automation_id=AUTOMATION_IDS[run_slot],
            prompt_sha256=str(identity[f"{run_slot}_prompt_sha256"]),
            now=current,
        )
    )
    coordinator = R6Coordinator(private_root, runtime_identity=identity)
    results: dict[str, Any] = {
        "run_slot": run_slot,
        "declared_trigger_source": trigger_source,
        "verified_trigger_source": evidence.get("thread_source", "unverified"),
    }
    if not resume_final_only:
        results["reminder"] = coordinator.ensure_slot(
            work_date=today,
            run_slot=run_slot,
            trigger_source=trigger_source,
            task_evidence=evidence,
            runner=lambda: _slot_runner(run_slot=run_slot),
            completed_probe=lambda: _completed_reminder_probe(
                work_date=today,
                run_slot=run_slot,
                archive_root=archive_root,
            ),
        )
    if run_slot == "morning":
        try:
            pending = find_latest_pending_work_date(onedrive_root=archive_root, timezone=TIMEZONE, now=current)
        except Exception as exc:
            pending = None
            results["final"] = coordinator.record_final_failure(
                work_date=today,
                trigger_source=trigger_source,
                task_evidence=evidence,
                error_type=exc.__class__.__name__,
            )
        if pending:
            search_roots = [Path.home() / "Downloads", private_root / "export_inbox"]
            results["final"] = coordinator.advance_final(
                work_date=pending,
                trigger_source=trigger_source,
                task_evidence=evidence,
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
        elif "final" not in results:
            results["final"] = {"status": "NO_PENDING_FINAL_RECONCILIATION"}
    results["acceptance"] = coordinator.acceptance_summary()
    results["status"] = _cycle_status(results)
    results["result_message"] = _cycle_result_message(results)
    final_result = results.get("final")
    if isinstance(final_result, Mapping) and final_result.get("status") == "WAITING_OFFICIAL_REPORT":
        results["follow_up"] = {
            "kind": "OFFICIAL_FINAL_RECONCILIATION",
            "status": "WAITING_OFFICIAL_REPORT",
            "work_date": final_result.get("work_date"),
            "blocks_reminder": False,
        }
    return results


def _workbook_is_valid(path: Path, *, work_date: str) -> bool:
    workbook_to_standard(path, work_date=work_date)
    return True


def _cycle_status(results: Mapping[str, Any]) -> str:
    reminder = results.get("reminder") if isinstance(results.get("reminder"), Mapping) else None
    final = results.get("final") if isinstance(results.get("final"), Mapping) else None
    reminder_status = reminder.get("status") if reminder else None
    final_status = final.get("status") if final else None
    if reminder_status in {"FAILED", "INTERRUPTED"}:
        return "FAILED"
    reminder_completed = reminder_status in COMPLETE_STATUSES or reminder_status == "IDEMPOTENT_SKIP"
    if reminder_completed and final_status in {"FAILED", "INTERRUPTED"}:
        return "REMINDER_COMPLETED_FINAL_FAILED"
    if reminder_completed and final_status == "WAITING_OFFICIAL_REPORT":
        return "COMPLETED"
    if reminder is None and final_status in {"FAILED", "INTERRUPTED"}:
        return "FINAL_FAILED"
    if reminder is None and final_status == "WAITING_OFFICIAL_REPORT":
        return "FINAL_WAITING"
    return "COMPLETED"


def _cycle_result_message(results: Mapping[str, Any]) -> str:
    reminder = results.get("reminder") if isinstance(results.get("reminder"), Mapping) else None
    final = results.get("final") if isinstance(results.get("final"), Mapping) else None
    reminder_status = reminder.get("status") if reminder else None
    final_status = final.get("status") if final else None
    reminder_completed = reminder_status in COMPLETE_STATUSES or reminder_status == "IDEMPOTENT_SKIP"
    if reminder_completed and final_status == "WAITING_OFFICIAL_REPORT":
        return "提醒成功，事后核验等待"
    if reminder_completed and final_status in {"FAILED", "INTERRUPTED"}:
        return "提醒成功，事后核验失败"
    if reminder_status in {"FAILED", "INTERRUPTED"}:
        return "提醒失败"
    if reminder_completed:
        return "提醒成功"
    if final_status == "WAITING_OFFICIAL_REPORT":
        return "事后核验等待"
    return "运行完成"


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
