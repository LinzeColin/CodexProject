#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = "outputs/finance_ledger_20220605_20260603"
DEFAULT_LEDGER_DB = "data/finance_ledger/finance_ledger.sqlite"


def run_command(command: list[str], *, cwd: Path = ROOT) -> dict[str, Any]:
    started = time.time()
    process = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "command": command,
        "returncode": process.returncode,
        "duration_seconds": round(time.time() - started, 2),
        "stdout": process.stdout[-6000:],
        "stderr": process.stderr[-6000:],
        "ok": process.returncode == 0,
    }


def classify_failure(result: dict[str, Any]) -> dict[str, str]:
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    command = " ".join(str(part) for part in result.get("command", []))
    if "Operation not permitted" in combined or "PermissionError" in combined:
        return {
            "kind": "sandbox_permission",
            "next_action": "Run the final gate with platform approval so local Chrome/CDP and localhost access are allowed.",
        }
    if "browser audit is older than current HTML pages" in combined:
        return {
            "kind": "stale_browser_acceptance",
            "next_action": "Run scripts/run_browser_visual_acceptance.py against the latest HTML pages, then rerun the final gate.",
        }
    if "Timed out waiting for" in combined or "Connection refused" in combined:
        return {
            "kind": "localhost_unavailable",
            "next_action": "Ensure the report server is running or rerun finalize_delivery.py with --ensure-server.",
        }
    if "Google Chrome" in command or "chrome" in combined.lower() or "CDP websocket" in combined:
        return {
            "kind": "browser_runtime",
            "next_action": "Verify local Chrome can launch headless and expose the DevTools port.",
        }
    return {
        "kind": "command_failed",
        "next_action": "Inspect stdout/stderr for the failed gate and rerun after fixing that step.",
    }


def url_available(url: str, timeout: float = 2) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except Exception:
        return False


def maybe_start_server(base_url: str, output_dir: Path) -> subprocess.Popen[str] | None:
    if url_available(base_url):
        return None
    parsed = urllib.parse.urlparse(base_url)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.port:
        return None
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(parsed.port), "--bind", "127.0.0.1"],
        cwd=output_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 8
    while time.time() < deadline:
        if process.poll() is not None:
            return process
        if url_available(base_url):
            return process
        time.sleep(0.2)
    return process


def process_tail(process: subprocess.Popen[str]) -> dict[str, Any]:
    stdout = ""
    stderr = ""
    if process.poll() is not None:
        try:
            out, err = process.communicate(timeout=1)
        except Exception:
            out, err = "", ""
        stdout = out[-3000:] if out else ""
        stderr = err[-3000:] if err else ""
    return {"returncode": process.poll(), "stdout": stdout, "stderr": stderr}


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    ledger_db = Path(args.ledger_db)
    base_url = args.base_url.rstrip("/") + "/"
    server_process: subprocess.Popen[str] | None = None
    steps: list[dict[str, Any]] = []
    try:
        if args.preflight_only:
            commands = [
                [
                    sys.executable,
                    "scripts/verify_browser_acceptance.py",
                    "--audit",
                    str(output_dir / "audit" / "browser_visual_acceptance.json"),
                    "--html-root",
                    str(output_dir),
                    "--json",
                ],
                [
                    sys.executable,
                    "scripts/audit_chatgpt_reference.py",
                    "--output-dir",
                    str(output_dir),
                    "--json",
                ],
                [
                    sys.executable,
                    "scripts/audit_goal_completion.py",
                    "--output-dir",
                    str(output_dir),
                    "--ledger-db",
                    str(ledger_db),
                    "--json",
                ],
                [sys.executable, "-m", "pytest", "-q"],
                [
                    sys.executable,
                    "scripts/validate_outputs.py",
                    "--output",
                    str(output_dir),
                    "--db",
                    str(ledger_db),
                    "--require-ledger",
                    "--json",
                ],
            ]
            step_names = ["browser_acceptance_freshness", "chatgpt_reference_audit", "goal_completion_audit", "tests", "output_validation"]
            preflight_warnings: list[dict[str, Any]] = []
            for name, command in zip(step_names, commands, strict=True):
                result = run_command(command)
                result["name"] = name
                if name == "browser_acceptance_freshness" and not result["ok"]:
                    preflight_warnings.append(
                        {
                            "name": name,
                            "failure": classify_failure(result),
                            "stdout": result.get("stdout", ""),
                            "stderr": result.get("stderr", ""),
                        }
                    )
                    result["preflight_warning"] = True
                    result["ok"] = True
                steps.append(result)
                if not result["ok"]:
                    return {"ok": False, "failed_step": name, "failure": classify_failure(result), "steps": steps}
            return {
                "ok": True,
                "mode": "preflight_only",
                "failed_step": "",
                "warnings": preflight_warnings,
                "steps": steps,
            }
        if args.ensure_server:
            server_process = maybe_start_server(base_url, ROOT / output_dir)
            if server_process is not None and server_process.poll() is not None:
                server_detail = process_tail(server_process)
                return {
                    "ok": False,
                    "failed_step": "ensure_server",
                    "steps": steps,
                    "error": "local report server exited before becoming available",
                    "failure": classify_failure(
                        {
                            "command": [sys.executable, "-m", "http.server"],
                            "stdout": server_detail.get("stdout", ""),
                            "stderr": server_detail.get("stderr", ""),
                        }
                    ),
                    "server": server_detail,
                }
        commands = [
            [
                sys.executable,
                "scripts/run_browser_visual_acceptance.py",
                "--base-url",
                base_url,
                "--output-dir",
                str(output_dir),
                "--startup-timeout",
                "60",
                "--json",
            ],
            [
                sys.executable,
                "scripts/verify_browser_acceptance.py",
                "--audit",
                str(output_dir / "audit" / "browser_visual_acceptance.json"),
                "--html-root",
                str(output_dir),
                "--json",
            ],
            [
                sys.executable,
                "scripts/audit_chatgpt_reference.py",
                "--output-dir",
                str(output_dir),
                "--json",
            ],
            [
                sys.executable,
                "scripts/audit_goal_completion.py",
                "--output-dir",
                str(output_dir),
                "--ledger-db",
                str(ledger_db),
                "--json",
            ],
            [sys.executable, "-m", "pytest", "-q"],
            [
                sys.executable,
                "scripts/validate_outputs.py",
                "--output",
                str(output_dir),
                "--db",
                str(ledger_db),
                "--require-ledger",
                "--json",
            ],
            [
                sys.executable,
                "scripts/package_delivery.py",
                "--output-dir",
                str(output_dir),
                "--ledger-db",
                str(ledger_db),
                "--json",
            ],
        ]
        step_names = ["browser_visual_acceptance", "browser_acceptance_freshness", "chatgpt_reference_audit", "goal_completion_audit", "tests", "output_validation", "delivery_package"]
        for name, command in zip(step_names, commands, strict=True):
            result = run_command(command)
            result["name"] = name
            steps.append(result)
            if not result["ok"]:
                return {"ok": False, "failed_step": name, "failure": classify_failure(result), "steps": steps}
        package_stdout = steps[-1]["stdout"]
        try:
            package_result = json.loads(package_stdout)
        except json.JSONDecodeError:
            package_result = {"raw_stdout": package_stdout}
        return {"ok": True, "failed_step": "", "steps": steps, "package": package_result}
    finally:
        if server_process is not None and server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run final delivery gates: browser acceptance, tests, output validation, and ZIP packaging.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8772/")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-db", default=DEFAULT_LEDGER_DB)
    parser.add_argument("--ensure-server", action="store_true", help="Start a temporary local static server from output-dir when base-url is not already available.")
    parser.add_argument("--preflight-only", action="store_true", help="Run non-browser gates and report stale browser acceptance as a warning. Does not create a final ZIP.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = finalize(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "OK" if result["ok"] else "FAIL"
        print(f"{status} finalize_delivery failed_step={result.get('failed_step', '')}")
        if result.get("package"):
            print(json.dumps(result["package"], ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
