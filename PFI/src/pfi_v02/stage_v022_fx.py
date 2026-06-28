from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


BASE_CURRENCY = "CNY"
DEFAULT_FX_BASE = "AUD"
DEFAULT_FX_QUOTE = "CNY"
DEFAULT_FX_PAIR = f"{DEFAULT_FX_BASE}/{DEFAULT_FX_QUOTE}"
DEFAULT_TIMEZONE = "Australia/Sydney"
DEFAULT_CUTOFF_LOCAL = "06:00"
FRANKFURTER_RATE_ENDPOINT = "https://api.frankfurter.dev/v2/rate/{base}/{quote}"
FX_SNAPSHOT_SCHEMA = "PFIV022FxSnapshotV1"
FX_LEDGER_AMOUNT_SCHEMA = "PFIV022LedgerAmountFieldsV1"


@dataclass(frozen=True)
class FxRateFetch:
    rate: Decimal
    provider_date: date
    source_url: str
    provider: str = "Frankfurter v2 public API"
    fetch_transport: str = "python_urllib_tls"


def default_fx_snapshot_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "fx_snapshots"


def parse_local_cutoff(value: str = DEFAULT_CUTOFF_LOCAL) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def local_datetime(value: datetime | None = None, *, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    tz = ZoneInfo(timezone_name)
    current = value or datetime.now(tz)
    if current.tzinfo is None:
        return current.replace(tzinfo=tz)
    return current.astimezone(tz)


def effective_fx_date(
    now: datetime | None = None,
    *,
    cutoff_local: str = DEFAULT_CUTOFF_LOCAL,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> date:
    """Return the local FX effective date.

    Stage 2 requires local time before 06:00 to use the previous effective FX
    day, while 06:00 and later use the current local day.
    """
    current = local_datetime(now, timezone_name=timezone_name)
    effective = current.date()
    if current.time() < parse_local_cutoff(cutoff_local):
        return effective - timedelta(days=1)
    return effective


def fx_snapshot_id(effective_date: date, *, base: str = DEFAULT_FX_BASE, quote: str = DEFAULT_FX_QUOTE) -> str:
    return f"fx_{base}_{quote}_{effective_date.strftime('%Y%m%d')}"


def fx_snapshot_path(
    snapshot_root: Path | None,
    effective_date: date,
    *,
    base: str = DEFAULT_FX_BASE,
    quote: str = DEFAULT_FX_QUOTE,
) -> Path:
    root = snapshot_root or default_fx_snapshot_root()
    return root / f"{base}_{quote}" / f"{effective_date.isoformat()}.json"


def frankfurter_rate_url(
    effective_date: date,
    *,
    base: str = DEFAULT_FX_BASE,
    quote: str = DEFAULT_FX_QUOTE,
) -> str:
    query = urlencode({"date": effective_date.isoformat()})
    return FRANKFURTER_RATE_ENDPOINT.format(base=base, quote=quote) + f"?{query}"


def fetch_frankfurter_rate(
    effective_date: date,
    *,
    base: str = DEFAULT_FX_BASE,
    quote: str = DEFAULT_FX_QUOTE,
    timeout_seconds: float = 10.0,
) -> FxRateFetch:
    source_url = frankfurter_rate_url(effective_date, base=base, quote=quote)
    request = Request(source_url, headers={"Accept": "application/json", "User-Agent": "PFI-v0.2.2-fx-snapshot"})
    transport = "python_urllib_tls"
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as error:
        # Some macOS Python installations lack a configured CA bundle while
        # system curl still verifies the same host successfully. This fallback
        # is only reachable from the explicit refresh path.
        payload = fetch_json_with_curl(source_url, timeout_seconds=timeout_seconds)
        transport = f"system_curl_fallback_after_{error.reason.__class__.__name__}"
    parsed = parse_frankfurter_rate_payload(payload, expected_base=base, expected_quote=quote)
    return FxRateFetch(
        rate=parsed["rate"],
        provider_date=parsed["provider_date"],
        source_url=source_url,
        fetch_transport=transport,
    )


def fetch_json_with_curl(source_url: str, *, timeout_seconds: float = 10.0) -> dict[str, Any]:
    result = subprocess.run(
        ["curl", "-fsSL", source_url],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return json.loads(result.stdout)


def parse_frankfurter_rate_payload(
    payload: dict[str, Any],
    *,
    expected_base: str = DEFAULT_FX_BASE,
    expected_quote: str = DEFAULT_FX_QUOTE,
) -> dict[str, Any]:
    base = str(payload.get("base", "")).upper()
    quote = str(payload.get("quote", "")).upper()
    if base != expected_base or quote != expected_quote:
        raise ValueError(f"Unexpected FX pair from provider: {base}/{quote}")
    provider_date = date.fromisoformat(str(payload["date"]))
    return {"rate": Decimal(str(payload["rate"])), "provider_date": provider_date}


def canonical_payload_for_hash(payload: dict[str, Any]) -> bytes:
    clone = dict(payload)
    clone.pop("hash", None)
    return json.dumps(clone, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload_for_hash(payload)).hexdigest()


def attach_snapshot_hash(payload: dict[str, Any]) -> dict[str, Any]:
    with_hash = dict(payload)
    with_hash["hash"] = payload_hash(with_hash)
    return with_hash


def validate_snapshot_hash(payload: dict[str, Any]) -> bool:
    return str(payload.get("hash", "")) == payload_hash(payload)


def build_fx_snapshot_payload(
    *,
    fetch: FxRateFetch,
    effective_date: date,
    fetched_at: datetime | None = None,
    base: str = DEFAULT_FX_BASE,
    quote: str = DEFAULT_FX_QUOTE,
    cutoff_local: str = DEFAULT_CUTOFF_LOCAL,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> dict[str, Any]:
    fetched = local_datetime(fetched_at, timezone_name=timezone_name)
    rate = fetch.rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    payload = {
        "schema": FX_SNAPSHOT_SCHEMA,
        "snapshot_id": fx_snapshot_id(effective_date, base=base, quote=quote),
        "effective_date": effective_date.isoformat(),
        "effective_time_local": cutoff_local,
        "timezone": timezone_name,
        "base_currency": BASE_CURRENCY,
        "display_pair": f"{base}/{quote}",
        "pair_base": base,
        "pair_quote": quote,
        "rate": str(rate),
        "rate_float": float(rate),
        "meaning_zh": f"1 {base} = {rate} {quote}",
        "source_provider": fetch.provider,
        "source_url": fetch.source_url,
        "fetch_transport": fetch.fetch_transport,
        "source_observed_date": fetch.provider_date.isoformat(),
        "fetched_at": fetched.isoformat(timespec="seconds"),
        "network_refresh_used": True,
        "ordinary_runtime_network_refresh": False,
        "cache_state": "cached",
    }
    return attach_snapshot_hash(payload)


def write_fx_snapshot(payload: dict[str, Any], snapshot_root: Path | None = None) -> Path:
    effective_date_value = date.fromisoformat(str(payload["effective_date"]))
    output_path = fx_snapshot_path(
        snapshot_root,
        effective_date_value,
        base=str(payload["pair_base"]),
        quote=str(payload["pair_quote"]),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def refresh_daily_fx_snapshot(
    *,
    snapshot_root: Path | None = None,
    now: datetime | None = None,
    allow_network: bool = False,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    if not allow_network:
        raise RuntimeError("Stage 2 forbids default network refresh; pass allow_network=True for an explicit daily FX refresh.")
    effective_date_value = effective_fx_date(now)
    fetch = fetch_frankfurter_rate(effective_date_value, timeout_seconds=timeout_seconds)
    payload = build_fx_snapshot_payload(fetch=fetch, effective_date=effective_date_value, fetched_at=now)
    write_fx_snapshot(payload, snapshot_root)
    return payload


def read_fx_snapshot(
    effective_date_value: date,
    *,
    snapshot_root: Path | None = None,
    base: str = DEFAULT_FX_BASE,
    quote: str = DEFAULT_FX_QUOTE,
) -> dict[str, Any]:
    path = fx_snapshot_path(snapshot_root, effective_date_value, base=base, quote=quote)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not validate_snapshot_hash(payload):
        raise ValueError(f"FX snapshot hash mismatch: {path}")
    return payload


def read_effective_fx_snapshot(
    *,
    snapshot_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    effective_date_value = effective_fx_date(now)
    return read_fx_snapshot(effective_date_value, snapshot_root=snapshot_root)


def missing_fx_snapshot_status(
    *,
    snapshot_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    effective_date_value = effective_fx_date(now)
    return {
        "status": "汇率数据待更新",
        "effective_date": effective_date_value.isoformat(),
        "expected_path": str(fx_snapshot_path(snapshot_root, effective_date_value)),
        "ordinary_runtime_network_refresh": False,
        "report_policy": "阻止生成新的正式报告，或将报告标记为汇率待更新。",
    }


def convert_amount_to_cny(original_amount: float | int | Decimal, original_currency: str, snapshot: dict[str, Any]) -> Decimal:
    amount = Decimal(str(original_amount))
    currency = original_currency.upper()
    if currency == BASE_CURRENCY:
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if currency == snapshot["pair_base"]:
        rate = Decimal(str(snapshot["rate"]))
        return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    raise ValueError(f"Missing CNY FX snapshot for {currency}.")


def amount_display_label(original_amount: float | int | Decimal, original_currency: str, snapshot: dict[str, Any]) -> str:
    amount_cny = convert_amount_to_cny(original_amount, original_currency, snapshot)
    rate = Decimal(str(snapshot["rate"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    original = Decimal(str(original_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"¥{amount_cny:,.2f} / 约 {original:,.2f} {original_currency.upper()} / {snapshot['display_pair']}={rate}"


def ledger_amount_fields(
    *,
    original_amount: float | int | Decimal,
    original_currency: str,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    amount_cny = convert_amount_to_cny(original_amount, original_currency, snapshot)
    return {
        "schema": FX_LEDGER_AMOUNT_SCHEMA,
        "original_amount": str(Decimal(str(original_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "original_currency": original_currency.upper(),
        "amount_cny": str(amount_cny),
        "fx_snapshot_id": snapshot["snapshot_id"],
        "fx_display_pair": snapshot["display_pair"],
        "fx_rate": snapshot["rate"],
    }


def build_default_fx_to_cny(snapshot: dict[str, Any] | None = None) -> dict[str, float]:
    snap = snapshot or read_effective_fx_snapshot()
    aud_to_cny = float(snap["rate"])
    return {
        "CNY": 1.0,
        "AUD": aud_to_cny,
        "USD": round(1.52 * aud_to_cny, 6),
        "HKD": round(0.195 * aud_to_cny, 6),
    }


def format_snapshot_badge(snapshot: dict[str, Any]) -> str:
    rate = Decimal(str(snapshot["rate"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    effective = date.fromisoformat(str(snapshot["effective_date"])).strftime("%Y%m%d")
    return f"{snapshot['display_pair']}={rate}（{effective}--{snapshot['effective_time_local']}）"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PFI v0.2.2 FX snapshot utility")
    sub = parser.add_subparsers(dest="command", required=True)
    refresh = sub.add_parser("refresh", help="explicitly fetch and cache the daily AUD/CNY snapshot")
    refresh.add_argument("--allow-network", action="store_true", help="required; prevents accidental per-run network refresh")
    refresh.add_argument("--snapshot-root", type=Path, default=None)
    read = sub.add_parser("read", help="read the effective local AUD/CNY snapshot without network")
    read.add_argument("--snapshot-root", type=Path, default=None)

    args = parser.parse_args(argv)
    if args.command == "refresh":
        payload = refresh_daily_fx_snapshot(snapshot_root=args.snapshot_root, allow_network=args.allow_network)
    else:
        try:
            payload = read_effective_fx_snapshot(snapshot_root=args.snapshot_root)
        except FileNotFoundError:
            payload = missing_fx_snapshot_status(snapshot_root=args.snapshot_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
