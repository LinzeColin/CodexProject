#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S03-P2.

Private source names, hashes, CAS identifiers, and cleanup plan digests remain
inside the ignored evidence root. This builder emits aggregate evidence only.
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
import time
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import ZipFile

from KMFA.tools import v015_s03_p2_private_derived_runtime as runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PHASE_BASE_COMMIT = "75c4aca93395375cf664963dec98272c45d9799c"

SOURCE_PACKAGE_NAME = "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
SOURCE_MANIFEST_BASENAME = "15_MANIFEST_SHA256_v2_0.csv"
SOURCE_MANIFEST_SHA256 = "a4a5cb0e301a841a922e761ff503a2fce72982b1b088d9aeee9e11998939b2a5"
SOURCE_ROADMAP_BASENAME = "02B_KMFA_Codex_Development_Roadmap_v2_0.json"
SOURCE_ROADMAP_SHA256 = "741fdf6a1dd6d04fdaaf916f8cf84ebce07207fbb50d7971736c1c9fc46a5145"
TRACKED_ROADMAP_SHA256 = "a0efdddc6e54a167751938353f71bb60a9cd4b43cbcf444d4c915a45b8b1ec06"
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME

RUN_PHASE_ID = "V015_S03_P2_PRIVATE_DERIVED_RUNTIME"
TASK_ID = "KMFA-V015-S03-P2-PRIVATE-DERIVED-RUNTIME-20260713"
ACCEPTANCE_ID = "ACC-KMFA-V015-S03-P2-PRIVATE-DERIVED-RUNTIME"
PRIVATE_ROOT_RELATIVE = Path(".codex_private_runtime/V015_S03_P2_PRIVATE_DERIVED_RUNTIME")
PRIVATE_RECEIPT_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_runtime_receipt.json"
PRIVATE_PROJECTION_RELATIVE = PRIVATE_ROOT_RELATIVE / "public_runtime_projection.json"
PRIVATE_VALIDATION_RECEIPTS_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_validation_receipts.jsonl"
P1_PRIVATE_POLICY_RELATIVE = Path(
    ".codex_private_runtime/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/private_root_policy.json"
)
P1_PRIVATE_RECEIPT_RELATIVE = Path(
    ".codex_private_runtime/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/private_guard_receipt.json"
)
LOCAL_RUNTIME_RELATIVE = Path("local_runtime")

PRIVATE_RECEIPT_SCHEMA_VERSION = "kmfa.v015.s03_p2.private_runtime_receipt.v1"
PUBLIC_PROJECTION_SCHEMA_VERSION = "kmfa.v015.s03_p2.public_runtime_projection.v1"
VALIDATION_RECEIPT_SCHEMA_VERSION = "kmfa.v015.s03_p2.validation_receipt.v1"

OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S03_P2_PRIVATE_DERIVED_RUNTIME")
MANIFEST_RELATIVE = Path("machine/s03_p2_private_derived_runtime_manifest.json")
TASK_MATRIX_RELATIVE = Path("machine/task_acceptance_matrix_public_safe.json")
RUNTIME_VERIFICATION_RELATIVE = Path("machine/private_runtime_verification_public_safe.json")
CLEANUP_REHEARSAL_RELATIVE = Path("machine/lifecycle_cleanup_rehearsal_public_safe.json")
EVIDENCE_SLOTS_RELATIVE = Path("machine/task_evidence_slot_matrix_public_safe.jsonl")
RECEIPT_TEMPLATE_RELATIVE = Path("machine/validation_receipts_template.jsonl")
VALIDATION_RESULTS_RELATIVE = Path("machine/validation_results.jsonl")
COMPLETION_RELATIVE = Path("human/completion_record_zh.md")
TEST_RESULTS_RELATIVE = Path("human/test_results_zh.md")
ROLLBACK_RELATIVE = Path("human/rollback_plan_zh.md")
OPEN_RISKS_RELATIVE = Path("human/open_risks_zh.md")
DIRECTORY_POLICY_RELATIVE = Path(
    "metadata/protocol/v015_s03_p2_private_runtime_directory_contract_public_safe.json"
)
LIFECYCLE_POLICY_RELATIVE = Path(
    "metadata/protocol/v015_s03_p2_lifecycle_policy_public_safe.json"
)

ARTIFACT_REFS = {
    "manifest": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{MANIFEST_RELATIVE.as_posix()}",
    "task_matrix": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{TASK_MATRIX_RELATIVE.as_posix()}",
    "runtime_verification": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{RUNTIME_VERIFICATION_RELATIVE.as_posix()}",
    "cleanup_rehearsal": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{CLEANUP_REHEARSAL_RELATIVE.as_posix()}",
    "evidence_slots": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{EVIDENCE_SLOTS_RELATIVE.as_posix()}",
    "receipt_template": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{RECEIPT_TEMPLATE_RELATIVE.as_posix()}",
    "validation_results": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{VALIDATION_RESULTS_RELATIVE.as_posix()}",
    "completion": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{COMPLETION_RELATIVE.as_posix()}",
    "test_results": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{TEST_RESULTS_RELATIVE.as_posix()}",
    "rollback": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{ROLLBACK_RELATIVE.as_posix()}",
    "open_risks": f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{OPEN_RISKS_RELATIVE.as_posix()}",
    "directory_policy": f"KMFA/{DIRECTORY_POLICY_RELATIVE.as_posix()}",
    "lifecycle_policy": f"KMFA/{LIFECYCLE_POLICY_RELATIVE.as_posix()}",
}

LAYERS = (
    "content_mirror", "extracted", "staging", "facts", "cache",
    "reports", "logs", "backups", "quarantine",
)
EXPECTED_SOURCE_FILE_COUNT = 5
TASKS = (
    {
        "task_id": "S03P2T01", "name": "建立 local_runtime 分层",
        "action": "划分内容镜像、抽取、暂存、事实、缓存、报告、日志、备份和隔离区。",
        "output": "目录合同。", "acceptance": "目录全部 gitignore，权限最小化。",
        "evidence": "目录树与权限测试。", "stop": "敏感派生数据进入 GitHub 时停止。",
    },
    {
        "task_id": "S03P2T02", "name": "实现只读复制与内容寻址",
        "action": "原始文件仅复制到内容寻址私有区处理。",
        "output": "不可变副本清单。", "acceptance": "副本 hash 与原始一致；重复导入幂等。",
        "evidence": "hash 对比、重复导入测试。", "stop": "hash 不一致时隔离。",
    },
    {
        "task_id": "S03P2T03", "name": "建立清理与保留策略",
        "action": "定义临时文件、缓存、派生版本和报告的保留期与安全清理。",
        "output": "生命周期规则。", "acceptance": "清理不影响原始数据、已发布报告和审计证据。",
        "evidence": "清理演练。", "stop": "无法恢复的清理操作必须二次确认。",
    },
)
EVIDENCE_SLOTS = (
    "manifest.json", "commands.txt", "test_results.json", "human_summary.md",
    "changed_files.txt", "screenshots/", "logs/", "exports/", "rollback.md", "open_risks.md",
)

EXPECTED_VALIDATION_RECEIPTS = {
    "python_compile": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; "
        "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in "
        "('KMFA/tools/v015_s03_p2_private_derived_runtime.py',"
        "'KMFA/tools/build_v015_s03_p2_private_derived_runtime.py',"
        "'KMFA/tools/check_v015_s03_p2_private_derived_runtime.py',"
        "'KMFA/tools/run_v015_s03_p2_validations.py')]\""
    ),
    "source_package_integrity": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_p2_private_derived_runtime.py --source-only"
    ),
    "runtime_focused_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p2_private_derived_runtime"
    ),
    "phase_focused_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p2_private_derived_runtime_governance"
    ),
    "validation_runner_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p2_validation_runner"
    ),
    "builder_exact_rebuild": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_p2_private_derived_runtime.py --check"
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
    "no_float_money": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    "no_omission": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    "git_diff_check": "git diff --check",
    "private_evidence_freshness": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_p2_private_derived_runtime.py "
        "--private-evidence-only --max-private-evidence-age-seconds 7200"
    ),
    "checker_core_private_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_p2_private_derived_runtime.py "
        "--require-private-evidence --require-dependency-validator "
        "--skip-validation-receipts --skip-exact-rebuild --pre-receipt-final-governance"
    ),
}

VALIDATION_MUTABLE_ARTIFACT_KEYS = frozenset({
    "manifest", "task_matrix", "runtime_verification", "cleanup_rehearsal",
    "validation_results", "completion", "test_results", "open_risks",
})
VALIDATION_SUBJECT_REFS = tuple(sorted({
    ref for key, ref in ARTIFACT_REFS.items() if key not in VALIDATION_MUTABLE_ARTIFACT_KEYS
} | {
    "KMFA/.gitignore", "KMFA/AGENTS.md", "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/tools/v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/build_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/check_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/run_v015_s03_p2_validations.py",
    "KMFA/tests/test_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tests/test_v015_s03_p2_private_derived_runtime_governance.py",
    "KMFA/tests/test_v015_s03_p2_validation_runner.py",
    "KMFA/tools/check_no_float_money.py", "KMFA/tools/no_omission_check.py",
    "scripts/lean_governance.py", "scripts/validate_governance_sync.py",
    "scripts/validate_project_governance.py", "scripts/validate_semantic_extractors.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
}))

_FORBIDDEN_PUBLIC_TOKENS = (
    b"/" + b"Users/", b"/" + b"Volumes/", b"/" + b"private/",
    b"/" + b"tmp/", b"/" + b"home/", b"KMFA_" + b"MetaData",
    b'"source_' + b'sha256"', b'"blob_' + b'sha256"', b'"source_' + b'name"',
    b'"raw_' + b'path"', b'"raw_' + b'name"',
    b'"private_' + b'manifest_items"', b'"plan_' + b'sha256"',
)
_EMAIL_RE = re.compile(rb"[A-Za-z0-9.!#$%&'*+/=?^_{}|~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SECRET_RE = re.compile(
    rb"(?i)(?:api[_-]?key|password|secret|(?:access|auth|bearer|refresh|session)[_-]?token)"
    rb"\s*[:=]\s*['\"][^'\"]{8,}"
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class BuildError(RuntimeError):
    """Source, private evidence, or deterministic output contract drift."""


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BuildError(message)


def _normalize_project_root(project_root: Optional[Path]) -> Path:
    root = Path(os.path.abspath(os.path.normpath(os.fspath(project_root or PROJECT_ROOT))))
    _require(root.name == "KMFA" and root.parent.name == "kmfa", "project root identity drift")
    return root


def _read_regular_bytes_no_follow(path: Path, *, label: str) -> bytes:
    before = os.lstat(path)
    _require(stat.S_ISREG(before.st_mode) and int(before.st_nlink) == 1, f"{label} type/link unsafe")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        _require(
            (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
            == (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
            f"{label} identity changed before read",
        )
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        _require(
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            == (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns),
            f"{label} changed during read",
        )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    value = json.loads(_read_regular_bytes_no_follow(path, label=label).decode("utf-8"))
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return dict(value)


def _read_jsonl(path: Path, *, label: str) -> list[dict[str, Any]]:
    rows = []
    for line in _read_regular_bytes_no_follow(path, label=label).decode("utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            _require(isinstance(value, dict), f"{label} has non-object row")
            rows.append(dict(value))
    return rows


def validation_subject_sha256(project_root: Optional[Path] = None) -> str:
    root = _normalize_project_root(project_root)
    digest = hashlib.sha256()
    for ref in VALIDATION_SUBJECT_REFS:
        payload = _read_regular_bytes_no_follow(root.parent / ref, label=f"subject {ref}")
        digest.update(ref.encode("utf-8") + b"\0" + str(len(payload)).encode("ascii") + b"\0")
        digest.update(payload + b"\0")
    return "sha256:" + digest.hexdigest()


def _find_member(archive: ZipFile, basename: str) -> str:
    matches = [name for name in archive.namelist() if PurePosixPath(name).name == basename]
    _require(len(matches) == 1, f"source member count drift for {basename}: {len(matches)}")
    return matches[0]


def _source_s03_p2(roadmap: Mapping[str, Any]) -> dict[str, Any]:
    stages = roadmap.get("stages")
    _require(isinstance(stages, list), "source roadmap stages missing")
    stage = [row for row in stages if isinstance(row, dict) and row.get("id") == "S03"]
    _require(len(stage) == 1 and isinstance(stage[0].get("phases"), list), "source S03 drift")
    phase = [row for row in stage[0]["phases"] if isinstance(row, dict) and row.get("id") == "P2"]
    _require(len(phase) == 1, "source S03-P2 count drift")
    return phase[0]


def verify_source_package(
    source_package: Path = DEFAULT_SOURCE_PACKAGE,
    project_root: Optional[Path] = None,
) -> dict[str, Any]:
    root = _normalize_project_root(project_root)
    package_payload = _read_regular_bytes_no_follow(Path(source_package), label="source package")
    _require(_sha256(package_payload) == "sha256:" + SOURCE_PACKAGE_SHA256, "source package SHA-256 drift")
    with ZipFile(io.BytesIO(package_payload)) as archive:
        manifest_name = _find_member(archive, SOURCE_MANIFEST_BASENAME)
        manifest_payload = archive.read(manifest_name)
        _require(_sha256(manifest_payload) == "sha256:" + SOURCE_MANIFEST_SHA256, "source manifest drift")
        rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8-sig"))))
        _require(len(rows) == 21 and set(rows[0] if rows else {}) == {"相对路径", "字节数", "SHA256"}, "source manifest schema/count drift")
        prefix = PurePosixPath(manifest_name).parent
        by_relative: dict[str, list[str]] = {}
        for name in archive.namelist():
            try:
                relative = PurePosixPath(name).relative_to(prefix).as_posix()
            except ValueError:
                continue
            by_relative.setdefault(relative, []).append(name)
        for row in rows:
            relative = PurePosixPath(row["相对路径"])
            _require(not relative.is_absolute() and ".." not in relative.parts, "unsafe source manifest path")
            matches = by_relative.get(relative.as_posix(), [])
            _require(len(matches) == 1, f"source member count drift: {relative.name}")
            payload = archive.read(matches[0])
            _require(len(payload) == int(row["字节数"]) and _sha256(payload) == "sha256:" + row["SHA256"], f"source integrity drift: {relative.name}")
        roadmap_payload = archive.read(_find_member(archive, SOURCE_ROADMAP_BASENAME))
        _require(_sha256(roadmap_payload) == "sha256:" + SOURCE_ROADMAP_SHA256, "source roadmap drift")
        source_roadmap = json.loads(roadmap_payload.decode("utf-8-sig"))
    tracked_payload = _read_regular_bytes_no_follow(root / "taskpack/v1_5/roadmap_v2_0.json", label="tracked roadmap")
    _require(_sha256(tracked_payload) == "sha256:" + TRACKED_ROADMAP_SHA256, "tracked roadmap drift")
    tracked_roadmap = json.loads(tracked_payload.decode("utf-8"))
    _require(tuple(source_roadmap.get(key) for key in ("stage_count", "phase_count", "task_count")) == (24, 72, 216), "roadmap count drift")
    source_phase = _source_s03_p2(source_roadmap)
    _require(source_phase == _source_s03_p2(tracked_roadmap), "source/tracked S03-P2 semantic drift")
    expected_tasks = [{
        "id": task["task_id"][-3:],
        **{key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")},
    } for task in TASKS]
    _require(source_phase.get("tasks") == expected_tasks, "S03-P2 exact Task contract drift")
    return {
        "package_file": SOURCE_PACKAGE_NAME, "package_sha256": SOURCE_PACKAGE_SHA256,
        "manifest_member": SOURCE_MANIFEST_BASENAME, "manifest_sha256": SOURCE_MANIFEST_SHA256,
        "verified_member_count": 21, "roadmap_member": SOURCE_ROADMAP_BASENAME,
        "roadmap_member_sha256": SOURCE_ROADMAP_SHA256, "tracked_roadmap_sha256": TRACKED_ROADMAP_SHA256,
        "stage_count": 24, "phase_count": 72, "task_count": 216,
        "s03_p2_semantic_equal": True, "s03_p2_task_count": 3,
    }


def _validate_runtime_tree(root: Path) -> dict[str, Any]:
    runtime_root = root / LOCAL_RUNTIME_RELATIVE
    value = os.lstat(runtime_root)
    _require(stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode) == 0o700, "local_runtime type/mode drift")
    _require(sorted(entry.name for entry in os.scandir(runtime_root)) == sorted(LAYERS), "local_runtime exact layer set drift")
    directory_count = 1
    file_count = 0
    for current, directory_names, file_names in os.walk(runtime_root, followlinks=False):
        current_path = Path(current)
        current_stat = os.lstat(current_path)
        _require(stat.S_ISDIR(current_stat.st_mode) and stat.S_IMODE(current_stat.st_mode) == 0o700, "runtime directory contract drift")
        if current_path != runtime_root:
            directory_count += 1
        for name in directory_names:
            child = os.lstat(current_path / name)
            _require(stat.S_ISDIR(child.st_mode), "runtime symlink or special directory forbidden")
        for name in file_names:
            child = os.lstat(current_path / name)
            _require(stat.S_ISREG(child.st_mode) and int(child.st_nlink) == 1, "runtime symlink, hardlink, or special file forbidden")
            _require(stat.S_IMODE(child.st_mode) in {0o400, 0o600}, "runtime private file mode drift")
            file_count += 1
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", "KMFA/local_runtime"],
        cwd=root.parent, capture_output=True, check=False,
    )
    _require(ignored.returncode == 0, "local_runtime is not Git ignored")
    tracked = subprocess.run(
        ["git", "ls-files", "--", "KMFA/local_runtime"],
        cwd=root.parent, capture_output=True, text=True, check=False,
    )
    _require(tracked.returncode == 0 and not tracked.stdout.strip(), "local_runtime has tracked entries")
    ignore_payload = _read_regular_bytes_no_follow(root / ".gitignore", label="KMFA gitignore")
    _require(any(line.strip() == b"local_runtime/" for line in ignore_payload.splitlines()), "exact local_runtime ignore rule missing")
    return {
        "gitignore_attested": True, "tracked_entry_count": 0, "unsafe_entry_count": 0,
        "private_directory_count": directory_count, "private_file_count": file_count,
    }


def _validate_projection(projection: Mapping[str, Any]) -> None:
    expected_identity = {
        "schema_version": PUBLIC_PROJECTION_SCHEMA_VERSION,
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2", "status": "PASS",
    }
    for key, expected in expected_identity.items():
        _require(projection.get(key) == expected, f"public projection {key} drift")
    for key in (
        "directory_contract", "copy_authorization", "p1_baseline_binding",
        "runtime_root_binding", "content_addressed_copy", "authorized_io",
        "cleanup", "privacy",
    ):
        _require(isinstance(projection.get(key), dict), f"public projection {key} missing")
    directory = projection["directory_contract"]
    authorization = projection["copy_authorization"]
    copy = projection["content_addressed_copy"]
    authorized = projection["authorized_io"]
    cleanup = projection["cleanup"]
    privacy = projection["privacy"]
    _require(directory.get("layer_count") == 9, "private layer count drift")
    for key in ("all_layers_present", "all_layer_modes_0700", "private_files_mode_0600", "cas_blob_mode_0400", "gitignore_attested"):
        _require(directory.get(key) is True, f"directory contract {key} is not true")
    expected_authorization = {
        "authorization_scope": "READ_ONLY_CONTENT_ADDRESSED_COPY",
        "copy_allowed": True,
        "raw_parse_allowed": False,
        "raw_value_extraction_allowed": False,
        "destination_must_be_private": True,
        "overwrite_existing_blob_allowed": False,
    }
    _require(authorization == expected_authorization, "public copy authorization drift")
    expected_baseline = {
        "fixed_project_entry": True,
        "policy_bound": True,
        "p1_receipt_strictly_reconstructed": True,
        "p1_final_snapshot_exact_match_both_runs": True,
        "raw_root_identity_match_both_runs": True,
        "final_drain_seconds": runtime.p1_guard.FINAL_DRAIN_SECONDS,
    }
    _require(projection["p1_baseline_binding"] == expected_baseline, "public P1 baseline binding drift")
    expected_runtime_binding = {
        "fixed_project_runtime": True,
        "held_dirfd_both_runs": True,
        "device_inode_stable": True,
        "pathname_identity_stable": True,
    }
    _require(projection["runtime_root_binding"] == expected_runtime_binding, "public runtime root binding drift")
    integer_keys = (
        "run_count", "source_file_count", "unique_blob_count",
        "first_inventory_count", "second_inventory_count",
        "first_run_created_count", "first_run_reused_count",
        "second_run_created_count", "second_run_reused_count", "second_run_new_bytes",
    )
    for key in integer_keys:
        _require(isinstance(copy.get(key), int) and not isinstance(copy.get(key), bool) and copy[key] >= 0, f"copy aggregate {key} invalid")
    source_count = copy["source_file_count"]
    _require(copy["run_count"] == 2, "phase idempotency requires exactly two bound imports")
    _require(source_count == EXPECTED_SOURCE_FILE_COUNT, "copy source count does not match frozen S03-P1 preflight")
    _require(0 < copy["unique_blob_count"] <= source_count, "copy source/blob count invalid")
    _require(copy["first_inventory_count"] == copy["second_inventory_count"] == copy["unique_blob_count"], "public CAS inventory count drift")
    _require(copy.get("inventory_digest_set_stable") is True, "public CAS digest inventory not stable")
    _require(copy["first_run_created_count"] + copy["first_run_reused_count"] == source_count, "first import accounting drift")
    _require(copy["second_run_created_count"] == 0, "second import created a new blob")
    _require(copy["second_run_reused_count"] == source_count, "second import did not reuse all sources")
    _require(copy["second_run_new_bytes"] == 0, "second import wrote new blob bytes")
    _require(copy.get("blob_count_stable") is True, "blob count was not stable")
    _require(copy.get("hash_match_both_runs") is True, "both import hashes did not match")
    _require(copy.get("hash_algorithm") == "sha256", "copy hash algorithm drift")
    _require(copy.get("idempotent_reuse_without_rewrite") is True, "copy idempotency failed")
    _require(copy.get("prohibited_raw_mutation_detected") is False, "prohibited raw mutation detected")
    _require(copy.get("quarantine_triggered") is False, "quarantine was triggered")
    _require(authorized.get("os_atime_side_effect_possible") is True, "atime possibility overclaim")
    _require(authorized.get("os_atime_side_effect_observed") in {True, False}, "atime observation missing")
    _require(authorized.get("os_atime_restoration_performed") is False, "atime restoration is forbidden")
    _require(authorized.get("absolute_zero_metadata_mutation_claimed") is False, "absolute-zero metadata mutation overclaim")
    expected_cleanup = {
        "mode": "DRY_RUN", "destructive_execution_performed": False,
        "second_confirmation_required": True, "exact_plan_digest_required": True,
        "one_use_marker_required": True, "real_runtime_deletion_allowed": False,
        "synthetic_rehearsal_pass": True, "plan_deterministic": True,
        "protected_violation_count": 0, "candidate_count": 0,
        "condition_based_retention": True,
        "canonical_retention_basis": "UNTIL_CONDITION",
        "canonical_auto_delete_enabled": False,
        "synthetic_backup_verified": True, "synthetic_delete_verified": True,
        "synthetic_restore_verified": True, "synthetic_rehash_verified": True,
    }
    for key, expected in expected_cleanup.items():
        _require(cleanup.get(key) == expected, f"cleanup {key} drift")
    privacy_keys = (
        "raw_paths_in_projection", "raw_names_in_projection",
        "raw_hashes_in_projection", "raw_values_in_projection", "path_tokens_in_projection",
    )
    for key in privacy_keys:
        _require(privacy.get(key) is False, f"projection privacy {key} drift")
    serialized = _json_bytes(projection)
    for token in _FORBIDDEN_PUBLIC_TOKENS:
        _require(token not in serialized, "private identifier leaked into projection")


def _canonical_projection_digest(projection: Mapping[str, Any]) -> str:
    payload = json.dumps(
        projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(payload)


def _validate_private_receipt(receipt: Mapping[str, Any], projection: Mapping[str, Any]) -> None:
    identity = {
        "schema_version": PRIVATE_RECEIPT_SCHEMA_VERSION,
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2", "status": "PASS",
    }
    for key, expected in identity.items():
        _require(receipt.get(key) == expected, f"private receipt {key} drift")
    _require(receipt.get("public_projection_sha256") == _canonical_projection_digest(projection), "private receipt/projection digest drift")
    directory = receipt.get("directory_contract")
    authorization = receipt.get("copy_authorization")
    baseline = receipt.get("p1_baseline_binding")
    runtime_binding = receipt.get("runtime_root_binding")
    copy = receipt.get("content_addressed_copy")
    monitor = receipt.get("monitor")
    authorized = receipt.get("authorized_io")
    cleanup = receipt.get("cleanup")
    for value, label in (
        (directory, "directory"), (authorization, "copy authorization"),
        (baseline, "P1 baseline"), (runtime_binding, "runtime root binding"),
        (copy, "copy"), (monitor, "monitor"),
        (authorized, "authorized IO"), (cleanup, "cleanup"),
    ):
        _require(isinstance(value, dict), f"private receipt {label} missing")
    _require(tuple(directory.get("layers", ())) == LAYERS, "private receipt layer order drift")
    _require(directory.get("directory_mode") == "0700" and directory.get("private_file_mode") == "0600" and directory.get("cas_blob_mode") == "0400", "private receipt mode contract drift")
    expected_private_authorization = {
        "authorization_scope": "READ_ONLY_CONTENT_ADDRESSED_COPY",
        "operation": "copy_to_private_content_addressed_mirror",
        "target_layer": "content_mirror",
        "copy_allowed": True,
        "raw_parse_allowed": False,
        "raw_value_extraction_allowed": False,
        "destination_must_be_private": True,
        "overwrite_existing_blob_allowed": False,
    }
    for key, expected in expected_private_authorization.items():
        _require(authorization.get(key) == expected, f"private copy authorization {key} drift")
    for key, expected in projection["copy_authorization"].items():
        _require(authorization.get(key) == expected, f"receipt/projection copy authorization {key} drift")
    _require(baseline.get("fixed_project_entry") is True, "private baseline is not fixed project entry")
    for key in ("policy_sha256", "p1_receipt_sha256"):
        _require(_DIGEST_RE.fullmatch(str(baseline.get(key))) is not None, f"private baseline {key} invalid")
    _require(
        isinstance(baseline.get("raw_root_device"), int)
        and baseline["raw_root_device"] >= 0
        and isinstance(baseline.get("raw_root_inode"), int)
        and baseline["raw_root_inode"] > 0,
        "private baseline raw root identity invalid",
    )
    _require(
        baseline.get("final_drain_seconds") == runtime.p1_guard.FINAL_DRAIN_SECONDS,
        "private baseline final drain drift",
    )
    baseline_rows = baseline.get("final_snapshot_file_rows")
    _require(
        isinstance(baseline_rows, list)
        and len(baseline_rows) == EXPECTED_SOURCE_FILE_COUNT,
        "private P1 final snapshot row count drift",
    )
    _require(runtime_binding.get("same_identity_both_runs") is True, "runtime root identity differs between imports")
    _require(runtime_binding.get("pathname_identity_stable") is True, "runtime root pathname identity drift")
    _require(runtime_binding.get("held_dirfd_both_runs") is True, "runtime root dirfd was not held")
    _require(
        isinstance(runtime_binding.get("device"), int)
        and runtime_binding["device"] >= 0
        and isinstance(runtime_binding.get("inode"), int)
        and runtime_binding["inode"] > 0,
        "private runtime root identity invalid",
    )
    _require(copy.get("run_count") == 2, "private receipt does not bind two imports")
    _require(copy.get("blob_count_stable") is True and copy.get("second_run_new_bytes") == 0, "private idempotency binding failed")
    public_copy = projection["content_addressed_copy"]
    for key in ("run_count", "source_file_count", "unique_blob_count", "blob_count_stable", "second_run_new_bytes", "inventory_digest_set_stable"):
        _require(copy.get(key) == public_copy.get(key), f"receipt/projection copy {key} drift")
    _require(copy.get("hash_algorithm") == public_copy.get("hash_algorithm") == "sha256", "receipt/projection hash algorithm drift")
    runs = copy.get("runs")
    _require(isinstance(runs, list) and len(runs) == 2, "private receipt run ledger drift")
    source_count = copy.get("source_file_count")
    _require(isinstance(source_count, int) and source_count > 0, "private source count invalid")
    manifests = []
    for index, run in enumerate(runs, start=1):
        _require(isinstance(run, dict) and run.get("run_number") == index, "private import run order drift")
        _require(
            isinstance(run.get("created_count"), int)
            and isinstance(run.get("reused_count"), int)
            and run["created_count"] >= 0
            and run["reused_count"] >= 0,
            "private import run count invalid",
        )
        _require(run.get("hash_match_all") is True, "private import hash mismatch")
        _require(
            run.get("final_drain_seconds") == runtime.p1_guard.FINAL_DRAIN_SECONDS,
            "private import final drain drift",
        )
        items = run.get("items")
        _require(isinstance(items, list) and len(items) == source_count, "private import item accounting drift")
        normalized = []
        for item in items:
            _require(isinstance(item, dict), "private import item invalid")
            _require(isinstance(item.get("path_token"), str) and item["path_token"], "private path token invalid")
            _require(_DIGEST_RE.fullmatch(str(item.get("content_sha256"))) is not None, "private content digest invalid")
            _require(isinstance(item.get("size_bytes"), int) and item["size_bytes"] >= 0, "private item bytes invalid")
            _require(item.get("status") in {"CREATED", "REUSED"}, "private import status invalid")
            normalized.append((item["path_token"], item["content_sha256"], item["size_bytes"]))
        manifests.append(tuple(sorted(normalized)))
    _require(manifests[0] == manifests[1], "two-run private manifests drift")
    normalized_baseline_rows = tuple(sorted(
        (
            row.get("path_token"),
            row.get("content_sha256"),
            row.get("size_bytes"),
        )
        for row in baseline_rows
        if isinstance(row, dict)
    ))
    _require(
        len(normalized_baseline_rows) == EXPECTED_SOURCE_FILE_COUNT
        and manifests[0] == normalized_baseline_rows,
        "P2 private manifest does not exactly match P1 final snapshot",
    )
    _require(runs[0].get("created_count") + runs[0].get("reused_count") == source_count, "first private run accounting drift")
    _require(runs[1].get("created_count") == 0 and runs[1].get("reused_count") == source_count, "second private run is not pure reuse")
    _require(runs[0].get("created_count") == public_copy["first_run_created_count"] and runs[0].get("reused_count") == public_copy["first_run_reused_count"], "first run receipt/projection accounting drift")
    _require(runs[1].get("created_count") == public_copy["second_run_created_count"] and runs[1].get("reused_count") == public_copy["second_run_reused_count"], "second run receipt/projection accounting drift")
    unique_digests = tuple(sorted({row[1] for row in manifests[0]}))
    _require(len(unique_digests) == copy.get("unique_blob_count"), "private unique digest count drift")
    first_inventory = copy.get("first_inventory")
    second_inventory = copy.get("second_inventory")
    for inventory, label in ((first_inventory, "first"), (second_inventory, "second")):
        _require(isinstance(inventory, dict), f"private {label} CAS inventory missing")
        _require(inventory.get("blob_count") == len(unique_digests), f"private {label} inventory count drift")
        _require(tuple(inventory.get("content_digests", ())) == unique_digests, f"private {label} inventory digest set drift")
        _require(inventory.get("source_digest_set_match") is True, f"private {label} inventory/source mismatch")
        _require(isinstance(inventory.get("total_bytes"), int) and inventory["total_bytes"] >= 0, f"private {label} inventory bytes invalid")
    _require(first_inventory == second_inventory, "private CAS inventory changed between imports")
    _require(copy.get("inventory_digest_set_stable") is True, "private inventory digest set not stable")
    _require(monitor.get("prohibited_raw_mutation_detected") is False, "private monitor detected raw mutation")
    _require(monitor.get("production_backend_attested_all_runs") is True, "production monitor not attested for both imports")
    _require(monitor.get("prohibited_raw_mutation_detected") == public_copy["prohibited_raw_mutation_detected"], "receipt/projection mutation attestation drift")
    _require(authorized.get("os_atime_side_effect_possible") is True, "private atime possibility drift")
    _require(authorized.get("os_atime_restoration_performed") is False, "private atime restoration forbidden")
    for key in ("os_atime_side_effect_possible", "os_atime_side_effect_observed", "os_atime_restoration_performed", "absolute_zero_metadata_mutation_claimed"):
        _require(authorized.get(key) == projection["authorized_io"].get(key), f"receipt/projection authorized IO {key} drift")
    _require(cleanup.get("mode") == "DRY_RUN", "private cleanup mode drift")
    _require(cleanup.get("canonical_retention_basis") == "UNTIL_CONDITION", "private cleanup retention basis drift")
    _require(cleanup.get("condition_based_retention") is True, "private condition-based retention missing")
    _require(cleanup.get("retention_days") == {}, "private canonical retention map must be empty")
    _require(isinstance(cleanup.get("evaluated_at_ns"), int) and cleanup["evaluated_at_ns"] > 0, "private cleanup evaluated_at_ns invalid")
    _require(cleanup.get("candidate_count") == 0 and cleanup.get("candidates") == [], "canonical cleanup must have zero candidates")
    _require(cleanup.get("protected_violation_count") == 0, "private cleanup protection drift")
    _require(_DIGEST_RE.fullmatch(str(cleanup.get("plan_digest"))) is not None, "private cleanup plan digest invalid")
    rehearsal = cleanup.get("synthetic_rehearsal")
    _require(isinstance(rehearsal, dict), "private synthetic rehearsal receipt missing")
    _require(rehearsal.get("status") == "PASS", "private synthetic rehearsal status drift")
    _require(isinstance(rehearsal.get("candidate_count"), int) and rehearsal["candidate_count"] > 0, "synthetic rehearsal has no deletion candidate")
    for key in ("backup_verified", "delete_verified", "restore_verified", "rehash_verified"):
        _require(rehearsal.get(key) is True, f"private synthetic rehearsal {key} drift")
        _require(rehearsal.get(key) == projection["cleanup"].get("synthetic_" + key), f"receipt/projection synthetic {key} drift")
    _require(rehearsal.get("protected_violation_count") == 0, "synthetic rehearsal protected violation")


def _validate_actual_cas_inventory(root: Path, receipt: Mapping[str, Any]) -> None:
    copy = receipt["content_addressed_copy"]
    first_inventory = copy["first_inventory"]
    expected = [value.removeprefix("sha256:") for value in first_inventory["content_digests"]]
    observed = runtime.inspect_cas_inventory(
        root / LOCAL_RUNTIME_RELATIVE,
        expected_source_digests=expected,
    )
    _require(observed.source_digest_set_match is True, "actual CAS/source digest set mismatch")
    _require(observed.blob_count == first_inventory["blob_count"], "actual CAS blob count drift")
    _require(observed.total_bytes == first_inventory["total_bytes"], "actual CAS byte inventory drift")
    _require(tuple("sha256:" + value for value in observed.content_digests) == tuple(first_inventory["content_digests"]), "actual CAS digest inventory drift")


def _validate_p1_policy_binding(root: Path, receipt: Mapping[str, Any]) -> None:
    policy_path = root / P1_PRIVATE_POLICY_RELATIVE
    p1_receipt_path = root / P1_PRIVATE_RECEIPT_RELATIVE
    for path, label in (
        (policy_path, "policy"),
        (p1_receipt_path, "receipt"),
    ):
        value = os.lstat(path)
        _require(
            stat.S_ISREG(value.st_mode)
            and int(value.st_nlink) == 1
            and stat.S_IMODE(value.st_mode) == 0o600,
            f"frozen P1 private {label} type/link/mode unsafe",
        )
    policy_payload = _read_regular_bytes_no_follow(policy_path, label="fixed P1 policy")
    p1_receipt_payload = _read_regular_bytes_no_follow(p1_receipt_path, label="fixed P1 receipt")
    fixed = runtime.load_fixed_p1_baseline()
    policy = fixed.policy
    authorization = receipt["copy_authorization"]
    baseline = receipt["p1_baseline_binding"]
    _require(authorization.get("root_id") == policy.root_id, "copy authorization root binding drift")
    _require(authorization.get("source_scope_id") == policy.source_scope_id, "copy authorization source scope binding drift")
    _require(tuple(authorization.get("allowed_extensions", ())) == tuple(runtime.p1_guard.EXPECTED_ALLOWED_EXTENSIONS), "copy authorization extension binding drift")
    _require(authorization.get("max_depth") == 0 == policy.max_depth, "copy authorization depth binding drift")
    _require(baseline["policy_sha256"] == _sha256(policy_payload), "P1 policy digest binding drift")
    _require(baseline["p1_receipt_sha256"] == _sha256(p1_receipt_payload), "P1 receipt digest binding drift")
    _require(
        (baseline["raw_root_device"], baseline["raw_root_inode"])
        == (fixed.root_device, fixed.root_inode),
        "P1 raw root identity binding drift",
    )
    expected_rows = [
        {
            "path_token": token,
            "content_sha256": "sha256:" + digest,
            "size_bytes": size,
        }
        for token, digest, size in fixed.file_rows
    ]
    _require(
        baseline["final_snapshot_file_rows"] == expected_rows,
        "P1 final token/digest/size baseline drift",
    )


def _validate_actual_runtime_root_binding(
    root: Path,
    receipt: Mapping[str, Any],
) -> None:
    value = os.lstat(root / LOCAL_RUNTIME_RELATIVE)
    binding = receipt["runtime_root_binding"]
    _require(
        stat.S_ISDIR(value.st_mode)
        and not stat.S_ISLNK(value.st_mode)
        and (int(value.st_dev), int(value.st_ino))
        == (binding["device"], binding["inode"]),
        "actual runtime root identity drift",
    )


def _validate_actual_cleanup_plan(root: Path, receipt: Mapping[str, Any]) -> None:
    cleanup = receipt["cleanup"]
    plan = runtime.build_cleanup_plan(
        root / LOCAL_RUNTIME_RELATIVE,
        now_ns=cleanup["evaluated_at_ns"],
        retention_days=cleanup["retention_days"] or None,
    )
    _require(plan.plan_digest == cleanup["plan_digest"], "canonical cleanup plan digest drift")
    _require(not plan.candidates and cleanup["candidates"] == [], "canonical cleanup candidate drift")
    _require(plan.protected_violation_count == cleanup["protected_violation_count"] == 0, "canonical cleanup protection drift")


def _validate_private_evidence(root: Path) -> dict[str, Any]:
    private_root = root / PRIVATE_ROOT_RELATIVE
    root_stat = os.lstat(private_root)
    _require(stat.S_ISDIR(root_stat.st_mode) and stat.S_IMODE(root_stat.st_mode) == 0o700, "private evidence root type/mode unsafe")
    receipt_path = root / PRIVATE_RECEIPT_RELATIVE
    projection_path = root / PRIVATE_PROJECTION_RELATIVE
    for path in (receipt_path, projection_path):
        value = os.lstat(path)
        _require(stat.S_ISREG(value.st_mode) and int(value.st_nlink) == 1 and stat.S_IMODE(value.st_mode) == 0o600, f"private evidence type/link/mode unsafe: {path.name}")
    receipt = _read_json(receipt_path, label="private runtime receipt")
    projection = _read_json(projection_path, label="private public projection")
    _validate_projection(projection)
    _validate_private_receipt(receipt, projection)
    _validate_actual_cas_inventory(root, receipt)
    _validate_p1_policy_binding(root, receipt)
    _validate_actual_runtime_root_binding(root, receipt)
    _validate_actual_cleanup_plan(root, receipt)
    return {
        "receipt": receipt, "projection": projection,
        "tree": _validate_runtime_tree(root),
        "receipt_mtime_ns": os.lstat(receipt_path).st_mtime_ns,
        "projection_mtime_ns": os.lstat(projection_path).st_mtime_ns,
    }


def _directory_policy() -> dict[str, Any]:
    responsibilities = {
        "content_mirror": ("L1", "IMMUTABLE_CONTENT_ADDRESSED_COPY"),
        "extracted": ("L2", "APPEND_ONLY_EXTRACTION_VERSIONS"),
        "staging": ("L3", "PRIVATE_UNPROMOTED_WORK"),
        "facts": ("L4_L7", "VERSIONED_FACTS_AND_APPEND_ONLY_CONTROL_EVENTS"),
        "cache": ("L5_SUPPORT", "REBUILDABLE_CACHE_ONLY"),
        "reports": ("L6", "VERSIONED_REPORTS_PUBLISHED_NEVER_OVERWRITTEN"),
        "logs": ("CROSS_LAYER_AUDIT", "APPEND_ONLY_OPERATION_LOG"),
        "backups": ("RECOVERY_PLANE", "RESTORE_TEST_REQUIRED"),
        "quarantine": ("EXCEPTION_PLANE", "NO_AUTOMATIC_PROMOTION"),
    }
    return {
        "schema_version": "kmfa.metadata.v015.s03_p2.private_runtime.directory_contract.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P2",
        "runtime_root_token": "LOCAL_RUNTIME",
        "raw_layer": {"logical_layer": "L0", "inside_runtime": False, "mutation_allowed": False, "cleanup_candidate_allowed": False},
        "layers": [{
            "layer_id": layer, "logical_mapping": responsibilities[layer][0],
            "responsibility": responsibilities[layer][1],
            "directory_mode": "0700", "gitignored": True,
        } for layer in LAYERS],
        "layer_count": 9, "root_directory_mode": "0700",
        "private_file_mode": "0600", "immutable_cas_blob_mode": "0400",
        "symlinks_allowed": False, "hardlinks_allowed": False,
        "special_files_allowed": False, "tracked_entries_allowed": False,
        "copy_authorization": {
            "scope": "READ_ONLY_CONTENT_ADDRESSED_COPY",
            "allowed_operations": ["list", "stat", "read", "hash", "copy"],
            "raw_parse_allowed": False, "raw_value_extraction_allowed": False,
            "destination_must_be_private": True, "overwrite_existing_blob_allowed": False,
        },
        "public_safe_status": "PUBLIC_SAFE",
    }


def _lifecycle_policy() -> dict[str, Any]:
    rules = {
        "content_mirror": ("INDEFINITE_WHILE_REFERENCED", False, "REIMPORT_FROM_REGISTERED_READ_ONLY_SOURCE"),
        "extracted": ("UNTIL_REBUILD_AND_AUDIT_DEPENDENCIES_RELEASED", False, "REBUILD_FROM_CONTENT_MIRROR"),
        "staging": ("UNTIL_RUN_CLOSED_AND_CONFIRMATION_BOUND", True, "RECREATE_FROM_CONTENT_MIRROR"),
        "facts": ("INDEFINITE_VERSIONED", False, "RESTORE_FROM_TESTED_BACKUP"),
        "cache": ("UNTIL_REBUILD_SAFE_AND_CONFIRMATION_BOUND", True, "REBUILD_FROM_FACTS"),
        "reports": ("PUBLISHED_INDEFINITE_DRAFTS_UNTIL_CONDITION", False, "REBUILD_FROM_FACTS_AND_MANIFEST"),
        "logs": ("AUDIT_INDEFINITE_OPERATIONAL_UNTIL_CONDITION", False, "RESTORE_AUDIT_LOG_BACKUP"),
        "backups": ("UNTIL_REPLACEMENT_RESTORE_TEST_PASSES", False, "RESTORE_FROM_ALTERNATE_TESTED_BACKUP"),
        "quarantine": ("UNTIL_OWNER_INVESTIGATION_CLOSED", False, "OWNER_DIRECTED_RECOVERY"),
    }
    return {
        "schema_version": "kmfa.metadata.v015.s03_p2.lifecycle_policy.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P2",
        "policy_basis": "CONDITION_BASED_NO_UNSUPPORTED_RETENTION_DAYS",
        "rules": [{
            "layer_id": layer, "owner_role": "KMFA_RUNTIME_OWNER",
            "retention": rules[layer][0], "automatically_deletable": rules[layer][1],
            "recovery_method": rules[layer][2], "dry_run_required": True,
            "exact_plan_confirmation_required": True, "one_use_confirmation_required": True,
        } for layer in LAYERS],
        "protected_classes": [
            "RAW_L0", "REFERENCED_CONTENT_MIRROR", "CONFIRMED_FACT", "CONTROL_EVENT",
            "AUDIT_EVIDENCE", "PUBLISHED_REPORT", "REPORT_REBUILD_DEPENDENCY",
            "ONLY_TESTED_BACKUP", "OPEN_QUARANTINE_CASE",
        ],
        "canonical_runtime_cleanup_mode": "DRY_RUN_ONLY",
        "destructive_cleanup_requires_second_confirmation": True,
        "synthetic_fixture_execution_allowed": True,
        "real_irreversible_cleanup_performed": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _normalize_validation_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    require_pass: bool,
    current_head: Optional[str] = None,
) -> list[dict[str, Any]]:
    expected_items = list(EXPECTED_VALIDATION_RECEIPTS.items())
    _require(len(rows) == len(expected_items), "validation receipt count drift")
    normalized = [dict(row) for row in rows]
    _require([row.get("validation_id") for row in normalized] == [item[0] for item in expected_items], "validation receipt order drift")
    if require_pass:
        _require(len({row.get("run_id") for row in normalized}) == 1, "validation receipts do not share one run_id")
        _require(len({row.get("validation_subject_sha256") for row in normalized}) == 1, "validation receipts do not share one subject")
    for sequence, (row, (validation_id, command)) in enumerate(zip(normalized, expected_items), start=1):
        _require(row.get("schema_version") == VALIDATION_RECEIPT_SCHEMA_VERSION, "validation schema drift")
        _require(row.get("validation_id") == validation_id and row.get("command") == command, "validation command drift")
        _require(row.get("execution_sequence") == sequence, "validation sequence drift")
        _require(row.get("phase_base_commit") == PHASE_BASE_COMMIT, "validation base drift")
        if require_pass:
            _require(row.get("result") == "PASS" and row.get("exit_code") == 0, "validation is not exact PASS")
            for key in ("validation_subject_sha256", "stdout_sha256", "stderr_sha256"):
                _require(_DIGEST_RE.fullmatch(str(row.get(key))) is not None, f"validation {key} invalid")
            _require(row.get("head_before") == row.get("head_after") == current_head, "validation HEAD drift")
            _require(isinstance(row.get("duration_ms"), int) and row["duration_ms"] >= 0, "validation duration invalid")
            for key in ("started_at", "ended_at"):
                parsed = datetime.fromisoformat(str(row.get(key, "")).replace("Z", "+00:00"))
                _require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "validation time lacks offset")
        else:
            _require(row.get("result") in {"PENDING", "PASS", "FAIL"}, "validation result invalid")
    return normalized


def _validation_rows(
    root: Path,
    validation_results_input: Optional[Path],
    *,
    reuse_public_results: bool,
) -> list[dict[str, Any]]:
    if validation_results_input is not None:
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root.parent,
            capture_output=True, text=True, check=False,
        )
        _require(current.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", current.stdout.strip()) is not None, "unable to resolve current HEAD")
        rows = _normalize_validation_rows(
            _read_jsonl(validation_results_input, label="private validation receipts"),
            require_pass=True, current_head=current.stdout.strip(),
        )
        subject = validation_subject_sha256(root)
        _require(all(row.get("validation_subject_sha256") == subject for row in rows), "validation subject is not current")
        return rows
    public_path = root / OUTPUT_ROOT_RELATIVE / VALIDATION_RESULTS_RELATIVE
    if reuse_public_results and public_path.exists():
        return _normalize_validation_rows(
            _read_jsonl(public_path, label="public validation results"),
            require_pass=False,
        )
    return [{
        "schema_version": VALIDATION_RECEIPT_SCHEMA_VERSION,
        "run_id": None, "validation_id": validation_id, "command": command,
        "result": "PENDING", "exit_code": None, "execution_sequence": sequence,
        "phase_base_commit": PHASE_BASE_COMMIT, "skip_reason": "VALIDATION_RUN_NOT_BOUND",
    } for sequence, (validation_id, command) in enumerate(EXPECTED_VALIDATION_RECEIPTS.items(), start=1)]


def _validation_accounting(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("result")) for row in rows)
    expected = len(EXPECTED_VALIDATION_RECEIPTS)
    return {
        "expected": expected, "recorded": len(rows), "passed": counts["PASS"],
        "pending": counts["PENDING"], "failed": counts["FAIL"],
        "all_exact_pass": len(rows) == expected and counts == Counter({"PASS": expected}),
    }


def _runtime_public(private: Mapping[str, Any]) -> dict[str, Any]:
    projection = deepcopy(private["projection"])
    projection["directory_contract"].update(private["tree"])
    projection["public_safe_status"] = "PUBLIC_SAFE"
    return projection


def _cleanup_public(runtime_public: Mapping[str, Any]) -> dict[str, Any]:
    cleanup = runtime_public["cleanup"]
    return {
        "schema_version": "kmfa.v015.s03_p2.lifecycle_cleanup_rehearsal.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_phase": "S03-P2",
        "canonical_runtime": {
            "mode": cleanup["mode"], "candidate_count": cleanup["candidate_count"],
            "retention_basis": cleanup["canonical_retention_basis"],
            "auto_delete_enabled": cleanup["canonical_auto_delete_enabled"],
            "protected_violation_count": cleanup["protected_violation_count"],
            "destructive_execution_performed": cleanup["destructive_execution_performed"],
            "real_runtime_deletion_allowed": cleanup["real_runtime_deletion_allowed"],
        },
        "synthetic_rehearsal": {
            "passed": cleanup["synthetic_rehearsal_pass"],
            "plan_deterministic": cleanup["plan_deterministic"],
            "second_confirmation_required": cleanup["second_confirmation_required"],
            "exact_plan_digest_required": cleanup["exact_plan_digest_required"],
            "one_use_marker_required": cleanup["one_use_marker_required"],
            "backup_verified": cleanup["synthetic_backup_verified"],
            "delete_verified": cleanup["synthetic_delete_verified"],
            "restore_verified": cleanup["synthetic_restore_verified"],
            "rehash_verified": cleanup["synthetic_rehash_verified"],
        },
        "raw_cleanup_candidate_allowed": False,
        "published_report_cleanup_candidate_allowed": False,
        "audit_evidence_cleanup_candidate_allowed": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _task_matrix(
    source: Mapping[str, Any],
    runtime_public: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    final_pass = runtime_public.get("status") == "PASS" and validation["all_exact_pass"]
    evidence = {
        "S03P2T01": [ARTIFACT_REFS["directory_policy"], ARTIFACT_REFS["runtime_verification"]],
        "S03P2T02": [ARTIFACT_REFS["runtime_verification"], ARTIFACT_REFS["validation_results"]],
        "S03P2T03": [ARTIFACT_REFS["lifecycle_policy"], ARTIFACT_REFS["cleanup_rehearsal"], ARTIFACT_REFS["validation_results"]],
    }
    tasks = []
    for task in TASKS:
        contract = {key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")}
        tasks.append({
            "task_id": task["task_id"], "source_contract": contract,
            "source_contract_sha256": _sha256(json.dumps(contract, ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED" if final_pass else "PENDING",
            "current_result": "TASK_ACCEPTED" if final_pass else "VALIDATION_PENDING",
            "evidence_refs": evidence[task["task_id"]],
        })
    return {
        "schema_version": "kmfa.v015.s03_p2.task_acceptance_matrix.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2", "source_package": dict(source),
        "tasks": tasks,
        "task_accounting": {"total": 3, "execution_complete": 3, "accepted": 3 if final_pass else 0},
        "phase_acceptance_status": "PASSED" if final_pass else "PENDING",
        "decision": "CONTINUE_TO_S03_P3_ONLY" if final_pass else "REMAIN_IN_S03_P2",
        "public_safe_status": "PUBLIC_SAFE",
    }


def _slot_rows() -> list[dict[str, Any]]:
    refs = {
        "manifest.json": [ARTIFACT_REFS["manifest"]],
        "commands.txt": [ARTIFACT_REFS["receipt_template"]],
        "test_results.json": [ARTIFACT_REFS["validation_results"]],
        "human_summary.md": [ARTIFACT_REFS["completion"]],
        "changed_files.txt": [ARTIFACT_REFS["manifest"]],
        "screenshots/": [],
        "logs/": [ARTIFACT_REFS["validation_results"]],
        "exports/": [ARTIFACT_REFS["runtime_verification"], ARTIFACT_REFS["cleanup_rehearsal"]],
        "rollback.md": [ARTIFACT_REFS["rollback"]],
        "open_risks.md": [ARTIFACT_REFS["open_risks"]],
    }
    rows = []
    for task in TASKS:
        for slot in EVIDENCE_SLOTS:
            na = slot == "screenshots/" or (slot == "exports/" and task["task_id"] == "S03P2T01")
            rows.append({
                "task_id": task["task_id"], "slot": slot,
                "status": "N/A_WITH_RATIONALE" if na else "COVERED",
                "evidence_refs": [] if na else refs[slot],
                "not_applicable_reason": (
                    "本 Phase 为 CLI 与机器合同，无视觉验收。"
                    if slot == "screenshots/"
                    else "T01 由 manifest 与机器策略覆盖，不生成额外 export。"
                    if na else None
                ),
            })
    return rows


def _human_outputs(
    matrix: Mapping[str, Any],
    validation: Mapping[str, Any],
    runtime_public: Mapping[str, Any],
) -> dict[str, bytes]:
    observed = runtime_public["authorized_io"]["os_atime_side_effect_observed"]
    return {
        "completion": (
            "# KMFA v1.5 S03-P2 私有派生目录完成记录\n\n"
            f"- Phase：{matrix['phase_acceptance_status']} / {matrix['decision']}。\n"
            "- S03：IN_PROGRESS / PENDING / 67%；本 run 未开始 S03-P3。\n"
            "- 九区完整、最小权限并被 Git 忽略；内容寻址副本两轮 hash 一致且第二轮零新增复用。\n"
            "- canonical runtime 仅 dry-run；真实删除未发生；合成 fixture 清理与恢复演练通过。\n"
            "- public evidence 不含 raw 路径、文件名、hash、业务值或私有清单标识。\n"
            f"- validation receipts：{validation['passed']}/{validation['expected']} PASS。\n"
        ).encode("utf-8"),
        "tests": (
            "# S03-P2 验证结果\n\n"
            f"- exact receipts：expected={validation['expected']}，passed={validation['passed']}，"
            f"pending={validation['pending']}，failed={validation['failed']}。\n"
            "- 覆盖九区/权限/Git ignore、CAS hash/幂等/隔离、atime truth、dry-run/二次确认/恢复和 public-safe 拒绝。\n"
        ).encode("utf-8"),
        "rollback": (
            "# S03-P2 回滚与恢复\n\n"
            "- raw L0 未被本 Phase 修改，禁止对 raw 执行回滚写入。\n"
            "- public-safe 代码与证据可反向提交；不得删除 raw、已发布报告或审计证据。\n"
            "- canonical runtime 清理仅 dry-run；异常副本保留在 quarantine 等待 owner 审核。\n"
        ).encode("utf-8"),
        "risks": (
            "# S03-P2 开放风险\n\n"
            f"- S03P2-RISK-001 / P1 / CONTROLLED_NONBLOCKING：授权读取可能触发 OS-managed atime；本次 observed={str(observed).lower()}，不恢复 atime。\n"
            "- S03P2-RISK-002 / P2 / CONTROLLED_NONBLOCKING：真实不可逆清理仍需 exact plan 绑定的一次性二次确认。\n"
            "- S03P2-RISK-003 / P2 / CONTROLLED_NONBLOCKING：private evidence 是本地证明，不等同于硬件级不可篡改证明。\n"
            "- S03P2-RISK-004 / P2 / CONTROLLED_NONBLOCKING：synthetic cleanup 尚未采用 tombstone transaction；确认先消费后逐项删除可能产生不可重试的部分删除，但能力被严格限制在 OS-temp synthetic fixture，canonical runtime 永不执行删除。\n"
            "- S03P2-RISK-005 / P2 / CONTROLLED_NONBLOCKING：synthetic backup 当前为内存 payload 恢复演练，未落盘到 backups 区并 fsync/reopen；仅证明受限 fixture 的逻辑恢复，不作为 canonical backup 有效性声明。\n"
            "- blocking risk：0；hash mismatch、raw mutation、Git 泄漏或保护对象入候选均 fail closed。\n"
        ).encode("utf-8"),
    }


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        for token in _FORBIDDEN_PUBLIC_TOKENS:
            if token in payload:
                raise BuildError(f"public-safe token violation in {path}: {token!r}")
        _require(_EMAIL_RE.search(payload) is None, f"email leaked into public output: {path}")
        _require(_SECRET_RE.search(payload) is None, f"secret-like assignment in public output: {path}")


def expected_outputs(
    *,
    project_root: Optional[Path] = None,
    source_package: Path = DEFAULT_SOURCE_PACKAGE,
    generated_at: str,
    validation_results_input: Optional[Path] = None,
    reuse_public_validation_results: bool = False,
) -> dict[Path, bytes]:
    try:
        generated = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError("generated_at must be ISO-8601") from error
    _require(generated.tzinfo is not None and generated.utcoffset() is not None, "generated_at lacks timezone")
    root = _normalize_project_root(project_root)
    source = verify_source_package(source_package, root)
    private = _validate_private_evidence(root)
    rows = _validation_rows(root, validation_results_input, reuse_public_results=reuse_public_validation_results)
    if validation_results_input is not None:
        newest = max(datetime.fromisoformat(str(row["ended_at"]).replace("Z", "+00:00")) for row in rows)
        now = datetime.now().astimezone()
        _require(-300 <= (generated - newest).total_seconds() <= 7200, "receipts not fresh for generated_at")
        _require(-300 <= (now - newest).total_seconds() <= 7200, "receipts stale against current clock")
        _require(-300 <= (now - generated).total_seconds() <= 7200, "generated_at stale against current clock")
    validation = _validation_accounting(rows)
    runtime_public = _runtime_public(private)
    cleanup_public = _cleanup_public(runtime_public)
    directory_policy = _directory_policy()
    lifecycle_policy = _lifecycle_policy()
    matrix = _task_matrix(source, runtime_public, validation)
    templates = [{
        "validation_id": validation_id, "command": command,
        "expected_result": "PASS", "expected_exit_code": 0, "blocking": True,
    } for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()]
    human = _human_outputs(matrix, validation, runtime_public)
    output_root = root / OUTPUT_ROOT_RELATIVE
    outputs: dict[Path, bytes] = {
        root / DIRECTORY_POLICY_RELATIVE: _json_bytes(directory_policy),
        root / LIFECYCLE_POLICY_RELATIVE: _json_bytes(lifecycle_policy),
        output_root / TASK_MATRIX_RELATIVE: _json_bytes(matrix),
        output_root / RUNTIME_VERIFICATION_RELATIVE: _json_bytes(runtime_public),
        output_root / CLEANUP_REHEARSAL_RELATIVE: _json_bytes(cleanup_public),
        output_root / EVIDENCE_SLOTS_RELATIVE: _jsonl_bytes(_slot_rows()),
        output_root / RECEIPT_TEMPLATE_RELATIVE: _jsonl_bytes(templates),
        output_root / VALIDATION_RESULTS_RELATIVE: _jsonl_bytes(rows),
        output_root / COMPLETION_RELATIVE: human["completion"],
        output_root / TEST_RESULTS_RELATIVE: human["tests"],
        output_root / ROLLBACK_RELATIVE: human["rollback"],
        output_root / OPEN_RISKS_RELATIVE: human["risks"],
    }
    final_pass = matrix["phase_acceptance_status"] == "PASSED"
    manifest = {
        "schema_version": "kmfa.v015.s03_p2.private_derived_runtime.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at, "run_mode": "IMPLEMENT",
        "work_kind": "PRIVATE_DERIVED_RUNTIME", "phase_base_commit": PHASE_BASE_COMMIT,
        "source_package": source, "task_accounting": matrix["task_accounting"],
        "execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS" if final_pass else "PENDING",
        "acceptance_status": "PASSED" if final_pass else "PENDING",
        "decision": "CONTINUE_TO_S03_P3_ONLY" if final_pass else "REMAIN_IN_S03_P2",
        "stage_status": {"lifecycle": "IN_PROGRESS", "acceptance": "PENDING", "execution_percentage": 67},
        "private_runtime": {
            "layer_count": 9, "all_layers_present": True, "all_layers_gitignored": True,
            "tracked_entry_count": 0, "minimum_permissions_pass": True, "raw_layer_inside_runtime": False,
        },
        "boundary_binding": {
            "fixed_p1_policy_and_receipt": True,
            "p1_final_snapshot_exact_match_both_runs": True,
            "raw_root_identity_match_both_runs": True,
            "final_drain_seconds": runtime.p1_guard.FINAL_DRAIN_SECONDS,
            "fixed_project_runtime": True,
            "held_runtime_root_dirfd_both_runs": True,
            "runtime_root_identity_stable": True,
        },
        "copy_acceptance": {
            "run_count": 2,
            "source_file_count": runtime_public["content_addressed_copy"]["source_file_count"],
            "unique_blob_count": runtime_public["content_addressed_copy"]["unique_blob_count"],
            "first_inventory_count": runtime_public["content_addressed_copy"]["first_inventory_count"],
            "second_inventory_count": runtime_public["content_addressed_copy"]["second_inventory_count"],
            "inventory_digest_set_stable": True,
            "second_run_created_count": 0, "second_run_new_bytes": 0,
            "blob_count_stable": True, "hash_match_both_runs": True,
            "idempotent_reuse_without_rewrite": True,
            "prohibited_raw_mutation_detected": False,
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": runtime_public["authorized_io"]["os_atime_side_effect_observed"],
            "os_atime_restoration_performed": False,
            "absolute_zero_metadata_mutation_claimed": False,
        },
        "cleanup_acceptance": {
            "canonical_dry_run": True, "synthetic_rehearsal_pass": True,
            "protected_violation_count": 0, "irreversible_real_cleanup_performed": False,
            "second_confirmation_required": True,
        },
        "private_evidence": {
            "required": True, "exact_path_public": False,
            "raw_path_or_name_public": False, "raw_hash_public": False,
            "private_manifest_public": False,
        },
        "evidence_slot_accounting": {
            "task_count": 3, "slots_per_task": 10, "total": 30,
            "covered": 24, "n_a_with_rationale": 6,
        },
        "validation_receipt_accounting": validation,
        "open_risk_accounting": {"total": 5, "blocking": 0, "p0": 0, "p1": 1, "p2": 4, "plan_gap_count": 0},
        "next_entry_gate": {
            "next_allowed_run": "S03-P3" if final_pass else "S03-P2",
            "s03_p3_entry_allowed": final_pass, "s03_p3_started": False,
            "stage3_review_entry_allowed": False, "product_implementation_allowed": False,
        },
        "downstream_actions": {
            "s03_p3_started": False, "stage3_review_performed": False,
            "product_runtime_implementation_performed": False,
            "github_upload_performed": False, "app_reinstall_performed": False,
            "business_execution_performed": False, "formal_report_generated": False,
            "irreversible_real_cleanup_performed": False,
        },
        "artifact_refs": dict(ARTIFACT_REFS),
        "artifact_integrity": [{
            "ref": path.relative_to(REPO_ROOT).as_posix(),
            "bytes": len(payload), "sha256": _sha256(payload),
        } for path, payload in sorted(outputs.items(), key=lambda item: item[0].as_posix())],
    }
    manifest["content_hash"] = _content_hash(manifest)
    outputs[output_root / MANIFEST_RELATIVE] = _json_bytes(manifest)
    _assert_public_safe(outputs)
    return outputs


def _open_directory_tree_no_follow(path: Path, *, create: bool) -> int:
    absolute = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
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


def _write_payload(path: Path, payload: bytes) -> None:
    parent_fd = _open_directory_tree_no_follow(path.parent, create=True)
    temporary = f".{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
    created = False
    try:
        try:
            existing = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            _require(
                stat.S_ISREG(existing.st_mode) and int(existing.st_nlink) == 1,
                f"unsafe output target: {path}",
            )
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            0o644,
            dir_fd=parent_fd,
        )
        created = True
        try:
            os.fchmod(descriptor, 0o644)
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(
            temporary,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        created = False
        final = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        _require(
            stat.S_ISREG(final.st_mode)
            and int(final.st_nlink) == 1
            and stat.S_IMODE(final.st_mode) == 0o644,
            f"output final type/link/mode drift: {path}",
        )
        os.fsync(parent_fd)
    finally:
        if created:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


def write_outputs(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        _write_payload(path, payload)


def check_outputs(outputs: Mapping[Path, bytes]) -> None:
    errors = []
    for path, expected in outputs.items():
        try:
            actual = _read_regular_bytes_no_follow(path, label="public output")
        except (BuildError, OSError) as error:
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
    parser.add_argument("--validation-results-input", type=Path)
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
                f"S03-P2 tasks={source['s03_p2_task_count']}; semantic_equal=true"
            )
            return 0
        if args.write == args.check:
            raise BuildError("select exactly one of --write or --check")
        root = _normalize_project_root(args.project_root)
        if args.check and args.validation_results_input is not None:
            raise BuildError("--check must reuse public validation results")
        if args.write and args.validation_results_input is not None:
            supplied = Path(os.path.abspath(os.path.normpath(os.fspath(args.validation_results_input))))
            fixed = Path(os.path.abspath(os.path.normpath(os.fspath(root / PRIVATE_VALIDATION_RECEIPTS_RELATIVE))))
            _require(supplied == fixed, "validation input must be the fixed private runner output")
        generated_at = args.generated_at
        if args.check and not generated_at:
            generated_at = str(_read_json(root / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE, label="manifest").get("generated_at", ""))
        _require(bool(generated_at), "--generated-at is required for write")
        outputs = expected_outputs(
            project_root=root, source_package=args.source_package,
            generated_at=generated_at, validation_results_input=args.validation_results_input,
            reuse_public_validation_results=args.check,
        )
        if args.write:
            write_outputs(outputs)
            print(f"PASS: wrote S03-P2 public-safe outputs ({len(outputs)} files)")
        else:
            check_outputs(outputs)
            print(f"PASS: exact S03-P2 outputs match ({len(outputs)} files)")
        return 0
    except (BuildError, json.JSONDecodeError, OSError, ValueError) as error:
        print("FAIL: KMFA v1.5 S03-P2 evidence build failed")
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
