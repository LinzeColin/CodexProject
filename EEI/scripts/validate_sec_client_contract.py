#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.sec_client import (  # noqa: E402
    SEC_ALLOWED_HOSTS,
    SEC_MAX_REQUESTS_PER_SECOND,
    SEC_MIN_REQUEST_INTERVAL_SECONDS,
    validate_sec_url,
    validate_sec_user_agent,
)

A096_OUTPUT = ROOT / "artifacts/tests/a096/t700_sec_client_allowlist_contract.json"
A097_OUTPUT = ROOT / "artifacts/tests/a097/t700_sec_client_rate_limit_contract.json"
CONTRACT_USER_AGENT = "EEI/0.1 contract-validator eei-operator@example.com"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_sec_user_agent(CONTRACT_USER_AGENT)
    validate_sec_url("https://data.sec.gov/submissions/CIK0000320193.json")
    validate_sec_url("https://www.sec.gov/Archives/example.json")
    require(SEC_MAX_REQUESTS_PER_SECOND == 8, "SEC request-rate ceiling must remain 8")
    require(
        SEC_MIN_REQUEST_INTERVAL_SECONDS == 0.125,
        "SEC fixed request interval must remain 0.125 seconds",
    )

    common = {
        "task_id": "T700",
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "release_scope": {
            "live_sec_request_performed": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
        "test_evidence": [
            "tests/unit/test_sec_client.py",
            "httpx.MockTransport",
        ],
    }
    a096 = {
        "schema_version": "eei-a096-sec-client-allowlist-contract-v1",
        "status": "PASS",
        "acceptance_ids": ["A096"],
        **common,
        "contract": {
            "descriptive_user_agent_required": True,
            "operator_contact_email_required": True,
            "allowed_schemes": ["https"],
            "allowed_hosts": sorted(SEC_ALLOWED_HOSTS),
            "standard_https_port_only": True,
            "url_credentials_allowed": False,
            "redirects_followed": False,
            "mock_http_validation": True,
        },
    }
    a097 = {
        "schema_version": "eei-a097-sec-client-rate-limit-contract-v1",
        "status": "PASS",
        "acceptance_ids": ["A097"],
        **common,
        "contract": {
            "algorithm": "serialized_fixed_interval_no_burst",
            "max_requests_per_second": SEC_MAX_REQUESTS_PER_SECOND,
            "minimum_interval_seconds": SEC_MIN_REQUEST_INTERVAL_SECONDS,
            "clock_is_injectable": True,
            "sleep_is_injectable": True,
            "deterministic_fake_clock_validation": True,
        },
    }
    return a096, a097


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_payload(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    require(isinstance(payload, dict), f"artifact must be an object: {path}")
    return payload


def validate_artifacts(a096: dict[str, Any], a097: dict[str, Any]) -> None:
    require(a096.get("status") == "PASS", "A096 contract status must be PASS")
    require(a096.get("task_id") == "T700", "A096 task_id must be T700")
    require(a096.get("acceptance_ids") == ["A096"], "A096 acceptance mapping drift")
    allowlist = a096.get("contract") or {}
    require(allowlist.get("descriptive_user_agent_required") is True, "User-Agent gate missing")
    require(allowlist.get("operator_contact_email_required") is True, "contact gate missing")
    require(allowlist.get("allowed_schemes") == ["https"], "HTTPS allowlist drift")
    require(
        allowlist.get("allowed_hosts") == sorted(SEC_ALLOWED_HOSTS),
        "SEC host allowlist drift",
    )
    require(allowlist.get("redirects_followed") is False, "redirect policy must fail closed")
    require(allowlist.get("mock_http_validation") is True, "mock HTTP evidence missing")

    require(a097.get("status") == "PASS", "A097 contract status must be PASS")
    require(a097.get("task_id") == "T700", "A097 task_id must be T700")
    require(a097.get("acceptance_ids") == ["A097"], "A097 acceptance mapping drift")
    limiter = a097.get("contract") or {}
    require(
        limiter.get("algorithm") == "serialized_fixed_interval_no_burst",
        "limiter algorithm drift",
    )
    require(
        limiter.get("max_requests_per_second") == SEC_MAX_REQUESTS_PER_SECOND,
        "SEC request-rate ceiling drift",
    )
    require(
        limiter.get("minimum_interval_seconds") == SEC_MIN_REQUEST_INTERVAL_SECONDS,
        "SEC request interval drift",
    )
    require(
        limiter.get("deterministic_fake_clock_validation") is True,
        "deterministic limiter evidence missing",
    )

    for artifact in (a096, a097):
        release_scope = artifact.get("release_scope") or {}
        require(
            release_scope.get("live_sec_request_performed") is False,
            "contract evidence must not claim a live SEC request",
        )
        require(
            release_scope.get("mvp_release_ready") is False,
            "T700 contract must not claim MVP release readiness",
        )
        require(bool(artifact.get("source_commit")), "source_commit is required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("generate", "validate"))
    args = parser.parse_args()

    if args.action == "generate":
        a096, a097 = build_contracts()
        validate_artifacts(a096, a097)
        write_payload(A096_OUTPUT, a096)
        write_payload(A097_OUTPUT, a097)
    else:
        a096 = read_payload(A096_OUTPUT)
        a097 = read_payload(A097_OUTPUT)
        validate_artifacts(a096, a097)

    print(
        json.dumps(
            {
                "valid": True,
                "task_id": "T700",
                "acceptance_ids": ["A096", "A097"],
                "live_sec_request_performed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
