#!/usr/bin/env python3
"""KMFA v1.5 S03-P3 public repository safety primitives.

The module implements three independent fail-closed controls:

* repository path and high-signal credential scanning;
* a strict public-safe metadata envelope with unknown-field rejection; and
* a synthetic private/public dual-plane probe using keyed opaque tokens.

It never opens the configured raw inbox. Synthetic sensitive values exist only
inside a caller-provided ignored/private directory or an OS temporary fixture.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import re
import stat
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PHASE_BASE_COMMIT = "c134cb72f05f99b6915732c5df835500f532b4b1"
RUN_PHASE_ID = "V015_S03_P3_PUBLIC_REPOSITORY_SAFETY"
TASK_ID = "KMFA-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY"

POLICY_VERSION = "SEC-KMFA-V015-S03P3-PUBLIC-REPOSITORY-DENY-001"
METADATA_CONTRACT_VERSION = "kmfa.v015.s03_p3.committable_metadata_contract.v1"
PUBLIC_ENVELOPE_VERSION = "kmfa.v015.public_safe_metadata_envelope.v1"
PRIVATE_RECEIPT_VERSION = "kmfa.private.v015.s03_p3.dual_plane_receipt.v1"
PUBLIC_PROJECTION_VERSION = "kmfa.v015.s03_p3.dual_plane_projection.public_safe.v1"
MAX_SCANNED_FILE_BYTES = 16 * 1024 * 1024
CURRENT_PUBLIC_EVIDENCE_PREFIX = (
    "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/"
)

PROTECTED_SUBMISSION_CLASSES = (
    "raw_business_payload",
    "credential_or_secret",
    "private_runtime_material",
    "runtime_library_or_log",
    "sensitive_report_detail",
)
COMMITTABLE_METADATA_CLASSES = (
    "schema",
    "deidentified_manifest",
    "status",
    "rule",
    "aggregate_evidence",
    "public_artifact_hash_index",
)
FORBIDDEN_PUBLIC_DETAIL_CLASSES = (
    "raw_or_source_filename",
    "person_customer_or_project_detail",
    "money_account_or_tax_detail",
    "credential_private_hash_or_absolute_location",
)

FORBIDDEN_SUFFIXES = frozenset(
    {
        ".7z", ".bak", ".bin", ".dat", ".db", ".dll", ".doc", ".docx", ".dylib", ".env", ".gz", ".key", ".log",
        ".m4v", ".mov", ".mp4", ".p12", ".pdf", ".pem", ".pfx", ".rar",
        ".orig", ".pyc", ".pyo", ".rej", ".so", ".sqlite", ".sqlite3", ".sqlite-shm", ".sqlite-wal", ".tar", ".tgz",
        ".xls", ".xlsm", ".xlsx", ".zip",
    }
)
FORBIDDEN_DIRECTORY_COMPONENTS = frozenset(
    {
        ".codex_private_runtime", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "cert", "certs", "credentials",
        "htmlcov", "inbox", "local_runtime", "logs", "node_modules", "private", "private_exports", "raw",
        "raw_data", "secrets", "vendor", "venv", "90_用户原始上传数据_仅本地私有_禁止提交github",
    }
)
FORBIDDEN_CREDENTIAL_BASENAMES = frozenset(
    {"client-secret.json", "client_secret.json", "credentials.json", "service-account.json", "service_account.json"}
)
FORBIDDEN_CACHE_BASENAMES = frozenset({".coverage", ".ds_store"})
FORBIDDEN_DIRECTORY_PAIRS = frozenset(
    {
        ("data", "private"), ("data", "raw"), ("exports", "private"),
        ("reports", "detail"), ("reports", "private"), ("reports", "raw"),
    }
)
SAFE_FORBIDDEN_PATH_EXCEPTIONS = frozenset(
    {
        "KMFA/metadata/dingtalk_attendance/private_runtime/.gitkeep",
        "KMFA/metadata/dingtalk_attendance/private_runtime/README.md",
        "KMFA/metadata/daily_routine_check/private_runtime/.gitkeep",
        "KMFA/metadata/daily_routine_check/private_runtime/README.md",
    }
)

IGNORE_PROBES = (
    "KMFA/raw/source.XLSX",
    "KMFA/private/source.csv",
    "KMFA/private_exports/export.ZIP",
    "KMFA/exports/private/detail.csv",
    "KMFA/data/raw/source.json",
    "KMFA/raw_data/source.csv",
    "KMFA/data/private/source.json",
    "KMFA/.codex_private_runtime/receipt.json",
    "KMFA/local_runtime/reports/detail.json",
    "KMFA/runtime.LOG",
    "KMFA/source.XLSM",
    "KMFA/cache.SQLITE3",
    "KMFA/private-key.PEM",
    "KMFA/client.P12",
    "KMFA/.env",
    "KMFA/.env.production",
    "KMFA/node_modules/package/index.js",
    "KMFA/vendor/runtime.so",
    "KMFA/logs/runtime.txt",
    "KMFA/reports/detail/full.csv",
    "KMFA/inbox/90_用户原始上传数据_仅本地私有_禁止提交GitHub/source.csv",
    "KMFA/reports/private/detail.csv",
    "KMFA/credentials/service-account.json",
    "KMFA/inbox/source.csv",
    "KMFA/runtime.so",
    "KMFA/runtime.dll",
    "KMFA/runtime.dylib",
    "KMFA/source.doc",
    "KMFA/source.docx",
    "KMFA/archive.gz",
    "KMFA/metadata/baseline/private_payload.bin",
    "KMFA/metadata/baseline/private_payload.dat",
    "KMFA/.DS_Store",
    "KMFA/tools/.pytest_cache/state.json",
    "KMFA/metadata/baseline/temporary.bak",
    "KMFA/metadata/baseline/merge.orig",
    "KMFA/metadata/baseline/conflict.rej",
)
NON_IGNORED_PUBLIC_PROBES = (
    "KMFA/metadata/protocol/public_safe_example.json",
    "KMFA/tools/public_safe_example.py",
    "KMFA/tests/test_public_safe_example.py",
)

_SECRET_KEY_PATTERN = (
    rb"(?:api[_-]?key|client[_-]?secret|credentials?|password|passwd|private[_-]?key|secret|token|"
    rb"(?:access|auth|bearer|refresh|session)[_-]?token|webhook[_-]?url)"
)
_QUOTED_ASSIGNMENT_RE = re.compile(
    rb"(?<![A-Za-z0-9_-])(?:[\"']" + _SECRET_KEY_PATTERN + rb"[\"']|" + _SECRET_KEY_PATTERN + rb")"
    rb"(?![A-Za-z0-9_-])\s*[:=]\s*(?P<quote>[\"'])(?P<value>[^\"'\r\n]{1,})(?P=quote)",
    re.IGNORECASE | re.MULTILINE,
)
_BARE_ASSIGNMENT_RE = re.compile(
    rb"(?<![A-Za-z0-9_-])(?:[\"']" + _SECRET_KEY_PATTERN + rb"[\"']|" + _SECRET_KEY_PATTERN + rb")"
    rb"(?![A-Za-z0-9_-])\s*(?P<separator>[:=])\s*(?![=\"'])(?P<value>"
    rb"\$\{[A-Za-z_][A-Za-z0-9_]*\}|\{\{\s*[A-Za-z_][A-Za-z0-9_]*\s*\}\}|"
    rb"<[A-Za-z_][A-Za-z0-9_-]*>|[A-Za-z0-9/+.!_$:@~()\[\]{}<>=?-]{1,})"
    rb"(?=$|[\t ,;#}\]\r\n])",
    re.IGNORECASE | re.MULTILINE,
)
_AUTHORIZATION_BEARER_RE = re.compile(
    rb"(?<![A-Za-z0-9_-])authorization(?![A-Za-z0-9_-])\s*[:=]\s*"
    rb"(?P<quote>[\"']?)bearer\s+(?P<value>[A-Za-z0-9._~+/=-]{4,})(?P=quote)",
    re.IGNORECASE | re.MULTILINE,
)
_PRIVATE_KEY_RE = re.compile(
    rb"-----BEGIN ((?:RSA |EC |OPENSSH )?PRIVATE KEY)-----"
    rb"\s+[A-Za-z0-9+/=\r\n]{64,}\s+-----END \1-----",
    re.DOTALL,
)
_KNOWN_TOKEN_RES = (
    re.compile(rb"s" + rb"k-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{50,}"),
    re.compile(rb"AKIA[A-Z0-9]{16}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(rb"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)
_PLACEHOLDER_RES = (
    re.compile(
        rb"^(?:example|placeholder|redacted|dummy|fake|sample|synthetic|test-only|"
        rb"not-a-secret|changeme)(?:[-_][A-Za-z0-9_-]+)*$",
        re.IGNORECASE,
    ),
    re.compile(rb"^(?:your|replace|insert)(?:[-_][A-Za-z0-9]+)+$", re.IGNORECASE),
    re.compile(rb"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$"),
    re.compile(rb"^\{\{\s*[A-Za-z_][A-Za-z0-9_]*\s*\}\}$"),
    re.compile(rb"^<[A-Za-z_][A-Za-z0-9_-]*>$"),
    re.compile(rb"^ENV::[A-Za-z_][A-Za-z0-9_]*$", re.IGNORECASE),
    re.compile(rb"^hmac-sha256:[0-9a-f]{64}$"),
    re.compile(
        rb"^(?:sk-|gh[pousr]_|xox[baprs]-)?(?:example|placeholder|dummy|fake|sample|synthetic|test-only)"
        rb"[-_][A-Za-z0-9_-]+$",
        re.IGNORECASE,
    ),
)
_CODE_REFERENCE_SUFFIXES = frozenset({".js", ".jsx", ".py", ".ts", ".tsx"})
_ABSOLUTE_PATH_RE = re.compile(
    r"^(?:/[Uu]sers/|/[Vv]olumes/|/home/|/tmp/|~[/\\]|[A-Za-z]:[/\\]|file://)",
    re.IGNORECASE,
)
_ABSOLUTE_PATH_ANY_RE = re.compile(
    r"(?:^|(?<=[\s\"'`(=:\[]))(?:/[Uu]sers/|/[Vv]olumes/|/home/|/tmp/|~[/\\]|"
    r"[A-Za-z]:[/\\]|file://)",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_{}|~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PUBLIC_REF_RE = re.compile(
    r"^KMFA/(?:metadata|stage_artifacts|docs|tools|tests|taskpack)/[^\x00-\x1f\x7f]+$"
)
_PUBLIC_ID_RE = re.compile(r"^PUB-[A-Z0-9]{12,64}$")
_PUBLIC_IDENTITY_REF_RE = re.compile(
    r"^(?:ROLE|TARGET|PERSON|PRIVATE-REGISTRY)::[A-Z0-9][A-Z0-9_.:-]{0,95}$"
)
_OPAQUE_TOKEN_RE = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

_RAW_FILENAME_KEYS = frozenset(
    {
        "filename", "file_name", "original_filename", "public_inventory_path",
        "raw_filename", "raw_name", "source_filename", "source_name", "source_zip_path",
        "member_name", "member_path",
    }
)
_IDENTITY_DETAIL_KEYS = frozenset(
    {
        "candidate_label", "customer_name", "customer_name_plaintext", "employee_name",
        "legal_name", "person_name", "project_name", "project_name_plaintext", "supplier_name",
    }
)
_MONEY_ACCOUNT_DETAIL_KEYS = frozenset(
    {
        "account_number", "amount", "amount_cents", "amount_yuan", "bank_account_number",
        "contract_amount", "invoice_amount", "salary", "tax_amount", "wage",
    }
)
_PRIVATE_DIGEST_KEYS = frozenset(
    {
        "blob_sha256", "file_hash", "member_path_hash", "member_sha256", "private_hash",
        "private_sha256", "raw_hash", "raw_sha256", "source_hash", "source_sha256",
    }
)
_CREDENTIAL_KEYS = frozenset(
    {
        "api_key", "access_token", "auth_token", "client_secret", "credential",
        "credentials", "password", "private_key", "refresh_token", "secret", "session_token",
    }
)

_RAW_FILENAME_ALIASES = frozenset(
    {
        "document_filename", "input_file_name", "input_filename", "source_file_path",
        "source_path", "upload_filename", "upload_name", "文件名", "原始文件名", "原文件名",
        "源文件名", "上传文件名",
    }
)
_IDENTITY_DETAIL_ALIASES = frozenset(
    {
        "client", "client_name", "customer", "customer_label", "employee", "employee_label",
        "known_no_record_names", "notification_owner_label", "notify_target_label", "party_name",
        "project_label", "recipient_name", "sender_name", "supplier", "vendor", "vendor_name", "人员姓名", "供应商",
        "供应商名称", "员工", "员工姓名", "姓名", "客户", "客户名称", "客户名", "项目", "项目名称",
        "项目名",
    }
)
_MONEY_ACCOUNT_DETAIL_ALIASES = frozenset(
    {
        "account", "balance", "contract_value", "invoice_total", "money", "price", "total_amount",
        "total", "total_value", "value_amount", "余额", "合同金额", "工资", "税额", "薪资", "金额", "银行账号",
        "银行账户", "发票金额",
    }
)
_PRIVATE_DIGEST_ALIASES = frozenset({"checksum", "digest", "hash"})
_PUBLIC_GOVERNANCE_DIGEST_KEYS = frozenset(
    {
        "source_snapshot_hash", "source_tree_hash", "validation_subject_sha256",
    }
)
_PUBLIC_ARTIFACT_REF_KEYS = ("artifact_ref", "public_artifact_ref", "ref", "target_path")
_PUBLIC_ARTIFACT_DIGEST_KEYS = ("artifact_sha256", "sha256")
_RAW_FILE_VALUE_RE = re.compile(
    r"(?:^|[/\\])[^/\\]+\.(?:csv|db|docx?|pdf|sqlite3?|xlsm?|xlsx|zip)$",
    re.IGNORECASE,
)
_SHA256_VALUE_RE = re.compile(r"(?:^|:)sha256:[0-9a-f]{64}(?:$|:)", re.IGNORECASE)
_HEX_DIGEST_VALUE_RE = re.compile(r"^[0-9a-f]{8,128}$", re.IGNORECASE)
_PUBLIC_METADATA_ALLOWED_SUFFIXES = frozenset(
    {".csv", ".json", ".jsonl", ".md", ".sql", ".toml", ".txt", ".yaml", ".yml"}
)

PUBLIC_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version", "record_type", "project_id", "target_release", "stage_id", "run_id",
        "phase_id", "public_record_id", "subject_class", "status", "aggregate_counts",
        "public_flags", "policy_refs", "evidence_refs", "public_artifact_digests",
        "opaque_tokens",
    }
)
PUBLIC_ENVELOPE_RECORD_TYPES = frozenset(
    {
        "public_safe_schema", "public_safe_deidentified_manifest", "public_safe_status",
        "public_safe_rule", "public_safe_aggregate_evidence", "public_safe_artifact_hash_index",
        "dual_plane_public_projection",
    }
)
PUBLIC_STATUS_VALUES = frozenset({"PASS", "FAIL", "PENDING", "NOT_APPLICABLE"})
PUBLIC_ARTIFACT_DIGEST_FIELDS = frozenset({"artifact_ref", "sha256"})
OPAQUE_TOKEN_FIELDS = frozenset({"token_type", "token"})
OPAQUE_TOKEN_TYPES = frozenset(
    {"source_locator", "party_label", "money_detail", "credential_material", "private_record"}
)


class SafetyError(RuntimeError):
    """Fail-closed public repository safety error."""


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    category: str
    detail: str


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _git(args: Sequence[str], *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=REPO_ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_output(args: Sequence[str]) -> bytes:
    result = _git(args)
    if result.returncode != 0:
        raise SafetyError(
            f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return result.stdout


def _looks_placeholder(value: bytes) -> bool:
    lowered = value.strip().lower()
    if lowered in {
        b"", b"0", b"absent", b"disabled", b"false", b"none", b"not_applicable", b"null", b"~"
    } or re.fullmatch(rb"0(?:/0)+", lowered):
        return True
    return any(pattern.fullmatch(value.strip()) for pattern in _PLACEHOLDER_RES)


def _looks_bare_code_reference(path: str, value: bytes) -> bool:
    if PurePosixPath(path).suffix.casefold() not in _CODE_REFERENCE_SUFFIXES:
        return False
    candidate = value.rstrip(b")]}")
    if re.fullmatch(rb"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*", candidate):
        return True
    return re.match(
        rb"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*[\[(]",
        candidate,
    ) is not None


def scan_payload_for_secrets(path: str, payload: bytes) -> list[Finding]:
    findings: list[Finding] = []
    candidates = [payload]
    try:
        normalized = unicodedata.normalize("NFKC", payload.decode("utf-8")).encode("utf-8")
    except UnicodeDecodeError:
        normalized = payload
    if normalized != payload:
        candidates.append(normalized)
    if any(_PRIVATE_KEY_RE.search(candidate) for candidate in candidates):
        findings.append(Finding(path, "credential_or_secret", "private key material"))
    for pattern in _KNOWN_TOKEN_RES:
        if any(
            not _looks_placeholder(match.group(0))
            for candidate in candidates
            for match in pattern.finditer(candidate)
        ):
            findings.append(Finding(path, "credential_or_secret", "high-signal token material"))
            break
    for candidate in candidates:
        for match in _AUTHORIZATION_BEARER_RE.finditer(candidate):
            if not _looks_placeholder(match.group("value")):
                findings.append(Finding(path, "credential_or_secret", "authorization bearer material"))
                return sorted(set(findings))
    for candidate in candidates:
        for pattern in (_QUOTED_ASSIGNMENT_RE, _BARE_ASSIGNMENT_RE):
            for match in pattern.finditer(candidate):
                value = match.group("value")
                is_bare_code_reference = pattern is _BARE_ASSIGNMENT_RE and (
                    _looks_bare_code_reference(path, value)
                    or (
                        PurePosixPath(path).suffix.casefold() in _CODE_REFERENCE_SUFFIXES
                        and match.group("separator") == b":"
                    )
                )
                if not _looks_placeholder(value) and not is_bare_code_reference:
                    findings.append(Finding(path, "credential_or_secret", "non-placeholder secret assignment"))
                    return sorted(set(findings))
    return findings


def scan_repository_path(path: str) -> list[Finding]:
    normalized_text = unicodedata.normalize("NFKC", path.replace("\\", "/"))
    normalized = PurePosixPath(normalized_text)
    parts = normalized.parts
    if path in SAFE_FORBIDDEN_PATH_EXCEPTIONS:
        return []
    findings: list[Finding] = []
    lowered_parts = tuple(part.casefold() for part in parts)
    if any(part in FORBIDDEN_DIRECTORY_COMPONENTS for part in lowered_parts):
        findings.append(Finding(path, "forbidden_path", "private/raw/runtime directory component"))
    if any(pair in zip(lowered_parts, lowered_parts[1:]) for pair in FORBIDDEN_DIRECTORY_PAIRS):
        findings.append(Finding(path, "forbidden_path", "private/raw report or export path"))
    lowered_name = normalized.name.casefold()
    if lowered_name == ".env" or lowered_name.startswith(".env."):
        if lowered_name != ".env.example":
            findings.append(Finding(path, "credential_or_secret", "local environment file"))
    if lowered_name in FORBIDDEN_CREDENTIAL_BASENAMES:
        findings.append(Finding(path, "credential_or_secret", "credential configuration filename"))
    if lowered_name in FORBIDDEN_CACHE_BASENAMES:
        findings.append(Finding(path, "forbidden_path", "local cache or operating-system metadata"))
    if lowered_name.endswith("~"):
        findings.append(Finding(path, "forbidden_suffix", "editor backup file suffix"))
    if any(lowered_name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        findings.append(Finding(path, "forbidden_suffix", "raw/archive/runtime/credential file suffix"))
    if (
        len(parts) == 2
        and parts[0] == "KMFA"
        and normalized.suffix.casefold() in {".bin", ".csv", ".dat", ".json", ".jsonl", ".toml", ".yaml", ".yml"}
    ):
        findings.append(Finding(path, "unapproved_root_data_path", "structured data is not allowed at project root"))
    return findings


def scan_candidate(path: str, payload: bytes, *, mode: int | None = None, nlink: int | None = None) -> list[Finding]:
    findings = scan_repository_path(path)
    if mode is not None and stat.S_ISLNK(mode):
        findings.append(Finding(path, "filesystem_alias", "symbolic link is not committable"))
    if mode is not None and stat.S_IFMT(mode) == 0o160000:
        findings.append(Finding(path, "filesystem_alias", "gitlink is not committable"))
    if nlink is not None and nlink != 1:
        findings.append(Finding(path, "filesystem_alias", "hard-linked file is not committable"))
    if len(payload) > MAX_SCANNED_FILE_BYTES:
        findings.append(Finding(path, "oversize_blob", "file exceeds deterministic scan limit"))
        return sorted(set(findings))
    text_suffixes = {".csv", ".css", ".html", ".js", ".json", ".jsonl", ".md", ".py", ".sh", ".toml", ".ts", ".txt", ".yaml", ".yml"}
    if PurePosixPath(path).suffix.casefold() in text_suffixes and b"\0" in payload:
        findings.append(Finding(path, "binary_text_payload", "text-like file contains NUL bytes"))
    findings.extend(scan_payload_for_secrets(path, payload))
    normalized_path = path.replace("\\", "/")
    legacy_plain_text_suffixes = {".md", ".sql", ".txt"}
    if (
        normalized_path.startswith(CURRENT_PUBLIC_EVIDENCE_PREFIX)
        or (
            normalized_path.startswith("KMFA/metadata/")
            and PurePosixPath(path).suffix.casefold() not in legacy_plain_text_suffixes
        )
    ):
        findings.extend(audit_public_metadata_bytes(path, payload))
    return sorted(set(findings))


def _candidate_worktree_paths() -> list[str]:
    payload = _git_output(["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "KMFA"])
    return sorted({part.decode("utf-8") for part in payload.split(b"\0") if part})


def _parse_git_mode_entries(payload: bytes) -> list[tuple[str, int, str]]:
    entries: list[tuple[str, int, str]] = []
    for raw_entry in payload.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            fields = metadata.split()
            mode_text = fields[0]
            object_id = next(
                field.decode("ascii")
                for field in fields[1:]
                if len(field) in {40, 64} and all(character in b"0123456789abcdef" for character in field)
            )
            entries.append((raw_path.decode("utf-8"), int(mode_text, 8), object_id))
        except (ValueError, UnicodeDecodeError) as error:
            raise SafetyError("cannot parse git tree/index entry") from error
    return sorted(entries)


def _candidate_index_entries() -> list[tuple[str, int, str]]:
    return _parse_git_mode_entries(_git_output(["ls-files", "-s", "-z", "--cached", "--", "KMFA"]))


def _candidate_head_entries() -> list[tuple[str, int, str]]:
    return _parse_git_mode_entries(_git_output(["ls-tree", "-r", "-z", "HEAD", "--", "KMFA"]))


def _read_git_blobs(entries: Sequence[tuple[str, int, str]]) -> dict[str, bytes]:
    object_ids = sorted({object_id for _, mode, object_id in entries if stat.S_IFMT(mode) != 0o160000})
    request = b"".join(object_id.encode("ascii") + b"\n" for object_id in object_ids)
    result = _git(["cat-file", "--batch"], input_bytes=request)
    if result.returncode != 0:
        raise SafetyError("git cat-file --batch failed")
    output = result.stdout
    position = 0
    blobs: dict[str, bytes] = {}
    for requested_id in object_ids:
        header_end = output.find(b"\n", position)
        if header_end < 0:
            raise SafetyError("truncated git cat-file batch header")
        header = output[position:header_end].split()
        position = header_end + 1
        if len(header) != 3 or header[1] != b"blob":
            raise SafetyError(f"unexpected git object for repository file: {requested_id}")
        size = int(header[2])
        payload = output[position : position + size]
        position += size
        if len(payload) != size or output[position : position + 1] != b"\n":
            raise SafetyError("truncated git cat-file batch payload")
        position += 1
        blobs[requested_id] = payload
    if position != len(output):
        raise SafetyError("unexpected trailing git cat-file batch output")
    return blobs


def scan_repository(*, scope: str = "worktree") -> tuple[int, list[Finding]]:
    if scope not in {"head", "index", "worktree"}:
        raise SafetyError(f"unsupported repository scan scope: {scope}")
    if scope == "worktree":
        entries = [(path, None, None) for path in _candidate_worktree_paths()]
    elif scope == "index":
        entries = _candidate_index_entries()
    else:
        entries = _candidate_head_entries()
    git_blobs = _read_git_blobs(entries) if scope in {"head", "index"} else {}
    findings: list[Finding] = []
    scanned = 0
    for path, git_mode, object_id in entries:
        if scope in {"head", "index"}:
            payload = b"" if stat.S_IFMT(int(git_mode or 0)) == 0o160000 else git_blobs.get(str(object_id), b"")
            if object_id is None or (not payload and stat.S_IFMT(int(git_mode or 0)) != 0o160000 and object_id not in git_blobs):
                findings.append(Finding(path, "unreadable_git_blob", f"cannot read {scope} blob"))
                continue
            mode = git_mode
            nlink = None
        else:
            try:
                metadata, payload = read_repository_candidate(path)
            except FileNotFoundError:
                continue
            except SafetyError:
                findings.append(
                    Finding(path, "filesystem_alias", "repository path has an unsafe ancestor")
                )
                scanned += 1
                continue
            mode = metadata.st_mode
            nlink = metadata.st_nlink
        findings.extend(scan_candidate(path, payload, mode=mode, nlink=nlink))
        scanned += 1
    return scanned, sorted(set(findings))


def verify_gitignore_contract() -> dict[str, Any]:
    blocked: list[str] = []
    missed: list[str] = []
    for path in IGNORE_PROBES:
        result = _git(["check-ignore", "--no-index", "-q", "--", path])
        (blocked if result.returncode == 0 else missed).append(path)
    wrongly_ignored: list[str] = []
    for path in NON_IGNORED_PUBLIC_PROBES:
        if _git(["check-ignore", "--no-index", "-q", "--", path]).returncode == 0:
            wrongly_ignored.append(path)
    return {
        "probe_count": len(IGNORE_PROBES),
        "blocked_count": len(blocked),
        "missed_count": len(missed),
        "public_probe_count": len(NON_IGNORED_PUBLIC_PROBES),
        "wrongly_ignored_public_count": len(wrongly_ignored),
        "pass": not missed and not wrongly_ignored,
        "missed_categories": sorted({PurePosixPath(path).suffix.casefold() or "path" for path in missed}),
    }


def _validate_public_ref(value: Any, *, label: str) -> None:
    if not isinstance(value, str):
        raise SafetyError(f"{label} must be a public repository-relative ref")
    if "\\" in value or unicodedata.normalize("NFKC", value) != value:
        raise SafetyError(f"{label} must use a normalized POSIX repository path")
    normalized = PurePosixPath(value)
    if (
        normalized.is_absolute()
        or any(part in {".", "..", ""} for part in value.split("/"))
        or str(normalized) != value
        or not _PUBLIC_REF_RE.fullmatch(value)
    ):
        raise SafetyError(f"{label} must be a public repository-relative ref")
    if scan_repository_path(value):
        raise SafetyError(f"{label} points into a forbidden public path")


def _read_tracked_public_artifact_blob(value: str, *, label: str) -> bytes:
    _validate_public_ref(value, label=label)
    tracked = _git(["ls-files", "--error-unmatch", "--", value])
    if tracked.returncode != 0:
        raise SafetyError(f"{label} must reference a tracked public artifact")
    try:
        return read_repository_file(value)
    except (FileNotFoundError, NotADirectoryError, OSError, ValueError, SafetyError) as error:
        raise SafetyError(f"{label} must reference an existing repository blob") from error


def _validate_public_artifact_digest(value: Mapping[str, Any], *, label: str) -> None:
    artifact_ref = value.get("artifact_ref")
    digest = value.get("sha256")
    _validate_public_ref(artifact_ref, label=f"{label}.artifact_ref")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise SafetyError(f"{label}.sha256 invalid")
    blob = _read_tracked_public_artifact_blob(artifact_ref, label=f"{label}.artifact_ref")
    if sha256_digest(blob) != digest:
        raise SafetyError(f"{label}.sha256 does not match the referenced public artifact blob")


def _validate_safe_named_mapping(value: Any, *, label: str, value_type: type) -> None:
    if not isinstance(value, dict):
        raise SafetyError(f"{label} must be an object")
    for key, item in value.items():
        if not isinstance(key, str) or not _SAFE_KEY_RE.fullmatch(key):
            raise SafetyError(f"{label} contains an invalid key")
        if key in (_RAW_FILENAME_KEYS | _IDENTITY_DETAIL_KEYS | _MONEY_ACCOUNT_DETAIL_KEYS | _PRIVATE_DIGEST_KEYS | _CREDENTIAL_KEYS):
            raise SafetyError(f"{label} contains forbidden detail key: {key}")
        if type(item) is not value_type:  # bool is intentionally not accepted as int.
            raise SafetyError(f"{label}.{key} must be {value_type.__name__}")
        if value_type is int and item < 0:
            raise SafetyError(f"{label}.{key} must be non-negative")


def validate_public_metadata_envelope(
    record: Mapping[str, Any], *, require_tracked_refs: bool = True
) -> None:
    if not isinstance(record, Mapping):
        raise SafetyError("public metadata envelope must be an object")
    keys = set(record)
    if keys != PUBLIC_ENVELOPE_FIELDS:
        raise SafetyError(
            f"public metadata envelope fields drift: missing={sorted(PUBLIC_ENVELOPE_FIELDS - keys)} "
            f"unknown={sorted(keys - PUBLIC_ENVELOPE_FIELDS)}"
        )
    expected_scalars = {
        "schema_version": PUBLIC_ENVELOPE_VERSION,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S03",
        "phase_id": "S03-P3",
    }
    for key, expected in expected_scalars.items():
        if record.get(key) != expected:
            raise SafetyError(f"public metadata {key} drift")
    if record.get("record_type") not in PUBLIC_ENVELOPE_RECORD_TYPES:
        raise SafetyError("public metadata record_type is not allowed")
    if not isinstance(record.get("run_id"), str) or not re.fullmatch(r"[0-9a-f]{32}", str(record["run_id"])):
        raise SafetyError("public metadata run_id must be 32 lowercase hex characters")
    if not isinstance(record.get("public_record_id"), str) or not _PUBLIC_ID_RE.fullmatch(str(record["public_record_id"])):
        raise SafetyError("public_record_id must be an opaque public identifier")
    if record.get("subject_class") not in COMMITTABLE_METADATA_CLASSES:
        raise SafetyError("public metadata subject_class is not allowed")
    if record.get("status") not in PUBLIC_STATUS_VALUES:
        raise SafetyError("public metadata status is not allowed")
    _validate_safe_named_mapping(record.get("aggregate_counts"), label="aggregate_counts", value_type=int)
    _validate_safe_named_mapping(record.get("public_flags"), label="public_flags", value_type=bool)
    for field in ("policy_refs", "evidence_refs"):
        values = record.get(field)
        if not isinstance(values, list) or not values:
            raise SafetyError(f"{field} must be a non-empty list")
        for index, value in enumerate(values):
            label = f"{field}[{index}]"
            if require_tracked_refs:
                _read_tracked_public_artifact_blob(value, label=label)
            else:
                _validate_public_ref(value, label=label)
    digests = record.get("public_artifact_digests")
    if not isinstance(digests, list):
        raise SafetyError("public_artifact_digests must be a list")
    for index, item in enumerate(digests):
        if not isinstance(item, dict) or set(item) != PUBLIC_ARTIFACT_DIGEST_FIELDS:
            raise SafetyError(f"public_artifact_digests[{index}] fields drift")
        _validate_public_artifact_digest(item, label=f"public_artifact_digests[{index}]")
    opaque = record.get("opaque_tokens")
    if not isinstance(opaque, list) or not opaque:
        raise SafetyError("opaque_tokens must be a non-empty list")
    for index, item in enumerate(opaque):
        if not isinstance(item, dict) or set(item) != OPAQUE_TOKEN_FIELDS:
            raise SafetyError(f"opaque_tokens[{index}] fields drift")
        if item.get("token_type") not in OPAQUE_TOKEN_TYPES:
            raise SafetyError(f"opaque_tokens[{index}].token_type invalid")
        if not isinstance(item.get("token"), str) or not _OPAQUE_TOKEN_RE.fullmatch(item["token"]):
            raise SafetyError(f"opaque_tokens[{index}].token invalid")
    serialized = _canonical_json_bytes(record)
    if scan_payload_for_secrets("public_metadata_envelope", serialized):
        raise SafetyError("public metadata envelope contains secret-like material")
    for value in _walk_scalars(record):
        if isinstance(value, str) and (_ABSOLUTE_PATH_RE.match(value) or _EMAIL_RE.fullmatch(value)):
            raise SafetyError("public metadata envelope contains absolute path or email")


def _walk_scalars(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_scalars(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_scalars(child)
    else:
        yield value


def _normalized_metadata_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    return re.sub(r"[-\s]+", "_", normalized)


def _meaningful_public_detail(value: Any) -> bool:
    return value not in (None, "", False)


def _plaintext_identity_detail(key: str, value: Any, field_path: str) -> bool:
    context = field_path.casefold()
    if any(marker in context for marker in ("normalization_rules", "schema", "field_dictionary")):
        return False
    if key in {"project_name", "项目名"} and isinstance(value, str) and value.strip().startswith("KMFA"):
        return False
    if isinstance(value, str):
        candidate = value.strip()
        return bool(candidate) and _PUBLIC_IDENTITY_REF_RE.fullmatch(candidate) is None
    if isinstance(value, list):
        return any(_plaintext_identity_detail(key, item, field_path) for item in value)
    return False


def _money_detail(value: Any, field_path: str) -> bool:
    if any(marker in field_path.casefold() for marker in ("count_by_field", "normalization_rules", "schema")):
        return False
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        candidate = value.strip().replace(",", "")
        return re.fullmatch(r"(?:[A-Z]{3}\s*)?[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:\s*[元$¥])?", candidate) is not None
    if isinstance(value, list):
        return any(_money_detail(item, field_path) for item in value)
    return False


def _private_digest_key(key: str) -> bool:
    if key in _PUBLIC_GOVERNANCE_DIGEST_KEYS or key.endswith("_commit"):
        return False
    if key in (_PRIVATE_DIGEST_KEYS | _PRIVATE_DIGEST_ALIASES):
        return True
    sensitive_prefix = (
        r"(?:raw|private|source|member|header|sheet|payload|input|upload|file|amount|cost|"
        r"revenue|cash|salary|tax|invoice|contract|customer|project|party|account|name)"
    )
    return re.fullmatch(
        rf".*{sensitive_prefix}.*(?:hash|sha256|digest|checksum|fingerprint)", key
    ) is not None


def _digest_shaped_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    return _SHA256_VALUE_RE.search(candidate) is not None or _HEX_DIGEST_VALUE_RE.fullmatch(candidate) is not None


def _is_existing_public_commit_ref(key: str, value: Any) -> bool:
    if key != "source_commit" and not key.endswith("_uploaded_commit"):
        return False
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40,64}", value) is None:
        return False
    return _git(["cat-file", "-e", f"{value}^{{commit}}"] ).returncode == 0


def _normalized_sha256(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip().casefold()
    if re.fullmatch(r"[0-9a-f]{64}", candidate):
        return "sha256:" + candidate
    if _SHA256_RE.fullmatch(candidate):
        return candidate
    return None


def _validated_public_artifact_digest_keys(
    value: Mapping[str, Any], *, path: str, field_path: str, findings: list[Finding]
) -> set[str]:
    ref_item = next(
        (
            (key, value[key])
            for key in _PUBLIC_ARTIFACT_REF_KEYS
            if key in value and isinstance(value[key], str)
        ),
        None,
    )
    if ref_item is None:
        return set()
    _, artifact_ref = ref_item
    validated: set[str] = set()
    for raw_digest_key in _PUBLIC_ARTIFACT_DIGEST_KEYS:
        if raw_digest_key not in value:
            continue
        digest = _normalized_sha256(value[raw_digest_key])
        detail = f"{field_path}.{raw_digest_key}"
        try:
            blob = _read_tracked_public_artifact_blob(
                artifact_ref, label=f"{field_path}.{ref_item[0]}"
            )
        except SafetyError:
            findings.append(Finding(path, "public_artifact_hash_binding", detail))
            continue
        if digest is None or sha256_digest(blob) != digest:
            findings.append(Finding(path, "public_artifact_hash_binding", detail))
            continue
        validated.add(_normalized_metadata_key(raw_digest_key))
    return validated


def _source_like_hash_value(key: str, field_path: str, value: Any) -> bool:
    if (
        key in _PUBLIC_GOVERNANCE_DIGEST_KEYS
        or _is_existing_public_commit_ref(key, value)
        or not _digest_shaped_string(value)
    ):
        return False
    context = f"{field_path}.{key}".casefold()
    return any(
        marker in context
        for marker in (
            "private", "raw", "source", "member", "header", "sheet", "payload",
            "metric_hash", "fact_hash", "input", "upload", "identity", "customer",
            "candidate", "amount", "cost", "revenue", "cash", "salary", "invoice",
            "contract", "party", "account",
        )
    ) and "public_artifact" not in context


def _raw_filename_detail(key: str, value: Any) -> bool:
    if not _meaningful_public_detail(value):
        return False
    if key in (_RAW_FILENAME_KEYS | _RAW_FILENAME_ALIASES):
        return True
    return (
        key in {"document", "file", "input", "path", "source", "upload"}
        and isinstance(value, str)
        and _RAW_FILE_VALUE_RE.search(value.strip()) is not None
    )


def audit_structured_public_value(value: Any, *, path: str, field_path: str = "$") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(value, Mapping):
        validated_public_digest_keys = _validated_public_artifact_digest_keys(
            value, path=path, field_path=field_path, findings=findings
        )
        for raw_key, child in value.items():
            key = _normalized_metadata_key(raw_key)
            child_path = f"{field_path}.{raw_key}"
            if _raw_filename_detail(key, child):
                findings.append(Finding(path, "raw_or_source_filename", child_path))
            if key in (_IDENTITY_DETAIL_KEYS | _IDENTITY_DETAIL_ALIASES) and _plaintext_identity_detail(
                key, child, field_path
            ):
                findings.append(Finding(path, "person_customer_or_project_detail", child_path))
            if key in (_MONEY_ACCOUNT_DETAIL_KEYS | _MONEY_ACCOUNT_DETAIL_ALIASES) and _money_detail(
                child, field_path
            ):
                findings.append(Finding(path, "money_account_or_tax_detail", child_path))
            if (
                key not in validated_public_digest_keys
                and (_private_digest_key(key) or key in _CREDENTIAL_KEYS)
                and _meaningful_public_detail(child)
                and (
                    key in _CREDENTIAL_KEYS
                    or _digest_shaped_string(child)
                )
            ) or (
                key not in validated_public_digest_keys
                and _source_like_hash_value(key, field_path, child)
            ):
                findings.append(Finding(path, "credential_or_private_hash", child_path))
            findings.extend(audit_structured_public_value(child, path=path, field_path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(audit_structured_public_value(child, path=path, field_path=f"{field_path}[{index}]"))
    elif isinstance(value, str):
        if _ABSOLUTE_PATH_ANY_RE.search(value):
            findings.append(Finding(path, "absolute_local_path", field_path))
    return sorted(set(findings))


def audit_json_or_jsonl_bytes(path: str, payload: bytes) -> list[Finding]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return [Finding(path, "structured_parse", "non-UTF-8 structured metadata")]
    rows: list[Any] = []
    try:
        if path.endswith(".jsonl"):
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            rows = [json.loads(text)]
    except (json.JSONDecodeError, TypeError):
        return [Finding(path, "structured_parse", "invalid JSON/JSONL")]
    findings: list[Finding] = []
    for index, row in enumerate(rows):
        findings.extend(audit_structured_public_value(row, path=path, field_path=f"$[{index}]"))
    return sorted(set(findings))


def _decode_public_metadata_text(path: str, payload: bytes) -> tuple[str | None, list[Finding]]:
    if b"\0" in payload:
        return None, [Finding(path, "metadata_format", "public metadata contains NUL bytes")]
    try:
        return payload.decode("utf-8"), []
    except UnicodeDecodeError:
        return None, [Finding(path, "metadata_format", "public metadata must be UTF-8 text")]


def _scalar_for_structured_audit(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith(("\"", "'")) and value.endswith(value[:1]) and len(value) >= 2:
        return value[1:-1]
    lowered = value.casefold()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered in {"false", "true"}:
        return lowered == "true"
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", value):
        return float(value)
    return value


def _audit_line_mapping_bytes(path: str, payload: bytes, *, toml: bool) -> list[Finding]:
    text, findings = _decode_public_metadata_text(path, payload)
    if text is None:
        return findings
    if not toml and text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [Finding(path, "structured_parse", "invalid JSON-compatible YAML")]
        return audit_structured_public_value(parsed, path=path)
    if "\t" in text:
        findings.append(Finding(path, "structured_parse", "tabs are not allowed in public YAML/TOML"))
    pattern = re.compile(
        r"^\s*(?:-\s*)?(?P<key>[A-Za-z0-9_\- .\u0080-\uffff\"']+)\s*"
        + (r"=" if toml else r":")
        + r"\s*(?P<value>.*)$"
    )
    lines = text.splitlines()
    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        line_number = line_index + 1
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or (toml and stripped.startswith("[")):
            line_index += 1
            continue
        match = pattern.match(line)
        if match is None:
            line_index += 1
            continue
        raw_key = match.group("key").strip().strip("\"'")
        key = raw_key.rsplit(".", 1)[-1].strip().strip("\"'") if toml else raw_key
        raw_value = match.group("value").strip()
        scalar: Any
        if not toml and re.fullmatch(r"[>|][+-]?", raw_value):
            base_indent = len(line) - len(line.lstrip(" "))
            block_lines: list[str] = []
            cursor = line_index + 1
            while cursor < len(lines):
                child = lines[cursor]
                child_indent = len(child) - len(child.lstrip(" "))
                if child.strip() and child_indent <= base_indent:
                    break
                block_lines.append(child.strip())
                cursor += 1
            scalar = "\n".join(block_lines)
            line_index = cursor
        elif raw_value.startswith("{"):
            try:
                scalar = json.loads(raw_value)
            except json.JSONDecodeError:
                findings.append(
                    Finding(path, "structured_parse", f"unsupported YAML/TOML flow mapping at line {line_number}")
                )
                line_index += 1
                continue
            line_index += 1
        elif raw_value.startswith("["):
            try:
                scalar = json.loads(raw_value)
            except json.JSONDecodeError:
                if not raw_value.endswith("]") or any(marker in raw_value[1:-1] for marker in "[]{}"):
                    findings.append(
                        Finding(path, "structured_parse", f"unsupported YAML/TOML flow list at line {line_number}")
                    )
                    line_index += 1
                    continue
                scalar = [
                    _scalar_for_structured_audit(item)
                    for item in raw_value[1:-1].split(",")
                    if item.strip()
                ]
            line_index += 1
        else:
            scalar = _scalar_for_structured_audit(raw_value)
            line_index += 1
        row = {key: scalar}
        findings.extend(
            audit_structured_public_value(row, path=path, field_path=f"$[line:{line_number}]")
        )
    return sorted(set(findings))


def _audit_plain_public_text_bytes(path: str, payload: bytes) -> list[Finding]:
    text, findings = _decode_public_metadata_text(path, payload)
    if text is None:
        return findings
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _ABSOLUTE_PATH_ANY_RE.search(line):
            findings.append(Finding(path, "absolute_local_path", f"$[line:{line_number}]"))
    findings.extend(_audit_line_mapping_bytes(path, payload, toml=False))
    return sorted(set(findings))


def _audit_csv_bytes(path: str, payload: bytes) -> list[Finding]:
    text, findings = _decode_public_metadata_text(path, payload)
    if text is None:
        return findings
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error:
        return [Finding(path, "structured_parse", "invalid public CSV")]
    if not rows:
        return []
    headers = [_normalized_metadata_key(header) for header in rows[0]]
    if any(not header for header in headers) or len(set(headers)) != len(headers):
        findings.append(Finding(path, "structured_parse", "CSV headers must be non-empty and unique"))
        return sorted(set(findings))
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            findings.append(Finding(path, "structured_parse", f"CSV row width drift at row {row_number}"))
            continue
        findings.extend(
            audit_structured_public_value(
                dict(zip(headers, row)), path=path, field_path=f"$[row:{row_number}]"
            )
        )
    return sorted(set(findings))


def audit_public_metadata_bytes(path: str, payload: bytes) -> list[Finding]:
    """Fail closed on unsupported metadata formats and structured private detail."""
    normalized = PurePosixPath(unicodedata.normalize("NFKC", path.replace("\\", "/")))
    suffix = normalized.suffix.casefold()
    if normalized.name in {".gitignore", ".gitkeep"}:
        _, findings = _decode_public_metadata_text(path, payload)
        return findings
    if suffix not in _PUBLIC_METADATA_ALLOWED_SUFFIXES:
        return [Finding(path, "metadata_format", f"unsupported public metadata format: {suffix or '[none]'}")]
    text, format_findings = _decode_public_metadata_text(path, payload)
    if text is None:
        return format_findings
    if suffix in {".json", ".jsonl"}:
        return audit_json_or_jsonl_bytes(path, payload)
    if suffix == ".csv":
        return _audit_csv_bytes(path, payload)
    if suffix in {".yaml", ".yml"}:
        return _audit_line_mapping_bytes(path, payload, toml=False)
    if suffix == ".toml":
        return _audit_line_mapping_bytes(path, payload, toml=True)
    return _audit_plain_public_text_bytes(path, payload)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _repository_path_parts(path: str) -> tuple[str, ...]:
    """Return a canonical project-relative path without resolving any symlink."""
    if not isinstance(path, str) or "\\" in path or unicodedata.normalize("NFKC", path) != path:
        raise SafetyError("repository path must be a normalized POSIX string")
    normalized = PurePosixPath(path)
    parts = normalized.parts
    if (
        normalized.is_absolute()
        or not parts
        or parts[0] != "KMFA"
        or str(normalized) != path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise SafetyError("repository path must stay below KMFA")
    return parts


def _open_repository_parent(path: str, *, create: bool = False) -> tuple[int, str]:
    """Open a repository parent via dirfd traversal, rejecting every symlink ancestor."""
    parts = _repository_path_parts(path)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(REPO_ROOT, flags)
    except OSError as error:
        raise SafetyError("repository root is not a safe directory") from error
    try:
        for part in parts[:-1]:
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, 0o755, dir_fd=descriptor)
                child = os.open(part, flags, dir_fd=descriptor)
            except OSError as error:
                raise SafetyError(f"unsafe repository ancestor: {path}") from error
            metadata = os.fstat(child)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(child)
                raise SafetyError(f"repository ancestor is not a directory: {path}")
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except BaseException:
        os.close(descriptor)
        raise


def read_repository_candidate(path: str) -> tuple[os.stat_result, bytes]:
    """Read one worktree candidate without following a final or ancestor symlink."""
    parent, name = _open_repository_parent(path)
    try:
        metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode):
            return metadata, b""
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(name, flags, dir_fd=parent)
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
            ):
                raise SafetyError(f"unsafe repository file type/link: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return opened, b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def read_repository_file(path: str) -> bytes:
    """Read a regular, single-link repository file through safe dirfd traversal."""
    metadata, payload = read_repository_candidate(path)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SafetyError(f"unsafe repository file type/link: {path}")
    return payload


def repository_file_exists(path: str) -> bool:
    """Check existence without treating a symlink or unsafe ancestor as absent."""
    try:
        metadata, _ = read_repository_candidate(path)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SafetyError(f"unsafe repository file type/link: {path}")
    return True


def write_repository_file(path: str, payload: bytes, *, mode: int = 0o644) -> None:
    """Write below KMFA without following aliases or truncating a hard-linked file."""
    if not isinstance(payload, bytes):
        raise SafetyError("repository payload must be bytes")
    parent, name = _open_repository_parent(path, create=True)
    descriptor: int | None = None
    try:
        flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, dir_fd=parent)
        except FileNotFoundError:
            descriptor = os.open(
                name,
                flags | os.O_CREAT | os.O_EXCL,
                mode,
                dir_fd=parent,
            )
        except OSError as error:
            raise SafetyError(f"unsafe repository output path: {path}") from error
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise SafetyError(f"unsafe repository output file type/link: {path}")
        os.ftruncate(descriptor, 0)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SafetyError(f"short repository write: {path}")
            view = view[written:]
        os.fsync(descriptor)
        os.fchmod(descriptor, mode)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _safe_private_directory(root: Path, *, allow_external_test_root: bool = False) -> Path:
    candidate = Path(os.path.abspath(root))
    allowed_bases = [PROJECT_ROOT / ".codex_private_runtime", PROJECT_ROOT / "local_runtime"]
    if allow_external_test_root:
        temp_base = Path(tempfile.gettempdir()).resolve()
        resolved_candidate = candidate.resolve(strict=False)
        if _is_relative_to(resolved_candidate, temp_base):
            candidate = resolved_candidate
        allowed_bases.append(temp_base)
    base = next((item for item in allowed_bases if _is_relative_to(candidate, item)), None)
    if base is None:
        raise SafetyError("private evidence root must stay in an approved ignored runtime")
    current = candidate
    while _is_relative_to(current, base):
        if current.exists() or current.is_symlink():
            metadata = os.lstat(current)
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise SafetyError(f"unsafe private directory: {current}")
        if current == base:
            break
        current = current.parent
    candidate.mkdir(parents=True, exist_ok=True, mode=0o700)
    resolved = candidate.resolve(strict=True)
    if not _is_relative_to(resolved, base.resolve(strict=True)):
        raise SafetyError("private evidence root escaped its approved runtime")
    os.chmod(resolved, 0o700)
    return resolved


def _read_regular_single_link(path: Path, *, expected_mode: int) -> bytes:
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SafetyError(f"unsafe private file type/link: {path}")
    if stat.S_IMODE(metadata.st_mode) != expected_mode:
        raise SafetyError(f"private file mode drift: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _create_private_file(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, mode)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SafetyError(f"short private write: {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(path, mode)


def _synthetic_private_record(run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise SafetyError("dual-plane run_id must be 32 lowercase hex characters")
    return {
        "schema_version": PRIVATE_RECEIPT_VERSION,
        "record_type": "synthetic_private_dual_plane_receipt",
        "run_id": run_id,
        "fixture_only": True,
        "raw_root_access_count": 0,
        "sensitive_values": {
            "source_locator": "synthetic-" + "source-ledger.xlsx",
            "party_label": "synthetic-" + "customer-alpha",
            "money_detail": "1274300" + ".19",
            "credential_material": "s" + "k-" + "SYNTHETICONLY" * 3,
        },
    }


def _hmac_token(key: bytes, label: str, value: bytes) -> str:
    return "hmac-sha256:" + hmac.new(key, label.encode("utf-8") + b"\0" + value, hashlib.sha256).hexdigest()


def project_public_plane(private_record: Mapping[str, Any], key: bytes) -> dict[str, Any]:
    if len(key) != 32:
        raise SafetyError("private HMAC key must be exactly 32 bytes")
    values = private_record.get("sensitive_values")
    if not isinstance(values, Mapping) or set(values) != set(OPAQUE_TOKEN_TYPES - {"private_record"}):
        raise SafetyError("private sensitive-value fixture drift")
    canonical_private = _canonical_json_bytes(private_record)
    tokens = [
        {"token_type": label, "token": _hmac_token(key, label, str(values[label]).encode("utf-8"))}
        for label in sorted(values)
    ]
    tokens.append(
        {"token_type": "private_record", "token": _hmac_token(key, "private_record", canonical_private)}
    )
    public_id = "PUB-" + hmac.new(key, b"public-record-id\0" + canonical_private, hashlib.sha256).hexdigest()[:32].upper()
    record = {
        "schema_version": PUBLIC_ENVELOPE_VERSION,
        "record_type": "dual_plane_public_projection",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S03",
        "phase_id": "S03-P3",
        "run_id": str(private_record["run_id"]),
        "public_record_id": public_id,
        "subject_class": "aggregate_evidence",
        "status": "PASS",
        "aggregate_counts": {
            "private_field_count": len(values),
            "opaque_token_count": len(tokens),
            "public_plaintext_disclosure_count": 0,
            "public_unkeyed_sensitive_digest_count": 0,
            "raw_root_access_count": 0,
        },
        "public_flags": {
            "fixture_only": True,
            "private_plane_required_for_exact_rebuild": True,
            "private_payload_committed": False,
            "private_key_committed": False,
            "public_only_reconstruction_material_present": False,
            "shared_run_identity_required": True,
        },
        "policy_refs": [
            "KMFA/metadata/protocol/v015_s03_p3_committable_metadata_policy_public_safe.json",
            "KMFA/metadata/protocol/v015_s03_p3_public_repository_protection_policy_public_safe.json",
        ],
        "evidence_refs": [
            "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/machine/dual_plane_verification_public_safe.json"
        ],
        "public_artifact_digests": [],
        "opaque_tokens": tokens,
    }
    # Projection construction precedes artifact materialization. Every tracked
    # publication path revalidates the envelope with the default strict refs.
    validate_public_metadata_envelope(record, require_tracked_refs=False)
    return record


def verify_dual_plane(private_record: Mapping[str, Any], key: bytes, public_record: Mapping[str, Any]) -> dict[str, Any]:
    expected = project_public_plane(private_record, key)
    if dict(public_record) != expected:
        raise SafetyError("public projection does not exactly rebuild from private plane")
    if public_record.get("run_id") != private_record.get("run_id"):
        raise SafetyError("private/public run identity drift")
    public_bytes = _canonical_json_bytes(public_record)
    private_bytes = _canonical_json_bytes(private_record)
    values = [str(value).encode("utf-8") for value in private_record["sensitive_values"].values()]
    attack_forms: set[bytes] = {key, key.hex().encode("ascii"), base64.b64encode(key), private_bytes}
    for value in values:
        attack_forms.update(
            {
                value,
                value.lower(),
                value.upper(),
                value.hex().encode("ascii"),
                base64.b64encode(value),
                hashlib.sha256(value).hexdigest().encode("ascii"),
                ("sha256:" + hashlib.sha256(value).hexdigest()).encode("ascii"),
            }
        )
    leaks = [form for form in attack_forms if form and form in public_bytes]
    if leaks:
        raise SafetyError("public projection contains a private or reconstructable attack form")
    return {
        "exact_private_to_public_rebuild": True,
        "attack_form_count": len(attack_forms),
        "attack_form_leak_count": 0,
        "public_plaintext_disclosure_count": 0,
        "public_unkeyed_sensitive_digest_count": 0,
        "public_only_reconstruction_material_present": False,
        "information_theoretic_non_reconstruction_claimed": False,
        "declared_attack_model_pass": True,
    }


def ensure_synthetic_private_dual_plane(
    private_root: Path,
    *,
    run_id: str,
    allow_external_test_root: bool = False,
) -> tuple[dict[str, Any], bytes, dict[str, Any], dict[str, Any]]:
    root = _safe_private_directory(private_root, allow_external_test_root=allow_external_test_root)
    key_path = root / "dual_plane_hmac.key"
    receipt_path = root / "synthetic_private_dual_plane_receipt.json"
    if key_path.exists():
        key = _read_regular_single_link(key_path, expected_mode=0o600)
    else:
        key = os.urandom(32)
        _create_private_file(key_path, key)
    if receipt_path.exists():
        payload = _read_regular_single_link(receipt_path, expected_mode=0o600)
        try:
            private_record = json.loads(payload)
        except json.JSONDecodeError as error:
            raise SafetyError(f"private dual-plane receipt is invalid: {error}") from error
        if private_record.get("run_id") != run_id:
            raise SafetyError("existing private receipt run_id drift")
    else:
        private_record = _synthetic_private_record(run_id)
        _create_private_file(receipt_path, _json_bytes(private_record))
    if private_record != _synthetic_private_record(run_id):
        raise SafetyError("private dual-plane receipt content drift")
    public_record = project_public_plane(private_record, key)
    verification = verify_dual_plane(private_record, key, public_record)
    return private_record, key, public_record, verification


def private_evidence_summary(private_root: Path, *, run_id: str) -> dict[str, Any]:
    private_record, key, public_record, verification = ensure_synthetic_private_dual_plane(private_root, run_id=run_id)
    relative = private_root.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    ignored = _git(["check-ignore", "-q", "--", relative]).returncode == 0
    tracked = _git(["ls-files", "--error-unmatch", "--", relative]).returncode == 0
    if not ignored or tracked:
        raise SafetyError("private dual-plane evidence must be ignored and untracked")
    return {
        "run_id": run_id,
        "private_receipt_schema": private_record["schema_version"],
        "public_projection_schema": PUBLIC_ENVELOPE_VERSION,
        "public_projection_contract_version": PUBLIC_PROJECTION_VERSION,
        "private_field_count": len(private_record["sensitive_values"]),
        "opaque_token_count": len(public_record["opaque_tokens"]),
        "private_evidence_gitignored": ignored,
        "private_evidence_tracked": tracked,
        "private_key_bytes": len(key),
        "public_projection": public_record,
        "verification": verification,
    }


def main() -> int:
    scanned, findings = scan_repository(scope="worktree")
    ignore = verify_gitignore_contract()
    if findings or not ignore["pass"]:
        for finding in findings:
            print(f"FAIL: {finding.path}: {finding.category}: {finding.detail}")
        if not ignore["pass"]:
            print("FAIL: gitignore contract drift")
        return 1
    print(
        "PASS: KMFA v1.5 public repository safety core "
        f"(files={scanned}, ignore={ignore['blocked_count']}/{ignore['probe_count']}, findings=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
