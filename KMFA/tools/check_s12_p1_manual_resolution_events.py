#!/usr/bin/env python3
"""Validate KMFA S12-P1 public-safe manual resolution event artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.manual_resolution_events import (
    DEFAULT_HTML_OUTPUT,
    DEFAULT_OUTPUT_EVENTS,
    DEFAULT_OUTPUT_MANIFEST,
    read_json,
    read_jsonl,
    validate_manual_resolution_event_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S12-P1 manual resolution events.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--events", type=Path, default=DEFAULT_OUTPUT_EVENTS)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_OUTPUT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    events = read_jsonl(args.events)
    render_outputs = {"html": {"kmfa_manual_resolution_workbench": args.html.read_text(encoding="utf-8")}}
    validate_manual_resolution_event_artifacts(manifest, events, render_outputs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S12-P1 manual resolution events passed "
        f"(events={summary['manual_event_count']}, "
        f"action_kinds={summary['manual_action_kind_count']}, "
        f"approved_events={summary['approved_event_count']}, "
        f"reverse_events={summary['reverse_event_count']}, "
        "raw_layer_write_allowed=false, approved_silent_update=false, "
        "impact_preview=false, rerun=false, formal_report_allowed=false, "
        "stage12_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
