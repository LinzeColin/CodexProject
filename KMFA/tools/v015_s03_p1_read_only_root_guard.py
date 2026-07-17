#!/usr/bin/env python3
"""Fail-closed read/hash root guard for KMFA v1.5 S03-P1.

The production surface deliberately exposes no application-level mutation
operation.  It validates one exact policy root, captures setup/pre/post
snapshots without following links, and combines snapshot equality with a
recursive Darwin kqueue vnode monitor.  Detailed receipts use opaque path
tokens only; public projections contain neither paths, tokens, nor hashes.

TaskPack-authorized ``read``/``hash`` calls can let the OS update file atime.
That kernel side effect is observed and disclosed separately from prohibited
content/namespace/security metadata mutation.  The guard never restores atime
and never claims absolute zero metadata mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import select
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence


POLICY_SCHEMA_VERSION = "kmfa.v015.s03_p1.read_only_root_policy.v1"
PRIVATE_RECEIPT_SCHEMA_VERSION = (
    "kmfa.v015.s03_p1.read_only_root_guard.private_receipt.v2"
)
PUBLIC_RECEIPT_SCHEMA_VERSION = (
    "kmfa.v015.s03_p1.read_only_root_guard.public_projection.v2"
)
FAILURE_SENTINEL_SCHEMA_VERSION = (
    "kmfa.v015.s03_p1.read_only_root_guard.failure_sentinel.v1"
)
EXPECTED_ALLOWED_OPERATIONS = ("list", "read", "stat", "hash")
EXPECTED_SOURCE_SCOPE_ID = "LOCAL_RAW_INBOX_V15"
EXPECTED_ALLOWED_EXTENSIONS = (".xlsx", ".zip")
EXPECTED_MAX_DEPTH = 0
CONTROLLED_WINDOW_SECONDS = 0.25
FINAL_DRAIN_SECONDS = 0.25
DEFAULT_PRIVATE_RUNTIME_DIR = Path(
    "KMFA/.codex_private_runtime/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"
)
DEFAULT_POLICY_PATH = DEFAULT_PRIVATE_RUNTIME_DIR / "private_root_policy.json"
DEFAULT_PRIVATE_RECEIPT_PATH = (
    DEFAULT_PRIVATE_RUNTIME_DIR / "private_guard_receipt.json"
)
DEFAULT_PUBLIC_PROJECTION_PATH = (
    DEFAULT_PRIVATE_RUNTIME_DIR / "public_guard_projection.json"
)
DEFAULT_FAILURE_SENTINEL_PATH = (
    DEFAULT_PRIVATE_RUNTIME_DIR / "public_guard_failure_sentinel.json"
)

_ROOT_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_EXTENSION_RE = re.compile(r"^\.[a-z0-9][a-z0-9._+-]*$")
_HASH_CHUNK_SIZE = 1024 * 1024
_PROJECT_ID = "KMFA"
_TARGET_RELEASE = "v1.5"
_STAGE_ID = "S03"
_PHASE_ID = "S03-P1"


class GuardError(RuntimeError):
    """Base class carrying a stable, public-safe failure code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class PolicyError(GuardError):
    pass


class RootBoundaryError(GuardError):
    pass


class SnapshotError(GuardError):
    pass


class SnapshotDriftError(GuardError):
    pass


class MonitorError(GuardError):
    pass


@dataclass(frozen=True)
class RootPolicy:
    root_id: str
    root_path: Path = field(repr=False)
    source_scope_id: str
    max_depth: int
    allowed_operations: tuple[str, ...]
    allowed_extensions: tuple[str, ...]
    default_deny_extensions: bool


@dataclass(frozen=True)
class SnapshotEntry:
    path_token: str
    kind: str
    device: int
    inode: int
    mode: int
    uid: int
    gid: int
    link_count: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int
    flags: int
    content_sha256: Optional[str] = None
    os_atime_side_effect_observed: bool = field(default=False, compare=False)
    _atime_before_operation_ns: Optional[int] = field(
        default=None,
        repr=False,
        compare=False,
    )
    _atime_after_operation_ns: Optional[int] = field(
        default=None,
        repr=False,
        compare=False,
    )

    def private_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "path_token": self.path_token,
            "kind": self.kind,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "uid": self.uid,
            "gid": self.gid,
            "link_count": self.link_count,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
            "ctime_ns": self.ctime_ns,
            "flags": self.flags,
            "os_atime_side_effect_observed": self.os_atime_side_effect_observed,
        }
        if self.content_sha256 is not None:
            value["content_sha256"] = self.content_sha256
        return value


@dataclass(frozen=True)
class WatchTarget:
    root_path: Path = field(repr=False)
    relative_parts: tuple[str, ...] = field(repr=False)
    device: int
    inode: int
    mode: int


@dataclass(frozen=True)
class RootSnapshot:
    root_id: str
    entries: tuple[SnapshotEntry, ...]
    snapshot_sha256: str
    file_count: int
    directory_count: int
    os_atime_side_effect_observed: bool = field(compare=False)
    os_atime_side_effect_count: int = field(compare=False)
    _watch_targets: Mapping[str, WatchTarget] = field(repr=False, compare=False)

    def watch_paths(self) -> dict[str, Path]:
        return {
            token: target.root_path.joinpath(*target.relative_parts)
            for token, target in self._watch_targets.items()
        }

    def watch_targets(self) -> dict[str, WatchTarget]:
        return dict(self._watch_targets)


@dataclass(frozen=True)
class MonitorEvent:
    path_token: str
    flags: tuple[str, ...]


@dataclass(frozen=True)
class OutputExpectation:
    path: Path = field(repr=False)
    parent_path: Path = field(repr=False)
    filename: str = field(repr=False)
    parent_device: int
    parent_inode: int


class MonitorBackend(Protocol):
    name: str

    def start(self, watch_targets: dict[str, WatchTarget]) -> None:
        ...

    def poll(self, timeout_seconds: float) -> list[MonitorEvent]:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class GuardRunResult:
    status: str
    policy: RootPolicy = field(repr=False)
    setup_snapshot: RootSnapshot
    pre_snapshot: RootSnapshot
    post_snapshot: Optional[RootSnapshot]
    setup_to_pre: Mapping[str, Any]
    pre_to_post: Mapping[str, Any]
    monitor_backend: str
    monitor_production_attested: bool
    controlled_window_seconds: float
    final_drain_seconds: float
    monitor_status: str
    monitor_events: tuple[MonitorEvent, ...]
    prohibited_raw_mutation_detected: bool
    os_atime_side_effect_observed: bool
    os_atime_side_effect_count: int
    failure_codes: tuple[str, ...]


def _require_mapping(value: Any, *, code: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PolicyError(code, f"{label} must be an object")
    return value


def validate_policy_payload(payload: Mapping[str, Any]) -> RootPolicy:
    """Validate a single-root, exact-operation, extension-default-deny policy."""

    policy = _require_mapping(payload, code="POLICY_NOT_OBJECT", label="policy")
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise PolicyError("POLICY_SCHEMA_DRIFT", "policy schema_version mismatch")
    if "roots" in policy:
        raise PolicyError("MULTIPLE_ROOTS_FORBIDDEN", "policy must declare one root")

    root = _require_mapping(
        policy.get("root"),
        code="ROOT_POLICY_MISSING",
        label="root",
    )
    if set(root) != {"root_id", "path"}:
        raise PolicyError(
            "ROOT_POLICY_FIELDS_DRIFT",
            "root must contain only root_id and path",
        )
    root_id = root.get("root_id")
    if not isinstance(root_id, str) or _ROOT_ID_RE.fullmatch(root_id) is None:
        raise PolicyError("ROOT_ID_INVALID", "root_id must be a stable public token")
    root_path_text = root.get("path")
    if not isinstance(root_path_text, str) or not root_path_text:
        raise PolicyError("ROOT_PATH_INVALID", "root path must be a non-empty string")
    root_path = Path(root_path_text)
    if not root_path.is_absolute():
        raise PolicyError("ROOT_PATH_NOT_ABSOLUTE", "root path must be absolute")
    normalized = Path(os.path.abspath(os.path.normpath(root_path_text)))
    if root_path != normalized or ".." in root_path.parts:
        raise PolicyError("ROOT_PATH_NOT_EXACT", "root path must be normalized and exact")

    source_scope_id = policy.get("source_scope_id")
    if source_scope_id != EXPECTED_SOURCE_SCOPE_ID:
        raise PolicyError(
            "SOURCE_SCOPE_UNREGISTERED",
            "source scope is not the registered S03-P1 scope",
        )
    max_depth = policy.get("max_depth")
    if isinstance(max_depth, bool) or not isinstance(max_depth, int):
        raise PolicyError(
            "MAX_DEPTH_INVALID",
            "max_depth must be an integer",
        )
    if max_depth != EXPECTED_MAX_DEPTH:
        raise PolicyError(
            "MAX_DEPTH_DRIFT",
            "max_depth must match the registered source scope",
        )

    operations = policy.get("allowed_operations")
    if not isinstance(operations, list) or any(
        not isinstance(item, str) for item in operations
    ):
        raise PolicyError(
            "ALLOWED_OPERATIONS_INVALID",
            "allowed_operations must be a string list",
        )
    if tuple(operations) != EXPECTED_ALLOWED_OPERATIONS:
        raise PolicyError(
            "ALLOWED_OPERATIONS_DRIFT",
            "allowed operations must be exactly list/read/stat/hash",
        )

    default_deny = policy.get("default_deny_extensions")
    if default_deny is not True:
        raise PolicyError(
            "EXTENSION_DEFAULT_DENY_REQUIRED",
            "extension policy must be default deny",
        )
    extensions = policy.get("allowed_extensions")
    if not isinstance(extensions, list) or not extensions:
        raise PolicyError(
            "ALLOWED_EXTENSIONS_INVALID",
            "allowed_extensions must be a non-empty list",
        )
    if any(
        not isinstance(item, str) or _EXTENSION_RE.fullmatch(item) is None
        for item in extensions
    ):
        raise PolicyError(
            "ALLOWED_EXTENSIONS_INVALID",
            "extensions must be unique lowercase dot-prefixed values",
        )
    if len(set(extensions)) != len(extensions) or extensions != sorted(extensions):
        raise PolicyError(
            "ALLOWED_EXTENSIONS_DRIFT",
            "allowed_extensions must be unique and sorted",
        )
    if tuple(extensions) != EXPECTED_ALLOWED_EXTENSIONS:
        raise PolicyError(
            "ALLOWED_EXTENSIONS_SCOPE_DRIFT",
            "allowed_extensions must match the registered source scope",
        )

    return RootPolicy(
        root_id=root_id,
        root_path=root_path,
        source_scope_id=source_scope_id,
        max_depth=max_depth,
        allowed_operations=tuple(operations),
        allowed_extensions=tuple(extensions),
        default_deny_extensions=True,
    )


def _validate_policy_instance(policy: RootPolicy) -> None:
    if not isinstance(policy, RootPolicy):
        raise PolicyError("POLICY_INSTANCE_INVALID", "policy must be RootPolicy")
    validated = validate_policy_payload(
        {
            "schema_version": POLICY_SCHEMA_VERSION,
            "root": {
                "root_id": policy.root_id,
                "path": str(policy.root_path),
            },
            "source_scope_id": policy.source_scope_id,
            "max_depth": policy.max_depth,
            "allowed_operations": list(policy.allowed_operations),
            "default_deny_extensions": policy.default_deny_extensions,
            "allowed_extensions": list(policy.allowed_extensions),
        }
    )
    if validated != policy:
        raise PolicyError("POLICY_INSTANCE_DRIFT", "policy instance is not canonical")


def _read_json_without_following(path: Path) -> Mapping[str, Any]:
    try:
        value = os.lstat(path)
    except FileNotFoundError as exc:
        raise PolicyError("POLICY_FILE_MISSING", "fixed policy file is missing") from exc
    except OSError as exc:
        raise PolicyError("POLICY_FILE_UNREADABLE", "fixed policy file is unreadable") from exc
    if stat.S_ISLNK(value.st_mode):
        raise PolicyError("POLICY_FILE_SYMLINK", "policy file must not be a symlink")
    if not stat.S_ISREG(value.st_mode):
        raise PolicyError("POLICY_FILE_NOT_REGULAR", "policy file must be regular")

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PolicyError("POLICY_FILE_UNREADABLE", "fixed policy file is unreadable") from exc
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (value.st_dev, value.st_ino):
            raise PolicyError("POLICY_FILE_IDENTITY_DRIFT", "policy identity changed")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, _HASH_CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    try:
        decoded = json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError("POLICY_JSON_INVALID", "policy must be valid UTF-8 JSON") from exc
    return _require_mapping(decoded, code="POLICY_NOT_OBJECT", label="policy")


def load_policy(path: Optional[Path] = None) -> RootPolicy:
    """Load a policy; the CLI always calls this with the fixed default path."""

    selected = DEFAULT_POLICY_PATH if path is None else Path(path)
    return validate_policy_payload(_read_json_without_following(selected))


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def _validate_root(policy: RootPolicy) -> os.stat_result:
    root = policy.root_path
    try:
        value = os.lstat(root)
    except FileNotFoundError as exc:
        raise RootBoundaryError("ROOT_MISSING", "configured root does not exist") from exc
    except OSError as exc:
        raise RootBoundaryError("ROOT_UNREADABLE", "configured root cannot be inspected") from exc
    if stat.S_ISLNK(value.st_mode):
        raise RootBoundaryError("ROOT_SYMLINK", "configured root must not be a symlink")
    if not stat.S_ISDIR(value.st_mode):
        raise RootBoundaryError("ROOT_NOT_DIRECTORY", "configured root must be a directory")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise RootBoundaryError("ROOT_UNRESOLVABLE", "configured root is not resolvable") from exc
    if resolved != root:
        raise RootBoundaryError(
            "ROOT_PATH_NOT_CANONICAL",
            "configured root must not traverse symlinked ancestors",
        )
    if not os.access(root, os.R_OK | os.X_OK):
        raise RootBoundaryError("ROOT_NOT_READABLE", "configured root is not readable")
    return value


def validate_output_paths(
    root: Path,
    paths: Sequence[Path],
) -> tuple[OutputExpectation, ...]:
    """Reject lexical or symlink-resolved receipt outputs within the raw root."""

    root_path = Path(root).resolve(strict=True)
    seen: set[Path] = set()
    expectations: list[OutputExpectation] = []
    for raw_path in paths:
        expectation = _capture_output_expectation(Path(raw_path))
        candidate = expectation.path
        real_candidate = Path(os.path.realpath(candidate))
        if _is_within(root_path, candidate) or _is_within(root_path, real_candidate):
            raise RootBoundaryError(
                "OUTPUT_INSIDE_ROOT",
                "receipt output must be outside configured root",
            )
        if real_candidate in seen:
            raise RootBoundaryError("OUTPUT_PATH_DUPLICATE", "receipt outputs must differ")
        seen.add(real_candidate)
        expectations.append(expectation)
    return tuple(expectations)


def _capture_output_expectation(path: Path) -> OutputExpectation:
    candidate = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    if candidate.name in {"", ".", ".."}:
        raise RootBoundaryError(
            "OUTPUT_NAME_INVALID",
            "receipt output name is invalid",
        )
    parent = candidate.parent
    try:
        parent_lstat = os.lstat(parent)
    except OSError as exc:
        raise RootBoundaryError(
            "OUTPUT_PARENT_UNAVAILABLE",
            "receipt output parent is unavailable",
        ) from exc
    if stat.S_ISLNK(parent_lstat.st_mode):
        raise RootBoundaryError(
            "OUTPUT_PARENT_SYMLINK",
            "receipt output parent must not be a symlink",
        )
    if not stat.S_ISDIR(parent_lstat.st_mode):
        raise RootBoundaryError(
            "OUTPUT_PARENT_NOT_DIRECTORY",
            "receipt output parent must be a directory",
        )
    if parent.resolve(strict=True) != parent:
        raise RootBoundaryError(
            "OUTPUT_PARENT_NOT_CANONICAL",
            "receipt output parent must have canonical ancestors",
        )
    return OutputExpectation(
        path=candidate,
        parent_path=parent,
        filename=candidate.name,
        parent_device=int(parent_lstat.st_dev),
        parent_inode=int(parent_lstat.st_ino),
    )


def _path_token(root_id: str, relative_path: str) -> str:
    value = hashlib.sha256(
        (root_id + "\x00" + relative_path).encode("utf-8", errors="surrogateescape")
    ).hexdigest()
    return "PATH-" + value


def _prohibited_fingerprint_signature(value: os.stat_result) -> tuple[int, ...]:
    """Return the prohibited-mutation fingerprint, deliberately excluding atime.

    Reading and hashing are explicitly allowed and can update atime on APFS.
    Content, identity, permissions, ownership, size, mtime, ctime, link count,
    and filesystem flags remain protected by this fail-closed fingerprint.
    """

    return (
        int(value.st_dev),
        int(value.st_ino),
        int(value.st_mode),
        int(value.st_uid),
        int(value.st_gid),
        int(value.st_nlink),
        int(value.st_size),
        int(value.st_mtime_ns),
        int(value.st_ctime_ns),
        int(getattr(value, "st_flags", 0)),
    )


def _snapshot_entry(
    *,
    path_token: str,
    kind: str,
    value: os.stat_result,
    content_sha256: Optional[str] = None,
    os_atime_side_effect_observed: bool = False,
    atime_before_operation_ns: Optional[int] = None,
    atime_after_operation_ns: Optional[int] = None,
) -> SnapshotEntry:
    return SnapshotEntry(
        path_token=path_token,
        kind=kind,
        device=int(value.st_dev),
        inode=int(value.st_ino),
        mode=int(value.st_mode),
        uid=int(value.st_uid),
        gid=int(value.st_gid),
        link_count=int(value.st_nlink),
        size_bytes=int(value.st_size),
        mtime_ns=int(value.st_mtime_ns),
        ctime_ns=int(value.st_ctime_ns),
        flags=int(getattr(value, "st_flags", 0)),
        content_sha256=content_sha256,
        os_atime_side_effect_observed=os_atime_side_effect_observed,
        _atime_before_operation_ns=atime_before_operation_ns,
        _atime_after_operation_ns=atime_after_operation_ns,
    )


def _open_verified_root(policy: RootPolicy) -> tuple[int, os.stat_result]:
    """Open the exact root once and bind all traversal to that directory fd."""

    expected = _validate_root(policy)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(policy.root_path, flags)
    except OSError as exc:
        raise RootBoundaryError(
            "ROOT_OPEN_FAILED",
            "configured root could not be securely opened",
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode):
            raise RootBoundaryError(
                "ROOT_TYPE_DRIFT",
                "opened root is not a directory",
            )
        if _prohibited_fingerprint_signature(
            opened
        ) != _prohibited_fingerprint_signature(expected):
            raise RootBoundaryError(
                "ROOT_IDENTITY_DRIFT",
                "configured root changed before secure open",
            )
        return descriptor, opened
    except Exception:
        os.close(descriptor)
        raise


def _hash_regular_descriptor(
    descriptor: int,
    expected: os.stat_result,
) -> tuple[str, os.stat_result, int, int]:
    """Hash an open fd, observe atime, and verify prohibited fields stay stable."""

    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise SnapshotError("FILE_TYPE_DRIFT", "opened object is not a regular file")
    if _prohibited_fingerprint_signature(
        before
    ) != _prohibited_fingerprint_signature(expected):
        raise SnapshotError("FILE_IDENTITY_DRIFT", "file changed before read")
    digest = hashlib.sha256()
    while True:
        chunk = os.read(descriptor, _HASH_CHUNK_SIZE)
        if not chunk:
            break
        digest.update(chunk)
    after = os.fstat(descriptor)
    if _prohibited_fingerprint_signature(
        after
    ) != _prohibited_fingerprint_signature(before):
        raise SnapshotError("FILE_CHANGED_DURING_READ", "file changed during read")
    return (
        digest.hexdigest(),
        after,
        int(before.st_atime_ns),
        int(after.st_atime_ns),
    )


def capture_snapshot(policy: RootPolicy) -> RootSnapshot:
    """Capture one root through a verified dirfd without path-based reopen."""

    _validate_policy_instance(policy)
    root_descriptor, root_before = _open_verified_root(policy)
    entries: list[SnapshotEntry] = []
    watch_targets: dict[str, WatchTarget] = {}
    allowed_extensions = frozenset(policy.allowed_extensions)
    root_token = _path_token(policy.root_id, ".")
    watch_targets[root_token] = WatchTarget(
        root_path=policy.root_path,
        relative_parts=(),
        device=int(root_before.st_dev),
        inode=int(root_before.st_ino),
        mode=int(root_before.st_mode),
    )
    root_atime_before_list_ns = int(root_before.st_atime_ns)
    root_atime_after_list_ns = root_atime_before_list_ns
    try:
        try:
            with os.scandir(root_descriptor) as iterator:
                child_names = sorted(entry.name for entry in iterator)
        except OSError as exc:
            raise SnapshotError(
                "DIRECTORY_LIST_FAILED",
                "root directory could not be listed through its verified fd",
            ) from exc
        root_after_list = os.fstat(root_descriptor)
        if _prohibited_fingerprint_signature(
            root_after_list
        ) != _prohibited_fingerprint_signature(root_before):
            raise SnapshotError(
                "DIRECTORY_CHANGED_DURING_SCAN",
                "root directory changed while its entries were listed",
            )
        root_atime_after_list_ns = int(root_after_list.st_atime_ns)

        for name in child_names:
            if (
                not isinstance(name, str)
                or name in {"", ".", ".."}
                or "/" in name
                or "\x00" in name
            ):
                raise SnapshotError(
                    "ENTRY_NAME_INVALID",
                    "root contains an invalid direct-child name",
                )
            relative_depth = 0
            try:
                expected = os.stat(
                    name,
                    dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
            except FileNotFoundError as exc:
                raise SnapshotError(
                    "ENTRY_DISAPPEARED",
                    "entry disappeared during scan",
                ) from exc
            except OSError as exc:
                raise SnapshotError(
                    "ENTRY_LSTAT_FAILED",
                    "entry could not be inspected through the verified root",
                ) from exc
            token = _path_token(policy.root_id, name)
            if stat.S_ISLNK(expected.st_mode):
                raise SnapshotError(
                    "SYMLINK_FORBIDDEN",
                    "symlinks are forbidden in root",
                )
            if stat.S_ISDIR(expected.st_mode):
                if relative_depth >= policy.max_depth:
                    raise SnapshotError(
                        "MAX_DEPTH_EXCEEDED",
                        "a child directory would exceed the registered source depth",
                    )
                raise SnapshotError(
                    "DIRECTORY_SCOPE_UNSUPPORTED",
                    "nested directory traversal is outside this fixed scope",
                )
            if not stat.S_ISREG(expected.st_mode):
                raise SnapshotError(
                    "SPECIAL_FILE_FORBIDDEN",
                    "special filesystem objects are forbidden in root",
                )
            if Path(name).suffix.lower() not in allowed_extensions:
                raise SnapshotError(
                    "UNSUPPORTED_EXTENSION",
                    "file extension is outside the default-deny whitelist",
                )

            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(name, flags, dir_fd=root_descriptor)
            except OSError as exc:
                raise SnapshotError(
                    "FILE_OPEN_FAILED",
                    "regular file could not be opened through the verified root",
                ) from exc
            try:
                (
                    content_hash,
                    opened,
                    atime_before_hash_ns,
                    atime_after_hash_ns,
                ) = _hash_regular_descriptor(descriptor, expected)
            finally:
                os.close(descriptor)
            try:
                linked_after = os.stat(
                    name,
                    dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise SnapshotError(
                    "FILE_PATH_DRIFT",
                    "file path changed after read",
                ) from exc
            if _prohibited_fingerprint_signature(
                linked_after
            ) != _prohibited_fingerprint_signature(opened):
                raise SnapshotError(
                    "FILE_PATH_DRIFT",
                    "file path identity changed during read",
                )
            entries.append(
                _snapshot_entry(
                    path_token=token,
                    kind="file",
                    value=opened,
                    content_sha256=content_hash,
                    os_atime_side_effect_observed=(
                        atime_before_hash_ns != atime_after_hash_ns
                    ),
                    atime_before_operation_ns=atime_before_hash_ns,
                    atime_after_operation_ns=atime_after_hash_ns,
                )
            )
            watch_targets[token] = WatchTarget(
                root_path=policy.root_path,
                relative_parts=(name,),
                device=int(opened.st_dev),
                inode=int(opened.st_ino),
                mode=int(opened.st_mode),
            )

        root_after = os.fstat(root_descriptor)
        if _prohibited_fingerprint_signature(
            root_after
        ) != _prohibited_fingerprint_signature(root_before):
            raise SnapshotError(
                "DIRECTORY_CHANGED_DURING_SCAN",
                "root directory changed during scan",
            )
        try:
            linked_root = os.lstat(policy.root_path)
        except OSError as exc:
            raise SnapshotError(
                "ROOT_PATH_IDENTITY_DRIFT",
                "configured root path disappeared during scan",
            ) from exc
        if (
            stat.S_ISLNK(linked_root.st_mode)
            or _prohibited_fingerprint_signature(
                linked_root
            )
            != _prohibited_fingerprint_signature(root_after)
        ):
            raise SnapshotError(
                "ROOT_PATH_IDENTITY_DRIFT",
                "configured root path changed during scan",
            )
        entries.append(
            _snapshot_entry(
                path_token=root_token,
                kind="directory",
                value=root_after,
                os_atime_side_effect_observed=(
                    root_atime_before_list_ns != root_atime_after_list_ns
                ),
                atime_before_operation_ns=root_atime_before_list_ns,
                atime_after_operation_ns=root_atime_after_list_ns,
            )
        )
    finally:
        os.close(root_descriptor)

    ordered_entries = tuple(sorted(entries, key=lambda item: item.path_token))
    atime_side_effect_count = sum(
        entry.os_atime_side_effect_observed for entry in ordered_entries
    )
    serialized = json.dumps(
        [entry.private_dict() for entry in ordered_entries],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return RootSnapshot(
        root_id=policy.root_id,
        entries=ordered_entries,
        snapshot_sha256=hashlib.sha256(serialized).hexdigest(),
        file_count=sum(entry.kind == "file" for entry in ordered_entries),
        directory_count=sum(entry.kind == "directory" for entry in ordered_entries),
        os_atime_side_effect_observed=bool(atime_side_effect_count),
        os_atime_side_effect_count=atime_side_effect_count,
        _watch_targets=watch_targets,
    )


def compare_snapshots(before: RootSnapshot, after: RootSnapshot) -> dict[str, Any]:
    """Compare prohibited fingerprints; authorized-I/O atime is excluded."""

    if before.root_id != after.root_id:
        raise SnapshotDriftError("ROOT_ID_DRIFT", "snapshot root identifiers differ")
    before_entries = {entry.path_token: entry for entry in before.entries}
    after_entries = {entry.path_token: entry for entry in after.entries}
    before_tokens = set(before_entries)
    after_tokens = set(after_entries)
    added = sorted(after_tokens - before_tokens)
    deleted = sorted(before_tokens - after_tokens)
    kind_changed: list[str] = []
    identity_changed: list[str] = []
    metadata_changed: list[str] = []
    content_changed: list[str] = []

    for token in sorted(before_tokens & after_tokens):
        left = before_entries[token]
        right = after_entries[token]
        if left.kind != right.kind:
            kind_changed.append(token)
        if (left.device, left.inode) != (right.device, right.inode):
            identity_changed.append(token)
        if (
            left.mode,
            left.uid,
            left.gid,
            left.link_count,
            left.size_bytes,
            left.mtime_ns,
            left.ctime_ns,
            left.flags,
        ) != (
            right.mode,
            right.uid,
            right.gid,
            right.link_count,
            right.size_bytes,
            right.mtime_ns,
            right.ctime_ns,
            right.flags,
        ):
            metadata_changed.append(token)
        if left.content_sha256 != right.content_sha256:
            content_changed.append(token)

    equal = not any(
        (
            added,
            deleted,
            kind_changed,
            identity_changed,
            metadata_changed,
            content_changed,
        )
    )
    return {
        "equal": equal,
        "status": "PASS" if equal else "FAIL",
        "added_path_tokens": added,
        "deleted_path_tokens": deleted,
        "kind_changed_path_tokens": kind_changed,
        "identity_changed_path_tokens": identity_changed,
        "metadata_changed_path_tokens": metadata_changed,
        "content_changed_path_tokens": content_changed,
    }


class DarwinKqueueVnodeMonitor:
    """Recursive no-follow vnode monitor used by production on Darwin."""

    name = "darwin_kqueue_vnode_recursive"

    def __init__(self) -> None:
        if sys.platform != "darwin" or not hasattr(select, "kqueue"):
            raise MonitorError(
                "MONITOR_BACKEND_UNSUPPORTED",
                "Darwin kqueue vnode monitoring is required",
            )
        self._queue: Optional[Any] = None
        self._descriptors: dict[int, str] = {}

    @staticmethod
    def _note_flags() -> tuple[tuple[int, str], ...]:
        names = (
            ("KQ_NOTE_DELETE", "DELETE"),
            ("KQ_NOTE_WRITE", "WRITE"),
            ("KQ_NOTE_EXTEND", "EXTEND"),
            ("KQ_NOTE_ATTRIB", "ATTRIB"),
            ("KQ_NOTE_LINK", "LINK"),
            ("KQ_NOTE_RENAME", "RENAME"),
            ("KQ_NOTE_REVOKE", "REVOKE"),
        )
        return tuple(
            (int(getattr(select, constant)), label)
            for constant, label in names
            if hasattr(select, constant)
        )

    def start(self, watch_targets: dict[str, WatchTarget]) -> None:
        if self._queue is not None:
            raise MonitorError("MONITOR_ALREADY_STARTED", "monitor already started")
        if not watch_targets:
            raise MonitorError("MONITOR_WATCH_SET_EMPTY", "monitor watch set is empty")
        root_rows = [
            (token, target)
            for token, target in watch_targets.items()
            if target.relative_parts == ()
        ]
        if len(root_rows) != 1:
            raise MonitorError(
                "MONITOR_ROOT_TARGET_INVALID",
                "monitor requires exactly one root target",
            )
        root_token, root_target = root_rows[0]
        self._queue = select.kqueue()
        changelist: list[Any] = []
        note_mask = 0
        for value, _ in self._note_flags():
            note_mask |= value
        try:
            root_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            root_flags |= getattr(os, "O_CLOEXEC", 0)
            root_flags |= getattr(os, "O_NOFOLLOW", 0)
            root_descriptor = os.open(root_target.root_path, root_flags)
            opened_root = os.fstat(root_descriptor)
            if (
                not stat.S_ISDIR(opened_root.st_mode)
                or (
                    int(opened_root.st_dev),
                    int(opened_root.st_ino),
                    int(opened_root.st_mode),
                )
                != (
                    root_target.device,
                    root_target.inode,
                    root_target.mode,
                )
            ):
                os.close(root_descriptor)
                raise MonitorError(
                    "MONITOR_ROOT_IDENTITY_DRIFT",
                    "root identity changed during monitor setup",
                )
            self._descriptors[root_descriptor] = root_token
            changelist.append(
                select.kevent(
                    root_descriptor,
                    filter=select.KQ_FILTER_VNODE,
                    flags=(
                        select.KQ_EV_ADD
                        | select.KQ_EV_ENABLE
                        | select.KQ_EV_CLEAR
                    ),
                    fflags=note_mask,
                )
            )

            for token, target in sorted(watch_targets.items()):
                if token == root_token:
                    continue
                if target.root_path != root_target.root_path:
                    raise MonitorError(
                        "MONITOR_ROOT_TARGET_DRIFT",
                        "watch targets do not share the verified root",
                    )
                if (
                    len(target.relative_parts) != 1
                    or target.relative_parts[0] in {"", ".", ".."}
                    or "/" in target.relative_parts[0]
                    or "\x00" in target.relative_parts[0]
                ):
                    raise MonitorError(
                        "MONITOR_TARGET_DEPTH_INVALID",
                        "watch target exceeds the fixed direct-child scope",
                    )
                open_flags = os.O_RDONLY
                open_flags |= getattr(os, "O_CLOEXEC", 0)
                open_flags |= getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(
                    target.relative_parts[0],
                    open_flags,
                    dir_fd=root_descriptor,
                )
                opened = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or (
                        int(opened.st_dev),
                        int(opened.st_ino),
                        int(opened.st_mode),
                    )
                    != (target.device, target.inode, target.mode)
                ):
                    os.close(descriptor)
                    raise MonitorError(
                        "MONITOR_IDENTITY_DRIFT",
                        "watch identity changed during monitor setup",
                    )
                self._descriptors[descriptor] = token
                changelist.append(
                    select.kevent(
                        descriptor,
                        filter=select.KQ_FILTER_VNODE,
                        flags=(
                            select.KQ_EV_ADD
                            | select.KQ_EV_ENABLE
                            | select.KQ_EV_CLEAR
                        ),
                        fflags=note_mask,
                    )
                )
            self._queue.control(changelist, 0, 0)
        except GuardError:
            self.close()
            raise
        except OSError as exc:
            self.close()
            raise MonitorError(
                "MONITOR_SETUP_FAILED",
                "recursive vnode monitor setup failed",
            ) from exc

    def poll(self, timeout_seconds: float) -> list[MonitorEvent]:
        if self._queue is None:
            raise MonitorError("MONITOR_NOT_STARTED", "monitor was not started")
        if timeout_seconds < 0 or timeout_seconds > 60:
            raise MonitorError(
                "MONITOR_TIMEOUT_INVALID",
                "monitor timeout must be between 0 and 60 seconds",
            )
        try:
            events = self._queue.control(
                None,
                max(1, len(self._descriptors) * 2),
                timeout_seconds,
            )
        except OSError as exc:
            raise MonitorError("MONITOR_POLL_FAILED", "vnode monitor poll failed") from exc
        note_flags = self._note_flags()
        output: list[MonitorEvent] = []
        for event in events:
            token = self._descriptors.get(int(event.ident))
            if token is None:
                raise MonitorError("MONITOR_UNKNOWN_EVENT", "monitor returned unknown event")
            flags = tuple(label for value, label in note_flags if int(event.fflags) & value)
            if int(event.flags) & int(getattr(select, "KQ_EV_ERROR", 0)):
                flags += ("ERROR",)
            output.append(MonitorEvent(path_token=token, flags=flags or ("UNKNOWN",)))
        return output

    def close(self) -> None:
        for descriptor in tuple(self._descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
        self._descriptors.clear()
        if self._queue is not None:
            try:
                self._queue.close()
            except OSError:
                pass
            self._queue = None


def _validate_monitor_events(
    events: Any,
    watch_targets: Mapping[str, WatchTarget],
) -> tuple[MonitorEvent, ...]:
    if not isinstance(events, list):
        raise MonitorError("MONITOR_EVENTS_INVALID", "monitor events must be a list")
    validated: list[MonitorEvent] = []
    for event in events:
        if not isinstance(event, MonitorEvent):
            raise MonitorError("MONITOR_EVENT_INVALID", "monitor event type is invalid")
        if event.path_token not in watch_targets:
            raise MonitorError("MONITOR_EVENT_OUTSIDE_WATCH", "monitor event is outside watch set")
        if not event.flags or any(not isinstance(item, str) for item in event.flags):
            raise MonitorError("MONITOR_EVENT_FLAGS_INVALID", "monitor event flags are invalid")
        validated.append(event)
    return tuple(validated)


def _failed_comparison(code: str) -> dict[str, Any]:
    return {
        "equal": False,
        "status": "FAIL",
        "capture_error_code": code,
        "added_path_tokens": [],
        "deleted_path_tokens": [],
        "kind_changed_path_tokens": [],
        "identity_changed_path_tokens": [],
        "metadata_changed_path_tokens": [],
        "content_changed_path_tokens": [],
    }


def _event_stop_comparison() -> dict[str, Any]:
    value = _failed_comparison("VNODE_EVENT_DETECTED_BEFORE_POST")
    value.pop("capture_error_code")
    value["stop_reason"] = "VNODE_EVENT_DETECTED_BEFORE_POST"
    return value


def _setup_pre_drift_stop_comparison() -> dict[str, Any]:
    value = _failed_comparison("SETUP_PRE_DRIFT_BEFORE_POST")
    value.pop("capture_error_code")
    value["stop_reason"] = "SETUP_PRE_DRIFT_BEFORE_POST"
    return value


def run_read_only_root_guard(
    policy: RootPolicy,
    *,
    monitor_backend: Optional[MonitorBackend] = None,
    monitor_timeout_seconds: float = 0.0,
    private_receipt_path: Optional[Path] = None,
    public_receipt_path: Optional[Path] = None,
) -> GuardRunResult:
    """Run setup/pre/post snapshots and monitoring without a mutation surface."""

    if monitor_timeout_seconds < 0 or monitor_timeout_seconds > 60:
        raise MonitorError(
            "MONITOR_TIMEOUT_INVALID",
            "monitor timeout must be between 0 and 60 seconds",
        )
    _validate_policy_instance(policy)
    _validate_root(policy)
    output_paths = [
        path
        for path in (private_receipt_path, public_receipt_path)
        if path is not None
    ]
    output_expectations = validate_output_paths(policy.root_path, output_paths)
    expectation_by_path = {
        expectation.path: expectation for expectation in output_expectations
    }

    setup = capture_snapshot(policy)
    monitor: MonitorBackend = monitor_backend or DarwinKqueueVnodeMonitor()
    monitor_name = getattr(monitor, "name", "")
    if (
        not isinstance(monitor_name, str)
        or re.fullmatch(r"[a-z][a-z0-9_]{2,63}", monitor_name) is None
    ):
        raise MonitorError("MONITOR_NAME_INVALID", "monitor backend name is missing")
    watch_targets = setup.watch_targets()
    events: tuple[MonitorEvent, ...] = ()
    post: Optional[RootSnapshot] = None
    post_error_code: Optional[str] = None
    try:
        monitor.start(watch_targets)
        pre = capture_snapshot(policy)
        setup_to_pre = compare_snapshots(setup, pre)
        if not setup_to_pre["equal"]:
            events = _validate_monitor_events(
                monitor.poll(0.0),
                watch_targets,
            )
            pre_to_post = _setup_pre_drift_stop_comparison()
        else:
            initial_events = _validate_monitor_events(
                monitor.poll(monitor_timeout_seconds),
                watch_targets,
            )
            if initial_events:
                events = initial_events
                pre_to_post = _event_stop_comparison()
            else:
                try:
                    post = capture_snapshot(policy)
                    pre_to_post = compare_snapshots(pre, post)
                except SnapshotError as exc:
                    post_error_code = exc.code
                    pre_to_post = _failed_comparison(exc.code)
                final_events = _validate_monitor_events(
                    monitor.poll(FINAL_DRAIN_SECONDS),
                    watch_targets,
                )
                events = final_events
    finally:
        monitor.close()

    failure_codes: list[str] = []
    if not setup_to_pre["equal"]:
        failure_codes.append("SETUP_PRE_DRIFT")
    if post_error_code is not None:
        failure_codes.append("POST_SNAPSHOT_FAILED_" + post_error_code)
    elif (
        not pre_to_post["equal"]
        and pre_to_post.get("stop_reason")
        not in {
            "VNODE_EVENT_DETECTED_BEFORE_POST",
            "SETUP_PRE_DRIFT_BEFORE_POST",
        }
    ):
        failure_codes.append("PRE_POST_DRIFT")
    if events:
        failure_codes.append("VNODE_EVENT_DETECTED")
    prohibited_mutation_detected = bool(
        events or not setup_to_pre["equal"] or not pre_to_post["equal"]
    )
    captured_snapshots = tuple(
        snapshot
        for snapshot in (setup, pre, post)
        if snapshot is not None
    )
    atime_side_effect_count = sum(
        snapshot.os_atime_side_effect_count for snapshot in captured_snapshots
    )
    status = "FAIL" if failure_codes else "PASS"
    result = GuardRunResult(
        status=status,
        policy=policy,
        setup_snapshot=setup,
        pre_snapshot=pre,
        post_snapshot=post,
        setup_to_pre=setup_to_pre,
        pre_to_post=pre_to_post,
        monitor_backend=monitor_name,
        monitor_production_attested=(
            monitor.__class__ is DarwinKqueueVnodeMonitor
        ),
        controlled_window_seconds=float(monitor_timeout_seconds),
        final_drain_seconds=FINAL_DRAIN_SECONDS,
        monitor_status="FAIL" if events else "PASS",
        monitor_events=events,
        prohibited_raw_mutation_detected=prohibited_mutation_detected,
        os_atime_side_effect_observed=bool(atime_side_effect_count),
        os_atime_side_effect_count=atime_side_effect_count,
        failure_codes=tuple(failure_codes),
    )

    forbidden_raw_identities = frozenset(
        (entry.device, entry.inode)
        for snapshot in (setup, pre, post)
        if snapshot is not None
        for entry in snapshot.entries
    )

    if private_receipt_path is not None:
        _write_json_receipt(
            expectation_by_path[
                Path(os.path.abspath(os.path.normpath(os.fspath(private_receipt_path))))
            ],
            build_private_receipt(result),
            mode=0o600,
            forbidden_raw_identities=forbidden_raw_identities,
        )
    if public_receipt_path is not None:
        _write_json_receipt(
            expectation_by_path[
                Path(os.path.abspath(os.path.normpath(os.fspath(public_receipt_path))))
            ],
            build_public_projection(result),
            mode=0o644,
            forbidden_raw_identities=forbidden_raw_identities,
        )
    return result


def _snapshot_private_value(snapshot: Optional[RootSnapshot]) -> dict[str, Any]:
    if snapshot is None:
        return {"status": "NOT_AVAILABLE"}
    return {
        "status": "CAPTURED",
        "snapshot_sha256": snapshot.snapshot_sha256,
        "file_count": snapshot.file_count,
        "directory_count": snapshot.directory_count,
        "entry_count": len(snapshot.entries),
        "os_atime_side_effect_observed": (
            snapshot.os_atime_side_effect_observed
        ),
        "os_atime_side_effect_count": snapshot.os_atime_side_effect_count,
        "entries": [entry.private_dict() for entry in snapshot.entries],
    }


def _root_permission_summary(snapshot: RootSnapshot) -> dict[str, Any]:
    root_token = _path_token(snapshot.root_id, ".")
    root_entry = next(
        (entry for entry in snapshot.entries if entry.path_token == root_token),
        None,
    )
    if root_entry is None or root_entry.kind != "directory":
        raise GuardError(
            "ROOT_PERMISSION_UNKNOWN",
            "root directory metadata is unavailable",
        )
    return {
        "root_readable": True,
        "root_permission_known": True,
        "root_owner_write_bit": bool(root_entry.mode & stat.S_IWUSR),
        "root_group_write_bit": bool(root_entry.mode & stat.S_IWGRP),
        "root_other_write_bit": bool(root_entry.mode & stat.S_IWOTH),
        "root_is_symlink": False,
    }


def build_private_receipt(result: GuardRunResult) -> dict[str, Any]:
    """Build a private receipt containing tokens/hashes but no plaintext paths."""

    value = {
        "schema_version": PRIVATE_RECEIPT_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
        "root_id": result.policy.root_id,
        "status": result.status,
        "failure_codes": list(result.failure_codes),
        "policy": {
            "source_scope_id": result.policy.source_scope_id,
            "max_depth": result.policy.max_depth,
            "allowed_operations": list(result.policy.allowed_operations),
            "allowed_extensions": list(result.policy.allowed_extensions),
            "default_deny_extensions": result.policy.default_deny_extensions,
            "single_exact_root": True,
        },
        "snapshots": {
            "setup": _snapshot_private_value(result.setup_snapshot),
            "pre": _snapshot_private_value(result.pre_snapshot),
            "post": _snapshot_private_value(result.post_snapshot),
        },
        "comparisons": {
            "setup_to_pre": dict(result.setup_to_pre),
            "pre_to_post": dict(result.pre_to_post),
        },
        "monitor": {
            "backend": result.monitor_backend,
            "production_backend_attested": result.monitor_production_attested,
            "controlled_window_seconds": result.controlled_window_seconds,
            "final_drain_seconds": result.final_drain_seconds,
            "status": result.monitor_status,
            "events": [
                {"path_token": event.path_token, "flags": list(event.flags)}
                for event in result.monitor_events
            ],
        },
        "guard": {
            "prohibited_raw_mutation_detected": (
                result.prohibited_raw_mutation_detected
            ),
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": (
                result.os_atime_side_effect_observed
            ),
            "os_atime_side_effect_count": result.os_atime_side_effect_count,
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
            "production_raw_mutation_api_present": False,
            "output_inside_root": False,
            **_root_permission_summary(result.setup_snapshot),
        },
        "privacy": {
            "root_path_plaintext_in_receipt": False,
            "relative_paths_plaintext_in_receipt": False,
            "path_tokens_private_only": True,
            "content_hashes_private_only": True,
            "raw_values_in_receipt": False,
        },
    }
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if str(result.policy.root_path) in serialized:
        raise GuardError("PRIVATE_RECEIPT_PATH_LEAK", "private receipt contains root path")
    _assert_private_receipt_has_no_plaintext_path(value)
    return value


def _receipt_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GuardError("PRIVATE_RECEIPT_INVALID", f"{label} must be an object")
    return value


def _assert_private_receipt_has_no_plaintext_path(value: Any) -> None:
    forbidden_keys = {
        "path",
        "root_path",
        "relative_path",
        "plaintext_path",
        "filename",
        "file_name",
    }
    private_absolute_prefixes = ("/" + "Users/", "/" + "Volumes/")

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if key in forbidden_keys:
                    raise GuardError(
                        "PRIVATE_RECEIPT_PATH_LEAK",
                        "private receipt contains a plaintext path field",
                    )
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)
        elif isinstance(item, str):
            if (
                item.startswith("/")
                or any(prefix in item for prefix in private_absolute_prefixes)
                or re.match(r"^[A-Za-z]:[\\/]", item) is not None
            ):
                raise GuardError(
                    "PRIVATE_RECEIPT_PATH_LEAK",
                    "private receipt contains plaintext path material",
                )

    visit(value)


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: frozenset[str],
    *,
    label: str,
    code: str = "PRIVATE_RECEIPT_INVALID",
) -> None:
    if set(value) != set(expected):
        raise GuardError(
            code,
            f"{label} fields are not canonical",
        )


_SNAPSHOT_ENTRY_BASE_KEYS = frozenset(
    {
        "path_token",
        "kind",
        "device",
        "inode",
        "mode",
        "uid",
        "gid",
        "link_count",
        "size_bytes",
        "mtime_ns",
        "ctime_ns",
        "flags",
        "os_atime_side_effect_observed",
    }
)
_SNAPSHOT_CAPTURED_KEYS = frozenset(
    {
        "status",
        "snapshot_sha256",
        "file_count",
        "directory_count",
        "entry_count",
        "os_atime_side_effect_observed",
        "os_atime_side_effect_count",
        "entries",
    }
)


def _validate_private_snapshot(
    value: Any,
    *,
    label: str,
    root_id: str,
) -> tuple[str, Optional[RootSnapshot]]:
    """Reconstruct and independently hash a private snapshot."""

    snapshot = _receipt_mapping(value, f"snapshots.{label}")
    status_value = snapshot.get("status")
    if status_value == "NOT_AVAILABLE" and label == "post":
        _require_exact_keys(snapshot, frozenset({"status"}), label=f"snapshots.{label}")
        return "NOT_AVAILABLE", None
    if status_value != "CAPTURED":
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label}.status is invalid",
        )
    _require_exact_keys(
        snapshot,
        _SNAPSHOT_CAPTURED_KEYS,
        label=f"snapshots.{label}",
    )
    declared_digest = snapshot.get("snapshot_sha256")
    if (
        not isinstance(declared_digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", declared_digest) is None
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} digest is invalid",
        )
    raw_entries = snapshot.get("entries")
    declared_counts = (
        snapshot.get("file_count"),
        snapshot.get("directory_count"),
        snapshot.get("entry_count"),
    )
    declared_atime_observed = snapshot.get("os_atime_side_effect_observed")
    declared_atime_count = snapshot.get("os_atime_side_effect_count")
    if not isinstance(raw_entries, list) or any(
        isinstance(count, bool) or not isinstance(count, int) or count < 0
        for count in declared_counts
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} accounting is invalid",
        )
    if (
        not isinstance(declared_atime_observed, bool)
        or isinstance(declared_atime_count, bool)
        or not isinstance(declared_atime_count, int)
        or declared_atime_count < 0
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} atime observation accounting is invalid",
        )

    entries: list[SnapshotEntry] = []
    seen_tokens: set[str] = set()
    numeric_fields = (
        "device",
        "inode",
        "mode",
        "uid",
        "gid",
        "link_count",
        "size_bytes",
        "mtime_ns",
        "ctime_ns",
        "flags",
    )
    for raw_entry in raw_entries:
        row = _receipt_mapping(raw_entry, f"snapshots.{label}.entry")
        kind = row.get("kind")
        expected_keys = _SNAPSHOT_ENTRY_BASE_KEYS
        if kind == "file":
            expected_keys = expected_keys | {"content_sha256"}
        _require_exact_keys(
            row,
            frozenset(expected_keys),
            label=f"snapshots.{label}.entry",
        )
        token = row.get("path_token")
        if (
            not isinstance(token, str)
            or re.fullmatch(r"PATH-[a-f0-9]{64}", token) is None
            or token in seen_tokens
        ):
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"snapshots.{label} path token is invalid or duplicated",
            )
        seen_tokens.add(token)
        if kind not in {"file", "directory"}:
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"snapshots.{label} entry kind is invalid",
            )
        atime_observed = row.get("os_atime_side_effect_observed")
        if not isinstance(atime_observed, bool):
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"snapshots.{label} atime observation is invalid",
            )
        for key in numeric_fields:
            number = row.get(key)
            if isinstance(number, bool) or not isinstance(number, int) or number < 0:
                raise GuardError(
                    "PRIVATE_RECEIPT_INVALID",
                    f"snapshots.{label} entry metadata is invalid",
                )
        if row["link_count"] < 1:
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"snapshots.{label} link count is invalid",
            )
        mode = row["mode"]
        if (kind == "file" and not stat.S_ISREG(mode)) or (
            kind == "directory" and not stat.S_ISDIR(mode)
        ):
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"snapshots.{label} kind/mode mismatch",
            )
        content_hash: Optional[str] = None
        if kind == "file":
            content_hash = row.get("content_sha256")
            if (
                not isinstance(content_hash, str)
                or re.fullmatch(r"[a-f0-9]{64}", content_hash) is None
            ):
                raise GuardError(
                    "PRIVATE_RECEIPT_INVALID",
                    f"snapshots.{label} content hash is invalid",
                )
        entries.append(
            SnapshotEntry(
                path_token=token,
                kind=kind,
                device=row["device"],
                inode=row["inode"],
                mode=mode,
                uid=row["uid"],
                gid=row["gid"],
                link_count=row["link_count"],
                size_bytes=row["size_bytes"],
                mtime_ns=row["mtime_ns"],
                ctime_ns=row["ctime_ns"],
                flags=row["flags"],
                content_sha256=content_hash,
                os_atime_side_effect_observed=atime_observed,
            )
        )

    ordered_entries = tuple(sorted(entries, key=lambda item: item.path_token))
    if [entry.path_token for entry in entries] != [
        entry.path_token for entry in ordered_entries
    ]:
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} entries are not canonically ordered",
        )
    file_count = sum(entry.kind == "file" for entry in ordered_entries)
    directory_count = sum(entry.kind == "directory" for entry in ordered_entries)
    atime_side_effect_count = sum(
        entry.os_atime_side_effect_observed for entry in ordered_entries
    )
    if declared_counts != (file_count, directory_count, len(ordered_entries)):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} accounting does not match entries",
        )
    if (
        declared_atime_count != atime_side_effect_count
        or declared_atime_observed is not bool(atime_side_effect_count)
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} atime observation does not match entries",
        )
    root_token = _path_token(root_id, ".")
    root_rows = [entry for entry in ordered_entries if entry.path_token == root_token]
    if len(root_rows) != 1 or root_rows[0].kind != "directory":
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} root entry is missing",
        )
    canonical = json.dumps(
        [entry.private_dict() for entry in ordered_entries],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    recomputed_digest = hashlib.sha256(canonical).hexdigest()
    if recomputed_digest != declared_digest:
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            f"snapshots.{label} digest does not match entries",
        )
    return (
        "CAPTURED",
        RootSnapshot(
            root_id=root_id,
            entries=ordered_entries,
            snapshot_sha256=recomputed_digest,
            file_count=file_count,
            directory_count=directory_count,
            os_atime_side_effect_observed=bool(atime_side_effect_count),
            os_atime_side_effect_count=atime_side_effect_count,
            _watch_targets={},
        ),
    )


def public_projection_from_private_receipt(
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Strictly rebuild a public projection from a private guard receipt."""

    private = _receipt_mapping(receipt, "private receipt")
    _assert_private_receipt_has_no_plaintext_path(private)
    _require_exact_keys(
        private,
        frozenset(
            {
                "schema_version",
                "project_id",
                "target_release",
                "stage_id",
                "phase_id",
                "root_id",
                "status",
                "failure_codes",
                "policy",
                "snapshots",
                "comparisons",
                "monitor",
                "guard",
                "privacy",
            }
        ),
        label="private receipt",
    )
    expected_identity = {
        "schema_version": PRIVATE_RECEIPT_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
    }
    for key, expected in expected_identity.items():
        if private.get(key) != expected:
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                f"private receipt {key} mismatch",
            )
    root_id = private.get("root_id")
    if not isinstance(root_id, str) or _ROOT_ID_RE.fullmatch(root_id) is None:
        raise GuardError("PRIVATE_RECEIPT_INVALID", "private receipt root_id invalid")
    status_value = private.get("status")
    if status_value not in {"PASS", "FAIL"}:
        raise GuardError("PRIVATE_RECEIPT_INVALID", "private receipt status invalid")
    failure_codes = private.get("failure_codes")
    if not isinstance(failure_codes, list) or any(
        not isinstance(item, str) or not item for item in failure_codes
    ):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "failure_codes invalid")
    if (status_value == "PASS") != (failure_codes == []):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "status/failure_codes mismatch")

    policy = _receipt_mapping(private.get("policy"), "policy")
    expected_policy = {
        "source_scope_id": EXPECTED_SOURCE_SCOPE_ID,
        "max_depth": EXPECTED_MAX_DEPTH,
        "allowed_operations": list(EXPECTED_ALLOWED_OPERATIONS),
        "allowed_extensions": list(EXPECTED_ALLOWED_EXTENSIONS),
        "default_deny_extensions": True,
        "single_exact_root": True,
    }
    if dict(policy) != expected_policy:
        raise GuardError("PRIVATE_RECEIPT_INVALID", "policy truth drift")

    snapshots = _receipt_mapping(private.get("snapshots"), "snapshots")
    _require_exact_keys(
        snapshots,
        frozenset({"setup", "pre", "post"}),
        label="snapshots",
    )
    setup_status, setup_snapshot = _validate_private_snapshot(
        snapshots.get("setup"),
        label="setup",
        root_id=root_id,
    )
    pre_status, pre_snapshot = _validate_private_snapshot(
        snapshots.get("pre"),
        label="pre",
        root_id=root_id,
    )
    post_status, post_snapshot = _validate_private_snapshot(
        snapshots.get("post"),
        label="post",
        root_id=root_id,
    )
    if setup_snapshot is None or pre_snapshot is None:
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "setup and pre snapshots must be captured",
        )
    snapshot_statuses = {
        "setup": setup_status,
        "pre": pre_status,
        "post": post_status,
    }

    monitor = _receipt_mapping(private.get("monitor"), "monitor")
    _require_exact_keys(
        monitor,
        frozenset(
            {
                "backend",
                "production_backend_attested",
                "controlled_window_seconds",
                "final_drain_seconds",
                "status",
                "events",
            }
        ),
        label="monitor",
    )
    backend = monitor.get("backend")
    production_attested = monitor.get("production_backend_attested")
    if (
        backend != DarwinKqueueVnodeMonitor.name
        or production_attested is not True
    ):
        raise GuardError(
            "PRODUCTION_MONITOR_REQUIRED",
            "public projection requires an attested Darwin kqueue run",
        )
    controlled_window = monitor.get("controlled_window_seconds")
    final_drain = monitor.get("final_drain_seconds")
    if (
        isinstance(controlled_window, bool)
        or not isinstance(controlled_window, (int, float))
        or float(controlled_window) != CONTROLLED_WINDOW_SECONDS
        or isinstance(final_drain, bool)
        or not isinstance(final_drain, (int, float))
        or float(final_drain) != FINAL_DRAIN_SECONDS
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "monitor timing attestation is invalid",
        )
    monitor_status = monitor.get("status")
    events = monitor.get("events")
    if (
        monitor_status not in {"PASS", "FAIL"}
        or not isinstance(events, list)
    ):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "monitor receipt invalid")
    setup_tokens = {entry.path_token for entry in setup_snapshot.entries}
    for event in events:
        row = _receipt_mapping(event, "monitor event")
        _require_exact_keys(
            row,
            frozenset({"path_token", "flags"}),
            label="monitor event",
        )
        token = row.get("path_token")
        flags = row.get("flags")
        if (
            not isinstance(token, str)
            or re.fullmatch(r"PATH-[a-f0-9]{64}", token) is None
            or token not in setup_tokens
            or not isinstance(flags, list)
            or not flags
            or any(not isinstance(item, str) or not item for item in flags)
            or len(set(flags)) != len(flags)
        ):
            raise GuardError("PRIVATE_RECEIPT_INVALID", "monitor event invalid")

    comparisons = _receipt_mapping(private.get("comparisons"), "comparisons")
    _require_exact_keys(
        comparisons,
        frozenset({"setup_to_pre", "pre_to_post"}),
        label="comparisons",
    )
    setup_to_pre = _receipt_mapping(
        comparisons.get("setup_to_pre"),
        "setup_to_pre",
    )
    expected_setup_to_pre = compare_snapshots(setup_snapshot, pre_snapshot)
    if dict(setup_to_pre) != expected_setup_to_pre:
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "setup/pre comparison does not match reconstructed snapshots",
        )
    pre_to_post = _receipt_mapping(
        comparisons.get("pre_to_post"),
        "pre_to_post",
    )
    post_capture_error: Optional[str] = None
    event_stop = False
    setup_pre_stop = False
    if post_snapshot is not None:
        expected_pre_to_post = compare_snapshots(pre_snapshot, post_snapshot)
        if dict(pre_to_post) != expected_pre_to_post:
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                "pre/post comparison does not match reconstructed snapshots",
            )
    elif pre_to_post.get("stop_reason") == "VNODE_EVENT_DETECTED_BEFORE_POST":
        if dict(pre_to_post) != _event_stop_comparison() or not events:
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                "event-stop comparison is not supported by monitor events",
            )
        event_stop = True
    elif pre_to_post.get("stop_reason") == "SETUP_PRE_DRIFT_BEFORE_POST":
        if (
            dict(pre_to_post) != _setup_pre_drift_stop_comparison()
            or setup_to_pre["equal"]
        ):
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                "setup/pre drift stop is not supported by the comparison",
            )
        setup_pre_stop = True
    else:
        capture_error = pre_to_post.get("capture_error_code")
        if (
            not isinstance(capture_error, str)
            or re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", capture_error) is None
            or dict(pre_to_post) != _failed_comparison(capture_error)
        ):
            raise GuardError(
                "PRIVATE_RECEIPT_INVALID",
                "post capture failure comparison is invalid",
            )
        post_capture_error = capture_error

    guard = _receipt_mapping(private.get("guard"), "guard")
    required_bool_fields = (
        "prohibited_raw_mutation_detected",
        "os_atime_side_effect_possible",
        "os_atime_side_effect_observed",
        "os_atime_restoration_performed",
        "absolute_zero_metadata_mutation_claimed",
        "production_raw_mutation_api_present",
        "output_inside_root",
        "root_readable",
        "root_permission_known",
        "root_owner_write_bit",
        "root_group_write_bit",
        "root_other_write_bit",
        "root_is_symlink",
    )
    _require_exact_keys(
        guard,
        frozenset(required_bool_fields) | {"os_atime_side_effect_count"},
        label="guard",
    )
    if any(not isinstance(guard.get(key), bool) for key in required_bool_fields):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "guard permission truth invalid")
    declared_atime_count = guard.get("os_atime_side_effect_count")
    if (
        isinstance(declared_atime_count, bool)
        or not isinstance(declared_atime_count, int)
        or declared_atime_count < 0
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "guard atime observation count is invalid",
        )
    expected_root_permissions = _root_permission_summary(setup_snapshot)
    if (
        guard.get("os_atime_side_effect_possible") is not True
        or guard.get("os_atime_restoration_performed") is not False
        or guard.get("absolute_zero_metadata_mutation_claimed") is not False
        or guard.get("production_raw_mutation_api_present") is not False
        or guard.get("output_inside_root") is not False
        or any(
            guard.get(key) is not expected
            for key, expected in expected_root_permissions.items()
        )
    ):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "guard boundary truth invalid")

    expected_failure_codes: list[str] = []
    if not setup_to_pre["equal"]:
        expected_failure_codes.append("SETUP_PRE_DRIFT")
    if post_capture_error is not None:
        expected_failure_codes.append("POST_SNAPSHOT_FAILED_" + post_capture_error)
    elif post_snapshot is not None and not pre_to_post["equal"]:
        expected_failure_codes.append("PRE_POST_DRIFT")
    if events:
        expected_failure_codes.append("VNODE_EVENT_DETECTED")
    expected_prohibited_mutation = bool(
        events or not setup_to_pre["equal"] or not pre_to_post["equal"]
    )
    expected_atime_count = sum(
        snapshot.os_atime_side_effect_count
        for snapshot in (setup_snapshot, pre_snapshot, post_snapshot)
        if snapshot is not None
    )
    if failure_codes != expected_failure_codes:
        raise GuardError("PRIVATE_RECEIPT_INVALID", "failure code accounting drift")
    if (
        guard.get("prohibited_raw_mutation_detected")
        is not expected_prohibited_mutation
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "prohibited mutation truth drift",
        )
    if (
        declared_atime_count != expected_atime_count
        or guard.get("os_atime_side_effect_observed")
        is not bool(expected_atime_count)
    ):
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "OS atime side-effect truth drift",
        )
    if monitor_status != ("FAIL" if events else "PASS"):
        raise GuardError("PRIVATE_RECEIPT_INVALID", "monitor status drift")
    if event_stop and post_status != "NOT_AVAILABLE":
        raise GuardError("PRIVATE_RECEIPT_INVALID", "event stop must omit post snapshot")
    if setup_pre_stop and post_status != "NOT_AVAILABLE":
        raise GuardError(
            "PRIVATE_RECEIPT_INVALID",
            "setup/pre drift stop must omit post snapshot",
        )

    privacy = _receipt_mapping(private.get("privacy"), "privacy")
    expected_privacy = {
        "root_path_plaintext_in_receipt": False,
        "relative_paths_plaintext_in_receipt": False,
        "path_tokens_private_only": True,
        "content_hashes_private_only": True,
        "raw_values_in_receipt": False,
    }
    if dict(privacy) != expected_privacy:
        raise GuardError("PRIVATE_RECEIPT_INVALID", "private receipt privacy drift")

    value = {
        "schema_version": PUBLIC_RECEIPT_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
        "root_id": root_id,
        "status": status_value,
        "failure_codes": list(failure_codes),
        "policy": {
            "source_scope_id": EXPECTED_SOURCE_SCOPE_ID,
            "max_depth": EXPECTED_MAX_DEPTH,
            "allowed_operations": list(EXPECTED_ALLOWED_OPERATIONS),
            "allowed_extension_count": len(EXPECTED_ALLOWED_EXTENSIONS),
            "default_deny_extensions": True,
            "single_exact_root": True,
        },
        "snapshots": {
            "setup": snapshot_statuses["setup"],
            "pre": snapshot_statuses["pre"],
            "post": snapshot_statuses["post"],
        },
        "comparisons": {
            "setup_pre_equal": setup_to_pre["equal"],
            "pre_post_equal": pre_to_post["equal"],
        },
        "monitor": {
            "backend": backend,
            "production_backend_attested": True,
            "controlled_window_seconds": float(controlled_window),
            "final_drain_seconds": float(final_drain),
            "status": monitor_status,
            "mutation_event_detected": bool(events),
        },
        "guard": {
            "prohibited_raw_mutation_detected": guard[
                "prohibited_raw_mutation_detected"
            ],
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": guard[
                "os_atime_side_effect_observed"
            ],
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
            "production_raw_mutation_api_present": False,
            "output_inside_root": False,
            "root_readable": guard["root_readable"],
            "root_permission_known": guard["root_permission_known"],
            "root_owner_write_bit": guard["root_owner_write_bit"],
            "root_group_write_bit": guard["root_group_write_bit"],
            "root_other_write_bit": guard["root_other_write_bit"],
            "root_is_symlink": False,
        },
        "privacy": {
            "root_path_committed": False,
            "relative_paths_committed": False,
            "path_tokens_committed": False,
            "content_hashes_committed": False,
            "snapshot_hashes_committed": False,
            "raw_values_committed": False,
        },
    }
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    forbidden_fields = (
        '"path_token":',
        '"content_sha256":',
        '"snapshot_sha256":',
    )
    if any(token in serialized for token in forbidden_fields):
        raise GuardError(
            "PUBLIC_PROJECTION_SAFETY_FAILED",
            "public projection contains private material",
        )
    return validate_public_projection(value)


def validate_public_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Validate public guard truth, including the no-atime-restoration rule."""

    public = _receipt_mapping(projection, "public projection")
    _require_exact_keys(
        public,
        frozenset(
            {
                "schema_version",
                "project_id",
                "target_release",
                "stage_id",
                "phase_id",
                "root_id",
                "status",
                "failure_codes",
                "policy",
                "snapshots",
                "comparisons",
                "monitor",
                "guard",
                "privacy",
            }
        ),
        label="public projection",
        code="PUBLIC_PROJECTION_INVALID",
    )
    expected_identity = {
        "schema_version": PUBLIC_RECEIPT_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
    }
    if any(public.get(key) != expected for key, expected in expected_identity.items()):
        raise GuardError(
            "PUBLIC_PROJECTION_INVALID",
            "public projection identity mismatch",
        )
    status_value = public.get("status")
    failure_codes = public.get("failure_codes")
    if (
        status_value not in {"PASS", "FAIL"}
        or not isinstance(failure_codes, list)
        or any(not isinstance(code, str) or not code for code in failure_codes)
        or (status_value == "PASS") != (failure_codes == [])
    ):
        raise GuardError(
            "PUBLIC_PROJECTION_INVALID",
            "public projection status accounting is invalid",
        )
    public_guard = _receipt_mapping(public.get("guard"), "public guard")
    public_guard_fields = frozenset(
        {
            "prohibited_raw_mutation_detected",
            "os_atime_side_effect_possible",
            "os_atime_side_effect_observed",
            "os_atime_restoration_performed",
            "absolute_zero_metadata_mutation_claimed",
            "production_raw_mutation_api_present",
            "output_inside_root",
            "root_readable",
            "root_permission_known",
            "root_owner_write_bit",
            "root_group_write_bit",
            "root_other_write_bit",
            "root_is_symlink",
        }
    )
    _require_exact_keys(
        public_guard,
        public_guard_fields,
        label="public guard",
        code="PUBLIC_PROJECTION_INVALID",
    )
    if any(not isinstance(public_guard.get(key), bool) for key in public_guard_fields):
        raise GuardError(
            "PUBLIC_PROJECTION_INVALID",
            "public guard truth values must be boolean",
        )
    if (
        public_guard.get("os_atime_side_effect_possible") is not True
        or public_guard.get("os_atime_restoration_performed") is not False
        or public_guard.get("absolute_zero_metadata_mutation_claimed") is not False
        or public_guard.get("production_raw_mutation_api_present") is not False
        or public_guard.get("output_inside_root") is not False
        or public_guard.get("root_readable") is not True
        or public_guard.get("root_permission_known") is not True
        or public_guard.get("root_is_symlink") is not False
    ):
        raise GuardError(
            "PUBLIC_PROJECTION_INVALID",
            "public guard boundary truth is invalid",
        )
    serialized = json.dumps(public, ensure_ascii=False, sort_keys=True)
    if any(
        token in serialized
        for token in ('"path_token":', '"content_sha256":', '"snapshot_sha256":')
    ):
        raise GuardError(
            "PUBLIC_PROJECTION_SAFETY_FAILED",
            "public projection contains private material",
        )
    return dict(public)


def build_public_projection(result: GuardRunResult) -> dict[str, Any]:
    """Build a public projection through the strict private-receipt boundary."""

    return public_projection_from_private_receipt(build_private_receipt(result))


def _write_json_receipt(
    expectation: OutputExpectation,
    payload: Mapping[str, Any],
    *,
    mode: int,
    forbidden_raw_identities: frozenset[tuple[int, int]],
) -> None:
    data = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    parent_flags |= getattr(os, "O_CLOEXEC", 0)
    parent_flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_descriptor = os.open(expectation.parent_path, parent_flags)
    except OSError as exc:
        raise GuardError(
            "OUTPUT_PARENT_OPEN_FAILED",
            "receipt output parent could not be securely opened",
        ) from exc
    expected_parent_identity = (
        expectation.parent_device,
        expectation.parent_inode,
    )
    try:
        opened_parent = os.fstat(parent_descriptor)
        if (
            (int(opened_parent.st_dev), int(opened_parent.st_ino))
            != expected_parent_identity
            or not stat.S_ISDIR(opened_parent.st_mode)
        ):
            raise GuardError(
                "OUTPUT_PARENT_IDENTITY_DRIFT",
                "receipt output parent identity changed before write",
            )
        flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(
                expectation.filename,
                flags,
                mode,
                dir_fd=parent_descriptor,
            )
        except OSError as exc:
            raise GuardError(
                "OUTPUT_WRITE_FAILED",
                "receipt output write failed",
            ) from exc
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise GuardError("OUTPUT_NOT_REGULAR", "receipt output is not regular")
            identity = (int(opened.st_dev), int(opened.st_ino))
            if identity in forbidden_raw_identities:
                raise GuardError(
                    "OUTPUT_RAW_IDENTITY_FORBIDDEN",
                    "receipt output identity belongs to configured root",
                )
            if int(opened.st_nlink) != 1:
                raise GuardError(
                    "OUTPUT_HARDLINK_FORBIDDEN",
                    "receipt output must have exactly one link",
                )
            os.fchmod(descriptor, mode)
            before_truncate = os.fstat(descriptor)
            if (
                (int(before_truncate.st_dev), int(before_truncate.st_ino))
                != identity
                or int(before_truncate.st_nlink) != 1
            ):
                raise GuardError(
                    "OUTPUT_IDENTITY_DRIFT",
                    "receipt output identity changed before truncate",
                )
            os.ftruncate(descriptor, 0)
            offset = 0
            while offset < len(data):
                offset += os.write(descriptor, data[offset:])
            os.fsync(descriptor)
            after_write = os.fstat(descriptor)
            if (
                (int(after_write.st_dev), int(after_write.st_ino)) != identity
                or int(after_write.st_nlink) != 1
                or stat.S_IMODE(after_write.st_mode) != mode
            ):
                raise GuardError(
                    "OUTPUT_POST_WRITE_IDENTITY_DRIFT",
                    "receipt output identity or mode changed during write",
                )
        finally:
            os.close(descriptor)
        after_parent = os.fstat(parent_descriptor)
        current_parent = os.lstat(expectation.parent_path)
        if (
            (int(after_parent.st_dev), int(after_parent.st_ino))
            != expected_parent_identity
            or stat.S_ISLNK(current_parent.st_mode)
            or (int(current_parent.st_dev), int(current_parent.st_ino))
            != expected_parent_identity
        ):
            raise GuardError(
                "OUTPUT_PARENT_POST_WRITE_DRIFT",
                "receipt output parent changed during write",
            )
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)


def _safe_invalidate_output(path: Path) -> None:
    """Remove one stale output without following links or truncating hardlinks."""

    expectation = _capture_output_expectation(path)
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    parent_flags |= getattr(os, "O_CLOEXEC", 0)
    parent_flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_descriptor = os.open(expectation.parent_path, parent_flags)
    except OSError as exc:
        raise GuardError(
            "STALE_OUTPUT_PARENT_OPEN_FAILED",
            "stale output parent could not be securely opened",
        ) from exc
    expected_parent = (expectation.parent_device, expectation.parent_inode)
    try:
        opened_parent = os.fstat(parent_descriptor)
        if (
            (int(opened_parent.st_dev), int(opened_parent.st_ino))
            != expected_parent
            or not stat.S_ISDIR(opened_parent.st_mode)
        ):
            raise GuardError(
                "STALE_OUTPUT_PARENT_IDENTITY_DRIFT",
                "stale output parent changed before invalidation",
            )
        try:
            stale = os.stat(
                expectation.filename,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return
        except OSError as exc:
            raise GuardError(
                "STALE_OUTPUT_INSPECTION_FAILED",
                "stale output could not be inspected",
            ) from exc

        stale_identity = (int(stale.st_dev), int(stale.st_ino))
        if stat.S_ISLNK(stale.st_mode):
            pass
        elif stat.S_ISREG(stale.st_mode):
            if int(stale.st_nlink) != 1:
                raise GuardError(
                    "STALE_OUTPUT_HARDLINK_FORBIDDEN",
                    "stale output hardlink was preserved without truncation",
                )
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(
                    expectation.filename,
                    flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as exc:
                raise GuardError(
                    "STALE_OUTPUT_OPEN_FAILED",
                    "stale output could not be securely opened",
                ) from exc
            try:
                opened = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or (int(opened.st_dev), int(opened.st_ino)) != stale_identity
                    or int(opened.st_nlink) != 1
                ):
                    raise GuardError(
                        "STALE_OUTPUT_IDENTITY_DRIFT",
                        "stale output changed before invalidation",
                    )
            finally:
                os.close(descriptor)
        else:
            raise GuardError(
                "STALE_OUTPUT_NOT_REGULAR",
                "stale output is neither a regular file nor a symlink",
            )

        try:
            current = os.stat(
                expectation.filename,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise GuardError(
                "STALE_OUTPUT_IDENTITY_DRIFT",
                "stale output changed before unlink",
            ) from exc
        if (
            (int(current.st_dev), int(current.st_ino)) != stale_identity
            or (stat.S_ISLNK(current.st_mode) != stat.S_ISLNK(stale.st_mode))
            or (stat.S_ISREG(current.st_mode) and int(current.st_nlink) != 1)
        ):
            raise GuardError(
                "STALE_OUTPUT_IDENTITY_DRIFT",
                "stale output changed before unlink",
            )
        try:
            os.unlink(expectation.filename, dir_fd=parent_descriptor)
            os.fsync(parent_descriptor)
        except OSError as exc:
            raise GuardError(
                "STALE_OUTPUT_UNLINK_FAILED",
                "stale output could not be invalidated",
            ) from exc
        after_parent = os.fstat(parent_descriptor)
        current_parent = os.lstat(expectation.parent_path)
        if (
            (int(after_parent.st_dev), int(after_parent.st_ino)) != expected_parent
            or stat.S_ISLNK(current_parent.st_mode)
            or (int(current_parent.st_dev), int(current_parent.st_ino))
            != expected_parent
        ):
            raise GuardError(
                "STALE_OUTPUT_PARENT_POST_UNLINK_DRIFT",
                "stale output parent changed during invalidation",
            )
    finally:
        os.close(parent_descriptor)


def _failure_payload(error: GuardError) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_RECEIPT_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
        "status": "FAIL",
        "failure_codes": [error.code],
    }


def _failure_sentinel_payload(failure_codes: Sequence[str]) -> dict[str, Any]:
    codes = list(failure_codes)
    if not codes or any(not isinstance(code, str) or not code for code in codes):
        raise GuardError(
            "FAILURE_SENTINEL_INVALID",
            "failure sentinel requires public-safe failure codes",
        )
    return {
        "schema_version": FAILURE_SENTINEL_SCHEMA_VERSION,
        "project_id": _PROJECT_ID,
        "target_release": _TARGET_RELEASE,
        "stage_id": _STAGE_ID,
        "phase_id": _PHASE_ID,
        "status": "FAIL",
        "failure_codes": codes,
        "stale_pass_invalidated": True,
    }


def _result_raw_identities(
    result: GuardRunResult,
) -> frozenset[tuple[int, int]]:
    return frozenset(
        (entry.device, entry.inode)
        for snapshot in (
            result.setup_snapshot,
            result.pre_snapshot,
            result.post_snapshot,
        )
        if snapshot is not None
        for entry in snapshot.entries
    )


def _write_failure_sentinel(
    failure_codes: Sequence[str],
    *,
    forbidden_raw_identities: frozenset[tuple[int, int]],
) -> None:
    expectation = _capture_output_expectation(DEFAULT_FAILURE_SENTINEL_PATH)
    _write_json_receipt(
        expectation,
        _failure_sentinel_payload(failure_codes),
        mode=0o644,
        forbidden_raw_identities=forbidden_raw_identities,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fixed-policy KMFA v1.5 S03-P1 read-only root guard."
    )
    parser.add_argument(
        "--private-receipt",
        type=Path,
        default=DEFAULT_PRIVATE_RECEIPT_PATH,
        help="Compatibility flag; only the fixed private path is accepted.",
    )
    parser.add_argument(
        "--public-receipt",
        type=Path,
        default=DEFAULT_PUBLIC_PROJECTION_PATH,
        help="Compatibility flag; only the fixed public path is accepted.",
    )
    parser.add_argument(
        "--monitor-timeout-seconds",
        type=float,
        default=CONTROLLED_WINDOW_SECONDS,
    )
    args = parser.parse_args(argv)

    try:
        requested_outputs = (
            Path(os.path.abspath(os.path.normpath(os.fspath(args.private_receipt)))),
            Path(os.path.abspath(os.path.normpath(os.fspath(args.public_receipt)))),
        )
        fixed_outputs = (
            Path(
                os.path.abspath(
                    os.path.normpath(os.fspath(DEFAULT_PRIVATE_RECEIPT_PATH))
                )
            ),
            Path(
                os.path.abspath(
                    os.path.normpath(os.fspath(DEFAULT_PUBLIC_PROJECTION_PATH))
                )
            ),
        )
        if requested_outputs != fixed_outputs:
            raise GuardError(
                "OUTPUT_OVERRIDE_FORBIDDEN",
                "production receipt outputs are frozen to the private runtime",
            )
        for stale_path in (
            DEFAULT_PRIVATE_RECEIPT_PATH,
            DEFAULT_PUBLIC_PROJECTION_PATH,
            DEFAULT_FAILURE_SENTINEL_PATH,
        ):
            _safe_invalidate_output(stale_path)
        policy = load_policy()
        result = run_read_only_root_guard(
            policy,
            monitor_timeout_seconds=args.monitor_timeout_seconds,
            private_receipt_path=DEFAULT_PRIVATE_RECEIPT_PATH,
            public_receipt_path=DEFAULT_PUBLIC_PROJECTION_PATH,
        )
        if result.status == "FAIL":
            _write_failure_sentinel(
                result.failure_codes,
                forbidden_raw_identities=_result_raw_identities(result),
            )
        return 0 if result.status == "PASS" else 1
    except GuardError as error:
        for stale_path in (
            DEFAULT_PRIVATE_RECEIPT_PATH,
            DEFAULT_PUBLIC_PROJECTION_PATH,
        ):
            try:
                _safe_invalidate_output(stale_path)
            except GuardError:
                pass
        try:
            _safe_invalidate_output(DEFAULT_FAILURE_SENTINEL_PATH)
            _write_failure_sentinel(
                [error.code],
                forbidden_raw_identities=frozenset(),
            )
        except GuardError:
            pass
        print(
            json.dumps(_failure_payload(error), ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    except Exception:
        error = GuardError(
            "INTERNAL_GUARD_ERROR",
            "unexpected guard failure was converted to fail-closed status",
        )
        for stale_path in (
            DEFAULT_PRIVATE_RECEIPT_PATH,
            DEFAULT_PUBLIC_PROJECTION_PATH,
        ):
            try:
                _safe_invalidate_output(stale_path)
            except GuardError:
                pass
        try:
            _safe_invalidate_output(DEFAULT_FAILURE_SENTINEL_PATH)
            _write_failure_sentinel(
                [error.code],
                forbidden_raw_identities=frozenset(),
            )
        except GuardError:
            pass
        print(
            json.dumps(_failure_payload(error), ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
