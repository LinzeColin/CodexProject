from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "WORD_REPORT_TYPES": "catalog",
    "artifact_counts": "catalog",
    "cleanup_report_junk": "catalog",
    "collect_report_artifacts": "catalog",
    "experiment_summaries_frame": "catalog",
    "filter_report_artifacts_frame": "catalog",
    "latest_report_artifact": "catalog",
    "load_experiment_detail": "catalog",
    "report_activity_frame": "catalog",
    "report_artifacts_frame": "catalog",
    "report_dashboard_cards": "catalog",
    "run_metadata_summaries_frame": "catalog",
    "run_status_counts_frame": "catalog",
    "search_report_artifacts_frame": "catalog",
    "strategy_run_summary_frame": "catalog",
    "REPORT_DECISION_COLUMNS": "decision_support",
    "build_report_decision_support_index": "decision_support",
    "report_decision_support_markdown": "decision_support",
    "write_report_decision_support_index": "decision_support",
    "export_backtest_docx": "export",
    "export_backtest_html": "export",
    "export_experiment_docx": "export",
    "export_strategy_review_docx": "export",
    "report_filename": "export",
    "unique_report_path": "export",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{_EXPORTS[name]}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
