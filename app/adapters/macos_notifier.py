from __future__ import annotations

import subprocess
from pathlib import Path


def applescript_for_notification(title: str, body: str) -> str:
    safe_title = title.replace('"', '\\"')
    safe_body = body.replace('"', '\\"').replace("\n", " ")[:220]
    return f'display notification "{safe_body}" with title "{safe_title}"'


def write_local_notification_script(path: Path, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(applescript_for_notification(title, body) + "\n", encoding="utf-8")
    return path


def send_local_notification(title: str, body: str) -> dict[str, str]:
    result = subprocess.run(
        ["osascript", "-e", applescript_for_notification(title, body)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {"status": "failed", "error": result.stderr.strip() or result.stdout.strip()}
    return {"status": "sent", "error": ""}
