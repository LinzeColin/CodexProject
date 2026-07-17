#!/usr/bin/env python3
"""Browser smoke test for the localhost-only S06-P2 private review UI.

This is intentionally separate from unittest discovery because Playwright is an
optional validation dependency.  The script emits aggregate state only and
never prints candidate content.
"""

from __future__ import annotations

import argparse
import atexit
import json
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


AUTHORIZATION = "I_CONFIRM_V015_S06_P2_GOLDEN_BASELINE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-host", action="store_true")
    parser.add_argument("--url")
    parser.add_argument("--draft-path", type=Path)
    parser.add_argument("--signoff-path", type=Path)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    temporary = None
    if args.self_host:
        from KMFA.tools import v015_s06_p2_signoff_review as review

        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        args.draft_path = root / "draft.json"
        args.signoff_path = root / "signoff.json"
        args.screenshot = root / "review.png"
        server = review.build_server(
            draft_path=args.draft_path, signoff_path=args.signoff_path,
            token="S06P2_BROWSER_SMOKE_TOKEN_000001",
        )
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        atexit.register(server.shutdown)
        args.url = server.review_url
    if not all((args.url, args.draft_path, args.signoff_path, args.screenshot)):
        parser.error("use --self-host or provide --url, --draft-path, --signoff-path and --screenshot")
    external_requests: list[str] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    http_errors: list[tuple[str, int]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.on(
            "request",
            lambda request: external_requests.append(request.url)
            if urlsplit(request.url).hostname not in {"127.0.0.1", "localhost"}
            else None,
        )
        page.on(
            "console",
            lambda message: console_errors.append(message.text) if message.type == "error" else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "response",
            lambda response: http_errors.append((urlsplit(response.url).path, response.status))
            if response.status >= 400
            else None,
        )
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_function("window.__KMFA_REVIEW_READY__ === true")
        candidate_count = int(page.locator("#total").inner_text())
        assert candidate_count > 0
        assert int(page.locator("#pending").inner_text()) == candidate_count
        assert page.locator("#accepted").inner_text() == "0"
        assert page.locator("#rejected").inner_text() == "0"

        page.locator("#source").select_option("S06P1-SRC-001")
        assert "筛选后 12 条" in page.locator("#pageInfo").inner_text()
        assert "待决定 12 条" in page.locator("#sourceInfo").inner_text()
        page.locator("#resetFilters").click()

        page.locator("#family").select_option("CONTRACT_AMOUNT")
        page.locator("#pageInfo").wait_for(state="visible")
        assert "筛选后 14 条" in page.locator("#pageInfo").inner_text()
        page.locator("#resetFilters").click()

        first = page.locator(".candidate").first
        first.locator("select").first.select_option("REJECT")
        first.locator("textarea").fill("browser smoke test rejection")
        page.locator("#identity").fill("browser-test-owner")
        page.locator("#role").fill("data-owner-test")
        page.locator("#confirmedAt").fill("2026-07-15T02:00:00+10:00")
        page.locator("#basis").fill("browser interaction smoke test only")
        page.locator("#save").click()
        page.locator("#message").filter(has_text="草稿已保存").wait_for()
        assert args.draft_path.exists()

        page.reload(wait_until="networkidle")
        page.wait_for_function("window.__KMFA_REVIEW_READY__ === true")
        assert int(page.locator("#pending").inner_text()) == candidate_count - 1
        assert page.locator("#rejected").inner_text() == "1"
        page.locator("#authorization").fill(AUTHORIZATION)
        page.locator("#finalize").click()
        page.locator("#message.error").wait_for()
        assert not args.signoff_path.exists()
        page.screenshot(path=str(args.screenshot), full_page=True)
        browser.close()

    assert external_requests == [], external_requests
    assert page_errors == [], page_errors
    assert http_errors == [("/api/finalize", 400)], http_errors
    unexpected_console_errors = [
        value for value in console_errors
        if not value.startswith("Failed to load resource: the server responded with a status of 400")
    ]
    assert unexpected_console_errors == [], unexpected_console_errors
    print(json.dumps({
        "status": "PASS",
        "candidate_count": candidate_count,
        "draft_persistence_verified": True,
        "incomplete_finalize_failed_closed": True,
        "external_request_count": 0,
        "page_error_count": 0,
        "unexpected_console_error_count": 0,
        "expected_fail_closed_http_400_count": 1,
        "screenshot_created": args.screenshot.exists(),
    }, sort_keys=True))
    if args.self_host:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
