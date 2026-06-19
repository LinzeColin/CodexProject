from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


LOCAL_PATH_RE = re.compile(r"/Users/[^\s`'\"|)\]}]+")


def display_path(root: Path, value: object | None) -> str:
    if value in (None, ""):
        return "none"
    text = str(value)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"}:
        return text
    path = Path(text).expanduser()
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return f"external:{path.name}"


def redact_text_for_markdown(root: Path, text: object | None) -> str:
    if text is None:
        return ""
    redacted = str(text)
    root_prefix = root.resolve(strict=False).as_posix()
    redacted = redacted.replace(root_prefix + "/", "")
    if redacted == root_prefix:
        return "."

    def replace_local_path(match: re.Match[str]) -> str:
        raw = match.group(0)
        trailing = ""
        while raw and raw[-1] in ".,;:":
            trailing = raw[-1] + trailing
            raw = raw[:-1]
        return display_path(root, raw) + trailing

    return LOCAL_PATH_RE.sub(replace_local_path, redacted)


def redact_value_for_markdown(root: Path, value: object) -> object:
    if isinstance(value, dict):
        return {str(key): redact_value_for_markdown(root, item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value_for_markdown(root, item) for item in value]
    if isinstance(value, tuple):
        return [redact_value_for_markdown(root, item) for item in value]
    if isinstance(value, str):
        return redact_text_for_markdown(root, value)
    return value
