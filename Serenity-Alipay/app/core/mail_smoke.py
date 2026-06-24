from __future__ import annotations

import html
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.adapters.mail_notifier import send_with_apple_mail, write_mail_ready_draft
from app.config import Settings
from app.core.path_display import display_path


@dataclass(frozen=True)
class AppleMailProbe:
    osascript: str | None
    app_scriptable: bool
    stdout: str
    stderr: str


def _now(settings: Settings) -> datetime:
    return datetime.now(ZoneInfo(settings.timezone_primary))


def _probe_apple_mail() -> AppleMailProbe:
    osascript = shutil.which("osascript")
    if not osascript:
        return AppleMailProbe(None, False, "", "osascript not found")
    result = subprocess.run(
        [osascript, "-e", 'id of application "Mail"'],
        capture_output=True,
        text=True,
        check=False,
    )
    return AppleMailProbe(
        osascript=osascript,
        app_scriptable=result.returncode == 0,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def _write_markdown(path: Path, settings: Settings, result: dict[str, object]) -> None:
    lines = [
        "# Apple Mail Smoke",
        "",
        f"- Generated at: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Recipient: `{result['recipient_email']}`",
        f"- Draft ready: `{result['draft_ready']}`",
        f"- Apple Mail scriptable: `{result['apple_mail']['app_scriptable']}`",
        f"- Mail send enabled: `{result['mail_send_enabled']}`",
        f"- Production send ready: `{result['production_send_ready']}`",
        f"- Send requested: `{result['send_requested']}`",
        f"- Send status: `{result['send_status']}`",
        f"- Draft path: `{display_path(settings.root_dir, result['draft_path'])}`",
        "",
        "Real sending requires `--send --confirm-real-send SEND` on a runtime that enables production mail intent.",
    ]
    if result.get("send_error"):
        lines.extend(["", f"- Send error: `{result['send_error']}`"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_mail_smoke(
    settings: Settings,
    *,
    send: bool = False,
    confirm_real_send: str = "",
    title: str | None = None,
    body: str | None = None,
) -> dict[str, object]:
    settings.ensure_dirs()
    generated_at = _now(settings)
    stamp = generated_at.strftime("%Y%m%dT%H%M%S")
    subject = title or "[Serenity自动化][测试] Apple Mail 发送链路检查"
    message = body or (
        "这是 Serenity 每日分析的 Apple Mail 发送链路检查。"
        "本邮件只验证通知链路，不授权交易，不提交基金申购或赎回。"
    )
    html_message = (
        "<!doctype html><html lang=\"zh-CN\"><body "
        "style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'PingFang SC','Microsoft YaHei',sans-serif;"
        "background-color:#f8fafc;color:#0f172a;padding:20px;\">"
        "<div style=\"max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #dbe4ee;border-radius:10px;overflow:hidden;\">"
        "<div style=\"background:#102033;color:#ffffff;padding:18px 20px;\">"
        f"<h1 style=\"margin:0;font-size:22px;\">{html.escape(subject)}</h1>"
        "</div>"
        "<div style=\"padding:18px 20px;\">"
        "<h2 style=\"font-size:18px;border-bottom:2px solid #dbeafe;padding-bottom:8px;\">一、测试结论</h2>"
        "<h3 style=\"font-size:15px;color:#1d4ed8;\">Apple Mail HTML 邮件链路</h3>"
        f"<p style=\"line-height:1.7;\"><strong>{html.escape(message)}</strong></p>"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border-collapse:collapse;border:1px solid #dbe4ee;\">"
        "<tr style=\"background:#eff6ff;\"><th style=\"padding:8px;text-align:left;\">检查项</th><th style=\"padding:8px;text-align:left;\">状态</th></tr>"
        "<tr><td style=\"padding:8px;border-top:1px solid #e5e7eb;\">格式</td><td style=\"padding:8px;border-top:1px solid #e5e7eb;\"><strong style=\"color:#1d4ed8;\">HTML + 纯文本兜底</strong></td></tr>"
        "<tr><td style=\"padding:8px;border-top:1px solid #e5e7eb;\">交易边界</td><td style=\"padding:8px;border-top:1px solid #e5e7eb;\">不授权交易，不提交基金申购或赎回</td></tr>"
        "</table></div></div></body></html>"
    )
    draft_path = settings.notifications_dir / f"mail_smoke_{stamp}.md"
    write_mail_ready_draft(draft_path, subject, message, settings.recipient_email, html_body=html_message)
    probe = _probe_apple_mail()

    recipient_ready = bool(settings.recipient_email)
    production_send_ready = bool(settings.mail_send_enabled and recipient_ready and probe.app_scriptable)
    send_status = "not_requested"
    send_error = ""
    if send:
        if not settings.mail_send_enabled:
            send_status = "blocked_by_config"
            send_error = "Real sending is not enabled for this runtime"
        elif confirm_real_send != "SEND":
            send_status = "blocked_by_confirmation"
            send_error = "Real send requires --confirm-real-send SEND"
        elif not recipient_ready:
            send_status = "blocked_by_recipient"
            send_error = "recipient_email is empty"
        elif not probe.app_scriptable:
            send_status = "failed"
            send_error = probe.stderr or "Apple Mail is not script-addressable"
        else:
            mail_result = send_with_apple_mail(subject, message, settings.recipient_email, html_body=html_message)
            send_status = mail_result["status"]
            send_error = mail_result["error"]

    status = "pass"
    if not recipient_ready or not probe.app_scriptable:
        status = "blocked"
    if send and send_status != "sent":
        status = "blocked"

    output_dir = settings.root_dir / "outputs" / "preflight"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "apple_mail_smoke_latest.json"
    markdown_path = output_dir / "apple_mail_smoke_latest.md"
    result: dict[str, object] = {
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "status": status,
        "recipient_email": settings.recipient_email,
        "mail_send_enabled": settings.mail_send_enabled,
        "draft_ready": draft_path.exists() and draft_path.stat().st_size > 0,
        "draft_path": str(draft_path),
        "html_path": str(draft_path.with_suffix(".html")),
        "apple_mail": asdict(probe),
        "production_send_ready": production_send_ready,
        "send_requested": send,
        "send_status": send_status,
        "send_error": send_error,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(markdown_path, settings, result)
    return result
