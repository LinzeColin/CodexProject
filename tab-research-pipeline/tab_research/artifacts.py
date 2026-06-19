from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict


LOCAL_PATH_RE = re.compile(
    r"(?P<path>/Users/[^\"'<>]+|/private/var/folders/[^\"'<>]+|/var/folders/[^\"'<>]+|/private/tmp/[^\"'<>]+|/tmp/[^\"'<>]+|/work/private/[^\"'<>]+)"
)
DOWNLOADS_RE = re.compile(r"Downloads/FIFA Report", re.IGNORECASE)
FILE_URI_RE = re.compile(r"file://[^\\s\"'<>]+", re.IGNORECASE)
PUBLIC_UI_REPLACEMENTS = {
    "My Bets": "私有持仓",
    "Bet Slip": "下注单",
    "Pending Bets": "待结算持仓",
    "My Offers": "私有优惠",
}


def public_artifact_name(path: Any) -> str:
    value = str(path or "")
    return Path(value).name if value else ""


def public_artifact_ref(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if is_local_path_like(text):
        return Path(text).name or "<local_path>"
    return text


def sanitize_public_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_public_payload(child) for key, child in value.items()}
    if isinstance(value, list):
        return [sanitize_public_payload(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_public_payload(item) for item in value]
    if isinstance(value, Path):
        return public_artifact_ref(value)
    if isinstance(value, str):
        return sanitize_public_text(value)
    return value


def sanitize_public_manifest(manifest: Dict) -> Dict:
    payload = sanitize_public_payload(manifest)
    if isinstance(payload, dict):
        payload.setdefault("schema_version", 1)
    return payload


def sanitize_public_text(text: str) -> str:
    if not text:
        return text
    stripped = text.strip()
    if LOCAL_PATH_RE.fullmatch(stripped) or DOWNLOADS_RE.fullmatch(stripped):
        return public_artifact_ref(stripped)

    def replace_path(match: re.Match) -> str:
        path = match.group("path")
        if "/work/private/" in path:
            return "<private>"
        return Path(path).name or "<local_path>"

    sanitized = LOCAL_PATH_RE.sub(replace_path, text)
    sanitized = FILE_URI_RE.sub(lambda match: f"local_file_ref:{Path(match.group(0).replace('file://', '')).name}", sanitized)
    sanitized = DOWNLOADS_RE.sub("FIFA Report", sanitized)
    for source, target in PUBLIC_UI_REPLACEMENTS.items():
        sanitized = sanitized.replace(source, target)
    return sanitized


def is_local_path_like(text: str) -> bool:
    return (
        text.startswith("/")
        or "/Users/" in text
        or "/var/folders/" in text
        or "/private/var/folders/" in text
        or "/tmp/" in text
        or "/private/tmp/" in text
        or "/work/private/" in text
        or "file://" in text.lower()
        or bool(DOWNLOADS_RE.search(text))
    )
