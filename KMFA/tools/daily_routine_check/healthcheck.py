from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_INPUT = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs")
DEFAULT_RUNTIME = Path("KMFA/metadata/daily_routine_check/private_runtime")
REQUIRED_GROUPS = ("付款请示群", "生产管理群")


def build_source_readiness(input_root: str | Path = DEFAULT_INPUT) -> dict[str, object]:
    root = Path(input_root).expanduser()
    onedrive_root = root.parent
    zip_path = onedrive_root / f"{root.name}.zip"
    archive_path = onedrive_root / "DWS_Archive"
    group_status = {}
    direct_input_ready = True
    next_enable_conditions: list[str] = []

    for group in REQUIRED_GROUPS:
        group_root = root / group
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

    if direct_input_ready:
        status = "READY"
    elif zip_path.exists() or archive_path.exists():
        status = "SOURCE_INPUT_FOLDER_MISSING"
    else:
        status = "SOURCE_MISSING"

    return {
        "input_root": str(root),
        "status": status,
        "direct_input_ready": direct_input_ready,
        "zip_present": zip_path.exists(),
        "zip_path": str(zip_path),
        "archive_present": archive_path.exists(),
        "archive_path": str(archive_path),
        "groups": group_status,
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
    print(f"source_readiness_status={readiness['status']}")
    print(f"direct_input_ready={str(readiness['direct_input_ready']).lower()}")
    print(f"zip_present={str(readiness['zip_present']).lower()} path={readiness['zip_path']}")
    print(f"archive_present={str(readiness['archive_present']).lower()} path={readiness['archive_path']}")
    for group in REQUIRED_GROUPS:
        gp = root / group
        print(f"group[{group}] exists={gp.exists()} path={gp}")
        print(f"  manifest={(gp / '_manifest' / 'manifest.csv').exists()}")
        print(f"  chat_records={(gp / 'chat_records' / 'chat_records.csv').exists()}")
    if not readiness["direct_input_ready"]:
        print("next_enable_conditions=")
        for item in readiness["next_enable_conditions"]:
            print(f"  - {item}")
    print(f"runtime_path={DEFAULT_RUNTIME}")
    print("config_only_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
