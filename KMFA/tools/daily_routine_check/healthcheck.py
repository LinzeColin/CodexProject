from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from .archive_reader import DwsArchiveReader
except ImportError:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from KMFA.tools.daily_routine_check.archive_reader import DwsArchiveReader

DEFAULT_INPUT = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs")
DEFAULT_RUNTIME = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime")
REQUIRED_GROUPS = ("付款请示群", "生产管理群")


def build_source_readiness(input_root: str | Path = DEFAULT_INPUT) -> dict[str, object]:
    root = Path(input_root).expanduser()
    zip_path = root if root.suffix.lower() == ".zip" else root.with_suffix(".zip")
    folder_root = root.with_suffix("") if root.suffix.lower() == ".zip" else root
    onedrive_root = zip_path.parent
    archive_path = onedrive_root / "DWS_Archive"
    group_status = {}
    direct_input_ready = True
    zip_input_ready = False
    next_enable_conditions: list[str] = []

    for group in REQUIRED_GROUPS:
        group_root = folder_root / group
        manifest_path = group_root / "_manifest" / "manifest.csv"
        chat_path = group_root / "chat_records" / "chat_records.csv"
        status = {
            "group_root_exists": group_root.exists(),
            "manifest_exists": manifest_path.exists(),
            "chat_records_exists": chat_path.exists(),
            "manifest_path": str(manifest_path),
            "chat_records_path": str(chat_path),
        }
        group_status[group] = status
        if not status["manifest_exists"] or not status["chat_records_exists"]:
            direct_input_ready = False
            next_enable_conditions.append(str(chat_path))
            next_enable_conditions.append(str(manifest_path))

    zip_reader = DwsArchiveReader(zip_path)
    zip_present = zip_path.exists()
    zip_error_code = zip_reader.zip_error_code() if zip_present else None
    zip_error_detail = zip_reader.zip_error_detail() if zip_present else ""
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
        next_enable_conditions = [
            item for item in next_enable_conditions
            if not item.startswith(str(folder_root))
        ]
        next_enable_conditions.append(f"{zip_path} must be a readable DWS_Outputs.zip; {zip_error_detail or zip_error_code}")
    else:
        next_enable_conditions.append(f"{zip_path} must exist as readable DWS_Outputs.zip or direct DWS_Outputs group folders must exist")

    if direct_input_ready or zip_input_ready:
        status = "READY"
        next_enable_conditions = []
    elif zip_present and zip_error_code:
        status = "ZIP_INPUT_UNREADABLE"
    else:
        status = "SOURCE_MISSING"

    return {
        "input_root": str(folder_root),
        "input_zip": str(zip_path),
        "status": status,
        "direct_input_ready": direct_input_ready,
        "zip_input_ready": zip_input_ready,
        "zip_present": zip_present,
        "zip_path": str(zip_path),
        "zip_error_code": zip_error_code,
        "zip_error_detail": zip_error_detail,
        "archive_present": archive_path.exists(),
        "archive_path": str(archive_path),
        "groups": group_status,
        "zip_groups": zip_group_status,
        "next_enable_conditions": next_enable_conditions,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-only", action="store_true")
    ap.add_argument("--input-root", default=str(DEFAULT_INPUT))
    args = ap.parse_args()

    root = Path(args.input_root).expanduser()
    readiness = build_source_readiness(root)
    print(f"input_root={root}")
    print(f"input_zip={readiness['input_zip']}")
    print(f"source_readiness_status={readiness['status']}")
    print(f"direct_input_ready={str(readiness['direct_input_ready']).lower()}")
    print(f"zip_input_ready={str(readiness['zip_input_ready']).lower()}")
    print(f"zip_present={str(readiness['zip_present']).lower()} path={readiness['zip_path']}")
    if readiness["zip_error_code"]:
        print(f"zip_error_code={readiness['zip_error_code']} detail={readiness['zip_error_detail']}")
    print(f"archive_present={str(readiness['archive_present']).lower()} path={readiness['archive_path']}")
    for group in REQUIRED_GROUPS:
        gp = Path(readiness["input_root"]) / group
        print(f"group[{group}] exists={gp.exists()} path={gp}")
        print(f"  manifest={(gp / '_manifest' / 'manifest.csv').exists()}")
        print(f"  chat_records={(gp / 'chat_records' / 'chat_records.csv').exists()}")
        zip_group = readiness["zip_groups"].get(group, {}) if isinstance(readiness["zip_groups"], dict) else {}
        if zip_group:
            print(f"  zip_manifest={zip_group.get('manifest_member')}")
            print(f"  zip_chat_records={zip_group.get('chat_records_member')}")
    if readiness["next_enable_conditions"]:
        print("next_enable_conditions=")
        for item in readiness["next_enable_conditions"]:
            print(f"  - {item}")
    print(f"runtime_path={DEFAULT_RUNTIME}")
    print("config_only_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
