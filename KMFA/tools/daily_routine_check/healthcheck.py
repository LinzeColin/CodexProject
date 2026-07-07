from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_INPUT = Path("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs")
DEFAULT_RUNTIME = Path("KMFA/metadata/daily_routine_check/private_runtime")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-only", action="store_true")
    ap.add_argument("--input-root", default=str(DEFAULT_INPUT))
    args = ap.parse_args()

    root = Path(args.input_root).expanduser()
    print(f"input_root={root}")
    for group in ["付款请示群", "生产管理群"]:
        gp = root / group
        print(f"group[{group}] exists={gp.exists()} path={gp}")
        print(f"  manifest={(gp / '_manifest' / 'manifest.csv').exists()}")
        print(f"  chat_records={(gp / 'chat_records' / 'chat_records.csv').exists()}")
    print(f"runtime_path={DEFAULT_RUNTIME}")
    print("config_only_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
