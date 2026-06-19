from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import V011_FINDINGS_BASELINE_SCHEMA, build_v011_findings_baseline


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_v011_findings_baseline_records_v02_p0_p1_scope_without_false_closure():
    baseline = build_v011_findings_baseline(
        PROJECT_ROOT,
        git_head="fd304d4",
        pr_url="https://github.com/LinzeColin/CodexProject/pull/2",
        now=datetime(2026, 6, 20, 0, 0, tzinfo=timezone.utc),
    )

    assert baseline["schema"] == V011_FINDINGS_BASELINE_SCHEMA
    assert baseline["iteration"] == "v0.1.1"
    assert baseline["status"] == "Review"
    assert baseline["finding_scope"]["source_count"] == 30
    assert baseline["finding_scope"]["p0_count"] == 12
    assert baseline["finding_scope"]["p1_count"] == 18
    assert baseline["status_counts"] == {"P0": 12, "P1": 18, "closed": 1, "partial": 18, "open": 11}
    assert baseline["missing_required_evidence_files"] == []
    assert "does not claim all v0.2 P0/P1 findings are closed" in baseline["completion_rule"]
    assert baseline["next_single_issue"].startswith("PFI-001")


def test_v011_findings_baseline_rejects_unsafe_follow_up_requests():
    baseline = build_v011_findings_baseline(PROJECT_ROOT)
    overrides = {row["request"]: row for row in baseline["policy_overrides"]}
    safety = baseline["safety_boundary"]

    assert overrides["future_live_auto_ordering"]["decision"] == "RejectedByPolicy"
    assert "OrderIntent" in overrides["future_live_auto_ordering"]["replacement"]
    assert overrides["private_data_in_public_git"]["decision"] == "RejectedByPolicy"
    assert "$PFI_OS_DATA_HOME" in overrides["private_data_in_public_git"]["replacement"]
    assert safety["research_only"] is True
    assert safety["human_review_required"] is True
    assert safety["autonomous_order_execution"] is False
    assert safety["private_data_in_public_git"] is False
    assert safety["secrets_in_public_git"] is False
