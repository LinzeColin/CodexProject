"""Test-only routing for the immutable v0.2.5 real-data snapshot.

The repository split intentionally removed the legacy top-level MetaDatabase
tree from HEAD.  Historical v0.2.5 tests must therefore replay the already
locked Git objects instead of treating the migrated directory as live state.
Runtime defaults remain unchanged; this adapter exists only in pytest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterator

import pytest

from pfi_os.application.metrics.model_validation import (
    build_stage5_private_surface_payload,
    run_phase53_real_model_validation,
)
from pfi_os.application.stage3_reconciliation import (
    run_phase33_real_reconciliation,
)
from pfi_v02.stage_v025_data_inventory import collect_data_root_inventory
from pfi_v02.stage_v025_safe_sandbox import (
    resolve_git_object_snapshot,
    run_git_object_read_parse_baseline,
)


PFI_ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOCK_PATH = PFI_ROOT / "config/sources/v025_immutable_real_source_lock.json"


def _locked_source_commit() -> str:
    payload = json.loads(SOURCE_LOCK_PATH.read_text(encoding="utf-8"))
    commit = payload.get("source_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise AssertionError("v0.2.5 immutable source lock has no valid source_commit")
    return commit


@pytest.fixture(scope="session", autouse=True)
def route_migrated_v025_sources_to_locked_git_objects() -> Iterator[None]:
    """Override only pytest call defaults; explicit git_ref values still win."""

    source_commit = _locked_source_commit()
    functions: tuple[Callable[..., object], ...] = (
        collect_data_root_inventory,
        resolve_git_object_snapshot,
        run_git_object_read_parse_baseline,
        run_phase33_real_reconciliation,
        run_phase53_real_model_validation,
        build_stage5_private_surface_payload,
    )
    original_defaults: list[tuple[Callable[..., object], dict[str, object]]] = []
    for function in functions:
        defaults = function.__kwdefaults__
        if defaults is None or "git_ref" not in defaults:
            raise AssertionError(f"{function.__name__} has no keyword-only git_ref default")
        original_defaults.append((function, defaults))
        function.__kwdefaults__ = {**defaults, "git_ref": source_commit}
    try:
        yield
    finally:
        for function, defaults in original_defaults:
            function.__kwdefaults__ = defaults
