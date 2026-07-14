from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.path_display import display_path, redact_text_for_markdown


SYSTEM_APPLICATION_DIRS = [Path("/Applications")]


@dataclass(frozen=True)
class SocketProbe:
    host: str
    port: int
    reachable: bool
    detail: str


@dataclass(frozen=True)
class SdkProbe:
    import_available: bool
    distribution_version: str | None
    detail: str


@dataclass(frozen=True)
class WorkbenchProbe:
    path: str
    exists: bool
    start_script: str | None
    check_script: str | None
    quote_script: str | None
    config_path: str | None
    sdk_vendor_path: str | None
    opend_vendor_path: str | None
    moomoo_opend_app_path: str | None


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def probe_socket(host: str, port: int, timeout: float) -> SocketProbe:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return SocketProbe(host, port, True, f"moomoo_OpenD socket reachable at {host}:{port}")
    except OSError as exc:
        return SocketProbe(
            host,
            port,
            False,
            f"moomoo_OpenD socket not reachable at {host}:{port}: {exc.__class__.__name__}: {exc}",
        )


def probe_sdk() -> SdkProbe:
    if importlib.util.find_spec("moomoo") is None:
        return SdkProbe(False, None, "Python import `moomoo` is not available in this interpreter")
    version = None
    for package_name in ("moomoo_api", "moomoo"):
        try:
            version = importlib.metadata.version(package_name)
            break
        except importlib.metadata.PackageNotFoundError:
            continue
    detail = "Python import `moomoo` is available"
    if version:
        detail = f"{detail}; installed distribution version={version}"
    return SdkProbe(True, version, detail)


def _first_existing(paths: list[Path]) -> str | None:
    for path in paths:
        if path.exists():
            return str(path)
    return None


def _latest_opend_failure_hint() -> str | None:
    log_dir = Path.home() / ".com.moomoo.OpenD" / "Log"
    if not log_dir.exists():
        return None
    candidates = sorted(
        log_dir.glob("GTWLog_*.log"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates[:3]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[-80_000:]
        except OSError:
            continue
        if "Password does not match" in text:
            return "moomoo_OpenD login failed: password does not match; update OpenD credentials or complete GUI login"
        if "Login failed" in text:
            return "moomoo_OpenD login failed; update OpenD credentials or complete GUI login"
        if "API Listening Address" in text and "moomoo OpenD has exited" in text:
            return "moomoo_OpenD started its API listener and then exited; inspect the latest moomoo_OpenD log"
    return None


def _probe_workbench(path: Path) -> WorkbenchProbe:
    vendor = path / "vendor"
    moomoo_opend_app_path = _first_existing(
        [
            path / "moomoo_OpenD.app",
            path / "moomoo_OpenD-GUI_10.6.6608_Mac" / "moomoo_OpenD.app",
            path / "OpenD.app",
            path / "moomoo_OpenD_10.6.6608_Mac" / "OpenD.app",
            vendor / "moomoo_OpenD_GUI" / "moomoo_OpenD.app",
            vendor / "moomoo_OpenD_10.6.6608_Mac" / "moomoo_OpenD_10.6.6608_Mac" / "OpenD.app",
        ]
    )
    return WorkbenchProbe(
        path=str(path),
        exists=path.exists(),
        start_script=str(path / "start_opend.sh") if (path / "start_opend.sh").exists() else None,
        check_script=str(path / "check_opend.py") if (path / "check_opend.py").exists() else None,
        quote_script=str(path / "quote_smoke_test.py") if (path / "quote_smoke_test.py").exists() else None,
        config_path=str(path / "config.json") if (path / "config.json").exists() else None,
        sdk_vendor_path=_first_existing(
            [
                candidate
                for candidate in vendor.glob("MMAPI4Python*")
                if candidate.is_dir() and (candidate / "setup.py").exists()
            ]
        )
        if vendor.exists()
        else None,
        opend_vendor_path=_first_existing(
            [
                candidate
                for candidate in vendor.glob("moomoo_OpenD*")
                if candidate.exists()
            ]
        )
        if vendor.exists()
        else None,
        moomoo_opend_app_path=moomoo_opend_app_path,
    )


def _has_workbench_artifact(probe: WorkbenchProbe) -> bool:
    return any(
        [
            probe.start_script,
            probe.check_script,
            probe.quote_script,
            probe.config_path,
            probe.sdk_vendor_path,
            probe.opend_vendor_path,
            probe.moomoo_opend_app_path,
        ]
    )


def discover_workbenches(settings: Settings, include_user_codex: bool = True) -> list[WorkbenchProbe]:
    candidates: list[Path] = [
        Path.home() / "Applications" / "MoomooOpenD",
        Path.home() / "Applications",
        *SYSTEM_APPLICATION_DIRS,
        settings.root_dir / "outputs" / "moomoo-api-workbench",
        Path.home() / "Applications" / "MoomooOpenD" / "moomoo_OpenD_10.6.6608_Mac" / "moomoo_OpenD_10.6.6608_Mac",
        Path.home() / "Applications" / "MoomooOpenD" / "moomoo_OpenD_10.6.6608_Mac" / "moomoo_OpenD-GUI_10.6.6608_Mac",
    ]
    if include_user_codex:
        codex_root = Path.home() / "Documents" / "Codex"
        if codex_root.exists():
            candidates.extend(codex_root.glob("*/*/outputs/moomoo-api-workbench"))
    seen: set[Path] = set()
    probes: list[WorkbenchProbe] = []
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        probe = _probe_workbench(resolved)
        if probe.exists and _has_workbench_artifact(probe):
            probes.append(probe)
    return probes


def _process_probe() -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            ["pgrep", "-af", "OpenD|moomoo_OpenD|Moomoo"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [{"status": "unavailable", "detail": str(exc)}]
    pids: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if parts[0].isdigit():
            pids.append(parts[0])
    if not pids:
        return []
    ps_result = subprocess.run(
        ["ps", "-p", ",".join(pids), "-o", "pid=", "-o", "args="],
        capture_output=True,
        text=True,
        check=False,
    )
    processes: list[dict[str, str]] = []
    for line in ps_result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        command = parts[1] if len(parts) > 1 else ""
        if "pgrep -af" in command:
            continue
        processes.append({"pid": parts[0], "command": command})
    return processes


def _recommended_actions(
    socket_probe: SocketProbe,
    sdk_probe: SdkProbe,
    workbenches: list[WorkbenchProbe],
    latest_failure_hint: str | None = None,
) -> list[str]:
    if socket_probe.reachable and sdk_probe.import_available:
        actions = ["moomoo_OpenD smoke is ready for read-only market data collection"]
        if workbenches and workbenches[0].quote_script:
            actions.append(f"Optional independent quote smoke: python {workbenches[0].quote_script}")
        actions.append("Keep moomoo_OpenD running and logged in before scheduled collection windows")
        return actions

    actions: list[str] = []
    if workbenches:
        primary = workbenches[0]
        if primary.moomoo_opend_app_path:
            actions.append(f"Start moomoo_OpenD app: {primary.moomoo_opend_app_path}")
        if primary.start_script:
            actions.append(f"Start moomoo_OpenD from existing workbench: {primary.start_script}")
        if primary.sdk_vendor_path and not sdk_probe.import_available:
            actions.append(f"Install local moomoo SDK vendor into this interpreter: python -m pip install {primary.sdk_vendor_path}")
        if primary.check_script:
            actions.append(f"Run existing moomoo_OpenD socket check after login: python {primary.check_script}")
        if primary.quote_script and sdk_probe.import_available and socket_probe.reachable:
            actions.append(f"Run quote smoke test: python {primary.quote_script}")
    else:
        actions.append("Install or provide a local moomoo_OpenD workbench, then start and log in to moomoo_OpenD")
    if not socket_probe.reachable:
        actions.append(f"Confirm moomoo_OpenD API listens on {socket_probe.host}:{socket_probe.port}")
    if latest_failure_hint:
        actions.append(latest_failure_hint)
    if not sdk_probe.import_available:
        actions.append("Install the moomoo Python SDK in the same interpreter used by this workspace")
    if not actions:
        actions.append("moomoo_OpenD is smoke-ready for production preflight")
    return actions


def run_moomoo_smoke(
    settings: Settings,
    host: str = "127.0.0.1",
    port: int = 11111,
    timeout: float = 0.5,
    *,
    include_user_codex: bool = True,
    write_output: bool = True,
    auto_start_opend: bool = False,
    keep_auto_started_opend: bool = False,
    opend_wait_seconds: float = 45.0,
) -> dict[str, object]:
    settings.ensure_dirs()
    lifecycle = None
    cleanup = None
    if auto_start_opend:
        from app.core.moomoo_lifecycle import cleanup_started_processes, ensure_opend, lifecycle_to_dict

        lifecycle = ensure_opend(
            settings,
            host=host,
            port=port,
            timeout=timeout,
            auto_start=True,
            cleanup_if_started=not keep_auto_started_opend,
            wait_seconds=opend_wait_seconds,
            include_user_codex=include_user_codex,
        )
    socket_probe = probe_socket(host, port, timeout)
    sdk_probe = probe_sdk()
    workbenches = discover_workbenches(settings, include_user_codex=include_user_codex)
    processes = _process_probe()
    status = "pass" if socket_probe.reachable and sdk_probe.import_available else "block"
    latest_failure_hint = None if socket_probe.reachable else _latest_opend_failure_hint()
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": status,
        "production_ready_for_moomoo_data": status == "pass",
        "socket": asdict(socket_probe),
        "sdk": asdict(sdk_probe),
        "workbenches": [asdict(workbench) for workbench in workbenches],
        "processes": processes,
        "latest_failure_hint": latest_failure_hint,
        "recommended_actions": _recommended_actions(socket_probe, sdk_probe, workbenches, latest_failure_hint),
    }
    if lifecycle is not None:
        result["opend_lifecycle"] = lifecycle_to_dict(lifecycle)
        if not keep_auto_started_opend and lifecycle.started_by_tool:
            cleanup = cleanup_started_processes(lifecycle)
            result["cleanup"] = cleanup
        elif lifecycle.started_by_tool:
            result["cleanup"] = {
                "cleanup_attempted": False,
                "cleanup_result": "kept_auto_started_opend_to_avoid_launch_close_loop",
            }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "moomoo_smoke_latest.json"
        md_path = output_dir / "moomoo_smoke_latest.md"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        md_lines = [
            "# MooMoo moomoo_OpenD Smoke Report",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Status: {status}",
            f"- Socket: {socket_probe.detail}",
            f"- SDK: {sdk_probe.detail}",
            f"- Auto-start attempted: {bool(lifecycle and lifecycle.start_attempted)}",
            f"- moomoo_OpenD lifecycle: {lifecycle.detail if lifecycle else 'not requested'}",
            "",
            "## Workbenches",
            "",
        ]
        if workbenches:
            for workbench in workbenches:
                md_lines.append(f"- {display_path(settings.root_dir, workbench.path)}")
                if workbench.start_script:
                    md_lines.append(f"  - start: `{display_path(settings.root_dir, workbench.start_script)}`")
                if workbench.sdk_vendor_path:
                    md_lines.append(f"  - SDK vendor: `{display_path(settings.root_dir, workbench.sdk_vendor_path)}`")
        else:
            md_lines.append("- None found")
        md_lines.extend(["", "## Recommended Actions", ""])
        for action in result["recommended_actions"]:
            md_lines.append(f"- {redact_text_for_markdown(settings.root_dir, action)}")
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
    return result
