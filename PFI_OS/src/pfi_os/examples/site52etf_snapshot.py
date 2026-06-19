from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.integrations.site52etf import (
    SITE52ETF_TIMEOUT_SECONDS,
    SITE52ETF_URL,
    build_site52etf_public_snapshot,
    write_site52etf_public_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh the PFI_OS 52ETF public read-only market-cloud snapshot.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to data/integrations/site52etf.")
    parser.add_argument("--source-url", default=SITE52ETF_URL, help="Public 52ETF page URL.")
    parser.add_argument("--timeout-seconds", type=int, default=SITE52ETF_TIMEOUT_SECONDS, help="Network timeout for the public page.")
    parser.add_argument("--source-html", default=None, help="Optional local HTML fixture; skips network when provided.")
    parser.add_argument("--json", action="store_true", help="Print PFIOS52ETFPublicSnapshotV1 as JSON.")
    parser.add_argument("--summary-json", action="store_true", help="Print a compact JSON summary.")
    args = parser.parse_args()

    html_text = Path(args.source_html).expanduser().read_text(encoding="utf-8") if args.source_html else None
    common = {
        "source_url": args.source_url,
        "timeout_seconds": args.timeout_seconds,
        "html_text": html_text,
    }
    if args.output_dir:
        payload = write_site52etf_public_snapshot(
            project_root=Path(args.project_root),
            output_dir=Path(args.output_dir).expanduser(),
            **common,
        )
    else:
        payload = build_site52etf_public_snapshot(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.summary_json:
        print(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str))
        return
    summary = _summary(payload)
    print(
        "PFI_OS_52ETF_PUBLIC_SNAPSHOT: "
        f"status={summary['status']} "
        f"artifact_status={summary['artifact_status']} "
        f"boards={summary['board_count']} "
        f"notes={summary['operating_note_count']} "
        f"cadence={summary['refresh_cadence_seconds']} "
        f"source={summary['source_url']}"
    )
    if payload.get("outputs"):
        print(f"PFI_OS_52ETF_PUBLIC_SNAPSHOT_OUTPUTS: {payload['outputs']}")


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "artifact_status": payload.get("artifact_status"),
        "source_url": payload.get("source_url"),
        "fetched_at": payload.get("fetched_at"),
        "board_count": payload.get("board_count"),
        "metric_count": payload.get("metric_count"),
        "operating_note_count": payload.get("operating_note_count"),
        "refresh_cadence_seconds": payload.get("refresh_cadence_seconds"),
        "evidence_status": payload.get("evidence_status"),
        "safety_boundary": payload.get("safety_boundary"),
    }


if __name__ == "__main__":
    main()
