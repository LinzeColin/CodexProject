#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    openapi_path = ROOT / "specs/api_contract.yaml"
    spec = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
    validate(spec)

    json_schema_paths = sorted((ROOT / "specs").glob("*.json"))
    for path in json_schema_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise AssertionError(f"{path} is not a JSON object")
        if "$schema" not in payload and "type" not in payload:
            raise AssertionError(f"{path} does not look like a JSON Schema")

    print("Contract validation: PASS")
    print(f"  openapi: {openapi_path.relative_to(ROOT)}")
    print(f"  json_schemas: {len(json_schema_paths)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Contract validation: FAIL - {exc}")
        raise SystemExit(1) from exc
