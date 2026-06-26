from __future__ import annotations

import csv
import json
import os
import sqlite3
import socket
import subprocess
import time
from pathlib import Path

from src.config import ROOT


MOOMOO_APP_NAME = "moomoo"
MOOMOO_BUNDLE_ID = "com.moomoo.mm-mac"
MOOMOO_APP_PATH = Path("/Applications/moomoo.app")
MOOMOO_CONTAINER = Path.home() / "Library" / "Containers" / MOOMOO_BUNDLE_ID / "Data" / "Library" / "Application Support"
STOCK_DB = MOOMOO_CONTAINER / "Common" / "stock_v15.db"
WORKBENCH = Path(os.environ.get("MOOMOO_WORKBENCH_ROOT", ROOT / "data" / "private" / "moomoo-api-workbench")).expanduser()
OPEND_CONFIG = WORKBENCH / "config.json"
OPEND_PYTHON = WORKBENCH / ".venv" / "bin" / "python"
OPEND_START = WORKBENCH / "start_opend.sh"


def ensure_moomoo_running(wait_seconds: int = 20) -> bool:
    if _is_running():
        return True
    _open_moomoo_app()
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if _is_running():
            return True
        time.sleep(1)
    return _is_running()


def _open_moomoo_app() -> None:
    commands = [
        ["open", "-b", MOOMOO_BUNDLE_ID],
    ]
    if MOOMOO_APP_PATH.exists():
        commands.append(["open", str(MOOMOO_APP_PATH)])
    commands.append(["open", "-a", MOOMOO_APP_NAME])
    for command in commands:
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode == 0:
            return


def sync_watchlist_from_desktop(
    output_path: str | Path | None = None,
    group_name: str = "全部",
    open_if_needed: bool = True,
) -> Path:
    if open_if_needed:
        ensure_moomoo_running()
    watchlist_db = _find_watchlist_db()
    output = Path(output_path or ROOT / "data" / "sample" / "watchlist_moomoo.csv")
    rows = _read_watchlist_rows(watchlist_db, group_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "group_name",
            "stock_id",
            "symbol",
            "code",
            "name",
            "eng_name",
            "exchange",
            "region",
            "currency_code",
            "instrument_type",
            "asset_class",
            "research_group",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output


def sync_quotes_from_opend(
    as_of: str,
    watchlist_path: str | Path | None = None,
    output_path: str | Path | None = None,
    open_if_needed: bool = True,
    fail_on_error: bool = True,
    allow_stale: bool = False,
) -> Path | None:
    config = _load_opend_config()
    host = config["opend"]["host"]
    port = int(config["opend"]["port"])
    status_path = ROOT / "data" / "sample" / "opend_status.json"
    output = Path(output_path or ROOT / "data" / "sample" / "watchlist_snapshot.csv")
    watchlist = Path(watchlist_path or ROOT / "data" / "sample" / "watchlist_moomoo.csv")

    try:
        if open_if_needed and not _port_open(host, port):
            _start_opend()
            _wait_for_port(host, port, timeout_seconds=35)
        if not _port_open(host, port):
            raise ConnectionError(f"OpenD is not reachable at {host}:{port}")
        command = [
            str(OPEND_PYTHON),
            str(ROOT / "src" / "integrations" / "moomoo_opend_fetch.py"),
            "--host",
            host,
            "--port",
            str(port),
            "--watchlist",
            str(watchlist),
            "--output",
            str(output),
            "--date",
            as_of,
        ]
        try:
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=False,
                env=_opend_subprocess_env(),
                timeout=_opend_fetch_timeout_seconds(),
            )
        except subprocess.TimeoutExpired as exc:
            fallback_command = [*command, "--skip-opend"]
            fallback_result = subprocess.run(
                fallback_command,
                text=True,
                capture_output=True,
                check=False,
                env={**_opend_subprocess_env(), "AI_RESEARCH_QUOTE_FALLBACK_BUDGET_SECONDS": "45"},
                timeout=_fallback_only_timeout_seconds(),
            )
            if fallback_result.returncode != 0:
                raise RuntimeError(
                    f"OpenD fetch timed out after {exc.timeout} seconds and fallback-only refresh failed: "
                    + (fallback_result.stderr.strip() or fallback_result.stdout.strip())
                ) from exc
            _write_status(
                status_path,
                "fallback_only_after_opend_timeout",
                f"OpenD fetch timed out after {exc.timeout} seconds; {fallback_result.stdout.strip()}",
                output,
            )
            return output
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        _write_status(status_path, "ok", result.stdout.strip(), output)
        return output
    except Exception as exc:
        _write_status(status_path, "failed", str(exc), output if output.exists() else None)
        if fail_on_error:
            raise
        return output if allow_stale and output.exists() else None


def _opend_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    runtime_dir = ROOT / "data" / "report_artifacts" / "automation_runtime"
    sitecustomize_dir = runtime_dir / "sitecustomize"
    home_dir = runtime_dir / "moomoo_home"
    sitecustomize_dir.mkdir(parents=True, exist_ok=True)
    home_dir.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home_dir)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(sitecustomize_dir) if not existing_pythonpath else str(sitecustomize_dir) + os.pathsep + existing_pythonpath
    return env


def _opend_fetch_timeout_seconds() -> int:
    raw = os.environ.get("AI_RESEARCH_OPEND_FETCH_TIMEOUT_SECONDS", "90")
    try:
        return max(15, int(raw))
    except ValueError:
        return 90


def _fallback_only_timeout_seconds() -> int:
    raw = os.environ.get("AI_RESEARCH_FALLBACK_ONLY_TIMEOUT_SECONDS", "70")
    try:
        return max(20, int(raw))
    except ValueError:
        return 70


def _is_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-x", MOOMOO_APP_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return True
    result = subprocess.run(
        ["pgrep", "-f", MOOMOO_BUNDLE_ID],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _load_opend_config() -> dict[str, object]:
    if OPEND_CONFIG.exists():
        return json.loads(OPEND_CONFIG.read_text(encoding="utf-8"))
    return {"opend": {"host": "127.0.0.1", "port": 11111}}


def _start_opend() -> None:
    if OPEND_START.exists():
        subprocess.run([str(OPEND_START)], cwd=str(WORKBENCH), check=False)


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        return True
    except PermissionError:
        return _port_listening_via_lsof(port)
    except OSError:
        return False
    finally:
        sock.close()


def _port_listening_via_lsof(port: int) -> bool:
    try:
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            text=True,
            capture_output=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and f":{port}" in result.stdout and "LISTEN" in result.stdout


def _wait_for_port(host: str, port: int, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(1)
    return False


def _write_status(path: Path, status: str, message: str, snapshot_path: Path | None) -> None:
    payload = {
        "status": status,
        "message": message,
        "snapshot_path": str(snapshot_path) if snapshot_path else "",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_watchlist_db() -> Path:
    users_dir = MOOMOO_CONTAINER / "Users"
    candidates = sorted(users_dir.glob("*/WatchlistGroup.db"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No moomoo WatchlistGroup.db found under {users_dir}")
    if not STOCK_DB.exists():
        raise FileNotFoundError(f"No moomoo stock database found at {STOCK_DB}")
    return candidates[0]


def _read_watchlist_rows(watchlist_db: Path, group_name: str) -> list[dict[str, object]]:
    connection = sqlite3.connect(STOCK_DB)
    try:
        connection.execute(f"attach database ? as wl", (str(watchlist_db),))
        cursor = connection.execute(
            """
            select distinct
                g.group_name,
                s.stock_id,
                s.futu_symbol,
                s.code,
                coalesce(nullif(s.sc_name, ''), nullif(s.eng_name, ''), s.code) as name,
                s.eng_name,
                s.exchange,
                s.region,
                s.currency_code,
                s.instrument_type
            from wl.t_watchlist_group wg
            join wl.t_watchlist_groups g on wg.group_id = g.group_id
            left join t_stock s on wg.stock_id = s.stock_id
            where g.group_name = ?
            order by wg.id
            """,
            (group_name,),
        )
        rows = []
        for row in cursor.fetchall():
            symbol = row[2] or row[3] or str(row[1])
            name = row[4] or symbol
            rows.append(
                {
                    "group_name": row[0],
                    "stock_id": row[1],
                    "symbol": symbol,
                    "code": row[3] or symbol,
                    "name": name,
                    "eng_name": row[5] or "",
                    "exchange": row[6] or "",
                    "region": row[7] or "",
                    "currency_code": row[8] or "",
                    "instrument_type": row[9] or "",
                    "asset_class": _asset_class(row[9], row[6]),
                    "research_group": _research_group(symbol, name, row[6], row[9]),
                }
            )
        return rows
    finally:
        connection.close()


def _asset_class(instrument_type: int | str | None, exchange: str | None) -> str:
    if exchange == "FX":
        return "FX"
    value = int(instrument_type or 0)
    if value == 4:
        return "ETF"
    if value == 6:
        return "Index"
    if value == 3:
        return "Stock"
    if value == 11:
        return "FX"
    return "Other"


def _research_group(symbol: str, name: str, exchange: str | None, instrument_type: int | str | None) -> str:
    text = f"{symbol} {name}"
    if exchange == "FX" or "人民币" in text or "澳元" in text:
        return "汇率"
    rules = [
        ("芯片", "半导体"),
        ("人工智能", "AI/科技"),
        ("科创", "科创成长"),
        ("恒生科技", "港股科技"),
        ("红利", "红利低波"),
        ("黄金", "黄金"),
        ("银行", "银行"),
        ("农业", "农业/周期"),
        ("化工", "化工/周期"),
        ("机器人", "机器人"),
        ("纳指", "美股科技"),
        ("QQQ", "美股科技"),
        ("NOBL", "美股红利"),
        ("标普500", "美股宽基"),
        ("VOO", "美股宽基"),
        ("纳斯达克", "交易所/金融科技"),
        ("上证", "宽基指数"),
        ("000001", "宽基指数"),
    ]
    for keyword, group in rules:
        if keyword in text:
            return group
    asset_class = _asset_class(instrument_type, exchange)
    return asset_class or "未分类"
