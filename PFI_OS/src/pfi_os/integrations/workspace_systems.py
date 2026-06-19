from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from pfi_os.config import PROJECT_ROOT


WORKSPACE_SYSTEM_IDS = ("finance_ledger", "industry_research", "policy_intelligence")
WORKSPACE_SYSTEM_SCHEMA = "WorkspaceSystemSummaryV1"
MAX_LIST_ITEMS = 3


@dataclass(frozen=True)
class WorkspaceSystemSummary:
    system_id: str
    display_name: str
    adapter_status: str
    migration_status: str
    migration_phase: str
    workspace_root: str
    source_root: str
    source_root_exists: bool
    sample_file_count: int
    entrypoints: tuple[str, ...]
    verification: tuple[str, ...]
    next_actions: tuple[str, ...]
    data_policy: dict[str, Any]
    legacy_root_count: int
    token_policy: str = "compact_summary_no_legacy_paths_no_private_runtime_data"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entrypoints"] = list(self.entrypoints)
        payload["verification"] = list(self.verification)
        payload["next_actions"] = list(self.next_actions)
        return payload


def workspace_systems_root(path: Path | str | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    override = os.environ.get("PFI_SYSTEMS_ROOT", "").strip()
    return Path(override).expanduser() if override else PROJECT_ROOT / "systems"


def workspace_manifest_path(system_id: str, *, systems_root: Path | str | None = None) -> Path:
    return workspace_systems_root(systems_root) / str(system_id) / "SYSTEM_MANIFEST.json"


def load_workspace_system_summary(system_id: str, *, systems_root: Path | str | None = None) -> WorkspaceSystemSummary:
    manifest_path = workspace_manifest_path(system_id, systems_root=systems_root)
    if not manifest_path.exists():
        system_root = manifest_path.parent
        return WorkspaceSystemSummary(
            system_id=str(system_id),
            display_name=str(system_id),
            adapter_status="MissingManifest",
            migration_status="missing",
            migration_phase="missing",
            workspace_root=_compact_path(system_root),
            source_root="",
            source_root_exists=False,
            sample_file_count=0,
            entrypoints=(),
            verification=(),
            next_actions=("restore SYSTEM_MANIFEST.json before ResearchBus registration",),
            data_policy={},
            legacy_root_count=0,
        )

    manifest = _load_json(manifest_path)
    system_root = manifest_path.parent
    source_root = _source_root(manifest, system_root)
    source_exists = source_root.exists()
    status = str(manifest.get("status") or "")
    migration_phase = str(manifest.get("migration_phase") or "")
    adapter_status = "Ready" if source_exists and status in {"source_migrated", "ready", "active"} else "Review"
    return WorkspaceSystemSummary(
        system_id=str(manifest.get("system_id") or system_id),
        display_name=str(manifest.get("display_name") or system_id),
        adapter_status=adapter_status,
        migration_status=status,
        migration_phase=migration_phase,
        workspace_root=_compact_path(system_root),
        source_root=_compact_path(source_root),
        source_root_exists=source_exists,
        sample_file_count=_sample_file_count(system_root),
        entrypoints=_compact_list(manifest.get("entrypoints", [])),
        verification=_compact_list(manifest.get("verification", [])),
        next_actions=_compact_list(manifest.get("next_actions", [])),
        data_policy=_compact_data_policy(manifest.get("data_policy", {})),
        legacy_root_count=len(manifest.get("legacy_local_roots", []) or []),
    )


def load_workspace_system_summaries(
    *,
    systems_root: Path | str | None = None,
    system_ids: Iterable[str] = WORKSPACE_SYSTEM_IDS,
) -> tuple[WorkspaceSystemSummary, ...]:
    return tuple(load_workspace_system_summary(system_id, systems_root=systems_root) for system_id in system_ids)


def compact_workspace_system_payload(
    *,
    systems_root: Path | str | None = None,
    system_ids: Iterable[str] = WORKSPACE_SYSTEM_IDS,
) -> dict[str, Any]:
    summaries = load_workspace_system_summaries(systems_root=systems_root, system_ids=system_ids)
    ready = [item.system_id for item in summaries if item.adapter_status == "Ready"]
    review = [item.system_id for item in summaries if item.adapter_status != "Ready"]
    return {
        "schema": WORKSPACE_SYSTEM_SCHEMA,
        "systems_root": str(workspace_systems_root(systems_root)),
        "system_count": len(summaries),
        "ready_count": len(ready),
        "review_count": len(review),
        "ready_systems": ready,
        "review_systems": review,
        "systems": [item.to_dict() for item in summaries],
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    return payload


def _source_root(manifest: dict[str, Any], system_root: Path) -> Path:
    source = Path(str(manifest.get("source_root") or ""))
    if source.is_absolute():
        return source
    if source.parts and source.parts[0] == "systems":
        return PROJECT_ROOT / source
    return system_root / source


def _compact_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def _sample_file_count(system_root: Path) -> int:
    sample_root = system_root / "source" / "data" / "sample"
    if not sample_root.exists():
        sample_root = system_root / "samples"
    if not sample_root.exists():
        return 0
    return sum(1 for item in sample_root.rglob("*") if item.is_file() and not item.name.startswith("."))


def _compact_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value[:MAX_LIST_ITEMS] if str(item).strip())


def _compact_data_policy(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): value[key] for key in sorted(value)[:MAX_LIST_ITEMS]}
