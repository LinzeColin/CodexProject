from __future__ import annotations

import subprocess
from pathlib import Path


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
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:{_applescript_string(title)}, content:{_applescript_string(body)}, visible:false}}
    tell newMessage
        make new to recipient at end of to recipients with properties {{address:{_applescript_string(recipient)}}}
        send
    end tell
end tell
'''


def _html_mail_script(title: str, body: str, html_body: str, recipient: str) -> str:
    return f'''
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:{_applescript_string(title)}, visible:false}}
    tell newMessage
        make new to recipient at end of to recipients with properties {{address:{_applescript_string(recipient)}}}
        try
            set html content to {_applescript_string(html_body)}
        on error
            set content to {_applescript_string(body)}
        end try
        send
    end tell
end tell
'''


def send_with_apple_mail(title: str, body: str, recipient: str, html_body: str | None = None) -> dict[str, str]:
    script = _html_mail_script(title, body, html_body, recipient) if html_body else _plain_mail_script(title, body, recipient)
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    if result.returncode != 0 and html_body:
        fallback = subprocess.run(
            ["osascript", "-e", _plain_mail_script(title, body, recipient)],
            capture_output=True,
            text=True,
            check=False,
        )
        if fallback.returncode == 0:
            return {"status": "sent", "error": ""}
        return {"status": "failed", "error": fallback.stderr.strip() or fallback.stdout.strip()}
    if result.returncode != 0:
        return {"status": "failed", "error": result.stderr.strip() or result.stdout.strip()}
    return {"status": "sent", "error": ""}
