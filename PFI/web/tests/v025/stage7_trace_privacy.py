"""Sanitize an actual Playwright trace while retaining its action timeline."""

from __future__ import annotations

import base64
import re
import zipfile
from pathlib import Path
from typing import Iterable


_SENSITIVE_JSON_FIELD = re.compile(
    r'("(?:value|postData|contentBase64|apiAuthToken|X-PFI-Runtime-Token)"\s*:\s*)'
    r'(?:("(?:\\.|[^"\\])*")|(-?[0-9]+(?:\.[0-9]+)?|null|true|false))',
    re.IGNORECASE,
)
_ABSOLUTE_PATH = re.compile(
    r"/(?:Users/|private/var/folders/|var/folders/|tmp/)[^\"'\s<>,)]+"
)
_FINANCIAL_TEXT = re.compile(r"CNY\s+-?[0-9][0-9,.]*")
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def sanitize_playwright_trace(
    raw_trace: Path,
    output_trace: Path,
    *,
    auth_tokens: Iterable[str] = (),
    private_payloads: Iterable[bytes] = (),
) -> dict[str, object]:
    """Remove values, request bodies, resources, tokens, and local paths from a trace."""

    tokens = tuple(token for token in auth_tokens if token)
    private_literals: list[str] = []
    for payload in private_payloads:
        if not payload:
            continue
        private_literals.append(base64.b64encode(payload).decode("ascii"))
        try:
            private_literals.append(payload.decode("utf-8"))
        except UnicodeDecodeError:
            pass

    temporary = output_trace.with_suffix(".sanitizing.zip")
    replacements = {
        "sensitive_fields": 0,
        "absolute_paths": 0,
        "financial_text": 0,
        "auth_tokens": 0,
        "private_payloads": 0,
        "resource_entries_removed": 0,
        "image_entries_removed": 0,
    }
    retained_entries: list[str] = []
    try:
        with zipfile.ZipFile(raw_trace) as source, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as target:
            for info in source.infolist():
                suffix = Path(info.filename).suffix.lower()
                if info.filename.startswith("resources/"):
                    replacements["resource_entries_removed"] += 1
                    continue
                if suffix in _IMAGE_SUFFIXES:
                    replacements["image_entries_removed"] += 1
                    continue
                data = source.read(info.filename)
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                text, count = _SENSITIVE_JSON_FIELD.subn(r'\1"[REDACTED]"', text)
                replacements["sensitive_fields"] += count
                text, count = _ABSOLUTE_PATH.subn("[LOCAL_PATH_REDACTED]", text)
                replacements["absolute_paths"] += count
                text, count = _FINANCIAL_TEXT.subn("CNY [FINANCIAL_VALUE_REDACTED]", text)
                replacements["financial_text"] += count
                for token in tokens:
                    count = text.count(token)
                    if count:
                        text = text.replace(token, "[RUNTIME_TOKEN_REDACTED]")
                        replacements["auth_tokens"] += count
                for literal in private_literals:
                    count = text.count(literal)
                    if count:
                        text = text.replace(literal, "[PRIVATE_PAYLOAD_REDACTED]")
                        replacements["private_payloads"] += count
                target.writestr(info, text.encode("utf-8"))
                retained_entries.append(info.filename)
        temporary.replace(output_trace)
    finally:
        temporary.unlink(missing_ok=True)

    if not retained_entries or not any(name.endswith(".trace") or name == "trace.trace" for name in retained_entries):
        output_trace.unlink(missing_ok=True)
        raise RuntimeError("sanitized Playwright trace has no retained action timeline")
    serialized = b""
    with zipfile.ZipFile(output_trace) as archive:
        serialized = b"\n".join(archive.read(info.filename) for info in archive.infolist())
    forbidden = [
        marker
        for marker in (
            b"/Users/", b"/private/var/folders/", b"/var/folders/", b"/tmp/",
            *(token.encode() for token in tokens),
            *(literal.encode("utf-8") for literal in private_literals),
        )
        if marker and marker in serialized
    ]
    if forbidden:
        output_trace.unlink(missing_ok=True)
        raise RuntimeError("sanitized Playwright trace still contains forbidden local data")
    return {
        "status": "pass",
        "trace": output_trace.name,
        "actual_playwright_trace": True,
        "retained_entry_count": len(retained_entries),
        "replacements": replacements,
        "resource_bodies_removed": True,
        "contains_private_values": False,
        "contains_runtime_token": False,
        "contains_absolute_local_path": False,
    }
