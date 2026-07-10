from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from .archive_reader import DwsArchiveReader
except ImportError:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from KMFA.tools.daily_routine_check.archive_reader import DwsArchiveReader

DEFAULT_INPUT = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip")
DEFAULT_RUNTIME = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime")
REQUIRED_GROUPS = ("付款请示群", "生产管理群")


def build_source_readiness(input_zip: str | Path = DEFAULT_INPUT) -> dict[str, object]:
    zip_path = Path(input_zip).expanduser()
    zip_reader = DwsArchiveReader(zip_path)
    onedrive_root = zip_path.parent
    archive_path = onedrive_root / "DWS_Archive"
    zip_input_ready = False
    next_enable_conditions: list[str] = []
    zip_present = zip_path.exists()
    zip_size_bytes = 0
    zip_allocated_bytes = 0
    if zip_present:
        zip_stat = zip_path.stat()
        zip_size_bytes = zip_stat.st_size
        zip_allocated_bytes = getattr(zip_stat, "st_blocks", 0) * 512
    zip_error_code = zip_reader.zip_error_code()
    zip_error_detail = zip_reader.zip_error_detail()
    zip_group_status = {}
    if zip_present and not zip_error_code:
        zip_input_ready = True
        for group in REQUIRED_GROUPS:
            chat_member = zip_reader.find_zip_member(group, "chat_records/chat_records.csv")
            manifest_member = zip_reader.find_zip_member(group, "_manifest/manifest.csv")
            zip_group_status[group] = {
                "chat_records_member": chat_member,
                "manifest_member": manifest_member,
            }
            if not chat_member:
                zip_input_ready = False
                next_enable_conditions.append(f"zip://{zip_path}!/*/{group}/chat_records/chat_records.csv")
            if not manifest_member:
                zip_input_ready = False
                next_enable_conditions.append(f"zip://{zip_path}!/*/{group}/_manifest/manifest.csv")
    elif zip_present:
        next_enable_conditions.append(f"{zip_path} must be a readable DWS_Outputs.zip; {zip_error_detail or zip_error_code}")
    else:
        next_enable_conditions.append(f"{zip_path} must exist as the readable ZIP-only DWS input")

    if zip_input_ready:
        status = "READY"
        next_enable_conditions = []
    elif zip_present and zip_error_code:
        status = "ZIP_INPUT_UNREADABLE"
    else:
        status = "SOURCE_MISSING"

    return {
        "input_zip": str(zip_path),
        "status": status,
        "zip_input_ready": zip_input_ready,
        "zip_present": zip_present,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_size_bytes,
        "zip_allocated_bytes": zip_allocated_bytes,
        "input_cache_policy": "stream_members_no_copy_no_extract",
        "zip_error_code": zip_error_code,
        "zip_error_detail": zip_error_detail,
        "archive_present": archive_path.exists(),
        "archive_path": str(archive_path),
        "zip_groups": zip_group_status,
        "next_enable_conditions": next_enable_conditions,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-only", action="store_true")
    ap.add_argument("--input-zip", default=str(DEFAULT_INPUT))
    args = ap.parse_args()

    zip_path = Path(args.input_zip).expanduser()
    readiness = build_source_readiness(zip_path)
    print(f"input_zip={readiness['input_zip']}")
    print(f"source_readiness_status={readiness['status']}")
    print(f"zip_input_ready={str(readiness['zip_input_ready']).lower()}")
    print(f"zip_present={str(readiness['zip_present']).lower()} path={readiness['zip_path']}")
    print(
        f"zip_size_bytes={readiness['zip_size_bytes']} "
        f"zip_allocated_bytes={readiness['zip_allocated_bytes']}"
    )
    print(f"input_cache_policy={readiness['input_cache_policy']}")
    if readiness["zip_error_code"]:
        print(f"zip_error_code={readiness['zip_error_code']} detail={readiness['zip_error_detail']}")
    print(f"archive_present={str(readiness['archive_present']).lower()} path={readiness['archive_path']}")
    for group in REQUIRED_GROUPS:
        zip_group = readiness["zip_groups"].get(group, {}) if isinstance(readiness["zip_groups"], dict) else {}
        print(f"group[{group}] zip_manifest={zip_group.get('manifest_member')}")
        print(f"group[{group}] zip_chat_records={zip_group.get('chat_records_member')}")
    if readiness["next_enable_conditions"]:
        print("next_enable_conditions=")
        for item in readiness["next_enable_conditions"]:
            print(f"  - {item}")
    print(f"runtime_path={DEFAULT_RUNTIME}")
    print("config_only_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
