#!/usr/bin/env python3
"""Validate KMFA S18-P3 integration preparation artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.integration_preparation import (
    DEFAULT_OUTPUT_BACKLOG,
    DEFAULT_OUTPUT_CONNECTORS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_OPME,
    read_json,
    read_jsonl,
    validate_integration_preparation_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S18-P3 integration preparation artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--connectors", type=Path, default=DEFAULT_OUTPUT_CONNECTORS)
    parser.add_argument("--opme", type=Path, default=DEFAULT_OUTPUT_OPME)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_OUTPUT_BACKLOG)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    connector_plans = read_jsonl(args.connectors)
    opme_plan = read_json(args.opme)
    backlog_items = read_jsonl(args.backlog)
    validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)
    print(
        "PASS: KMFA S18-P3 integration preparation check passed "
        f"(connectors={len(connector_plans)}, "
        f"opme_surfaces={len(opme_plan['entry_surfaces'])}, "
        f"backlog={len(backlog_items)}, "
        "live_connector_called=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
