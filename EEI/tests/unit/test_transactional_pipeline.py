from __future__ import annotations

from copy import deepcopy

from apps.api.app.ingest.transactional_pipeline import (
    classify_change_types,
    publication_fields_unchanged,
)


def test_new_stale_document_emits_created_and_stale() -> None:
    assert classify_change_types(
        previous_payload=None,
        current_payload={"title": "initial"},
        source_active=True,
        review_status="machine_verified",
        stale=True,
    ) == ["created", "stale"]


def test_changed_disputed_inactive_document_emits_full_change_set() -> None:
    assert classify_change_types(
        previous_payload={"title": "before"},
        current_payload={"title": "after"},
        source_active=False,
        review_status="disputed",
        stale=True,
    ) == ["updated", "superseded", "conflict_detected", "revoked", "stale"]


def test_unchanged_current_document_emits_no_change() -> None:
    payload = {"title": "stable", "nested": {"value": 1}}

    assert classify_change_types(
        previous_payload=deepcopy(payload),
        current_payload=payload,
        source_active=True,
        review_status="machine_verified",
        stale=False,
    ) == []


def test_failure_audit_may_add_change_without_publication_state_drift() -> None:
    before = {
        "fact_version_count": 10,
        "scoring_run_count": 4,
        "score_result_count": 20,
        "change_count": 8,
        "active_data_snapshot_id": "data-before",
        "active_scoring_run_id": "score-before",
        "refresh_token": "refresh-before",
        "refresh_generation": 3,
    }
    after = {**before, "change_count": 9}

    assert publication_fields_unchanged(before, after) is True

    after["score_result_count"] = 21
    assert publication_fields_unchanged(before, after) is False
