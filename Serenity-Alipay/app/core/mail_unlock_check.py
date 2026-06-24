from __future__ import annotations

import json
import plistlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.mail_smoke import run_mail_smoke


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _rel(settings: Settings, path: Path | str) -> str:
    path_obj = Path(path)
    try:
        return path_obj.relative_to(settings.root_dir).as_posix()
    except ValueError:
        return str(path)


def _load_plist(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        data = plistlib.load(handle)
    return data if isinstance(data, dict) else {}


def _write_production_mail_plist(settings: Settings) -> tuple[Path, bool, str]:
    source = settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist"
    destination = settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.production-mail.plist"
    data = _load_plist(source)
    if not data:
        return destination, False, "source launchd plist missing or invalid"
    env = data.get("EnvironmentVariables")
    if isinstance(env, dict):
        env.pop("SERENITY_MAIL_SEND_ENABLED", None)
        env.pop("SERENITY_DRY_RUN", None)
        if env:
            data["EnvironmentVariables"] = env
        else:
            data.pop("EnvironmentVariables", None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        plistlib.dump(data, handle, sort_keys=False)
    return destination, True, "production launchd review copy generated with command-driven mail semantics; not installed"


def _write_markdown(path: Path, result: dict[str, object], settings: Settings) -> None:
    lines = [
        "# Mail Unlock Check",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Workflow ready: {result['workflow_ready']}",
        f"- Production send ready now: {result['production_send_ready_now']}",
        f"- Mail send enabled now: {result['mail_send_enabled_now']}",
        f"- Recipient: `{result['recipient_email']}`",
        f"- Production plist generated: {result['production_plist_generated']}",
        f"- Production plist path: `{_rel(settings, result['production_plist_path'])}`",
        "",
        "## Required Manual Gate",
        "",
        "Run the real-send smoke only after production data gates pass and you explicitly want a real test email:",
        "",
        "```bash",
        str(result["real_send_smoke_command"]),
        "```",
        "",
        "Install or reload the launchd plist after the real-send smoke succeeds if you need to refresh the installed job:",
        "",
        "```bash",
        str(result["install_production_plist_command"]),
        "```",
        "",
        "Rollback command:",
        "",
        "```bash",
        str(result["rollback_command"]),
        "```",
        "",
        "## Boundary",
        "",
        "- This command does not send mail.",
        "- This command does not install or reload launchd.",
        "- This command does not place trades.",
        "- The launchd template and automation command share the same command-driven production mail semantics; no separate env flip is required.",
        "- Current production remains blocked until data gates pass and a real-send smoke is explicitly approved.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_mail_unlock_check(settings: Settings) -> dict[str, object]:
    settings.ensure_dirs()
    smoke = run_mail_smoke(settings, send=False)
    plist_path, plist_generated, plist_message = _write_production_mail_plist(settings)
    workflow_ready = bool(
        smoke.get("draft_ready")
        and isinstance(smoke.get("apple_mail"), dict)
        and smoke["apple_mail"].get("app_scriptable")
        and settings.recipient_email
        and plist_generated
    )
    status = "pass" if workflow_ready else "blocked"
    real_send_smoke_command = (
        "python -m app.cli mail-smoke "
        "--send --confirm-real-send SEND --require-send-ready --json"
    )
    install_production_plist_command = (
        "cp outputs/implementation/com.serenity.daily-analysis.plist "
        "~/Library/LaunchAgents/com.serenity.daily-analysis.plist && "
        "plutil -lint ~/Library/LaunchAgents/com.serenity.daily-analysis.plist && "
        "launchctl kickstart -k \"gui/$(id -u)/com.serenity.daily-analysis\""
    )
    rollback_command = "echo 'No launchd rollback needed; the base plist already uses command-driven production semantics.'"
    output_dir = settings.root_dir / "outputs" / "preflight"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mail_unlock_check_latest.json"
    markdown_path = output_dir / "mail_unlock_check_latest.md"
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "status": status,
        "workflow_ready": workflow_ready,
        "production_send_ready_now": smoke.get("production_send_ready"),
        "mail_send_enabled_now": settings.mail_send_enabled,
        "recipient_email": settings.recipient_email,
        "mail_smoke_status": smoke.get("status"),
        "mail_smoke_json_path": smoke.get("json_path"),
        "production_plist_path": str(plist_path),
        "production_plist_generated": plist_generated,
        "production_plist_message": plist_message,
        "real_send_smoke_command": real_send_smoke_command,
        "install_production_plist_command": install_production_plist_command,
        "rollback_command": rollback_command,
        "mail_sent": False,
        "launchd_modified": False,
        "trades_placed": False,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(markdown_path, result, settings)
    return result
