#!/usr/bin/env python3
"""Privacy guards for raw private import and redacted derived outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DERIVED_IMPORT_DIR = Path("data/derived/privacy_imports")
PRIVACY_AUDIT_LOG = Path("data/run_logs/privacy/privacy_imports.jsonl")
PRIVATE_ROOTS = (Path("data/raw"), Path("data/raw_encrypted"), Path("data/private_imports"))
REQUIRED_GITIGNORE_PATTERNS = ("*.zip", "data/raw/", "data/raw_encrypted/", "data/private_imports/")
SECRET_PATTERNS = (
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{10,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
)
CREDENTIAL_POLICY = "credential_is_not_memory"
CREDENTIAL_PATTERNS = (
    ("api_keys", SECRET_PATTERNS[0][1]),
    ("api_keys", SECRET_PATTERNS[1][1]),
    ("api_keys", SECRET_PATTERNS[2][1]),
    ("api_keys", SECRET_PATTERNS[3][1]),
    (
        "api_keys",
        re.compile(r"\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:;-]{7,}", re.I),
    ),
    (
        "cookies",
        re.compile(r"\b(?:cookie|set-cookie)\b\s*[:=]\s*['\"]?[^'\"\n]{12,}", re.I),
    ),
    (
        "session_tokens",
        re.compile(r"\b(?:session[_-]?token|sessionid|auth[_-]?token|csrf[_-]?token)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,}", re.I),
    ),
    (
        "passwords",
        re.compile(r"\b(?:password|passwd|pwd)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,}", re.I),
    ),
    (
        "private_keys",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----\s*[A-Za-z0-9+/=\r\n]{16,}\s*-----END [A-Z ]*PRIVATE KEY-----", re.S),
    ),
    (
        "oauth_tokens",
        re.compile(r"\b(?:access[_-]?token|refresh[_-]?token|oauth[_-]?token|id[_-]?token)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:;-]{7,}", re.I),
    ),
    ("oauth_tokens", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.I)),
    (
        "browser_credential_store",
        re.compile(r"\b(?:browser[_-]?credential[_-]?store|login[_-]?data|keychain)\b\s*[:=]\s*['\"]?[A-Za-z0-9][^'\"\n]{7,}", re.I),
    ),
)
REDACTION_PATTERNS = (
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"\+?\d[\d\s().-]{8,}\d"), "[REDACTED_PHONE]"),
    ("openai_api_key", SECRET_PATTERNS[0][1], "[REDACTED_SECRET]"),
    ("github_token", SECRET_PATTERNS[1][1], "[REDACTED_SECRET]"),
    ("slack_token", SECRET_PATTERNS[2][1], "[REDACTED_SECRET]"),
    ("aws_access_key", SECRET_PATTERNS[3][1], "[REDACTED_SECRET]"),
    (
        "local_absolute_path",
        re.compile(r"(?:[A-Za-z]:[\\/][^\s\"']+|/(?:Users|home)/[^\s\"']+)"),
        "[REDACTED_LOCAL_PATH]",
    ),
)


class PrivacyViolation(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def is_private_source_location(raw_path: Path, database_dir: Path) -> bool:
    resolved_raw = raw_path.resolve()
    resolved_db = database_dir.resolve()
    if not is_relative_to(resolved_raw, resolved_db):
        return True
    return any(is_relative_to(resolved_raw, resolved_db / root) for root in PRIVATE_ROOTS)


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    redacted = text
    counts: dict[str, int] = {}
    for name, pattern, replacement in REDACTION_PATTERNS:
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            counts[name] = counts.get(name, 0) + count
    redacted, credential_counts = redact_credentials_in_text(redacted)
    for name, count in credential_counts.items():
        counts[f"credential_{name}"] = counts.get(f"credential_{name}", 0) + count
    return redacted, counts


def credential_exclusion_hits(text: str, source: str = "") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for category, pattern in CREDENTIAL_PATTERNS:
        for match in pattern.finditer(text):
            key = (category, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                {
                    "category": category,
                    "source": source,
                    "start": match.start(),
                    "end": match.end(),
                    "policy": CREDENTIAL_POLICY,
                    "evidence": "[REDACTED_CREDENTIAL]",
                }
            )
    return hits


def assert_no_credentials(text: str, source: str = "") -> None:
    hits = credential_exclusion_hits(text, source)
    if hits:
        categories = sorted({str(hit["category"]) for hit in hits})
        label = f" in {source}" if source else ""
        raise PrivacyViolation(f"credential content is not memory{label}: {', '.join(categories)}")


def redact_credentials_in_text(text: str) -> tuple[str, dict[str, int]]:
    redacted = text
    counts: dict[str, int] = {}
    for category, pattern in CREDENTIAL_PATTERNS:
        redacted, count = pattern.subn("[REDACTED_CREDENTIAL]", redacted)
        if count:
            counts[category] = counts.get(category, 0) + count
    return redacted, counts


def merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, 0) + value
    return merged


def redact_payload(value: Any) -> tuple[Any, dict[str, int]]:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        counts: dict[str, int] = {}
        redacted_items = []
        for item in value:
            redacted_item, item_counts = redact_payload(item)
            redacted_items.append(redacted_item)
            counts = merge_counts(counts, item_counts)
        return redacted_items, counts
    if isinstance(value, dict):
        counts: dict[str, int] = {}
        redacted_dict: dict[str, Any] = {}
        for key, item in value.items():
            redacted_item, item_counts = redact_payload(item)
            redacted_dict[str(key)] = redacted_item
            counts = merge_counts(counts, item_counts)
        return redacted_dict, counts
    return value, {}


def read_private_payload(raw_path: Path) -> Any:
    text = raw_path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def safe_output_name(name: str | None, raw_path: Path) -> str:
    candidate = name or f"{raw_path.stem}.redacted.json"
    if Path(candidate).name != candidate or not candidate.endswith(".json"):
        raise PrivacyViolation(f"output_name must be a simple .json filename: {candidate}")
    return candidate


def import_private_export(raw_path: Path, database_dir: Path, output_name: str | None = None) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    raw_path = raw_path.resolve()
    if not raw_path.is_file():
        raise PrivacyViolation(f"raw private source does not exist: {raw_path}")
    if not is_private_source_location(raw_path, database_dir):
        raise PrivacyViolation("raw private source must be outside the repo or under an ignored private input root")

    raw_bytes = raw_path.read_bytes()
    raw_payload = read_private_payload(raw_path)
    redacted_payload, redaction_counts = redact_payload(raw_payload)
    redacted_source_name, name_counts = redact_text(raw_path.name)
    redaction_counts = merge_counts(redaction_counts, name_counts)
    output_rel = DERIVED_IMPORT_DIR / safe_output_name(output_name, raw_path)
    output_path = database_dir / output_rel
    result = {
        "schema_version": "openaidatabase.redacted_private_import.v1",
        "generated_at": now_utc(),
        "raw_private_data_included": False,
        "plaintext_secrets_included": False,
        "local_absolute_paths_included": False,
        "raw_source_name": redacted_source_name,
        "raw_source_sha256": sha256_bytes(raw_bytes),
        "raw_source_size_bytes": len(raw_bytes),
        "redaction_counts": redaction_counts,
        "redacted_payload": redacted_payload,
    }
    write_json_atomic(output_path, result)
    append_jsonl(
        database_dir / PRIVACY_AUDIT_LOG,
        {
            "timestamp": result["generated_at"],
            "event_type": "redacted_private_import",
            "output_path": output_rel.as_posix(),
            "raw_private_data_included": False,
            "raw_source_name": redacted_source_name,
            "raw_source_sha256": result["raw_source_sha256"],
            "redaction_counts": redaction_counts,
        },
    )
    return {"status": "PASS", "output_path": output_rel.as_posix(), "redaction_counts": redaction_counts}


def git_ls_files(database_dir: Path, paths: list[str] | None = None) -> list[str]:
    command = ["git", "ls-files"]
    if paths:
        command.extend(["--", *paths])
    try:
        result = subprocess.run(
            command,
            cwd=database_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def gitignore_declares_private_defaults(database_dir: Path) -> dict[str, Any]:
    text = (database_dir / ".gitignore").read_text(encoding="utf-8", errors="ignore") if (database_dir / ".gitignore").exists() else ""
    entries = {line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")}
    missing = [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in entries]
    return {"ok": not missing, "missing": missing, "required": list(REQUIRED_GITIGNORE_PATTERNS)}


def high_risk_secret_hits(database_dir: Path, tracked_files: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for rel in tracked_files:
        path = database_dir / rel
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for segment in privacy_scan_segments(path, text):
            for hit in credential_exclusion_hits(segment, rel):
                hits.append({"path": rel, "pattern": str(hit["category"])})
    return hits


def iter_json_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_json_strings(item)


def privacy_scan_segments(path: Path, text: str) -> list[str]:
    if path.suffix not in {".json", ".jsonl"}:
        return [text]
    try:
        if path.suffix == ".json":
            payloads = [json.loads(text)]
        else:
            payloads = [json.loads(line) for line in text.splitlines() if line.strip()]
    except json.JSONDecodeError:
        return [text]
    return [segment for payload in payloads for segment in iter_json_strings(payload)]


def scan_repo_privacy(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    tracked_private = git_ls_files(database_dir, [root.as_posix() for root in PRIVATE_ROOTS])
    tracked_files = git_ls_files(database_dir)
    ignore_contract = gitignore_declares_private_defaults(database_dir)
    secret_hits = high_risk_secret_hits(database_dir, tracked_files)
    return {
        "status": "PASS" if not tracked_private and not secret_hits and ignore_contract["ok"] else "FAIL",
        "credential_is_not_memory": True,
        "ordinary_transcript_blocked": False,
        "tracked_raw_private_files": tracked_private,
        "tracked_raw_private_file_count": len(tracked_private),
        "high_risk_secret_hits": secret_hits,
        "high_risk_secret_hit_count": len(secret_hits),
        "gitignore_contract": ignore_contract,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAIDatabase privacy import and scan guard.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--import-private", type=Path)
    parser.add_argument("--output-name")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.scan_only:
        result = scan_repo_privacy(args.database_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    if args.import_private:
        result = import_private_export(args.import_private, args.database_dir, args.output_name)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    raise SystemExit("Use --scan-only or --import-private")


if __name__ == "__main__":
    raise SystemExit(main())
