from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.system.macos_public_acceptance import (
    build_macos_public_acceptance_summary,
    macos_public_acceptance_markdown,
    write_macos_public_acceptance_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a GitHub-safe macOS acceptance summary from local evidence.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="PFI_OS / PFIOS project root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for sanitized JSON/Markdown artifacts.")
    parser.add_argument("--runtime-evidence", default=None, help="Optional MacOSRuntimeAcceptance_latest.json path.")
    parser.add_argument("--ui-evidence", default=None, help="Optional UIVisualAcceptance_latest.json path.")
    parser.add_argument("--json", action="store_true", help="Print PFIOSMacOSPublicAcceptanceSummaryV1 as JSON.")
    parser.add_argument("--markdown", action="store_true", help="Print sanitized Markdown summary.")
    parser.add_argument("--summary-json", action="store_true", help="Print compact summary JSON.")
    args = parser.parse_args()

    common = {
        "project_root": Path(args.project_root),
        "runtime_evidence": Path(args.runtime_evidence).expanduser() if args.runtime_evidence else None,
        "ui_evidence": Path(args.ui_evidence).expanduser() if args.ui_evidence else None,
    }
    if args.output_dir:
        payload = write_macos_public_acceptance_summary(output_dir=Path(args.output_dir).expanduser(), **common)
    else:
        payload = build_macos_public_acceptance_summary(**common)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if args.markdown:
        print(macos_public_acceptance_markdown(payload))
        return
    if args.summary_json:
        print(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str))
        return
    summary = payload["summary"]
    print(
        "PFI_OS_MACOS_PUBLIC_ACCEPTANCE: "
        f"status={payload['status']} "
        f"sources_pass={summary['sources_pass']}/{summary['sources_total']} "
        f"runtime={summary['runtime_status']} "
        f"ui={summary['ui_status']}"
    )
    print(f"PFI_OS_MACOS_PUBLIC_ACCEPTANCE_NEXT_ACTION: {payload['next_action']}")
    if payload.get("outputs"):
        print(f"PFI_OS_MACOS_PUBLIC_ACCEPTANCE_OUTPUTS: {payload['outputs']}")


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "evidence_sources": payload.get("evidence_sources"),
        "coverage": payload.get("coverage"),
        "privacy_redaction": payload.get("privacy_redaction"),
        "heavy_smoke_policy": payload.get("heavy_smoke_policy"),
        "safety_boundary": payload.get("safety_boundary"),
        "outputs": payload.get("outputs"),
        "next_action": payload.get("next_action"),
    }


if __name__ == "__main__":
    main()
