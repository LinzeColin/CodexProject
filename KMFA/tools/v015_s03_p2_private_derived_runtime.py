#!/usr/bin/env python3
"""Private derived-runtime primitives for KMFA v1.5 S03-P2.

The module has two deliberately separate capabilities:

* copy policy-authorized, direct-child raw files into an immutable SHA-256 CAS;
* plan retention cleanup, while allowing deletion only in an explicitly marked
  synthetic test runtime after a second, exact-digest confirmation.

Raw paths, names, path tokens, and content hashes are private-only.  The public
projection returned by :func:`build_public_projection` contains aggregates.
There is intentionally no destructive command-line entry point.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import secrets
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from KMFA.tools import v015_s03_p1_read_only_root_guard as p1_guard


PRIVATE_RECEIPT_SCHEMA_VERSION = "kmfa.v015.s03_p2.private_runtime_receipt.v1"
PUBLIC_PROJECTION_SCHEMA_VERSION = (
    "kmfa.v015.s03_p2.public_runtime_projection.v1"
)
RUNTIME_CONTRACT_SCHEMA_VERSION = "kmfa.v015.s03_p2.runtime_contract.v1"
CLEANUP_PLAN_SCHEMA_VERSION = "kmfa.v015.s03_p2.cleanup_plan.v1"
COPY_AUTHORIZATION_SCHEMA_VERSION = "kmfa.v015.s03_p2.copy_authorization.v1"

PROJECT_ID = "KMFA"
TARGET_RELEASE = "v1.5"
STAGE_ID = "S03"
PHASE_ID = "S03-P2"
HASH_ALGORITHM = "sha256"
HASH_CHUNK_SIZE = 1024 * 1024

RUNTIME_LAYERS = (
    "content_mirror",
    "extracted",
    "staging",
    "facts",
    "cache",
    "reports",
    "logs",
    "backups",
    "quarantine",
)
DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
CAS_BLOB_MODE = 0o400
EXPECTED_SOURCE_EXTENSIONS = frozenset({".xlsx", ".zip"})
EXPECTED_COPY_OPERATION = "copy_to_private_content_addressed_mirror"
EXPECTED_COPY_TARGET_LAYER = "content_mirror"
EXPECTED_AUTHORIZATION_SCOPE = "READ_ONLY_CONTENT_ADDRESSED_COPY"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXED_P1_PRIVATE_DIR_RELATIVE = Path(
    "KMFA/.codex_private_runtime/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"
)
FIXED_P1_POLICY_FILENAME = "private_root_policy.json"
FIXED_P1_RECEIPT_FILENAME = "private_guard_receipt.json"
FIXED_RUNTIME_ROOT_RELATIVE = Path("KMFA/local_runtime")

RETENTION_CATEGORIES = (
    "extracted",
    "staging",
    "cache",
    "report_draft",
    "operational_log",
    "backup_duplicate",
)
# The TaskPack defines condition-based retention but no numeric production
# periods.  The canonical default therefore yields no deletion candidates.
# Numeric periods are accepted only when a caller explicitly supplies the
# complete policy (the focused tests use this for synthetic rehearsal only).
DEFAULT_RETENTION_DAYS: Mapping[str, int] = {}

_SYNTHETIC_MARKER_NAME = ".s03_p2_synthetic_cleanup_root"
_SYNTHETIC_MARKER_VALUE = "KMFA_S03_P2_SYNTHETIC_CLEANUP_ONLY_V1\n"
_CONFIRMATION_PREFIX = ".s03_p2_cleanup_confirmation_"


class PrivateRuntimeError(RuntimeError):
    """Fail-closed error with a stable, public-safe code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class RuntimeContract:
    root: Path = field(repr=False)
    root_device: int
    root_inode: int
    layers: tuple[str, ...]
    all_layers_present: bool
    all_layer_modes_0700: bool


@dataclass(frozen=True)
class CopyAuthorization:
    root_id: str
    source_scope_id: str
    operation: str
    target_layer: str
    authorization_scope: str
    copy_allowed: bool
    raw_parse_allowed: bool
    raw_value_extraction_allowed: bool
    destination_must_be_private: bool
    overwrite_existing_blob_allowed: bool
    allowed_extensions: tuple[str, ...]
    max_depth: int


@dataclass(frozen=True)
class CasInventory:
    blob_count: int
    total_bytes: int
    content_digests: tuple[str, ...] = field(repr=False)
    source_digest_set_match: bool


@dataclass(frozen=True)
class P1BaselineBinding:
    fixed_project_entry: bool
    fixed_runtime_root: Path = field(repr=False)
    policy: p1_guard.RootPolicy = field(repr=False)
    policy_sha256: str
    receipt_sha256: str
    root_device: int
    root_inode: int
    file_rows: tuple[tuple[str, str, int], ...] = field(repr=False)


@dataclass(frozen=True)
class ImportItem:
    path_token: str
    content_sha256: str = field(repr=False)
    size_bytes: int
    status: str
    os_atime_side_effect_observed: bool


@dataclass(frozen=True)
class ImportResult:
    status: str
    runtime_contract: RuntimeContract
    copy_authorization: CopyAuthorization
    p1_baseline_binding: Optional[P1BaselineBinding] = field(repr=False)
    final_drain_seconds: float
    runtime_root_device: int
    runtime_root_inode: int
    items: tuple[ImportItem, ...]
    cas_inventory: CasInventory
    source_file_count: int
    unique_blob_count: int
    created_count: int
    reused_count: int
    hash_match_all: bool
    idempotent_reuse_without_rewrite: bool
    prohibited_raw_mutation_detected: bool
    quarantine_triggered: bool
    os_atime_side_effect_observed: bool
    monitor_backend: str
    monitor_production_attested: bool


@dataclass(frozen=True)
class PhaseRunResult:
    """Bound first/second imports proving stable, zero-new-byte reuse."""

    status: str
    runtime_contract: RuntimeContract
    first_import: ImportResult
    second_import: ImportResult
    source_file_count: int
    unique_blob_count: int
    first_inventory_count: int
    second_inventory_count: int
    inventory_digest_set_stable: bool
    second_run_new_bytes: int
    hash_match_both_runs: bool
    blob_count_stable: bool
    idempotent_reuse_without_rewrite: bool
    prohibited_raw_mutation_detected: bool
    quarantine_triggered: bool
    os_atime_side_effect_observed: bool


@dataclass(frozen=True)
class CleanupCandidate:
    relative_path: str = field(repr=False)
    category: str
    size_bytes: int
    device: int = field(repr=False)
    inode: int = field(repr=False)
    mode: int = field(repr=False)
    link_count: int = field(repr=False)
    mtime_ns: int = field(repr=False)
    ctime_ns: int = field(repr=False)


@dataclass(frozen=True)
class CleanupPlan:
    runtime_root: Path = field(repr=False)
    root_device: int = field(repr=False)
    root_inode: int = field(repr=False)
    candidates: tuple[CleanupCandidate, ...]
    protected_count: int
    protected_violation_count: int
    total_candidate_bytes: int
    retention_days: Mapping[str, int]
    evaluated_at_ns: int
    plan_digest: str


@dataclass(frozen=True)
class CleanupExecutionResult:
    status: str
    deleted_count: int
    deleted_bytes: int
    confirmation_marker_consumed: bool


@dataclass(frozen=True)
class SyntheticCleanupRehearsalResult:
    status: str
    backup_verified: bool
    delete_verified: bool
    restore_verified: bool
    rehash_verified: bool
    protected_violation_count: int
    candidate_count: int


@dataclass(frozen=True)
class _SourceEntry:
    name: str = field(repr=False)
    path_token: str
    expected: os.stat_result = field(repr=False)


def _mode(value: os.stat_result) -> int:
    return stat.S_IMODE(value.st_mode)


def _absolute_runtime_root(value: Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    # Resolve existing ancestors.  The runtime itself is separately lstat'ed,
    # so a pre-existing symlink at the final component is still rejected.
    return candidate.parent.resolve(strict=True) / candidate.name


def _is_within(parent: Path, candidate: Path) -> bool:
    try:
        common = os.path.commonpath(
            (os.fspath(parent), os.fspath(candidate))
        )
    except ValueError:
        return False
    return common == os.fspath(parent)


def _validate_runtime_outside_source(
    policy: p1_guard.RootPolicy,
    runtime_root: Path,
) -> Path:
    """Reject lexical and symlink-resolved runtime aliases inside raw."""

    p1_guard._validate_root(policy)
    raw_root = policy.root_path
    lexical = Path(
        os.path.abspath(os.path.normpath(os.fspath(Path(runtime_root).expanduser())))
    )
    resolved = Path(os.path.realpath(lexical))
    if _is_within(raw_root, lexical) or _is_within(raw_root, resolved):
        raise PrivateRuntimeError(
            "RUNTIME_INSIDE_SOURCE_FORBIDDEN",
            "private runtime must not equal or resolve inside the raw root",
        )
    return _absolute_runtime_root(lexical)


def _ensure_directory(path: Path, *, mode: int = DIRECTORY_MODE) -> None:
    try:
        os.mkdir(path, mode)
    except FileExistsError:
        pass
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_CREATE_FAILED",
            "private runtime directory could not be created",
        ) from exc
    try:
        current = os.lstat(path)
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_UNAVAILABLE",
            "private runtime directory could not be inspected",
        ) from exc
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISDIR(current.st_mode):
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_TYPE_INVALID",
            "private runtime directory must be a non-symlink directory",
        )
    try:
        os.chmod(path, mode, follow_symlinks=False)
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_PERMISSION_FAILED",
            "private runtime directory permissions could not be enforced",
        ) from exc
    if _mode(os.lstat(path)) != mode:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_PERMISSION_DRIFT",
            "private runtime directory permissions are not least privilege",
        )


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_OPEN_FAILED",
            "private directory could not be securely opened",
        ) from exc
    value = os.fstat(descriptor)
    if not stat.S_ISDIR(value.st_mode):
        os.close(descriptor)
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_TYPE_DRIFT",
            "opened private object is not a directory",
        )
    return descriptor


def _assert_runtime_root_identity(
    root_path: Path,
    descriptor: int,
    expected: os.stat_result,
) -> None:
    opened = os.fstat(descriptor)
    try:
        linked = os.lstat(root_path)
    except OSError as exc:
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_PATH_IDENTITY_DRIFT",
            "runtime root pathname disappeared during import",
        ) from exc
    expected_identity = (
        int(expected.st_dev),
        int(expected.st_ino),
        stat.S_IFMT(expected.st_mode),
        stat.S_IMODE(expected.st_mode),
    )
    if (
        stat.S_ISLNK(linked.st_mode)
        or not stat.S_ISDIR(linked.st_mode)
        or (
            int(opened.st_dev),
            int(opened.st_ino),
            stat.S_IFMT(opened.st_mode),
            stat.S_IMODE(opened.st_mode),
        )
        != expected_identity
        or (
            int(linked.st_dev),
            int(linked.st_ino),
            stat.S_IFMT(linked.st_mode),
            stat.S_IMODE(linked.st_mode),
        )
        != expected_identity
    ):
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_PATH_IDENTITY_DRIFT",
            "runtime root pathname no longer identifies the held root dirfd",
        )


def _mkdir_at(parent_descriptor: int, name: str) -> int:
    if not name or name in {".", ".."} or "/" in name or "\x00" in name:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_NAME_INVALID",
            "private directory component is invalid",
        )
    try:
        os.mkdir(name, DIRECTORY_MODE, dir_fd=parent_descriptor)
    except FileExistsError:
        pass
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_CREATE_FAILED",
            "private subdirectory could not be created",
        ) from exc
    try:
        value = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_UNAVAILABLE",
            "private subdirectory could not be inspected",
        ) from exc
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_TYPE_INVALID",
            "private subdirectory must be a non-symlink directory",
        )
    try:
        os.chmod(
            name,
            DIRECTORY_MODE,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_PERMISSION_FAILED",
            "private subdirectory permissions could not be enforced",
        ) from exc
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_OPEN_FAILED",
            "private subdirectory could not be securely opened",
        ) from exc
    opened = os.fstat(descriptor)
    if not stat.S_ISDIR(opened.st_mode) or _mode(opened) != DIRECTORY_MODE:
        os.close(descriptor)
        raise PrivateRuntimeError(
            "PRIVATE_DIRECTORY_PERMISSION_DRIFT",
            "private subdirectory is not mode 0700",
        )
    return descriptor


def initialize_runtime(runtime_root: Path) -> RuntimeContract:
    """Create and verify the exact nine-layer private directory contract."""

    root = _absolute_runtime_root(runtime_root)
    _ensure_directory(root)
    root_descriptor = _open_directory(root)
    try:
        for layer in RUNTIME_LAYERS:
            descriptor = _mkdir_at(root_descriptor, layer)
            os.close(descriptor)
    finally:
        os.close(root_descriptor)
    return inspect_runtime_contract(root)


def inspect_runtime_contract(runtime_root: Path) -> RuntimeContract:
    root = _absolute_runtime_root(runtime_root)
    root_value = os.lstat(root)
    if (
        stat.S_ISLNK(root_value.st_mode)
        or not stat.S_ISDIR(root_value.st_mode)
        or _mode(root_value) != DIRECTORY_MODE
    ):
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_CONTRACT_FAILED",
            "private runtime root must be a mode 0700 non-symlink directory",
        )
    try:
        root_entries = tuple(sorted(path.name for path in root.iterdir()))
    except OSError as exc:
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_LIST_FAILED",
            "private runtime root could not be listed",
        ) from exc
    if root_entries != tuple(sorted(RUNTIME_LAYERS)):
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_CONTENT_DRIFT",
            "private runtime root must contain exactly the nine registered layers",
        )
    present: list[str] = []
    modes_ok = True
    for layer in RUNTIME_LAYERS:
        path = root / layer
        try:
            value = os.lstat(path)
        except OSError:
            continue
        if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
            raise PrivateRuntimeError(
                "RUNTIME_LAYER_TYPE_INVALID",
                "runtime layer must be a non-symlink directory",
            )
        present.append(layer)
        modes_ok = modes_ok and _mode(value) == DIRECTORY_MODE
    contract = RuntimeContract(
        root=root,
        root_device=int(root_value.st_dev),
        root_inode=int(root_value.st_ino),
        layers=tuple(present),
        all_layers_present=tuple(present) == RUNTIME_LAYERS,
        all_layer_modes_0700=modes_ok and len(present) == len(RUNTIME_LAYERS),
    )
    if not contract.all_layers_present or not contract.all_layer_modes_0700:
        raise PrivateRuntimeError(
            "RUNTIME_LAYER_CONTRACT_FAILED",
            "all nine runtime layers must exist with mode 0700",
        )
    return contract


def _validate_source_policy(policy: p1_guard.RootPolicy) -> None:
    p1_guard._validate_policy_instance(policy)
    if policy.max_depth != 0:
        raise PrivateRuntimeError(
            "SOURCE_DEPTH_NOT_AUTHORIZED",
            "S03-P2 copy accepts direct children only",
        )
    if frozenset(policy.allowed_extensions) != EXPECTED_SOURCE_EXTENSIONS:
        raise PrivateRuntimeError(
            "SOURCE_EXTENSION_POLICY_DRIFT",
            "S03-P2 copy accepts only the registered .xlsx/.zip set",
        )


def validate_copy_authorization(
    payload: Mapping[str, Any],
    policy: p1_guard.RootPolicy,
) -> CopyAuthorization:
    """Bind the P1 root policy to the fixed S03-P2 private-copy capability."""

    expected_fields = {
        "schema_version",
        "project_id",
        "target_release",
        "stage_id",
        "phase_id",
        "root_id",
        "source_scope_id",
        "operation",
        "target_layer",
        "authorization_scope",
        "copy_allowed",
        "raw_parse_allowed",
        "raw_value_extraction_allowed",
        "destination_must_be_private",
        "overwrite_existing_blob_allowed",
        "allowed_extensions",
        "max_depth",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_fields:
        raise PrivateRuntimeError(
            "COPY_AUTHORIZATION_FIELDS_DRIFT",
            "copy authorization must contain the exact S03-P2 fields",
        )
    fixed = {
        "schema_version": COPY_AUTHORIZATION_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "target_release": TARGET_RELEASE,
        "stage_id": STAGE_ID,
        "phase_id": PHASE_ID,
        "root_id": policy.root_id,
        "source_scope_id": policy.source_scope_id,
        "operation": EXPECTED_COPY_OPERATION,
        "target_layer": EXPECTED_COPY_TARGET_LAYER,
        "authorization_scope": EXPECTED_AUTHORIZATION_SCOPE,
        "copy_allowed": True,
        "raw_parse_allowed": False,
        "raw_value_extraction_allowed": False,
        "destination_must_be_private": True,
        "overwrite_existing_blob_allowed": False,
        "allowed_extensions": list(p1_guard.EXPECTED_ALLOWED_EXTENSIONS),
        "max_depth": 0,
    }
    if dict(payload) != fixed:
        raise PrivateRuntimeError(
            "COPY_AUTHORIZATION_NOT_EXACT",
            "copy authorization does not exactly bind this S03-P2 boundary",
        )
    return CopyAuthorization(
        root_id=policy.root_id,
        source_scope_id=policy.source_scope_id,
        operation=EXPECTED_COPY_OPERATION,
        target_layer=EXPECTED_COPY_TARGET_LAYER,
        authorization_scope=EXPECTED_AUTHORIZATION_SCOPE,
        copy_allowed=True,
        raw_parse_allowed=False,
        raw_value_extraction_allowed=False,
        destination_must_be_private=True,
        overwrite_existing_blob_allowed=False,
        allowed_extensions=tuple(p1_guard.EXPECTED_ALLOWED_EXTENSIONS),
        max_depth=0,
    )


def copy_authorization_payload(policy: p1_guard.RootPolicy) -> dict[str, Any]:
    """Return the fixed non-secret S03-P2 capability payload for validation."""

    return {
        "schema_version": COPY_AUTHORIZATION_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "target_release": TARGET_RELEASE,
        "stage_id": STAGE_ID,
        "phase_id": PHASE_ID,
        "root_id": policy.root_id,
        "source_scope_id": policy.source_scope_id,
        "operation": EXPECTED_COPY_OPERATION,
        "target_layer": EXPECTED_COPY_TARGET_LAYER,
        "authorization_scope": EXPECTED_AUTHORIZATION_SCOPE,
        "copy_allowed": True,
        "raw_parse_allowed": False,
        "raw_value_extraction_allowed": False,
        "destination_must_be_private": True,
        "overwrite_existing_blob_allowed": False,
        "allowed_extensions": list(p1_guard.EXPECTED_ALLOWED_EXTENSIONS),
        "max_depth": 0,
    }


def _validate_copy_authorization_instance(
    authorization: Optional[CopyAuthorization],
    policy: p1_guard.RootPolicy,
) -> CopyAuthorization:
    if not isinstance(authorization, CopyAuthorization):
        raise PrivateRuntimeError(
            "COPY_AUTHORIZATION_REQUIRED",
            "S03-P2 import requires an explicit validated copy authorization",
        )
    expected = validate_copy_authorization(copy_authorization_payload(policy), policy)
    if authorization != expected:
        raise PrivateRuntimeError(
            "COPY_AUTHORIZATION_INSTANCE_DRIFT",
            "copy authorization instance does not match the active root policy",
        )
    return authorization


def _fixed_capture_paths() -> tuple[Path, Path, Path]:
    private_dir = PROJECT_ROOT / FIXED_P1_PRIVATE_DIR_RELATIVE
    return (
        private_dir / FIXED_P1_POLICY_FILENAME,
        private_dir / FIXED_P1_RECEIPT_FILENAME,
        PROJECT_ROOT / FIXED_RUNTIME_ROOT_RELATIVE,
    )


def _initialize_fixed_runtime_contract() -> RuntimeContract:
    """Create/open KMFA/local_runtime only through held project dirfds."""

    project_root = PROJECT_ROOT
    try:
        project_linked = os.lstat(project_root)
    except OSError as exc:
        raise PrivateRuntimeError(
            "FIXED_PROJECT_ROOT_UNAVAILABLE",
            "module-derived project root is unavailable",
        ) from exc
    if (
        stat.S_ISLNK(project_linked.st_mode)
        or not stat.S_ISDIR(project_linked.st_mode)
        or project_root.resolve(strict=True) != project_root
    ):
        raise PrivateRuntimeError(
            "FIXED_PROJECT_ROOT_UNSAFE",
            "module-derived project root must be canonical and non-symlink",
        )
    project_descriptor = _open_directory(project_root)
    kmfa_descriptor: Optional[int] = None
    runtime_descriptor: Optional[int] = None
    try:
        project_opened = os.fstat(project_descriptor)
        if (
            int(project_opened.st_dev),
            int(project_opened.st_ino),
        ) != (
            int(project_linked.st_dev),
            int(project_linked.st_ino),
        ):
            raise PrivateRuntimeError(
                "FIXED_PROJECT_ROOT_IDENTITY_DRIFT",
                "module-derived project root changed during secure open",
            )
        kmfa_descriptor = _open_inventory_directory(
            project_descriptor,
            "KMFA",
            required_mode=None,
        )
        runtime_descriptor = _mkdir_at(kmfa_descriptor, "local_runtime")
        for layer in RUNTIME_LAYERS:
            layer_descriptor = _mkdir_at(runtime_descriptor, layer)
            os.close(layer_descriptor)
        if _directory_names(runtime_descriptor) != tuple(sorted(RUNTIME_LAYERS)):
            raise PrivateRuntimeError(
                "RUNTIME_ROOT_CONTENT_DRIFT",
                "fixed runtime root must contain exactly the nine layers",
            )
        runtime_value = os.fstat(runtime_descriptor)
        linked_runtime = os.stat(
            "local_runtime",
            dir_fd=kmfa_descriptor,
            follow_symlinks=False,
        )
        if (
            int(runtime_value.st_dev),
            int(runtime_value.st_ino),
        ) != (
            int(linked_runtime.st_dev),
            int(linked_runtime.st_ino),
        ):
            raise PrivateRuntimeError(
                "RUNTIME_ROOT_PATH_IDENTITY_DRIFT",
                "fixed runtime root changed during dirfd initialization",
            )
        linked_project_after = os.lstat(project_root)
        if (
            stat.S_ISLNK(linked_project_after.st_mode)
            or (
                int(linked_project_after.st_dev),
                int(linked_project_after.st_ino),
            )
            != (
                int(project_opened.st_dev),
                int(project_opened.st_ino),
            )
        ):
            raise PrivateRuntimeError(
                "FIXED_PROJECT_ROOT_IDENTITY_DRIFT",
                "module-derived project root pathname changed during initialization",
            )
        return RuntimeContract(
            root=project_root / FIXED_RUNTIME_ROOT_RELATIVE,
            root_device=int(runtime_value.st_dev),
            root_inode=int(runtime_value.st_ino),
            layers=RUNTIME_LAYERS,
            all_layers_present=True,
            all_layer_modes_0700=True,
        )
    finally:
        if runtime_descriptor is not None:
            os.close(runtime_descriptor)
        if kmfa_descriptor is not None:
            os.close(kmfa_descriptor)
        os.close(project_descriptor)


def _read_fixed_json(path: Path, *, label: str) -> tuple[Mapping[str, Any], str]:
    try:
        linked = os.lstat(path)
    except OSError as exc:
        raise PrivateRuntimeError(
            "FIXED_CAPTURE_INPUT_MISSING",
            f"fixed {label} input is unavailable",
        ) from exc
    if (
        stat.S_ISLNK(linked.st_mode)
        or not stat.S_ISREG(linked.st_mode)
        or int(linked.st_nlink) != 1
        or path.resolve(strict=True) != path
    ):
        raise PrivateRuntimeError(
            "FIXED_CAPTURE_INPUT_UNSAFE",
            f"fixed {label} input must be a single-link regular file",
        )
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if p1_guard._prohibited_fingerprint_signature(
            opened
        ) != p1_guard._prohibited_fingerprint_signature(linked):
            raise PrivateRuntimeError(
                "FIXED_CAPTURE_INPUT_IDENTITY_DRIFT",
                f"fixed {label} changed during secure open",
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, HASH_CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if p1_guard._prohibited_fingerprint_signature(
            after
        ) != p1_guard._prohibited_fingerprint_signature(opened):
            raise PrivateRuntimeError(
                "FIXED_CAPTURE_INPUT_CHANGED",
                f"fixed {label} changed while read",
            )
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateRuntimeError(
            "FIXED_CAPTURE_INPUT_INVALID_JSON",
            f"fixed {label} is not canonical UTF-8 JSON",
        ) from exc
    if not isinstance(decoded, Mapping):
        raise PrivateRuntimeError(
            "FIXED_CAPTURE_INPUT_NOT_OBJECT",
            f"fixed {label} must be a JSON object",
        )
    return decoded, hashlib.sha256(payload).hexdigest()


def load_fixed_p1_baseline() -> P1BaselineBinding:
    """Load and strictly reconstruct the one project-derived P1 baseline."""

    policy_path, receipt_path, fixed_runtime_root = _fixed_capture_paths()
    policy_payload, policy_sha256 = _read_fixed_json(
        policy_path,
        label="P1 policy",
    )
    receipt_payload, receipt_sha256 = _read_fixed_json(
        receipt_path,
        label="P1 receipt",
    )
    policy = p1_guard.validate_policy_payload(policy_payload)
    try:
        p1_public = p1_guard.public_projection_from_private_receipt(
            receipt_payload
        )
        post_status, post_snapshot = p1_guard._validate_private_snapshot(
            receipt_payload.get("snapshots", {}).get("post"),
            label="post",
            root_id=policy.root_id,
        )
    except p1_guard.GuardError as exc:
        raise PrivateRuntimeError(
            "P1_BASELINE_STRICT_VALIDATION_FAILED",
            "fixed P1 receipt failed strict reconstruction",
        ) from exc
    if (
        p1_public.get("status") != "PASS"
        or p1_public.get("root_id") != policy.root_id
        or p1_public.get("guard", {}).get("prohibited_raw_mutation_detected")
        is not False
        or post_status != "CAPTURED"
        or post_snapshot is None
    ):
        raise PrivateRuntimeError(
            "P1_BASELINE_NOT_FINAL_PASS",
            "fixed P1 receipt is not the final passing post snapshot",
        )
    root_token = p1_guard._path_token(policy.root_id, ".")
    root_rows = [
        entry
        for entry in post_snapshot.entries
        if entry.path_token == root_token and entry.kind == "directory"
    ]
    if len(root_rows) != 1:
        raise PrivateRuntimeError(
            "P1_BASELINE_ROOT_IDENTITY_MISSING",
            "fixed P1 post snapshot has no unique root identity",
        )
    file_rows = tuple(
        sorted(
            (
                entry.path_token,
                entry.content_sha256 or "",
                entry.size_bytes,
            )
            for entry in post_snapshot.entries
            if entry.kind == "file"
        )
    )
    if any(not digest for _, digest, _ in file_rows):
        raise PrivateRuntimeError(
            "P1_BASELINE_FILE_HASH_MISSING",
            "fixed P1 post snapshot file hash is missing",
        )
    return P1BaselineBinding(
        fixed_project_entry=True,
        fixed_runtime_root=fixed_runtime_root,
        policy=policy,
        policy_sha256=policy_sha256,
        receipt_sha256=receipt_sha256,
        root_device=root_rows[0].device,
        root_inode=root_rows[0].inode,
        file_rows=file_rows,
    )


def _list_source_entries(
    policy: p1_guard.RootPolicy,
    root_descriptor: int,
    root_before: os.stat_result,
) -> tuple[_SourceEntry, ...]:
    try:
        with os.scandir(root_descriptor) as iterator:
            names = sorted(entry.name for entry in iterator)
    except OSError as exc:
        raise PrivateRuntimeError(
            "SOURCE_LIST_FAILED",
            "authorized source root could not be listed",
        ) from exc
    root_after_list = os.fstat(root_descriptor)
    if p1_guard._prohibited_fingerprint_signature(
        root_after_list
    ) != p1_guard._prohibited_fingerprint_signature(root_before):
        raise PrivateRuntimeError(
            "SOURCE_ROOT_CHANGED_DURING_LIST",
            "source root changed during direct-child listing",
        )
    output: list[_SourceEntry] = []
    for name in names:
        if (
            not isinstance(name, str)
            or not name
            or name in {".", ".."}
            or "/" in name
            or "\x00" in name
        ):
            raise PrivateRuntimeError(
                "SOURCE_NAME_INVALID",
                "source root contains an invalid direct-child name",
            )
        try:
            value = os.stat(
                name,
                dir_fd=root_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise PrivateRuntimeError(
                "SOURCE_ENTRY_UNAVAILABLE",
                "source entry could not be inspected through the root dirfd",
            ) from exc
        if stat.S_ISLNK(value.st_mode):
            raise PrivateRuntimeError(
                "SOURCE_SYMLINK_FORBIDDEN",
                "source symlinks are outside the authorized boundary",
            )
        if not stat.S_ISREG(value.st_mode):
            raise PrivateRuntimeError(
                "SOURCE_NON_REGULAR_FORBIDDEN",
                "source entries must be regular files",
            )
        if int(value.st_nlink) != 1:
            raise PrivateRuntimeError(
                "SOURCE_MULTILINK_FORBIDDEN",
                "source files must have exactly one hard link",
            )
        if Path(name).suffix.lower() not in EXPECTED_SOURCE_EXTENSIONS:
            raise PrivateRuntimeError(
                "SOURCE_EXTENSION_FORBIDDEN",
                "source extension is outside the registered allowlist",
            )
        output.append(
            _SourceEntry(
                name=name,
                path_token=p1_guard._path_token(policy.root_id, name),
                expected=value,
            )
        )
    return tuple(output)


def _watch_targets(
    policy: p1_guard.RootPolicy,
    root_before: os.stat_result,
    entries: Sequence[_SourceEntry],
) -> dict[str, p1_guard.WatchTarget]:
    root_token = p1_guard._path_token(policy.root_id, ".")
    output = {
        root_token: p1_guard.WatchTarget(
            root_path=policy.root_path,
            relative_parts=(),
            device=int(root_before.st_dev),
            inode=int(root_before.st_ino),
            mode=int(root_before.st_mode),
        )
    }
    for entry in entries:
        output[entry.path_token] = p1_guard.WatchTarget(
            root_path=policy.root_path,
            relative_parts=(entry.name,),
            device=int(entry.expected.st_dev),
            inode=int(entry.expected.st_ino),
            mode=int(entry.expected.st_mode),
        )
    return output


def _new_private_temp(incoming_descriptor: int) -> tuple[str, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    for _ in range(16):
        name = ".incoming_" + secrets.token_hex(16)
        try:
            descriptor = os.open(
                name,
                flags,
                PRIVATE_FILE_MODE,
                dir_fd=incoming_descriptor,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise PrivateRuntimeError(
                "CAS_TEMP_CREATE_FAILED",
                "private CAS temporary file could not be created",
            ) from exc
        os.fchmod(descriptor, PRIVATE_FILE_MODE)
        return name, descriptor
    raise PrivateRuntimeError(
        "CAS_TEMP_NAME_EXHAUSTED",
        "private CAS temporary filename could not be allocated",
    )


def _write_all(descriptor: int, value: bytes) -> None:
    view = memoryview(value)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise PrivateRuntimeError(
                "CAS_TEMP_WRITE_FAILED",
                "private CAS temporary write made no progress",
            )
        view = view[written:]


def _hash_open_blob(descriptor: int) -> tuple[str, int]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = os.read(descriptor, HASH_CHUNK_SIZE)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def _verify_existing_blob(
    prefix_descriptor: int,
    digest: str,
    expected_size: int,
) -> bool:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(digest, flags, dir_fd=prefix_descriptor)
    except OSError:
        return False
    try:
        value = os.fstat(descriptor)
        if (
            not stat.S_ISREG(value.st_mode)
            or int(value.st_nlink) != 1
            or _mode(value) != CAS_BLOB_MODE
            or int(value.st_size) != expected_size
        ):
            return False
        observed_digest, observed_size = _hash_open_blob(descriptor)
        return observed_digest == digest and observed_size == expected_size
    finally:
        os.close(descriptor)


def _directory_names(descriptor: int) -> tuple[str, ...]:
    try:
        with os.scandir(descriptor) as iterator:
            return tuple(sorted(entry.name for entry in iterator))
    except OSError as exc:
        raise PrivateRuntimeError(
            "CAS_INVENTORY_LIST_FAILED",
            "CAS inventory directory could not be listed",
        ) from exc


def _open_inventory_directory(
    parent_descriptor: int,
    name: str,
    *,
    required_mode: Optional[int] = DIRECTORY_MODE,
) -> int:
    try:
        linked = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise PrivateRuntimeError(
            "CAS_DIRECTORY_MISSING",
            "required CAS inventory directory is missing",
        ) from exc
    if (
        stat.S_ISLNK(linked.st_mode)
        or not stat.S_ISDIR(linked.st_mode)
        or (required_mode is not None and _mode(linked) != required_mode)
    ):
        raise PrivateRuntimeError(
            "CAS_DIRECTORY_CONTRACT_INVALID",
            "directory failed the required mode or non-symlink contract",
        )
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    opened = os.fstat(descriptor)
    if p1_guard._prohibited_fingerprint_signature(
        opened
    ) != p1_guard._prohibited_fingerprint_signature(linked):
        os.close(descriptor)
        raise PrivateRuntimeError(
            "CAS_DIRECTORY_IDENTITY_DRIFT",
            "CAS inventory directory changed during secure open",
        )
    return descriptor


def inspect_cas_inventory(
    runtime_root: Path,
    *,
    expected_source_digests: Optional[Sequence[str]] = None,
) -> CasInventory:
    """Verify the complete canonical CAS structure and every blob digest."""

    contract = inspect_runtime_contract(runtime_root)
    content_descriptor = _open_directory(contract.root / "content_mirror")
    sha256_descriptor: Optional[int] = None
    incoming_descriptor: Optional[int] = None
    prefix_descriptors: list[int] = []
    digests: list[str] = []
    total_bytes = 0
    try:
        if _directory_names(content_descriptor) != (".incoming", "sha256"):
            raise PrivateRuntimeError(
                "CAS_ROOT_STRUCTURE_INVALID",
                "content_mirror must contain only .incoming and sha256",
            )
        incoming_descriptor = _open_inventory_directory(
            content_descriptor,
            ".incoming",
        )
        if _directory_names(incoming_descriptor):
            raise PrivateRuntimeError(
                "CAS_INCOMING_NOT_EMPTY",
                "CAS incoming directory must be empty at inventory gate",
            )
        sha256_descriptor = _open_inventory_directory(
            content_descriptor,
            HASH_ALGORITHM,
        )
        prefix_names = _directory_names(sha256_descriptor)
        for prefix in prefix_names:
            if len(prefix) != 2 or any(
                character not in "0123456789abcdef" for character in prefix
            ):
                raise PrivateRuntimeError(
                    "CAS_PREFIX_NAME_INVALID",
                    "CAS prefix directory must be two lowercase hex characters",
                )
            prefix_value = os.stat(
                prefix,
                dir_fd=sha256_descriptor,
                follow_symlinks=False,
            )
            if (
                stat.S_ISLNK(prefix_value.st_mode)
                or not stat.S_ISDIR(prefix_value.st_mode)
                or _mode(prefix_value) != DIRECTORY_MODE
            ):
                raise PrivateRuntimeError(
                    "CAS_PREFIX_CONTRACT_INVALID",
                    "CAS prefix must be a mode 0700 non-symlink directory",
                )
            prefix_descriptor = _open_inventory_directory(
                sha256_descriptor,
                prefix,
            )
            prefix_descriptors.append(prefix_descriptor)
            for digest in _directory_names(prefix_descriptor):
                if (
                    len(digest) != 64
                    or digest[:2] != prefix
                    or any(
                        character not in "0123456789abcdef"
                        for character in digest
                    )
                ):
                    raise PrivateRuntimeError(
                        "CAS_BLOB_NAME_INVALID",
                        "CAS blob name must be its lowercase SHA-256 under its prefix",
                    )
                linked = os.stat(
                    digest,
                    dir_fd=prefix_descriptor,
                    follow_symlinks=False,
                )
                if stat.S_ISLNK(linked.st_mode) or not stat.S_ISREG(
                    linked.st_mode
                ):
                    raise PrivateRuntimeError(
                        "CAS_BLOB_TYPE_INVALID",
                        "CAS blob must be a non-symlink regular file",
                    )
                if int(linked.st_nlink) != 1:
                    raise PrivateRuntimeError(
                        "CAS_BLOB_LINK_COUNT_INVALID",
                        "CAS blob must have exactly one hard link",
                    )
                if _mode(linked) != CAS_BLOB_MODE:
                    raise PrivateRuntimeError(
                        "CAS_BLOB_MODE_INVALID",
                        "CAS blob must remain mode 0400",
                    )
                flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                flags |= getattr(os, "O_NOFOLLOW", 0)
                blob_descriptor = os.open(
                    digest,
                    flags,
                    dir_fd=prefix_descriptor,
                )
                try:
                    opened = os.fstat(blob_descriptor)
                    if p1_guard._prohibited_fingerprint_signature(
                        opened
                    ) != p1_guard._prohibited_fingerprint_signature(linked):
                        raise PrivateRuntimeError(
                            "CAS_BLOB_IDENTITY_DRIFT",
                            "CAS blob identity changed during inventory",
                        )
                    observed_digest, observed_size = _hash_open_blob(
                        blob_descriptor
                    )
                    after = os.fstat(blob_descriptor)
                    if p1_guard._prohibited_fingerprint_signature(
                        after
                    ) != p1_guard._prohibited_fingerprint_signature(opened):
                        raise PrivateRuntimeError(
                            "CAS_BLOB_CHANGED_DURING_HASH",
                            "CAS blob changed during inventory hash",
                        )
                finally:
                    os.close(blob_descriptor)
                if observed_digest != digest:
                    raise PrivateRuntimeError(
                        "CAS_BLOB_HASH_MISMATCH",
                        "CAS blob content does not match its address",
                    )
                if digest in digests:
                    raise PrivateRuntimeError(
                        "CAS_BLOB_DUPLICATE",
                        "CAS inventory contains a duplicate content address",
                    )
                digests.append(digest)
                total_bytes += observed_size
    finally:
        for descriptor in prefix_descriptors:
            os.close(descriptor)
        if sha256_descriptor is not None:
            os.close(sha256_descriptor)
        if incoming_descriptor is not None:
            os.close(incoming_descriptor)
        os.close(content_descriptor)

    ordered = tuple(sorted(digests))
    expected = None
    if expected_source_digests is not None:
        expected = tuple(sorted(set(expected_source_digests)))
        if ordered != expected:
            raise PrivateRuntimeError(
                "CAS_INVENTORY_SOURCE_SET_MISMATCH",
                "CAS inventory does not exactly equal the current source digest set",
            )
    return CasInventory(
        blob_count=len(ordered),
        total_bytes=total_bytes,
        content_digests=ordered,
        source_digest_set_match=(expected is None or ordered == expected),
    )


def _quarantine_existing_blob(
    prefix_descriptor: int,
    quarantine_descriptor: int,
    digest: str,
    *,
    reason: str,
) -> None:
    quarantine_name = (
        f"cas_{reason}_{digest}_{secrets.token_hex(8)}.blob"
    )
    try:
        os.rename(
            digest,
            quarantine_name,
            src_dir_fd=prefix_descriptor,
            dst_dir_fd=quarantine_descriptor,
        )
        os.fsync(prefix_descriptor)
        os.fsync(quarantine_descriptor)
    except OSError as exc:
        raise PrivateRuntimeError(
            "CAS_QUARANTINE_FAILED",
            "invalid private CAS object could not be quarantined",
        ) from exc


def _promote_or_reuse(
    *,
    incoming_descriptor: int,
    temp_name: str,
    prefix_descriptor: int,
    quarantine_descriptor: int,
    digest: str,
    size_bytes: int,
) -> str:
    try:
        os.link(
            temp_name,
            digest,
            src_dir_fd=incoming_descriptor,
            dst_dir_fd=prefix_descriptor,
            follow_symlinks=False,
        )
    except FileExistsError:
        if not _verify_existing_blob(prefix_descriptor, digest, size_bytes):
            _quarantine_existing_blob(
                prefix_descriptor,
                quarantine_descriptor,
                digest,
                reason="mismatch",
            )
            raise PrivateRuntimeError(
                "CAS_MISMATCH_QUARANTINED",
                "existing CAS object failed digest, mode, type, or link validation",
            )
        os.unlink(temp_name, dir_fd=incoming_descriptor)
        os.fsync(incoming_descriptor)
        return "REUSED"
    except OSError as exc:
        raise PrivateRuntimeError(
            "CAS_ATOMIC_PROMOTION_FAILED",
            "private CAS object could not be atomically promoted",
        ) from exc
    os.unlink(temp_name, dir_fd=incoming_descriptor)
    os.fsync(incoming_descriptor)
    os.fsync(prefix_descriptor)
    if not _verify_existing_blob(prefix_descriptor, digest, size_bytes):
        _quarantine_existing_blob(
            prefix_descriptor,
            quarantine_descriptor,
            digest,
            reason="post_promotion",
        )
        raise PrivateRuntimeError(
            "CAS_POST_PROMOTION_VERIFY_FAILED",
            "new CAS object failed post-promotion verification",
        )
    return "CREATED"


def _copy_one_source(
    *,
    root_descriptor: int,
    entry: _SourceEntry,
    incoming_descriptor: int,
    sha256_descriptor: int,
    quarantine_descriptor: int,
) -> ImportItem:
    try:
        linked_before = os.stat(
            entry.name,
            dir_fd=root_descriptor,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise PrivateRuntimeError(
            "SOURCE_PATH_DRIFT",
            "source path changed before copy",
        ) from exc
    if p1_guard._prohibited_fingerprint_signature(
        linked_before
    ) != p1_guard._prohibited_fingerprint_signature(entry.expected):
        raise PrivateRuntimeError(
            "SOURCE_FINGERPRINT_DRIFT",
            "source fingerprint changed before copy",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        source_descriptor = os.open(
            entry.name,
            flags,
            dir_fd=root_descriptor,
        )
    except OSError as exc:
        raise PrivateRuntimeError(
            "SOURCE_OPEN_FAILED",
            "source file could not be securely opened through the root dirfd",
        ) from exc
    temp_name: Optional[str] = None
    temp_descriptor: Optional[int] = None
    try:
        source_before = os.fstat(source_descriptor)
        if (
            not stat.S_ISREG(source_before.st_mode)
            or int(source_before.st_nlink) != 1
            or p1_guard._prohibited_fingerprint_signature(source_before)
            != p1_guard._prohibited_fingerprint_signature(entry.expected)
        ):
            raise PrivateRuntimeError(
                "SOURCE_OPEN_IDENTITY_DRIFT",
                "opened source identity differs from the listed source",
            )
        temp_name, temp_descriptor = _new_private_temp(incoming_descriptor)
        digest = hashlib.sha256()
        bytes_copied = 0
        while True:
            chunk = os.read(source_descriptor, HASH_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
            _write_all(temp_descriptor, chunk)
            bytes_copied += len(chunk)
        os.fsync(temp_descriptor)
        source_after = os.fstat(source_descriptor)
        if p1_guard._prohibited_fingerprint_signature(
            source_after
        ) != p1_guard._prohibited_fingerprint_signature(source_before):
            raise PrivateRuntimeError(
                "SOURCE_CHANGED_DURING_COPY",
                "source content or protected metadata changed during copy",
            )
        if bytes_copied != int(source_before.st_size):
            raise PrivateRuntimeError(
                "SOURCE_BYTE_COUNT_MISMATCH",
                "copied bytes differ from the stable source size",
            )
        linked_after = os.stat(
            entry.name,
            dir_fd=root_descriptor,
            follow_symlinks=False,
        )
        if p1_guard._prohibited_fingerprint_signature(
            linked_after
        ) != p1_guard._prohibited_fingerprint_signature(source_after):
            raise PrivateRuntimeError(
                "SOURCE_PATH_DRIFT",
                "source path identity changed during copy",
            )
        content_digest = digest.hexdigest()
        temp_value = os.fstat(temp_descriptor)
        if (
            not stat.S_ISREG(temp_value.st_mode)
            or int(temp_value.st_nlink) != 1
            or _mode(temp_value) != PRIVATE_FILE_MODE
            or int(temp_value.st_size) != bytes_copied
        ):
            raise PrivateRuntimeError(
                "CAS_TEMP_CONTRACT_FAILED",
                "private CAS temporary file failed type, link, mode, or size checks",
            )
        os.fchmod(temp_descriptor, CAS_BLOB_MODE)
        os.close(temp_descriptor)
        temp_descriptor = None
        prefix_descriptor = _mkdir_at(sha256_descriptor, content_digest[:2])
        try:
            result_status = _promote_or_reuse(
                incoming_descriptor=incoming_descriptor,
                temp_name=temp_name,
                prefix_descriptor=prefix_descriptor,
                quarantine_descriptor=quarantine_descriptor,
                digest=content_digest,
                size_bytes=bytes_copied,
            )
            temp_name = None
        finally:
            os.close(prefix_descriptor)
        return ImportItem(
            path_token=entry.path_token,
            content_sha256=content_digest,
            size_bytes=bytes_copied,
            status=result_status,
            os_atime_side_effect_observed=(
                int(source_before.st_atime_ns) != int(source_after.st_atime_ns)
            ),
        )
    finally:
        os.close(source_descriptor)
        if temp_descriptor is not None:
            os.close(temp_descriptor)
        if temp_name is not None:
            try:
                os.unlink(temp_name, dir_fd=incoming_descriptor)
            except OSError:
                pass


def import_authorized_root(
    policy: p1_guard.RootPolicy,
    runtime_root: Path,
    *,
    copy_authorization: Optional[CopyAuthorization] = None,
    p1_baseline_binding: Optional[P1BaselineBinding] = None,
    monitor_backend: Optional[p1_guard.MonitorBackend] = None,
    final_drain_seconds: float = p1_guard.FINAL_DRAIN_SECONDS,
    _preinitialized_runtime_contract: Optional[RuntimeContract] = None,
) -> ImportResult:
    """Copy one authorized root into the private CAS without parsing values."""

    _validate_source_policy(policy)
    validated_copy_authorization = _validate_copy_authorization_instance(
        copy_authorization,
        policy,
    )
    if (
        p1_baseline_binding is not None
        and p1_baseline_binding.policy != policy
    ):
        raise PrivateRuntimeError(
            "P1_BASELINE_POLICY_DRIFT",
            "active source policy differs from the fixed P1 baseline",
        )
    if final_drain_seconds < 0 or final_drain_seconds > 60:
        raise PrivateRuntimeError(
            "MONITOR_TIMEOUT_INVALID",
            "final monitor drain must be between 0 and 60 seconds",
        )
    safe_runtime_root = _validate_runtime_outside_source(policy, runtime_root)
    if _preinitialized_runtime_contract is None:
        contract = initialize_runtime(safe_runtime_root)
    else:
        contract = _preinitialized_runtime_contract
        if contract.root != safe_runtime_root:
            raise PrivateRuntimeError(
                "PREINITIALIZED_RUNTIME_ROOT_MISMATCH",
                "preinitialized runtime contract does not bind the requested root",
            )
    runtime_root_descriptor = _open_directory(contract.root)
    runtime_root_before = os.fstat(runtime_root_descriptor)
    if (
        int(runtime_root_before.st_dev),
        int(runtime_root_before.st_ino),
    ) != (contract.root_device, contract.root_inode):
        os.close(runtime_root_descriptor)
        raise PrivateRuntimeError(
            "RUNTIME_ROOT_PATH_IDENTITY_DRIFT",
            "opened runtime root differs from its preinitialized contract",
        )
    root_descriptor, root_before = p1_guard._open_verified_root(policy)
    if p1_baseline_binding is not None:
        if (int(root_before.st_dev), int(root_before.st_ino)) != (
            p1_baseline_binding.root_device,
            p1_baseline_binding.root_inode,
        ):
            os.close(root_descriptor)
            os.close(runtime_root_descriptor)
            raise PrivateRuntimeError(
                "P1_BASELINE_ROOT_IDENTITY_DRIFT",
                "active raw root identity differs from the P1 final snapshot",
            )
    root_atime_before_ns = int(root_before.st_atime_ns)
    root_atime_after_ns = root_atime_before_ns
    try:
        monitor = monitor_backend or p1_guard.DarwinKqueueVnodeMonitor()
    except Exception:
        os.close(root_descriptor)
        os.close(runtime_root_descriptor)
        raise
    monitor_name = getattr(monitor, "name", "")
    if not isinstance(monitor_name, str) or not monitor_name:
        os.close(root_descriptor)
        os.close(runtime_root_descriptor)
        raise PrivateRuntimeError(
            "MONITOR_NAME_INVALID",
            "monitor backend must declare a stable name",
        )
    entries: tuple[_SourceEntry, ...] = ()
    monitor_started = False
    content_descriptor: Optional[int] = None
    incoming_descriptor: Optional[int] = None
    sha256_descriptor: Optional[int] = None
    quarantine_descriptor: Optional[int] = None
    items: list[ImportItem] = []
    events: list[p1_guard.MonitorEvent] = []
    quarantine_triggered = False
    inventory: Optional[CasInventory] = None
    try:
        _assert_runtime_root_identity(
            contract.root,
            runtime_root_descriptor,
            runtime_root_before,
        )
        entries = _list_source_entries(policy, root_descriptor, root_before)
        targets = _watch_targets(policy, root_before, entries)
        monitor.start(targets)
        monitor_started = True
        initial = p1_guard._validate_monitor_events(monitor.poll(0.0), targets)
        events.extend(initial)
        if initial:
            raise PrivateRuntimeError(
                "SOURCE_MONITOR_EVENT_BEFORE_COPY",
                "source vnode event occurred before copy",
            )
        content_descriptor = _open_inventory_directory(
            runtime_root_descriptor,
            "content_mirror",
        )
        incoming_descriptor = _mkdir_at(content_descriptor, ".incoming")
        sha256_descriptor = _mkdir_at(content_descriptor, HASH_ALGORITHM)
        quarantine_descriptor = _open_inventory_directory(
            runtime_root_descriptor,
            "quarantine",
        )
        for entry in entries:
            try:
                item = _copy_one_source(
                    root_descriptor=root_descriptor,
                    entry=entry,
                    incoming_descriptor=incoming_descriptor,
                    sha256_descriptor=sha256_descriptor,
                    quarantine_descriptor=quarantine_descriptor,
                )
            except PrivateRuntimeError as exc:
                quarantine_triggered = quarantine_triggered or (
                    "QUARANTIN" in exc.code
                )
                raise
            items.append(item)
            current = p1_guard._validate_monitor_events(
                monitor.poll(0.0),
                targets,
            )
            events.extend(current)
            if current:
                raise PrivateRuntimeError(
                    "SOURCE_MONITOR_EVENT_DURING_COPY",
                    "source vnode event occurred during copy",
                )
        os.fsync(incoming_descriptor)
        os.fsync(sha256_descriptor)
        os.fsync(content_descriptor)
        for entry in entries:
            try:
                final_source = os.stat(
                    entry.name,
                    dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise PrivateRuntimeError(
                    "SOURCE_FINAL_FINGERPRINT_UNAVAILABLE",
                    "source entry disappeared before final attestation",
                ) from exc
            if p1_guard._prohibited_fingerprint_signature(
                final_source
            ) != p1_guard._prohibited_fingerprint_signature(entry.expected):
                raise PrivateRuntimeError(
                    "SOURCE_FINAL_FINGERPRINT_DRIFT",
                    "source entry changed before final attestation",
                )
        root_after = os.fstat(root_descriptor)
        root_atime_after_ns = int(root_after.st_atime_ns)
        try:
            linked_root = os.lstat(policy.root_path)
        except OSError as exc:
            raise PrivateRuntimeError(
                "SOURCE_ROOT_PATH_DRIFT",
                "source root path disappeared during copy",
            ) from exc
        expected_signature = p1_guard._prohibited_fingerprint_signature(root_before)
        if (
            p1_guard._prohibited_fingerprint_signature(root_after)
            != expected_signature
            or stat.S_ISLNK(linked_root.st_mode)
            or p1_guard._prohibited_fingerprint_signature(linked_root)
            != expected_signature
        ):
            raise PrivateRuntimeError(
                "SOURCE_ROOT_FINGERPRINT_DRIFT",
                "source root changed during copy",
            )
        final_events = p1_guard._validate_monitor_events(
            monitor.poll(final_drain_seconds),
            targets,
        )
        events.extend(final_events)
        if final_events:
            raise PrivateRuntimeError(
                "SOURCE_MONITOR_EVENT_AFTER_COPY",
                "source vnode event occurred before final attestation",
            )
        observed_rows = tuple(
            sorted(
                (item.path_token, item.content_sha256, item.size_bytes)
                for item in items
            )
        )
        if (
            p1_baseline_binding is not None
            and observed_rows != p1_baseline_binding.file_rows
        ):
            raise PrivateRuntimeError(
                "P1_BASELINE_FILE_MANIFEST_DRIFT",
                "P2 copied token, digest, or size differs from P1 final snapshot",
            )
        _assert_runtime_root_identity(
            contract.root,
            runtime_root_descriptor,
            runtime_root_before,
        )
        inventory = inspect_cas_inventory(
            contract.root,
            expected_source_digests=[item.content_sha256 for item in items],
        )
        _assert_runtime_root_identity(
            contract.root,
            runtime_root_descriptor,
            runtime_root_before,
        )
    finally:
        for descriptor in (
            quarantine_descriptor,
            sha256_descriptor,
            incoming_descriptor,
            content_descriptor,
        ):
            if descriptor is not None:
                os.close(descriptor)
        if monitor_started:
            monitor.close()
        os.close(root_descriptor)
        try:
            _assert_runtime_root_identity(
                contract.root,
                runtime_root_descriptor,
                runtime_root_before,
            )
        finally:
            os.close(runtime_root_descriptor)

    if inventory is None:
        raise PrivateRuntimeError(
            "CAS_INVENTORY_NOT_ATTESTED",
            "CAS inventory was not completed under the held runtime root",
        )
    unique_blob_count = inventory.blob_count
    created_count = sum(item.status == "CREATED" for item in items)
    reused_count = sum(item.status == "REUSED" for item in items)
    return ImportResult(
        status="PASS",
        runtime_contract=contract,
        copy_authorization=validated_copy_authorization,
        p1_baseline_binding=p1_baseline_binding,
        final_drain_seconds=float(final_drain_seconds),
        runtime_root_device=int(runtime_root_before.st_dev),
        runtime_root_inode=int(runtime_root_before.st_ino),
        items=tuple(items),
        cas_inventory=inventory,
        source_file_count=len(items),
        unique_blob_count=unique_blob_count,
        created_count=created_count,
        reused_count=reused_count,
        hash_match_all=True,
        idempotent_reuse_without_rewrite=(created_count == 0),
        prohibited_raw_mutation_detected=bool(events),
        quarantine_triggered=quarantine_triggered,
        os_atime_side_effect_observed=any(
            item.os_atime_side_effect_observed for item in items
        )
        or root_atime_before_ns != root_atime_after_ns,
        monitor_backend=monitor_name,
        monitor_production_attested=(
            monitor.__class__ is p1_guard.DarwinKqueueVnodeMonitor
        ),
    )


def combine_idempotency_runs(
    first_import: ImportResult,
    second_import: ImportResult,
) -> PhaseRunResult:
    """Bind two imports and fail unless the second is a pure verified reuse."""

    if first_import.status != "PASS" or second_import.status != "PASS":
        raise PrivateRuntimeError(
            "IMPORT_RUN_STATUS_INVALID",
            "both content-addressed import runs must pass",
        )
    first_baseline = first_import.p1_baseline_binding
    second_baseline = second_import.p1_baseline_binding
    if (
        first_baseline is None
        or second_baseline is None
        or not first_baseline.fixed_project_entry
        or first_baseline != second_baseline
        or first_import.runtime_contract.root
        != first_baseline.fixed_runtime_root
        or second_import.runtime_contract.root
        != first_baseline.fixed_runtime_root
    ):
        raise PrivateRuntimeError(
            "FINAL_CAPTURE_BINDING_REQUIRED",
            "final PhaseRunResult requires the one fixed project P1 baseline/runtime",
        )
    if (
        first_import.final_drain_seconds != p1_guard.FINAL_DRAIN_SECONDS
        or second_import.final_drain_seconds != p1_guard.FINAL_DRAIN_SECONDS
    ):
        raise PrivateRuntimeError(
            "FINAL_CAPTURE_DRAIN_INVALID",
            "both fixed capture runs require the P1 final drain duration",
        )
    if not (
        first_import.monitor_production_attested
        and second_import.monitor_production_attested
        and first_import.monitor_backend
        == p1_guard.DarwinKqueueVnodeMonitor.name
        and second_import.monitor_backend
        == p1_guard.DarwinKqueueVnodeMonitor.name
    ):
        raise PrivateRuntimeError(
            "IMPORT_MONITOR_PRODUCTION_ATTESTATION_REQUIRED",
            "final two-run evidence requires the production monitor in both runs",
        )
    if first_import.runtime_contract != second_import.runtime_contract:
        raise PrivateRuntimeError(
            "IMPORT_RUNTIME_CONTRACT_DRIFT",
            "runtime directory contract changed between imports",
        )
    if (
        first_import.runtime_root_device,
        first_import.runtime_root_inode,
    ) != (
        second_import.runtime_root_device,
        second_import.runtime_root_inode,
    ):
        raise PrivateRuntimeError(
            "IMPORT_RUNTIME_ROOT_IDENTITY_DRIFT",
            "runtime root device or inode changed between imports",
        )
    if first_import.copy_authorization != second_import.copy_authorization:
        raise PrivateRuntimeError(
            "IMPORT_COPY_AUTHORIZATION_DRIFT",
            "S03-P2 copy authorization changed between imports",
        )
    first_rows = tuple(
        (item.path_token, item.content_sha256, item.size_bytes)
        for item in first_import.items
    )
    second_rows = tuple(
        (item.path_token, item.content_sha256, item.size_bytes)
        for item in second_import.items
    )
    if first_rows != second_rows:
        raise PrivateRuntimeError(
            "IMPORT_MANIFEST_DRIFT",
            "source token, digest, or byte manifest changed between imports",
        )
    expected_digests = tuple(sorted({row[1] for row in first_rows}))
    try:
        current_runtime = os.lstat(second_import.runtime_contract.root)
    except OSError as exc:
        raise PrivateRuntimeError(
            "IMPORT_RUNTIME_ROOT_IDENTITY_DRIFT",
            "runtime root is unavailable at final inventory gate",
        ) from exc
    if (
        stat.S_ISLNK(current_runtime.st_mode)
        or not stat.S_ISDIR(current_runtime.st_mode)
        or (
            int(current_runtime.st_dev),
            int(current_runtime.st_ino),
        )
        != (
            second_import.runtime_root_device,
            second_import.runtime_root_inode,
        )
    ):
        raise PrivateRuntimeError(
            "IMPORT_RUNTIME_ROOT_IDENTITY_DRIFT",
            "runtime pathname differs from the bound import root",
        )
    current_inventory = inspect_cas_inventory(
        second_import.runtime_contract.root,
        expected_source_digests=expected_digests,
    )
    current_runtime_after = os.lstat(second_import.runtime_contract.root)
    if (
        stat.S_ISLNK(current_runtime_after.st_mode)
        or (
            int(current_runtime_after.st_dev),
            int(current_runtime_after.st_ino),
        )
        != (
            second_import.runtime_root_device,
            second_import.runtime_root_inode,
        )
    ):
        raise PrivateRuntimeError(
            "IMPORT_RUNTIME_ROOT_IDENTITY_DRIFT",
            "runtime pathname changed during final inventory gate",
        )
    inventory_stable = (
        first_import.cas_inventory.source_digest_set_match
        and second_import.cas_inventory.source_digest_set_match
        and first_import.cas_inventory.content_digests == expected_digests
        and second_import.cas_inventory.content_digests == expected_digests
        and current_inventory.content_digests == expected_digests
        and first_import.cas_inventory.blob_count
        == second_import.cas_inventory.blob_count
        == current_inventory.blob_count
    )
    if not inventory_stable:
        raise PrivateRuntimeError(
            "IMPORT_CAS_INVENTORY_DRIFT",
            "verified CAS inventory is not stable across both import runs",
        )
    if (
        first_import.source_file_count != second_import.source_file_count
        or first_import.unique_blob_count != second_import.unique_blob_count
    ):
        raise PrivateRuntimeError(
            "IMPORT_COUNT_DRIFT",
            "source or unique blob count changed between imports",
        )
    second_new_bytes = sum(
        item.size_bytes for item in second_import.items if item.status == "CREATED"
    )
    if (
        second_import.created_count != 0
        or second_new_bytes != 0
        or second_import.reused_count != second_import.source_file_count
        or not second_import.idempotent_reuse_without_rewrite
    ):
        raise PrivateRuntimeError(
            "IMPORT_IDEMPOTENCY_FAILED",
            "second import must reuse every source with zero new bytes",
        )
    prohibited = (
        first_import.prohibited_raw_mutation_detected
        or second_import.prohibited_raw_mutation_detected
    )
    quarantine = (
        first_import.quarantine_triggered or second_import.quarantine_triggered
    )
    if prohibited or quarantine:
        raise PrivateRuntimeError(
            "IMPORT_SAFETY_ATTESTATION_FAILED",
            "both imports must be free of raw mutation and quarantine events",
        )
    return PhaseRunResult(
        status="PASS",
        runtime_contract=first_import.runtime_contract,
        first_import=first_import,
        second_import=second_import,
        source_file_count=first_import.source_file_count,
        unique_blob_count=first_import.unique_blob_count,
        first_inventory_count=first_import.cas_inventory.blob_count,
        second_inventory_count=second_import.cas_inventory.blob_count,
        inventory_digest_set_stable=inventory_stable,
        second_run_new_bytes=second_new_bytes,
        hash_match_both_runs=(
            first_import.hash_match_all and second_import.hash_match_all
        ),
        blob_count_stable=(
            first_import.cas_inventory.blob_count
            == second_import.cas_inventory.blob_count
        ),
        idempotent_reuse_without_rewrite=True,
        prohibited_raw_mutation_detected=False,
        quarantine_triggered=False,
        os_atime_side_effect_observed=(
            first_import.os_atime_side_effect_observed
            or second_import.os_atime_side_effect_observed
        ),
    )


def run_fixed_project_capture() -> PhaseRunResult:
    """Run the only final-eligible P2 capture from fixed project paths."""

    baseline = load_fixed_p1_baseline()
    authorization = validate_copy_authorization(
        copy_authorization_payload(baseline.policy),
        baseline.policy,
    )
    _, _, runtime_root = _fixed_capture_paths()
    runtime_contract = _initialize_fixed_runtime_contract()
    first = import_authorized_root(
        baseline.policy,
        runtime_root,
        copy_authorization=authorization,
        p1_baseline_binding=baseline,
        final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
        _preinitialized_runtime_contract=runtime_contract,
    )
    second = import_authorized_root(
        baseline.policy,
        runtime_root,
        copy_authorization=authorization,
        p1_baseline_binding=baseline,
        final_drain_seconds=p1_guard.FINAL_DRAIN_SECONDS,
        _preinitialized_runtime_contract=runtime_contract,
    )
    return combine_idempotency_runs(first, second)


def _private_item_value(item: ImportItem) -> dict[str, Any]:
    return {
        "path_token": item.path_token,
        "content_sha256": "sha256:" + item.content_sha256,
        "size_bytes": item.size_bytes,
        "status": item.status,
        "os_atime_side_effect_observed": item.os_atime_side_effect_observed,
    }


def _cleanup_public_value(
    plan: CleanupPlan,
    rehearsal: SyntheticCleanupRehearsalResult,
) -> dict[str, Any]:
    return {
        "mode": "DRY_RUN",
        "canonical_retention_basis": "UNTIL_CONDITION",
        "canonical_auto_delete_enabled": False,
        "condition_based_retention": True,
        "candidate_count": len(plan.candidates),
        "protected_count": plan.protected_count,
        "protected_violation_count": plan.protected_violation_count,
        "synthetic_rehearsal_pass": rehearsal.status == "PASS",
        "synthetic_backup_verified": rehearsal.backup_verified,
        "synthetic_delete_verified": rehearsal.delete_verified,
        "synthetic_restore_verified": rehearsal.restore_verified,
        "synthetic_rehash_verified": rehearsal.rehash_verified,
        "plan_deterministic": True,
        "destructive_execution_performed": False,
        "second_confirmation_required": True,
        "exact_plan_digest_required": True,
        "one_use_marker_required": True,
        "real_runtime_deletion_allowed": False,
    }


def _validate_final_cleanup_evidence(
    result: PhaseRunResult,
    plan: CleanupPlan,
    rehearsal: SyntheticCleanupRehearsalResult,
) -> None:
    if not isinstance(plan, CleanupPlan):
        raise PrivateRuntimeError(
            "FINAL_CLEANUP_PLAN_REQUIRED",
            "final evidence requires a canonical cleanup plan",
        )
    if plan.runtime_root != result.runtime_contract.root:
        raise PrivateRuntimeError(
            "FINAL_CLEANUP_ROOT_MISMATCH",
            "canonical cleanup plan must bind the phase runtime root",
        )
    _verify_plan_digest(plan)
    _verify_plan_matches_current_runtime(plan)
    if (
        dict(plan.retention_days)
        or plan.candidates
        or plan.protected_violation_count != 0
    ):
        raise PrivateRuntimeError(
            "FINAL_CLEANUP_PLAN_NOT_CONDITION_BASED",
            "final cleanup plan must be no-auto-delete with zero candidates",
        )
    if not isinstance(rehearsal, SyntheticCleanupRehearsalResult) or not (
        rehearsal.status == "PASS"
        and rehearsal.backup_verified
        and rehearsal.delete_verified
        and rehearsal.restore_verified
        and rehearsal.rehash_verified
        and rehearsal.protected_violation_count == 0
        and rehearsal.candidate_count > 0
    ):
        raise PrivateRuntimeError(
            "FINAL_SYNTHETIC_REHEARSAL_INVALID",
            "final evidence requires a complete synthetic lifecycle rehearsal",
        )


def _bound_import_runs(
    result: PhaseRunResult,
) -> tuple[ImportResult, ImportResult]:
    if not isinstance(result, PhaseRunResult):
        raise PrivateRuntimeError(
            "FINAL_EVIDENCE_REQUIRES_TWO_IMPORT_RUNS",
            "final evidence must bind a validated PhaseRunResult",
        )
    validated = combine_idempotency_runs(
        result.first_import,
        result.second_import,
    )
    if result != validated:
        raise PrivateRuntimeError(
            "FINAL_PHASE_RESULT_INVALID",
            "final phase result differs from recomputed two-run evidence",
        )
    return (result.first_import, result.second_import)


def build_public_projection(
    result: PhaseRunResult,
    *,
    cleanup_plan: CleanupPlan,
    synthetic_rehearsal_result: SyntheticCleanupRehearsalResult,
    gitignore_attested: bool = False,
) -> dict[str, Any]:
    """Return aggregate evidence with no paths, names, tokens, or hashes."""

    first_run, second_run = _bound_import_runs(result)
    runs = (first_run, second_run)
    _validate_final_cleanup_evidence(
        result,
        cleanup_plan,
        synthetic_rehearsal_result,
    )
    value = {
        "schema_version": PUBLIC_PROJECTION_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "target_release": TARGET_RELEASE,
        "stage_id": STAGE_ID,
        "phase_id": PHASE_ID,
        "status": result.status,
        "directory_contract": {
            "layer_count": len(result.runtime_contract.layers),
            "all_layers_present": result.runtime_contract.all_layers_present,
            "all_layer_modes_0700": (
                result.runtime_contract.all_layer_modes_0700
            ),
            "private_files_mode_0600": True,
            "cas_blob_mode_0400": True,
            "gitignore_attested": gitignore_attested,
        },
        "copy_authorization": {
            "authorization_scope": (
                first_run.copy_authorization.authorization_scope
            ),
            "copy_allowed": first_run.copy_authorization.copy_allowed,
            "raw_parse_allowed": (
                first_run.copy_authorization.raw_parse_allowed
            ),
            "raw_value_extraction_allowed": (
                first_run.copy_authorization.raw_value_extraction_allowed
            ),
            "destination_must_be_private": (
                first_run.copy_authorization.destination_must_be_private
            ),
            "overwrite_existing_blob_allowed": (
                first_run.copy_authorization.overwrite_existing_blob_allowed
            ),
        },
        "p1_baseline_binding": {
            "fixed_project_entry": True,
            "policy_bound": True,
            "p1_receipt_strictly_reconstructed": True,
            "p1_final_snapshot_exact_match_both_runs": True,
            "raw_root_identity_match_both_runs": True,
            "final_drain_seconds": p1_guard.FINAL_DRAIN_SECONDS,
        },
        "runtime_root_binding": {
            "fixed_project_runtime": True,
            "held_dirfd_both_runs": True,
            "device_inode_stable": True,
            "pathname_identity_stable": True,
        },
        "content_addressed_copy": {
            "run_count": 2,
            "source_file_count": result.source_file_count,
            "unique_blob_count": result.unique_blob_count,
            "first_inventory_count": result.first_inventory_count,
            "second_inventory_count": result.second_inventory_count,
            "inventory_digest_set_stable": (
                result.inventory_digest_set_stable
            ),
            "first_run_created_count": first_run.created_count,
            "first_run_reused_count": first_run.reused_count,
            "second_run_created_count": second_run.created_count,
            "second_run_reused_count": second_run.reused_count,
            "second_run_new_bytes": result.second_run_new_bytes,
            "blob_count_stable": result.blob_count_stable,
            "hash_match_both_runs": result.hash_match_both_runs,
            "hash_algorithm": HASH_ALGORITHM,
            "idempotent_reuse_without_rewrite": (
                result.idempotent_reuse_without_rewrite
            ),
            "prohibited_raw_mutation_detected": (
                result.prohibited_raw_mutation_detected
            ),
            "quarantine_triggered": result.quarantine_triggered,
        },
        "authorized_io": {
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": (
                result.os_atime_side_effect_observed
            ),
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
        },
        "cleanup": _cleanup_public_value(
            cleanup_plan,
            synthetic_rehearsal_result,
        ),
        "privacy": {
            "raw_paths_in_projection": False,
            "raw_names_in_projection": False,
            "raw_hashes_in_projection": False,
            "raw_values_in_projection": False,
            "path_tokens_in_projection": False,
        },
    }
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    private_items = tuple(item for run in runs for item in run.items)
    if any(item.path_token in serialized for item in private_items) or any(
        item.content_sha256 in serialized for item in private_items
    ):
        raise PrivateRuntimeError(
            "PUBLIC_PROJECTION_PRIVATE_LEAK",
            "public projection contains a private token or digest",
        )
    return value


def build_private_receipt(
    result: PhaseRunResult,
    public_projection: Mapping[str, Any],
    *,
    cleanup_plan: CleanupPlan,
    synthetic_rehearsal_result: SyntheticCleanupRehearsalResult,
) -> dict[str, Any]:
    runs = _bound_import_runs(result)
    _validate_final_cleanup_evidence(
        result,
        cleanup_plan,
        synthetic_rehearsal_result,
    )
    projection_bytes = json.dumps(
        public_projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": PRIVATE_RECEIPT_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "target_release": TARGET_RELEASE,
        "stage_id": STAGE_ID,
        "phase_id": PHASE_ID,
        "status": result.status,
        "public_projection_sha256": (
            "sha256:" + hashlib.sha256(projection_bytes).hexdigest()
        ),
        "directory_contract": {
            "schema_version": RUNTIME_CONTRACT_SCHEMA_VERSION,
            "layers": list(result.runtime_contract.layers),
            "directory_mode": "0700",
            "private_file_mode": "0600",
            "cas_blob_mode": "0400",
        },
        "copy_authorization": {
            "root_id": result.first_import.copy_authorization.root_id,
            "source_scope_id": (
                result.first_import.copy_authorization.source_scope_id
            ),
            "authorization_scope": (
                result.first_import.copy_authorization.authorization_scope
            ),
            "operation": result.first_import.copy_authorization.operation,
            "target_layer": result.first_import.copy_authorization.target_layer,
            "allowed_extensions": list(
                result.first_import.copy_authorization.allowed_extensions
            ),
            "max_depth": result.first_import.copy_authorization.max_depth,
            "copy_allowed": result.first_import.copy_authorization.copy_allowed,
            "raw_parse_allowed": (
                result.first_import.copy_authorization.raw_parse_allowed
            ),
            "raw_value_extraction_allowed": (
                result.first_import.copy_authorization.raw_value_extraction_allowed
            ),
            "destination_must_be_private": (
                result.first_import.copy_authorization.destination_must_be_private
            ),
            "overwrite_existing_blob_allowed": (
                result.first_import.copy_authorization.overwrite_existing_blob_allowed
            ),
        },
        "p1_baseline_binding": {
            "fixed_project_entry": True,
            "policy_sha256": (
                "sha256:"
                + result.first_import.p1_baseline_binding.policy_sha256
            ),
            "p1_receipt_sha256": (
                "sha256:"
                + result.first_import.p1_baseline_binding.receipt_sha256
            ),
            "raw_root_device": (
                result.first_import.p1_baseline_binding.root_device
            ),
            "raw_root_inode": (
                result.first_import.p1_baseline_binding.root_inode
            ),
            "final_snapshot_file_rows": [
                {
                    "path_token": token,
                    "content_sha256": "sha256:" + digest,
                    "size_bytes": size,
                }
                for token, digest, size in (
                    result.first_import.p1_baseline_binding.file_rows
                )
            ],
            "final_drain_seconds": p1_guard.FINAL_DRAIN_SECONDS,
        },
        "runtime_root_binding": {
            "device": result.first_import.runtime_root_device,
            "inode": result.first_import.runtime_root_inode,
            "same_identity_both_runs": (
                (
                    result.first_import.runtime_root_device,
                    result.first_import.runtime_root_inode,
                )
                == (
                    result.second_import.runtime_root_device,
                    result.second_import.runtime_root_inode,
                )
            ),
            "pathname_identity_stable": True,
            "held_dirfd_both_runs": True,
        },
        "content_addressed_copy": {
            "hash_algorithm": HASH_ALGORITHM,
            "run_count": 2,
            "source_file_count": result.source_file_count,
            "unique_blob_count": result.unique_blob_count,
            "first_inventory": {
                "blob_count": result.first_import.cas_inventory.blob_count,
                "total_bytes": result.first_import.cas_inventory.total_bytes,
                "content_digests": [
                    "sha256:" + digest
                    for digest in result.first_import.cas_inventory.content_digests
                ],
                "source_digest_set_match": (
                    result.first_import.cas_inventory.source_digest_set_match
                ),
            },
            "second_inventory": {
                "blob_count": result.second_import.cas_inventory.blob_count,
                "total_bytes": result.second_import.cas_inventory.total_bytes,
                "content_digests": [
                    "sha256:" + digest
                    for digest in result.second_import.cas_inventory.content_digests
                ],
                "source_digest_set_match": (
                    result.second_import.cas_inventory.source_digest_set_match
                ),
            },
            "inventory_digest_set_stable": (
                result.inventory_digest_set_stable
            ),
            "blob_count_stable": result.blob_count_stable,
            "second_run_new_bytes": result.second_run_new_bytes,
            "runs": [
                {
                    "run_number": index,
                    "created_count": run.created_count,
                    "reused_count": run.reused_count,
                    "hash_match_all": run.hash_match_all,
                    "final_drain_seconds": run.final_drain_seconds,
                    "os_atime_side_effect_observed": (
                        run.os_atime_side_effect_observed
                    ),
                    "observation_scope": "raw_root_and_direct_files",
                    "items": [_private_item_value(item) for item in run.items],
                }
                for index, run in enumerate(runs, start=1)
            ],
        },
        "monitor": {
            "backends": [run.monitor_backend for run in runs],
            "production_backend_attested_all_runs": all(
                run.monitor_production_attested for run in runs
            ),
            "prohibited_raw_mutation_detected": (
                result.prohibited_raw_mutation_detected
            ),
        },
        "authorized_io": {
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": (
                result.os_atime_side_effect_observed
            ),
            "observation_scope": "raw_root_and_direct_files_each_copy_run",
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
        },
        "cleanup": {
            "mode": "DRY_RUN",
            "canonical_retention_basis": "UNTIL_CONDITION",
            "condition_based_retention": True,
            "evaluated_at_ns": cleanup_plan.evaluated_at_ns,
            "retention_days": dict(cleanup_plan.retention_days),
            "plan_digest": cleanup_plan.plan_digest,
            "candidate_count": len(cleanup_plan.candidates),
            "candidates": [
                {
                    "relative_path": item.relative_path,
                    "category": item.category,
                    "size_bytes": item.size_bytes,
                }
                for item in cleanup_plan.candidates
            ],
            "protected_count": cleanup_plan.protected_count,
            "protected_violation_count": cleanup_plan.protected_violation_count,
            "synthetic_rehearsal": {
                "status": synthetic_rehearsal_result.status,
                "candidate_count": synthetic_rehearsal_result.candidate_count,
                "backup_verified": (
                    synthetic_rehearsal_result.backup_verified
                ),
                "delete_verified": (
                    synthetic_rehearsal_result.delete_verified
                ),
                "restore_verified": (
                    synthetic_rehearsal_result.restore_verified
                ),
                "rehash_verified": (
                    synthetic_rehearsal_result.rehash_verified
                ),
                "protected_violation_count": (
                    synthetic_rehearsal_result.protected_violation_count
                ),
            },
        },
        "privacy": {
            "private_receipt_git_ignored": True,
            "raw_plaintext_paths_present": False,
            "raw_plaintext_names_present": False,
            "business_values_present": False,
        },
    }


def _write_private_file(path: Path, value: bytes, *, exclusive: bool) -> None:
    path = Path(path)
    if (
        not path.name
        or path.name in {".", ".."}
        or "/" in path.name
        or "\x00" in path.name
    ):
        raise PrivateRuntimeError(
            "PRIVATE_FILE_NAME_INVALID",
            "private evidence filename is invalid",
        )
    parent = path.parent
    _ensure_directory(parent)
    parent_descriptor = _open_directory(parent)
    temp_name = ".private_write_" + secrets.token_hex(16)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: Optional[int] = None
    promoted = False
    try:
        descriptor = os.open(
            temp_name,
            flags,
            PRIVATE_FILE_MODE,
            dir_fd=parent_descriptor,
        )
        os.fchmod(descriptor, PRIVATE_FILE_MODE)
        _write_all(descriptor, value)
        os.fsync(descriptor)
        temp_value = os.fstat(descriptor)
        if (
            not stat.S_ISREG(temp_value.st_mode)
            or int(temp_value.st_nlink) != 1
            or _mode(temp_value) != PRIVATE_FILE_MODE
        ):
            raise PrivateRuntimeError(
                "PRIVATE_FILE_TEMP_INVALID",
                "private temporary file failed type, link, or mode checks",
            )
        os.close(descriptor)
        descriptor = None

        try:
            existing = os.stat(
                path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            existing = None
        except OSError as exc:
            raise PrivateRuntimeError(
                "PRIVATE_FILE_EXISTING_CHECK_FAILED",
                "existing private evidence target could not be inspected",
            ) from exc
        if existing is not None and (
            not stat.S_ISREG(existing.st_mode) or int(existing.st_nlink) != 1
        ):
            raise PrivateRuntimeError(
                "PRIVATE_FILE_EXISTING_UNSAFE",
                "existing private target must be a single-link regular file",
            )
        if exclusive:
            if existing is not None:
                raise PrivateRuntimeError(
                    "PRIVATE_FILE_ALREADY_EXISTS",
                    "exclusive private evidence target already exists",
                )
            try:
                os.link(
                    temp_name,
                    path.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise PrivateRuntimeError(
                    "PRIVATE_FILE_ALREADY_EXISTS",
                    "exclusive private evidence target appeared concurrently",
                ) from exc
            os.unlink(temp_name, dir_fd=parent_descriptor)
            promoted = True
        else:
            os.replace(
                temp_name,
                path.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
            promoted = True
        os.fsync(parent_descriptor)
        final_value = os.stat(
            path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(final_value.st_mode)
            or int(final_value.st_nlink) != 1
            or _mode(final_value) != PRIVATE_FILE_MODE
        ):
            raise PrivateRuntimeError(
                "PRIVATE_FILE_FINAL_INVALID",
                "private evidence target failed final type, link, or mode checks",
            )
    except PrivateRuntimeError:
        raise
    except OSError as exc:
        raise PrivateRuntimeError(
            "PRIVATE_FILE_WRITE_FAILED",
            "private evidence file could not be securely written",
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not promoted:
            try:
                os.unlink(temp_name, dir_fd=parent_descriptor)
            except OSError:
                pass
        os.close(parent_descriptor)


def write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    _write_private_file(Path(path), payload, exclusive=False)


def initialize_synthetic_cleanup_runtime(runtime_root: Path) -> RuntimeContract:
    """Create a test-only runtime that can exercise confirmed deletion."""

    _verify_synthetic_fixture_location(runtime_root)
    contract = initialize_runtime(runtime_root)
    marker = contract.root / "logs" / _SYNTHETIC_MARKER_NAME
    if not marker.exists():
        _write_private_file(
            marker,
            _SYNTHETIC_MARKER_VALUE.encode("ascii"),
            exclusive=True,
        )
    return contract


def _verify_synthetic_fixture_location(runtime_root: Path) -> Path:
    try:
        temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        candidate = _absolute_runtime_root(runtime_root)
        resolved_candidate = Path(os.path.realpath(candidate))
    except OSError as exc:
        raise PrivateRuntimeError(
            "SYNTHETIC_FIXTURE_LOCATION_UNAVAILABLE",
            "synthetic cleanup fixture location could not be resolved",
        ) from exc
    if (
        resolved_candidate == temp_root
        or not _is_within(temp_root, resolved_candidate)
    ):
        raise PrivateRuntimeError(
            "SYNTHETIC_FIXTURE_OUTSIDE_OS_TEMP",
            "synthetic cleanup is restricted to the canonical OS temp root",
        )
    return resolved_candidate


def _retention_mapping(
    retention_days: Optional[Mapping[str, int]],
) -> dict[str, int]:
    if retention_days is None:
        return dict(DEFAULT_RETENTION_DAYS)
    if set(retention_days) != set(RETENTION_CATEGORIES):
        raise PrivateRuntimeError(
            "RETENTION_POLICY_FIELDS_DRIFT",
            "explicit retention policy must define the exact registered categories",
        )
    value = dict(retention_days)
    if any(type(days) is not int or days < 0 for days in value.values()):
        raise PrivateRuntimeError(
            "RETENTION_POLICY_INVALID",
            "retention days must be non-negative integers",
        )
    return value


def _walk_regular_files(layer_path: Path) -> list[tuple[str, os.stat_result]]:
    output: list[tuple[str, os.stat_result]] = []
    for current_root, directory_names, file_names in os.walk(
        layer_path,
        topdown=True,
        followlinks=False,
    ):
        directory_names.sort()
        file_names.sort()
        current = Path(current_root)
        for name in list(directory_names):
            child = current / name
            value = os.lstat(child)
            if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
                raise PrivateRuntimeError(
                    "CLEANUP_DIRECTORY_TYPE_INVALID",
                    "cleanup planning rejects symlink or non-directory traversal",
                )
            if _mode(value) != DIRECTORY_MODE:
                raise PrivateRuntimeError(
                    "CLEANUP_DIRECTORY_MODE_INVALID",
                    "cleanup directories must remain mode 0700",
                )
        for name in file_names:
            child = current / name
            value = os.lstat(child)
            if (
                stat.S_ISLNK(value.st_mode)
                or not stat.S_ISREG(value.st_mode)
                or int(value.st_nlink) != 1
            ):
                raise PrivateRuntimeError(
                    "CLEANUP_FILE_TYPE_INVALID",
                    "cleanup planning rejects symlink, special, or multi-link files",
                )
            relative = child.relative_to(layer_path).as_posix()
            output.append((relative, value))
    return output


def _candidate_category(layer: str, relative: str) -> Optional[str]:
    parts = tuple(Path(relative).parts)
    if layer in {"extracted", "staging", "cache"}:
        return layer
    if layer == "reports" and parts and parts[0] == "drafts":
        return "report_draft"
    if layer == "logs" and parts and parts[0] == "operational":
        return "operational_log"
    return None


def _candidate_payload(candidate: CleanupCandidate) -> dict[str, Any]:
    return {
        "relative_path": candidate.relative_path,
        "category": candidate.category,
        "size_bytes": candidate.size_bytes,
        "device": candidate.device,
        "inode": candidate.inode,
        "mode": candidate.mode,
        "link_count": candidate.link_count,
        "mtime_ns": candidate.mtime_ns,
        "ctime_ns": candidate.ctime_ns,
    }


def _plan_payload(
    *,
    root_device: int,
    root_inode: int,
    candidates: Sequence[CleanupCandidate],
    protected_count: int,
    protected_violation_count: int,
    retention_days: Mapping[str, int],
    evaluated_at_ns: int,
) -> dict[str, Any]:
    return {
        "schema_version": CLEANUP_PLAN_SCHEMA_VERSION,
        "root_identity": [root_device, root_inode],
        "candidates": [_candidate_payload(item) for item in candidates],
        "protected_count": protected_count,
        "protected_violation_count": protected_violation_count,
        "retention_days": dict(sorted(retention_days.items())),
        "evaluated_at_ns": evaluated_at_ns,
    }


def _payload_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_cleanup_plan(
    runtime_root: Path,
    *,
    now_ns: int,
    retention_days: Optional[Mapping[str, int]] = None,
) -> CleanupPlan:
    """Build a deterministic dry-run plan; never delete from this function."""

    if type(now_ns) is not int or now_ns < 0:
        raise PrivateRuntimeError(
            "CLEANUP_NOW_INVALID",
            "cleanup planning requires a non-negative integer timestamp",
        )
    contract = inspect_runtime_contract(runtime_root)
    policy = _retention_mapping(retention_days)
    root_value = os.lstat(contract.root)
    candidates: list[CleanupCandidate] = []
    protected_count = 0

    backup_rows = _walk_regular_files(contract.root / "backups")
    newest_backup: Optional[str] = None
    if backup_rows:
        newest_backup = max(
            backup_rows,
            key=lambda item: (int(item[1].st_mtime_ns), item[0]),
        )[0]

    for layer in RUNTIME_LAYERS:
        rows = backup_rows if layer == "backups" else _walk_regular_files(
            contract.root / layer
        )
        for relative, value in rows:
            if layer == "logs" and (
                relative == _SYNTHETIC_MARKER_NAME
                or relative.startswith(_CONFIRMATION_PREFIX)
            ):
                # Synthetic capability/confirmation controls are excluded
                # from lifecycle accounting so a second invocation can
                # rebuild the exact pre-confirmation plan.
                continue
            category = _candidate_category(layer, relative)
            if layer == "backups":
                category = None if relative == newest_backup else "backup_duplicate"
            if category is None:
                protected_count += 1
                continue
            if category not in policy:
                # Canonical TaskPack behavior: UNTIL_CONDITION / no automatic
                # delete.  Numeric rehearsal periods must be explicit.
                protected_count += 1
                continue
            age_ns = max(0, now_ns - int(value.st_mtime_ns))
            threshold_ns = policy[category] * 24 * 60 * 60 * 1_000_000_000
            if age_ns < threshold_ns:
                protected_count += 1
                continue
            relative_path = f"{layer}/{relative}"
            candidates.append(
                CleanupCandidate(
                    relative_path=relative_path,
                    category=category,
                    size_bytes=int(value.st_size),
                    device=int(value.st_dev),
                    inode=int(value.st_ino),
                    mode=int(value.st_mode),
                    link_count=int(value.st_nlink),
                    mtime_ns=int(value.st_mtime_ns),
                    ctime_ns=int(value.st_ctime_ns),
                )
            )
    ordered = tuple(sorted(candidates, key=lambda item: item.relative_path))
    protected_violation_count = 0
    payload = _plan_payload(
        root_device=int(root_value.st_dev),
        root_inode=int(root_value.st_ino),
        candidates=ordered,
        protected_count=protected_count,
        protected_violation_count=protected_violation_count,
        retention_days=policy,
        evaluated_at_ns=now_ns,
    )
    return CleanupPlan(
        runtime_root=contract.root,
        root_device=int(root_value.st_dev),
        root_inode=int(root_value.st_ino),
        candidates=ordered,
        protected_count=protected_count,
        protected_violation_count=protected_violation_count,
        total_candidate_bytes=sum(item.size_bytes for item in ordered),
        retention_days=policy,
        evaluated_at_ns=now_ns,
        plan_digest=_payload_digest(payload),
    )


def _verify_plan_digest(plan: CleanupPlan) -> None:
    payload = _plan_payload(
        root_device=plan.root_device,
        root_inode=plan.root_inode,
        candidates=plan.candidates,
        protected_count=plan.protected_count,
        protected_violation_count=plan.protected_violation_count,
        retention_days=plan.retention_days,
        evaluated_at_ns=plan.evaluated_at_ns,
    )
    if _payload_digest(payload) != plan.plan_digest:
        raise PrivateRuntimeError(
            "CLEANUP_PLAN_DIGEST_INVALID",
            "cleanup plan digest does not match its deterministic content",
        )


def _verify_plan_matches_current_runtime(plan: CleanupPlan) -> None:
    rebuilt = build_cleanup_plan(
        plan.runtime_root,
        now_ns=plan.evaluated_at_ns,
        retention_days=(plan.retention_days or None),
    )
    if rebuilt != plan:
        raise PrivateRuntimeError(
            "CLEANUP_PLAN_STATE_MISMATCH",
            "cleanup plan does not exactly match a full current-state rebuild",
        )


def _verify_synthetic_marker(plan: CleanupPlan) -> None:
    _verify_synthetic_fixture_location(plan.runtime_root)
    marker = plan.runtime_root / "logs" / _SYNTHETIC_MARKER_NAME
    try:
        value = os.lstat(marker)
    except OSError as exc:
        raise PrivateRuntimeError(
            "REAL_RUNTIME_CLEANUP_FORBIDDEN",
            "destructive cleanup is allowed only in a marked synthetic runtime",
        ) from exc
    if (
        stat.S_ISLNK(value.st_mode)
        or not stat.S_ISREG(value.st_mode)
        or int(value.st_nlink) != 1
        or _mode(value) != PRIVATE_FILE_MODE
        or marker.read_text(encoding="ascii") != _SYNTHETIC_MARKER_VALUE
    ):
        raise PrivateRuntimeError(
            "SYNTHETIC_MARKER_INVALID",
            "synthetic cleanup marker failed type, link, mode, or content checks",
        )


def _confirmation_name(plan: CleanupPlan, suffix: str) -> str:
    digest = plan.plan_digest.removeprefix("sha256:")
    return f"{_CONFIRMATION_PREFIX}{digest}.{suffix}"


def prepare_cleanup_confirmation(plan: CleanupPlan) -> str:
    """First invocation: arm an exact plan digest in a synthetic runtime."""

    _verify_plan_digest(plan)
    _verify_synthetic_marker(plan)
    _verify_plan_matches_current_runtime(plan)
    pending = plan.runtime_root / "logs" / _confirmation_name(plan, "pending")
    _write_private_file(
        pending,
        (plan.plan_digest + "\n").encode("ascii"),
        exclusive=True,
    )
    return plan.plan_digest


def _open_relative_parent(root_descriptor: int, relative_path: str) -> tuple[int, str]:
    parts = tuple(Path(relative_path).parts)
    if (
        len(parts) < 2
        or any(part in {"", ".", ".."} or "/" in part for part in parts)
        or Path(relative_path).is_absolute()
    ):
        raise PrivateRuntimeError(
            "CLEANUP_RELATIVE_PATH_INVALID",
            "cleanup candidate path is not a safe runtime-relative path",
        )
    current = os.dup(root_descriptor)
    try:
        for part in parts[:-1]:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            flags |= getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            next_descriptor = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = next_descriptor
            opened = os.fstat(current)
            if not stat.S_ISDIR(opened.st_mode):
                raise PrivateRuntimeError(
                    "CLEANUP_PARENT_TYPE_DRIFT",
                    "cleanup candidate parent is not a directory",
                )
        return current, parts[-1]
    except Exception:
        os.close(current)
        raise


def _candidate_matches(value: os.stat_result, item: CleanupCandidate) -> bool:
    return (
        stat.S_ISREG(value.st_mode)
        and int(value.st_nlink) == 1
        and (
            int(value.st_dev),
            int(value.st_ino),
            int(value.st_mode),
            int(value.st_nlink),
            int(value.st_size),
            int(value.st_mtime_ns),
            int(value.st_ctime_ns),
        )
        == (
            item.device,
            item.inode,
            item.mode,
            item.link_count,
            item.size_bytes,
            item.mtime_ns,
            item.ctime_ns,
        )
    )


def execute_synthetic_cleanup(
    plan: CleanupPlan,
    *,
    confirmation_digest: str,
) -> CleanupExecutionResult:
    """Second invocation: consume one marker and delete only synthetic files."""

    _verify_plan_digest(plan)
    _verify_synthetic_marker(plan)
    if confirmation_digest != plan.plan_digest:
        raise PrivateRuntimeError(
            "CLEANUP_CONFIRMATION_MISMATCH",
            "confirmation must exactly equal the current plan digest",
        )
    _verify_plan_matches_current_runtime(plan)
    root_descriptor = _open_directory(plan.runtime_root)
    parent_rows: list[tuple[int, str, CleanupCandidate]] = []
    logs_descriptor: Optional[int] = None
    try:
        root_value = os.fstat(root_descriptor)
        if (int(root_value.st_dev), int(root_value.st_ino)) != (
            plan.root_device,
            plan.root_inode,
        ):
            raise PrivateRuntimeError(
                "CLEANUP_ROOT_IDENTITY_DRIFT",
                "cleanup runtime identity changed after dry run",
            )
        logs_descriptor, _ = _open_relative_parent(
            root_descriptor,
            "logs/placeholder",
        )
        used_name = _confirmation_name(plan, "used")
        try:
            os.stat(
                used_name,
                dir_fd=logs_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_CHECK_FAILED",
                "one-use cleanup marker could not be inspected",
            ) from exc
        else:
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_ALREADY_USED",
                "cleanup confirmation marker is one-use only",
            )
        for item in plan.candidates:
            parent_descriptor, name = _open_relative_parent(
                root_descriptor,
                item.relative_path,
            )
            try:
                value = os.stat(
                    name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                os.close(parent_descriptor)
                raise PrivateRuntimeError(
                    "CLEANUP_CANDIDATE_DRIFT",
                    "cleanup candidate disappeared after dry run",
                ) from exc
            if not _candidate_matches(value, item):
                os.close(parent_descriptor)
                raise PrivateRuntimeError(
                    "CLEANUP_CANDIDATE_DRIFT",
                    "cleanup candidate identity changed after dry run",
                )
            parent_rows.append((parent_descriptor, name, item))

        pending_name = _confirmation_name(plan, "pending")
        try:
            pending_value = os.stat(
                pending_name,
                dir_fd=logs_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_NOT_ARMED",
                "exact-digest cleanup confirmation has not been prepared",
            ) from exc
        if (
            not stat.S_ISREG(pending_value.st_mode)
            or int(pending_value.st_nlink) != 1
            or _mode(pending_value) != PRIVATE_FILE_MODE
        ):
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_INVALID",
                "cleanup confirmation marker failed type, link, or mode checks",
            )
        pending_fd = os.open(
            pending_name,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=logs_descriptor,
        )
        try:
            pending_bytes = b""
            while True:
                chunk = os.read(pending_fd, 4096)
                if not chunk:
                    break
                pending_bytes += chunk
        finally:
            os.close(pending_fd)
        if pending_bytes != (plan.plan_digest + "\n").encode("ascii"):
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_INVALID",
                "cleanup confirmation marker content differs from the plan digest",
            )

        used_fd = os.open(
            used_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            PRIVATE_FILE_MODE,
            dir_fd=logs_descriptor,
        )
        try:
            os.fchmod(used_fd, PRIVATE_FILE_MODE)
            _write_all(used_fd, (plan.plan_digest + "\n").encode("ascii"))
            os.fsync(used_fd)
        finally:
            os.close(used_fd)
        os.unlink(pending_name, dir_fd=logs_descriptor)

        deleted_bytes = 0
        for parent_descriptor, name, item in parent_rows:
            current = os.stat(
                name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if not _candidate_matches(current, item):
                raise PrivateRuntimeError(
                    "CLEANUP_CANDIDATE_DRIFT",
                    "cleanup candidate changed immediately before deletion",
                )
            os.unlink(name, dir_fd=parent_descriptor)
            deleted_bytes += item.size_bytes
        return CleanupExecutionResult(
            status="PASS",
            deleted_count=len(parent_rows),
            deleted_bytes=deleted_bytes,
            confirmation_marker_consumed=True,
        )
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise PrivateRuntimeError(
                "CLEANUP_CONFIRMATION_ALREADY_USED",
                "cleanup confirmation marker is one-use only",
            ) from exc
        raise PrivateRuntimeError(
            "CLEANUP_EXECUTION_FAILED",
            "synthetic cleanup failed closed",
        ) from exc
    finally:
        for parent_descriptor, _, _ in parent_rows:
            try:
                os.close(parent_descriptor)
            except OSError:
                pass
        if logs_descriptor is not None:
            os.close(logs_descriptor)
        os.close(root_descriptor)


def _read_synthetic_candidate(
    plan: CleanupPlan,
    item: CleanupCandidate,
    *,
    require_planned_identity: bool,
) -> bytes:
    root_descriptor = _open_directory(plan.runtime_root)
    parent_descriptor: Optional[int] = None
    descriptor: Optional[int] = None
    try:
        parent_descriptor, name = _open_relative_parent(
            root_descriptor,
            item.relative_path,
        )
        linked = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if require_planned_identity:
            valid = _candidate_matches(linked, item)
        else:
            valid = (
                stat.S_ISREG(linked.st_mode)
                and int(linked.st_nlink) == 1
                and _mode(linked) == PRIVATE_FILE_MODE
                and int(linked.st_size) == item.size_bytes
            )
        if not valid:
            raise PrivateRuntimeError(
                "SYNTHETIC_REHEARSAL_FILE_INVALID",
                "synthetic rehearsal file failed identity or private-mode checks",
            )
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        if (
            int(opened.st_dev),
            int(opened.st_ino),
            int(opened.st_mode),
            int(opened.st_nlink),
            int(opened.st_size),
        ) != (
            int(linked.st_dev),
            int(linked.st_ino),
            int(linked.st_mode),
            int(linked.st_nlink),
            int(linked.st_size),
        ):
            raise PrivateRuntimeError(
                "SYNTHETIC_REHEARSAL_FILE_DRIFT",
                "synthetic rehearsal file changed during secure open",
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, HASH_CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
        payload = b"".join(chunks)
        if len(payload) != item.size_bytes:
            raise PrivateRuntimeError(
                "SYNTHETIC_REHEARSAL_SIZE_MISMATCH",
                "synthetic rehearsal bytes differ from the planned size",
            )
        return payload
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        os.close(root_descriptor)


def run_synthetic_cleanup_rehearsal(
    plan: CleanupPlan,
) -> SyntheticCleanupRehearsalResult:
    """Exercise backup, delete, restore, and rehash in an OS-temp fixture."""

    _verify_plan_digest(plan)
    _verify_synthetic_marker(plan)
    _verify_plan_matches_current_runtime(plan)
    if not plan.candidates:
        raise PrivateRuntimeError(
            "SYNTHETIC_REHEARSAL_CANDIDATES_EMPTY",
            "synthetic rehearsal requires at least one explicit fixture candidate",
        )
    backups: list[tuple[CleanupCandidate, bytes, str]] = []
    for item in plan.candidates:
        if stat.S_IMODE(item.mode) != PRIVATE_FILE_MODE:
            raise PrivateRuntimeError(
                "SYNTHETIC_REHEARSAL_MODE_INVALID",
                "synthetic rehearsal candidates must be private mode 0600",
            )
        payload = _read_synthetic_candidate(
            plan,
            item,
            require_planned_identity=True,
        )
        digest = hashlib.sha256(payload).hexdigest()
        if hashlib.sha256(bytes(payload)).hexdigest() != digest:
            raise PrivateRuntimeError(
                "SYNTHETIC_BACKUP_VERIFY_FAILED",
                "synthetic in-memory backup failed immediate verification",
            )
        backups.append((item, payload, digest))

    confirmation = prepare_cleanup_confirmation(plan)
    execution = execute_synthetic_cleanup(
        plan,
        confirmation_digest=confirmation,
    )
    delete_verified = execution.deleted_count == len(backups) and all(
        not (plan.runtime_root / item.relative_path).exists()
        for item, _, _ in backups
    )
    if not delete_verified:
        raise PrivateRuntimeError(
            "SYNTHETIC_DELETE_VERIFY_FAILED",
            "synthetic candidates were not all deleted",
        )

    for item, payload, _ in backups:
        destination = plan.runtime_root / item.relative_path
        _write_private_file(destination, payload, exclusive=True)
        os.utime(
            destination,
            ns=(item.mtime_ns, item.mtime_ns),
            follow_symlinks=False,
        )
        os.chmod(destination, PRIVATE_FILE_MODE, follow_symlinks=False)
    restore_verified = all(
        (plan.runtime_root / item.relative_path).is_file()
        for item, _, _ in backups
    )
    if not restore_verified:
        raise PrivateRuntimeError(
            "SYNTHETIC_RESTORE_VERIFY_FAILED",
            "synthetic candidates were not all restored",
        )

    rehash_verified = True
    for item, _, digest in backups:
        restored = _read_synthetic_candidate(
            plan,
            item,
            require_planned_identity=False,
        )
        rehash_verified = rehash_verified and (
            hashlib.sha256(restored).hexdigest() == digest
        )
    if not rehash_verified:
        raise PrivateRuntimeError(
            "SYNTHETIC_REHASH_VERIFY_FAILED",
            "restored synthetic content differs from its verified backup",
        )
    return SyntheticCleanupRehearsalResult(
        status="PASS",
        backup_verified=True,
        delete_verified=True,
        restore_verified=True,
        rehash_verified=True,
        protected_violation_count=plan.protected_violation_count,
        candidate_count=len(plan.candidates),
    )
