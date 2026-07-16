from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from stage12_whole_review_final_acceptance import (  # noqa: E402
    ACCEPTANCE_REQUESTED_AT,
    EVIDENCE_INDEX_SHA256,
    FINAL_ACCEPTANCE,
    KNOWN_DEFECTS,
    OUTPUT_DIR,
    PRODUCT_CANDIDATE_COMMIT,
    REREVIEW_EVIDENCE_COMMIT,
    REVIEWED_CLOSURE_COMMIT,
    TASKPACK,
    expected_acceptance,
    verify,
)


def test_final_acceptance_is_exact_and_schema_valid() -> None:
    assert FINAL_ACCEPTANCE.is_file()
    payload = json.loads(FINAL_ACCEPTANCE.read_text(encoding="utf-8"))
    import zipfile

    with zipfile.ZipFile(TASKPACK) as archive:
        schema = json.loads(
            archive.read(
                "PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"
            )
        )
    Draft202012Validator(schema).validate(payload)
    assert payload == expected_acceptance()
    assert payload["git_commit"] == PRODUCT_CANDIDATE_COMMIT
    assert payload["evidence_index_hash"] == EVIDENCE_INDEX_SHA256
    assert REVIEWED_CLOSURE_COMMIT in payload["acceptance_statement"]
    assert REREVIEW_EVIDENCE_COMMIT in payload["acceptance_statement"]
    assert ACCEPTANCE_REQUESTED_AT in payload["acceptance_statement"]
    assert payload["known_defects"] == KNOWN_DEFECTS


def test_release_freeze_stops_before_delivery() -> None:
    freeze = json.loads(
        (OUTPUT_DIR / "release_freeze.json").read_text(encoding="utf-8")
    )
    assert freeze["status"] == "frozen_waiting_single_delivery_transaction"
    assert freeze["release_freeze_performed"] is True
    assert freeze["final_human_acceptance"] is True
    assert freeze["push_performed"] is False
    assert freeze["app_reinstall_performed"] is False
    assert freeze["production_accepted"] is False
    assert freeze["finder_used"] is False


def test_final_acceptance_pack_verifies() -> None:
    result = verify()
    assert result["status"] == "pass"
    assert all(result["checks"].values())


def test_finalizer_contains_no_gui_command_invocation() -> None:
    source = (
        PFI_ROOT / "scripts/v025/stage12_whole_review_final_acceptance.py"
    ).read_text(encoding="utf-8")
    forbidden_command_literals = (
        '["open"',
        "['open'",
        '["osascript"',
        "['osascript'",
        '["lsregister"',
        "['lsregister'",
    )
    assert not any(marker in source for marker in forbidden_command_literals)
