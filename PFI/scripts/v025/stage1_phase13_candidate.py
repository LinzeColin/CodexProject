#!/usr/bin/env python3
"""Prepare, inspect and clean the disposable PFI v0.2.5 Stage 1 candidate."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


STATE_SCHEMA = "PFIV025Stage1Phase13CandidateStateV1"
RUNTIME_CLEANUP_CHECKPOINT_SCHEMA = "PFIV025Stage1Phase13RuntimeCleanupCheckpointV1"
FINALIZING_TOMBSTONE_NAME = "PFI_STAGE1_FINALIZING"
FINALIZING_TOMBSTONE_PAYLOAD = b"PFI_STAGE1_FINALIZING_V1\n"
TEMP_ROOT_PATTERN = re.compile(r"^pfi-v025-s1p13-[A-Za-z0-9._-]+$")
EVIDENCE_ROOT_PATTERN = re.compile(r"^pfi-v025-s1p13-evidence-[A-Za-z0-9._-]+$")
HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
LSREGISTER = Path(
    "/System/Library/Frameworks/CoreServices.framework/Frameworks/"
    "LaunchServices.framework/Support/lsregister"
)
IDENTITY_FILES = (
    "Contents/MacOS/PFI",
    "Contents/Info.plist",
    "Contents/_CodeSignature/CodeResources",
    "Contents/Resources/PFI_PROJECT_ROOT",
    "Contents/Resources/PFI_STAGE1_ISOLATED_ROOT",
    "Contents/Resources/PFI_STAGE1_STREAMLIT_PORT",
    "Contents/Resources/PFI_STAGE1_HEARTBEAT_PORT",
)
CANONICAL_SYMBOLS = {
    "applications": "${APPLICATIONS}/PFI.app",
    "desktop": "${HOME}/Desktop/PFI.app",
    "downloads": "${HOME}/Downloads/PFI.app",
}


class CandidateError(RuntimeError):
    """A fail-closed candidate lifecycle error."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise CandidateError(f"required regular file is unavailable: {path.name}")
    return _sha256_bytes(path.read_bytes())


def _run(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
    timeout: float = 60,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    if check and completed.returncode != 0:
        command = Path(args[0]).name
        raise CandidateError(f"{command} failed with exit code {completed.returncode}")
    return completed


def _xattr_hash(path: Path) -> str:
    args = ["/usr/bin/xattr", "-l", "-x"]
    if path.is_symlink():
        args.append("-s")
    completed = subprocess.run([*args, str(path)], check=False, capture_output=True)
    return _sha256_bytes(
        b"\0".join(
            (
                str(completed.returncode).encode("ascii"),
                completed.stdout,
                completed.stderr,
            )
        )
    )


def _acl_hash(path: Path) -> str:
    completed = subprocess.run(
        ["/bin/ls", "-ldeO@", str(path)],
        check=False,
        capture_output=True,
    )
    return _sha256_bytes(
        b"\0".join(
            (
                str(completed.returncode).encode("ascii"),
                completed.stdout,
                completed.stderr,
            )
        )
    )


def _metadata_record(path: Path, *, relative: str) -> bytes:
    metadata = path.lstat()
    values = (
        relative,
        str(stat.S_IFMT(metadata.st_mode)),
        str(stat.S_IMODE(metadata.st_mode)),
        str(metadata.st_uid),
        str(metadata.st_gid),
        str(metadata.st_size),
        str(metadata.st_mtime_ns),
        str(getattr(metadata, "st_flags", 0)),
        str(getattr(metadata, "st_birthtime", 0)),
        _xattr_hash(path),
    )
    return ("\0".join(values) + "\n").encode("utf-8")


def _tree_sha256(root: Path) -> str:
    records: list[bytes] = []
    paths = [root, *root.rglob("*")] if root.exists() and not root.is_symlink() else [root]
    for path in sorted(paths, key=lambda item: item.relative_to(root.parent).as_posix()):
        metadata = path.lstat()
        relative = path.relative_to(root.parent).as_posix()
        records.append(_metadata_record(path, relative=relative))
        records.append(f"A\0{relative}\0{_acl_hash(path)}\n".encode("utf-8"))
        if stat.S_ISLNK(metadata.st_mode):
            payload = f"L\0{relative}\0{_sha256_bytes(os.readlink(path).encode('utf-8'))}\n"
        elif stat.S_ISDIR(metadata.st_mode):
            payload = f"D\0{relative}\n"
        elif stat.S_ISREG(metadata.st_mode):
            payload = f"F\0{relative}\0{_sha256_file(path)}\n"
        else:
            payload = f"O\0{relative}\0{stat.S_IFMT(metadata.st_mode)}\n"
        records.append(payload.encode("utf-8"))
    return _sha256_bytes(b"".join(records))


def _bundle_identity(bundle: Path) -> dict[str, object]:
    plist_path = bundle / "Contents" / "Info.plist"
    with plist_path.open("rb") as file_obj:
        plist = plistlib.load(file_obj)
    executable = bundle / "Contents" / "MacOS" / str(plist["CFBundleExecutable"])
    codesign = subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(bundle)],
        check=False,
        capture_output=True,
    )
    return {
        "tree_sha256": _tree_sha256(bundle),
        "executable_sha256": _sha256_file(executable),
        "plist_identity": {
            "bundle_identifier": str(plist["CFBundleIdentifier"]),
            "short_version": str(plist["CFBundleShortVersionString"]),
            "build_version": str(plist["CFBundleVersion"]),
        },
        "codesign_valid": codesign.returncode == 0,
    }


def snapshot_canonical_entries(home: Path) -> dict[str, dict[str, object]]:
    """Return a strictly symbolic, read-only inventory of the three canonical entries."""

    home = home.expanduser().resolve()
    entries = {
        "applications": Path("/Applications/PFI.app"),
        "desktop": home / "Desktop" / "PFI.app",
        "downloads": home / "Downloads" / "PFI.app",
    }
    known_targets = {
        path.resolve(strict=True): CANONICAL_SYMBOLS[label]
        for label, path in entries.items()
        if path.exists() and not path.is_symlink()
    }
    snapshot: dict[str, dict[str, object]] = {}
    for label, path in entries.items():
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            snapshot[label] = {"kind": "missing", "symbolic_path": CANONICAL_SYMBOLS[label]}
            continue
        if stat.S_ISLNK(metadata.st_mode):
            resolved = path.resolve(strict=True)
            symbolic_target = known_targets.get(resolved)
            if symbolic_target is None:
                raise CandidateError(f"canonical symlink target is not an allowlisted entry: {label}")
            snapshot[label] = {
                "kind": "symlink",
                "symbolic_path": CANONICAL_SYMBOLS[label],
                "symbolic_target": symbolic_target,
                **_bundle_identity(resolved),
            }
        elif stat.S_ISDIR(metadata.st_mode):
            snapshot[label] = {
                "kind": "bundle",
                "symbolic_path": CANONICAL_SYMBOLS[label],
                **_bundle_identity(path),
            }
        else:
            raise CandidateError(f"canonical entry has an unsupported kind: {label}")
    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    if str(home) in serialized or "/Users/" in serialized:
        raise CandidateError("canonical inventory contains a private path")
    return snapshot


def _candidate_bundle_sha256(candidate_app: Path) -> str:
    records: list[bytes] = []
    for relative in IDENTITY_FILES:
        records.append(f"{relative}={_sha256_file(candidate_app / relative)}\n".encode("utf-8"))
    return _sha256_bytes(b"".join(records))


def _git_value(git_root: Path, *args: str) -> str:
    return _run("git", *args, cwd=git_root).stdout.strip()


def _select_free_ports() -> tuple[int, int]:
    sockets: list[socket.socket] = []
    ports: list[int] = []
    try:
        while len(ports) < 2:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = int(listener.getsockname()[1])
            if port in {8501, 8502} or port in ports:
                listener.close()
                continue
            sockets.append(listener)
            ports.append(port)
    finally:
        for listener in sockets:
            listener.close()
    return ports[0], ports[1]


def _write_marker(path: Path, value: str) -> None:
    encoded = value.encode("ascii")
    if not encoded or any(byte < 32 or byte > 126 for byte in encoded):
        raise CandidateError(f"marker value is not printable ASCII: {path.name}")
    path.write_bytes(encoded + b"\n")
    path.chmod(0o600)


def _ready_marker_record(project_root: Path) -> dict[str, object]:
    marker = project_root / ".venv" / ".pfi_os_app_ready"
    if not marker.is_file():
        return {"exists": False}
    metadata = marker.stat()
    return {
        "exists": True,
        "sha256": _sha256_file(marker),
        "mode": stat.S_IMODE(metadata.st_mode),
        "mtime_ns": metadata.st_mtime_ns,
    }


def _write_state(state_path: Path, state: dict[str, Any]) -> None:
    temporary = state_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(state_path)
    state_path.chmod(0o600)


def _unregister(candidate_app: Path) -> int:
    if not LSREGISTER.is_file():
        return 127
    try:
        return _run(
            str(LSREGISTER),
            "-u",
            str(candidate_app),
            check=False,
            timeout=15,
        ).returncode
    except (OSError, subprocess.SubprocessError):
        return 127


def _launchservices_exact_path_status(candidate_app: Path) -> tuple[bool, int, str]:
    """Return query success, exact registration count and a sanitized record digest."""

    if not LSREGISTER.is_file():
        return False, 0, ""
    try:
        completed = _run(str(LSREGISTER), "-dump", check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False, 0, ""
    if completed.returncode != 0:
        return False, 0, ""
    candidate = str(candidate_app.resolve())
    pattern = re.compile(
        rf"^path:\s+{re.escape(candidate)}(?:\s+\(0x[0-9a-fA-F]+\))?\s*$"
    )
    matches = [
        line.strip()
        for line in completed.stdout.splitlines()
        if pattern.fullmatch(line.strip())
    ]
    digest = _sha256_bytes("\n".join(matches).encode("utf-8")) if matches else _sha256_bytes(b"absent")
    return True, len(matches), digest


def _wait_for_launchservices_state(
    candidate_app: Path,
    *,
    registered: bool,
    timeout_seconds: float = 15,
) -> tuple[bool, int, str]:
    deadline = time.monotonic() + timeout_seconds
    last = (False, 0, "")
    stable_matches = 0
    required_stable_matches = 2 if registered else 3
    while True:
        last = _launchservices_exact_path_status(candidate_app)
        query_ok, count, _digest = last
        if query_ok and ((registered and count > 0) or (not registered and count == 0)):
            stable_matches += 1
            if stable_matches >= required_stable_matches:
                return last
        else:
            stable_matches = 0
        if time.monotonic() >= deadline:
            return last
        time.sleep(0.25)


def prepare_candidate(project_root: Path) -> dict[str, Any]:
    """Build, sign and register one disposable candidate without canonical mutation."""

    project_root = project_root.expanduser().resolve(strict=True)
    git_root = project_root.parent
    if project_root.name != "PFI" or not (project_root / "StartPFI.command").is_file():
        raise CandidateError("project_root is not the PFI source root")
    if Path(_git_value(git_root, "rev-parse", "--show-toplevel")) != git_root:
        raise CandidateError("PFI git root is not the expected worktree")
    checkout_commit = _git_value(git_root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", checkout_commit):
        raise CandidateError("checkout commit is invalid")

    source_app = project_root / "macos" / "PFI.app"
    launcher_source = project_root / "macos" / "PFI_launcher.c"
    if not source_app.is_dir() or not launcher_source.is_file():
        raise CandidateError("source App or launcher source is missing")
    source_identity = _bundle_identity(source_app)
    if source_identity["plist_identity"]["short_version"] != "0.2.5":  # type: ignore[index]
        raise CandidateError("source App is not v0.2.5")

    canonical_before = snapshot_canonical_entries(Path.home())
    source_app_tree_sha256 = str(source_identity["tree_sha256"])
    git_status = _git_value(git_root, "status", "--short")
    streamlit_port, heartbeat_port = _select_free_ports()
    isolated_root = Path(tempfile.mkdtemp(prefix="pfi-v025-s1p13-", dir="/private/tmp")).resolve()
    isolated_root.chmod(0o700)
    candidate_app = isolated_root / "PFI.app"
    registered = False
    try:
        _run(
            "/usr/bin/ditto",
            "--norsrc",
            "--noextattr",
            "--noacl",
            str(source_app),
            str(candidate_app),
        )
        copied_app_tree_sha256 = _tree_sha256(candidate_app)
        candidate_executable = candidate_app / "Contents" / "MacOS" / "PFI"
        _run(
            "clang",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wl,-no_uuid",
            "-DPFI_STAGE1_ISOLATED_PROCESS_GROUP=1",
            "-o",
            str(candidate_executable),
            str(launcher_source),
        )

        resources = candidate_app / "Contents" / "Resources"
        resources.mkdir(parents=True, exist_ok=True)
        marker_values = {
            "PFI_PROJECT_ROOT": str(project_root),
            "PFI_STAGE1_ISOLATED_ROOT": str(isolated_root),
            "PFI_STAGE1_STREAMLIT_PORT": str(streamlit_port),
            "PFI_STAGE1_HEARTBEAT_PORT": str(heartbeat_port),
            "PFI_STAGE1_CHECKOUT_COMMIT": checkout_commit,
            "PFI_STAGE1_SOURCE_APP_TREE_SHA256": source_app_tree_sha256,
            "PFI_STAGE1_COPIED_APP_TREE_SHA256": copied_app_tree_sha256,
        }
        for name, value in marker_values.items():
            _write_marker(resources / name, value)

        _run("/usr/bin/codesign", "--force", "--deep", "--sign", "-", str(candidate_app))
        _run("/usr/bin/codesign", "--verify", "--deep", "--strict", str(candidate_app))
        if not LSREGISTER.is_file():
            raise CandidateError("LaunchServices registrar is unavailable")
        _run(str(LSREGISTER), "-f", str(candidate_app))
        registered = True
        registration_query_ok, registration_count, registration_digest = (
            _wait_for_launchservices_state(candidate_app, registered=True)
        )
        if not registration_query_ok or registration_count < 1 or not HEX64_PATTERN.fullmatch(registration_digest):
            raise CandidateError("LaunchServices candidate registration could not be proven")

        candidate_app_path_sha256 = _sha256_bytes(str(candidate_app).encode("utf-8"))
        candidate_executable_sha256 = _sha256_file(candidate_executable)
        candidate_bundle_sha256 = _candidate_bundle_sha256(candidate_app)
        state_path = isolated_root / "state.json"
        checkout_binding_sha256 = _sha256_bytes(
            f"{checkout_commit}\0{project_root}".encode("utf-8")
        )
        git_status_sha256 = _sha256_bytes(git_status.encode("utf-8"))
        state: dict[str, Any] = {
            "schema": STATE_SCHEMA,
            "state_path": str(state_path),
            "isolated_root": str(isolated_root),
            "isolated_root_st_dev": isolated_root.stat().st_dev,
            "isolated_root_st_ino": isolated_root.stat().st_ino,
            "temp_root": str(isolated_root),
            "candidate_app": str(candidate_app),
            "app_path": str(candidate_app),
            "active_marker_path": str(isolated_root / "runtime" / "pfi_active_service.env"),
            "project_root": str(project_root),
            "git_root": str(git_root),
            "checkout_commit": checkout_commit,
            "checkout_binding_sha256": checkout_binding_sha256,
            "git_status_sha256": git_status_sha256,
            "git_status_sha256_before": git_status_sha256,
            "git_status_clean": not bool(git_status),
            "source_app_tree_sha256": source_app_tree_sha256,
            "source_tree_sha256": source_app_tree_sha256,
            "source_executable_sha256": source_identity["executable_sha256"],
            "copied_app_tree_sha256": copied_app_tree_sha256,
            "copied_tree_sha256": copied_app_tree_sha256,
            "candidate_app_tree_sha256": _tree_sha256(candidate_app),
            "candidate_app_path_sha256": candidate_app_path_sha256,
            "candidate_executable_sha256": candidate_executable_sha256,
            "candidate_bundle_sha256": candidate_bundle_sha256,
            "streamlit_port": streamlit_port,
            "app_port": streamlit_port,
            "heartbeat_port": heartbeat_port,
            "canonical_before": canonical_before,
            "protected_metadata_before": {
                "ready_marker": _ready_marker_record(project_root),
                "source_app": source_identity,
            },
            "launchservices_registered": True,
            "launchservices_registration_verified": True,
            "launchservices_registration_record_count": registration_count,
            "launchservices_registration_record_sha256": registration_digest,
            "prepared_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "lifecycle_state": "PREPARED",
        }
        _write_state(state_path, state)
        return state
    except Exception:
        if registered:
            _unregister(candidate_app)
            _wait_for_launchservices_state(candidate_app, registered=False)
        shutil.rmtree(isolated_root, ignore_errors=True)
        raise


def _validate_state_path(state_path: Path) -> tuple[Path, dict[str, Any]]:
    requested_state_path = state_path.expanduser()
    if requested_state_path.is_symlink():
        raise CandidateError("candidate state path must not be a symlink")
    state_path = requested_state_path.resolve(strict=True)
    isolated_root = state_path.parent
    if (
        state_path.name != "state.json"
        or isolated_root.parent != Path("/private/tmp")
        or not TEMP_ROOT_PATTERN.fullmatch(isolated_root.name)
        or isolated_root.is_symlink()
        or isolated_root.stat().st_uid != os.getuid()
        or stat.S_IMODE(isolated_root.stat().st_mode) != 0o700
        or state_path.stat().st_uid != os.getuid()
        or stat.S_IMODE(state_path.stat().st_mode) != 0o600
    ):
        raise CandidateError("state path is outside an owned Stage 1 temp root")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("schema") != STATE_SCHEMA:
        raise CandidateError("candidate state schema mismatch")
    if Path(str(state.get("isolated_root"))).resolve() != isolated_root:
        raise CandidateError("candidate state root mismatch")
    if Path(str(state.get("candidate_app"))).resolve() != isolated_root / "PFI.app":
        raise CandidateError("candidate App path mismatch")
    root_metadata = isolated_root.stat()
    if (
        state.get("isolated_root_st_dev") != root_metadata.st_dev
        or state.get("isolated_root_st_ino") != root_metadata.st_ino
    ):
        raise CandidateError("candidate root identity mismatch")
    return isolated_root, state


def _read_active_marker(marker_path: Path) -> dict[str, str]:
    if not marker_path.is_file() or marker_path.is_symlink():
        raise CandidateError("active marker is unavailable")
    values: dict[str, str] = {}
    for line in marker_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if not separator or not key or key in values:
            raise CandidateError("active marker format is invalid")
        values[key] = value
    return values


def _process_cwd(pid: int) -> str:
    completed = _run("lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn", check=False)
    for line in completed.stdout.splitlines():
        if line.startswith("n"):
            return line[1:]
    return ""


def _pid_exists(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_for_pid_exit(pid: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return True
        time.sleep(0.1)
    return False


def _port_has_listener(port: int) -> bool:
    completed = _run(
        "lsof",
        "-nP",
        f"-iTCP:{port}",
        "-sTCP:LISTEN",
        "-Fn",
        check=False,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise CandidateError("listener query failed")


def _process_tcp_listener_endpoints(pid: int) -> set[tuple[str, int]]:
    if pid <= 1:
        return set()
    completed = _run(
        "lsof",
        "-nP",
        "-a",
        "-p",
        str(pid),
        "-iTCP",
        "-sTCP:LISTEN",
        "-Fn",
        check=False,
    )
    if completed.returncode == 1:
        return set()
    if completed.returncode != 0:
        raise CandidateError("process listener census failed")
    endpoints: set[tuple[str, int]] = set()
    for line in completed.stdout.splitlines():
        if not line.startswith("n"):
            continue
        match = re.fullmatch(r"n(.+):(\d+)", line)
        if not match:
            raise CandidateError("process listener endpoint is invalid")
        endpoints.add((match.group(1), int(match.group(2))))
    return endpoints


def _process_tcp_listen_ports(pid: int) -> set[int]:
    return {port for _address, port in _process_tcp_listener_endpoints(pid)}


def _process_group_pids(process_group_id: int) -> set[int]:
    if process_group_id <= 1:
        return set()
    completed = _run("ps", "-axo", "pid=,pgid=", check=False)
    if completed.returncode != 0:
        raise CandidateError("process group census failed")
    members: set[int] = set()
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2 or not all(field.isdigit() for field in fields):
            continue
        pid, pgid = (int(field) for field in fields)
        if pgid == process_group_id:
            members.add(pid)
    return members


def _process_group_tcp_listeners(
    process_group_id: int,
) -> set[tuple[int, str, int]]:
    return {
        (pid, address, port)
        for pid in _process_group_pids(process_group_id)
        for address, port in _process_tcp_listener_endpoints(pid)
    }


def _listener_endpoint_set_sha256(records: set[tuple[int, str, int]]) -> str:
    payload = "".join(
        f"{pid}:{address}:{port}\n" for pid, address, port in sorted(records)
    )
    return _sha256_bytes(payload.encode("ascii"))


def _process_tree_pids(root_pids: set[int]) -> set[int]:
    roots = {pid for pid in root_pids if pid > 1}
    if not roots:
        return set()
    completed = _run("ps", "-axo", "pid=,ppid=", check=False)
    if completed.returncode != 0:
        raise CandidateError("process tree census failed")
    children: dict[int, set[int]] = {}
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2 or not all(field.isdigit() for field in fields):
            continue
        pid, parent = (int(field) for field in fields)
        children.setdefault(parent, set()).add(pid)
    tree = set(roots)
    pending = list(roots)
    while pending:
        parent = pending.pop()
        for child in children.get(parent, set()):
            if child not in tree:
                tree.add(child)
                pending.append(child)
    return tree


def _process_tree_tcp_listeners(root_pids: set[int]) -> set[tuple[int, int]]:
    tree = _process_tree_pids(root_pids)
    return {
        (pid, port)
        for pid in tree
        for port in _process_tcp_listen_ports(pid)
    }


def _listener_owner_port_set_sha256(records: set[tuple[int, int]]) -> str:
    payload = "".join(f"{pid}:{port}\n" for pid, port in sorted(records))
    return _sha256_bytes(payload.encode("ascii"))


def _process_identity_digest(pid: int) -> str:
    if not _pid_exists(pid):
        return ""
    completed = _run(
        "ps",
        "-p",
        str(pid),
        "-o",
        "lstart=",
        "-o",
        "command=",
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return ""
    cwd = _process_cwd(pid)
    return _sha256_bytes(f"{completed.stdout.strip()}\0{cwd}".encode("utf-8"))


def _process_tree_identity_records(root_pids: set[int]) -> dict[int, str]:
    tree = _process_tree_pids(root_pids)
    records = {pid: _process_identity_digest(pid) for pid in tree}
    if any(not digest for digest in records.values()):
        raise CandidateError("process tree identity census changed during inspection")
    return records


def _process_group_identity_records(process_group_id: int) -> dict[int, str]:
    members = _process_group_pids(process_group_id)
    records = {pid: _process_identity_digest(pid) for pid in members}
    if any(not digest for digest in records.values()):
        raise CandidateError("process group identity census changed during inspection")
    return records


def _process_group_id(pid: int) -> int | None:
    completed = _run("ps", "-p", str(pid), "-o", "pgid=", check=False)
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value.isdigit():
        return None
    return int(value)


def _process_tree_identity_sha256(records: dict[int, str]) -> str:
    payload = "".join(f"{digest}\n" for digest in sorted(records.values()))
    return _sha256_bytes(payload.encode("ascii"))


def _wait_for_port_release(port: int, *, timeout_seconds: float = 15) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if not _port_has_listener(port):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)


def _process_owns_candidate(state: dict[str, Any], pid: int) -> tuple[bool, str]:
    if pid <= 1:
        return False, ""
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False, ""
    command = _run(
        "ps",
        "-p",
        str(pid),
        "-o",
        "lstart=",
        "-o",
        "command=",
        check=False,
    ).stdout.strip()
    cwd = _process_cwd(pid)
    project_root = str(state["project_root"])
    port = int(state["streamlit_port"])
    wrapper_path = str(
        Path(project_root) / "scripts" / "v025" / "run_streamlit_with_release_cache.py"
    )
    app_entry = "src/pfi_os/app/streamlit_app.py"
    listener_endpoints = _process_tcp_listener_endpoints(pid)
    app_endpoint = ("127.0.0.1", port)
    runtime_endpoints = listener_endpoints - {app_endpoint}
    runtime_port = next(iter(runtime_endpoints))[1] if len(runtime_endpoints) == 1 else 0
    owned = (
        bool(re.search(rf"(?:^|\s){re.escape(wrapper_path)}(?=\s|$)", command))
        and bool(re.search(rf"(?:^|\s){re.escape(app_entry)}(?=\s|$)", command))
        and _command_option_matches(command, "--server.port", port)
        and cwd == project_root
        and app_endpoint in listener_endpoints
        and len(listener_endpoints) == 2
        and len(runtime_endpoints) == 1
        and all(address == "127.0.0.1" for address, _listener_port in listener_endpoints)
        and runtime_port not in {0, port, int(state["heartbeat_port"]), 8501, 8502, 8766}
    )
    digest = (
        _sha256_bytes(
            f"{command}\0{cwd}\0{port}\0{runtime_port}".encode("utf-8")
        )
        if owned
        else ""
    )
    return owned, digest


def _process_owns_launcher(state: dict[str, Any], launcher_pid: int) -> tuple[bool, str]:
    if not _pid_exists(launcher_pid):
        return False, ""
    command = _run(
        "ps",
        "-p",
        str(launcher_pid),
        "-o",
        "lstart=",
        "-o",
        "command=",
        check=False,
    ).stdout.strip()
    cwd = _process_cwd(launcher_pid)
    project_root = str(state["project_root"])
    launcher_path = str(Path(project_root) / "StartPFI.command")
    owned = (
        bool(
            re.search(
                rf"(?:^|\s){re.escape(launcher_path)}(?=\s|$)",
                command,
            )
        )
        and cwd == project_root
    )
    digest = _sha256_bytes(f"{command}\0{cwd}".encode("utf-8")) if owned else ""
    return owned, digest


def _command_option_matches(command: str, option: str, value: int) -> bool:
    return bool(
        re.search(
            rf"(?:^|\s){re.escape(option)}(?:=|\s+){value}(?=\s|$)",
            command,
        )
    )


def _process_owns_monitor(
    state: dict[str, Any],
    monitor_pid: int,
    streamlit_pid: int,
) -> tuple[bool, str]:
    if not _pid_exists(monitor_pid):
        return False, ""
    command = _run(
        "ps",
        "-p",
        str(monitor_pid),
        "-o",
        "lstart=",
        "-o",
        "command=",
        check=False,
    ).stdout.strip()
    cwd = _process_cwd(monitor_pid)
    project_root = str(state["project_root"])
    monitor_path = str(
        Path(project_root) / "src" / "pfi_os" / "system" / "shutdown_monitor.py"
    )
    heartbeat_port = int(state["heartbeat_port"])
    owned = (
        bool(
            re.search(
                rf"(?:^|\s){re.escape(monitor_path)}(?=\s|$)",
                command,
            )
        )
        and _command_option_matches(command, "--port", heartbeat_port)
        and _command_option_matches(command, "--streamlit-pid", streamlit_pid)
        and cwd == project_root
        and _process_tcp_listener_endpoints(monitor_pid)
        == {("127.0.0.1", heartbeat_port)}
    )
    digest = (
        _sha256_bytes(
            f"{command}\0{cwd}\0{heartbeat_port}\0{streamlit_pid}".encode("utf-8")
        )
        if owned
        else ""
    )
    return owned, digest


def _marker_matches_state(marker: dict[str, str], state: dict[str, Any]) -> bool:
    expected = {
        "PFI_ACTIVE_CANDIDATE_MODE": "1",
        "PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256": str(state["candidate_app_path_sha256"]),
        "PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256": str(state["candidate_executable_sha256"]),
        "PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256": str(state["candidate_bundle_sha256"]),
        "PFI_ACTIVE_PORT": str(state["streamlit_port"]),
    }
    return all(marker.get(key) == value for key, value in expected.items())


def inspect_candidate(state_path: Path, *, timeout_seconds: float = 120) -> dict[str, object]:
    isolated_root, _state = _validate_state_path(state_path)
    if (isolated_root / FINALIZING_TOMBSTONE_NAME).exists():
        raise CandidateError("candidate finalization is already active")
    lock_path = isolated_root / ".pfi_stage1_finalize.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise CandidateError("candidate finalization is already active") from error
        return _inspect_candidate_locked(state_path, timeout_seconds=timeout_seconds)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _inspect_candidate_locked(
    state_path: Path, *, timeout_seconds: float = 120
) -> dict[str, object]:
    """Wait for and validate the real LaunchServices-started candidate marker."""

    isolated_root, state = _validate_state_path(state_path)
    marker_path = isolated_root / "runtime" / "pfi_active_service.env"
    deadline = time.monotonic() + timeout_seconds
    while not marker_path.is_file() and time.monotonic() < deadline:
        time.sleep(0.25)
    marker = _read_active_marker(marker_path)
    if not _marker_matches_state(marker, state):
        raise CandidateError("LaunchServices active marker does not match the prepared candidate")
    if marker.get("PFI_ACTIVE_HEARTBEAT_PORT") != str(state["heartbeat_port"]):
        raise CandidateError("LaunchServices active marker heartbeat port does not match the candidate")
    raw_pid = marker.get("PFI_ACTIVE_PID", "")
    if not raw_pid.isdigit():
        raise CandidateError("LaunchServices active marker PID is invalid")
    pid = int(raw_pid)
    owned, process_digest = _process_owns_candidate(state, pid)
    if not owned:
        raise CandidateError("LaunchServices-started process ownership could not be proven")
    raw_runtime_api_port = marker.get("PFI_ACTIVE_RUNTIME_API_PORT", "")
    if not raw_runtime_api_port.isdigit():
        raise CandidateError("LaunchServices active marker runtime API port is invalid")
    runtime_api_port = int(raw_runtime_api_port)
    if runtime_api_port in {
        int(state["streamlit_port"]),
        int(state["heartbeat_port"]),
        8501,
        8502,
        8766,
    }:
        raise CandidateError("LaunchServices active marker runtime API port is not isolated")
    raw_monitor_pid = marker.get("PFI_ACTIVE_MONITOR_PID", "")
    if not raw_monitor_pid.isdigit():
        raise CandidateError("LaunchServices active marker monitor PID is invalid")
    monitor_pid = int(raw_monitor_pid)
    monitor_owned, monitor_digest = _process_owns_monitor(state, monitor_pid, pid)
    if not monitor_owned:
        raise CandidateError("LaunchServices-started monitor ownership could not be proven")
    raw_launcher_pid = marker.get("PFI_ACTIVE_LAUNCHER_PID", "")
    if not raw_launcher_pid.isdigit():
        raise CandidateError("LaunchServices active marker launcher PID is invalid")
    launcher_pid = int(raw_launcher_pid)
    launcher_owned, launcher_digest = _process_owns_launcher(state, launcher_pid)
    if not launcher_owned:
        raise CandidateError("LaunchServices-started launcher ownership could not be proven")
    raw_process_group_id = marker.get("PFI_ACTIVE_PROCESS_GROUP_ID", "")
    if not raw_process_group_id.isdigit():
        raise CandidateError("LaunchServices active marker process group is invalid")
    process_group_id = int(raw_process_group_id)
    if process_group_id != launcher_pid:
        raise CandidateError("LaunchServices active marker process group is not launcher-owned")
    if any(
        _process_group_id(member_pid) != process_group_id
        for member_pid in (launcher_pid, pid, monitor_pid)
    ):
        raise CandidateError("LaunchServices-started processes do not share the candidate group")
    process_group_records = _process_group_identity_records(process_group_id)
    if set(process_group_records) != {launcher_pid, pid, monitor_pid}:
        raise CandidateError("LaunchServices-started candidate process group has an unexpected member")
    process_tree_records = _process_tree_identity_records({launcher_pid})
    if pid not in process_tree_records or monitor_pid not in process_tree_records:
        raise CandidateError("LaunchServices-started processes are not owned by the launcher tree")
    streamlit_listener_endpoints = _process_tcp_listener_endpoints(pid)
    monitor_listener_endpoints = _process_tcp_listener_endpoints(monitor_pid)
    process_group_listeners = _process_group_tcp_listeners(process_group_id)
    listener_owner_ports = {
        (owner_pid, port)
        for owner_pid, _address, port in process_group_listeners
    }
    expected_owner_ports = {
        (pid, int(state["streamlit_port"])),
        (pid, runtime_api_port),
        (monitor_pid, int(state["heartbeat_port"])),
    }
    if streamlit_listener_endpoints != {
        ("127.0.0.1", int(state["streamlit_port"])),
        ("127.0.0.1", runtime_api_port),
    }:
        raise CandidateError("LaunchServices-started candidate has an unexpected listener")
    if monitor_listener_endpoints != {("127.0.0.1", int(state["heartbeat_port"]))}:
        raise CandidateError("LaunchServices-started monitor has an unexpected listener")
    expected_group_listeners = {
        (pid, "127.0.0.1", int(state["streamlit_port"])),
        (pid, "127.0.0.1", runtime_api_port),
        (monitor_pid, "127.0.0.1", int(state["heartbeat_port"])),
    }
    if process_group_listeners != expected_group_listeners:
        raise CandidateError("LaunchServices-started candidate process group has an unexpected listener")
    url = f"http://127.0.0.1:{int(state['streamlit_port'])}"
    try:
        with urlopen(f"{url}/_stcore/health", timeout=3) as response:
            healthy = response.status == 200
    except URLError:
        healthy = False
    if not healthy:
        raise CandidateError("LaunchServices-started candidate health check failed")
    heartbeat_url = f"http://127.0.0.1:{int(state['heartbeat_port'])}/heartbeat"
    try:
        with urlopen(heartbeat_url, timeout=3) as response:
            heartbeat_ready = response.status == 204
    except URLError:
        heartbeat_ready = False
    if not heartbeat_ready:
        raise CandidateError("LaunchServices-started shutdown monitor heartbeat failed")
    runtime_api_url = f"http://127.0.0.1:{runtime_api_port}"
    try:
        with urlopen(f"{runtime_api_url}/health", timeout=3) as response:
            runtime_api_ready = response.status == 200
    except URLError:
        runtime_api_ready = False
    if not runtime_api_ready:
        raise CandidateError("LaunchServices-started runtime API health check failed")

    sanitized = {
        "schema": "PFIV025Stage1Phase13CandidateInspectionV1",
        "launchservices_started": True,
        "candidate_mode": True,
        "candidate_path_symbolic": "${ISOLATED_ROOT}/PFI.app",
        "streamlit_port": int(state["streamlit_port"]),
        "runtime_api_port": runtime_api_port,
        "heartbeat_port": int(state["heartbeat_port"]),
        "pid_observed": True,
        "process_identity_sha256": process_digest,
        "monitor_pid_observed": True,
        "monitor_identity_sha256": monitor_digest,
        "launcher_pid_observed": True,
        "launcher_identity_sha256": launcher_digest,
        "launcher_process_tree_verified": True,
        "process_group_verified": True,
        "process_group_member_count": len(process_group_records),
        "process_group_identity_sha256": _process_tree_identity_sha256(
            process_group_records
        ),
        "process_tree_member_count": len(process_tree_records),
        "process_tree_identity_sha256": _process_tree_identity_sha256(
            process_tree_records
        ),
        "health_ready": True,
        "runtime_api_ready": True,
        "heartbeat_ready": True,
        "streamlit_listener_set_verified": True,
        "streamlit_listener_count": len(streamlit_listener_endpoints),
        "streamlit_listener_set_sha256": _sha256_bytes(
            "\0".join(
                f"{address}:{port}"
                for address, port in sorted(streamlit_listener_endpoints)
            ).encode("ascii")
        ),
        "monitor_listener_set_verified": True,
        "monitor_listener_count": len(monitor_listener_endpoints),
        "monitor_listener_set_sha256": _sha256_bytes(
            "\0".join(
                f"{address}:{port}"
                for address, port in sorted(monitor_listener_endpoints)
            ).encode("ascii")
        ),
        "listener_owner_port_set_verified": True,
        "listener_owner_port_count": len(listener_owner_ports),
        "listener_owner_port_set_sha256": _listener_owner_port_set_sha256(
            listener_owner_ports
        ),
        "listener_endpoint_set_verified": True,
        "listener_endpoint_count": len(process_group_listeners),
        "listener_endpoint_set_sha256": _listener_endpoint_set_sha256(
            process_group_listeners
        ),
        "launchservices_registration_verified": state.get(
            "launchservices_registration_verified"
        )
        is True,
        "candidate_app_path_sha256": state["candidate_app_path_sha256"],
        "candidate_executable_sha256": state["candidate_executable_sha256"],
        "candidate_bundle_sha256": state["candidate_bundle_sha256"],
    }
    state["observed_pid"] = pid
    state["observed_monitor_pid"] = monitor_pid
    state["observed_launcher_pid"] = launcher_pid
    state["observed_process_group_id"] = process_group_id
    state["observed_runtime_api_port"] = runtime_api_port
    state["observed_process_group"] = {
        str(member_pid): identity
        for member_pid, identity in sorted(process_group_records.items())
    }
    state["observed_process_tree"] = {
        str(member_pid): identity
        for member_pid, identity in sorted(process_tree_records.items())
    }
    state["inspection"] = sanitized
    state["lifecycle_state"] = "INSPECTED"
    _write_state(Path(state["state_path"]), state)
    return sanitized


def _stop_owned_process(state: dict[str, Any], marker: dict[str, str] | None) -> tuple[str, bool]:
    raw_pid = ""
    if marker:
        raw_pid = marker.get("PFI_ACTIVE_PID", "")
    if not raw_pid and isinstance(state.get("observed_pid"), int):
        raw_pid = str(state["observed_pid"])
    if not raw_pid.isdigit():
        return "not_observed", False
    pid = int(raw_pid)
    owned, process_digest = _process_owns_candidate(state, pid)
    if not owned:
        inspection = state.get("inspection")
        if (
            isinstance(inspection, dict)
            and inspection.get("launchservices_started") is True
            and (
                not _pid_exists(pid)
                or _wait_for_pid_exit(pid, timeout_seconds=2)
            )
        ):
            return "observed_exited_before_signal", True
        return "not_owned_not_signaled", True
    inspection = state.get("inspection")
    if isinstance(inspection, dict):
        expected_digest = inspection.get("process_identity_sha256")
        if isinstance(expected_digest, str) and expected_digest != process_digest:
            return "identity_changed_not_signaled", True
    owned_again, second_digest = _process_owns_candidate(state, pid)
    if not owned_again or second_digest != process_digest:
        return "identity_changed_not_signaled", True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return "owned_exited_before_signal", True
    if _wait_for_pid_exit(pid, timeout_seconds=10):
        return "owned_stopped", True
    owned, final_digest = _process_owns_candidate(state, pid)
    if not owned and not _pid_exists(pid):
        return "owned_stopped", True
    if owned and final_digest == process_digest:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return "owned_stopped", True
        if _wait_for_pid_exit(pid, timeout_seconds=5):
            return "owned_stopped", True
        return "owned_kill_timeout", True
    return "identity_changed_not_signaled", True


def _stop_owned_monitor(
    state: dict[str, Any],
    marker: dict[str, str] | None,
) -> tuple[str, bool, bool]:
    raw_pid = marker.get("PFI_ACTIVE_MONITOR_PID", "") if marker else ""
    if not raw_pid and isinstance(state.get("observed_monitor_pid"), int):
        raw_pid = str(state["observed_monitor_pid"])
    if not raw_pid.isdigit():
        return "not_observed", False, True
    monitor_pid = int(raw_pid)
    if not _pid_exists(monitor_pid):
        return "observed_exited_before_signal", True, True
    if _wait_for_pid_exit(monitor_pid, timeout_seconds=5):
        return "owned_exited_after_streamlit", True, True

    streamlit_pid_value = state.get("observed_pid")
    if not isinstance(streamlit_pid_value, int) and marker:
        raw_streamlit_pid = marker.get("PFI_ACTIVE_PID", "")
        streamlit_pid_value = int(raw_streamlit_pid) if raw_streamlit_pid.isdigit() else None
    if not isinstance(streamlit_pid_value, int):
        return "streamlit_pid_not_observed", True, False

    owned, monitor_digest = _process_owns_monitor(state, monitor_pid, streamlit_pid_value)
    if not owned:
        return "not_owned_not_signaled", True, False
    inspection = state.get("inspection")
    if isinstance(inspection, dict):
        expected_digest = inspection.get("monitor_identity_sha256")
        if isinstance(expected_digest, str) and expected_digest != monitor_digest:
            return "identity_changed_not_signaled", True, False

    owned_again, second_digest = _process_owns_monitor(state, monitor_pid, streamlit_pid_value)
    if not owned_again and not _pid_exists(monitor_pid):
        return "owned_exited_after_streamlit", True, True
    if not owned_again or second_digest != monitor_digest:
        return "identity_changed_not_signaled", True, False
    try:
        os.kill(monitor_pid, signal.SIGTERM)
    except ProcessLookupError:
        return "owned_exited_before_signal", True, True
    if _wait_for_pid_exit(monitor_pid, timeout_seconds=5):
        return "owned_stopped", True, True
    owned_again, final_digest = _process_owns_monitor(state, monitor_pid, streamlit_pid_value)
    if not owned_again and not _pid_exists(monitor_pid):
        return "owned_stopped", True, True
    if not owned_again or final_digest != monitor_digest:
        return "identity_changed_not_signaled", True, False
    try:
        os.kill(monitor_pid, signal.SIGKILL)
    except ProcessLookupError:
        return "owned_stopped", True, True
    if _wait_for_pid_exit(monitor_pid, timeout_seconds=5):
        return "owned_stopped", True, True
    return "owned_kill_timeout", True, False


def _wait_for_process_group_empty(
    process_group_id: int, *, timeout_seconds: float = 10
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if not _process_group_pids(process_group_id):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)


def _stop_owned_process_group(
    state: dict[str, Any], marker: dict[str, str]
) -> tuple[str, dict[int, str], bool]:
    raw_group = marker.get("PFI_ACTIVE_PROCESS_GROUP_ID", "")
    raw_launcher = marker.get("PFI_ACTIVE_LAUNCHER_PID", "")
    raw_streamlit = marker.get("PFI_ACTIVE_PID", "")
    raw_monitor = marker.get("PFI_ACTIVE_MONITOR_PID", "")
    if not all(value.isdigit() for value in (raw_group, raw_launcher, raw_streamlit, raw_monitor)):
        return "group_identity_unavailable", {}, False
    process_group_id = int(raw_group)
    launcher_pid = int(raw_launcher)
    streamlit_pid = int(raw_streamlit)
    monitor_pid = int(raw_monitor)
    if process_group_id != launcher_pid or process_group_id <= 1:
        return "group_identity_invalid", {}, False
    launcher_owned, _launcher_digest = _process_owns_launcher(state, launcher_pid)
    if not launcher_owned or _process_group_id(launcher_pid) != process_group_id:
        return "group_not_owned_not_signaled", {}, False
    records = _process_group_identity_records(process_group_id)
    if not {launcher_pid, streamlit_pid, monitor_pid}.issubset(records):
        return "group_membership_invalid_not_signaled", records, False
    second_records = _process_group_identity_records(process_group_id)
    if second_records != records:
        return "group_identity_changed_not_signaled", records, False
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        return "owned_group_exited_before_signal", records, True
    if _wait_for_process_group_empty(process_group_id, timeout_seconds=10):
        return "owned_group_stopped", records, True
    remaining = _process_group_identity_records(process_group_id)
    if not remaining or any(
        pid in records and records[pid] != identity
        for pid, identity in remaining.items()
    ):
        return "group_identity_changed_not_signaled", records, False
    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        return "owned_group_stopped", records, True
    if _wait_for_process_group_empty(process_group_id, timeout_seconds=5):
        return "owned_group_stopped", records, True
    return "owned_group_kill_timeout", records, False


def _launcher_pid_from_lock(isolated_root: Path) -> int | None:
    lock_pid = isolated_root / "runtime" / "pfi_launch.lockdir" / "pid"
    if not lock_pid.exists():
        return None
    if lock_pid.is_symlink() or not lock_pid.is_file():
        raise CandidateError("candidate launch lock is invalid")
    raw_pid = lock_pid.read_text(encoding="ascii").strip()
    if not raw_pid.isdigit() or int(raw_pid) <= 1:
        raise CandidateError("candidate launch lock PID is invalid")
    return int(raw_pid)


def _stop_owned_launcher_group(
    state: dict[str, Any], launcher_pid: int
) -> tuple[str, dict[int, str], bool]:
    launcher_owned, _launcher_digest = _process_owns_launcher(state, launcher_pid)
    process_group_id = _process_group_id(launcher_pid)
    if not launcher_owned or process_group_id != launcher_pid:
        return "launcher_group_not_owned_not_signaled", {}, False
    records = _process_group_identity_records(process_group_id)
    if launcher_pid not in records:
        return "launcher_group_identity_invalid", records, False
    second_records = _process_group_identity_records(process_group_id)
    if second_records != records:
        return "launcher_group_identity_changed_not_signaled", records, False
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        return "owned_launcher_group_exited_before_signal", records, True
    if _wait_for_process_group_empty(process_group_id, timeout_seconds=10):
        return "owned_launcher_group_stopped", records, True
    remaining = _process_group_identity_records(process_group_id)
    if not remaining or any(
        pid in records and records[pid] != identity
        for pid, identity in remaining.items()
    ):
        return "launcher_group_identity_changed_not_signaled", records, False
    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        return "owned_launcher_group_stopped", records, True
    if _wait_for_process_group_empty(process_group_id, timeout_seconds=5):
        return "owned_launcher_group_stopped", records, True
    return "owned_launcher_group_kill_timeout", records, False


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def _wait_for_process_tree_exit(
    records: dict[int, str], *, timeout_seconds: float = 10
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if all(_process_identity_digest(pid) != digest for pid, digest in records.items()):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)


def _validate_external_evidence_directory(
    evidence_dir: Path, isolated_root: Path
) -> Path:
    requested = evidence_dir.expanduser()
    if requested.is_symlink():
        raise CandidateError("evidence directory is not an owned external staging root")
    try:
        resolved = requested.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as error:
        raise CandidateError(
            "evidence directory is not an owned external staging root"
        ) from error
    if (
        not resolved.is_dir()
        or resolved.parent != Path("/private/tmp")
        or not EVIDENCE_ROOT_PATTERN.fullmatch(resolved.name)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or resolved == isolated_root
        or isolated_root in resolved.parents
    ):
        raise CandidateError("evidence directory is not an owned external staging root")
    return resolved


def _state_process_tree_records(state: dict[str, Any]) -> dict[int, str]:
    raw_process_tree = state.get("observed_process_tree")
    if raw_process_tree is None:
        return {}
    if not isinstance(raw_process_tree, dict):
        raise CandidateError("process tree identity is unavailable")
    records = {
        int(raw_pid): str(identity)
        for raw_pid, identity in raw_process_tree.items()
        if str(raw_pid).isdigit() and re.fullmatch(r"[0-9a-f]{64}", str(identity))
    }
    if len(records) != len(raw_process_tree):
        raise CandidateError("process tree identity is invalid")
    return records


def _state_process_group_records(state: dict[str, Any]) -> dict[int, str]:
    raw_process_group = state.get("observed_process_group")
    if raw_process_group is None:
        return {}
    if not isinstance(raw_process_group, dict):
        raise CandidateError("process group identity is unavailable")
    records = {
        int(raw_pid): str(identity)
        for raw_pid, identity in raw_process_group.items()
        if str(raw_pid).isdigit() and re.fullmatch(r"[0-9a-f]{64}", str(identity))
    }
    if len(records) != len(raw_process_group):
        raise CandidateError("process group identity is invalid")
    return records


def _runtime_cleanup_checkpoint(state: dict[str, Any]) -> dict[str, Any] | None:
    checkpoint = state.get("runtime_cleanup_checkpoint")
    if checkpoint is None:
        return None
    required_true = {
        "process_tree_identity_unchanged_before_cleanup",
        "process_group_identity_unchanged_before_cleanup",
        "listener_owner_port_set_unchanged_before_cleanup",
        "listener_endpoint_set_unchanged_before_cleanup",
        "process_tree_cleanup_verified",
        "process_group_cleanup_verified",
        "runtime_process_cleanup_verified",
        "shutdown_monitor_stopped",
        "launcher_stopped",
        "launch_lock_quiescent",
        "streamlit_port_released_before_cleanup",
        "runtime_api_port_released_before_cleanup",
        "heartbeat_port_released_before_cleanup",
    }
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("schema") != RUNTIME_CLEANUP_CHECKPOINT_SCHEMA
        or any(checkpoint.get(key) is not True for key in required_true)
        or checkpoint.get("launchservices_runtime_verified")
        is not (
            isinstance(state.get("inspection"), dict)
            and state["inspection"].get("launchservices_started") is True
        )
        or not isinstance(checkpoint.get("process_stop_status"), str)
        or not isinstance(checkpoint.get("monitor_stop_status"), str)
        or checkpoint.get("process_tree_identity_sha256")
        != _process_tree_identity_sha256(_state_process_tree_records(state))
        or checkpoint.get("process_group_identity_sha256")
        != _process_tree_identity_sha256(_state_process_group_records(state))
    ):
        raise CandidateError("runtime cleanup checkpoint is invalid")
    return checkpoint


def _launchservices_cleanup_checkpoint(state: dict[str, Any]) -> dict[str, Any] | None:
    checkpoint = state.get("launchservices_cleanup_checkpoint")
    if checkpoint is None:
        return None
    required = {
        "schema",
        "unregister_command_required",
        "unregister_returncode",
        "launchservices_before_unregister_query_ok",
        "launchservices_before_unregister_record_count",
        "launchservices_before_unregister_record_sha256",
        "launchservices_post_unregister_absent",
        "launchservices_post_unregister_record_count",
        "launchservices_post_unregister_record_sha256",
    }
    if (
        not isinstance(checkpoint, dict)
        or set(checkpoint) != required
        or checkpoint.get("schema")
        != "PFIV025Stage1Phase13LaunchServicesCheckpointV1"
        or checkpoint.get("unregister_command_required") is not True
        or checkpoint.get("unregister_returncode") != 0
        or checkpoint.get("launchservices_before_unregister_query_ok") is not True
        or not isinstance(
            checkpoint.get("launchservices_before_unregister_record_count"), int
        )
        or checkpoint["launchservices_before_unregister_record_count"] < 1
        or not HEX64_PATTERN.fullmatch(
            str(checkpoint.get("launchservices_before_unregister_record_sha256", ""))
        )
        or checkpoint.get("launchservices_post_unregister_absent") is not True
        or checkpoint.get("launchservices_post_unregister_record_count") != 0
        or not HEX64_PATTERN.fullmatch(
            str(checkpoint.get("launchservices_post_unregister_record_sha256", ""))
        )
    ):
        raise CandidateError("LaunchServices cleanup checkpoint is invalid")
    return checkpoint


def _candidate_root_removal_safe(
    *,
    shutdown_monitor_stopped: bool,
    streamlit_port_released: bool,
    runtime_api_port_released: bool,
    heartbeat_port_released: bool,
    launchservices_absent: bool,
    runtime_cleanup_verified: bool,
    listener_set_unchanged: bool,
    process_tree_cleanup_verified: bool,
    evidence_records_written: bool,
) -> bool:
    return all(
        (
            shutdown_monitor_stopped,
            streamlit_port_released,
            runtime_api_port_released,
            heartbeat_port_released,
            launchservices_absent,
            runtime_cleanup_verified,
            listener_set_unchanged,
            process_tree_cleanup_verified,
            evidence_records_written,
        )
    )


def _quarantine_and_remove_root(
    isolated_root: Path, *, expected_device: int, expected_inode: int
) -> bool:
    parent = Path("/private/tmp")
    if isolated_root.parent != parent:
        raise CandidateError("candidate root parent changed before deletion")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    parent_descriptor = os.open(parent, os.O_RDONLY | directory_flag)
    quarantine_name = (
        f".{isolated_root.name}.delete-{os.getpid()}-{time.time_ns()}"
    )
    renamed = False
    try:
        metadata = os.stat(
            isolated_root.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if metadata.st_dev != expected_device or metadata.st_ino != expected_inode:
            raise CandidateError("candidate root identity changed before deletion")
        os.rename(
            isolated_root.name,
            quarantine_name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        renamed = True
        quarantine_metadata = os.stat(
            quarantine_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            quarantine_metadata.st_dev != expected_device
            or quarantine_metadata.st_ino != expected_inode
        ):
            raise CandidateError("candidate quarantine identity mismatch")
        quarantine_path = parent / quarantine_name
        shutil.rmtree(quarantine_path)
        if isolated_root.exists():
            raise CandidateError("candidate root path was reused during deletion")
        return not quarantine_path.exists()
    except Exception:
        if renamed:
            quarantine_path = parent / quarantine_name
            if quarantine_path.exists() and not isolated_root.exists():
                try:
                    os.rename(
                        quarantine_name,
                        isolated_root.name,
                        src_dir_fd=parent_descriptor,
                        dst_dir_fd=parent_descriptor,
                    )
                except OSError:
                    pass
        raise
    finally:
        os.close(parent_descriptor)


def _publish_finalizing_tombstone(isolated_root: Path) -> Path:
    tombstone = isolated_root / FINALIZING_TOMBSTONE_NAME
    if os.path.lexists(tombstone):
        metadata = tombstone.lstat()
        if (
            tombstone.is_symlink()
            or not tombstone.is_file()
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or tombstone.read_bytes() != FINALIZING_TOMBSTONE_PAYLOAD
        ):
            raise CandidateError("candidate finalization tombstone is invalid")
        return tombstone
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(tombstone, flags, 0o600)
    complete = False
    try:
        os.fchmod(descriptor, 0o600)
        written = os.write(descriptor, FINALIZING_TOMBSTONE_PAYLOAD)
        if written != len(FINALIZING_TOMBSTONE_PAYLOAD):
            raise CandidateError("candidate finalization tombstone write failed")
        os.fsync(descriptor)
        complete = True
    finally:
        os.close(descriptor)
        if not complete:
            tombstone.unlink(missing_ok=True)
    return tombstone


def finalize_candidate(state_path: Path, evidence_dir: Path) -> dict[str, object]:
    isolated_root, _state = _validate_state_path(state_path)
    lock_path = isolated_root / ".pfi_stage1_finalize.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise CandidateError("candidate finalization is already active") from error
        return _finalize_candidate_locked(state_path, evidence_dir)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _finalize_candidate_locked(
    state_path: Path, evidence_dir: Path
) -> dict[str, object]:
    """Stop the owned candidate group, persist retry checkpoints, then remove it."""

    isolated_root, state = _validate_state_path(state_path)
    candidate_app = isolated_root / "PFI.app"
    _publish_finalizing_tombstone(isolated_root)
    finalization_error = False

    resolved_evidence_dir: Path | None = None
    try:
        resolved_evidence_dir = _validate_external_evidence_directory(
            evidence_dir, isolated_root
        )
    except Exception:
        finalization_error = True

    marker_path = isolated_root / "runtime" / "pfi_active_service.env"
    marker: dict[str, str] | None = None
    marker_file_observed = marker_path.exists()
    if marker_file_observed:
        try:
            marker = _read_active_marker(marker_path)
            if not _marker_matches_state(marker, state):
                raise CandidateError("active marker identity mismatch")
        except Exception:
            marker = None
            finalization_error = True

    inspection = state.get("inspection")
    launchservices_runtime_verified = (
        isinstance(inspection, dict) and inspection.get("launchservices_started") is True
    )
    observed_tree: dict[int, str] = {}
    observed_group: dict[int, str] = {}
    try:
        observed_tree = _state_process_tree_records(state)
        observed_group = _state_process_group_records(state)
    except Exception:
        finalization_error = True

    runtime_checkpoint: dict[str, Any] | None = None
    runtime_cleanup_checkpoint_reused = False
    try:
        runtime_checkpoint = _runtime_cleanup_checkpoint(state)
        runtime_cleanup_checkpoint_reused = runtime_checkpoint is not None
    except Exception:
        finalization_error = True

    launch_lock_pid: int | None = None
    try:
        launch_lock_pid = _launcher_pid_from_lock(isolated_root)
    except Exception:
        finalization_error = True
    lock_pid_live = isinstance(launch_lock_pid, int) and _pid_exists(launch_lock_pid)
    marker_live = bool(
        marker
        and any(
            raw.isdigit() and _pid_exists(int(raw))
            for raw in (
                marker.get("PFI_ACTIVE_PID", ""),
                marker.get("PFI_ACTIVE_MONITOR_PID", ""),
                marker.get("PFI_ACTIVE_LAUNCHER_PID", ""),
            )
        )
    )
    runtime_was_present = launchservices_runtime_verified or marker_live or lock_pid_live

    pid_observed = bool(
        isinstance(state.get("observed_pid"), int)
        or (marker and marker.get("PFI_ACTIVE_PID", "").isdigit())
    )
    monitor_pid_observed = bool(
        isinstance(state.get("observed_monitor_pid"), int)
        or (marker and marker.get("PFI_ACTIVE_MONITOR_PID", "").isdigit())
    )
    launcher_pid_observed = bool(
        isinstance(state.get("observed_launcher_pid"), int)
        or (marker and marker.get("PFI_ACTIVE_LAUNCHER_PID", "").isdigit())
        or lock_pid_live
    )

    process_tree_identity_unchanged_before_cleanup = not runtime_was_present
    listener_owner_port_set_unchanged_before_cleanup = not runtime_was_present
    process_group_identity_unchanged_before_cleanup = not runtime_was_present
    listener_endpoint_set_unchanged_before_cleanup = not runtime_was_present
    process_stop_status = "not_started"
    monitor_stop_status = "not_started"
    shutdown_monitor_stopped = not runtime_was_present
    launcher_stopped = not runtime_was_present
    process_tree_cleanup_verified = not runtime_was_present
    process_group_cleanup_verified = not runtime_was_present
    launch_lock_quiescent = not lock_pid_live
    runtime_process_cleanup_verified = not runtime_was_present

    if runtime_cleanup_checkpoint_reused and runtime_checkpoint is not None:
        process_tree_identity_unchanged_before_cleanup = True
        listener_owner_port_set_unchanged_before_cleanup = True
        process_group_identity_unchanged_before_cleanup = True
        listener_endpoint_set_unchanged_before_cleanup = True
        process_stop_status = str(runtime_checkpoint["process_stop_status"])
        monitor_stop_status = str(runtime_checkpoint["monitor_stop_status"])
        pid_observed = bool(runtime_checkpoint.get("pid_observed"))
        monitor_pid_observed = bool(runtime_checkpoint.get("monitor_pid_observed"))
        launcher_pid_observed = bool(runtime_checkpoint.get("launcher_pid_observed"))
        process_group_id = state.get("observed_process_group_id")
        try:
            process_group_cleanup_verified = (
                not isinstance(process_group_id, int)
                or not _process_group_pids(process_group_id)
            ) and _wait_for_process_tree_exit(observed_group)
            process_tree_cleanup_verified = _wait_for_process_tree_exit(observed_tree)
            launch_lock_quiescent = not (
                isinstance(launch_lock_pid, int) and _pid_exists(launch_lock_pid)
            )
        except Exception:
            process_group_cleanup_verified = False
            process_tree_cleanup_verified = False
            launch_lock_quiescent = False
        shutdown_monitor_stopped = process_group_cleanup_verified
        launcher_stopped = process_group_cleanup_verified and launch_lock_quiescent
        runtime_process_cleanup_verified = all(
            (
                process_group_cleanup_verified,
                process_tree_cleanup_verified,
                launcher_stopped,
            )
        )
    else:
        if launchservices_runtime_verified:
            try:
                streamlit_pid = int(state["observed_pid"])
                monitor_pid = int(state["observed_monitor_pid"])
                launcher_pid = int(state["observed_launcher_pid"])
                process_group_id = int(state["observed_process_group_id"])
                if process_group_id != launcher_pid or not marker:
                    raise CandidateError("candidate process group identity is unavailable")
                current_group = _process_group_identity_records(process_group_id)
                current_tree = _process_tree_identity_records({launcher_pid})
                expected_endpoints = {
                    (streamlit_pid, "127.0.0.1", int(state["streamlit_port"])),
                    (
                        streamlit_pid,
                        "127.0.0.1",
                        int(state["observed_runtime_api_port"]),
                    ),
                    (monitor_pid, "127.0.0.1", int(state["heartbeat_port"])),
                }
                current_endpoints = _process_group_tcp_listeners(process_group_id)
                process_group_identity_unchanged_before_cleanup = (
                    current_group == observed_group
                    and set(current_group) == {launcher_pid, streamlit_pid, monitor_pid}
                    and isinstance(inspection, dict)
                    and inspection.get("process_group_verified") is True
                    and inspection.get("process_group_identity_sha256")
                    == _process_tree_identity_sha256(observed_group)
                )
                process_tree_identity_unchanged_before_cleanup = (
                    current_tree == observed_tree
                    and isinstance(inspection, dict)
                    and inspection.get("launcher_process_tree_verified") is True
                )
                listener_endpoint_set_unchanged_before_cleanup = (
                    current_endpoints == expected_endpoints
                    and isinstance(inspection, dict)
                    and inspection.get("listener_endpoint_set_verified") is True
                    and inspection.get("listener_endpoint_set_sha256")
                    == _listener_endpoint_set_sha256(expected_endpoints)
                )
                listener_owner_port_set_unchanged_before_cleanup = (
                    listener_endpoint_set_unchanged_before_cleanup
                    and inspection.get("listener_owner_port_set_verified") is True
                )
            except Exception:
                process_group_identity_unchanged_before_cleanup = False
                process_tree_identity_unchanged_before_cleanup = False
                listener_endpoint_set_unchanged_before_cleanup = False
                listener_owner_port_set_unchanged_before_cleanup = False
        elif runtime_was_present:
            process_group_identity_unchanged_before_cleanup = False
            process_tree_identity_unchanged_before_cleanup = False
            listener_endpoint_set_unchanged_before_cleanup = False
            listener_owner_port_set_unchanged_before_cleanup = False

        group_records: dict[int, str] = {}
        group_stopped = False
        try:
            if marker_live and marker is not None:
                process_stop_status, group_records, group_stopped = (
                    _stop_owned_process_group(state, marker)
                )
            elif lock_pid_live and isinstance(launch_lock_pid, int):
                process_stop_status, group_records, group_stopped = (
                    _stop_owned_launcher_group(state, launch_lock_pid)
                )
            elif runtime_was_present:
                process_stop_status = "runtime_identity_unavailable_not_signaled"
            else:
                process_stop_status = "not_started"
                group_stopped = True
        except Exception:
            process_stop_status = "group_cleanup_error"
            group_stopped = False
        monitor_stop_status = process_stop_status
        if group_records and not observed_group:
            observed_group = group_records
            state["observed_process_group"] = {
                str(pid): digest for pid, digest in sorted(group_records.items())
            }
            group_ids = {
                group_id
                for group_id in (_process_group_id(pid) for pid in group_records)
                if isinstance(group_id, int)
            }
            if len(group_ids) == 1:
                state["observed_process_group_id"] = next(iter(group_ids))
        process_group_id = state.get("observed_process_group_id")
        try:
            process_group_cleanup_verified = group_stopped and (
                not isinstance(process_group_id, int)
                or not _process_group_pids(process_group_id)
            )
            process_tree_cleanup_verified = (
                not observed_tree or _wait_for_process_tree_exit(observed_tree)
            ) and (not observed_group or _wait_for_process_tree_exit(observed_group))
            launch_lock_quiescent = not (
                isinstance(launch_lock_pid, int) and _pid_exists(launch_lock_pid)
            )
        except Exception:
            process_group_cleanup_verified = False
            process_tree_cleanup_verified = False
            launch_lock_quiescent = False
        shutdown_monitor_stopped = process_group_cleanup_verified
        launcher_stopped = process_group_cleanup_verified and launch_lock_quiescent
        runtime_process_cleanup_verified = (
            group_stopped
            and process_group_cleanup_verified
            and process_tree_cleanup_verified
            and launcher_stopped
        )

    streamlit_port_released_before_cleanup = False
    runtime_api_port_released_before_cleanup = not isinstance(
        state.get("observed_runtime_api_port"), int
    )
    heartbeat_port_released_before_cleanup = False
    try:
        streamlit_port_released_before_cleanup = _wait_for_port_release(
            int(state["streamlit_port"])
        )
        if isinstance(state.get("observed_runtime_api_port"), int):
            runtime_api_port_released_before_cleanup = _wait_for_port_release(
                int(state["observed_runtime_api_port"])
            )
        heartbeat_port_released_before_cleanup = _wait_for_port_release(
            int(state["heartbeat_port"])
        )
    except Exception:
        finalization_error = True

    runtime_checkpoint_ready = all(
        (
            process_tree_identity_unchanged_before_cleanup,
            process_group_identity_unchanged_before_cleanup,
            listener_owner_port_set_unchanged_before_cleanup,
            listener_endpoint_set_unchanged_before_cleanup,
            process_tree_cleanup_verified,
            process_group_cleanup_verified,
            runtime_process_cleanup_verified,
            shutdown_monitor_stopped,
            launcher_stopped,
            launch_lock_quiescent,
            streamlit_port_released_before_cleanup,
            runtime_api_port_released_before_cleanup,
            heartbeat_port_released_before_cleanup,
        )
    )
    if runtime_checkpoint_ready and not runtime_cleanup_checkpoint_reused:
        runtime_checkpoint = {
            "schema": RUNTIME_CLEANUP_CHECKPOINT_SCHEMA,
            "launchservices_runtime_verified": launchservices_runtime_verified,
            "pid_observed": pid_observed,
            "monitor_pid_observed": monitor_pid_observed,
            "launcher_pid_observed": launcher_pid_observed,
            "process_stop_status": process_stop_status,
            "monitor_stop_status": monitor_stop_status,
            "process_tree_identity_unchanged_before_cleanup": True,
            "process_group_identity_unchanged_before_cleanup": True,
            "listener_owner_port_set_unchanged_before_cleanup": True,
            "listener_endpoint_set_unchanged_before_cleanup": True,
            "process_tree_cleanup_verified": True,
            "process_group_cleanup_verified": True,
            "runtime_process_cleanup_verified": True,
            "shutdown_monitor_stopped": True,
            "launcher_stopped": True,
            "launch_lock_quiescent": True,
            "streamlit_port_released_before_cleanup": True,
            "runtime_api_port_released_before_cleanup": True,
            "heartbeat_port_released_before_cleanup": True,
            "process_tree_identity_sha256": _process_tree_identity_sha256(observed_tree),
            "process_group_identity_sha256": _process_tree_identity_sha256(observed_group),
        }
        state["runtime_cleanup_checkpoint"] = runtime_checkpoint
        state["lifecycle_state"] = "STOPPED"
        try:
            _write_state(Path(str(state["state_path"])), state)
        except Exception:
            runtime_checkpoint_ready = False
            finalization_error = True
    if not runtime_checkpoint_ready:
        finalization_error = True
    owned_process_stopped = runtime_was_present and runtime_process_cleanup_verified

    launchservices_checkpoint: dict[str, Any] | None = None
    launchservices_checkpoint_reused = False
    try:
        launchservices_checkpoint = _launchservices_cleanup_checkpoint(state)
        launchservices_checkpoint_reused = launchservices_checkpoint is not None
    except Exception:
        finalization_error = True
    if launchservices_checkpoint_reused and launchservices_checkpoint is not None:
        launchservices_before_unregister_query_ok = True
        launchservices_before_unregister_count = int(
            launchservices_checkpoint["launchservices_before_unregister_record_count"]
        )
        launchservices_before_unregister_sha256 = str(
            launchservices_checkpoint["launchservices_before_unregister_record_sha256"]
        )
        unregister_command_required = True
        unregister_returncode = 0
        launchservices_post_unregister_count = 0
        launchservices_post_unregister_sha256 = str(
            launchservices_checkpoint["launchservices_post_unregister_record_sha256"]
        )
        current_query_ok, current_count, _current_sha256 = (
            _launchservices_exact_path_status(candidate_app)
        )
        if current_query_ok and current_count > 0:
            unregister_returncode = _unregister(candidate_app)
        (
            launchservices_query_ok,
            current_absent_count,
            current_absent_sha256,
        ) = _wait_for_launchservices_state(candidate_app, registered=False)
        launchservices_post_unregister_absent = (
            launchservices_query_ok
            and current_absent_count == 0
            and current_absent_sha256 == launchservices_post_unregister_sha256
        )
    else:
        (
            launchservices_before_unregister_query_ok,
            launchservices_before_unregister_count,
            launchservices_before_unregister_sha256,
        ) = _launchservices_exact_path_status(candidate_app)
        unregister_command_required = bool(
            launchservices_before_unregister_query_ok
            and launchservices_before_unregister_count >= 1
        )
        unregister_returncode = (
            _unregister(candidate_app) if unregister_command_required else 1
        )
        (
            launchservices_query_ok,
            launchservices_post_unregister_count,
            launchservices_post_unregister_sha256,
        ) = _wait_for_launchservices_state(candidate_app, registered=False)
        launchservices_post_unregister_absent = (
            launchservices_query_ok and launchservices_post_unregister_count == 0
        )
        if (
            unregister_command_required
            and unregister_returncode == 0
            and launchservices_post_unregister_absent
        ):
            launchservices_checkpoint = {
                "schema": "PFIV025Stage1Phase13LaunchServicesCheckpointV1",
                "unregister_command_required": True,
                "unregister_returncode": 0,
                "launchservices_before_unregister_query_ok": True,
                "launchservices_before_unregister_record_count": launchservices_before_unregister_count,
                "launchservices_before_unregister_record_sha256": launchservices_before_unregister_sha256,
                "launchservices_post_unregister_absent": True,
                "launchservices_post_unregister_record_count": 0,
                "launchservices_post_unregister_record_sha256": launchservices_post_unregister_sha256,
            }
            state["launchservices_cleanup_checkpoint"] = launchservices_checkpoint
            state["lifecycle_state"] = "UNREGISTERED"
            try:
                _write_state(Path(str(state["state_path"])), state)
            except Exception:
                finalization_error = True
        else:
            finalization_error = True

    launchservices_unregistered = bool(
        unregister_returncode == 0 and launchservices_post_unregister_absent
    )
    (
        launchservices_final_query_ok,
        launchservices_final_record_count,
        launchservices_final_record_sha256,
    ) = _wait_for_launchservices_state(candidate_app, registered=False)
    launchservices_final_absent = (
        launchservices_final_query_ok and launchservices_final_record_count == 0
    )
    launchservices_unregistered = (
        launchservices_unregistered and launchservices_final_absent
    )

    canonical_after: dict[str, dict[str, object]] = {}
    protected_metadata_after: dict[str, object] = {}
    canonical_unchanged = False
    protected_metadata_unchanged = False
    git_status_unchanged = False
    candidate_record: dict[str, object] = {}
    entry_matrix: dict[str, object] = {}
    evidence_records_written = False
    try:
        canonical_after = snapshot_canonical_entries(Path.home())
        canonical_unchanged = canonical_after == state["canonical_before"]
        project_root = Path(str(state["project_root"]))
        protected_metadata_after = {
            "ready_marker": _ready_marker_record(project_root),
            "source_app": _bundle_identity(project_root / "macos" / "PFI.app"),
        }
        protected_metadata_unchanged = (
            protected_metadata_after == state["protected_metadata_before"]
        )
        git_status_after = _git_value(Path(str(state["git_root"])), "status", "--short")
        git_status_before_hash = state.get(
            "git_status_sha256_before", state.get("git_status_sha256")
        )
        git_status_unchanged = bool(
            isinstance(git_status_before_hash, str)
            and _sha256_bytes(git_status_after.encode("utf-8"))
            == git_status_before_hash
        )
        candidate_record = {
            "schema": "PFIV025Stage1Phase13CandidateAppEvidenceV1",
            "candidate_path_symbolic": "${ISOLATED_ROOT}/PFI.app",
            "checkout_commit": state["checkout_commit"],
            "source_app_tree_sha256": state["source_app_tree_sha256"],
            "copied_app_tree_sha256": state["copied_app_tree_sha256"],
            "candidate_app_tree_sha256": state["candidate_app_tree_sha256"],
            "candidate_app_path_sha256": state["candidate_app_path_sha256"],
            "candidate_executable_sha256": state["candidate_executable_sha256"],
            "candidate_bundle_sha256": state["candidate_bundle_sha256"],
            "streamlit_port": state["streamlit_port"],
            "runtime_api_port": state.get("observed_runtime_api_port"),
            "heartbeat_port": state["heartbeat_port"],
            "canonical_app_install": False,
            "active_marker_observed": marker_file_observed,
            "launchservices_runtime_verified": launchservices_runtime_verified,
            "pid_observed": pid_observed,
            "monitor_pid_observed": monitor_pid_observed,
            "launcher_pid_observed": launcher_pid_observed,
            "process_stop_status": process_stop_status,
            "monitor_stop_status": monitor_stop_status,
            "process_identity_sha256": inspection.get("process_identity_sha256", "") if isinstance(inspection, dict) else "",
            "monitor_identity_sha256": inspection.get("monitor_identity_sha256", "") if isinstance(inspection, dict) else "",
            "launcher_identity_sha256": inspection.get("launcher_identity_sha256", "") if isinstance(inspection, dict) else "",
            "launcher_process_tree_verified": inspection.get("launcher_process_tree_verified") is True if isinstance(inspection, dict) else False,
            "process_tree_member_count": inspection.get("process_tree_member_count", 0) if isinstance(inspection, dict) else 0,
            "process_tree_identity_sha256": inspection.get("process_tree_identity_sha256", "") if isinstance(inspection, dict) else "",
            "process_group_verified": inspection.get("process_group_verified") is True if isinstance(inspection, dict) else False,
            "process_group_member_count": inspection.get("process_group_member_count", 0) if isinstance(inspection, dict) else 0,
            "process_group_identity_sha256": inspection.get("process_group_identity_sha256", "") if isinstance(inspection, dict) else "",
            "process_tree_identity_unchanged_before_cleanup": process_tree_identity_unchanged_before_cleanup,
            "process_group_identity_unchanged_before_cleanup": process_group_identity_unchanged_before_cleanup,
            "process_tree_cleanup_verified": process_tree_cleanup_verified,
            "process_group_cleanup_verified": process_group_cleanup_verified,
            "launch_lock_quiescent": launch_lock_quiescent,
            "launcher_stopped": launcher_stopped,
            "health_ready": inspection.get("health_ready") is True if isinstance(inspection, dict) else False,
            "runtime_api_ready": inspection.get("runtime_api_ready") is True if isinstance(inspection, dict) else False,
            "heartbeat_ready": inspection.get("heartbeat_ready") is True if isinstance(inspection, dict) else False,
            "streamlit_listener_set_verified": inspection.get("streamlit_listener_set_verified") is True if isinstance(inspection, dict) else False,
            "streamlit_listener_count": inspection.get("streamlit_listener_count", 0) if isinstance(inspection, dict) else 0,
            "streamlit_listener_set_sha256": inspection.get("streamlit_listener_set_sha256", "") if isinstance(inspection, dict) else "",
            "monitor_listener_set_verified": inspection.get("monitor_listener_set_verified") is True if isinstance(inspection, dict) else False,
            "monitor_listener_count": inspection.get("monitor_listener_count", 0) if isinstance(inspection, dict) else 0,
            "monitor_listener_set_sha256": inspection.get("monitor_listener_set_sha256", "") if isinstance(inspection, dict) else "",
            "listener_owner_port_set_verified": inspection.get("listener_owner_port_set_verified") is True if isinstance(inspection, dict) else False,
            "listener_owner_port_count": inspection.get("listener_owner_port_count", 0) if isinstance(inspection, dict) else 0,
            "listener_owner_port_set_sha256": inspection.get("listener_owner_port_set_sha256", "") if isinstance(inspection, dict) else "",
            "listener_endpoint_set_verified": inspection.get("listener_endpoint_set_verified") is True if isinstance(inspection, dict) else False,
            "listener_endpoint_count": inspection.get("listener_endpoint_count", 0) if isinstance(inspection, dict) else 0,
            "listener_endpoint_set_sha256": inspection.get("listener_endpoint_set_sha256", "") if isinstance(inspection, dict) else "",
            "listener_owner_port_set_unchanged_before_cleanup": listener_owner_port_set_unchanged_before_cleanup,
            "listener_endpoint_set_unchanged_before_cleanup": listener_endpoint_set_unchanged_before_cleanup,
            "owned_process_stopped": owned_process_stopped,
            "runtime_process_cleanup_verified": runtime_process_cleanup_verified,
            "runtime_cleanup_checkpoint_reused": runtime_cleanup_checkpoint_reused,
            "shutdown_monitor_stopped": shutdown_monitor_stopped,
            "streamlit_port_released_before_cleanup": streamlit_port_released_before_cleanup,
            "runtime_api_port_released_before_cleanup": runtime_api_port_released_before_cleanup,
            "heartbeat_port_released_before_cleanup": heartbeat_port_released_before_cleanup,
            "streamlit_port_released": streamlit_port_released_before_cleanup,
            "runtime_api_port_released": runtime_api_port_released_before_cleanup,
            "heartbeat_port_released": heartbeat_port_released_before_cleanup,
            "launchservices_registered": state.get("launchservices_registered") is True,
            "launchservices_registration_verified": state.get("launchservices_registration_verified") is True,
            "launchservices_registration_record_count": state.get("launchservices_registration_record_count", 0),
            "launchservices_registration_record_sha256": state.get("launchservices_registration_record_sha256", ""),
            "protected_metadata_unchanged": protected_metadata_unchanged,
        }
        entry_matrix = {
            "schema": "PFIV025Stage1Phase13CanonicalEntryMatrixV1",
            "before": state["canonical_before"],
            "after": canonical_after,
            "canonical_unchanged": canonical_unchanged,
        }
        if resolved_evidence_dir is None:
            raise CandidateError("evidence directory is unavailable")
        _write_json(resolved_evidence_dir / "candidate_app.json", candidate_record)
        _write_json(resolved_evidence_dir / "entry_matrix.json", entry_matrix)
        _write_json(
            resolved_evidence_dir / "protected_metadata.json",
            {
                "schema": "PFIV025Stage1Phase13ProtectedMetadataV1",
                "before": state["protected_metadata_before"],
                "after": protected_metadata_after,
                "protected_metadata_unchanged": protected_metadata_unchanged,
                "git_status_unchanged": git_status_unchanged,
            },
        )
        evidence_records_written = True
    except Exception:
        finalization_error = True

    base_cleanup_record: dict[str, object] = {
        "schema": "PFIV025Stage1Phase13LaunchServicesCleanupV1",
        "candidate_path_symbolic": "${ISOLATED_ROOT}/PFI.app",
        "launchservices_registered": state.get("launchservices_registered") is True,
        "launchservices_registration_verified": state.get("launchservices_registration_verified") is True,
        "launchservices_unregistered": launchservices_unregistered,
        "launchservices_checkpoint_reused": launchservices_checkpoint_reused,
        "unregister_command_required": unregister_command_required,
        "launchservices_before_unregister_record_count": launchservices_before_unregister_count,
        "launchservices_before_unregister_record_sha256": launchservices_before_unregister_sha256,
        "launchservices_post_unregister_absent": launchservices_post_unregister_absent,
        "registration_absent_after": launchservices_final_absent,
        "launchservices_post_unregister_record_count": launchservices_post_unregister_count,
        "launchservices_post_unregister_record_sha256": launchservices_post_unregister_sha256,
        "launchservices_final_absent": launchservices_final_absent,
        "launchservices_final_record_count": launchservices_final_record_count,
        "launchservices_final_record_sha256": launchservices_final_record_sha256,
        "unregister_returncode": unregister_returncode,
        "pid_observed": pid_observed,
        "monitor_pid_observed": monitor_pid_observed,
        "launcher_pid_observed": launcher_pid_observed,
        "process_stop_status": process_stop_status,
        "monitor_stop_status": monitor_stop_status,
        "owned_process_stopped": owned_process_stopped,
        "runtime_process_cleanup_verified": runtime_process_cleanup_verified,
        "runtime_cleanup_checkpoint_reused": runtime_cleanup_checkpoint_reused,
        "shutdown_monitor_stopped": shutdown_monitor_stopped,
        "launcher_stopped": launcher_stopped,
        "process_tree_identity_unchanged_before_cleanup": process_tree_identity_unchanged_before_cleanup,
        "process_group_identity_unchanged_before_cleanup": process_group_identity_unchanged_before_cleanup,
        "process_tree_cleanup_verified": process_tree_cleanup_verified,
        "process_group_cleanup_verified": process_group_cleanup_verified,
        "launch_lock_quiescent": launch_lock_quiescent,
        "listener_owner_port_set_unchanged_before_cleanup": listener_owner_port_set_unchanged_before_cleanup,
        "listener_endpoint_set_unchanged_before_cleanup": listener_endpoint_set_unchanged_before_cleanup,
        "streamlit_port_released_before_cleanup": streamlit_port_released_before_cleanup,
        "runtime_api_port_released_before_cleanup": runtime_api_port_released_before_cleanup,
        "heartbeat_port_released_before_cleanup": heartbeat_port_released_before_cleanup,
        "canonical_unchanged": canonical_unchanged,
        "protected_metadata_unchanged": protected_metadata_unchanged,
        "git_status_unchanged": git_status_unchanged,
        "finalization_tombstone_published": True,
    }

    safe_to_remove_root = not finalization_error and _candidate_root_removal_safe(
        shutdown_monitor_stopped=shutdown_monitor_stopped,
        streamlit_port_released=streamlit_port_released_before_cleanup,
        runtime_api_port_released=runtime_api_port_released_before_cleanup,
        heartbeat_port_released=heartbeat_port_released_before_cleanup,
        launchservices_absent=launchservices_unregistered,
        runtime_cleanup_verified=runtime_process_cleanup_verified,
        listener_set_unchanged=all(
            (
                listener_owner_port_set_unchanged_before_cleanup,
                listener_endpoint_set_unchanged_before_cleanup,
                process_group_identity_unchanged_before_cleanup,
                launch_lock_quiescent,
                canonical_unchanged,
                protected_metadata_unchanged,
                git_status_unchanged,
            )
        ),
        process_tree_cleanup_verified=all(
            (process_tree_cleanup_verified, process_group_cleanup_verified)
        ),
        evidence_records_written=evidence_records_written,
    )
    cleanup_complete = False
    root_deleted = False
    streamlit_port_released_after_cleanup = False
    runtime_api_port_released_after_cleanup = not isinstance(
        state.get("observed_runtime_api_port"), int
    )
    heartbeat_port_released_after_cleanup = False
    post_root_launchservices_absent = False
    pending_cleanup: Path | None = None
    cleanup_record = {
        **base_cleanup_record,
        "streamlit_port_released_after_cleanup": False,
        "runtime_api_port_released_after_cleanup": runtime_api_port_released_after_cleanup,
        "heartbeat_port_released_after_cleanup": False,
        "streamlit_port_released": False,
        "runtime_api_port_released": False,
        "heartbeat_port_released": False,
        "post_root_launchservices_absent": False,
        "cleanup_complete": False,
        "temp_root_deleted": False,
        "root_retained_for_retry": True,
    }
    if safe_to_remove_root and resolved_evidence_dir is not None:
        pending_cleanup = resolved_evidence_dir / ".launchservices_cleanup.pending.json"
        try:
            provisional_record = {
                **cleanup_record,
                "schema": "PFIV025Stage1Phase13CleanupPendingV1",
                "transaction_state": "PRE_ROOT_DELETE",
                "streamlit_port_released_after_cleanup": False,
                "runtime_api_port_released_after_cleanup": runtime_api_port_released_after_cleanup,
                "heartbeat_port_released_after_cleanup": False,
                "streamlit_port_released": False,
                "runtime_api_port_released": False,
                "heartbeat_port_released": False,
                "post_root_launchservices_absent": False,
                "cleanup_complete": False,
                "temp_root_deleted": False,
                "root_retained_for_retry": True,
            }
            _write_json(pending_cleanup, provisional_record)
            _validate_state_path(state_path)
            root_deleted = _quarantine_and_remove_root(
                isolated_root,
                expected_device=int(state["isolated_root_st_dev"]),
                expected_inode=int(state["isolated_root_st_ino"]),
            )
            if not root_deleted:
                raise CandidateError("candidate root deletion failed")
            streamlit_port_released_after_cleanup = _wait_for_port_release(
                int(state["streamlit_port"])
            )
            if isinstance(state.get("observed_runtime_api_port"), int):
                runtime_api_port_released_after_cleanup = _wait_for_port_release(
                    int(state["observed_runtime_api_port"])
                )
            heartbeat_port_released_after_cleanup = _wait_for_port_release(
                int(state["heartbeat_port"])
            )
            final_query_ok, final_count, final_sha256 = (
                _wait_for_launchservices_state(candidate_app, registered=False)
            )
            post_root_launchservices_absent = bool(
                final_query_ok
                and final_count == 0
                and final_sha256 == launchservices_final_record_sha256
            )
            cleanup_complete = all(
                (
                    root_deleted,
                    streamlit_port_released_after_cleanup,
                    runtime_api_port_released_after_cleanup,
                    heartbeat_port_released_after_cleanup,
                    post_root_launchservices_absent,
                )
            )
            cleanup_record = {
                **cleanup_record,
                "registration_absent_after": post_root_launchservices_absent,
                "launchservices_final_absent": post_root_launchservices_absent,
                "streamlit_port_released_after_cleanup": streamlit_port_released_after_cleanup,
                "runtime_api_port_released_after_cleanup": runtime_api_port_released_after_cleanup,
                "heartbeat_port_released_after_cleanup": heartbeat_port_released_after_cleanup,
                "streamlit_port_released": (
                    streamlit_port_released_before_cleanup
                    and streamlit_port_released_after_cleanup
                ),
                "runtime_api_port_released": (
                    runtime_api_port_released_before_cleanup
                    and runtime_api_port_released_after_cleanup
                ),
                "heartbeat_port_released": (
                    heartbeat_port_released_before_cleanup
                    and heartbeat_port_released_after_cleanup
                ),
                "post_root_launchservices_absent": post_root_launchservices_absent,
                "cleanup_complete": cleanup_complete,
                "temp_root_deleted": root_deleted,
                "root_retained_for_retry": not root_deleted,
            }
            _write_json(pending_cleanup, cleanup_record)
            pending_cleanup.replace(resolved_evidence_dir / "launchservices_cleanup.json")
            if not cleanup_complete:
                finalization_error = True
        except Exception:
            finalization_error = True
            root_deleted = not isolated_root.exists()
            cleanup_complete = False
            cleanup_record = {
                **cleanup_record,
                "registration_absent_after": post_root_launchservices_absent,
                "launchservices_final_absent": post_root_launchservices_absent,
                "streamlit_port_released_after_cleanup": streamlit_port_released_after_cleanup,
                "runtime_api_port_released_after_cleanup": runtime_api_port_released_after_cleanup,
                "heartbeat_port_released_after_cleanup": heartbeat_port_released_after_cleanup,
                "streamlit_port_released": (
                    streamlit_port_released_before_cleanup
                    and streamlit_port_released_after_cleanup
                ),
                "runtime_api_port_released": (
                    runtime_api_port_released_before_cleanup
                    and runtime_api_port_released_after_cleanup
                ),
                "heartbeat_port_released": (
                    heartbeat_port_released_before_cleanup
                    and heartbeat_port_released_after_cleanup
                ),
                "post_root_launchservices_absent": post_root_launchservices_absent,
                "cleanup_complete": False,
                "temp_root_deleted": root_deleted,
                "root_retained_for_retry": not root_deleted,
            }
            if root_deleted and resolved_evidence_dir is not None:
                try:
                    _write_json(
                        resolved_evidence_dir / "launchservices_cleanup.json",
                        cleanup_record,
                    )
                except Exception:
                    pass
            elif pending_cleanup is not None:
                pending_cleanup.unlink(missing_ok=True)
    else:
        finalization_error = True

    if not cleanup_complete and not root_deleted and resolved_evidence_dir is not None:
        cleanup_record = {
            **cleanup_record,
            "cleanup_complete": False,
            "temp_root_deleted": False,
            "root_retained_for_retry": True,
        }
        try:
            _write_json(resolved_evidence_dir / "launchservices_cleanup.json", cleanup_record)
        except Exception:
            finalization_error = True

    result = {
        "cleanup_complete": cleanup_complete,
        "temp_root_deleted": root_deleted,
        "pid_observed": pid_observed,
        "monitor_pid_observed": monitor_pid_observed,
        "launcher_pid_observed": launcher_pid_observed,
        "process_stop_status": process_stop_status,
        "monitor_stop_status": monitor_stop_status,
        "owned_process_stopped": owned_process_stopped,
        "runtime_process_cleanup_verified": runtime_process_cleanup_verified,
        "runtime_cleanup_checkpoint_reused": runtime_cleanup_checkpoint_reused,
        "shutdown_monitor_stopped": shutdown_monitor_stopped,
        "launcher_stopped": launcher_stopped,
        "process_tree_identity_unchanged_before_cleanup": process_tree_identity_unchanged_before_cleanup,
        "process_group_identity_unchanged_before_cleanup": process_group_identity_unchanged_before_cleanup,
        "process_tree_cleanup_verified": process_tree_cleanup_verified,
        "process_group_cleanup_verified": process_group_cleanup_verified,
        "launch_lock_quiescent": launch_lock_quiescent,
        "listener_owner_port_set_unchanged_before_cleanup": listener_owner_port_set_unchanged_before_cleanup,
        "listener_endpoint_set_unchanged_before_cleanup": listener_endpoint_set_unchanged_before_cleanup,
        "streamlit_port_released": (
            streamlit_port_released_before_cleanup
            and (not root_deleted or streamlit_port_released_after_cleanup)
        ),
        "runtime_api_port_released": (
            runtime_api_port_released_before_cleanup
            and (not root_deleted or runtime_api_port_released_after_cleanup)
        ),
        "heartbeat_port_released": (
            heartbeat_port_released_before_cleanup
            and (not root_deleted or heartbeat_port_released_after_cleanup)
        ),
        "canonical_unchanged": canonical_unchanged,
        "protected_metadata_unchanged": protected_metadata_unchanged,
        "git_status_unchanged": git_status_unchanged,
        "launchservices_unregistered": launchservices_unregistered,
        "launchservices_post_unregister_absent": launchservices_post_unregister_absent,
        "launchservices_final_absent": (
            launchservices_final_absent
            and (not root_deleted or post_root_launchservices_absent)
        ),
        "post_root_launchservices_absent": post_root_launchservices_absent,
        "finalization_tombstone_published": True,
        "root_retained_for_retry": not root_deleted,
    }
    if finalization_error or not cleanup_complete:
        raise CandidateError("candidate finalization evidence failed")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="prepare one disposable candidate")
    prepare.add_argument("--project-root", type=Path, required=True)
    inspect_parser = subparsers.add_parser("inspect", help="inspect the LaunchServices-started runtime")
    inspect_parser.add_argument("--state", type=Path, required=True)
    inspect_parser.add_argument("--timeout-seconds", type=float, default=120)
    finalize = subparsers.add_parser("finalize", help="clean the disposable candidate")
    finalize.add_argument("--state", type=Path, required=True)
    finalize.add_argument("--evidence-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "prepare":
        state = prepare_candidate(args.project_root)
        print(state["state_path"])
        return 0
    if args.command == "inspect":
        print(json.dumps(inspect_candidate(args.state, timeout_seconds=args.timeout_seconds), sort_keys=True))
        return 0
    if args.command == "finalize":
        print(json.dumps(finalize_candidate(args.state, args.evidence_dir), sort_keys=True))
        return 0
    raise CandidateError("unsupported command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CandidateError as error:
        print(f"PFI_STAGE1_CANDIDATE_ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print("PFI_STAGE1_CANDIDATE_ERROR: unexpected lifecycle failure", file=sys.stderr)
        raise SystemExit(1) from None
