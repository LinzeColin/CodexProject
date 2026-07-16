from __future__ import annotations

import json
from pathlib import Path
import plistlib
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from stage12_whole_review_remediation import (  # noqa: E402
    FINAL_ACCEPTANCE,
    RELEASE_SOURCE_COMMIT,
    entry_audit,
    exact_binding_audit,
    quarantine_old_app,
    release_identity_audit,
    _git_text,
    _is_ancestor,
)


def _fake_app(root: Path, *, version: str, build: str) -> None:
    contents = root / "Contents"
    executable = contents / "MacOS/PFI"
    marker = contents / "Resources/PFI_PROJECT_ROOT"
    executable.parent.mkdir(parents=True)
    marker.parent.mkdir(parents=True)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleShortVersionString": version,
                "CFBundleVersion": build,
                "CFBundleIdentifier": "com.linze.pfi.test-old",
            }
        )
    )
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    marker.write_text("test-project\n", encoding="utf-8")


def test_cli_quarantine_is_atomic_reversible_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "downloads/PFI.app"
    target = tmp_path / "private/PFI-v0.2.3-20260629.1.app"
    receipt = tmp_path / "receipt/entry_quarantine.json"
    canonical = tmp_path / "applications/PFI.app"
    _fake_app(source, version="0.2.3", build="20260629.1")
    _fake_app(canonical, version="0.2.5", build="20260712.1")

    first = quarantine_old_app(
        source=source,
        target=target,
        receipt_path=receipt,
        canonical_app=canonical,
    )
    second = quarantine_old_app(
        source=source,
        target=target,
        receipt_path=receipt,
        canonical_app=canonical,
    )

    assert first["moved_this_run"] is True
    assert second["idempotent_recheck"] is True
    assert not source.exists()
    assert target.is_dir()
    assert first["bundle_tree_sha256"] == second["bundle_tree_sha256"]
    public = receipt.read_text(encoding="utf-8")
    assert str(tmp_path) not in public
    assert "$HOME/Downloads/PFI.app" in public
    assert first["finder_used"] is False
    assert first["deletion_performed"] is False


def test_release_source_and_candidate_identity_are_exact() -> None:
    index = json.loads(
        (
            PFI_ROOT
            / "reports/pfi_v025/stage_12/phase_12_3/final_evidence_index.json"
        ).read_text(encoding="utf-8")
    )
    candidate = str(index["candidate_git_commit"])
    head = _git_text("rev-parse", "HEAD")
    audit = release_identity_audit(candidate)
    head_audit = release_identity_audit(head)
    assert audit["status"] == "pass"
    assert head_audit["status"] == "pass"
    assert audit["release_source_commit"] == RELEASE_SOURCE_COMMIT
    assert audit["latest_runtime_payload_commit"] == RELEASE_SOURCE_COMMIT
    assert audit["changed_runtime_payload_file_count"] == 0
    assert head_audit["changed_runtime_payload_file_count"] == 0
    assert _is_ancestor(candidate, head)
    assert all(audit["checks"].values())


def test_phase123_binding_has_no_self_or_stale_head() -> None:
    index = json.loads(
        (
            PFI_ROOT
            / "reports/pfi_v025/stage_12/phase_12_3/final_evidence_index.json"
        ).read_text(encoding="utf-8")
    )
    candidate = str(index["candidate_git_commit"])
    audit = exact_binding_audit(candidate)
    assert audit["status"] == "pass"
    assert re.fullmatch(r"[0-9a-f]{40}", audit["candidate_commit"])
    assert audit["indexed_file_mismatch_count"] == 0
    assert all(audit["checks"].values())
    assert audit["final_human_acceptance"] is FINAL_ACCEPTANCE.exists()


def test_live_cli_entry_census_has_no_noncanonical_copy() -> None:
    audit = entry_audit()
    assert audit["status"] == "pass"
    assert audit["noncanonical_entry_mismatch_count"] == 0
    assert all(audit["checks"].values())
    assert audit["canonical_app_modified"] is False


def test_remediation_sources_have_no_gui_file_operation_command() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            PFI_ROOT / "scripts/v025/stage12_whole_review_remediation.py",
            PFI_ROOT / "scripts/v025/prepare_release_freeze.py",
        )
    )
    forbidden_command_literals = (
        '["open"',
        "['open'",
        '["osascript"',
        "['osascript'",
        '["lsregister"',
        "['lsregister'",
    )
    assert not any(marker in sources for marker in forbidden_command_literals)


def test_closed_findings_remain_pending_independent_rereview_when_present() -> None:
    path = (
        PFI_ROOT
        / "reports/pfi_v025/stage_12/whole_stage_review/remediation/closed_findings.json"
    )
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["closed_finding_count"] == 3
    assert payload["remediation_open_p0_count"] == 0
    assert payload["remediation_open_p1_count"] == 0
    assert payload["rereview_status"] == "not_started"
    assert payload["stage_12_accepted"] is False
