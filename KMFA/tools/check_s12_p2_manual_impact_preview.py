#!/usr/bin/env python3
"""Validate KMFA S12-P2 public-safe manual impact preview artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.manual_impact_preview import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_PREVIEWS,
    read_json,
    read_jsonl,
    validate_manual_impact_preview_artifacts,
)
from KMFA.tools.manual_resolution_events import DEFAULT_OUTPUT_EVENTS as DEFAULT_SOURCE_EVENTS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S12-P2 manual impact preview.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--previews", type=Path, default=DEFAULT_OUTPUT_PREVIEWS)
    parser.add_argument("--source-events", type=Path, default=DEFAULT_SOURCE_EVENTS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    previews = read_jsonl(args.previews)
    source_events = read_jsonl(args.source_events)
    render_outputs = {"html": {"kmfa_manual_impact_preview": args.html.read_text(encoding="utf-8")}}
    validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, source_events)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P2 manual impact preview passed "
        f"(previews={summary['impact_preview_count']}, "
        f"projects={summary['affected_project_count']}, "
        f"metrics={summary['affected_metric_count']}, "
        f"reports={summary['affected_report_count']}, "
        f"high_risk={summary['high_risk_count']}, "
        f"blocked_publish={summary['blocked_publish_count']}, "
        "rerun=false, formal_report=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
