#!/usr/bin/env python3
"""Safely plan, import and verify authorized public raw text evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import unicodedata
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from memory_security import MemorySecurityError, assert_untrusted_text_safe, load_policy
from public_raw_sanitizer import sanitize_public_text


DEFAULT_CONTRACT = Path("config/storage/raw_import.json")
MEMORY_CLI_THIN_WRAPPER = True
ARCHIVE_MAGIC = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"7z\xbc\xaf\x27\x1c",
    b"Rar!\x1a\x07",
    b"\x1f\x8b",
    b"BZh",
    b"\xfd7zXZ\x00",
)
SOURCE_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
AUTH_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}\Z")
OWNER_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{1,127}\Z")
SHA256_REF_RE = re.compile(r"sha256:[a-f0-9]{64}\Z")
MONTH_RE = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])\Z")


class RawImportError(ValueError):
    """Raised before any canonical raw write when an import gate fails."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_json_strict(payload: str, label: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RawImportError(f"{label} contains a duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(payload, object_pairs_hook=reject_duplicates)
    except RawImportError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RawImportError(f"{label} is not valid UTF-8 JSON") from exc


def parse_rfc3339(value: str, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise RawImportError(f"{label} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RawImportError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise RawImportError(f"{label} must include a timezone")
    return parsed


def safe_relative_path(value: str, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or any(c in value for c in "\r\n\x00"):
        raise RawImportError(f"{label} must be a safe POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RawImportError(f"{label} must be a safe POSIX relative path")
    return path


def assert_no_symlink_path(path: Path, stop_at: Path | None = None) -> None:
    current = path
    stop = stop_at.resolve() if stop_at is not None else None
    while True:
        if current.exists() and stat.S_ISLNK(current.lstat().st_mode):
            raise RawImportError("symlink input or destination is prohibited")
        if stop is not None and current.resolve() == stop:
            return
        if current.parent == current:
            return
        current = current.parent


def resolve_source(source_root: Path, source_relative: str) -> Path:
    relative = safe_relative_path(source_relative, "source")
    if source_root.is_symlink():
        raise RawImportError("source_root symlink is prohibited")
    root = source_root.resolve(strict=True)
    candidate = root.joinpath(*relative.parts)
    assert_no_symlink_path(candidate, root)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise RawImportError("source must be a regular file inside source_root") from exc
    if not resolved.is_file():
        raise RawImportError("source must be a regular file inside source_root")
    return resolved


def read_regular_file(path: Path, max_bytes: int, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise RawImportError(f"{label} must be a regular non-symlink file")
    size = path.stat().st_size
    if size > max_bytes:
        raise RawImportError(f"{label} exceeds the configured byte limit")
    return path.read_bytes()


def validate_contract(contract: dict[str, Any]) -> None:
    expected = {
        "schema_version": "openai_database.raw_import.v1",
        "project_id": "OpenAIDatabase",
        "canonical_root": "data/public_raw",
        "partition_pattern": "YYYY-MM",
        "instruction_trust": "none",
        "memory_source_type": "raw_import",
        "memory_status": "candidate",
        "automatic_active_promotion": False,
        "security_policy": "config/memory-security-policy.json",
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            raise RawImportError(f"raw import contract has invalid {key}")
    for key in ("max_text_part_bytes", "max_input_bytes", "max_authorization_bytes", "max_parts"):
        if not isinstance(contract.get(key), int) or int(contract[key]) <= 0:
            raise RawImportError(f"raw import contract has invalid {key}")
    if int(contract["max_text_part_bytes"]) > 900 * 1024:
        raise RawImportError("raw import part limit exceeds 900 KiB")
    if int(contract["max_input_bytes"]) > int(contract["max_text_part_bytes"]) * int(contract["max_parts"]):
        raise RawImportError("raw import input limit exceeds part capacity")


def load_authorization(path: Path, contract: dict[str, Any], original_sha: str) -> dict[str, Any]:
    payload = read_regular_file(path, int(contract["max_authorization_bytes"]), "authorization")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RawImportError("authorization is not valid UTF-8 JSON") from exc
    value = load_json_strict(text, "authorization")
    if not isinstance(value, dict):
        raise RawImportError("authorization must be a JSON object")
    required = {
        "schema_version",
        "authorization_id",
        "owner_id",
        "decision",
        "authorized_at",
        "content_rights_confirmed",
        "public_repository_allowed",
        "source_id",
        "source_ref",
        "observed_at",
        "source_sha256",
    }
    if set(value) != required:
        raise RawImportError("authorization fields do not match the exact contract")
    if value["schema_version"] != contract["authorization_schema_version"]:
        raise RawImportError("authorization schema_version is invalid")
    if value["decision"] != contract["authorization_decision"]:
        raise RawImportError("public publication authorization is missing")
    if value["content_rights_confirmed"] is not True or value["public_repository_allowed"] is not True:
        raise RawImportError("content rights or public-repository authorization is missing")
    if not isinstance(value["authorization_id"], str) or not AUTH_ID_RE.fullmatch(value["authorization_id"]):
        raise RawImportError("authorization_id is invalid")
    if not isinstance(value["owner_id"], str) or not OWNER_ID_RE.fullmatch(value["owner_id"]):
        raise RawImportError("owner_id is invalid")
    if not isinstance(value["source_id"], str) or not SOURCE_ID_RE.fullmatch(value["source_id"]):
        raise RawImportError("source_id is invalid")
    safe_relative_path(value["source_ref"], "source_ref")
    parse_rfc3339(value["authorized_at"], "authorized_at")
    observed_at = parse_rfc3339(value["observed_at"], "observed_at")
    if value["source_sha256"] != f"sha256:{original_sha}":
        raise RawImportError("authorization source_sha256 does not match the source")
    if not SHA256_REF_RE.fullmatch(value["source_sha256"]):
        raise RawImportError("authorization source_sha256 is invalid")
    value["partition"] = f"{observed_at.year:04d}-{observed_at.month:02d}"
    return value


def assert_text_security(text: str, security_policy: dict[str, Any]) -> None:
    try:
        assert_untrusted_text_safe(text, "raw_evidence", security_policy)
    except MemorySecurityError as exc:
        raise RawImportError("untrusted content is prohibited by memory security policy") from exc


def normalize_and_sanitize(
    source: Path,
    payload: bytes,
    contract: dict[str, Any],
    security_policy: dict[str, Any],
) -> tuple[bytes, dict[str, int]]:
    suffix = source.suffix.lower()
    allowed = {str(item) for item in contract.get("allowed_source_extensions") or []}
    denied = {str(item) for item in contract.get("archive_extensions_denied") or []}
    if suffix in denied or any(payload.startswith(magic) for magic in ARCHIVE_MAGIC):
        raise RawImportError("archive input is prohibited; extract and authorize one bounded text file")
    if suffix not in allowed:
        raise RawImportError("source extension is not allowed")
    try:
        text = payload.decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise RawImportError("source must be strict UTF-8 text") from exc
    text = unicodedata.normalize("NFC", text)
    assert_text_security(text, security_policy)
    sanitized, counts = sanitize_public_text(text)
    if counts.get("binary_omission"):
        raise RawImportError("binary-like content is prohibited in public raw text")
    return sanitized.encode("utf-8"), counts


def split_utf8(payload: bytes, limit: int, max_parts: int) -> list[bytes]:
    if not payload:
        return [b""]
    parts: list[bytes] = []
    start = 0
    while start < len(payload):
        end = min(start + limit, len(payload))
        while end < len(payload) and end > start and payload[end] & 0xC0 == 0x80:
            end -= 1
        if end == start:
            raise RawImportError("UTF-8 character exceeds the part limit")
        part = payload[start:end]
        part.decode("utf-8", errors="strict")
        parts.append(part)
        start = end
    if len(parts) > max_parts:
        raise RawImportError("sanitized content exceeds the configured part capacity")
    return parts


def sidecar_payload(
    contract: dict[str, Any],
    authorization: dict[str, Any],
    source_suffix: str,
    original: bytes,
    sanitized: bytes,
    part_paths: list[str],
    parts: list[bytes],
    sidecar_path: str,
    counts: dict[str, int],
) -> dict[str, Any]:
    original_sha = sha256_bytes(original)
    return {
        "schema_version": "openai_database.raw_evidence_sidecar.v1",
        "evidence_id": f"raw_{original_sha[:32]}",
        "classification": "evidence",
        "source": {
            "source_id": authorization["source_id"],
            "source_ref": authorization["source_ref"],
            "observed_at": authorization["observed_at"],
            "original_extension": source_suffix,
        },
        "authorization": {
            "authorization_id": authorization["authorization_id"],
            "owner_id": authorization["owner_id"],
            "decision": authorization["decision"],
            "authorized_at": authorization["authorized_at"],
            "content_rights_confirmed": True,
            "public_repository_allowed": True,
        },
        "hashes": {
            "original_sha256": f"sha256:{original_sha}",
            "sanitized_sha256": f"sha256:{sha256_bytes(sanitized)}",
            "original_bytes": len(original),
            "sanitized_bytes": len(sanitized),
        },
        "parts": [
            {
                "index": index,
                "path": path,
                "bytes": len(part),
                "sha256": f"sha256:{sha256_bytes(part)}",
            }
            for index, (path, part) in enumerate(zip(part_paths, parts, strict=True), 1)
        ],
        "instruction_trust": contract["instruction_trust"],
        "credential_scan": {"status": "PASS", "hit_count": 0},
        "sanitization_counts": {key: counts[key] for key in sorted(counts) if counts[key]},
        "memory_contract": {
            "source_type": contract["memory_source_type"],
            "source_ref": sidecar_path,
            "allowed_status": contract["memory_status"],
            "automatic_active_promotion": contract["automatic_active_promotion"],
        },
    }


def expected_artifacts(
    database_dir: Path,
    contract: dict[str, Any],
    authorization: dict[str, Any],
    source_suffix: str,
    original: bytes,
    sanitized: bytes,
    parts: list[bytes],
    counts: dict[str, int],
) -> tuple[dict[Path, bytes], Path, dict[str, Any]]:
    root = database_dir / contract["canonical_root"]
    partition = authorization["partition"]
    if not MONTH_RE.fullmatch(partition):
        raise RawImportError("derived partition is invalid")
    original_sha = sha256_bytes(original)
    stem = f"{authorization['source_id']}.{original_sha[:12]}"
    part_rel_paths = [
        f"{contract['canonical_root']}/{partition}/{stem}.part-{index:04d}.md"
        for index in range(1, len(parts) + 1)
    ]
    sidecar_rel = f"{contract['canonical_root']}/{partition}/{stem}.sidecar.json"
    sidecar = sidecar_payload(
        contract,
        authorization,
        source_suffix,
        original,
        sanitized,
        part_rel_paths,
        parts,
        sidecar_rel,
        counts,
    )
    artifacts = {database_dir / rel: part for rel, part in zip(part_rel_paths, parts, strict=True)}
    sidecar_path = database_dir / sidecar_rel
    artifacts[sidecar_path] = (
        json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert_no_symlink_path(root, database_dir.resolve())
    return artifacts, sidecar_path, sidecar


def artifact_plan_sha256(database_dir: Path, artifacts: dict[Path, bytes]) -> str:
    root = database_dir.resolve()
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": len(payload),
            "sha256": f"sha256:{sha256_bytes(payload)}",
        }
        for path, payload in sorted(artifacts.items(), key=lambda item: item[0].as_posix())
    ]
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{sha256_bytes(payload)}"


def commit_new_artifacts(artifacts: dict[Path, bytes], partition_dir: Path) -> bool:
    existing = {path: path.read_bytes() for path in artifacts if path.exists() and path.is_file()}
    if existing:
        if len(existing) == len(artifacts) and all(existing[path] == payload for path, payload in artifacts.items()):
            return True
        raise RawImportError("append-only raw artifact collision or partial transaction detected")
    if any(path.exists() for path in artifacts):
        raise RawImportError("raw artifact destination is not a regular file")

    partition_existed = partition_dir.exists()
    partition_dir.mkdir(parents=True, exist_ok=True)
    if partition_dir.is_symlink():
        raise RawImportError("raw partition symlink is prohibited")
    temp_paths: list[Path] = []
    committed: list[Path] = []
    try:
        for index, (path, payload) in enumerate(artifacts.items(), 1):
            temp = path.with_name(f".{path.name}.{os.getpid()}.{index}.tmp")
            with temp.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temp_paths.append(temp)
        for temp, path in zip(temp_paths, artifacts, strict=True):
            os.link(temp, path)
            committed.append(path)
        return False
    except Exception:
        for path in committed:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)
        if not partition_existed and partition_dir.exists() and not any(partition_dir.iterdir()):
            partition_dir.rmdir()


def import_raw_evidence(
    database_dir: Path,
    contract: dict[str, Any],
    source_root: Path,
    source_relative: str,
    authorization_path: Path | None,
    *,
    apply: bool,
    expected_artifact_plan_sha256: str | None = None,
) -> dict[str, Any]:
    validate_contract(contract)
    if authorization_path is None:
        raise RawImportError("explicit authorization file is required")
    source = resolve_source(source_root, source_relative)
    original = read_regular_file(source, int(contract["max_input_bytes"]), "source")
    authorization = load_authorization(authorization_path, contract, sha256_bytes(original))
    try:
        security_policy = load_policy(database_dir, Path(str(contract["security_policy"])))
    except MemorySecurityError as exc:
        raise RawImportError("memory security policy is invalid or unavailable") from exc
    sanitized, counts = normalize_and_sanitize(source, original, contract, security_policy)
    parts = split_utf8(sanitized, int(contract["max_text_part_bytes"]), int(contract["max_parts"]))
    artifacts, sidecar_path, sidecar = expected_artifacts(
        database_dir.resolve(),
        contract,
        authorization,
        source.suffix.lower(),
        original,
        sanitized,
        parts,
        counts,
    )
    artifact_plan = artifact_plan_sha256(database_dir, artifacts)
    if expected_artifact_plan_sha256 is not None and artifact_plan != expected_artifact_plan_sha256:
        raise RawImportError("raw artifact plan changed before apply")
    idempotent = False
    if apply:
        idempotent = commit_new_artifacts(artifacts, sidecar_path.parent)
    return {
        "status": "PASS",
        "mode": "apply" if apply else "plan",
        "task_id": contract["task_id"],
        "acceptance_id": contract["acceptance_id"],
        "evidence_id": sidecar["evidence_id"],
        "raw_root": contract["canonical_root"],
        "partition": authorization["partition"],
        "sidecar": sidecar_path.relative_to(database_dir.resolve()).as_posix(),
        "part_count": len(parts),
        "part_bytes": [len(part) for part in parts],
        "original_sha256": sidecar["hashes"]["original_sha256"],
        "sanitized_sha256": sidecar["hashes"]["sanitized_sha256"],
        "artifact_plan_sha256": artifact_plan,
        "instruction_obedience_count": 0,
        "credential_leak_count": 0,
        "automatic_active_promotion_count": 0,
        "writes": 0 if not apply or idempotent else len(artifacts),
        "idempotent": idempotent,
    }


def reassemble_raw_evidence(database_dir: Path, sidecar_relative: str, contract: dict[str, Any]) -> bytes:
    validate_contract(contract)
    relative = safe_relative_path(sidecar_relative, "sidecar")
    expected_prefix = PurePosixPath(contract["canonical_root"])
    if tuple(relative.parts[: len(expected_prefix.parts)]) != expected_prefix.parts:
        raise RawImportError("sidecar is outside canonical raw root")
    sidecar_path = database_dir.resolve().joinpath(*relative.parts)
    assert_no_symlink_path(sidecar_path, database_dir.resolve())
    payload = read_regular_file(sidecar_path, int(contract["max_authorization_bytes"]) * 4, "sidecar")
    sidecar = load_json_strict(payload.decode("utf-8", errors="strict"), "sidecar")
    if not isinstance(sidecar, dict) or sidecar.get("schema_version") != "openai_database.raw_evidence_sidecar.v1":
        raise RawImportError("sidecar schema_version is invalid")
    memory = sidecar.get("memory_contract") or {}
    if memory != {
        "source_type": "raw_import",
        "source_ref": sidecar_relative,
        "allowed_status": "candidate",
        "automatic_active_promotion": False,
    }:
        raise RawImportError("sidecar memory contract is invalid")
    part_rows = sidecar.get("parts")
    if not isinstance(part_rows, list) or not part_rows or len(part_rows) > int(contract["max_parts"]):
        raise RawImportError("sidecar parts are invalid")
    assembled: list[bytes] = []
    for expected_index, row in enumerate(part_rows, 1):
        if not isinstance(row, dict) or row.get("index") != expected_index:
            raise RawImportError("sidecar part ordering is invalid")
        part_relative = safe_relative_path(str(row.get("path") or ""), "part path")
        if tuple(part_relative.parts[: len(expected_prefix.parts)]) != expected_prefix.parts:
            raise RawImportError("sidecar part is outside canonical raw root")
        part_path = database_dir.resolve().joinpath(*part_relative.parts)
        assert_no_symlink_path(part_path, database_dir.resolve())
        part = read_regular_file(part_path, int(contract["max_text_part_bytes"]), "part")
        if row.get("bytes") != len(part) or row.get("sha256") != f"sha256:{sha256_bytes(part)}":
            raise RawImportError("sidecar part hash or size mismatch")
        assembled.append(part)
    result = b"".join(assembled)
    hashes = sidecar.get("hashes") or {}
    if hashes.get("sanitized_bytes") != len(result) or hashes.get("sanitized_sha256") != f"sha256:{sha256_bytes(result)}":
        raise RawImportError("reassembled evidence hash or size mismatch")
    result.decode("utf-8", errors="strict")
    return result


def load_contract(database_dir: Path, contract_path: Path) -> dict[str, Any]:
    path = contract_path if contract_path.is_absolute() else database_dir / contract_path
    value = load_json_strict(path.read_text(encoding="utf-8"), "raw import contract")
    if not isinstance(value, dict):
        raise RawImportError("raw import contract must be a JSON object")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "apply"):
        child = subparsers.add_parser(command)
        child.add_argument("--source-root", type=Path, required=True)
        child.add_argument("--source", required=True)
        child.add_argument("--authorization", type=Path, required=True)
        if command == "apply":
            child.add_argument("--apply", action="store_true")
            child.add_argument("--base-sha")
            child.add_argument("--idempotency-key")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--sidecar", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from memory import main as memory_main

    if args.command == "apply" and not args.apply:
        print(
            json.dumps(
                {
                    "schema_version": "openai_database.memory_cli.v1",
                    "status": "FAIL_CLOSED",
                    "reason": "legacy apply requires explicit --apply and memory.py write guards",
                    "writes_files": False,
                },
                sort_keys=True,
            )
        )
        return 2

    forwarded = [
        "--database-dir",
        str(args.database_dir),
        "import",
        "--contract",
        str(args.contract),
    ]
    if args.command == "verify":
        forwarded.extend(["--verify-sidecar", args.sidecar])
    else:
        forwarded.extend(
            [
                "--source-root",
                str(args.source_root),
                "--source",
                args.source,
                "--authorization",
                str(args.authorization),
            ]
        )
        if args.command == "apply":
            if args.apply:
                forwarded.append("--apply")
            if args.base_sha is not None:
                forwarded.extend(["--base-sha", args.base_sha])
            if args.idempotency_key is not None:
                forwarded.extend(["--idempotency-key", args.idempotency_key])
    return memory_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
