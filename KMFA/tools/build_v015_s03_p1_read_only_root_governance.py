#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S03-P1.

The live guard keeps the exact raw-root path, recursive fingerprints, content
hashes, and vnode events in the ignored private runtime.  This builder verifies
that private evidence and emits only the public-safe phase contract, aggregate
guard result, Task evidence-slot index, and validation receipts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import ZipFile

from KMFA.tools import v015_s03_p1_read_only_root_guard as guard


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PHASE_BASE_COMMIT = "70a3699255c5cf8d23928fbaf0d365ce37ea2c0f"
SOURCE_PACKAGE_NAME = "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
SOURCE_MANIFEST_BASENAME = "15_MANIFEST_SHA256_v2_0.csv"
SOURCE_MANIFEST_SHA256 = "a4a5cb0e301a841a922e761ff503a2fce72982b1b088d9aeee9e11998939b2a5"
SOURCE_ROADMAP_BASENAME = "02B_KMFA_Codex_Development_Roadmap_v2_0.json"
SOURCE_ROADMAP_SHA256 = "741fdf6a1dd6d04fdaaf916f8cf84ebce07207fbb50d7971736c1c9fc46a5145"
TRACKED_ROADMAP_SHA256 = "a0efdddc6e54a167751938353f71bb60a9cd4b43cbcf444d4c915a45b8b1ec06"
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME

RUN_PHASE_ID = "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"
TASK_ID = "KMFA-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-20260713"
ACCEPTANCE_ID = "ACC-KMFA-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE"
ROOT_ID = "PRIMARY_RAW_ROOT"
OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE")
PRIVATE_ROOT_RELATIVE = Path(".codex_private_runtime/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE")
PRIVATE_POLICY_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_root_policy.json"
PRIVATE_RECEIPT_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_guard_receipt.json"
PRIVATE_PROJECTION_RELATIVE = PRIVATE_ROOT_RELATIVE / "public_guard_projection.json"
PRIVATE_FAILURE_SENTINEL_RELATIVE = PRIVATE_ROOT_RELATIVE / "public_guard_failure_sentinel.json"
PRIVATE_VALIDATION_RECEIPTS_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_validation_receipts.jsonl"

MANIFEST_RELATIVE = Path("machine/s03_p1_read_only_root_governance_manifest.json")
TASK_MATRIX_RELATIVE = Path("machine/task_acceptance_matrix_public_safe.json")
WRITE_GUARD_RELATIVE = Path("machine/write_protection_validation_public_safe.json")
READ_SCOPE_RELATIVE = Path("machine/read_scope_whitelist_public_safe.json")
EVIDENCE_SLOTS_RELATIVE = Path("machine/task_evidence_slot_matrix_public_safe.jsonl")
RECEIPT_TEMPLATE_RELATIVE = Path("machine/validation_receipts_template.jsonl")
VALIDATION_RESULTS_RELATIVE = Path("machine/validation_results.jsonl")
COMPLETION_RELATIVE = Path("human/completion_record_zh.md")
TEST_RESULTS_RELATIVE = Path("human/test_results_zh.md")
ROLLBACK_RELATIVE = Path("human/rollback_plan_zh.md")
OPEN_RISKS_RELATIVE = Path("human/open_risks_zh.md")
PUBLIC_REGISTRY_RELATIVE = Path("metadata/protocol/v015_s03_p1_read_only_root_registry_public_safe.json")
PUBLIC_ALLOWLIST_RELATIVE = Path("metadata/protocol/v015_s03_p1_read_allowlist_public_safe.json")

ARTIFACT_REFS = {
    "manifest": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{MANIFEST_RELATIVE.as_posix()}",
    "task_matrix": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{TASK_MATRIX_RELATIVE.as_posix()}",
    "write_guard": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{WRITE_GUARD_RELATIVE.as_posix()}",
    "read_scope": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{READ_SCOPE_RELATIVE.as_posix()}",
    "evidence_slots": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{EVIDENCE_SLOTS_RELATIVE.as_posix()}",
    "receipt_template": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{RECEIPT_TEMPLATE_RELATIVE.as_posix()}",
    "validation_results": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{VALIDATION_RESULTS_RELATIVE.as_posix()}",
    "completion": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{COMPLETION_RELATIVE.as_posix()}",
    "test_results": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{TEST_RESULTS_RELATIVE.as_posix()}",
    "rollback": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{ROLLBACK_RELATIVE.as_posix()}",
    "open_risks": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{OPEN_RISKS_RELATIVE.as_posix()}",
    "public_registry": f"KMFA/{PUBLIC_REGISTRY_RELATIVE.as_posix()}",
    "public_allowlist": f"KMFA/{PUBLIC_ALLOWLIST_RELATIVE.as_posix()}",
}

VALIDATION_RECEIPT_SCHEMA_VERSION = "kmfa.v015.s03_p1.validation_receipt.v1"
# The live replay can legitimately change aggregate atime observation and the
# owner-write observation.  Public projections carrying those aggregates are
# therefore post-run outputs: final manifest integrity plus the strict checker
# bind them, while the pre-run validation subject excludes them.
VALIDATION_MUTABLE_ARTIFACT_KEYS = frozenset({
    "manifest", "task_matrix", "write_guard", "validation_results", "completion",
    "test_results", "open_risks", "public_registry",
})
# Acceptance-state governance mirrors and append-only ledgers are promoted only
# after the receipt run.  The final strict checker validates them, but including
# them in the pre-run subject would either pre-open the S03-P2 gate or create a
# circular claim about a validation result that does not yet exist.
POST_VALIDATION_GOVERNANCE_REFS = frozenset({
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
})
VALIDATION_SUBJECT_REFS = tuple(sorted(
    {
        ref
        for key, ref in ARTIFACT_REFS.items()
        if key not in VALIDATION_MUTABLE_ARTIFACT_KEYS
    }
    | {
        "KMFA/tools/v015_s03_p1_read_only_root_guard.py",
        "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py",
        "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py",
        "KMFA/tools/run_v015_s03_p1_validations.py",
        "KMFA/tests/test_v015_s03_p1_read_only_root_guard.py",
        "KMFA/tests/test_v015_s03_p1_read_only_root_governance.py",
        "KMFA/tests/test_v015_s03_p1_validation_runner.py",
        "KMFA/tools/check_no_float_money.py",
        "KMFA/tools/no_omission_check.py",
        "scripts/lean_governance.py",
        "scripts/validate_governance_sync.py",
        "scripts/validate_project_governance.py",
        "scripts/validate_semantic_extractors.py",
        "KMFA/tools/v015_roadmap_governance_sync.py",
        "KMFA/tests/test_v015_roadmap_governance_sync.py",
        "KMFA/AGENTS.md",
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/README.md",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/formula_registry.yaml",
        "KMFA/docs/governance/MODEL_SPEC.md",
        "KMFA/docs/governance/model_registry.yaml",
        "KMFA/docs/governance/parameter_registry.csv",
        "KMFA/docs/governance/project.yaml",
        "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/model_registry.yaml",
        "KMFA/metadata/project/project.yaml",
        "KMFA/tests/test_v015_roadmap_governance_sync.py",
        "KMFA/tools/v015_roadmap_governance_sync.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    }
    - POST_VALIDATION_GOVERNANCE_REFS
))

EXPECTED_ALLOWED_OPERATIONS = ("list", "read", "stat", "hash")
EXPECTED_MUTATION_CLASSES = ("CREATE", "DELETE", "MODIFY", "RENAME")
EXPECTED_PROHIBITED_MUTATION_SCOPE = (
    "content", "namespace", "permission", "owner", "xattr", "flags",
    "size", "mtime", "ctime", "inode",
)
EXPECTED_ALLOWED_EXTENSIONS = (".xlsx", ".zip")
EXPECTED_SOURCE_SCOPE_ID = guard.EXPECTED_SOURCE_SCOPE_ID
EXPECTED_MAX_DEPTH = guard.EXPECTED_MAX_DEPTH
EVIDENCE_SLOTS = (
    "manifest.json", "commands.txt", "test_results.json", "human_summary.md",
    "changed_files.txt", "screenshots/", "logs/", "exports/", "rollback.md",
    "open_risks.md",
)

TASKS = (
    {
        "task_id": "S03P1T01", "name": "登记原始数据根目录",
        "action": "将本机路径、权限、允许操作和禁止操作写入机器可读配置。",
        "output": "只读根目录登记。",
        "acceptance": "只允许列举、读取、stat、hash；禁止写删改移覆盖。",
        "evidence": "权限配置与测试。",
        "stop": "目录不可读或权限不明时停止。",
    },
    {
        "task_id": "S03P1T02", "name": "实现目录写保护验证",
        "action": "运行前后递归指纹比对并监控文件系统事件。",
        "output": "写保护验证器。",
        "acceptance": "任何新增、删除、修改、重命名均失败。",
        "evidence": "自动测试与事件日志。",
        "stop": "发现写入立即终止任务。",
    },
    {
        "task_id": "S03P1T03", "name": "设计最小读取授权",
        "action": "按数据源和文件类型定义最小读取范围。",
        "output": "读取白名单。",
        "acceptance": "不得全盘扫描无关目录。",
        "evidence": "白名单与拒绝测试。",
        "stop": "越界读取即失败。",
    },
)

EXPECTED_VALIDATION_RECEIPTS = {
    "python_compile": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; "
        "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in "
        "('KMFA/tools/v015_s03_p1_read_only_root_guard.py',"
        "'KMFA/tools/build_v015_s03_p1_read_only_root_governance.py',"
        "'KMFA/tools/check_v015_s03_p1_read_only_root_governance.py',"
        "'KMFA/tools/run_v015_s03_p1_validations.py')]\""
    ),
    "source_package_integrity": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py --source-only"
    ),
    "guard_focused_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p1_read_only_root_guard"
    ),
    "phase_focused_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p1_read_only_root_governance"
    ),
    "validation_runner_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p1_validation_runner"
    ),
    "builder_exact_rebuild": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py --check"
    ),
    "roadmap_governance_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_roadmap_governance_sync"
    ),
    "project_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/validate_project_governance.py --project KMFA --mode required"
    ),
    "lean_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/lean_governance.py validate --project KMFA --mode required"
    ),
    "governance_sync": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        f"scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE_COMMIT} --enforce-sync"
    ),
    "no_float_money": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"
    ),
    "no_omission": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"
    ),
    "git_diff_check": "git diff --check",
    "live_raw_guard_receipt_freshness": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py "
        "--private-evidence-only --require-event-monitor "
        "--max-private-evidence-age-seconds 7200"
    ),
    "checker_core_private_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py "
        "--require-private-evidence --require-event-monitor --require-dependency-validator "
        "--skip-validation-receipts --skip-exact-rebuild "
        "--pre-receipt-final-governance"
    ),
}

_FORBIDDEN_PUBLIC_TOKENS = (
    b"/" + b"Users/", b"/" + b"Volumes/", b"/" + b"private/",
    b"/" + b"tmp/", b"/" + b"home/", b"KMFA_" + b"MetaData",
)
_EMAIL_RE = re.compile(rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SECRET_RE = re.compile(
    rb"(?i)(?:api[_-]?key|password|secret|(?:access|auth|bearer|refresh|session)[_-]?token)"
    rb"\s*[:=]\s*['\"][^'\"]{8,}"
)


class BuildError(RuntimeError):
    """Raised when the source, private evidence, or output contract drifts."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def _content_hash(value: Mapping[str, Any]) -> str:
    copy = dict(value)
    copy.pop("content_hash", None)
    return "sha256:" + _sha256(
        json.dumps(copy, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _read_signature(value: os.stat_result) -> tuple[int, ...]:
    return (
        int(value.st_dev), int(value.st_ino), int(value.st_mode),
        int(value.st_nlink), int(value.st_uid), int(value.st_gid),
        int(value.st_size), int(value.st_mtime_ns), int(value.st_ctime_ns),
        int(getattr(value, "st_flags", 0)),
    )


def _read_regular_bytes_no_follow(path: Path, *, label: str) -> bytes:
    """Read one stable single-link regular file without following final links."""

    try:
        before = os.lstat(path)
    except OSError as error:
        raise BuildError(f"{label} unavailable: {path}: {error}") from error
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or int(before.st_nlink) != 1
    ):
        raise BuildError(f"{label} type/link unsafe: {path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise BuildError(f"{label} open failed: {path}: {error}") from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or int(opened.st_nlink) != 1
            or _read_signature(opened) != _read_signature(before)
        ):
            raise BuildError(f"{label} identity changed before read: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if _read_signature(after) != _read_signature(opened):
            raise BuildError(f"{label} changed during read: {path}")
        try:
            linked_after = os.lstat(path)
        except OSError as error:
            raise BuildError(f"{label} path disappeared after read: {path}") from error
        if _read_signature(linked_after) != _read_signature(after):
            raise BuildError(f"{label} path identity changed after read: {path}")
        payload = b"".join(chunks)
        if len(payload) != int(opened.st_size):
            raise BuildError(f"{label} size changed during read: {path}")
        return payload
    finally:
        os.close(descriptor)


def validation_subject_sha256(project_root: Optional[Path] = None) -> str:
    """Hash every immutable public input validated by the S03-P1 receipt run."""

    root = _normalize_project_root(project_root)
    repo_root = root.parent
    digest = hashlib.sha256()
    for seed in (
        "kmfa.v015.s03_p1.validation_subject.v1",
        PHASE_BASE_COMMIT,
        SOURCE_PACKAGE_SHA256,
    ):
        digest.update(seed.encode("utf-8"))
        digest.update(b"\0")
    for ref in VALIDATION_SUBJECT_REFS:
        path = repo_root / ref
        payload = _read_regular_bytes_no_follow(path, label="validation subject file")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(payload)).encode("ascii"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_regular_bytes_no_follow(path, label="required JSON").decode("utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    payload = _read_regular_bytes_no_follow(path, label="required JSONL").decode("utf-8")
    for line_no, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise BuildError(f"expected JSON object at {path}:{line_no}")
        rows.append(value)
    return rows


def _normalize_project_root(project_root: Optional[Path]) -> Path:
    root = PROJECT_ROOT if project_root is None else Path(project_root).resolve()
    if (root / "tools").is_dir() and (root / "stage_artifacts").is_dir():
        return root
    nested = root / "KMFA"
    if (nested / "tools").is_dir() and (nested / "stage_artifacts").is_dir():
        return nested
    raise BuildError(f"KMFA project root not found: {root}")


def _find_member(archive: ZipFile, basename: str) -> str:
    matches = [name for name in archive.namelist() if PurePosixPath(name).name == basename]
    if len(matches) != 1:
        raise BuildError(f"source member count drift for {basename}: {len(matches)}")
    return matches[0]


def _source_s03_p1(roadmap: Mapping[str, Any]) -> dict[str, Any]:
    stages = roadmap.get("stages")
    if not isinstance(stages, list):
        raise BuildError("source roadmap stages missing")
    matches = [item for item in stages if isinstance(item, dict) and item.get("id") == "S03"]
    if len(matches) != 1:
        raise BuildError("source S03 count drift")
    phases = matches[0].get("phases")
    if not isinstance(phases, list):
        raise BuildError("source S03 phases missing")
    phase = [item for item in phases if isinstance(item, dict) and item.get("id") == "P1"]
    if len(phase) != 1:
        raise BuildError("source S03-P1 count drift")
    return phase[0]


def verify_source_package(source_package: Path = DEFAULT_SOURCE_PACKAGE, project_root: Optional[Path] = None) -> dict[str, Any]:
    root = _normalize_project_root(project_root)
    package = Path(source_package)
    package_payload = _read_regular_bytes_no_follow(package, label="source package")
    if _sha256(package_payload) != SOURCE_PACKAGE_SHA256:
        raise BuildError("source package SHA-256 drift")
    with ZipFile(io.BytesIO(package_payload)) as archive:
        manifest_name = _find_member(archive, SOURCE_MANIFEST_BASENAME)
        manifest_payload = archive.read(manifest_name)
        if _sha256(manifest_payload) != SOURCE_MANIFEST_SHA256:
            raise BuildError("source manifest SHA-256 drift")
        rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8-sig"))))
        if len(rows) != 21 or set(rows[0] if rows else {}) != {"相对路径", "字节数", "SHA256"}:
            raise BuildError("source manifest schema/count drift")
        archive_by_relative: dict[str, list[str]] = {}
        prefix = PurePosixPath(manifest_name).parent
        for name in archive.namelist():
            pure = PurePosixPath(name)
            try:
                relative = pure.relative_to(prefix).as_posix()
            except ValueError:
                continue
            archive_by_relative.setdefault(relative, []).append(name)
        verified = 0
        for row in rows:
            relative = PurePosixPath(row["相对路径"])
            if relative.is_absolute() or ".." in relative.parts:
                raise BuildError("unsafe source manifest relative path")
            matches = archive_by_relative.get(relative.as_posix(), [])
            if len(matches) != 1:
                raise BuildError(f"source manifest member count drift: {relative.name}")
            payload = archive.read(matches[0])
            if len(payload) != int(row["字节数"]) or _sha256(payload) != row["SHA256"]:
                raise BuildError(f"source manifest integrity drift: {relative.name}")
            verified += 1
        roadmap_name = _find_member(archive, SOURCE_ROADMAP_BASENAME)
        roadmap_payload = archive.read(roadmap_name)
        if _sha256(roadmap_payload) != SOURCE_ROADMAP_SHA256:
            raise BuildError("source roadmap member SHA-256 drift")
        source_roadmap = json.loads(roadmap_payload.decode("utf-8-sig"))
    tracked_path = root / "taskpack/v1_5/roadmap_v2_0.json"
    tracked_payload = _read_regular_bytes_no_follow(tracked_path, label="tracked roadmap")
    if _sha256(tracked_payload) != TRACKED_ROADMAP_SHA256:
        raise BuildError("tracked roadmap SHA-256 drift")
    tracked_roadmap = json.loads(tracked_payload.decode("utf-8"))
    if tuple(source_roadmap.get(key) for key in ("stage_count", "phase_count", "task_count")) != (24, 72, 216):
        raise BuildError("source roadmap count drift")
    source_phase = _source_s03_p1(source_roadmap)
    tracked_phase = _source_s03_p1(tracked_roadmap)
    if source_phase != tracked_phase:
        raise BuildError("source/tracked S03-P1 semantic drift")
    source_tasks = source_phase.get("tasks")
    expected_tasks = [
        {
            "id": task["task_id"][-3:],
            **{key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")},
        }
        for task in TASKS
    ]
    if source_tasks != expected_tasks:
        raise BuildError("S03-P1 exact Task contract drift")
    return {
        "package_file": SOURCE_PACKAGE_NAME,
        "package_sha256": SOURCE_PACKAGE_SHA256,
        "manifest_member": SOURCE_MANIFEST_BASENAME,
        "manifest_sha256": SOURCE_MANIFEST_SHA256,
        "verified_member_count": verified,
        "roadmap_member": SOURCE_ROADMAP_BASENAME,
        "roadmap_member_sha256": SOURCE_ROADMAP_SHA256,
        "tracked_roadmap_sha256": TRACKED_ROADMAP_SHA256,
        "stage_count": 24, "phase_count": 72, "task_count": 216,
        "s03_p1_semantic_equal": True,
        "s03_p1_task_count": 3,
    }


def _validate_private_evidence(root: Path) -> dict[str, Any]:
    policy_path = root / PRIVATE_POLICY_RELATIVE
    receipt_path = root / PRIVATE_RECEIPT_RELATIVE
    projection_path = root / PRIVATE_PROJECTION_RELATIVE
    failure_sentinel_path = root / PRIVATE_FAILURE_SENTINEL_RELATIVE
    if os.path.lexists(failure_sentinel_path):
        raise BuildError("live guard failure sentinel is present")
    private_stats: dict[Path, os.stat_result] = {}
    for path, expected_mode in (
        (policy_path, 0o600),
        (receipt_path, 0o600),
        (projection_path, 0o644),
    ):
        value = os.lstat(path)
        if (
            not stat.S_ISREG(value.st_mode)
            or int(value.st_nlink) != 1
            or stat.S_IMODE(value.st_mode) != expected_mode
        ):
            raise BuildError(f"private evidence type/link/mode unsafe: {path.name}")
        private_stats[path] = value
    policy = guard.load_policy(policy_path)
    receipt = _read_json(receipt_path)
    projection = _read_json(projection_path)
    if receipt.get("schema_version") != guard.PRIVATE_RECEIPT_SCHEMA_VERSION:
        raise BuildError("private guard receipt schema drift")
    if projection.get("schema_version") != guard.PUBLIC_RECEIPT_SCHEMA_VERSION:
        raise BuildError("private public-projection schema drift")
    for value in (receipt, projection):
        if (
            value.get("project_id") != "KMFA"
            or value.get("stage_id") != "S03"
            or value.get("phase_id") != "S03-P1"
        ):
            raise BuildError("private guard identity drift")
        if value.get("root_id") != ROOT_ID:
            raise BuildError("private guard root_id drift")
    if tuple(policy.allowed_operations) != EXPECTED_ALLOWED_OPERATIONS:
        raise BuildError("private policy allowed operations drift")
    if policy.source_scope_id != EXPECTED_SOURCE_SCOPE_ID:
        raise BuildError("private policy source scope drift")
    if policy.max_depth != EXPECTED_MAX_DEPTH:
        raise BuildError("private policy max depth drift")
    if tuple(sorted(policy.allowed_extensions)) != tuple(sorted(EXPECTED_ALLOWED_EXTENSIONS)):
        raise BuildError("private policy extension allowlist drift")
    expected_projection = guard.public_projection_from_private_receipt(receipt)
    if projection != expected_projection:
        raise BuildError("private/public guard projection drift")
    comparisons = projection.get("comparisons", {})
    for key in ("setup_pre_equal", "pre_post_equal"):
        if comparisons.get(key) is not True:
            raise BuildError(f"guard projection {key} must be true")
    monitor = projection.get("monitor", {})
    guard_result = projection.get("guard", {})
    privacy = receipt.get("privacy", {})
    if projection.get("status") != "PASS":
        raise BuildError("live guard did not PASS")
    if monitor.get("status") != "PASS":
        raise BuildError("live event monitor did not PASS")
    if monitor.get("backend") != guard.DarwinKqueueVnodeMonitor.name:
        raise BuildError("live event monitor backend drift")
    if monitor.get("production_backend_attested") is not True:
        raise BuildError("live production event monitor is not attested")
    if float(monitor.get("controlled_window_seconds", -1)) != guard.CONTROLLED_WINDOW_SECONDS:
        raise BuildError("live controlled monitor window drift")
    if float(monitor.get("final_drain_seconds", -1)) != guard.FINAL_DRAIN_SECONDS:
        raise BuildError("live final monitor drain drift")
    if monitor.get("mutation_event_detected") is not False:
        raise BuildError("live event monitor detected a mutation event")
    if guard_result.get("prohibited_raw_mutation_detected") is not False:
        raise BuildError("live guard detected a prohibited raw mutation")
    if guard_result.get("os_atime_side_effect_possible") is not True:
        raise BuildError("live guard omitted OS-managed atime possibility")
    if not isinstance(guard_result.get("os_atime_side_effect_observed"), bool):
        raise BuildError("live guard atime observation must be boolean")
    if guard_result.get("absolute_zero_metadata_mutation_claimed") is not False:
        raise BuildError("live guard overclaimed absolute zero metadata mutation")
    if guard_result.get("os_atime_restoration_performed") is not False:
        raise BuildError("live guard must not restore atime")
    if guard_result.get("production_raw_mutation_api_present") is not False:
        raise BuildError("live guard exposes a production raw mutation API")
    if privacy.get("root_path_plaintext_in_receipt") is not False:
        raise BuildError("private receipt persisted plaintext path")
    raw_identities = {
        (int(row["device"]), int(row["inode"]))
        for row in receipt["snapshots"]["setup"]["entries"]
    }
    for path, value in private_stats.items():
        if (int(value.st_dev), int(value.st_ino)) in raw_identities:
            raise BuildError(f"private evidence aliases protected raw identity: {path.name}")
    return {
        "policy": policy,
        "receipt": receipt,
        "projection": projection,
        "policy_ref": f"KMFA/{PRIVATE_POLICY_RELATIVE.as_posix()}",
        "receipt_ref": f"KMFA/{PRIVATE_RECEIPT_RELATIVE.as_posix()}",
        "projection_ref": f"KMFA/{PRIVATE_PROJECTION_RELATIVE.as_posix()}",
    }


def _normalize_validation_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    project_root: Optional[Path] = None,
) -> list[dict[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        validation_id = str(row.get("validation_id", ""))
        if not validation_id or validation_id in by_id:
            raise BuildError("duplicate or empty validation_id")
        by_id[validation_id] = row
    if set(by_id) != set(EXPECTED_VALIDATION_RECEIPTS):
        raise BuildError("validation receipt ID set drift")
    expected_subject: Optional[str] = None
    expected_run_id: Optional[str] = None
    expected_head: Optional[str] = None
    normalized: list[dict[str, Any]] = []
    for sequence, (validation_id, command) in enumerate(
        EXPECTED_VALIDATION_RECEIPTS.items(),
        start=1,
    ):
        row = by_id[validation_id]
        if row.get("command") != command:
            raise BuildError(f"validation command drift: {validation_id}")
        result = row.get("result")
        exit_code = row.get("exit_code")
        if not (
            (result == "PENDING" and exit_code is None)
            or (result == "PASS" and exit_code == 0)
            or (
                result == "FAIL"
                and isinstance(exit_code, int)
                and not isinstance(exit_code, bool)
                and exit_code != 0
            )
        ):
            raise BuildError(f"invalid validation result: {validation_id}")
        normalized_row = {
            "validation_id": validation_id,
            "command": command,
            "result": result,
            "exit_code": exit_code,
        }
        if result != "PENDING":
            if row.get("schema_version") != VALIDATION_RECEIPT_SCHEMA_VERSION:
                raise BuildError(f"validation receipt schema drift: {validation_id}")
            run_id = row.get("run_id")
            if not isinstance(run_id, str) or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
                raise BuildError(f"validation run_id invalid: {validation_id}")
            if expected_run_id is None:
                expected_run_id = run_id
            if run_id != expected_run_id:
                raise BuildError(f"validation run_id drift: {validation_id}")
            if row.get("execution_sequence") != sequence:
                raise BuildError(f"validation execution sequence drift: {validation_id}")
            if row.get("phase_base_commit") != PHASE_BASE_COMMIT:
                raise BuildError(f"validation phase base drift: {validation_id}")
            if expected_subject is None:
                expected_subject = validation_subject_sha256(project_root)
            if row.get("validation_subject_sha256") != expected_subject:
                raise BuildError(f"validation subject drift: {validation_id}")
            for key in ("head_before", "head_after"):
                if not isinstance(row.get(key), str) or re.fullmatch(r"[0-9a-f]{40}", row[key]) is None:
                    raise BuildError(f"validation {key} invalid: {validation_id}")
            if row["head_before"] != row["head_after"]:
                raise BuildError(f"validation HEAD changed during run: {validation_id}")
            if expected_head is None:
                expected_head = row["head_before"]
            if row["head_before"] != expected_head:
                raise BuildError(f"validation HEAD differs across receipts: {validation_id}")
            parsed_times = []
            for key in ("started_at", "ended_at"):
                try:
                    parsed = datetime.fromisoformat(str(row.get(key, "")).replace("Z", "+00:00"))
                except ValueError as error:
                    raise BuildError(f"validation {key} invalid: {validation_id}") from error
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise BuildError(f"validation {key} timezone missing: {validation_id}")
                parsed_times.append(parsed)
            if parsed_times[1] < parsed_times[0]:
                raise BuildError(f"validation time order invalid: {validation_id}")
            duration = row.get("duration_ms")
            if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
                raise BuildError(f"validation duration invalid: {validation_id}")
            for key in ("stdout_sha256", "stderr_sha256"):
                if not isinstance(row.get(key), str) or re.fullmatch(r"sha256:[0-9a-f]{64}", row[key]) is None:
                    raise BuildError(f"validation {key} invalid: {validation_id}")
            normalized_row.update({
                "schema_version": row["schema_version"],
                "run_id": expected_run_id,
                "execution_sequence": sequence,
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "duration_ms": duration,
                "phase_base_commit": PHASE_BASE_COMMIT,
                "head_before": row["head_before"],
                "head_after": row["head_after"],
                "validation_subject_sha256": expected_subject,
                "stdout_sha256": row["stdout_sha256"],
                "stderr_sha256": row["stderr_sha256"],
            })
        normalized.append(normalized_row)
    return normalized


def _validation_rows(
    output_root: Path,
    input_path: Optional[Path],
    *,
    project_root: Optional[Path] = None,
    reuse_public_results: bool = False,
) -> list[dict[str, Any]]:
    if input_path is not None:
        value = os.lstat(input_path)
        if (
            not stat.S_ISREG(value.st_mode)
            or int(value.st_nlink) != 1
            or stat.S_IMODE(value.st_mode) != 0o600
        ):
            raise BuildError("private validation receipt type/link/mode is unsafe")
        return _normalize_validation_rows(
            _read_jsonl(Path(input_path)),
            project_root=project_root,
        )
    existing = output_root / VALIDATION_RESULTS_RELATIVE
    if reuse_public_results and existing.is_file():
        return _normalize_validation_rows(
            _read_jsonl(existing),
            project_root=project_root,
        )
    return [
        {"validation_id": validation_id, "command": command, "result": "PENDING", "exit_code": None}
        for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()
    ]


def _validation_accounting(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("result")) for row in rows)
    all_pass = len(rows) == len(EXPECTED_VALIDATION_RECEIPTS) and counts == Counter({"PASS": len(rows)})
    return {
        "expected": len(EXPECTED_VALIDATION_RECEIPTS),
        "recorded": len(rows),
        "passed": counts["PASS"],
        "pending": counts["PENDING"],
        "failed": counts["FAIL"],
        "all_exact_pass": all_pass,
    }


def _public_registry(private: Mapping[str, Any]) -> dict[str, Any]:
    policy = private["policy"]
    guard_result = private["projection"]["guard"]
    return {
        "schema_version": "kmfa.metadata.v015.s03_p1.read_only_root_registry.public_safe.v2",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P1",
        "root_id": ROOT_ID,
        "path_binding": {
            "visibility": "PRIVATE_ONLY", "exact_path_registered": True,
            "public_path_value": None, "private_registry_ref": private["policy_ref"],
        },
        "permission_observation": {
            "readable": guard_result.get("root_readable") is True,
            "permission_known": guard_result.get("root_permission_known") is True,
            "owner_write_bit_observed": guard_result.get("root_owner_write_bit") is True,
            "os_level_immutable_claimed": False,
            "guard_kind": "APPLICATION_FAIL_CLOSED_RECURSIVE_KQUEUE_GUARD",
        },
        "allowed_operations": list(EXPECTED_ALLOWED_OPERATIONS),
        "forbidden_operations": [
            "create", "write", "modify", "delete", "move", "rename", "overwrite",
            "copy", "extract", "convert", "chmod", "chown", "xattr",
        ],
        "allowed_operations_performed": list(EXPECTED_ALLOWED_OPERATIONS),
        "forbidden_operations_performed": [],
        "raw_bytes_streamed_for_hash": True,
        "raw_business_content_interpreted": False,
        "raw_business_values_extracted": False,
        "prohibited_raw_mutation_detected": guard_result.get("prohibited_raw_mutation_detected"),
        "prohibited_mutation_scope": list(EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "os_atime_side_effect_possible": guard_result.get("os_atime_side_effect_possible"),
        "os_atime_side_effect_observed": guard_result.get("os_atime_side_effect_observed"),
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
        "absolute_zero_metadata_mutation_claimed": guard_result.get("absolute_zero_metadata_mutation_claimed"),
        "os_atime_restoration_performed": guard_result.get("os_atime_restoration_performed"),
        "production_raw_mutation_api_present": guard_result.get("production_raw_mutation_api_present"),
        "private_evidence_required_for_local_revalidation": True,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _public_allowlist(private: Mapping[str, Any]) -> dict[str, Any]:
    policy = private["policy"]
    return {
        "schema_version": "kmfa.metadata.v015.s03_p1.read_allowlist.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P1",
        "authorization_model": "DEFAULT_DENY_EXACT_ROOT_AND_FILE_TYPE",
        "source_rules": [{
            "source_scope_id": policy.source_scope_id,
            "root_id": ROOT_ID,
            "root_count": 1,
            "path_binding": "PRIVATE_EXACT_PATH",
            "recursive_scope": True,
            "max_depth": policy.max_depth,
            "allowed_file_extensions": sorted(policy.allowed_extensions),
            "allowed_operations": list(EXPECTED_ALLOWED_OPERATIONS),
            "allowed_read_purposes": ["RECURSIVE_FINGERPRINT_SHA256_ONLY"],
            "follow_symlinks": False,
            "special_files_allowed": False,
            "raw_parse_allowed": False,
            "raw_value_extract_allowed": False,
            "copy_allowed": False,
        }],
        "deny_rules": {
            "outside_registered_root": "DENY",
            "unregistered_source_scope": "DENY",
            "unregistered_file_type": "DENY",
            "depth_exceeded": "DENY",
            "symlink_or_special_file": "DENY",
            "operation_not_explicitly_allowed": "DENY",
        },
        "full_disk_scan_allowed": False,
        "arbitrary_root_cli_override_allowed": False,
        "s03_p2_copy_started": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _task_matrix(source: Mapping[str, Any], private: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    guard_pass = private["projection"].get("status") == "PASS"
    final_pass = guard_pass and validation["all_exact_pass"]
    rows = []
    for task in TASKS:
        source_contract = {key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")}
        rows.append({
            "task_id": task["task_id"],
            "source_contract": source_contract,
            "source_contract_sha256": _sha256(json.dumps(source_contract, ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED" if final_pass else "PENDING",
            "current_result": "TASK_ACCEPTED" if final_pass else "VALIDATION_PENDING",
            "evidence_refs": {
                "S03P1T01": [ARTIFACT_REFS["public_registry"], ARTIFACT_REFS["task_matrix"]],
                "S03P1T02": [ARTIFACT_REFS["write_guard"], ARTIFACT_REFS["validation_results"]],
                "S03P1T03": [ARTIFACT_REFS["public_allowlist"], ARTIFACT_REFS["validation_results"]],
            }[task["task_id"]],
        })
    return {
        "schema_version": "kmfa.v015.s03_p1.task_acceptance_matrix.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S03", "phase_id": "S03-P1",
        "source_package": dict(source),
        "tasks": rows,
        "task_accounting": {"total": 3, "execution_complete": 3, "accepted": 3 if final_pass else 0},
        "phase_acceptance_status": "PASSED" if final_pass else "PENDING",
        "decision": "CONTINUE_TO_S03_P2_ONLY" if final_pass else "REMAIN_IN_S03_P1",
        "public_safe_status": "PUBLIC_SAFE",
    }


def _write_guard_public(private: Mapping[str, Any]) -> dict[str, Any]:
    projection = private["projection"]
    snapshots = projection["snapshots"]
    comparisons = projection["comparisons"]
    monitor = projection["monitor"]
    guard_result = projection["guard"]
    return {
        "schema_version": "kmfa.v015.s03_p1.write_protection_validation.public_safe.v2",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P1", "root_id": ROOT_ID,
        "guard_kind": "APPLICATION_FAIL_CLOSED_RECURSIVE_KQUEUE_GUARD",
        "os_level_immutable_claimed": False,
        "setup_snapshot_status": snapshots.get("setup"),
        "pre_snapshot_status": snapshots.get("pre"),
        "post_snapshot_status": snapshots.get("post"),
        "setup_pre_equal": comparisons.get("setup_pre_equal"),
        "pre_post_equal": comparisons.get("pre_post_equal"),
        "event_monitor_backend": monitor.get("backend"),
        "event_monitor_status": monitor.get("status"),
        "event_monitor_production_attested": monitor.get("production_backend_attested"),
        "controlled_window_seconds": monitor.get("controlled_window_seconds"),
        "final_drain_seconds": monitor.get("final_drain_seconds"),
        "prohibited_raw_mutation_detected": guard_result.get("prohibited_raw_mutation_detected"),
        "prohibited_mutation_scope": list(EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "os_atime_side_effect_possible": guard_result.get("os_atime_side_effect_possible"),
        "os_atime_side_effect_observed": guard_result.get("os_atime_side_effect_observed"),
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
        "absolute_zero_metadata_mutation_claimed": guard_result.get("absolute_zero_metadata_mutation_claimed"),
        "os_atime_restoration_performed": guard_result.get("os_atime_restoration_performed"),
        "production_raw_mutation_api_present": guard_result.get("production_raw_mutation_api_present"),
        "mutation_class_contract": list(EXPECTED_MUTATION_CLASSES),
        "mutation_class_count": 4,
        "guard_status": projection.get("status"),
        "guard_error_codes": projection.get("failure_codes", []),
        "private_fingerprint_or_path_published": False,
        "private_event_detail_published": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _slot_rows() -> list[dict[str, Any]]:
    refs = {
        "manifest.json": [ARTIFACT_REFS["manifest"]],
        "commands.txt": [ARTIFACT_REFS["receipt_template"]],
        "test_results.json": [ARTIFACT_REFS["validation_results"], ARTIFACT_REFS["test_results"]],
        "human_summary.md": [ARTIFACT_REFS["completion"]],
        "changed_files.txt": [ARTIFACT_REFS["manifest"]],
        "screenshots/": [],
        "logs/": [ARTIFACT_REFS["write_guard"]],
        "exports/": [],
        "rollback.md": [ARTIFACT_REFS["rollback"]],
        "open_risks.md": [ARTIFACT_REFS["open_risks"]],
    }
    na = {
        "screenshots/": "本 Phase 无 UI；截图不能证明 raw 写保护。",
        "exports/": "本 Phase 禁止 raw copy/export；S03-P2 尚未启动。",
    }
    rows: list[dict[str, Any]] = []
    for task in TASKS:
        for slot in EVIDENCE_SLOTS:
            rows.append({
                "task_id": task["task_id"], "slot": slot,
                "status": "N/A_WITH_RATIONALE" if slot in na else "COVERED",
                "evidence_refs": refs[slot], "not_applicable_reason": na.get(slot, ""),
                "private_detail_published": False,
            })
    return rows


def _completion_markdown(matrix: Mapping[str, Any], validation: Mapping[str, Any], private: Mapping[str, Any]) -> bytes:
    atime_observed = private["projection"]["guard"].get("os_atime_side_effect_observed")
    return (
        "# KMFA v1.5 S03-P1 只读根目录治理完成记录\n\n"
        f"- Phase acceptance：`{matrix['phase_acceptance_status']}`。\n"
        f"- decision：`{matrix['decision']}`。\n"
        f"- Task：`{matrix['task_accounting']['accepted']}/3` accepted。\n"
        f"- validation receipts：`{validation['passed']}/{validation['expected']}` exact PASS。\n"
        "- live guard：递归 setup/pre/post 指纹一致，Darwin kqueue 观察窗口无 vnode mutation event。\n"
        "- raw 操作：仅 list/stat/read-for-hash/hash；未复制、解析或抽取业务值，未检测到 content/namespace/permission/owner/xattr/flags/size/mtime/ctime/inode 等禁止的应用级变更。\n"
        f"- atime 事实：OS-managed atime side effect possible=`true`，final v2 replay 聚合 observed=`{str(atime_observed).lower()}`；pre-v2 两次授权读取缺少 baseline，historical effect=`UNKNOWN`；absolute-zero metadata mutation claim=`false`，未执行 utime 恢复。\n"
        "- 真实性边界：这是应用级 fail-closed guard，不声称 raw 目录具备 OS immutable 属性、绝对零 metadata mutation 或 24x7 守护。\n"
        "- public/private：exact path、逐项路径 token、content hash 和事件细节只在 ignored private runtime。\n"
        "- Stage：S03 仅为 `IN_PROGRESS / PENDING / 33%`；S03-P2 尚未启动。\n"
    ).encode("utf-8")


def _test_markdown(validation: Mapping[str, Any]) -> bytes:
    lines = [
        "# KMFA v1.5 S03-P1 测试结果", "",
        f"- exact receipts：{validation['passed']}/{validation['expected']} PASS。",
        f"- pending={validation['pending']}；failed={validation['failed']}。", "",
    ]
    for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items():
        lines.append(f"- `{validation_id}`：`{command}`")
    lines.extend(["", "真实 raw 目录未执行任何应用级写入探针；新增/删除/修改/重命名拒绝测试全部使用 synthetic tempfile。授权 list/read/hash 可能触发 OS-managed atime，guard 只观察且绝不以 utime 恢复。", ""])
    return "\n".join(lines).encode("utf-8")


def _rollback_markdown() -> bytes:
    return (
        "# KMFA v1.5 S03-P1 回滚计划\n\n"
        f"- tracked 回滚基线：`{PHASE_BASE_COMMIT}`。\n"
        "- 只回滚本 Phase 新增 guard、checker、tests、public-safe evidence 与治理镜像。\n"
        "- private receipt 只可在确认不再需要本地复验后按后续 S03-P2-T03 生命周期规则处理；本 Run 不清理。\n"
        "- 未检测到禁止的应用级 raw 变更，因此 raw content/namespace rollback 为 N/A；OS-managed atime 不回写、不以 utime 恢复。严禁以回滚名义删除、移动、覆盖或恢复 raw。\n"
        "- 回滚后 gate 恢复 `GO_TO_S03_P1_ONLY`，不得直接进入 S03-P2。\n"
    ).encode("utf-8")


def _risks_markdown(private: Mapping[str, Any]) -> bytes:
    owner_write = private["receipt"]["guard"].get("root_owner_write_bit") is True
    return (
        "# KMFA v1.5 S03-P1 开放风险\n\n"
        "- `S03P1-RISK-001 / P1 / CONTROLLED_NONBLOCKING`：kqueue 仅覆盖受控运行窗口，不是 24x7 守护；持续可观测性路由 `S22P3T01`。\n"
        f"- `S03P1-RISK-002 / P2 / CONTROLLED_NONBLOCKING`：owner write bit observed=`{str(owner_write).lower()}`；本 Phase 禁止 chmod/ACL 变更，以递归 guard 检测并 fail-closed；稳定运行复验路由 `S24P2T02`。\n"
        "- `S03P1-RISK-003 / P2 / CONTROLLED_NONBLOCKING`：private fingerprint/event evidence 的保留与安全清理策略尚未执行；路由 `S03P2T03`。\n"
        "- `S03P1-RISK-004 / P1 / CONTROLLED_NONBLOCKING`：macOS/APFS 的授权 list/read/hash 可能更新 root/file atime；pre-v2 两次读取没有 atime baseline，历史 effect 保持 UNKNOWN，final v2 replay 仅代表该次聚合观测；拒绝 absolute-zero metadata mutation 声明且不做 utime 恢复；clone/content-addressed copy 隔离路由 `S03P2T02`。\n"
        "- blocking risk：0；以上风险均有明确 control、follow-up Task 和 stop condition。\n"
    ).encode("utf-8")


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        for token in _FORBIDDEN_PUBLIC_TOKENS:
            if token in payload:
                raise BuildError(f"public-safe token violation in {path}: {token!r}")
        if _EMAIL_RE.search(payload):
            raise BuildError(f"email leaked into public output: {path}")
        if _SECRET_RE.search(payload):
            raise BuildError(f"secret-like assignment in public output: {path}")


def expected_outputs(
    *, project_root: Optional[Path] = None, source_package: Path = DEFAULT_SOURCE_PACKAGE,
    generated_at: str, validation_results_input: Optional[Path] = None,
    reuse_public_validation_results: bool = False,
) -> dict[Path, bytes]:
    try:
        parsed = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError("generated_at must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BuildError("generated_at must include timezone offset")
    root = _normalize_project_root(project_root)
    output_root = root / OUTPUT_ROOT_RELATIVE
    source = verify_source_package(source_package, root)
    private = _validate_private_evidence(root)
    validation_rows = _validation_rows(
        output_root,
        validation_results_input,
        project_root=root,
        reuse_public_results=reuse_public_validation_results,
    )
    if validation_results_input is not None and all(
        row.get("result") == "PASS" for row in validation_rows
    ):
        ended = [
            datetime.fromisoformat(str(row["ended_at"]).replace("Z", "+00:00"))
            for row in validation_rows
        ]
        newest_end = max(ended)
        freshness_seconds = (parsed - newest_end).total_seconds()
        if freshness_seconds < 0 or freshness_seconds > 2 * 60 * 60:
            raise BuildError("private validation receipts are not fresh for this write")
        now = datetime.now().astimezone()
        receipt_age_seconds = (now - newest_end).total_seconds()
        generated_age_seconds = (now - parsed).total_seconds()
        if not (-5 * 60 <= receipt_age_seconds <= 2 * 60 * 60):
            raise BuildError("private validation receipts are stale against the current clock")
        if not (-5 * 60 <= generated_age_seconds <= 2 * 60 * 60):
            raise BuildError("generated_at is stale against the current clock")
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        resolved_head = current_head.stdout.strip()
        if (
            current_head.returncode != 0
            or re.fullmatch(r"[0-9a-f]{40}", resolved_head) is None
            or any(row.get("head_before") != resolved_head for row in validation_rows)
        ):
            raise BuildError("private validation receipt HEAD is not the current HEAD")
    validation = _validation_accounting(validation_rows)
    registry = _public_registry(private)
    allowlist = _public_allowlist(private)
    matrix = _task_matrix(source, private, validation)
    write_guard = _write_guard_public(private)
    slot_rows = _slot_rows()
    template_rows = [
        {"validation_id": validation_id, "command": command, "expected_result": "PASS", "expected_exit_code": 0, "blocking": True}
        for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()
    ]
    outputs: dict[Path, bytes] = {
        root / PUBLIC_REGISTRY_RELATIVE: _json_bytes(registry),
        root / PUBLIC_ALLOWLIST_RELATIVE: _json_bytes(allowlist),
        output_root / TASK_MATRIX_RELATIVE: _json_bytes(matrix),
        output_root / WRITE_GUARD_RELATIVE: _json_bytes(write_guard),
        output_root / READ_SCOPE_RELATIVE: _json_bytes(allowlist),
        output_root / EVIDENCE_SLOTS_RELATIVE: _jsonl_bytes(slot_rows),
        output_root / RECEIPT_TEMPLATE_RELATIVE: _jsonl_bytes(template_rows),
        output_root / VALIDATION_RESULTS_RELATIVE: _jsonl_bytes(validation_rows),
        output_root / COMPLETION_RELATIVE: _completion_markdown(matrix, validation, private),
        output_root / TEST_RESULTS_RELATIVE: _test_markdown(validation),
        output_root / ROLLBACK_RELATIVE: _rollback_markdown(),
        output_root / OPEN_RISKS_RELATIVE: _risks_markdown(private),
    }
    final_pass = matrix["phase_acceptance_status"] == "PASSED"
    manifest = {
        "schema_version": "kmfa.v015.s03_p1.read_only_root_governance.v2",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S03", "phase_id": "S03-P1",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at, "run_mode": "IMPLEMENT", "work_kind": "READ_ONLY_ROOT_GOVERNANCE",
        "phase_base_commit": PHASE_BASE_COMMIT,
        "source_package": source,
        "task_accounting": matrix["task_accounting"],
        "execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS" if final_pass else "PENDING",
        "acceptance_status": "PASSED" if final_pass else "PENDING",
        "decision": "CONTINUE_TO_S03_P2_ONLY" if final_pass else "REMAIN_IN_S03_P1",
        "stage_status": {"lifecycle": "IN_PROGRESS", "acceptance": "PENDING", "execution_percentage": 33},
        "raw_access": {
            "allowed_operations_performed": list(EXPECTED_ALLOWED_OPERATIONS),
            "forbidden_operations_performed": [],
            "raw_bytes_streamed_for_hash": True,
            "raw_business_content_interpreted": False,
            "raw_business_values_extracted": False,
            "raw_copy_performed": False,
            "prohibited_raw_mutation_detected": write_guard["prohibited_raw_mutation_detected"],
            "prohibited_mutation_scope": list(EXPECTED_PROHIBITED_MUTATION_SCOPE),
            "os_atime_side_effect_possible": write_guard["os_atime_side_effect_possible"],
            "os_atime_side_effect_observed": write_guard["os_atime_side_effect_observed"],
            "historical_pre_v2_atime_effect_unknown": True,
            "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
            "absolute_zero_metadata_mutation_claimed": write_guard["absolute_zero_metadata_mutation_claimed"],
            "os_atime_restoration_performed": write_guard["os_atime_restoration_performed"],
            "production_raw_mutation_api_present": write_guard["production_raw_mutation_api_present"],
        },
        "guard_result": {
            "guard_status": write_guard["guard_status"],
            "setup_pre_equal": write_guard["setup_pre_equal"],
            "pre_post_equal": write_guard["pre_post_equal"],
            "event_monitor_status": write_guard["event_monitor_status"],
            "event_monitor_production_attested": write_guard["event_monitor_production_attested"],
            "controlled_window_seconds": write_guard["controlled_window_seconds"],
            "final_drain_seconds": write_guard["final_drain_seconds"],
            "os_level_immutable_claimed": False,
            "prohibited_raw_mutation_detected": write_guard["prohibited_raw_mutation_detected"],
            "os_atime_side_effect_possible": write_guard["os_atime_side_effect_possible"],
            "os_atime_side_effect_observed": write_guard["os_atime_side_effect_observed"],
            "historical_pre_v2_atime_effect_unknown": True,
            "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
            "absolute_zero_metadata_mutation_claimed": write_guard["absolute_zero_metadata_mutation_claimed"],
            "os_atime_restoration_performed": write_guard["os_atime_restoration_performed"],
            "production_raw_mutation_api_present": write_guard["production_raw_mutation_api_present"],
        },
        "private_evidence": {
            "required": True,
            "exact_path_public": False,
            "raw_path_or_hash_public": False,
            "policy_ref": private["policy_ref"],
            "guard_receipt_ref": private["receipt_ref"],
            "guard_projection_ref": private["projection_ref"],
        },
        "evidence_slot_accounting": {"task_count": 3, "slots_per_task": 10, "total": 30, "covered": 24, "n_a_with_rationale": 6},
        "validation_receipt_accounting": validation,
        "open_risk_accounting": {"total": 4, "blocking": 0, "p0": 0, "p1": 2, "p2": 2, "plan_gap_count": 0},
        "next_entry_gate": {
            "next_allowed_run": "S03-P2" if final_pass else "S03-P1",
            "s03_p2_entry_allowed": final_pass,
            "s03_p2_started": False,
            "s03_p3_entry_allowed": False,
            "stage3_review_entry_allowed": False,
            "product_implementation_allowed": False,
        },
        "downstream_actions": {
            "s03_p2_started": False, "s03_p3_started": False, "stage3_review_performed": False,
            "product_runtime_implementation_performed": False, "github_upload_performed": False,
            "app_reinstall_performed": False, "raw_copy_performed": False,
            "business_execution_performed": False, "formal_report_generated": False,
        },
        "artifact_refs": dict(ARTIFACT_REFS),
        "artifact_integrity": [
            {"ref": path.relative_to(REPO_ROOT).as_posix(), "bytes": len(payload), "sha256": _sha256(payload)}
            for path, payload in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        ],
    }
    manifest["content_hash"] = _content_hash(manifest)
    outputs[output_root / MANIFEST_RELATIVE] = _json_bytes(manifest)
    _assert_public_safe(outputs)
    return outputs


def _open_directory_tree_no_follow(path: Path, *, create: bool) -> int:
    absolute = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open("/", flags)
    try:
        for component in absolute.parts[1:]:
            try:
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o755, dir_fd=descriptor)
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _write_payload_no_follow(
    path: Path,
    payload: bytes,
    *,
    forbidden_identities: frozenset[tuple[int, int]],
) -> None:
    absolute = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    project_absolute = Path(os.path.abspath(os.path.normpath(os.fspath(PROJECT_ROOT))))
    try:
        inside_project = os.path.commonpath((str(project_absolute), str(absolute))) == str(project_absolute)
    except ValueError:
        inside_project = False
    if not inside_project or absolute == project_absolute:
        raise BuildError("builder output escaped the KMFA project root")
    parent_fd = _open_directory_tree_no_follow(absolute.parent, create=True)
    descriptor: Optional[int] = None
    try:
        common_flags = os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(absolute.name, common_flags, dir_fd=parent_fd)
        except FileNotFoundError:
            descriptor = os.open(
                absolute.name,
                common_flags | os.O_CREAT | os.O_EXCL,
                0o644,
                dir_fd=parent_fd,
            )
        opened = os.fstat(descriptor)
        identity = (int(opened.st_dev), int(opened.st_ino))
        if not stat.S_ISREG(opened.st_mode):
            raise BuildError(f"builder output is not a regular file: {absolute}")
        if int(opened.st_nlink) != 1:
            raise BuildError(f"builder output link count is unsafe: {absolute}")
        if identity in forbidden_identities:
            raise BuildError(f"builder output aliases protected raw identity: {absolute}")
        os.fchmod(descriptor, 0o644)
        before_truncate = os.fstat(descriptor)
        if (
            (int(before_truncate.st_dev), int(before_truncate.st_ino)) != identity
            or int(before_truncate.st_nlink) != 1
        ):
            raise BuildError(f"builder output identity changed before write: {absolute}")
        os.ftruncate(descriptor, 0)
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
        after_write = os.fstat(descriptor)
        if (
            (int(after_write.st_dev), int(after_write.st_ino)) != identity
            or int(after_write.st_nlink) != 1
            or stat.S_IMODE(after_write.st_mode) != 0o644
        ):
            raise BuildError(f"builder output identity/mode changed during write: {absolute}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)


def write_outputs(outputs: Mapping[Path, bytes]) -> None:
    expected_paths = {
        PROJECT_ROOT / Path(ref).relative_to("KMFA")
        for ref in ARTIFACT_REFS.values()
    }
    if set(outputs) != expected_paths:
        raise BuildError("builder output path set drift")
    private = _validate_private_evidence(PROJECT_ROOT)
    setup_entries = private["receipt"]["snapshots"]["setup"]["entries"]
    forbidden_identities = frozenset(
        (int(row["device"]), int(row["inode"]))
        for row in setup_entries
    )
    for path, payload in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        _write_payload_no_follow(
            path,
            payload,
            forbidden_identities=forbidden_identities,
        )


def check_outputs(outputs: Mapping[Path, bytes]) -> None:
    errors = []
    for path, expected in outputs.items():
        try:
            actual = _read_regular_bytes_no_follow(path, label="expected output")
        except BuildError as error:
            errors.append(str(error))
            continue
        if actual != expected:
            errors.append(f"output drift: {path}")
    if errors:
        raise BuildError("\n".join(errors))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--validation-results-input", type=Path, default=None)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.source_only:
            source = verify_source_package(args.source_package, args.project_root)
            print(
                "PASS: source package 21/21; "
                f"roadmap={source['stage_count']}/{source['phase_count']}/{source['task_count']}; "
                f"S03-P1 tasks={source['s03_p1_task_count']}; semantic_equal={str(source['s03_p1_semantic_equal']).lower()}"
            )
            return 0
        if args.write == args.check:
            raise BuildError("select exactly one of --write or --check")
        root = _normalize_project_root(args.project_root)
        if args.check and args.validation_results_input is not None:
            raise BuildError("--check must use the committed public validation results")
        if args.write and args.validation_results_input is not None:
            supplied = Path(os.path.abspath(os.path.normpath(os.fspath(args.validation_results_input))))
            fixed = Path(os.path.abspath(os.path.normpath(os.fspath(root / PRIVATE_VALIDATION_RECEIPTS_RELATIVE))))
            if supplied != fixed:
                raise BuildError("--validation-results-input must be the fixed private runner output")
        generated_at = args.generated_at
        if args.check and not generated_at:
            manifest = _read_json(root / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE)
            generated_at = str(manifest.get("generated_at", ""))
        if not generated_at:
            raise BuildError("--generated-at is required for --write")
        outputs = expected_outputs(
            project_root=root, source_package=args.source_package, generated_at=generated_at,
            validation_results_input=args.validation_results_input,
            reuse_public_validation_results=args.check,
        )
        if args.write:
            write_outputs(outputs)
            print(f"PASS: wrote S03-P1 public-safe outputs ({len(outputs)} files)")
        else:
            check_outputs(outputs)
            print(f"PASS: exact S03-P1 outputs match ({len(outputs)} files)")
        return 0
    except (BuildError, guard.GuardError, json.JSONDecodeError, OSError, ValueError) as error:
        print("FAIL: KMFA v1.5 S03-P1 evidence build failed")
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
