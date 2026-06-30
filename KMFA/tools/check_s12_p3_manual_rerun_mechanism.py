#!/usr/bin/env python3
"""Validate KMFA S12-P3 public-safe manual rerun mechanism artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.manual_impact_preview import DEFAULT_OUTPUT_PREVIEWS as DEFAULT_SOURCE_PREVIEWS
from KMFA.tools.manual_resolution_events import DEFAULT_OUTPUT_EVENTS as DEFAULT_SOURCE_EVENTS
from KMFA.tools.manual_rerun_mechanism import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_CONSISTENCY_CHECKS,
    DEFAULT_OUTPUT_INVALIDATIONS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_STEPS,
    read_json,
    read_jsonl,
    validate_manual_rerun_mechanism_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S12-P3 manual rerun mechanism.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--invalidations", type=Path, default=DEFAULT_OUTPUT_INVALIDATIONS)
    parser.add_argument("--steps", type=Path, default=DEFAULT_OUTPUT_STEPS)
    parser.add_argument("--consistency-checks", type=Path, default=DEFAULT_OUTPUT_CONSISTENCY_CHECKS)
    parser.add_argument("--source-events", type=Path, default=DEFAULT_SOURCE_EVENTS)
    parser.add_argument("--source-previews", type=Path, default=DEFAULT_SOURCE_PREVIEWS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    invalidations = read_jsonl(args.invalidations)
    rerun_steps = read_jsonl(args.steps)
    consistency_checks = read_jsonl(args.consistency_checks)
    source_events = read_jsonl(args.source_events)
    source_previews = read_jsonl(args.source_previews)
    render_outputs = {"html": {"kmfa_manual_rerun_mechanism": args.html.read_text(encoding="utf-8")}}
    validate_manual_rerun_mechanism_artifacts(
        manifest,
        invalidations,
        rerun_steps,
        consistency_checks,
        render_outputs,
        source_events,
        source_previews,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P3 manual rerun mechanism passed "
        f"(eligible={summary['eligible_event_count']}, "
        f"blocked_previews={summary['blocked_preview_count']}, "
        f"invalidations={summary['cache_invalidation_count']}, "
        f"rerun_steps={summary['rerun_step_count']}, "
        f"consistency_checks={summary['same_source_consistency_check_count']}, "
        "formal_report=false, stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
