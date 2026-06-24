from app.adapters.mail_notifier import send_with_apple_mail
from subprocess import TimeoutExpired


class _Completed:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_send_with_apple_mail_prefers_html_content(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return _Completed()

    monkeypatch.setattr("app.adapters.mail_notifier.subprocess.run", fake_run)

    result = send_with_apple_mail(
        "标题",
        "纯文本兜底",
        "linzezhang35@gmail.com",
        html_body="<!doctype html><html><body><h1>标题</h1><table></table></body></html>",
    )

    assert result == {"status": "sent", "error": ""}
    assert len(calls) == 1
    assert "set html content to" in calls[0][2]
    assert "set content to" in calls[0][2]
    assert "ignoring application responses" in calls[0][2]
    assert "with timeout of" in calls[0][2]


def test_send_with_apple_mail_falls_back_to_plain_text_when_html_script_fails(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            return _Completed(returncode=1, stderr="html failed")
        return _Completed()

    monkeypatch.setattr("app.adapters.mail_notifier.subprocess.run", fake_run)

    result = send_with_apple_mail(
        "标题",
        "纯文本兜底",
        "linzezhang35@gmail.com",
        html_body="<!doctype html><html><body><h1>标题</h1></body></html>",
    )

    assert result == {"status": "sent", "error": ""}
    assert len(calls) == 2
    assert "set html content to" in calls[0][2]
    assert "content:" in calls[1][2]
    assert "ignoring application responses" in calls[1][2]


def test_send_with_apple_mail_reports_subprocess_timeout(monkeypatch):
    def fake_run(args, **kwargs):
        raise TimeoutExpired(args, kwargs.get("timeout"))

    monkeypatch.setattr("app.adapters.mail_notifier.subprocess.run", fake_run)

    result = send_with_apple_mail("标题", "纯文本兜底", "linzezhang35@gmail.com")

    assert result["status"] == "failed"
    assert "timed out" in result["error"]
