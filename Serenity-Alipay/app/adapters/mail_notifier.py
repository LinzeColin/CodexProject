from __future__ import annotations

import os
import subprocess
from pathlib import Path


APPLE_MAIL_TIMEOUT_SECONDS = int(os.getenv("SERENITY_APPLE_MAIL_TIMEOUT_SECONDS", "45"))


def _applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "\\n") + '"'


def write_mail_ready_draft(path: Path, title: str, body: str, recipient: str, html_body: str | None = None) -> Path:
    text = f"To: {recipient}\nSubject: {title}\n\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if html_body:
        path.with_suffix(".html").write_text(html_body, encoding="utf-8")
    return path


def _plain_mail_script(title: str, body: str, recipient: str) -> str:
    return f'''
with timeout of {APPLE_MAIL_TIMEOUT_SECONDS} seconds
    tell application "Mail"
        activate
        set newMessage to make new outgoing message with properties {{subject:{_applescript_string(title)}, content:{_applescript_string(body)}, visible:false}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:{_applescript_string(recipient)}}}
            ignoring application responses
                send
            end ignoring
        end tell
    end tell
end timeout
'''


def _html_mail_script(title: str, body: str, html_body: str, recipient: str) -> str:
    return f'''
with timeout of {APPLE_MAIL_TIMEOUT_SECONDS} seconds
    tell application "Mail"
        activate
        set newMessage to make new outgoing message with properties {{subject:{_applescript_string(title)}, visible:false}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:{_applescript_string(recipient)}}}
            try
                set html content to {_applescript_string(html_body)}
            on error
                set content to {_applescript_string(body)}
            end try
            ignoring application responses
                send
            end ignoring
        end tell
    end tell
end timeout
'''


def _run_osascript(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=APPLE_MAIL_TIMEOUT_SECONDS + 5,
    )


def _send_error(result: subprocess.CompletedProcess[str]) -> str:
    return result.stderr.strip() or result.stdout.strip()


def send_with_apple_mail(title: str, body: str, recipient: str, html_body: str | None = None) -> dict[str, str]:
    script = _html_mail_script(title, body, html_body, recipient) if html_body else _plain_mail_script(title, body, recipient)
    try:
        result = _run_osascript(script)
    except subprocess.TimeoutExpired:
        result = subprocess.CompletedProcess(["osascript", "-e", script], 124, "", "Apple Mail osascript subprocess timed out")
    if result.returncode != 0 and html_body:
        try:
            fallback = _run_osascript(_plain_mail_script(title, body, recipient))
        except subprocess.TimeoutExpired:
            fallback = subprocess.CompletedProcess(
                ["osascript", "-e", "plain-mail-fallback"],
                124,
                "",
                "Apple Mail plain-text fallback subprocess timed out",
            )
        if fallback.returncode == 0:
            return {"status": "sent", "error": ""}
        return {"status": "failed", "error": _send_error(fallback)}
    if result.returncode != 0:
        return {"status": "failed", "error": _send_error(result)}
    return {"status": "sent", "error": ""}
