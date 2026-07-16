#!/usr/bin/env python3
"""Write one minimized, read-only PFI Context v1 artifact for Alpha."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pfi_os.security.pfi_context_export import (  # noqa: E402
    CONTEXT_PAYLOAD_FIELDS,
    ContextExportError,
    build_pfi_context_export,
    write_new_context_export,
)


INPUT_FIELDS = ("as_of", "source_or_read_model_hash", *CONTEXT_PAYLOAD_FIELDS)
MAX_INPUT_BYTES = 64 * 1024


def _load_input(path_value: Path) -> dict[str, object]:
    if path_value.is_symlink() or not path_value.is_file():
        raise ContextExportError("context input must be a regular non-symlink file")
    if path_value.stat().st_size > MAX_INPUT_BYTES:
        raise ContextExportError("context input exceeds the 64 KiB state-only limit")
    try:
        payload = json.loads(path_value.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContextExportError("context input is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ContextExportError("context input must be a JSON object")
    if set(payload) != set(INPUT_FIELDS):
        raise ContextExportError("context input fields do not match the minimized contract")
    return payload


def _build_from_input(payload: dict[str, object]) -> dict[str, object]:
    tags = payload["investment_behavior_tags"]
    if not isinstance(tags, list):
        raise ContextExportError("investment_behavior_tags must be a JSON array")
    return build_pfi_context_export(
        as_of=str(payload["as_of"]),
        source_or_read_model_hash=str(payload["source_or_read_model_hash"]),
        net_worth_state=str(payload["net_worth_state"]),
        investable_cash_state=str(payload["investable_cash_state"]),
        cashflow_pressure=str(payload["cashflow_pressure"]),
        asset_allocation=str(payload["asset_allocation"]),
        risk_budget=str(payload["risk_budget"]),
        investment_behavior_tags=[str(item) for item in tags],
        consumption_pressure_summary=str(payload["consumption_pressure_summary"]),
        data_freshness=str(payload["data_freshness"]),
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        payload = _build_from_input(_load_input(args.input))
        receipt = write_new_context_export(payload, args.output)
    except ContextExportError as exc:
        print(
            json.dumps(
                {
                    "schema": "PFIV025ContextExportCLIErrorV1",
                    "status": "rejected",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "contains_path": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
