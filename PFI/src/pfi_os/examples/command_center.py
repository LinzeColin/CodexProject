from __future__ import annotations

import argparse
from pathlib import Path

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.executive import build_command_center, write_command_center


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the PFI_OS Executive Command Center snapshot.")
    parser.add_argument("--as-of", default=None, help="Audit date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--report-root", default=str(REPORT_ROOT_DIR), help="Formal report root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory. Defaults to data/commandCenter.")
    parser.add_argument("--artifact-limit", type=int, default=300, help="Reserved compatibility limit for local fallback builders.")
    parser.add_argument("--json-only", action="store_true", help="Build and print status without writing files.")
    args = parser.parse_args()

    common = {
        "as_of": args.as_of,
        "project_root": Path(args.project_root),
        "report_root": Path(args.report_root),
        "artifact_limit": args.artifact_limit,
    }
    if args.json_only:
        payload = build_command_center(**common)
    else:
        payload = write_command_center(output_dir=Path(args.output_dir) if args.output_dir else None, **common)
    print(
        "PFI_COMMAND_CENTER: "
        f"status={payload['command_status']} "
        f"actions={len(payload['action_queue'])} "
        f"as_of={payload['as_of']}"
    )
    if payload.get("outputs"):
        print(f"PFI_COMMAND_CENTER_OUTPUTS: {payload['outputs']}")


if __name__ == "__main__":
    main()
