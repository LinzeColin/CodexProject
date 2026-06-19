#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "prototype" / "standalone.html"
TARGETS = json.loads((ROOT / "config" / "ui" / "visual-coverage-targets.json").read_text(encoding="utf-8"))
CORE_VIEWS = ["data", "models", "taxonomy", "delivery", "architecture", "governance", "ops"]


def _launch_kwargs() -> dict:
    candidates = [os.environ.get("CHROMIUM_PATH"), "/usr/bin/chromium", "/usr/bin/chromium-browser"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return {"executable_path": candidate, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    return {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}


def _measure(page, view: str) -> dict:
    page.evaluate("view => showView(view, false)", view)
    page.wait_for_timeout(120)
    return page.evaluate(
        """
        () => {
          const screen = document.querySelector('.screen.active[data-information-workspace]');
          if (!screen) throw new Error('active information workspace missing');
          const sr = screen.getBoundingClientRect();
          const heading = screen.querySelector(':scope > .screen-heading');
          const hr = heading ? heading.getBoundingClientRect() : null;
          const bounds = {
            left: sr.left,
            right: sr.right,
            top: hr ? Math.max(sr.top, hr.bottom) : sr.top,
            bottom: sr.bottom,
          };
          const surfaces = [...screen.querySelectorAll('[data-visual-surface]')]
            .filter(el => getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden')
            .map(el => {
              const r = el.getBoundingClientRect();
              return {
                left: Math.max(bounds.left, r.left),
                right: Math.min(bounds.right, r.right),
                top: Math.max(bounds.top, r.top),
                bottom: Math.min(bounds.bottom, r.bottom),
              };
            })
            .filter(r => r.right > r.left && r.bottom > r.top);

          const xs = [...new Set([bounds.left, bounds.right, ...surfaces.flatMap(r => [r.left, r.right])])].sort((a,b)=>a-b);
          let union = 0;
          for (let i=0; i<xs.length-1; i++) {
            const x1=xs[i], x2=xs[i+1];
            if (x2 <= x1) continue;
            const intervals = surfaces
              .filter(r => r.left < x2 && r.right > x1)
              .map(r => [r.top, r.bottom])
              .sort((a,b)=>a[0]-b[0]);
            let covered = 0, start = null, end = null;
            for (const [a,b] of intervals) {
              if (start === null) { start=a; end=b; continue; }
              if (a <= end) end=Math.max(end,b);
              else { covered += end-start; start=a; end=b; }
            }
            if (start !== null) covered += end-start;
            union += (x2-x1)*covered;
          }
          const workspaceArea = Math.max(1, (bounds.right-bounds.left)*(bounds.bottom-bounds.top));
          return {
            screen: screen.dataset.screen,
            ratio: union/workspaceArea,
            workspace_area: workspaceArea,
            visual_area: union,
            surface_count: surfaces.length,
          };
        }
        """
    )


def main() -> int:
    html = HTML.read_text(encoding="utf-8")
    home_min = float(TARGETS["home_visual_surface_ratio_min"])
    system_min = float(TARGETS["system_visual_first_coverage_min"])
    model_min = float(TARGETS["model_studio_visual_surface_ratio_min"])
    failures: list[str] = []
    rows: list[dict] = []
    page_errors: list[str] = []
    console_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **_launch_kwargs())
        for viewport in TARGETS["viewports"]:
            page = browser.new_page(viewport=viewport, reduced_motion="no-preference")
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type in ("warning", "error") else None)
            page.set_content(html, wait_until="load")
            page.wait_for_timeout(500)
            home = _measure(page, "map")
            core = [_measure(page, view) for view in CORE_VIEWS]
            average = sum(x["ratio"] for x in core) / len(core)
            rows.append({"viewport": viewport, "home": home, "core": core, "system_average": average})
            label = f"{viewport['width']}x{viewport['height']}"
            if home["ratio"] + 1e-9 < home_min:
                failures.append(f"{label}: home {home['ratio']:.3f} < {home_min:.3f}")
            if average + 1e-9 < system_min:
                failures.append(f"{label}: system average {average:.3f} < {system_min:.3f}")
            model = next(x for x in core if x["screen"] == "models")
            if model["ratio"] + 1e-9 < model_min:
                failures.append(f"{label}: model studio {model['ratio']:.3f} < {model_min:.3f}")
            page.close()
        browser.close()

    if page_errors:
        failures.append(f"page errors: {page_errors}")
    if console_errors:
        failures.append(f"console warnings/errors: {console_errors}")

    print("VISUAL COVERAGE REPORT")
    for row in rows:
        vp = row["viewport"]
        print(f"viewport={vp['width']}x{vp['height']} home={row['home']['ratio']:.3f} system_average={row['system_average']:.3f}")
        for item in row["core"]:
            print(f"  {item['screen']}: {item['ratio']:.3f} ({item['surface_count']} surfaces)")
    if failures:
        print("VISUAL COVERAGE: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("VISUAL COVERAGE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
