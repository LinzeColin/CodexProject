from __future__ import annotations

from typing import Any, Dict, List


RUN_SCOPED_ARTIFACT_KEYS = frozenset(
    {
        "pdf_run_copy",
        "bankroll_plan_run_copy",
        "dashboard_run_copy",
        "dashboard_data_run_copy",
        "manifest",
        "raw_refresh_diagnostics",
        "pdf_qa",
        "automation_preflight",
        "report_index",
        "report_index_report",
        "report_index_pdf",
        "report_intelligence",
        "report_intelligence_report",
        "report_intelligence_pdf",
    }
)

REQUIRED_RUN_ARTIFACT_KEYS = frozenset(
    {
        "pdf_run_copy",
        "bankroll_plan_run_copy",
        "dashboard_run_copy",
        "dashboard_data_run_copy",
        "manifest",
    }
)


def latest_commit_artifact_consistency_issues(payload: Dict[str, Any]) -> List[str]:
    """Return public latest-commit artifact pointer issues.

    A latest commit may reference stable convenience files, but run-scoped
    artifact keys must not point at *_latest files from a failed or newer run.
    """

    issues: List[str] = []
    run_id = str(payload.get("run_id") or "")
    artifacts = _dict_or_empty(payload.get("artifacts"))
    run_artifacts = _dict_or_empty(payload.get("run_artifacts"))

    for section_name, section in [("artifacts", artifacts), ("run_artifacts", run_artifacts)]:
        for key, value in section.items():
            name = str(value or "")
            if not name:
                continue
            if "/" in name or "\\" in name:
                issues.append(f"{section_name}.{key} is not a public artifact name")
            if name.startswith("."):
                issues.append(f"{section_name}.{key} points to a hidden/internal artifact")

    for key in sorted(REQUIRED_RUN_ARTIFACT_KEYS):
        if not run_artifacts.get(key):
            issues.append(f"run_artifacts.{key} is missing")

    for key in sorted(RUN_SCOPED_ARTIFACT_KEYS):
        for section_name, section in [("artifacts", artifacts), ("run_artifacts", run_artifacts)]:
            name = str(section.get(key) or "")
            if not name:
                continue
            if "_latest" in name:
                issues.append(f"{section_name}.{key} points to a latest artifact instead of a run artifact: {name}")
            if run_id and run_id not in name:
                issues.append(f"{section_name}.{key} does not include run_id {run_id}: {name}")

    for key, value in artifacts.items():
        name = str(value or "")
        if key.endswith("_latest") and name and "_latest" not in name:
            issues.append(f"artifacts.{key} should point to a *_latest artifact: {name}")

    return issues


def _dict_or_empty(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}
