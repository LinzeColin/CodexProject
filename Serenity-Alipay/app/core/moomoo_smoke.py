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


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def probe_socket(host: str, port: int, timeout: float) -> SocketProbe:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return SocketProbe(host, port, True, f"OpenD socket reachable at {host}:{port}")
    except OSError as exc:
        return SocketProbe(
            host,
            port,
            False,
            f"OpenD socket not reachable at {host}:{port}: {exc.__class__.__name__}: {exc}",
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


def _probe_workbench(path: Path) -> WorkbenchProbe:
    vendor = path / "vendor"
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
    )


def discover_workbenches(settings: Settings, include_user_codex: bool = True) -> list[WorkbenchProbe]:
    candidates: list[Path] = [
        settings.root_dir / "outputs" / "moomoo-api-workbench",
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
        if probe.exists:
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


def _recommended_actions(socket_probe: SocketProbe, sdk_probe: SdkProbe, workbenches: list[WorkbenchProbe]) -> list[str]:
    if socket_probe.reachable and sdk_probe.import_available:
        actions = ["Moomoo/OpenD smoke is ready for read-only market data collection"]
        if workbenches and workbenches[0].quote_script:
            actions.append(f"Optional independent quote smoke: python {workbenches[0].quote_script}")
        actions.append("Keep OpenD running and logged in before scheduled collection windows")
        return actions

    actions: list[str] = []
    if workbenches:
        primary = workbenches[0]
        if primary.start_script:
            actions.append(f"Start OpenD from existing workbench: {primary.start_script}")
        if primary.sdk_vendor_path and not sdk_probe.import_available:
            actions.append(f"Install local moomoo SDK vendor into this interpreter: python -m pip install {primary.sdk_vendor_path}")
        if primary.check_script:
            actions.append(f"Run existing OpenD socket check after login: python {primary.check_script}")
        if primary.quote_script and sdk_probe.import_available and socket_probe.reachable:
            actions.append(f"Run quote smoke test: python {primary.quote_script}")
    else:
        actions.append("Install or provide a local moomoo/OpenD workbench, then start and log in to OpenD")
    if not socket_probe.reachable:
        actions.append(f"Confirm OpenD API listens on {socket_probe.host}:{socket_probe.port}")
    if not sdk_probe.import_available:
        actions.append("Install the moomoo Python SDK in the same interpreter used by this workspace")
    if not actions:
        actions.append("Moomoo/OpenD is smoke-ready for production preflight")
    return actions


def run_moomoo_smoke(
    settings: Settings,
    host: str = "127.0.0.1",
    port: int = 11111,
    timeout: float = 0.5,
    *,
    include_user_codex: bool = True,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    socket_probe = probe_socket(host, port, timeout)
    sdk_probe = probe_sdk()
    workbenches = discover_workbenches(settings, include_user_codex=include_user_codex)
    processes = _process_probe()
    status = "pass" if socket_probe.reachable and sdk_probe.import_available else "block"
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": status,
        "production_ready_for_moomoo_data": status == "pass",
        "socket": asdict(socket_probe),
        "sdk": asdict(sdk_probe),
        "workbenches": [asdict(workbench) for workbench in workbenches],
        "processes": processes,
        "recommended_actions": _recommended_actions(socket_probe, sdk_probe, workbenches),
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "moomoo_smoke_latest.json"
        md_path = output_dir / "moomoo_smoke_latest.md"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        md_lines = [
            "# MooMoo/OpenD Smoke Report",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Status: {status}",
            f"- Socket: {socket_probe.detail}",
            f"- SDK: {sdk_probe.detail}",
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
