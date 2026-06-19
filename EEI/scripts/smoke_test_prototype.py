#!/usr/bin/env python3
"""Offline browser smoke test for the fixture-only v4.2 prototype.

Requires Python Playwright and a Chromium executable. The single-file prototype
is injected with page.set_content(), so no network or local server is needed.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "prototype/standalone.html"


def main() -> int:
    errors: list[str] = []
    result: dict[str, object] = {}
    executable = (
        os.environ.get("CHROMIUM_PATH")
        or shutil.which("chromium")
        or shutil.which("google-chrome")
    )
    html = HTML.read_text(encoding="utf-8")

    with sync_playwright() as playwright:
        launch_args: dict[str, object] = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        }
        if executable:
            launch_args["executable_path"] = executable
        browser = playwright.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
            reduced_motion="no-preference",
        )
        page = context.new_page()
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.on(
            "console",
            lambda msg: errors.append(f"console {msg.type}: {msg.text}")
            if msg.type in {"error", "warning"}
            else None,
        )
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(900)

        result["title"] = page.title()
        result["node_count"] = page.locator("#nodeLayer .graph-node").count()
        result["edge_count"] = page.locator("#edgeLayer .edge-path").count()
        result["fixture_badge"] = page.get_by_text("交互原型 · 示例数据", exact=True).count() == 1

        for view in ["models", "data", "taxonomy", "delivery", "governance", "map"]:
            page.locator(f'[data-view="{view}"]').click()
            page.wait_for_timeout(160)
            active = page.locator(".screen.active").get_attribute("data-screen")
            if active != view:
                raise AssertionError(f"view did not activate: expected={view}, actual={active}")

        page.locator('[data-view="map"]').click()
        page.locator('[data-node="tsmc"]').click()
        page.wait_for_timeout(180)
        if page.locator("#inspectorDrawer").get_attribute("aria-hidden") != "false":
            raise AssertionError("TSMC detail drawer did not open")
        page.locator("#drawerFocusButton").click()
        page.wait_for_timeout(620)
        heading = page.locator("#focusTitle").inner_text()
        if "TSMC" not in heading:
            raise AssertionError(f"reroot failed, heading={heading!r}")
        result["reroot_target"] = heading
        result["page_console_errors"] = errors
        context.close()
        browser.close()

    if int(result["node_count"]) < 10 or int(result["edge_count"]) < 10:
        raise AssertionError(f"graph unexpectedly empty: {result}")
    if not result["fixture_badge"]:
        raise AssertionError("fixture disclosure badge missing")
    if errors:
        raise AssertionError("browser emitted errors/warnings: " + "; ".join(errors))

    print("Prototype smoke test: PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
