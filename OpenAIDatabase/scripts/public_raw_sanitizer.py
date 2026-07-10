#!/usr/bin/env python3
"""Shared recursive sanitizer for public raw JSON exports."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from typing import Any

from privacy_guard import redact_text


MAX_PUBLIC_RAW_FILE_BYTES = 40 * 1024 * 1024
BINARY_STRING_MIN_BYTES = 256 * 1024

_DATA_URL_BASE64_RE = re.compile(r"\Adata:[^,\r\n]*;base64,", re.IGNORECASE)
_BASE64_RE = re.compile(r"[A-Za-z0-9+/_-]+={0,2}")
_HEX_IDENTIFIER_RE = re.compile(r"[0-9a-f]{12,64}\Z")
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z",
    re.IGNORECASE,
)
_ISO_DATE_TIME_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?\Z"
)
_PUBLIC_RELATIVE_PREFIXES = (
    "data/public_raw/",
    "sessions/",
    "archived_sessions/",
)
_NON_TEXT_STRING_FIELDS = {"encrypted_content"}


class PublicRawSanitizationError(ValueError):
    pass


class PublicRawLimitError(PublicRawSanitizationError):
    """Compatibility error for concurrent R7 connector work."""


def merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, 0) + value
    return {key: merged[key] for key in sorted(merged)}


def binary_omission_marker(value: str) -> str:
    payload = value.encode("utf-8")
    return (
        f"[REDACTED_BINARY sha256={hashlib.sha256(payload).hexdigest()} "
        f"bytes={len(payload)} reason=non_text_binary_not_transcript]"
    )


def _is_strong_base64_candidate(candidate: str) -> bool:
    core = candidate.rstrip("=")
    if not core:
        return False
    character_classes = (
        any(character.isupper() for character in core),
        any(character.islower() for character in core),
        any(character.isdigit() for character in core),
        any(character in "+/_-" for character in core),
    )
    return sum(character_classes) >= 3 or len(set(core)) >= 32


def _decoded_payload_is_text(payload: bytes) -> bool:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if not text:
        return True
    printable = sum(character.isprintable() or character in "\r\n\t" for character in text)
    return printable / len(text) >= 0.95


def is_non_text_binary(value: str) -> bool:
    if _DATA_URL_BASE64_RE.match(value):
        return True
    if len(value.encode("utf-8")) < BINARY_STRING_MIN_BYTES:
        return False
    if any(character.isspace() and character not in "\r\n" for character in value):
        return False

    candidate = value.replace("\r", "").replace("\n", "")
    if len(candidate) < BINARY_STRING_MIN_BYTES or not _BASE64_RE.fullmatch(candidate):
        return False
    if len(candidate) % 4 == 1 or not _is_strong_base64_candidate(candidate):
        return False

    padded_candidate = candidate + "=" * (-len(candidate) % 4)
    try:
        decoded = base64.b64decode(padded_candidate, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        return False
    return bool(decoded) and not _decoded_payload_is_text(decoded)


def is_non_text_binary_string(value: str) -> bool:
    """Compatibility alias for concurrent R7 connector work."""
    return is_non_text_binary(value)


def is_safe_public_structured_string(value: str) -> bool:
    """Return whether a complete value is a portable identifier, time or raw ref."""

    if _UUID_RE.fullmatch(value) or _ISO_DATE_TIME_RE.fullmatch(value):
        return True
    if _HEX_IDENTIFIER_RE.fullmatch(value) and any(character in "abcdef" for character in value):
        return True
    if value.startswith(_PUBLIC_RELATIVE_PREFIXES):
        if any(character in "\r\n\t" for character in value):
            return False
        parts = value.replace("\\", "/").split("/")
        return bool(parts) and all(part not in {"", ".", ".."} for part in parts)
    return False


def sanitize_public_text(value: str) -> tuple[str, dict[str, int]]:
    if is_non_text_binary(value):
        return binary_omission_marker(value), {"binary_omission": 1}
    if is_safe_public_structured_string(value):
        return value, {}
    redacted, counts = redact_text(value)
    return redacted, {key: counts[key] for key in sorted(counts)}


def sanitize_public_value(value: Any) -> tuple[Any, dict[str, int]]:
    if isinstance(value, str):
        return sanitize_public_text(value)

    if isinstance(value, list):
        sanitized_items: list[Any] = []
        counts: dict[str, int] = {}
        for item in value:
            sanitized_item, item_counts = sanitize_public_value(item)
            sanitized_items.append(sanitized_item)
            counts = merge_counts(counts, item_counts)
        return sanitized_items, counts

    if isinstance(value, dict):
        sanitized_dict: dict[Any, Any] = {}
        counts: dict[str, int] = {}
        for key, item in value.items():
            sanitized_key: Any = key
            key_counts: dict[str, int] = {}
            if isinstance(key, str):
                sanitized_key, key_counts = sanitize_public_text(key)
                if sanitized_key in sanitized_dict:
                    suffix = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12].translate(
                        str.maketrans("0123456789", "ghijklmnop")
                    )
                    sanitized_key = f"{sanitized_key}__redacted_key_{suffix}"
                    counter = 2
                    while sanitized_key in sanitized_dict:
                        sanitized_key = (
                            f"{sanitized_key.rsplit('__', 1)[0]}__{counter}"
                        )
                        counter += 1
            if (
                isinstance(key, str)
                and key.strip().lower() in _NON_TEXT_STRING_FIELDS
                and isinstance(item, str)
                and item
            ):
                sanitized_item = binary_omission_marker(item)
                item_counts = {"binary_omission": 1}
            else:
                sanitized_item, item_counts = sanitize_public_value(item)
            sanitized_dict[sanitized_key] = sanitized_item
            counts = merge_counts(counts, key_counts)
            counts = merge_counts(counts, item_counts)
        return sanitized_dict, counts

    return value, {}


def sanitize_jsonl_event(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    if not isinstance(event, dict):
        raise PublicRawSanitizationError("JSONL event must be a dictionary")
    sanitized, counts = sanitize_public_value(event)
    if not isinstance(sanitized, dict):
        raise PublicRawSanitizationError("sanitized JSONL event must remain a dictionary")
    return sanitized, counts


def assert_json_event_within_limit(
    event: dict[str, Any], limit: int = MAX_PUBLIC_RAW_FILE_BYTES
) -> None:
    payload = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    size = len(payload)
    if size > limit:
        raise PublicRawSanitizationError(
            f"compact UTF-8 JSONL event is {size} bytes; limit is {limit} bytes"
        )


def require_public_raw_file_size(payload: bytes | str, label: str) -> int:
    """Compatibility size guard for concurrent R7 connector work."""
    encoded = payload.encode("utf-8") if isinstance(payload, str) else payload
    size = len(encoded)
    if size > MAX_PUBLIC_RAW_FILE_BYTES:
        raise PublicRawLimitError(
            f"{label} is {size} bytes; public raw limit is {MAX_PUBLIC_RAW_FILE_BYTES} bytes"
        )
    return size
