from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from immutable_real_sources import load_locked_source_objects  # noqa: E402


PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_3"
FINAL_ACCEPTANCE = (
    PFI_ROOT / "reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json"
)


def _json(name: str) -> dict[str, object]:
    payload = json.loads((PHASE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_immutable_source_lock_survives_current_tree_migration() -> None:
    objects, attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    assert len(objects) == 4
    assert attestation["status"] == "pass"
    assert re.fullmatch(r"[0-9a-f]{40}", str(attestation["source_commit"]))
    assert attestation["source_commit"] != "HEAD"
    assert attestation["source_commit_reachable_from_head"] is True
    assert attestation["raw_filenames_emitted"] is False
    assert all(isinstance(row["content"], bytes) for row in objects)


def test_final_evidence_index_has_detached_hash_and_no_cycle() -> None:
    index_path = PHASE_DIR / "final_evidence_index.json"
    expected = hashlib.sha256(index_path.read_bytes()).hexdigest()
    detached = (PHASE_DIR / "final_evidence_index.sha256").read_text(
        encoding="utf-8"
    )
    assert detached == f"{expected}  final_evidence_index.json\n"
    index = _json("final_evidence_index.json")
    paths = {row["path"] for row in index["files"]}
    assert index["status"] == "remediation_candidate_ready_for_independent_rereview"
    assert index["coverage"]["stage_0_through_11_whole_stage_evidence_present"] is True
    assert re.fullmatch(r"[0-9a-f]{40}", str(index["candidate_git_commit"]))
    assert not any("phase_12_3" in path for path in paths)


def test_acceptance_request_is_exactly_bound_but_not_acceptance() -> None:
    request = _json("human_acceptance_request.json")
    index_hash = "sha256:" + hashlib.sha256(
        (PHASE_DIR / "final_evidence_index.json").read_bytes()
    ).hexdigest()
    assert request["version"] == "v0.2.5"
    assert request["app_build"] == "20260712.1"
    assert re.fullmatch(r"[0-9a-f]{40}", str(request["git_commit"]))
    assert request["git_commit"] == _json("final_evidence_index.json")[
        "candidate_git_commit"
    ]
    assert request["evidence_index_hash"] == index_hash
    assert request["explicit_confirmation_required"] is True
    assert request["prior_blanket_authorization_is_not_final_acceptance"] is True
    assert request["final_human_acceptance"] is False
    if FINAL_ACCEPTANCE.exists():
        acceptance = json.loads(FINAL_ACCEPTANCE.read_text(encoding="utf-8"))
        assert acceptance["product"] == "PFI"
        assert acceptance["version"] == "v0.2.5"
        assert acceptance["build_id"] == "pfi-v025-s1p1-20260712.1"
        assert acceptance["git_commit"] == request["git_commit"]
        assert acceptance["evidence_index_hash"] == index_hash
        assert acceptance["stage"] == 12
        assert len(acceptance["known_defects"]) == 5


def test_state_is_consistent_and_stops_before_final_gate() -> None:
    state = _json("state_consistency.json")
    assert state["status"] == "pass"
    assert all(state["checks"].values())
    assert state["progress"]["project_tasks"] == "155/156 (99.36%)"
    assert state["progress"]["stage_12_tasks"] == "11/12 (91.67%)"
    assert state["progress"]["next_task"] == "STAGE12-WHOLE-REVIEW-REMEDIATION"
    assert state["git"]["candidate_commit"] == _json(
        "human_acceptance_request.json"
    )["git_commit"]
    assert state["git"]["candidate_commit_exact_at_generation"] is True
    assert state["release_freeze_performed"] is False
    assert state["push_performed"] is False
    assert state["final_human_acceptance"] is False


def test_phase123_code_has_no_gui_file_operation_command() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            PFI_ROOT / "scripts/v025/prepare_release_freeze.py",
            PFI_ROOT / "scripts/v025/immutable_real_sources.py",
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
