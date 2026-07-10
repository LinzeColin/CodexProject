#!/usr/bin/env python3
"""Rehearse Memory Atlas recovery from one exact tracked-files-only Git commit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA_VERSION = "memory_atlas.github_recovery_audit.v1_2_r7"
SOURCE_PACKAGE_ROOT = Path("docs/source_packages/memory_atlas_v1_2")
SOURCE_PACKAGE_MANIFEST = SOURCE_PACKAGE_ROOT / "SOURCE_MANIFEST.json"
PUBLIC_RAW_ROOT = Path("data/public_raw")
RAW_LEDGER_PATH = Path("机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl")
CURRENT_RELEASE_PATH = Path("机器治理/发布快照/memory_atlas_current_release.json")
RELEASE_ROOT = Path("data/releases/memory_atlas/v1_2")
DERIVED_SNAPSHOT_PATH = Path("data/derived/visualization/memory_atlas.json")
FRONTEND_PATH = Path("apps/memory-atlas")
PAGES_SNAPSHOT_PATH = FRONTEND_PATH / "dist/memory_atlas.json"
PUBLIC_RAW_AUDITOR_PATH = Path("scripts/audit_memory_atlas_public_raw.py")

MAX_PUBLIC_RAW_FILE_BYTES = 40 * 1024 * 1024
MAX_COMMAND_OUTPUT_BYTES = 4 * 1024 * 1024
OUTPUT_TAIL_BYTES = 16 * 1024
COMMAND_TIMEOUT_SECONDS = 15 * 60
EXACT_COMMIT_PATTERN = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
SAFE_RELEASE_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]+\Z")
IGNORED_PUBLIC_RAW_NAMES = {".DS_Store", ".gitkeep", "README.md"}


class RecoveryAuditError(RuntimeError):
    """A fail-closed recovery gate rejected the candidate."""

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class ReleaseContract:
    release_id: str
    manifest_path: Path
    snapshot_path: Path
    snapshot_sha256: str
    raw_manifest_path: Path
    raw_manifest_sha256: str
    source_package_manifest_path: Path
    source_package_manifest_sha256: str
    source_package_manifest_size_bytes: int
    source_packages: tuple[dict[str, Any], ...]
    snapshot_counts: dict[str, int]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file():
        raise RecoveryAuditError(code, "Required JSON file is missing.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryAuditError(code, "Required JSON file is invalid.") from exc
    if not isinstance(payload, dict):
        raise RecoveryAuditError(code, "Required JSON payload must be an object.")
    return payload


def _load_jsonl(path: Path, missing_code: str, invalid_code: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise RecoveryAuditError(missing_code, "Required JSONL file is missing.")
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if not isinstance(row, dict):
                    raise ValueError(f"row {line_number} is not an object")
                rows.append(row)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RecoveryAuditError(invalid_code, "Required JSONL payload is invalid.") from exc
    return rows


def _relative_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RecoveryAuditError("NON_PORTABLE_PATH", f"{field} must be a non-empty relative path.")
    text = value.strip().replace("\\", "/")
    pure = PurePosixPath(text)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise RecoveryAuditError("NON_PORTABLE_PATH", f"{field} must be a normalized relative path.")
    if re.match(r"^[A-Za-z]:", text):
        raise RecoveryAuditError("NON_PORTABLE_PATH", f"{field} must not use a drive-qualified path.")
    return Path(*pure.parts)


def _resolve_under(root: Path, relative: Path, code: str) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / relative).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise RecoveryAuditError(code, "Resolved path escapes the recovery root.") from exc
    return target


def _assert_relative_manifest_paths(value: Any, context: str, key: str = "") -> None:
    if isinstance(value, dict):
        for child_key, child in value.items():
            _assert_relative_manifest_paths(child, context, str(child_key))
        return
    if isinstance(value, list):
        for child in value:
            _assert_relative_manifest_paths(child, context, key)
        return
    if not isinstance(value, str):
        return
    normalized_key = key.lower()
    if "path" in normalized_key or normalized_key.endswith("_root"):
        _relative_path(value, f"{context}.{key}")


def _valid_sha256(value: Any, field: str) -> str:
    text = str(value or "").strip().lower()
    if not SHA256_PATTERN.fullmatch(text):
        raise RecoveryAuditError("INVALID_SHA256", f"{field} must contain a SHA-256 digest.")
    return text


def _bounded_tail(text: Any, replacements: Iterable[Path] = ()) -> str:
    value = str(text or "")
    replacement_values = {str(path.resolve()) for path in replacements}
    replacement_values.add(str(Path.home().resolve()))
    for sensitive in sorted(replacement_values, key=len, reverse=True):
        if sensitive:
            value = value.replace(sensitive, "<recovery-root>")
    value = re.sub(
        r"(^|[\s(=])/(?:[^\s)'\"<>]+)",
        lambda match: f"{match.group(1)}<absolute-path>",
        value,
        flags=re.MULTILINE,
    )
    value = re.sub(r"\b[A-Za-z]:[\\/][^\s)'\"<>]+", "<absolute-path>", value)
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) > OUTPUT_TAIL_BYTES:
        marker = b"[output-tail-truncated]\n"
        tail_budget = max(0, OUTPUT_TAIL_BYTES - len(marker))
        encoded = encoded[-tail_budget:] if tail_budget else b""
        value = marker.decode("ascii") + encoded.decode("utf-8", errors="ignore")
    else:
        value = encoded.decode("utf-8", errors="replace")
    return value


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        process.terminate()
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
    else:
        process.kill()
    process.wait()


def run_bounded_command(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    display_argv: list[str] | None = None,
    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS,
    max_output_bytes: int = MAX_COMMAND_OUTPUT_BYTES,
    sensitive_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    """Run one command without retaining unbounded output or machine-local paths."""

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            process = subprocess.Popen(
                argv,
                cwd=str(cwd),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                start_new_session=os.name == "posix",
            )
        except OSError as exc:
            return {
                "status": "FAIL",
                "command": list(display_argv or argv),
                "returncode": 127,
                "stdout_tail": "",
                "stderr_tail": _bounded_tail(exc, sensitive_roots),
            }

        deadline = time.monotonic() + timeout_seconds
        failure_status = ""
        while process.poll() is None:
            output_size = os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size
            if output_size > max_output_bytes:
                failure_status = "OUTPUT_LIMIT"
                _terminate_process(process)
                break
            if time.monotonic() >= deadline:
                failure_status = "TIMEOUT"
                _terminate_process(process)
                break
            time.sleep(0.02)

        output_size = os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size
        if output_size > max_output_bytes and not failure_status:
            failure_status = "OUTPUT_LIMIT"
        stdout_file.seek(max(0, os.fstat(stdout_file.fileno()).st_size - OUTPUT_TAIL_BYTES))
        stderr_file.seek(max(0, os.fstat(stderr_file.fileno()).st_size - OUTPUT_TAIL_BYTES))
        stdout = stdout_file.read(OUTPUT_TAIL_BYTES).decode("utf-8", errors="replace")
        stderr = stderr_file.read(OUTPUT_TAIL_BYTES).decode("utf-8", errors="replace")
        returncode = int(process.returncode if process.returncode is not None else -1)
        return {
            "status": "PASS" if returncode == 0 and not failure_status else "FAIL",
            "command": list(display_argv or argv),
            "returncode": returncode,
            "failure_status": failure_status,
            "stdout_tail": _bounded_tail(stdout, sensitive_roots),
            "stderr_tail": _bounded_tail(stderr, sensitive_roots),
        }


def run_frontend_command(argv: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    return run_bounded_command(
        argv,
        cwd=cwd,
        env=env,
        display_argv=argv,
        sensitive_roots=(cwd,),
    )


def _safe_environment(workspace: Path | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    if workspace is not None:
        home = workspace / ".home"
        cache = workspace / ".npm-cache"
        home.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        env["HOME"] = str(home)
        env["npm_config_cache"] = str(cache)
        env["NPM_CONFIG_UPDATE_NOTIFIER"] = "false"
    return env


def build_recovery_plan(repo_root: Path, commit: str) -> list[list[str]]:
    """Return the portable command plan for one immutable candidate commit."""

    if not EXACT_COMMIT_PATTERN.fullmatch(str(commit or "")):
        raise RecoveryAuditError("EXACT_COMMIT_REQUIRED", "A full hexadecimal commit ID is required.")
    if not (Path(repo_root) / ".git").exists():
        raise RecoveryAuditError("GIT_REPOSITORY_REQUIRED", "repo_root must be a non-bare Git working tree.")
    return [
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        ["git", "archive", "--format=tar", "--output=recovery.tar", commit],
        ["python3", PUBLIC_RAW_AUDITOR_PATH.as_posix(), "--database-dir", "."],
        ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        ["npm", "run", "build"],
    ]


def _extract_archive_safely(archive_path: Path, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    file_count = 0
    try:
        archive = tarfile.open(archive_path, mode="r:")
    except (OSError, tarfile.TarError) as exc:
        raise RecoveryAuditError("GIT_ARCHIVE_INVALID", "git archive did not produce a valid tar file.") from exc
    with archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
                raise RecoveryAuditError("GIT_ARCHIVE_UNSAFE", "git archive contains an unsafe path.")
            if ".git" in pure.parts or member.issym() or member.islnk() or member.isdev():
                raise RecoveryAuditError("GIT_ARCHIVE_UNSAFE", "git archive contains a forbidden member type.")
            normalized = pure.as_posix().rstrip("/")
            if normalized in seen:
                raise RecoveryAuditError("GIT_ARCHIVE_UNSAFE", "git archive contains duplicate paths.")
            seen.add(normalized)
            target = _resolve_under(destination, Path(*pure.parts), "GIT_ARCHIVE_UNSAFE")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise RecoveryAuditError("GIT_ARCHIVE_UNSAFE", "git archive contains an unsupported member type.")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RecoveryAuditError("GIT_ARCHIVE_INVALID", "git archive member could not be read.")
            with source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            target.chmod(member.mode & 0o777)
            file_count += 1
    if file_count <= 0:
        raise RecoveryAuditError("GIT_ARCHIVE_EMPTY", "git archive contains no tracked files.")
    return file_count


def _find_database_dir(recovered_root: Path) -> tuple[Path, str]:
    nested = recovered_root / "OpenAIDatabase"
    if (nested / "scripts").is_dir() and (nested / "apps/memory-atlas").is_dir():
        return nested, "OpenAIDatabase"
    if (recovered_root / "scripts").is_dir() and (recovered_root / "apps/memory-atlas").is_dir():
        return recovered_root, "."
    raise RecoveryAuditError("DATABASE_ROOT_MISSING", "Recovered archive does not contain OpenAIDatabase.")


def _snapshot_counts(snapshot: dict[str, Any]) -> dict[str, int]:
    overview = snapshot.get("overview") if isinstance(snapshot.get("overview"), dict) else {}
    counts: dict[str, int] = {}
    for key, value in overview.items():
        if isinstance(value, int) and not isinstance(value, bool):
            counts[str(key)] = value
    nodes = snapshot.get("nodes")
    edges = snapshot.get("edges")
    if isinstance(nodes, list):
        counts.setdefault("node_count", len(nodes))
    if isinstance(edges, list):
        counts.setdefault("edge_count", len(edges))
    return counts


def _release_value(manifest: dict[str, Any], flat_key: str, nested_key: str) -> Any:
    value = manifest.get(flat_key)
    if value is not None and value != "":
        return value
    nested = manifest.get(nested_key)
    if isinstance(nested, dict):
        if flat_key.endswith("_path"):
            return nested.get("relative_path") or nested.get("path")
        if flat_key.endswith("_sha256"):
            return nested.get("sha256")
    return None


def _source_package_records(
    manifest: dict[str, Any],
) -> tuple[Path, str, int, tuple[dict[str, Any], ...]]:
    value = manifest.get("source_packages")
    if not isinstance(value, dict):
        raise RecoveryAuditError(
            "SOURCE_PACKAGE_RELEASE_METADATA_MISSING",
            "Release manifest must record the source-package manifest and files.",
        )
    manifest_path = _relative_path(value.get("manifest_path"), "release.source_packages.manifest_path")
    manifest_sha256 = _valid_sha256(value.get("manifest_sha256"), "source package manifest")
    try:
        manifest_size_bytes = int(value.get("manifest_size_bytes"))
    except (TypeError, ValueError) as exc:
        raise RecoveryAuditError(
            "SOURCE_PACKAGE_RELEASE_METADATA_INVALID",
            "Release source-package manifest size is invalid.",
        ) from exc
    value = value.get("files")
    if not isinstance(value, list) or not value:
        raise RecoveryAuditError(
            "SOURCE_PACKAGE_RELEASE_METADATA_MISSING",
            "Release manifest must record source-package file paths and hashes.",
        )
    rows = []
    for item in value:
        if not isinstance(item, dict):
            raise RecoveryAuditError(
                "SOURCE_PACKAGE_RELEASE_METADATA_INVALID",
                "Release source-package metadata must contain objects.",
            )
        path_value = item.get("relative_path") or item.get("path") or item.get("storage_path")
        path = _relative_path(path_value, "release.source_packages.relative_path")
        rows.append({**item, "relative_path": path.as_posix(), "sha256": _valid_sha256(item.get("sha256"), "source package")})
    return manifest_path, manifest_sha256, manifest_size_bytes, tuple(rows)


def _load_release_contract(database_dir: Path) -> tuple[ReleaseContract, dict[str, Any]]:
    pointer = _load_json(database_dir / CURRENT_RELEASE_PATH, "CURRENT_RELEASE_MISSING")
    _assert_relative_manifest_paths(pointer, "current_release")
    if pointer.get("schema_version") != "memory_atlas.current_release.v1":
        raise RecoveryAuditError("CURRENT_RELEASE_SCHEMA_INVALID", "Current release pointer schema is invalid.")
    release_id = str(pointer.get("release_id") or "").strip()
    if not SAFE_RELEASE_ID_PATTERN.fullmatch(release_id):
        raise RecoveryAuditError("RELEASE_ID_INVALID", "Current release must contain a portable release ID.")

    manifest_value = pointer.get("release_manifest_path") or pointer.get("manifest_path")
    if manifest_value:
        manifest_relative = _relative_path(manifest_value, "current_release.release_manifest_path")
    else:
        manifest_relative = RELEASE_ROOT / release_id / "release_manifest.json"
    expected_manifest_relative = RELEASE_ROOT / release_id / "release_manifest.json"
    if manifest_relative != expected_manifest_relative:
        raise RecoveryAuditError(
            "RELEASE_MANIFEST_PATH_MISMATCH",
            "Current release manifest path does not match its release ID.",
        )
    manifest_path = _resolve_under(database_dir, manifest_relative, "RELEASE_MANIFEST_PATH_INVALID")
    manifest = _load_json(manifest_path, "RELEASE_MANIFEST_MISSING")
    _assert_relative_manifest_paths(manifest, "release_manifest")
    if manifest.get("schema_version") != "memory_atlas.release_manifest.v1":
        raise RecoveryAuditError("RELEASE_MANIFEST_SCHEMA_INVALID", "Release manifest schema is invalid.")
    if str(manifest.get("release_id") or "") != release_id:
        raise RecoveryAuditError("RELEASE_ID_MISMATCH", "Current pointer and release manifest identify different releases.")

    snapshot_relative = _relative_path(
        _release_value(manifest, "snapshot_path", "snapshot") or pointer.get("snapshot_path"),
        "release.snapshot_path",
    )
    expected_snapshot_relative = RELEASE_ROOT / release_id / "memory_atlas.json"
    if snapshot_relative != expected_snapshot_relative:
        raise RecoveryAuditError(
            "RELEASE_SNAPSHOT_PATH_MISMATCH",
            "Immutable release snapshot path does not match its release ID.",
        )
    pointer_snapshot = _relative_path(pointer.get("snapshot_path"), "current_release.snapshot_path")
    if pointer_snapshot != snapshot_relative:
        raise RecoveryAuditError(
            "CURRENT_RELEASE_PATH_MISMATCH",
            "Current release pointer and release manifest use different snapshot paths.",
        )
    snapshot_sha256 = _valid_sha256(
        _release_value(manifest, "snapshot_sha256", "snapshot") or pointer.get("snapshot_sha256"),
        "release.snapshot_sha256",
    )
    raw_manifest_relative = _relative_path(
        _release_value(manifest, "raw_manifest_path", "raw_manifest"),
        "release.raw_manifest_path",
    )
    raw_manifest_sha256 = _valid_sha256(
        _release_value(manifest, "raw_manifest_sha256", "raw_manifest"),
        "release.raw_manifest_sha256",
    )
    snapshot_path = _resolve_under(database_dir, snapshot_relative, "RELEASE_SNAPSHOT_PATH_INVALID")
    raw_manifest_path = _resolve_under(database_dir, raw_manifest_relative, "RAW_MANIFEST_PATH_INVALID")
    if not snapshot_path.is_file():
        raise RecoveryAuditError("RELEASE_SNAPSHOT_MISSING", "Immutable release snapshot is missing.")
    if sha256_file(snapshot_path) != snapshot_sha256:
        raise RecoveryAuditError("RELEASE_SNAPSHOT_HASH_MISMATCH", "Immutable release snapshot hash does not match its manifest.")
    if not raw_manifest_path.is_file():
        raise RecoveryAuditError("RAW_MANIFEST_MISSING", "Release raw manifest is missing.")
    if sha256_file(raw_manifest_path) != raw_manifest_sha256:
        raise RecoveryAuditError("RAW_MANIFEST_HASH_MISMATCH", "Raw manifest hash does not match the release manifest.")
    snapshot_record = manifest.get("snapshot")
    if not isinstance(snapshot_record, dict) or snapshot_record.get("size_bytes") != snapshot_path.stat().st_size:
        raise RecoveryAuditError("RELEASE_SNAPSHOT_SIZE_MISMATCH", "Immutable release snapshot size does not match its manifest.")
    raw_manifest_record = manifest.get("raw_manifest")
    if not isinstance(raw_manifest_record, dict) or raw_manifest_record.get("size_bytes") != raw_manifest_path.stat().st_size:
        raise RecoveryAuditError("RAW_MANIFEST_SIZE_MISMATCH", "Raw manifest size does not match the release manifest.")

    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryAuditError("RELEASE_SNAPSHOT_INVALID", "Immutable release snapshot is invalid JSON.") from exc
    if not isinstance(snapshot, dict):
        raise RecoveryAuditError("RELEASE_SNAPSHOT_INVALID", "Immutable release snapshot must be an object.")
    expected_counts = manifest.get("snapshot_counts")
    if not isinstance(expected_counts, dict):
        nested_snapshot = manifest.get("snapshot")
        expected_counts = nested_snapshot.get("counts") if isinstance(nested_snapshot, dict) else None
    if not isinstance(expected_counts, dict) or not expected_counts:
        raise RecoveryAuditError("RELEASE_COUNTS_MISSING", "Release manifest must record snapshot counts.")
    actual_counts = _snapshot_counts(snapshot)
    normalized_counts: dict[str, int] = {}
    for key, value in expected_counts.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise RecoveryAuditError("RELEASE_COUNTS_INVALID", "Release snapshot counts must be integers.")
        normalized_counts[str(key)] = value
        if actual_counts.get(str(key)) != value:
            raise RecoveryAuditError("RELEASE_COUNTS_MISMATCH", "Release snapshot counts do not match snapshot content.")

    derived_path = database_dir / DERIVED_SNAPSHOT_PATH
    if not derived_path.is_file():
        raise RecoveryAuditError("DERIVED_SNAPSHOT_MISSING", "Tracked derived snapshot is missing.")
    if sha256_file(derived_path) != snapshot_sha256:
        raise RecoveryAuditError("DERIVED_SNAPSHOT_MISMATCH", "Tracked derived snapshot does not match the immutable release.")
    pointer_sha = pointer.get("snapshot_sha256")
    if pointer_sha is not None and _valid_sha256(pointer_sha, "current release snapshot") != snapshot_sha256:
        raise RecoveryAuditError("CURRENT_RELEASE_HASH_MISMATCH", "Current release pointer hash does not match its manifest.")

    (
        source_manifest_path,
        source_manifest_sha256,
        source_manifest_size_bytes,
        source_packages,
    ) = _source_package_records(manifest)
    contract = ReleaseContract(
        release_id=release_id,
        manifest_path=manifest_relative,
        snapshot_path=snapshot_relative,
        snapshot_sha256=snapshot_sha256,
        raw_manifest_path=raw_manifest_relative,
        raw_manifest_sha256=raw_manifest_sha256,
        source_package_manifest_path=source_manifest_path,
        source_package_manifest_sha256=source_manifest_sha256,
        source_package_manifest_size_bytes=source_manifest_size_bytes,
        source_packages=source_packages,
        snapshot_counts=normalized_counts,
    )
    result = {
        "status": "PASS",
        "release_id": release_id,
        "release_manifest_path": manifest_relative.as_posix(),
        "snapshot_path": snapshot_relative.as_posix(),
        "snapshot_sha256": snapshot_sha256,
        "snapshot_counts": normalized_counts,
        "derived_snapshot_path": DERIVED_SNAPSHOT_PATH.as_posix(),
        "raw_manifest_path": raw_manifest_relative.as_posix(),
        "raw_manifest_sha256": raw_manifest_sha256,
    }
    return contract, result


def _audit_source_packages(database_dir: Path, contract: ReleaseContract) -> dict[str, Any]:
    if contract.source_package_manifest_path != SOURCE_PACKAGE_MANIFEST:
        raise RecoveryAuditError(
            "SOURCE_PACKAGE_RELEASE_METADATA_MISMATCH",
            "Release source-package manifest path does not match the recovery contract.",
        )
    manifest_path = database_dir / SOURCE_PACKAGE_MANIFEST
    manifest = _load_json(manifest_path, "SOURCE_PACKAGE_MANIFEST_MISSING")
    if (
        sha256_file(manifest_path) != contract.source_package_manifest_sha256
        or manifest_path.stat().st_size != contract.source_package_manifest_size_bytes
    ):
        raise RecoveryAuditError(
            "SOURCE_PACKAGE_RELEASE_METADATA_MISMATCH",
            "Tracked source-package manifest does not match the immutable release metadata.",
        )
    _assert_relative_manifest_paths(manifest, "source_package_manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) < 2:
        raise RecoveryAuditError("SOURCE_PACKAGE_MANIFEST_INVALID", "Source package manifest must contain both source files.")
    release_records = {str(row["relative_path"]): row for row in contract.source_packages}
    restored_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="memory-atlas-source-restore-") as temp_dir:
        restore_root = Path(temp_dir)
        for item in files:
            if not isinstance(item, dict):
                raise RecoveryAuditError("SOURCE_PACKAGE_MANIFEST_INVALID", "Source package file metadata is invalid.")
            original = _relative_path(item.get("original_name"), "source_package.original_name")
            storage = _relative_path(item.get("storage_name"), "source_package.storage_name")
            if len(original.parts) != 1 or len(storage.parts) != 1:
                raise RecoveryAuditError("SOURCE_PACKAGE_MANIFEST_INVALID", "Source package names must not contain directories.")
            expected_sha = _valid_sha256(item.get("sha256"), "source package manifest")
            try:
                expected_size = int(item.get("size"))
            except (TypeError, ValueError) as exc:
                raise RecoveryAuditError("SOURCE_PACKAGE_MANIFEST_INVALID", "Source package size is invalid.") from exc
            storage_relative = SOURCE_PACKAGE_ROOT / storage
            source = database_dir / storage_relative
            if not source.is_file():
                raise RecoveryAuditError("SOURCE_PACKAGE_MISSING", "A tracked source-package part is missing.")
            if source.stat().st_size != expected_size or sha256_file(source) != expected_sha:
                raise RecoveryAuditError("SOURCE_PACKAGE_HASH_MISMATCH", "A tracked source-package part failed hash validation.")

            release_record = release_records.get(storage_relative.as_posix())
            if release_record is None:
                matching = [
                    row
                    for row in contract.source_packages
                    if Path(str(row["relative_path"])).name in {storage.name, original.name}
                ]
                release_record = matching[0] if len(matching) == 1 else None
            if release_record is None or str(release_record.get("sha256")) != expected_sha:
                raise RecoveryAuditError(
                    "SOURCE_PACKAGE_RELEASE_METADATA_MISMATCH",
                    "Release source-package metadata does not match tracked source inputs.",
                )
            if release_record.get("size_bytes") is not None:
                try:
                    release_size = int(release_record["size_bytes"])
                except (TypeError, ValueError) as exc:
                    raise RecoveryAuditError(
                        "SOURCE_PACKAGE_RELEASE_METADATA_MISMATCH",
                        "Release source-package size metadata is invalid.",
                    ) from exc
                if release_size != expected_size:
                    raise RecoveryAuditError(
                        "SOURCE_PACKAGE_RELEASE_METADATA_MISMATCH",
                        "Release source-package size does not match tracked source inputs.",
                    )

            mode = str(item.get("restore_mode") or "")
            if mode not in {"copy", "copy_part_to_original_name"}:
                raise RecoveryAuditError("SOURCE_PACKAGE_RESTORE_MODE_INVALID", "Source package restore mode is unsupported.")
            restored = restore_root / original.name
            shutil.copyfile(source, restored)
            if restored.stat().st_size != expected_size or sha256_file(restored) != expected_sha:
                raise RecoveryAuditError("SOURCE_PACKAGE_RESTORE_MISMATCH", "Restored source package failed hash validation.")
            if restored.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(restored) as archive:
                        bad_member = archive.testzip()
                        archive_file_count = len(archive.infolist())
                except (OSError, zipfile.BadZipFile) as exc:
                    raise RecoveryAuditError("SOURCE_PACKAGE_ZIP_INVALID", "Restored TaskPack is not a valid ZIP archive.") from exc
                if bad_member is not None or archive_file_count <= 0:
                    raise RecoveryAuditError("SOURCE_PACKAGE_ZIP_INVALID", "Restored TaskPack ZIP failed integrity validation.")
            restored_rows.append(
                {
                    "original_name": original.name,
                    "storage_path": storage_relative.as_posix(),
                    "sha256": expected_sha,
                    "size_bytes": expected_size,
                }
            )
    return {
        "status": "PASS",
        "source_package_manifest": SOURCE_PACKAGE_MANIFEST.as_posix(),
        "source_package_manifest_sha256": contract.source_package_manifest_sha256,
        "restored_file_count": len(restored_rows),
        "files": restored_rows,
    }


def _normalize_raw_relative(value: Any, field: str) -> Path:
    relative = _relative_path(value, field)
    public_parts = PUBLIC_RAW_ROOT.parts
    if relative.parts[: len(public_parts)] == public_parts:
        relative = Path(*relative.parts[len(public_parts) :])
    if not relative.parts:
        raise RecoveryAuditError("RAW_PATH_INVALID", "Raw path must identify a file below data/public_raw.")
    return relative


def _iter_public_raw_files(database_dir: Path) -> list[Path]:
    raw_root = database_dir / PUBLIC_RAW_ROOT
    if not raw_root.is_dir():
        return []
    files = []
    for path in raw_root.rglob("*"):
        if not path.is_file() or path.name in IGNORED_PUBLIC_RAW_NAMES:
            continue
        relative = path.relative_to(raw_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        files.append(path)
    return sorted(files)


def _run_public_raw_auditor(database_dir: Path) -> dict[str, Any]:
    script_path = database_dir / PUBLIC_RAW_AUDITOR_PATH
    if not script_path.is_file():
        raise RecoveryAuditError("PUBLIC_RAW_AUDITOR_MISSING", "Full public-raw auditor is missing.")
    module_name = f"memory_atlas_public_raw_audit_{hashlib.sha256(str(script_path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RecoveryAuditError("PUBLIC_RAW_AUDITOR_INVALID", "Full public-raw auditor could not be loaded.")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    previous_bytecode = sys.dont_write_bytecode
    previous_modules = set(sys.modules)
    scripts_path = str(script_path.parent)
    inserted_scripts_path = scripts_path not in sys.path
    if inserted_scripts_path:
        sys.path.insert(0, scripts_path)
    sys.modules[module_name] = module
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
        audit = getattr(module, "audit_public_raw", None)
        if not callable(audit):
            raise RecoveryAuditError("PUBLIC_RAW_AUDITOR_INVALID", "Full public-raw auditor has no audit_public_raw API.")
        result = audit(database_dir=database_dir, max_file_bytes=MAX_PUBLIC_RAW_FILE_BYTES)
    except RecoveryAuditError:
        raise
    except Exception as exc:
        raise RecoveryAuditError("PUBLIC_RAW_AUDIT_FAILED", "Full public-raw audit raised an error.") from exc
    finally:
        sys.dont_write_bytecode = previous_bytecode
        if inserted_scripts_path:
            try:
                sys.path.remove(scripts_path)
            except ValueError:
                pass
        scripts_root = script_path.parent.resolve()
        for imported_name in set(sys.modules) - previous_modules:
            imported = sys.modules.get(imported_name)
            imported_file = getattr(imported, "__file__", None)
            if not imported_file:
                continue
            try:
                Path(imported_file).resolve().relative_to(scripts_root)
            except (OSError, ValueError):
                continue
            sys.modules.pop(imported_name, None)
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
    if not isinstance(result, dict) or result.get("status") != "PASS":
        raise RecoveryAuditError("PUBLIC_RAW_AUDIT_FAILED", "Full public-raw audit did not pass.")
    raw_file_count = result.get("raw_file_count")
    if raw_file_count is None:
        raw_file_count = result.get("audited_file_count")
    if raw_file_count is None:
        raw_file_count = result.get("public_raw_file_count")
    if raw_file_count is None:
        raw_file_count = result.get("file_count")
    return {
        "status": "PASS",
        "raw_file_count": int(raw_file_count or 0),
        "finding_count": int(result.get("finding_count") or result.get("failed_check_count") or 0),
    }


def _audit_raw_integrity(database_dir: Path, contract: ReleaseContract) -> dict[str, Any]:
    raw_manifest_path = database_dir / contract.raw_manifest_path
    rows = _load_jsonl(raw_manifest_path, "RAW_MANIFEST_MISSING", "RAW_MANIFEST_INVALID")
    if not rows:
        raise RecoveryAuditError("RAW_MANIFEST_EMPTY", "Raw manifest must contain imported public raw files.")
    ledger_rows = _load_jsonl(database_dir / RAW_LEDGER_PATH, "RAW_LEDGER_MISSING", "RAW_LEDGER_INVALID")
    if not ledger_rows:
        raise RecoveryAuditError("RAW_LEDGER_EMPTY", "Raw hash ledger must not be empty.")
    raw_root = database_dir / PUBLIC_RAW_ROOT
    raw_files = _iter_public_raw_files(database_dir)
    if not raw_files:
        raise RecoveryAuditError("PUBLIC_RAW_EMPTY", "Public raw archive must not be empty.")

    manifest_by_path: dict[str, dict[str, Any]] = {}
    source_ids: set[str] = set()
    for row in rows:
        relative = _normalize_raw_relative(row.get("relative_path"), "raw_manifest.relative_path")
        key = relative.as_posix()
        if key in manifest_by_path:
            raise RecoveryAuditError("RAW_MANIFEST_DUPLICATE", "Raw manifest contains duplicate paths.")
        path = _resolve_under(raw_root, relative, "RAW_PATH_INVALID")
        if not path.is_file():
            raise RecoveryAuditError("RAW_FILE_MISSING", "Raw manifest references a missing public raw file.")
        expected_sha = _valid_sha256(row.get("sha256"), "raw manifest")
        if sha256_file(path) != expected_sha:
            raise RecoveryAuditError("RAW_FILE_HASH_MISMATCH", "Public raw file hash does not match its manifest.")
        if row.get("size_bytes") is not None and int(row["size_bytes"]) != path.stat().st_size:
            raise RecoveryAuditError("RAW_FILE_SIZE_MISMATCH", "Public raw file size does not match its manifest.")
        manifest_by_path[key] = row
        source_ids.add(str(row.get("source_id") or ""))

    required_sources = {"chatgpt", "codex"}
    if not required_sources.issubset(source_ids) or not any(source.startswith("agent:") for source in source_ids):
        raise RecoveryAuditError("RAW_SOURCE_FAMILY_MISSING", "Raw manifest must contain ChatGPT, Codex and agent sources.")

    ledger_by_path: dict[str, dict[str, Any]] = {}
    for row in ledger_rows:
        relative = _normalize_raw_relative(row.get("relative_path"), "raw_ledger.relative_path")
        key = relative.as_posix()
        if key in ledger_by_path:
            raise RecoveryAuditError("RAW_LEDGER_DUPLICATE", "Raw hash ledger contains duplicate paths.")
        path = _resolve_under(raw_root, relative, "RAW_PATH_INVALID")
        if not path.is_file():
            raise RecoveryAuditError("RAW_LEDGER_DELETED_FILE", "Raw hash ledger references a deleted public raw file.")
        expected_sha = _valid_sha256(row.get("sha256"), "raw hash ledger")
        if sha256_file(path) != expected_sha:
            raise RecoveryAuditError("RAW_LEDGER_HASH_MISMATCH", "Raw hash ledger contains hash drift.")
        ledger_by_path[key] = row

    actual_paths = {path.relative_to(raw_root).as_posix() for path in raw_files}
    if actual_paths != set(manifest_by_path):
        raise RecoveryAuditError("RAW_MANIFEST_COVERAGE_MISMATCH", "Raw manifest does not cover the current public raw archive exactly.")
    if not set(manifest_by_path).issubset(ledger_by_path):
        raise RecoveryAuditError("RAW_LEDGER_COVERAGE_MISMATCH", "Raw hash ledger does not cover the current raw manifest.")
    for key, row in manifest_by_path.items():
        if str(row.get("sha256")) != str(ledger_by_path[key].get("sha256")):
            raise RecoveryAuditError("RAW_LEDGER_HASH_MISMATCH", "Raw manifest and hash ledger disagree.")

    privacy = _run_public_raw_auditor(database_dir)
    if privacy["raw_file_count"] != len(raw_files):
        raise RecoveryAuditError("PUBLIC_RAW_AUDIT_COVERAGE_MISMATCH", "Full public-raw audit covered a different file set.")
    return {
        "status": "PASS",
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "raw_manifest_path": contract.raw_manifest_path.as_posix(),
        "raw_manifest_sha256": contract.raw_manifest_sha256,
        "hash_ledger_path": RAW_LEDGER_PATH.as_posix(),
        "raw_file_count": len(raw_files),
        "manifest_entry_count": len(rows),
        "ledger_entry_count": len(ledger_rows),
        "source_ids": sorted(source_ids),
        "public_raw_audit": privacy,
    }


def audit_recovered_tree(database_dir: Path) -> dict[str, Any]:
    """Audit one already recovered OpenAIDatabase tree without building the frontend."""

    database_dir = Path(database_dir)
    if not database_dir.is_dir():
        raise RecoveryAuditError("DATABASE_ROOT_MISSING", "Recovered OpenAIDatabase root is missing.")
    contract, release = _load_release_contract(database_dir)
    source_packages = _audit_source_packages(database_dir, contract)
    raw_integrity = _audit_raw_integrity(database_dir, contract)
    return {
        "status": "PASS",
        "database_dir": ".",
        "source_packages": source_packages,
        "raw_integrity": raw_integrity,
        "release": release,
    }


def _normalized_command_result(
    result: Any,
    roots: Iterable[Path],
    expected_command: list[str],
) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise RecoveryAuditError("COMMAND_RESULT_INVALID", "Command runner returned an invalid result.")
    command = result.get("command")
    if command is not None and (not isinstance(command, list) or not all(isinstance(item, str) for item in command)):
        raise RecoveryAuditError("COMMAND_RESULT_INVALID", "Command runner omitted its portable command.")
    return {
        "status": "PASS" if result.get("status") == "PASS" else "FAIL",
        "command": list(expected_command),
        "returncode": int(result.get("returncode") if result.get("returncode") is not None else -1),
        "failure_status": str(result.get("failure_status") or ""),
        "stdout_tail": _bounded_tail(result.get("stdout_tail"), roots),
        "stderr_tail": _bounded_tail(result.get("stderr_tail"), roots),
    }


def _run_frontend_recovery(database_dir: Path, workspace: Path, release_sha256: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frontend = database_dir / FRONTEND_PATH
    if not (frontend / "package.json").is_file() or not (frontend / "package-lock.json").is_file():
        raise RecoveryAuditError("FRONTEND_PACKAGE_MISSING", "Recovered frontend package or lockfile is missing.")
    if (frontend / "node_modules").exists():
        raise RecoveryAuditError("FRONTEND_NOT_FRESH", "Tracked archive unexpectedly contains node_modules.")
    env = _safe_environment(workspace)
    commands = [
        (["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], "NPM_CI_FAILED"),
        (["npm", "run", "build"], "FRONTEND_BUILD_FAILED"),
    ]
    results: list[dict[str, Any]] = []
    for argv, failure_code in commands:
        normalized = _normalized_command_result(
            run_frontend_command(argv, cwd=frontend, env=env),
            (database_dir, workspace, frontend),
            argv,
        )
        results.append(normalized)
        if normalized["status"] != "PASS":
            raise RecoveryAuditError(
                failure_code,
                "Fresh frontend dependency recovery or build failed.",
                command=normalized["command"],
                returncode=normalized["returncode"],
                failure_status=normalized["failure_status"],
                stdout_tail=normalized["stdout_tail"],
                stderr_tail=normalized["stderr_tail"],
                commands=results,
            )

    pages_snapshot = database_dir / PAGES_SNAPSHOT_PATH
    if not pages_snapshot.is_file():
        raise RecoveryAuditError("PAGES_SNAPSHOT_MISSING", "Frontend build did not produce the Pages snapshot.")
    pages_sha256 = sha256_file(pages_snapshot)
    if pages_sha256 != release_sha256:
        raise RecoveryAuditError("PAGES_SNAPSHOT_MISMATCH", "Built Pages snapshot does not match the immutable release.")
    return results, {
        "status": "PASS",
        "pages_snapshot_path": PAGES_SNAPSHOT_PATH.as_posix(),
        "snapshot_sha256": pages_sha256,
    }


def _failure_payload(error: RecoveryAuditError, roots: Iterable[Path]) -> dict[str, Any]:
    payload = {"code": error.code, "message": error.message}
    for key, value in error.details.items():
        if key in {"stdout_tail", "stderr_tail"}:
            payload[key] = _bounded_tail(value, roots)
        elif key == "command" and isinstance(value, list):
            payload[key] = [str(item) for item in value]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            payload[key] = value
    return payload


def rehearse_recovery(repo_root: Path, commit: str, output_dir: Path) -> dict[str, Any]:
    """Recover one exact commit, audit it, build it, verify parity and clean up."""

    repo_root = Path(repo_root)
    output_dir = Path(output_dir)
    created_workspace = False
    workspace_preexisted = output_dir.exists()
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL",
        "commit": str(commit or ""),
        "remote_clone_verified": False,
        "r8_delivery_performed": False,
    }
    try:
        plan = build_recovery_plan(repo_root, commit)
        result["plan"] = plan
        if output_dir.exists():
            raise RecoveryAuditError("OUTPUT_DIR_EXISTS", "Recovery output directory must not already exist.")
        repo_resolved = repo_root.resolve()
        output_resolved = output_dir.resolve()
        try:
            output_resolved.relative_to(repo_resolved)
        except ValueError:
            pass
        else:
            raise RecoveryAuditError("OUTPUT_DIR_INSIDE_REPOSITORY", "Recovery output directory must be outside the repository.")

        resolve_result = run_bounded_command(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=repo_root,
            env=_safe_environment(),
            display_argv=plan[0],
            sensitive_roots=(repo_root,),
        )
        if resolve_result["status"] != "PASS" or resolve_result["stdout_tail"].strip().lower() != commit.lower():
            raise RecoveryAuditError("COMMIT_NOT_FOUND", "Exact candidate commit could not be resolved in the repository.")

        output_dir.mkdir(parents=True, exist_ok=False)
        created_workspace = True
        archive_path = output_dir / "recovery.tar"
        recovered_root = output_dir / "recovered"
        git_result = run_bounded_command(
            ["git", "archive", "--format=tar", f"--output={archive_path}", commit],
            cwd=repo_root,
            env=_safe_environment(output_dir),
            display_argv=plan[1],
            sensitive_roots=(repo_root, output_dir),
        )
        if git_result["status"] != "PASS":
            raise RecoveryAuditError(
                "GIT_ARCHIVE_FAILED",
                "git archive failed for the exact candidate commit.",
                stderr_tail=git_result.get("stderr_tail", ""),
            )
        tracked_file_count = _extract_archive_safely(archive_path, recovered_root)
        archive_path.unlink()
        database_dir, database_relative = _find_database_dir(recovered_root)

        tree_audit = audit_recovered_tree(database_dir)
        command_results, pages_parity = _run_frontend_recovery(
            database_dir,
            output_dir,
            str(tree_audit["release"]["snapshot_sha256"]),
        )
        result.update(
            {
                "status": "PASS",
                "database_dir": database_relative,
                "archive": {
                    "status": "PASS",
                    "source": "git_tracked_files_only",
                    "format": "tar",
                    "tracked_file_count": tracked_file_count,
                    "working_tree_files_copied": 0,
                },
                "source_packages": tree_audit["source_packages"],
                "raw_integrity": tree_audit["raw_integrity"],
                "release": tree_audit["release"],
                "commands": command_results,
                "pages_parity": pages_parity,
            }
        )
    except RecoveryAuditError as exc:
        result["status"] = "FAIL"
        if isinstance(exc.details.get("commands"), list):
            result["commands"] = exc.details["commands"]
        result["failure"] = _failure_payload(exc, (repo_root, output_dir))
    except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        result["status"] = "FAIL"
        result["failure"] = {
            "code": "RECOVERY_IO_FAILED",
            "message": "Recovery rehearsal failed during isolated filesystem processing.",
            "stderr_tail": _bounded_tail(exc, (repo_root, output_dir)),
        }
    except Exception:
        result["status"] = "FAIL"
        result["failure"] = {
            "code": "RECOVERY_INTERNAL_FAILED",
            "message": "Recovery rehearsal stopped on an unexpected internal error.",
        }
    finally:
        cleanup_error = ""
        if created_workspace:
            try:
                shutil.rmtree(output_dir)
            except OSError as exc:
                cleanup_error = _bounded_tail(exc, (repo_root, output_dir))
        removed = not output_dir.exists()
        cleanup_succeeded = (removed and not cleanup_error) if created_workspace else True
        result["cleanup"] = {
            "status": "PASS" if cleanup_succeeded else "FAIL",
            "workspace_created": created_workspace,
            "output_dir_removed": removed,
            "preexisting_output_preserved": workspace_preexisted and output_dir.exists(),
            "npm_cache_removed": removed if created_workspace else True,
            "recovered_tree_removed": removed if created_workspace else True,
        }
        if created_workspace and (cleanup_error or not removed):
            result["status"] = "FAIL"
            result["failure"] = {
                "code": "RECOVERY_CLEANUP_FAILED",
                "message": "Recovery workspace cleanup did not complete.",
                "stderr_tail": cleanup_error,
            }
    return result


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(serialized, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Git working-tree root")
    parser.add_argument("--commit", required=True, help="exact 40- or 64-hex candidate commit")
    parser.add_argument("--output-dir", required=True, help="nonexistent temporary recovery directory")
    parser.add_argument("--status-output", help="optional JSON evidence output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = rehearse_recovery(Path(args.repo_root), args.commit, Path(args.output_dir))
    if args.status_output:
        _write_json_atomic(Path(args.status_output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
