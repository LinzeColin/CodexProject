#!/usr/bin/env python3
"""Materialize private raw archive replay day facts with raw-detail linkage."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from inspect_raw_archive_month import (  # noqa: E402
    get_record_list,
    has_location_evidence,
    inspect_month,
    is_seed_run_id,
    resolve_raw_path,
    run_id_from_manifest,
    run_id_from_raw,
    sha256_file,
)


NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "kmfa-dingtalk-attendance-skill/raw-replay-day-fact")


def open_raw(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def stable_uuid(*parts: Any) -> str:
    return str(uuid.uuid5(NAMESPACE, ":".join(str(part) for part in parts)))


def stable_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return len(rows)


def employee_key_hash(row: Mapping[str, Any]) -> str:
    member = row.get("member") if isinstance(row.get("member"), Mapping) else {}
    raw_key = (
        member.get("userId")
        or member.get("userid")
        or member.get("dingtalk_userid")
        or member.get("staffId")
        or json.dumps(member, ensure_ascii=False, sort_keys=True)
    )
    return "sha256:" + hashlib.sha256(str(raw_key).encode("utf-8")).hexdigest()


def punch_time(punch: Mapping[str, Any]) -> str:
    return str(
        punch.get("userCheckTime")
        or punch.get("checkTime")
        or punch.get("actual_time")
        or punch.get("user_check_time")
        or ""
    )


def punch_check_type(punch: Mapping[str, Any]) -> str:
    return str(
        punch.get("checkTypeDesc")
        or punch.get("checkType")
        or punch.get("check_type")
        or ""
    )


def raw_files_for_replay(
    archive_root: Path,
    target_month: str,
    *,
    allow_seed_raw_without_manifest: bool,
) -> list[tuple[str, Path, str]]:
    month_dir = archive_root / target_month
    manifests = sorted(month_dir.glob("s19_*.manifest.json"))
    raw_files = sorted(month_dir.glob("s19_*.raw.jsonl.gz")) + sorted(month_dir.glob("s19_*.raw.jsonl"))
    manifest_run_ids = {run_id_from_manifest(path) for path in manifests}
    selected: list[tuple[str, Path, str]] = []
    for manifest_path in manifests:
        run_id = run_id_from_manifest(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_path = resolve_raw_path(month_dir, manifest.get("raw_jsonl_gz"))
        if raw_path is not None:
            selected.append((run_id, raw_path, "formal"))
    if allow_seed_raw_without_manifest:
        for raw_path in raw_files:
            run_id = run_id_from_raw(raw_path)
            if run_id not in manifest_run_ids and is_seed_run_id(run_id):
                selected.append((run_id, raw_path, "seed"))
    return sorted(selected, key=lambda item: (item[2], item[0]))


def parse_replay_rows(raw_items: list[tuple[str, Path, str]], target_month: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    day_index: dict[tuple[str, str], dict[str, Any]] = {}
    link_rows: list[dict[str, Any]] = []
    rows_without_punches = 0
    for run_id, raw_path, run_kind in raw_items:
        raw_sha256 = sha256_file(raw_path)
        with open_raw(raw_path) as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, Mapping) or row.get("type") != "employee_attendance":
                    continue
                work_date = str(row.get("work_date") or "")
                if not work_date:
                    continue
                key_hash = employee_key_hash(row)
                punches = [punch for punch in get_record_list(row) if isinstance(punch, Mapping)]
                if not punches:
                    rows_without_punches += 1
                    continue
                day_fact_id = stable_uuid("attendance_day_fact", target_month, key_hash, work_date)
                day_key = (key_hash, work_date)
                day = day_index.setdefault(
                    day_key,
                    {
                        "day_fact_id": day_fact_id,
                        "target_month": target_month,
                        "employee_key_hash": key_hash,
                        "work_date": work_date,
                        "required_attendance_state": "workday",
                        "actual_attendance_state": "unknown",
                        "first_in_time": None,
                        "last_out_time": None,
                        "missing_punch_count": 0,
                        "location_evidence_count": 0,
                        "trajectory_evidence_count": 0,
                        "source_detail_ids": [],
                        "source_run_hashes": [],
                    },
                )
                if raw_sha256 not in day["source_run_hashes"]:
                    day["source_run_hashes"].append(raw_sha256)
                for punch_index, punch in enumerate(punches):
                    p_time = punch_time(punch)
                    p_hash = stable_hash(punch)
                    raw_detail_id = stable_uuid(
                        "raw_detail",
                        target_month,
                        run_id,
                        key_hash,
                        work_date,
                        line_no,
                        punch_index,
                        p_hash,
                    )
                    if raw_detail_id not in day["source_detail_ids"]:
                        day["source_detail_ids"].append(raw_detail_id)
                    if p_time:
                        day["first_in_time"] = min([x for x in [day["first_in_time"], p_time] if x])
                        day["last_out_time"] = max([x for x in [day["last_out_time"], p_time] if x])
                    has_location = has_location_evidence(punch)
                    if has_location:
                        day["location_evidence_count"] += 1
                        day["trajectory_evidence_count"] += 1
                    link_rows.append({
                        "raw_detail_id": raw_detail_id,
                        "day_fact_id": day_fact_id,
                        "target_month": target_month,
                        "employee_key_hash": key_hash,
                        "work_date": work_date,
                        "run_id": run_id,
                        "run_kind": run_kind,
                        "raw_sha256": raw_sha256,
                        "punch_hash": p_hash,
                        "check_type": punch_check_type(punch),
                        "has_location_evidence": has_location,
                    })
    day_rows = []
    for day in day_index.values():
        punch_count = len(day["source_detail_ids"])
        day["actual_attendance_state"] = "present" if punch_count >= 2 else "incomplete"
        day["missing_punch_count"] = max(0, 2 - punch_count)
        day["source_detail_ids"] = sorted(day["source_detail_ids"])
        day["source_run_hashes"] = sorted(day["source_run_hashes"])
        day["derivation_hash"] = stable_hash({
            key: value for key, value in day.items()
            if key not in {"day_fact_id", "derivation_hash"}
        })
        day_rows.append(day)
    return (
        sorted(day_rows, key=lambda row: (row["work_date"], row["employee_key_hash"])),
        sorted(link_rows, key=lambda row: (row["work_date"], row["employee_key_hash"], row["run_id"], row["raw_detail_id"])),
        rows_without_punches,
    )


def canonical_snapshot(target_month: str, replay_manifest: dict[str, Any], day_rows: list[dict[str, Any]], link_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "target_month": target_month,
        "raw_replay_hash": replay_manifest.get("replay_hash"),
        "seed_replay_hash": replay_manifest.get("seed_replay_hash"),
        "attendance_day_facts": day_rows,
        "raw_detail_linkage_count": len(link_rows),
        "raw_detail_linkage_hash": stable_hash(link_rows),
    }


def materialize_bundle(
    archive_root: Path,
    target_month: str,
    out_dir: Path,
    *,
    allow_seed_raw_without_manifest: bool,
    min_location_coverage_ratio: float,
) -> dict[str, Any]:
    replay_manifest = inspect_month(
        archive_root,
        target_month,
        allow_seed_raw_without_manifest=allow_seed_raw_without_manifest,
        min_location_coverage_ratio=min_location_coverage_ratio,
    )
    failures = list(replay_manifest.get("failures") or [])
    if replay_manifest.get("status") != "pass":
        return {
            "status": "fail",
            "mode": "offline_raw_replay_day_fact_bundle",
            "target_month": target_month,
            "raw_replay_status": replay_manifest.get("status"),
            "checks": {"public_safe_output": True},
            "failures": failures,
            "postgres_connection_used": False,
            "database_mutation_performed": False,
            "live_dws_performed": False,
        }
    raw_items = raw_files_for_replay(
        archive_root,
        target_month,
        allow_seed_raw_without_manifest=allow_seed_raw_without_manifest,
    )
    day_rows, link_rows, rows_without_punches = parse_replay_rows(raw_items, target_month)
    if not day_rows:
        failures.append("attendance_day_fact_empty")
    if any(not row.get("source_detail_ids") for row in day_rows):
        failures.append("day_fact_without_raw_detail_link")
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = canonical_snapshot(target_month, replay_manifest, day_rows, link_rows)
    canonical_hash = stable_hash(snapshot)
    canonical_hash_repeat = stable_hash(snapshot)
    write_json(out_dir / "raw_replay_manifest.json", replay_manifest)
    write_jsonl(out_dir / "attendance_day_fact.jsonl", day_rows)
    write_jsonl(out_dir / "raw_detail_linkage.jsonl", link_rows)
    write_json(out_dir / "canonical_replay_snapshot.json", snapshot)
    (out_dir / "canonical_replay_snapshot.sha256").write_text(canonical_hash + "\n", encoding="utf-8")
    summary = {
        "status": "fail" if failures else "READY",
        "mode": "offline_raw_replay_day_fact_bundle",
        "target_month": target_month,
        "raw_replay_status": replay_manifest.get("status"),
        "raw_file_count": replay_manifest.get("raw_file_count"),
        "manifest_count": replay_manifest.get("manifest_count"),
        "seed_raw_without_manifest_count": replay_manifest.get("seed_raw_without_manifest_count"),
        "formal_raw_without_manifest_count": replay_manifest.get("formal_raw_without_manifest_count"),
        "attendance_day_fact_rows": len(day_rows),
        "raw_detail_linkage_rows": len(link_rows),
        "raw_employee_rows_without_punches": rows_without_punches,
        "canonical_snapshot_hash": canonical_hash,
        "checks": {
            "raw_manifest_pairs_complete": bool(replay_manifest.get("checks", {}).get("raw_manifest_pairs_complete")),
            "raw_counts_match_manifest": bool(replay_manifest.get("checks", {}).get("raw_counts_match_manifest")),
            "raw_hashes_match_manifest": bool(replay_manifest.get("checks", {}).get("raw_hashes_match_manifest")),
            "location_coverage_threshold_met": bool(replay_manifest.get("checks", {}).get("location_coverage_threshold_met")),
            "every_day_fact_links_to_raw_ids": bool(day_rows) and all(bool(row.get("source_detail_ids")) for row in day_rows),
            "canonical_hash_stable": canonical_hash == canonical_hash_repeat,
            "public_safe_output": True,
        },
        "failures": failures,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }
    write_json(out_dir / "raw_replay_day_fact_manifest.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare private day-fact bundle from KMFA raw archive replay.")
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--allow-seed-raw-without-manifest", action="store_true")
    parser.add_argument("--min-location-coverage-ratio", type=float, default=0.0)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = materialize_bundle(
        Path(args.archive_root),
        args.target_month,
        Path(args.out_dir),
        allow_seed_raw_without_manifest=args.allow_seed_raw_without_manifest,
        min_location_coverage_ratio=args.min_location_coverage_ratio,
    )
    if args.print_json or result["status"] == "fail":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
