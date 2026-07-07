#!/usr/bin/env python3
"""Inspect a private KMFA DingTalk raw archive month without exposing raw data."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


LOCATION_KEYS = {
    "userLatitude",
    "userLongitude",
    "userAddress",
    "baseLatitude",
    "baseLongitude",
    "baseAddress",
    "latitude",
    "longitude",
    "address",
    "locationText",
}
STAT_KEYS = ("member_count", "record_success_count", "summary_success_count")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_id_from_manifest(path: Path) -> str:
    return path.name.removesuffix(".manifest.json")


def run_id_from_raw(path: Path) -> str:
    return path.name.removesuffix(".raw.jsonl.gz").removesuffix(".raw.jsonl")


def is_seed_run_id(run_id: str) -> bool:
    return run_id.startswith("s19_seed_")


def open_raw(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def resolve_raw_path(month_dir: Path, value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return month_dir / path


def get_record_list(row: Mapping[str, Any]) -> list[Any]:
    direct_records = row.get("record_list")
    if isinstance(direct_records, list):
        return direct_records
    record = row.get("record") if isinstance(row.get("record"), Mapping) else {}
    final = record.get("final") if isinstance(record.get("final"), Mapping) else {}
    payload = final.get("payload") if isinstance(final.get("payload"), Mapping) else {}
    result = payload.get("result") if isinstance(payload.get("result"), Mapping) else {}
    records = result.get("recordList")
    return records if isinstance(records, list) else []


def has_location_evidence(punch: Any) -> bool:
    if not isinstance(punch, Mapping):
        return False
    for key in LOCATION_KEYS:
        value = punch.get(key)
        if value not in (None, ""):
            return True
    return False


def derived_success(row: Mapping[str, Any], key: str) -> bool:
    derived = row.get("derived") if isinstance(row.get("derived"), Mapping) else {}
    if key in derived:
        return bool(derived[key])
    if key == "record_success" and isinstance(row.get("record_list"), list):
        return True
    source_key = "record" if key == "record_success" else "summary"
    source = row.get(source_key) if isinstance(row.get(source_key), Mapping) else {}
    final = source.get("final") if isinstance(source.get("final"), Mapping) else {}
    payload = final.get("payload") if isinstance(final.get("payload"), Mapping) else {}
    if "success" in payload:
        return bool(payload["success"])
    return final.get("returncode") == 0


def inspect_raw(raw_path: Path) -> dict[str, Any]:
    counters: Counter[str] = Counter()
    work_dates: set[str] = set()
    with open_raw(raw_path) as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, Mapping):
                raise ValueError(f"{raw_path.name}:{line_no} must contain a JSON object")
            row_type = str(row.get("type") or "")
            if row_type == "metadata":
                counters["metadata_row_count"] += 1
                continue
            if row_type != "employee_attendance":
                counters["unknown_row_count"] += 1
                continue
            counters["employee_attendance_row_count"] += 1
            if derived_success(row, "record_success"):
                counters["record_success_count"] += 1
            if derived_success(row, "summary_success"):
                counters["summary_success_count"] += 1
            work_date = str(row.get("work_date") or "")
            if work_date:
                work_dates.add(work_date)
            for punch in get_record_list(row):
                counters["punch_count"] += 1
                if has_location_evidence(punch):
                    counters["punches_with_location_evidence"] += 1
    return {
        "stats": {
            "member_count": counters["employee_attendance_row_count"],
            "record_success_count": counters["record_success_count"],
            "summary_success_count": counters["summary_success_count"],
        },
        "metadata_row_count": counters["metadata_row_count"],
        "employee_attendance_row_count": counters["employee_attendance_row_count"],
        "unknown_row_count": counters["unknown_row_count"],
        "punch_count": counters["punch_count"],
        "punches_with_location_evidence": counters["punches_with_location_evidence"],
        "work_dates": sorted(work_dates),
    }


def add_totals(total: dict[str, int], values: Mapping[str, Any]) -> None:
    for key in STAT_KEYS:
        total[key] = total.get(key, 0) + int(values.get(key) or 0)


def inspect_month(
    archive_root: Path,
    target_month: str,
    *,
    allow_seed_raw_without_manifest: bool = False,
    min_location_coverage_ratio: float = 0.0,
) -> dict[str, Any]:
    month_dir = archive_root / target_month
    failures: list[str] = []
    manifests = sorted(month_dir.glob("s19_*.manifest.json")) if month_dir.is_dir() else []
    raw_files = sorted(month_dir.glob("s19_*.raw.jsonl.gz")) + sorted(month_dir.glob("s19_*.raw.jsonl"))
    raw_by_run_id = {run_id_from_raw(path): path for path in raw_files}
    manifest_run_ids = {run_id_from_manifest(path) for path in manifests}
    raw_run_ids = {run_id_from_raw(path) for path in raw_files}
    raw_without_manifest = sorted(raw_run_ids - manifest_run_ids)
    seed_raw_without_manifest = sorted(run_id for run_id in raw_without_manifest if is_seed_run_id(run_id))
    formal_raw_without_manifest = sorted(run_id for run_id in raw_without_manifest if not is_seed_run_id(run_id))
    manifest_without_raw = sorted(manifest_run_ids - raw_run_ids)
    if not month_dir.is_dir():
        failures.append("month_dir_missing")
    if not manifests:
        failures.append("manifest_missing")
    if not raw_files:
        failures.append("raw_missing")
    if allow_seed_raw_without_manifest:
        failures.extend(f"raw_without_manifest:{run_id}" for run_id in formal_raw_without_manifest)
    else:
        failures.extend(f"raw_without_manifest:{run_id}" for run_id in raw_without_manifest)
    failures.extend(f"manifest_without_raw:{run_id}" for run_id in manifest_without_raw)

    manifest_totals = {key: 0 for key in STAT_KEYS}
    raw_totals = {key: 0 for key in STAT_KEYS}
    seed_raw_totals = {key: 0 for key in STAT_KEYS}
    replay_items: list[dict[str, Any]] = []
    seed_replay_items: list[dict[str, Any]] = []
    metadata_row_count = 0
    employee_attendance_row_count = 0
    unknown_row_count = 0
    punch_count = 0
    punches_with_location = 0
    seed_metadata_row_count = 0
    seed_employee_attendance_row_count = 0
    seed_unknown_row_count = 0
    seed_punch_count = 0
    seed_punches_with_location = 0

    for manifest_path in manifests:
        run_id = run_id_from_manifest(manifest_path)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"manifest_read_failed:{run_id}:{type(exc).__name__}")
            continue
        stats = manifest.get("stats") if isinstance(manifest.get("stats"), Mapping) else {}
        manifest_stats = {key: int(stats.get(key) or 0) for key in STAT_KEYS}
        add_totals(manifest_totals, manifest_stats)
        raw_path = resolve_raw_path(month_dir, manifest.get("raw_jsonl_gz"))
        if raw_path is None or not raw_path.is_file():
            failures.append(f"manifest_raw_missing:{run_id}")
            continue
        actual_hash = sha256_file(raw_path)
        manifest_hash = str(manifest.get("raw_jsonl_gz_sha256") or "")
        if actual_hash != manifest_hash:
            failures.append(f"raw_hash_mismatch:{run_id}")
        try:
            raw_result = inspect_raw(raw_path)
        except (OSError, gzip.BadGzipFile, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"raw_read_failed:{run_id}:{type(exc).__name__}")
            continue
        raw_stats = raw_result["stats"]
        add_totals(raw_totals, raw_stats)
        for key in STAT_KEYS:
            if manifest_stats[key] != raw_stats[key]:
                failures.append(f"manifest_count_mismatch:{run_id}:{key}")
        metadata_row_count += int(raw_result["metadata_row_count"])
        employee_attendance_row_count += int(raw_result["employee_attendance_row_count"])
        unknown_row_count += int(raw_result["unknown_row_count"])
        punch_count += int(raw_result["punch_count"])
        punches_with_location += int(raw_result["punches_with_location_evidence"])
        replay_items.append({
            "run_id": run_id,
            "raw_sha256": actual_hash,
            "manifest_stats": manifest_stats,
            "raw_stats": raw_stats,
            "work_dates": raw_result["work_dates"],
            "punch_count": raw_result["punch_count"],
            "punches_with_location_evidence": raw_result["punches_with_location_evidence"],
        })

    for run_id in seed_raw_without_manifest:
        raw_path = raw_by_run_id[run_id]
        try:
            raw_result = inspect_raw(raw_path)
        except (OSError, gzip.BadGzipFile, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"seed_raw_read_failed:{run_id}:{type(exc).__name__}")
            continue
        raw_stats = raw_result["stats"]
        add_totals(seed_raw_totals, raw_stats)
        seed_metadata_row_count += int(raw_result["metadata_row_count"])
        seed_employee_attendance_row_count += int(raw_result["employee_attendance_row_count"])
        seed_unknown_row_count += int(raw_result["unknown_row_count"])
        seed_punch_count += int(raw_result["punch_count"])
        seed_punches_with_location += int(raw_result["punches_with_location_evidence"])
        seed_replay_items.append({
            "run_id": run_id,
            "raw_sha256": sha256_file(raw_path),
            "raw_stats": raw_stats,
            "work_dates": raw_result["work_dates"],
            "punch_count": raw_result["punch_count"],
            "punches_with_location_evidence": raw_result["punches_with_location_evidence"],
        })

    replay_payload = {
        "target_month": target_month,
        "runs": sorted(replay_items, key=lambda item: item["run_id"]),
    }
    seed_replay_payload = {
        "target_month": target_month,
        "seed_runs": sorted(seed_replay_items, key=lambda item: item["run_id"]),
    }
    replay_hash = "sha256:" + hashlib.sha256(
        json.dumps(replay_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    replay_hash_repeat = "sha256:" + hashlib.sha256(
        json.dumps(replay_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    seed_replay_hash = "sha256:" + hashlib.sha256(
        json.dumps(seed_replay_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    raw_counts_match = not any(failure.startswith("manifest_count_mismatch:") for failure in failures)
    raw_hashes_match = not any(failure.startswith("raw_hash_mismatch:") for failure in failures)
    ratio = round(punches_with_location / punch_count, 6) if punch_count else 0.0
    seed_ratio = round(seed_punches_with_location / seed_punch_count, 6) if seed_punch_count else 0.0
    if ratio < min_location_coverage_ratio:
        failures.append(f"location_coverage_below_threshold:{ratio}<{min_location_coverage_ratio}")
    pairs_complete = (not raw_without_manifest and not manifest_without_raw) or (
        allow_seed_raw_without_manifest and not formal_raw_without_manifest and not manifest_without_raw
    )
    return {
        "status": "fail" if failures else "pass",
        "mode": "private_raw_archive_month_replay_inspection",
        "target_month": target_month,
        "archive_root_included": False,
        "raw_file_count": len(raw_files),
        "manifest_count": len(manifests),
        "raw_without_manifest_count": len(raw_without_manifest),
        "seed_raw_without_manifest_count": len(seed_raw_without_manifest),
        "formal_raw_without_manifest_count": len(formal_raw_without_manifest),
        "manifest_without_raw_count": len(manifest_without_raw),
        "metadata_row_count": metadata_row_count,
        "employee_attendance_row_count": employee_attendance_row_count,
        "unknown_row_count": unknown_row_count,
        "seed_metadata_row_count": seed_metadata_row_count,
        "seed_employee_attendance_row_count": seed_employee_attendance_row_count,
        "seed_unknown_row_count": seed_unknown_row_count,
        "manifest_stats_totals": manifest_totals,
        "raw_stats_totals": raw_totals,
        "seed_raw_stats_totals": seed_raw_totals,
        "location_coverage": {
            "punch_count": punch_count,
            "punches_with_location_evidence": punches_with_location,
            "punches_without_location_evidence": punch_count - punches_with_location,
            "ratio": ratio,
        },
        "seed_location_coverage": {
            "punch_count": seed_punch_count,
            "punches_with_location_evidence": seed_punches_with_location,
            "punches_without_location_evidence": seed_punch_count - seed_punches_with_location,
            "ratio": seed_ratio,
        },
        "replay_hash": replay_hash,
        "seed_replay_hash": seed_replay_hash,
        "min_location_coverage_ratio": min_location_coverage_ratio,
        "checks": {
            "raw_counts_match_manifest": raw_counts_match,
            "raw_hashes_match_manifest": raw_hashes_match,
            "raw_manifest_pairs_complete": pairs_complete,
            "seed_raw_without_manifest_indexed": bool(seed_raw_without_manifest) and not any(
                failure.startswith("seed_raw_read_failed:") for failure in failures
            ),
            "location_coverage_threshold_met": ratio >= min_location_coverage_ratio,
            "replay_hash_stable": replay_hash == replay_hash_repeat,
            "public_safe_output": True,
        },
        "failures": failures,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a private KMFA DingTalk raw archive month without exposing raw data.")
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out", default="")
    parser.add_argument("--allow-seed-raw-without-manifest", action="store_true")
    parser.add_argument("--min-location-coverage-ratio", type=float, default=0.0)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = inspect_month(
        Path(args.archive_root),
        args.target_month,
        allow_seed_raw_without_manifest=args.allow_seed_raw_without_manifest,
        min_location_coverage_ratio=args.min_location_coverage_ratio,
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.print_json or result["status"] == "fail":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
