from __future__ import annotations

import ast
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import pfi_v02.stage_v022_fx as legacy_fx
import pfi_v02.stage_v025_fx_policy as fx_module
from pfi_v02.stage_v025_fx_policy import (
    CUTOFF_LOCAL,
    FX_BASE_CURRENCY,
    FX_QUOTE_CURRENCY,
    TIMEZONE_NAME,
    build_fx_snapshot_status,
    build_network_audit,
    canonical_snapshot_hash,
    effective_fx_business_date,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
MODULE_PATH = PFI_ROOT / "src" / "pfi_v02" / "stage_v025_fx_policy.py"
POLICY_PATH = PFI_ROOT / "config" / "sources" / "v025_phase_2_2_fx_policy.json"
SNAPSHOT_SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "fx_snapshot_status.schema.json"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_2" / "phase_2_2"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _snapshot(effective_date: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "snapshot_id": f"fx_AUD_CNY_{effective_date.replace('-', '')}",
        "source_id": "SRC-FX-SNAPSHOT",
        "source_provider": "test-local-snapshot",
        "base_currency": FX_BASE_CURRENCY,
        "quote_currency": FX_QUOTE_CURRENCY,
        "direction": "AUD_TO_CNY",
        "effective_business_date": effective_date,
        "fx_effective_at": f"{effective_date}T06:00:00+10:00",
        "rate": "4.7000",
    }
    payload["source_hash"] = canonical_snapshot_hash(payload)
    return payload


@pytest.mark.parametrize(
    ("instant", "closed_dates", "expected"),
    [
        ("2026-07-13T05:59:59+10:00", set(), date(2026, 7, 10)),
        ("2026-07-13T06:00:00+10:00", set(), date(2026, 7, 13)),
        ("2026-07-11T12:00:00+10:00", set(), date(2026, 7, 10)),
        ("2026-07-14T05:59:59+10:00", {date(2026, 7, 13)}, date(2026, 7, 10)),
        ("2026-07-14T06:00:00+10:00", {date(2026, 7, 13)}, date(2026, 7, 14)),
        ("2026-10-04T18:59:59Z", set(), date(2026, 10, 2)),
        ("2026-10-04T19:00:00Z", set(), date(2026, 10, 5)),
    ],
)
def test_effective_date_uses_sydney_cutoff_weekends_explicit_holidays_and_dst(
    instant: str,
    closed_dates: set[date],
    expected: date,
) -> None:
    assert effective_fx_business_date(
        datetime.fromisoformat(instant.replace("Z", "+00:00")),
        explicit_closed_dates=closed_dates,
    ) == expected


def test_effective_date_rejects_ambiguous_inputs() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        effective_fx_business_date(datetime(2026, 7, 14, 6, 0))
    with pytest.raises(ValueError, match="HH:MM:SS"):
        effective_fx_business_date(
            datetime.fromisoformat("2026-07-14T06:00:00+10:00"),
            cutoff_local="6am",
        )
    with pytest.raises(TypeError, match="date objects"):
        effective_fx_business_date(
            datetime.fromisoformat("2026-07-14T06:00:00+10:00"),
            explicit_closed_dates={"2026-07-13"},  # type: ignore[arg-type]
        )


def test_snapshot_status_is_current_stale_or_blocked_without_inventing_a_rate() -> None:
    evaluated = datetime.fromisoformat("2026-07-14T08:00:00+10:00")
    registry_source = {
        "source_id": "SRC-FX-SNAPSHOT",
        "status": "not_loaded",
        "source_type": "fx_snapshot",
    }

    blocked = build_fx_snapshot_status(registry_source, snapshot=None, evaluated_at=evaluated)
    assert blocked["status"] == "not_loaded"
    assert blocked["stale_status"] == "unavailable"
    assert blocked["rate"] is None
    assert blocked["source_hash"] is None
    assert blocked["snapshot_id"] is None
    assert blocked["expected_effective_business_date"] == "2026-07-14"
    assert blocked["ordinary_runtime_network_allowed"] is False
    assert blocked["blocking_reason_zh"]

    current_source = dict(registry_source, status="ready")
    current = build_fx_snapshot_status(current_source, snapshot=_snapshot("2026-07-14"), evaluated_at=evaluated)
    assert current["status"] == "ready"
    assert current["stale_status"] == "current"
    assert current["stale_business_days"] == 0

    stale = build_fx_snapshot_status(current_source, snapshot=_snapshot("2026-07-10"), evaluated_at=evaluated)
    assert stale["status"] == "outdated"
    assert stale["stale_status"] == "stale"
    assert stale["stale_business_days"] == 2


def test_snapshot_hash_direction_and_future_date_fail_closed() -> None:
    evaluated = datetime.fromisoformat("2026-07-14T08:00:00+10:00")
    source = {"source_id": "SRC-FX-SNAPSHOT", "status": "ready"}
    bad_hash = _snapshot("2026-07-14")
    bad_hash["source_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        build_fx_snapshot_status(source, snapshot=bad_hash, evaluated_at=evaluated)

    wrong_direction = _snapshot("2026-07-14")
    wrong_direction["direction"] = "CNY_TO_AUD"
    wrong_direction["source_hash"] = canonical_snapshot_hash(wrong_direction)
    with pytest.raises(ValueError, match="direction"):
        build_fx_snapshot_status(source, snapshot=wrong_direction, evaluated_at=evaluated)

    future = _snapshot("2026-07-15")
    with pytest.raises(ValueError, match="future"):
        build_fx_snapshot_status(source, snapshot=future, evaluated_at=evaluated)


def test_policy_and_schema_define_direction_cutoff_and_zero_implicit_network() -> None:
    policy = _json(POLICY_PATH)
    schema = _json(SNAPSHOT_SCHEMA_PATH)

    assert policy["timezone"] == TIMEZONE_NAME == "Australia/Sydney"
    assert policy["cutoff_local"] == CUTOFF_LOCAL == "06:00:00"
    assert policy["pair"] == "AUD/CNY"
    assert policy["direction"] == "AUD_TO_CNY"
    assert policy["meaning"] == "1 AUD = rate CNY"
    assert policy["ordinary_runtime_network_allowed"] is False
    assert policy["holiday_policy"]["source"] == "explicit_source_closed_dates"
    assert policy["holiday_policy"]["fallback"] == "previous_open_business_date"
    assert policy["production_rate"] is None
    assert "4.81" not in POLICY_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(schema)


def test_normal_runtime_has_no_network_capability_and_legacy_refresh_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {"urllib", "requests", "httpx", "aiohttp", "socket"}
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module).split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)

    called = False

    def fail_fetch(*_args: object, **_kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("network fetch must not run")

    monkeypatch.setattr(legacy_fx, "fetch_frankfurter_rate", fail_fetch)
    with pytest.raises(RuntimeError, match="forbids default network refresh"):
        legacy_fx.refresh_daily_fx_snapshot(allow_network=False)
    assert called is False

    audit = build_network_audit(MODULE_PATH, POLICY_PATH)
    assert audit["status"] == "pass"
    assert audit["network_import_count"] == 0
    assert audit["network_call_count"] == 0
    assert audit["ordinary_runtime_network_allowed"] is False
    assert audit["finder_used"] is False


def test_tracked_snapshot_status_and_network_audit_are_deterministic_and_public_safe() -> None:
    status = _json(REPORT_ROOT / "fx_snapshot_status.json")
    audit = _json(REPORT_ROOT / "network_audit.json")
    schema = _json(SNAPSHOT_SCHEMA_PATH)

    Draft202012Validator(schema).validate(status)
    assert status["source_id"] == "SRC-FX-SNAPSHOT"
    assert status["status"] == "not_loaded"
    assert status["stale_status"] == "unavailable"
    assert status["rate"] is None
    assert status["source_hash"] is None
    assert status["legacy_reference"]["loaded_as_production"] is False
    assert status["private_values_included"] is False
    assert audit == build_network_audit(MODULE_PATH, POLICY_PATH)
    assert audit["status"] == "pass"
    assert audit["network_import_count"] == 0
    assert audit["network_call_count"] == 0


def test_phase22_privacy_scan_is_deterministic() -> None:
    tracked = (REPORT_ROOT / "privacy_scan.txt").read_text(encoding="utf-8")
    observed_at = next(
        line.removeprefix("observed_at=")
        for line in tracked.splitlines()
        if line.startswith("observed_at=")
    )
    assert fx_module.build_phase22_privacy_scan_report(REPO_ROOT, observed_at) == tracked
    assert tracked.splitlines()[0] == "PASS"
    assert "input_count=9" in tracked
    for counter in (
        "absolute_private_paths",
        "raw_filenames",
        "financial_row_values",
        "account_identifiers",
        "credentials",
        "sqlite_table_names",
        "finder_operations",
        "source_mutations",
        "financial_fixture_fallback",
    ):
        assert f"{counter}=0" in tracked


def test_snapshot_hash_is_sha256_of_canonical_content_without_hash_field() -> None:
    snapshot = _snapshot("2026-07-14")
    expected = hashlib.sha256(
        json.dumps(
            {key: value for key, value in snapshot.items() if key != "source_hash"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert snapshot["source_hash"] == f"sha256:{expected}"
