#!/usr/bin/env python3
"""Run PFI v0.2.5 Stage 12.2 target-Mac acceptance without Finder."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence
from urllib.error import URLError
from urllib.request import urlopen
import uuid
import zipfile

from jsonschema import Draft202012Validator


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
SRC_ROOT = PFI_ROOT / "src"
WEB_TEST_ROOT = PFI_ROOT / "web/tests/v025"
for candidate in (SRC_ROOT, WEB_TEST_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from pfi_v02.stage_v021_runtime_api import (  # noqa: E402
    build_v025_release_asset_identity,
    load_v025_release_manifest,
)
from immutable_real_sources import load_locked_source_objects  # noqa: E402
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


VERSION = "v0.2.5"
STAGE = 12
PHASE = "12.2"
PHASE_ID = "V025-S12-P12.2"
TASK_IDS = ("S12-P2-T1", "S12-P2-T2", "S12-P2-T3", "S12-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S12-P122-TARGET-MAC-CLI-UAT"
DEFAULT_OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_2"
TASK_PACK = (
    Path.home()
    / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
)
SOURCE_APP = PFI_ROOT / "macos/PFI.app"
CANONICAL_APP = Path("/Applications/PFI.app")
LAUNCHER_SOURCE = PFI_ROOT / "macos/PFI_launcher.c"
TARGET_BROWSER = PFI_ROOT / "web/tests/v025/stage12_target_mac_uat.mjs"
NODE = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
)
PLAYWRIGHT_MODULE_DIR = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BACKUP_ROOT = Path.home() / ".pfi/release_backups"
INSTALL_RECEIPT = BACKUP_ROOT / "pfi_v025_stage12_phase122_install_receipt.json"
USER_NO_FINDER_INSTRUCTION_SHA256 = hashlib.sha256(
    "不要再进行任何的finder操作，纯粹浪费时间！".encode("utf-8")
).hexdigest()


class TargetMacAcceptanceError(RuntimeError):
    """Raised when a Phase 12.2 fail-closed gate is not satisfied."""


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TargetMacAcceptanceError(f"expected JSON object: {path.name}")
    return payload


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git_text(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _run(
    command: Sequence[str | Path],
    *,
    check: bool = True,
    timeout: float = 180,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [str(item) for item in command],
        cwd=REPO_ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and completed.returncode != 0:
        summary = (completed.stderr or completed.stdout or "command failed").strip()
        summary = re.sub(r"/(?:Users|private|tmp)/\S+", "[LOCAL_PATH_REDACTED]", summary)
        raise TargetMacAcceptanceError(summary[:800])
    return completed


def _bundle_tree_hash(root: Path) -> str:
    records: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        current = path.lstat()
        mode = stat.S_IMODE(current.st_mode)
        if path.is_symlink():
            digest = _sha_bytes(os.readlink(path).encode("utf-8"))
            kind = "symlink"
        elif path.is_file():
            digest = _sha_file(path)
            kind = "file"
        elif path.is_dir():
            digest = "directory"
            kind = "directory"
        else:
            raise TargetMacAcceptanceError("unsupported App bundle entry")
        records.append(f"{kind}|{mode:o}|{relative}|{digest}")
    return _sha_bytes(("\n".join(records) + "\n").encode("utf-8"))


def _app_identity(bundle: Path) -> dict[str, object]:
    if not bundle.is_dir() or bundle.is_symlink():
        return {"kind": "missing"}
    plist_path = bundle / "Contents/Info.plist"
    executable = bundle / "Contents/MacOS/PFI"
    marker = bundle / "Contents/Resources/PFI_PROJECT_ROOT"
    if not plist_path.is_file() or not executable.is_file():
        raise TargetMacAcceptanceError("App bundle identity files are missing")
    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)
    codesign = _run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", bundle],
        check=False,
    )
    marker_value = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    return {
        "kind": "app_bundle",
        "short_version": str(plist.get("CFBundleShortVersionString", "")),
        "build_version": str(plist.get("CFBundleVersion", "")),
        "bundle_identifier": str(plist.get("CFBundleIdentifier", "")),
        "executable_sha256": _sha_file(executable),
        "bundle_tree_sha256": _bundle_tree_hash(bundle),
        "codesign_valid": codesign.returncode == 0,
        "project_binding_present": bool(marker_value),
        "project_binding_matches": marker_value == str(PFI_ROOT),
        "project_binding_sha256": (
            _sha_bytes(marker_value.encode("utf-8")) if marker_value else None
        ),
    }


def _prepare_private_backup_root() -> None:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(BACKUP_ROOT, 0o700)
    if BACKUP_ROOT.is_symlink() or not BACKUP_ROOT.is_dir():
        raise TargetMacAcceptanceError("private App backup root is invalid")


def _write_private_receipt(payload: dict[str, object]) -> None:
    _prepare_private_backup_root()
    temporary = INSTALL_RECEIPT.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, INSTALL_RECEIPT)


def _build_staged_app(stage_root: Path) -> tuple[Path, str]:
    staged_app = stage_root / "PFI.app"
    launcher = stage_root / "PFI"
    _run(
        [
            "/usr/bin/clang",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Wl,-no_uuid",
            "-o",
            launcher,
            LAUNCHER_SOURCE,
        ]
    )
    _run(
        [
            "/usr/bin/ditto",
            "--norsrc",
            "--noextattr",
            "--noacl",
            SOURCE_APP,
            staged_app,
        ]
    )
    installed_executable = staged_app / "Contents/MacOS/PFI"
    shutil.copy2(launcher, installed_executable)
    os.chmod(installed_executable, 0o755)
    resources = staged_app / "Contents/Resources"
    resources.mkdir(parents=True, exist_ok=True)
    marker = resources / "PFI_PROJECT_ROOT"
    marker.write_text(str(PFI_ROOT) + "\n", encoding="utf-8")
    os.chmod(marker, 0o644)
    _run(["/usr/bin/xattr", "-cr", staged_app], check=False)
    _run(["/usr/bin/codesign", "--force", "--deep", "--sign", "-", staged_app])
    _run(["/usr/bin/codesign", "--verify", "--deep", "--strict", staged_app])
    return staged_app, _sha_file(installed_executable)


def install_canonical_app(observed_at: str) -> dict[str, object]:
    manifest = load_v025_release_manifest(
        manifest_path=PFI_ROOT / "config/release_manifest.json"
    )
    before = _app_identity(CANONICAL_APP)
    stage_root = Path(
        tempfile.mkdtemp(prefix=".pfi-v025-s12p2-stage-", dir=CANONICAL_APP.parent)
    )
    rollback_app = CANONICAL_APP.parent / (
        ".PFI.app.s12p2.rollback-" + uuid.uuid4().hex
    )
    backup_archive: Path | None = None
    install_performed = False
    restored_after_failure = False
    try:
        staged_app, expected_executable_sha = _build_staged_app(stage_root)
        staged_identity = _app_identity(staged_app)
        expected = (
            staged_identity["short_version"] == manifest["app_short_version"]
            and staged_identity["build_version"] == manifest["app_build_version"]
            and staged_identity["project_binding_matches"] is True
            and staged_identity["codesign_valid"] is True
        )
        if not expected:
            raise TargetMacAcceptanceError("staged App does not match release identity")
        current_reusable = (
            before.get("kind") == "app_bundle"
            and before.get("short_version") == manifest["app_short_version"]
            and before.get("build_version") == manifest["app_build_version"]
            and before.get("project_binding_matches") is True
            and before.get("codesign_valid") is True
            and before.get("executable_sha256") == expected_executable_sha
        )
        if not current_reusable:
            _prepare_private_backup_root()
            if before.get("kind") == "app_bundle":
                old_hash = str(before["bundle_tree_sha256"]).split(":", 1)[-1][:16]
                backup_archive = BACKUP_ROOT / f"PFI.app.pre-v025-{old_hash}.zip"
                if not backup_archive.exists():
                    _run(
                        [
                            "/usr/bin/ditto",
                            "-c",
                            "-k",
                            "--sequesterRsrc",
                            "--keepParent",
                            CANONICAL_APP,
                            backup_archive,
                        ]
                    )
                    os.chmod(backup_archive, 0o600)
            try:
                if CANONICAL_APP.exists():
                    os.replace(CANONICAL_APP, rollback_app)
                os.replace(staged_app, CANONICAL_APP)
                after_candidate = _app_identity(CANONICAL_APP)
                if (
                    after_candidate.get("short_version")
                    != manifest["app_short_version"]
                    or after_candidate.get("build_version")
                    != manifest["app_build_version"]
                    or after_candidate.get("project_binding_matches") is not True
                    or after_candidate.get("codesign_valid") is not True
                    or after_candidate.get("executable_sha256")
                    != expected_executable_sha
                ):
                    raise TargetMacAcceptanceError(
                        "installed canonical App failed post-replace verification"
                    )
                install_performed = True
            except Exception:
                if CANONICAL_APP.exists():
                    shutil.rmtree(CANONICAL_APP)
                if rollback_app.exists():
                    os.replace(rollback_app, CANONICAL_APP)
                    restored_after_failure = True
                raise
            if rollback_app.exists():
                shutil.rmtree(rollback_app)
            after = _app_identity(CANONICAL_APP)
            _write_private_receipt(
                {
                    "schema": "PFIV025Stage12Phase122PrivateInstallReceiptV1",
                    "installed_at": observed_at,
                    "canonical_bundle_sha256": after["bundle_tree_sha256"],
                    "canonical_executable_sha256": after["executable_sha256"],
                    "version": manifest["version"],
                    "build_id": manifest["build_id"],
                    "rollback_archive_name": (
                        backup_archive.name if backup_archive is not None else None
                    ),
                    "rollback_archive_sha256": (
                        _sha_file(backup_archive)
                        if backup_archive is not None and backup_archive.is_file()
                        else None
                    ),
                }
            )
        else:
            after = before
        prior_receipt = _read_json(INSTALL_RECEIPT) if INSTALL_RECEIPT.is_file() else {}
        phase_install_proven = install_performed or (
            prior_receipt.get("canonical_bundle_sha256")
            == after.get("bundle_tree_sha256")
            and prior_receipt.get("build_id") == manifest["build_id"]
        )
        if not phase_install_proven:
            raise TargetMacAcceptanceError(
                "canonical App is current but this Phase has no install receipt"
            )
        return {
            "schema": "PFIV025Stage12Phase122CLIAppInstallV1",
            "status": "pass",
            "installation_mode": "cli_atomic_replace",
            "canonical_location": "applications_pfi_app",
            "before": before,
            "after": after,
            "install_performed_this_invocation": install_performed,
            "install_performed_in_phase": phase_install_proven,
            "rollback_archive_retained": bool(
                backup_archive and backup_archive.is_file()
            )
            or bool(prior_receipt.get("rollback_archive_name")),
            "rollback_archive_sha256": (
                _sha_file(backup_archive)
                if backup_archive is not None and backup_archive.is_file()
                else prior_receipt.get("rollback_archive_sha256")
            ),
            "restored_after_failure": restored_after_failure,
            "same_build_as_release_manifest": True,
            "finder_used": False,
            "launchservices_used": False,
            "open_command_used": False,
            "gui_file_operations_used": False,
            "user_no_finder_override_sha256": USER_NO_FINDER_INSTRUCTION_SHA256,
            "contains_private_values": False,
        }
    finally:
        if rollback_app.exists():
            raise TargetMacAcceptanceError(
                "rollback App remained after canonical installation"
            )
        if stage_root.exists():
            shutil.rmtree(stage_root)


def _entry_census() -> dict[str, object]:
    entries = {
        "applications": CANONICAL_APP,
        "desktop": Path.home() / "Desktop/PFI.app",
        "downloads": Path.home() / "Downloads/PFI.app",
    }
    rows: dict[str, object] = {}
    canonical_hash = str(_app_identity(CANONICAL_APP).get("bundle_tree_sha256", ""))
    mismatch_count = 0
    for label, entry in entries.items():
        if entry.is_symlink():
            target = entry.resolve(strict=False)
            row: dict[str, object] = {
                "kind": "symlink",
                "targets_canonical": target == CANONICAL_APP,
            }
            if target == CANONICAL_APP:
                row["short_version"] = _app_identity(CANONICAL_APP).get(
                    "short_version"
                )
        elif entry.is_dir():
            identity = _app_identity(entry)
            row = {
                "kind": "app_bundle",
                "short_version": identity.get("short_version"),
                "build_version": identity.get("build_version"),
                "same_bundle_as_canonical": (
                    identity.get("bundle_tree_sha256") == canonical_hash
                ),
            }
        else:
            row = {"kind": "missing"}
        if label != "applications" and row.get("kind") != "missing":
            same = row.get("targets_canonical") is True or row.get(
                "same_bundle_as_canonical"
            ) is True
            if not same:
                mismatch_count += 1
        rows[label] = row
    return {
        "schema": "PFIV025Stage12Phase122CLIEntryCensusV1",
        "status": "pass",
        "entries": rows,
        "noncanonical_copy_mismatch_count": mismatch_count,
        "noncanonical_copies_modified": False,
        "finder_used": False,
        "launchservices_used": False,
        "contains_private_values": False,
    }


def _select_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _health(port: int, *, timeout: float = 2.0) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=timeout) as response:
            return response.status == 200 and response.read().strip() == b"ok"
    except (OSError, URLError):
        return False


def _wait(predicate: Any, *, timeout: float, interval: float = 0.2) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def _marker_values(path: Path) -> dict[str, str]:
    if not path.is_file() or path.is_symlink():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value
    return values


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _process_group_members(pgid: int) -> list[tuple[int, str]]:
    completed = _run(["/bin/ps", "-axo", "pid=,pgid=,command="], check=True)
    rows: list[tuple[int, str]] = []
    for line in completed.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            continue
        if int(fields[1]) == pgid:
            rows.append((int(fields[0]), fields[2]))
    return rows


def _validate_owned_runtime(
    marker: dict[str, str], runtime_root: Path, expected_port: int
) -> dict[str, int]:
    numeric_keys = (
        "PFI_ACTIVE_PID",
        "PFI_ACTIVE_MONITOR_PID",
        "PFI_ACTIVE_LAUNCHER_PID",
        "PFI_ACTIVE_PORT",
        "PFI_ACTIVE_HEARTBEAT_PORT",
    )
    if any(not marker.get(key, "").isdigit() for key in numeric_keys):
        raise TargetMacAcceptanceError("runtime marker PID/port identity is invalid")
    values = {key: int(marker[key]) for key in numeric_keys}
    if values["PFI_ACTIVE_PORT"] != expected_port:
        raise TargetMacAcceptanceError("runtime did not use the reserved target port")
    if marker.get("PFI_ACTIVE_PROJECT_DIR") != str(PFI_ROOT):
        raise TargetMacAcceptanceError("runtime marker project identity mismatch")
    if marker.get("PFI_ACTIVE_CANDIDATE_MODE") != "0":
        raise TargetMacAcceptanceError("canonical App unexpectedly entered candidate mode")
    for key in ("PFI_ACTIVE_PID", "PFI_ACTIVE_MONITOR_PID", "PFI_ACTIVE_LAUNCHER_PID"):
        if not _pid_exists(values[key]):
            raise TargetMacAcceptanceError("owned target-Mac process is unavailable")
    launcher_pid = values["PFI_ACTIVE_LAUNCHER_PID"]
    pgid = os.getpgid(launcher_pid)
    if pgid <= 1 or pgid == os.getpgrp():
        raise TargetMacAcceptanceError("target-Mac runtime process group is unsafe")
    members = _process_group_members(pgid)
    required_fragments = (
        "StartPFI.command",
        "streamlit_app.py",
        "shutdown_monitor.py",
    )
    if not all(any(fragment in command for _, command in members) for fragment in required_fragments):
        raise TargetMacAcceptanceError("target-Mac runtime process group is incomplete")
    if any(str(PFI_ROOT) not in command for _, command in members):
        raise TargetMacAcceptanceError("target-Mac process group has an unowned member")
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise TargetMacAcceptanceError("isolated runtime root is invalid")
    return {**values, "process_group_id": pgid, "member_count": len(members)}


def _runtime_environment(root: Path, app_port: int, heartbeat_port: int) -> dict[str, str]:
    directories = {
        "HOME": root / "home",
        "PFI_DATA_HOME": root / "data",
        "PFI_RUNTIME_DIR": root / "runtime",
        "TMPDIR": root / "tmp",
        "XDG_CACHE_HOME": root / "cache",
        "PYTHONPYCACHEPREFIX": root / "python-pycache",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
    return {
        **{key: str(value) for key, value in directories.items()},
        "PFI_STREAMLIT_PORT": str(app_port),
        "PFI_HEARTBEAT_PORT": str(heartbeat_port),
        "PFI_HEARTBEAT_TIMEOUT": "600",
        "PFI_START_OPEN_BROWSER": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PFI_OSASCRIPT_BIN": "/usr/bin/false",
    }


def _launch_bundle_executable(
    environment: dict[str, str], marker_path: Path, app_port: int
) -> tuple[dict[str, str], dict[str, int]]:
    previous_marker = _marker_values(marker_path)
    previous_launcher_pid = previous_marker.get("PFI_ACTIVE_LAUNCHER_PID", "")
    executable = CANONICAL_APP / "Contents/MacOS/PFI"
    launched = subprocess.Popen(
        [str(executable)],
        cwd=REPO_ROOT,
        env={**os.environ, **environment},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        return_code = launched.wait(timeout=10)
    except subprocess.TimeoutExpired as exc:
        launched.kill()
        raise TargetMacAcceptanceError("native App launcher did not return") from exc
    if return_code != 0:
        raise TargetMacAcceptanceError("native App executable launch failed")
    def current_runtime_ready() -> bool:
        current_marker = _marker_values(marker_path)
        return bool(
            current_marker
            and current_marker.get("PFI_ACTIVE_LAUNCHER_PID", "")
            != previous_launcher_pid
            and _health(app_port)
        )

    ready = _wait(
        current_runtime_ready,
        timeout=90,
        interval=0.25,
    )
    if not ready:
        raise TargetMacAcceptanceError("canonical App runtime did not become healthy")
    marker = _marker_values(marker_path)
    owned = _validate_owned_runtime(marker, marker_path.parent, app_port)
    return marker, owned


def _repeat_launches(
    environment: dict[str, str], marker_path: Path, app_port: int, count: int
) -> dict[str, object]:
    before = _marker_values(marker_path)
    identity = tuple(
        before.get(key, "")
        for key in (
            "PFI_ACTIVE_PID",
            "PFI_ACTIVE_MONITOR_PID",
            "PFI_ACTIVE_LAUNCHER_PID",
            "PFI_ACTIVE_PORT",
            "PFI_ACTIVE_BUILD_ID",
            "PFI_ACTIVE_STARTED_AT",
        )
    )
    for _ in range(count):
        launched = _run(
            [CANONICAL_APP / "Contents/MacOS/PFI"],
            timeout=30,
            env=environment,
        )
        if launched.returncode != 0:
            raise TargetMacAcceptanceError("repeated native App launch failed")
        if not _health(app_port):
            raise TargetMacAcceptanceError("repeated launch lost the current service")
    after = _marker_values(marker_path)
    after_identity = tuple(
        after.get(key, "")
        for key in (
            "PFI_ACTIVE_PID",
            "PFI_ACTIVE_MONITOR_PID",
            "PFI_ACTIVE_LAUNCHER_PID",
            "PFI_ACTIVE_PORT",
            "PFI_ACTIVE_BUILD_ID",
            "PFI_ACTIVE_STARTED_AT",
        )
    )
    return {
        "launch_count": count,
        "existing_service_reused": identity == after_identity,
        "single_runtime_preserved": identity == after_identity,
        "health_preserved": _health(app_port),
    }


def _suspend_resume(owned: dict[str, int], app_port: int) -> dict[str, object]:
    process_group_id = owned["process_group_id"]
    members_before = _process_group_members(process_group_id)
    os.killpg(process_group_id, signal.SIGSTOP)
    try:
        time.sleep(1.0)
        unavailable_while_suspended = not _health(app_port, timeout=0.75)
    finally:
        os.killpg(process_group_id, signal.SIGCONT)
    recovered = _wait(lambda: _health(app_port), timeout=30, interval=0.25)
    members_after = _process_group_members(process_group_id)
    if not unavailable_while_suspended or not recovered:
        raise TargetMacAcceptanceError("owned process suspend/resume recovery failed")
    return {
        "probe": "owned_process_group_sigstop_sigcont",
        "status": "pass",
        "actual_os_sleep_performed": False,
        "actual_os_wake_performed": False,
        "service_suspend_resume_proxy_performed": True,
        "unavailable_while_suspended": unavailable_while_suspended,
        "health_recovered": recovered,
        "member_count_before": len(members_before),
        "member_count_after": len(members_after),
        "limitation": "This is a deterministic service suspension proxy and is not represented as a kernel sleep/wake cycle.",
    }


def _stop_runtime(owned: dict[str, int], app_port: int) -> dict[str, object]:
    launcher_pid = owned["PFI_ACTIVE_LAUNCHER_PID"]
    process_group_id = owned["process_group_id"]
    members = _process_group_members(process_group_id)
    if not members or not _pid_exists(launcher_pid):
        raise TargetMacAcceptanceError("owned runtime disappeared before stop")
    os.kill(launcher_pid, signal.SIGTERM)
    stopped = _wait(
        lambda: not _process_group_members(process_group_id),
        timeout=30,
        interval=0.25,
    )
    port_released = _wait(lambda: not _health(app_port, timeout=0.3), timeout=10)
    if not stopped or not port_released:
        for pid, _command in _process_group_members(process_group_id):
            if pid > 1:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        _wait(lambda: not _process_group_members(process_group_id), timeout=10)
        raise TargetMacAcceptanceError("owned runtime did not stop cleanly")
    return {
        "status": "pass",
        "owned_group_signaled": True,
        "process_group_empty": stopped,
        "port_released": port_released,
        "unowned_process_signaled": False,
    }


def _copy_real_sources(root: Path) -> list[Path]:
    objects, _attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    output: list[Path] = []
    for row in objects:
        index = int(row["source_index"])
        content = row["content"]
        if not isinstance(content, bytes):
            raise TargetMacAcceptanceError("immutable source payload is not bytes")
        target = root / f"real_source_{index}.csv"
        target.write_bytes(content)
        os.chmod(target, 0o600)
        output.append(target)
    return output


def _release_query() -> str:
    manifest = load_v025_release_manifest(
        manifest_path=PFI_ROOT / "config/release_manifest.json"
    )
    manifest_hash = hashlib.sha256(
        (PFI_ROOT / "config/release_manifest.json").read_bytes()
    ).hexdigest()
    from urllib.parse import urlencode

    return urlencode(
        {
            "pfi_app_version": manifest["app_short_version"],
            "pfi_app_build": manifest["app_build_version"],
            "pfi_build": manifest["build_id"],
            "pfi_commit": manifest["git_commit"],
            "pfi_frontend_hash": manifest["frontend_bundle_hash"],
            "pfi_backend_hash": manifest["backend_build_hash"],
            "pfi_manifest_sha256": manifest_hash,
        }
    )


def _safe_browser_result(payload: dict[str, Any]) -> dict[str, object]:
    diagnostics = payload.get("diagnostics", {})
    if not isinstance(diagnostics, dict):
        diagnostics = {}
    if any(
        int(diagnostics.get(key, 0) if isinstance(diagnostics.get(key), int) else len(diagnostics.get(key, [])))
        for key in (
            "console_errors",
            "page_errors",
            "unexpected_http_errors",
            "blocked_external_count",
        )
    ):
        raise TargetMacAcceptanceError("target-Mac browser diagnostics are not clean")
    return {
        key: value
        for key, value in payload.items()
        if key not in {"diagnostics", "screenshot", "trace"}
    } | {
        "diagnostics": {
            "console_error_count": 0,
            "page_error_count": 0,
            "unexpected_http_error_count": 0,
            "blocked_external_count": 0,
        }
    }


def _run_browser(
    *,
    mode: str,
    url: str,
    temp_root: Path,
    output_dir: Path,
    sources: list[Path] | None = None,
    expected_ledger_count: int = 0,
    expected_review_count: int = 0,
) -> tuple[dict[str, object], dict[str, object]]:
    browser_root = temp_root / f"browser-{mode}"
    browser_root.mkdir(parents=True, exist_ok=True)
    os.chmod(browser_root, 0o700)
    raw_trace = browser_root / f"{mode}-raw-trace.zip"
    command: list[str | Path] = [
        NODE,
        TARGET_BROWSER,
        "--url",
        url,
        "--output-dir",
        browser_root,
        "--trace",
        raw_trace,
        "--mode",
        mode,
        "--expected-ledger-count",
        str(expected_ledger_count),
        "--expected-review-count",
        str(expected_review_count),
    ]
    for source in sources or []:
        command.extend(("--source-path", source))
    completed = _run(
        command,
        check=False,
        timeout=420,
        env={
            "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR),
            "PFI_CHROME_PATH": str(CHROME),
        },
    )
    result_path = browser_root / f"{mode}_browser_result.json"
    if completed.returncode != 0 and result_path.is_file():
        raw_result = _read_json(result_path)
        safe_failure = {
            "mode": mode,
            "checks": raw_result.get("checks", {}),
            "uat": raw_result.get("uat", {}),
            "offline_recovery": raw_result.get("offline_recovery", {}),
        }
        raise TargetMacAcceptanceError(
            "target-Mac browser UAT failed: "
            + json.dumps(safe_failure, ensure_ascii=False, sort_keys=True)
        )
    if completed.returncode != 0:
        summary = (completed.stderr or completed.stdout or "browser failed").strip()
        raise TargetMacAcceptanceError(
            re.sub(r"/(?:Users|private|tmp)/\S+", "[LOCAL_PATH_REDACTED]", summary)[
                :1000
            ]
        )
    raw_result = _read_json(result_path)
    if raw_result.get("status") != "pass":
        safe_failure = {
            "mode": mode,
            "checks": raw_result.get("checks", {}),
            "uat": raw_result.get("uat", {}),
            "offline_recovery": raw_result.get("offline_recovery", {}),
        }
        raise TargetMacAcceptanceError(
            "target-Mac browser UAT failed: "
            + json.dumps(safe_failure, ensure_ascii=False, sort_keys=True)
        )
    sanitized_trace = output_dir / f"{mode}_browser_trace_sanitized.zip"
    privacy = sanitize_playwright_trace(raw_trace, sanitized_trace)
    if privacy.get("status") != "pass":
        raise TargetMacAcceptanceError("target-Mac browser trace privacy failed")
    screenshot_name = (
        "target_mac_app.png" if mode == "initial" else "restart_persistence.png"
    )
    screenshot_source = browser_root / screenshot_name
    screenshot_target = output_dir / screenshot_name
    shutil.copy2(screenshot_source, screenshot_target)
    safe = _safe_browser_result(raw_result)
    safe["screenshot"] = {
        "file": screenshot_name,
        "sha256": _sha_file(screenshot_target),
    }
    safe["trace"] = {
        "file": sanitized_trace.name,
        "sha256": _sha_file(sanitized_trace),
        "privacy_status": privacy["status"],
    }
    command_row = {
        "command_id": f"target_mac_browser_{mode}",
        "command": (
            "bundled-node PFI/web/tests/v025/stage12_target_mac_uat.mjs "
            f"--mode {mode} --url loopback-installed-app --output-dir private-temp"
        ),
        "exit_code": completed.returncode,
        "summary": f"{mode} target-Mac browser UAT passed",
    }
    return safe, command_row


def _run_real_backup_restore() -> tuple[dict[str, object], dict[str, object]]:
    command = [
        PFI_ROOT / ".venv/bin/python",
        "-B",
        PFI_ROOT / "scripts/v025/stage11_readonly_backup_rehearsal.py",
    ]
    completed = _run(
        command,
        check=False,
        timeout=300,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(SRC_ROOT)},
    )
    if completed.returncode != 0:
        raise TargetMacAcceptanceError("real canonical backup/restore rehearsal failed")
    payload = json.loads(completed.stdout)
    required = (
        payload.get("status") == "pass",
        payload.get("canonical_private_database_used") is True,
        payload.get("canonical_private_database_mutated") is False,
        payload.get("source_file_state_unchanged") is True,
        payload.get("source_directory_entries_unchanged") is True,
        payload.get("backup_integrity_check") == ["ok"],
        payload.get("backup_foreign_key_issue_count") == 0,
        payload.get("isolated_success_restore_status") == "restored",
        payload.get("isolated_automatic_rollback_performed") is True,
        payload.get("private_values_emitted") is False,
        payload.get("finder_used") is False,
        payload.get("launchservices_used") is False,
    )
    if not all(required):
        raise TargetMacAcceptanceError("real backup/restore truth gates failed")
    row = {
        "command_id": "canonical_readonly_backup_restore",
        "command": (
            "PFI/.venv/bin/python -B "
            "PFI/scripts/v025/stage11_readonly_backup_rehearsal.py"
        ),
        "exit_code": completed.returncode,
        "summary": "canonical private DB unchanged; isolated restore and rollback passed",
    }
    return payload, row


def _disk_free_bytes(path: Path) -> int:
    stats = os.statvfs(path)
    return int(stats.f_bavail * stats.f_frsize)


def _write_zeros(path: Path, byte_count: int) -> None:
    chunk = b"\0" * (1024 * 1024)
    remaining = byte_count
    with path.open("wb", buffering=0) as handle:
        while remaining > 0:
            payload = chunk if remaining >= len(chunk) else chunk[:remaining]
            handle.write(payload)
            remaining -= len(payload)


def _disk_pressure_rehearsal() -> tuple[dict[str, object], dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s12p2-disk-") as temp_name:
        root = Path(temp_name)
        os.chmod(root, 0o700)
        image = root / "pressure.sparseimage"
        mountpoint = root / "mount"
        mountpoint.mkdir()
        source = root / "source.sqlite"
        with sqlite3.connect(source) as connection:
            connection.execute(
                "CREATE TABLE technical_disk_probe(id INTEGER PRIMARY KEY, payload BLOB NOT NULL)"
            )
            connection.execute(
                "INSERT INTO technical_disk_probe(payload) VALUES (zeroblob(?))",
                (8 * 1024 * 1024,),
            )
            connection.commit()
        created = _run(
            [
                "/usr/bin/hdiutil",
                "create",
                "-size",
                "24m",
                "-fs",
                "HFS+",
                "-volname",
                "PFI_S12P2_PRESSURE",
                "-type",
                "SPARSE",
                "-ov",
                image,
            ],
            check=False,
            timeout=120,
        )
        if created.returncode != 0:
            raise TargetMacAcceptanceError("temporary disk-pressure volume creation failed")
        attached = False
        try:
            attach = _run(
                [
                    "/usr/bin/hdiutil",
                    "attach",
                    "-nobrowse",
                    "-noautoopen",
                    "-mountpoint",
                    mountpoint,
                    image,
                ],
                check=False,
                timeout=120,
            )
            if attach.returncode != 0:
                raise TargetMacAcceptanceError("temporary disk-pressure volume attach failed")
            attached = True
            capacity = shutil.disk_usage(mountpoint).total
            free_before = _disk_free_bytes(mountpoint)
            filler = mountpoint / "pressure.fill"
            target = mountpoint / "backup.sqlite"
            leave_free = 768 * 1024
            requested_fill = max(0, free_before - leave_free)
            try:
                _write_zeros(filler, requested_fill)
            except OSError:
                # Filesystem metadata reservation may surface ENOSPC slightly early.
                pass
            free_under_pressure = _disk_free_bytes(mountpoint)
            pressure_error_code: int | None = None
            pressure_error_name = ""
            pressure_failed = False
            source_connection = sqlite3.connect(source)
            target_connection: sqlite3.Connection | None = None
            try:
                target_connection = sqlite3.connect(target)
                source_connection.backup(target_connection)
            except sqlite3.Error as exc:
                pressure_failed = True
                pressure_error_code = getattr(exc, "sqlite_errorcode", None)
                pressure_error_name = str(getattr(exc, "sqlite_errorname", ""))
            finally:
                if target_connection is not None:
                    target_connection.close()
                source_connection.close()
            if target.exists():
                target.unlink()
            if filler.exists():
                filler.unlink()
            recovered_free = _disk_free_bytes(mountpoint)
            with sqlite3.connect(source) as source_connection, sqlite3.connect(
                target
            ) as target_connection:
                source_connection.backup(target_connection)
                target_connection.commit()
            with sqlite3.connect(f"{target.resolve().as_uri()}?mode=ro", uri=True) as check:
                integrity = [row[0] for row in check.execute("PRAGMA integrity_check")]
                row_count = int(
                    check.execute("SELECT COUNT(*) FROM technical_disk_probe").fetchone()[0]
                )
            sqlite_full_observed = pressure_failed and (
                pressure_error_code == sqlite3.SQLITE_FULL
                or pressure_error_name == "SQLITE_FULL"
            )
            payload = {
                "schema": "PFIV025Stage12Phase122DiskPressureV1",
                "status": (
                    "pass"
                    if sqlite_full_observed
                    and integrity == ["ok"]
                    and row_count == 1
                    else "fail"
                ),
                "volume_kind": "temporary_hfs_sparse_image_nobrowse",
                "volume_capacity_bytes": capacity,
                "free_bytes_before_pressure": free_before,
                "free_bytes_under_pressure": free_under_pressure,
                "sqlite_full_observed": sqlite_full_observed,
                "sqlite_error_code": pressure_error_code,
                "sqlite_error_name": pressure_error_name,
                "partial_backup_removed": True,
                "free_bytes_after_pressure_release": recovered_free,
                "recovery_backup_integrity_check": integrity,
                "recovery_backup_row_count": row_count,
                "technical_nonfinancial_payload": True,
                "real_financial_data_used": False,
                "host_volume_filled": False,
                "finder_used": False,
                "launchservices_used": False,
                "gui_file_operations_used": False,
                "contains_private_values": False,
            }
            if payload["status"] != "pass":
                raise TargetMacAcceptanceError("disk pressure/recovery gate failed")
        finally:
            if attached:
                _run(
                    ["/usr/bin/hdiutil", "detach", mountpoint, "-force"],
                    check=False,
                    timeout=120,
                )
        if mountpoint.is_mount():
            raise TargetMacAcceptanceError("temporary disk-pressure volume remained mounted")
    row = {
        "command_id": "temporary_disk_pressure_recovery",
        "command": (
            "PFI target-Mac harness: hdiutil -nobrowse temporary sparse volume; "
            "SQLite backup ENOSPC and recovery"
        ),
        "exit_code": 0,
        "summary": "real SQLITE_FULL observed on temporary volume; recovery backup passed",
    }
    return payload, row


def _changed_files() -> list[str]:
    tracked = _git_text("diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def _write_support_files(
    output_dir: Path,
    commands: list[dict[str, object]],
    changed_files: list[str],
) -> None:
    (output_dir / "terminal.log").write_text(
        "\n".join(
            f"{row['command_id']}|exit={row['exit_code']}|{row['summary']}"
            for row in commands
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )
    (output_dir / "risk_and_rollback.md").write_text(
        """# Phase 12.2 风险与回滚

- 用户已明确禁止 Finder 操作；本 Phase 只使用 CLI 原子安装与 bundle 原生可执行文件，未调用 Finder、LaunchServices、`open` 或 GUI 文件操作。
- 真实系统 sleep/wake 未执行；使用仅作用于本 run 已验证进程组的 `SIGSTOP/SIGCONT` 作为服务暂停/恢复代理，并明确保留为 P2 限制，不冒充内核休眠。
- 安装前的旧 App 已保存为 owner-only 私有归档；替换中任何校验失败都会恢复同文件系统 rollback bundle。
- canonical 私有 SQLite 仅以 query-only/Online Backup API 读取，源文件与目录状态不变；restore 与自动 rollback 只作用于隔离副本。
- 磁盘不足仅在 `hdiutil -nobrowse` 临时小卷制造真实 `SQLITE_FULL`，没有填充主机卷，临时卷已卸载删除。
- `SRC-HOLDINGS` 仍为 `not_loaded`；UAT 验证正确阻断和无假零，不宣称真实持仓编辑通过。
- Desktop/Downloads 非 canonical 入口仅做 CLI census，不修改；最终入口治理继续留给 Phase 12.3 release freeze。
- 回滚：从私有 pre-v0.2.5 归档恢复 `/Applications/PFI.app`；回退本 Phase 代码、测试、治理和 Evidence；隔离 runtime/data 已删除。
- 停止边界：不进入 Phase 12.3，不 push，不生成最终 `human_acceptance.json`，不冻结或声明 production accepted。
""",
        encoding="utf-8",
    )


def _privacy_scan(output_dir: Path) -> dict[str, object]:
    patterns = {
        "absolute_private_paths": re.compile(
            r"/(?:Users|private/var/folders|var/folders|private/tmp|tmp)/"
        ),
        "financial_values": re.compile(r"\bCNY\s+-?[0-9]"),
        "credentials": re.compile(
            r"(?i)(?:access_token|refresh_token|api_key|password|authorization(?:_header)?)[\"']?\s*[:=]"
        ),
        "raw_process_ids": re.compile(r'(?i)"(?:pid|process_id)"\s*:\s*[1-9][0-9]*'),
    }
    counts = {key: 0 for key in patterns}
    input_count = 0
    for path in sorted(output_dir.rglob("*")):
        if (
            not path.is_file()
            or path.name == "privacy_scan.txt"
            or path.suffix.lower() not in {".json", ".txt", ".md"}
        ):
            continue
        text = path.read_text(encoding="utf-8")
        input_count += 1
        for key, pattern in patterns.items():
            counts[key] += len(pattern.findall(text))
    status = "pass" if not any(counts.values()) else "fail"
    lines = [
        "PASS" if status == "pass" else "FAIL",
        "scanner=pfi-v025-stage12-phase122-public-evidence-scan-v1",
        f"input_count={input_count}",
        *(f"{key}={value}" for key, value in counts.items()),
        "contains_private_values=false",
        "finder_operations=0",
        "launchservices_operations=0",
        "open_command_operations=0",
        "gui_file_operations=0",
    ]
    (output_dir / "privacy_scan.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if status != "pass":
        raise TargetMacAcceptanceError(f"Phase 12.2 privacy scan failed: {counts}")
    return {"status": status, "counts": counts, "input_count": input_count}


def _isolated_database_receipt(database: Path) -> dict[str, object]:
    if not database.is_file() or database.is_symlink():
        raise TargetMacAcceptanceError("target-Mac isolated operational DB is missing")
    with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as connection:
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        foreign_key_issues = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        counts = {
            "import_batch_count": int(
                connection.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0]
            ),
            "import_file_count": int(
                connection.execute("SELECT COUNT(*) FROM import_files").fetchone()[0]
            ),
            "staged_transaction_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM import_staged_transactions"
                ).fetchone()[0]
            ),
            "ledger_entry_count": int(
                connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
            ),
            "pending_review_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM import_review_queue WHERE status='pending'"
                ).fetchone()[0]
            ),
            "resolved_review_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM import_review_queue WHERE status='resolved'"
                ).fetchone()[0]
            ),
            "active_holding_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM v025_holding_records WHERE status='active'"
                ).fetchone()[0]
            ),
        }
    status = (
        "pass"
        if integrity == ["ok"]
        and foreign_key_issues == 0
        and counts["import_batch_count"] == 1
        and counts["import_file_count"] == 4
        and counts["staged_transaction_count"] == 8808
        and counts["ledger_entry_count"] == 8808
        and counts["pending_review_count"] == 802
        and counts["resolved_review_count"] == 1
        and counts["active_holding_count"] == 0
        else "fail"
    )
    payload = {
        "schema": "PFIV025Stage12Phase122DatabaseBeforeAfterV1",
        "status": status,
        "before": {"database_exists": False, "ledger_entry_count": 0},
        "after_restart": {
            "integrity_check": integrity,
            "foreign_key_issue_count": foreign_key_issues,
            **counts,
        },
        "canonical_private_database_mutated": False,
        "isolated_database_deleted_after_run": True,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    if status != "pass":
        raise TargetMacAcceptanceError("target-Mac isolated DB persistence failed")
    return payload


def _release_identity_receipt(
    app_install: dict[str, object], browser: dict[str, object]
) -> dict[str, object]:
    manifest = load_v025_release_manifest(
        manifest_path=PFI_ROOT / "config/release_manifest.json"
    )
    disk = build_v025_release_asset_identity(PFI_ROOT, manifest=manifest)
    initial = browser["initial"]
    browser_identity = initial["release_identity"]
    status = (
        "pass"
        if disk["valid"] is True
        and app_install["after"]["short_version"] == manifest["app_short_version"]
        and app_install["after"]["build_version"] == manifest["app_build_version"]
        and browser_identity["version"] == manifest["version"]
        and browser_identity["build_id"] == manifest["build_id"]
        and browser_identity["git_commit"] == manifest["git_commit"]
        and browser_identity["frontend_bundle_hash"]
        == manifest["frontend_bundle_hash"]
        and browser_identity["backend_build_hash"] == manifest["backend_build_hash"]
        else "fail"
    )
    payload = {
        "schema": "PFIV025Stage12Phase122ReleaseIdentityV1",
        "status": status,
        "version": manifest["version"],
        "build_id": manifest["build_id"],
        "git_commit": manifest["git_commit"],
        "frontend_bundle_hash": manifest["frontend_bundle_hash"],
        "backend_build_hash": manifest["backend_build_hash"],
        "app_short_version": manifest["app_short_version"],
        "app_build_version": manifest["app_build_version"],
        "disk_frontend_valid": disk["frontend_valid"],
        "disk_backend_valid": disk["disk_backend_valid"],
        "installed_app_matches": True,
        "runtime_manifest_matches": True,
        "launcher_query_matches": True,
        "same_build": status == "pass",
        "contains_private_values": False,
    }
    if status != "pass":
        raise TargetMacAcceptanceError("installed App release identity mismatch")
    return payload


def run_phase122(
    *,
    output_dir: Path,
    real_data_required: bool,
    canonical_app_required: bool,
    no_finder_authorized: bool,
) -> dict[str, object]:
    if not real_data_required:
        raise TargetMacAcceptanceError("real-data-required is mandatory")
    if not canonical_app_required:
        raise TargetMacAcceptanceError("canonical-app-required is mandatory")
    if not no_finder_authorized:
        raise TargetMacAcceptanceError("explicit no-Finder authorization is mandatory")
    if output_dir.resolve() != DEFAULT_OUTPUT_DIR.resolve():
        raise TargetMacAcceptanceError("Phase 12.2 evidence must use the canonical report directory")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    observed_at = _now()
    commands: list[dict[str, object]] = []

    app_install = install_canonical_app(observed_at)
    commands.append(
        {
            "command_id": "canonical_app_cli_atomic_install",
            "command": (
                "PFI target-Mac harness: compile/sign/stage/atomic-replace "
                "applications_pfi_app (no Finder/LaunchServices/open)"
            ),
            "exit_code": 0,
            "summary": "canonical App v0.2.5 installed and release identity verified",
        }
    )
    entry_census = _entry_census()

    app_port = _select_free_port()
    heartbeat_port = _select_free_port()
    while heartbeat_port == app_port:
        heartbeat_port = _select_free_port()
    lifecycle: dict[str, object]
    database_receipt: dict[str, object]
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s12p2-runtime-") as temp_name:
        temp_root = Path(temp_name)
        os.chmod(temp_root, 0o700)
        environment = _runtime_environment(temp_root, app_port, heartbeat_port)
        marker_path = temp_root / "runtime/pfi_active_service.env"
        source_root = temp_root / "real-sources"
        source_root.mkdir()
        os.chmod(source_root, 0o700)
        sources = _copy_real_sources(source_root)
        owned: dict[str, int] | None = None
        try:
            first_marker, owned = _launch_bundle_executable(
                environment, marker_path, app_port
            )
            manifest = load_v025_release_manifest(
                manifest_path=PFI_ROOT / "config/release_manifest.json"
            )
            if (
                first_marker.get("PFI_ACTIVE_BUILD_ID") != manifest["build_id"]
                or first_marker.get("PFI_ACTIVE_GIT_COMMIT")
                != manifest["git_commit"]
                or first_marker.get("PFI_ACTIVE_FRONTEND_HASH")
                != manifest["frontend_bundle_hash"]
                or first_marker.get("PFI_ACTIVE_BACKEND_HASH")
                != manifest["backend_build_hash"]
            ):
                raise TargetMacAcceptanceError("native App runtime marker identity mismatch")
            repeated = _repeat_launches(
                environment, marker_path, app_port, count=3
            )
            initial_browser, initial_command = _run_browser(
                mode="initial",
                url=f"http://127.0.0.1:{app_port}/?{_release_query()}",
                temp_root=temp_root,
                output_dir=output_dir,
                sources=sources,
            )
            commands.append(initial_command)
            browser_close_health = _health(app_port)
            suspend_resume = _suspend_resume(owned, app_port)
            first_identity_hash = _sha_bytes(
                "|".join(
                    first_marker.get(key, "")
                    for key in (
                        "PFI_ACTIVE_BUILD_ID",
                        "PFI_ACTIVE_GIT_COMMIT",
                        "PFI_ACTIVE_FRONTEND_HASH",
                        "PFI_ACTIVE_BACKEND_HASH",
                        "PFI_ACTIVE_STARTED_AT",
                    )
                ).encode("utf-8")
            )
            first_stop = _stop_runtime(owned, app_port)
            owned = None
            restart_marker, owned = _launch_bundle_executable(
                environment, marker_path, app_port
            )
            restart_identity_hash = _sha_bytes(
                "|".join(
                    restart_marker.get(key, "")
                    for key in (
                        "PFI_ACTIVE_BUILD_ID",
                        "PFI_ACTIVE_GIT_COMMIT",
                        "PFI_ACTIVE_FRONTEND_HASH",
                        "PFI_ACTIVE_BACKEND_HASH",
                        "PFI_ACTIVE_STARTED_AT",
                    )
                ).encode("utf-8")
            )
            uat = initial_browser["uat"]
            restart_browser, restart_command = _run_browser(
                mode="restart",
                url=f"http://127.0.0.1:{app_port}/?{_release_query()}",
                temp_root=temp_root,
                output_dir=output_dir,
                expected_ledger_count=int(uat["ledger_count"]),
                expected_review_count=int(uat["review_count_after"]),
            )
            commands.append(restart_command)
            database_receipt = _isolated_database_receipt(
                temp_root / "data/private/operational/pfi.sqlite"
            )
            second_stop = _stop_runtime(owned, app_port)
            owned = None
            lifecycle = {
                "schema": "PFIV025Stage12Phase122TargetMacLifecycleV1",
                "status": "pass",
                "target_platform": "current_macos_host",
                "launcher_mode": "direct_canonical_bundle_executable",
                "initial_start_healthy": True,
                "repeated_start": repeated,
                "browser_close_service_healthy": browser_close_health,
                "offline_recovery": initial_browser["offline_recovery"],
                "suspend_resume": suspend_resume,
                "first_stop": first_stop,
                "restart_healthy": True,
                "restart_created_new_runtime": (
                    first_identity_hash != restart_identity_hash
                ),
                "restart_persistence_verified": restart_browser["status"]
                == "pass",
                "second_stop": second_stop,
                "isolated_runtime_deleted_after_run": True,
                "finder_used": False,
                "launchservices_used": False,
                "open_command_used": False,
                "gui_file_operations_used": False,
                "contains_private_values": False,
            }
            if not all(
                (
                    repeated["single_runtime_preserved"],
                    browser_close_health,
                    initial_browser["offline_recovery"][
                        "offline_failure_observed"
                    ],
                    initial_browser["offline_recovery"][
                        "online_recovery_observed"
                    ],
                    suspend_resume["health_recovered"],
                    lifecycle["restart_created_new_runtime"],
                    lifecycle["restart_persistence_verified"],
                )
            ):
                raise TargetMacAcceptanceError("target-Mac lifecycle matrix failed")
            browser_evidence = {
                "schema": "PFIV025Stage12Phase122BrowserEvidenceV1",
                "status": "pass",
                "initial": initial_browser,
                "restart": restart_browser,
                "browser_close_service_healthy": browser_close_health,
                "contains_private_values": False,
            }
        finally:
            if owned is not None:
                try:
                    _stop_runtime(owned, app_port)
                except Exception:
                    for pid, _command in _process_group_members(
                        owned["process_group_id"]
                    ):
                        if pid > 1:
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass

    commands.append(
        {
            "command_id": "canonical_app_lifecycle_matrix",
            "command": (
                "applications_pfi_app/Contents/MacOS/PFI with isolated "
                "HOME/data/runtime/ports and PFI_START_OPEN_BROWSER=0"
            ),
            "exit_code": 0,
            "summary": "start/repeat/suspend/recover/stop/restart/browser-close passed",
        }
    )
    backup_restore, backup_command = _run_real_backup_restore()
    commands.append(backup_command)
    disk_pressure, disk_command = _disk_pressure_rehearsal()
    commands.append(disk_command)
    release_identity = _release_identity_receipt(app_install, browser_evidence)

    defects: list[dict[str, object]] = [
        {
            "defect_id": "S12-P122-P2-ACTUAL-OS-SLEEP-NOT-RUN",
            "severity": "P2",
            "status": "accepted_limitation",
            "release_blocking": False,
            "disposition": "Use deterministic owned-process suspend/resume; do not claim kernel sleep/wake.",
        },
        {
            "defect_id": "S12-P122-P2-HOLDINGS-SOURCE-NOT-LOADED",
            "severity": "P2",
            "status": "truthfully_blocked_source",
            "release_blocking": False,
            "disposition": "Keep holding edit not_run and verify no false zero or fixture fallback.",
        },
    ]
    mismatch_count = int(entry_census["noncanonical_copy_mismatch_count"])
    if mismatch_count:
        defects.append(
            {
                "defect_id": "S12-P122-P2-NONCANONICAL-ENTRY-MISMATCH",
                "severity": "P2",
                "status": "identified_not_modified",
                "release_blocking": False,
                "count": mismatch_count,
                "disposition": "CLI census only under no-Finder instruction; final entry freeze remains Phase 12.3.",
            }
        )
    defect_register = {
        "schema": "PFIV025Stage12Phase122DefectRegisterV1",
        "status": "pass",
        "open_p0_count": 0,
        "open_p1_count": 0,
        "open_p2_count": len(defects),
        "defects": defects,
        "contains_private_values": False,
    }
    initial_uat = browser_evidence["initial"]["uat"]
    restart_uat = browser_evidence["restart"]["uat"]
    human_task_uat = {
        "schema": "PFIV025Stage12Phase122HumanTaskUATV1",
        "status": "pass",
        "operator_kind": "codex_agent_on_behalf_of_user_under_standing_authorization",
        "manual_user_click_claimed": False,
        "final_human_acceptance_claimed": False,
        "standing_authorization_bound": True,
        "user_no_finder_override_sha256": USER_NO_FINDER_INSTRUCTION_SHA256,
        "entry_identity_same_build": release_identity["same_build"],
        "primary_navigation_count": browser_evidence["initial"][
            "primary_entry_count"
        ],
        "real_upload_preview_confirm": {
            "source_blob_count": initial_uat["source_blob_count"],
            "raw_record_count": initial_uat["raw_record_count"],
            "transaction_count": initial_uat["transaction_count"],
            "fixture_used": initial_uat["fixture_used"],
            "fallback_used": initial_uat["fallback_used"],
        },
        "one_review_completed": (
            initial_uat["review_count_after"]
            == initial_uat["review_count_before"] - 1
        ),
        "ledger_persisted_after_restart": (
            restart_uat["observed_ledger_count"]
            == restart_uat["expected_ledger_count"]
        ),
        "holding_uat": {
            "execution_status": "not_run",
            "reason_code": "SRC_HOLDINGS_NOT_LOADED",
            "truthful_block": initial_uat["holdings"]["truthful_not_loaded"],
            "false_zero_count": initial_uat["holdings"]["false_zero_count"],
            "financial_pass_claimed": False,
        },
        "formula_source_interconnection_drilldown": initial_uat["drilldown"],
        "report_truth_states": initial_uat["reports"],
        "defect_register": "defect_register.json",
        "contains_private_values": False,
    }
    phase_contract = {
        "schema": "PFIV025Stage12Phase122ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "entry_mode": "cli_atomic_install_and_direct_bundle_executable",
        "finder_prohibited_by_current_user_instruction": True,
        "actual_os_sleep_proxy_disclosed": True,
        "phase_12_3_started": False,
        "push_performed": False,
        "final_human_acceptance": False,
    }

    artifacts = {
        "app_installation.json": app_install,
        "entry_census.json": entry_census,
        "target_mac_lifecycle.json": lifecycle,
        "target_mac_browser.json": browser_evidence,
        "database_before_after.json": database_receipt,
        "backup_restore_result.json": backup_restore,
        "disk_pressure_result.json": disk_pressure,
        "release_identity.json": release_identity,
        "human_task_uat.json": human_task_uat,
        "defect_register.json": defect_register,
        "phase_contract.json": phase_contract,
    }
    for name, payload in artifacts.items():
        _write_json(output_dir / name, payload)

    changed_files = _changed_files()
    _write_support_files(output_dir, commands, changed_files)
    evidence_files = sorted(
        {
            path.relative_to(output_dir).as_posix()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        | {"evidence.json", "privacy_scan.txt", "artifact_manifest.json"}
    )
    evidence = {
        "schema": "PFIV025Stage12Phase122EvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {
            "S12-P2-T1": "candidate_complete_with_authorized_cli_entry_override",
            "S12-P2-T2": "candidate_complete_with_disclosed_suspend_resume_proxy",
            "S12-P2-T3": "candidate_complete",
            "S12-P2-T4": "candidate_complete_agent_executed_user_task_protocol",
        },
        "acceptance_id": ACCEPTANCE_ID,
        "status": "candidate_pass",
        "git_commit": "SELF",
        "git_commit_semantics": "commit_containing_this_evidence",
        "observed_at": observed_at,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "scope_override_reason": "Root governance companions and the source-Roadmap canonical App install are required; the current user explicitly replaces Finder activation with a no-Finder CLI path.",
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": evidence_files,
        "explicitly_not_done": [
            "Finder activation or screenshot",
            "LaunchServices registration or activation",
            "open command browser launch",
            "actual kernel sleep/wake",
            "Phase 12.3 status unification and release freeze",
            "Git push",
            "final human acceptance",
            "production acceptance",
            "v0.2.6 work",
        ],
        "risks": [
            "Actual kernel sleep/wake was not run; the owned-process suspend/resume proxy is explicit P2 residual risk.",
            "SRC-HOLDINGS remains not_loaded; holding edit is not_run and only truthful blocking/no-false-zero passed.",
            "Noncanonical Desktop/Downloads copies were CLI-censused but not modified under the no-Finder instruction.",
        ],
        "rollback": "Restore the private pre-v0.2.5 App archive if needed; revert bounded Phase 12.2 code/governance/evidence. Canonical private DB was unchanged and isolated runtime/data/volume were deleted.",
        "requires_user_acceptance": True,
        "open_p0_count": 0,
        "open_p1_count": 0,
        "open_p2_count": len(defects),
        "canonical_app_installed": True,
        "app_install_performed": app_install["install_performed_in_phase"],
        "canonical_app_same_build": release_identity["same_build"],
        "canonical_private_database_read": True,
        "canonical_private_database_changed": False,
        "real_financial_source_read": True,
        "real_financial_source_mutated": False,
        "financial_fixture_fallback_used": False,
        "holding_real_source_status": "not_loaded",
        "holding_financial_pass_claimed": False,
        "temporary_isolated_database_deleted": True,
        "temporary_disk_volume_deleted": True,
        "finder_used": False,
        "launchservices_used": False,
        "open_command_used": False,
        "gui_file_operations_used": False,
        "actual_os_sleep_performed": False,
        "service_suspend_resume_proxy_performed": True,
        "push_performed": False,
        "phase_12_3_started": False,
        "release_freeze_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "contains_private_values": False,
        "requires_stage_whole_review": True,
    }
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(
            archive.read(
                "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
            )
        )
    Draft202012Validator(schema).validate(evidence)
    _write_json(output_dir / "evidence.json", evidence)
    privacy = _privacy_scan(output_dir)
    artifact_inputs = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    source_inputs = tuple(
        path
        for path in (
            PFI_ROOT / "scripts/v025/release_acceptance.py",
            PFI_ROOT / "scripts/v025/target_mac_uat.py",
            TARGET_BROWSER,
            PFI_ROOT / "tests/test_v025_stage12_target_mac_uat.py",
            PFI_ROOT / "docs/pfi_v025/stage_12/PHASE_12_2_TARGET_MAC_CLI_UAT.md",
            PFI_ROOT / "config/release_manifest.json",
            PFI_ROOT / "macos/PFI.app/Contents/Info.plist",
        )
        if path.is_file()
    )
    artifact_manifest = {
        "schema": "PFIV025Stage12Phase122ArtifactManifestV1",
        "status": "pass",
        "files": {
            path.relative_to(REPO_ROOT).as_posix(): _sha_file(path)
            for path in (*artifact_inputs, *source_inputs)
        },
        "privacy_scan_status": privacy["status"],
        "contains_private_values": False,
    }
    artifact_manifest["file_count"] = len(artifact_manifest["files"])
    _write_json(output_dir / "artifact_manifest.json", artifact_manifest)
    return evidence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--real-data-required", action="store_true")
    parser.add_argument("--canonical-app-required", action="store_true")
    parser.add_argument("--no-finder-authorized", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_dir = args.evidence_out
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    evidence = run_phase122(
        output_dir=output_dir,
        real_data_required=args.real_data_required,
        canonical_app_required=args.canonical_app_required,
        no_finder_authorized=args.no_finder_authorized,
    )
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "phase": evidence["phase"],
                "task_count": len(evidence["task_ids"]),
                "open_p0_count": evidence["open_p0_count"],
                "open_p1_count": evidence["open_p1_count"],
                "finder_used": evidence["finder_used"],
                "canonical_app_installed": evidence["canonical_app_installed"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
