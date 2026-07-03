from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from .core import (
    DEFAULT_DATA_CORE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RUNTIME_ROOT,
    DEFAULT_SOURCE_WORKSPACE,
    build_status,
    initialize_runtime,
    launcher_url,
    run_update,
)


def path_arg(value: str | None, default: Path) -> Path:
    return Path(value).expanduser() if value else default


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runtime-root", default=os.environ.get("WDA_R3_RUNTIME_ROOT"))
    parser.add_argument("--data-core", default=os.environ.get("WDA_R3_DATA_CORE"))
    parser.add_argument(
        "--source-workspace", default=os.environ.get("WDA_R3_SOURCE_WORKSPACE")
    )


def common_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    return (
        path_arg(args.runtime_root, DEFAULT_RUNTIME_ROOT),
        path_arg(args.data_core, DEFAULT_DATA_CORE),
        path_arg(args.source_workspace, DEFAULT_SOURCE_WORKSPACE),
    )


def cmd_init(args: argparse.Namespace) -> int:
    runtime_root, data_core, source_workspace = common_paths(args)
    print(
        json.dumps(
            initialize_runtime(runtime_root, data_core, source_workspace),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    runtime_root, data_core, source_workspace = common_paths(args)
    print(
        json.dumps(
            build_status(data_core, source_workspace, runtime_root),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    runtime_root, data_core, source_workspace = common_paths(args)
    print(
        json.dumps(
            run_update(runtime_root, data_core, source_workspace),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    runtime_root, data_core, source_workspace = common_paths(args)
    initialize_runtime(runtime_root, data_core, source_workspace)
    import uvicorn

    uvicorn.run(
        "WDA.app_api.main:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
    )
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    url = launcher_url(args.host, args.port)
    webbrowser.open(url)
    print(url)
    return 0


def cmd_start_background(args: argparse.Namespace) -> int:
    runtime_root, _, _ = common_paths(args)
    log_dir = runtime_root / "logs"
    state_dir = runtime_root / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "WDA.app_api.cli",
        "serve",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    with (log_dir / "service.log").open("ab") as out:
        process = subprocess.Popen(
            command,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    (state_dir / "service.pid").write_text(str(process.pid) + "\n", encoding="utf-8")
    print(json.dumps({"pid": process.pid, "url": launcher_url(args.host, args.port)}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WDA v0.2-R3 local app runtime.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    add_common(init_parser)
    init_parser.set_defaults(func=cmd_init)

    status_parser = subparsers.add_parser("status")
    add_common(status_parser)
    status_parser.set_defaults(func=cmd_status)

    update_parser = subparsers.add_parser("update")
    add_common(update_parser)
    update_parser.set_defaults(func=cmd_update)

    serve_parser = subparsers.add_parser("serve")
    add_common(serve_parser)
    serve_parser.add_argument("--host", default=DEFAULT_HOST)
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve_parser.set_defaults(func=cmd_serve)

    start_parser = subparsers.add_parser("start-background")
    add_common(start_parser)
    start_parser.add_argument("--host", default=DEFAULT_HOST)
    start_parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    start_parser.set_defaults(func=cmd_start_background)

    open_parser = subparsers.add_parser("open")
    open_parser.add_argument("--host", default=DEFAULT_HOST)
    open_parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    open_parser.set_defaults(func=cmd_open)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
