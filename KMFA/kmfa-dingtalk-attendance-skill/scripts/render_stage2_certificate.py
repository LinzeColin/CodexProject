#!/usr/bin/env python3
"""Render a compact Markdown certificate from stage2_consensus_certificate.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("certificate_json")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    data = json.loads(Path(args.certificate_json).read_text(encoding="utf-8"))
    lines = [
        f"# KMFA Stage-2 Payroll Baseline Certificate - {data.get('target_month')}",
        "",
        f"status: {data.get('stage2_status')}",
        f"accepted: {data.get('accepted')}",
        f"canonical_snapshot_hash: {data.get('canonical_snapshot_hash')}",
        "",
        "## Run matrix",
        "",
        "| Run | Hash | Quality | P0 | P1 | Failures |",
        "|---:|---|---|---:|---:|---|",
    ]
    for r in data.get("run_checks", []):
        lines.append(f"| {r.get('run_index')} | {r.get('hash') or ''} | {r.get('quality_grade') or ''} | {r.get('p0') if r.get('p0') is not None else ''} | {r.get('p1') if r.get('p1') is not None else ''} | {'; '.join(r.get('failures') or [])} |")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
