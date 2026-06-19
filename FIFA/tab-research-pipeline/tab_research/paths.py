from __future__ import annotations

import os
from pathlib import Path


def resolve_workspace_root(anchor: Path) -> Path:
    override = os.getenv("TAB_FIFA_WORKSPACE_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    current = Path(anchor).resolve()
    if current.is_file():
        current = current.parent
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "outputs").exists() and (candidate / "work" / "tab-research-pipeline").exists():
            return candidate
    for candidate in candidates:
        if (candidate / "tab-research-pipeline").exists() and ((candidate / "AGENTS.md").exists() or (candidate / ".git").exists()):
            return candidate
    return current


def resolve_output_dir(anchor: Path) -> Path:
    override = os.getenv("TAB_FIFA_OUTPUT_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return resolve_workspace_root(anchor) / "outputs"


def resolve_private_dir(anchor: Path, *parts: str) -> Path:
    base = os.getenv("TAB_FIFA_PRIVATE_DIR")
    if base:
        root = Path(base).expanduser().resolve()
    else:
        root = resolve_workspace_root(anchor) / "work" / "private" / "tab_fifa"
    return root.joinpath(*parts) if parts else root
