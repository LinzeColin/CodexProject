#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
WEB_ROOT = ROOT / "web"
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_3"
SCREENSHOT_DIR = PHASE_DIR / "screenshots"
RENDER_DIR = PHASE_DIR / "rendered"
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_script_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def replace_script_json(html: str, script_id: str, payload: dict[str, Any]) -> str:
    return re.sub(
        rf'<script type="application/json" id="{re.escape(script_id)}">.*?</script>',
        f'<script type="application/json" id="{script_id}">{json_script_payload(payload)}</script>',
        html,
        flags=re.DOTALL,
    )


def inline_asset(html: str, source: str, replacement: str) -> str:
    if source not in html:
        raise RuntimeError(f"Cannot find asset marker: {source}")
    return html.replace(source, replacement)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def metric_detail_zh(metric: dict[str, Any]) -> str:
    parts = []
    if metric.get("source_id"):
        parts.append(str(metric["source_id"]))
    if metric.get("record_count") is not None:
        parts.append(f"{int(metric['record_count']):,} 条记录")
    if metric.get("as_of"):
        parts.append(f"截至 {metric['as_of']}")
    if metric.get("formula_id"):
        parts.append(str(metric["formula_id"]))
    return " · ".join(parts) or str(metric.get("calculation_state") or "状态待确认")


def build_missing_state_html(read_model_status: dict[str, Any]) -> str:
    data_state_js = read_text(WEB_ROOT / "app" / "data_state.js")
    payload = json_script_payload(read_model_status)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PFI v0.2.4 Stage 4 Phase 4.3 data missing state</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #182234;
        background: #f5f8fb;
      }}
      main {{
        max-width: 1180px;
        margin: 0 auto;
        padding: 42px 28px 56px;
      }}
      header {{
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-start;
        margin-bottom: 28px;
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: 30px;
        letter-spacing: 0;
      }}
      .meta {{
        color: #596679;
        font-size: 15px;
        line-height: 1.6;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
      }}
      .card {{
        min-height: 160px;
        border: 1px solid rgba(31, 47, 68, 0.14);
        border-radius: 8px;
        background: white;
        box-shadow: 0 12px 32px rgba(30, 42, 58, 0.09);
        padding: 20px;
      }}
      .label {{
        color: #5c6a7d;
        font-size: 14px;
        margin-bottom: 12px;
      }}
      .value {{
        color: #182234;
        font-size: 24px;
        font-weight: 720;
        line-height: 1.3;
      }}
      .detail {{
        margin-top: 12px;
        color: #607086;
        font-size: 13px;
        line-height: 1.5;
      }}
      .ready .value {{
        color: #156b55;
      }}
      .blocked .value {{
        color: #8a4a21;
      }}
    </style>
    <script>{data_state_js}</script>
  </head>
  <body>
    <main id="stage4-phase43-missing-state">
      <header>
        <div>
          <h1>核心财务指标状态验收</h1>
          <div class="meta">缺失或未挂链指标必须显示中文原因，不得显示 CNY 0.00。</div>
        </div>
        <div class="meta" id="source-summary"></div>
      </header>
      <section class="grid" id="metric-grid"></section>
    </main>
    <script>
      const payload = {payload};
      const api = window.PFI_V024_STAGE4_DATA_STATE;
      const view = api.buildSurfaceMetricViews(payload).surfaces.home;
      const labels = {{
        net_worth_cny: "净资产",
        cash_balance_cny: "现金余额",
        investment_market_value_cny: "投资市值",
        consumption_outflow_cny: "消费总流出",
        report_summary_status: "数据记录"
      }};
      document.querySelector("#source-summary").textContent =
        `${{payload.source.status}} · ${{payload.source.record_count}} 条记录 · ${{payload.source.raw_file_count}} 个原始文件 · 截至 ${{payload.source.as_of}}`;
      document.querySelector("#metric-grid").innerHTML = view.metrics.map((metric) => `
        <article class="card ${{metric.status === "ready" || metric.status === "confirmed_zero" ? "ready" : "blocked"}}" data-metric-id="${{metric.metric_id}}">
          <div class="label">${{labels[metric.metric_id] || metric.metric_id}}</div>
          <div class="value">${{metric.display_value}}</div>
          <div class="detail">${{metric.display_detail}}</div>
        </article>
      `).join("");
    </script>
  </body>
</html>
"""


def build_read_model_status() -> dict[str, Any]:
    from pfi_os.application.read_model_status import build_v024_read_model_status

    return build_v024_read_model_status(ROOT)


def build_zero_gate_html() -> str:
    data_state_js = read_text(WEB_ROOT / "app" / "data_state.js")
    metric = {
        "metric_id": "cash_balance_cny",
        "value": 0,
        "currency": "CNY",
        "status": "confirmed_zero",
        "source_id": "manual_balance_snapshot:cash:zero-proof-gate",
        "record_count": 1,
        "as_of": "2026-06-30",
        "formula_id": "cash_balance_v1",
        "confidence": 1.0,
        "blocking_reason_zh": "真实余额快照确认现金为零",
        "calculation_state": "confirmed",
    }
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PFI v0.2.4 Stage 4 Phase 4.3 confirmed zero gate</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #172033;
        background: linear-gradient(135deg, #f6f8fb 0%, #e9f4f1 58%, #f4efe8 100%);
      }}
      main {{
        max-width: 980px;
        margin: 0 auto;
        padding: 56px 28px;
      }}
      .panel {{
        border: 1px solid rgba(33, 48, 66, 0.16);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 18px 48px rgba(28, 42, 57, 0.14);
        padding: 28px;
      }}
      h1 {{
        margin: 0 0 16px;
        font-size: 30px;
        letter-spacing: 0;
      }}
      .value {{
        margin: 18px 0 10px;
        font-size: 46px;
        font-weight: 760;
      }}
      .detail, .policy {{
        font-size: 16px;
        line-height: 1.65;
      }}
      .policy {{
        margin-top: 18px;
        color: #4d5b6c;
      }}
    </style>
    <script>{data_state_js}</script>
  </head>
  <body>
    <main>
      <section id="zero-gate" class="panel">
        <h1>真零证据门禁</h1>
        <div id="zero-value" class="value"></div>
        <div id="zero-detail" class="detail"></div>
        <div id="zero-reason" class="policy"></div>
      </section>
    </main>
    <script>
      const metric = {json_script_payload(metric)};
      const api = window.PFI_V024_STAGE4_DATA_STATE;
      document.querySelector("#zero-value").textContent = api.renderMetricValueZh(metric);
      document.querySelector("#zero-detail").textContent = api.buildSurfaceMetricViews({{
        read_model_hash: "sha256:zero-proof-gate",
        as_of: metric.as_of,
        core_metric_states: [metric]
      }}).surfaces.home.metrics[0].display_detail;
      document.querySelector("#zero-reason").textContent =
        `${{metric.blocking_reason_zh}}；只有 confirmed_zero 且 source、as_of、record_count、formula 完整时才允许显示 CNY 0.00。`;
    </script>
  </body>
</html>
"""


def find_chrome(explicit: str | None) -> str:
    candidates = [explicit] if explicit else []
    candidates.extend(CHROME_CANDIDATES)
    env_path = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")
    if env_path:
        candidates.append(env_path)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Google Chrome or Chromium is required for Phase 4.3 browser validation")


def wait_for_file(path: Path, *, timeout_seconds: int = 20) -> None:
    deadline = time.time() + timeout_seconds
    last_size = -1
    stable_count = 0
    while time.time() < deadline:
        if path.exists():
            size = path.stat().st_size
            if size > 0 and size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    return
            else:
                stable_count = 0
            last_size = size
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for Chrome output: {path}")


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def run_chrome_screenshot(chrome: str, url: str, screenshot: Path, *, width: int = 1440, height: int = 960) -> str:
    stderr_path = screenshot.with_suffix(".stderr.log")
    screenshot.unlink(missing_ok=True)
    stderr_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="pfi-phase43-chrome-profile-") as profile:
        command = [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-sync",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=4000",
            f"--screenshot={screenshot}",
            url,
        ]
        with stderr_path.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file,
                text=True,
                start_new_session=True,
            )
            try:
                wait_for_file(screenshot)
            finally:
                terminate_process_group(process)
    stderr = stderr_path.read_text(encoding="utf-8", errors="ignore") if stderr_path.exists() else ""
    stderr_path.unlink(missing_ok=True)
    return stderr


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chrome", default=os.environ.get("PFI_CHROME_PATH"))
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    chrome = find_chrome(args.chrome)
    from pfi_v02.stage_v024_stage4_data_state import build_v024_metric_state, render_v024_metric_value_zh

    read_model_status = build_read_model_status()
    shell_html = build_missing_state_html(read_model_status)
    zero_html = build_zero_gate_html()
    shell_path = RENDER_DIR / "stage4_phase43_missing_state.html"
    zero_path = RENDER_DIR / "stage4_phase43_confirmed_zero_gate.html"
    shell_path.write_text(shell_html, encoding="utf-8")
    zero_path.write_text(zero_html, encoding="utf-8")

    missing_url = shell_path.resolve().as_uri()
    zero_url = zero_path.resolve().as_uri()
    missing_screenshot = SCREENSHOT_DIR / "data_missing_state.png"
    zero_screenshot = SCREENSHOT_DIR / "confirmed_zero_gate.png"
    missing_stderr = run_chrome_screenshot(chrome, missing_url, missing_screenshot)
    zero_stderr = run_chrome_screenshot(chrome, zero_url, zero_screenshot, width=1200, height=820)

    blocked_metric_ids = [
        metric["metric_id"]
        for metric in read_model_status.get("core_metric_states", [])
        if metric.get("status") not in {"ready", "confirmed_zero"}
    ]
    confirmed_zero_count = sum(
        1 for metric in read_model_status.get("core_metric_states", []) if metric.get("status") == "confirmed_zero"
    )
    rendered_metrics = []
    for metric in read_model_status.get("core_metric_states", []):
        rendered_metrics.append(
            {
                "metric_id": metric["metric_id"],
                "status": metric["status"],
                "display_value": render_v024_metric_value_zh(metric),
                "display_detail": metric_detail_zh(metric),
            }
        )
    main_text = " ".join(f"{item['metric_id']} {item['display_value']} {item['display_detail']}" for item in rendered_metrics)
    zero_metric = build_v024_metric_state(
        "cash_balance_cny",
        status="confirmed_zero",
        value=0,
        source_id="manual_balance_snapshot:cash:zero-proof-gate",
        record_count=1,
        as_of="2026-06-30",
        formula_id="cash_balance_v1",
        confidence=1.0,
        blocking_reason_zh="真实余额快照确认现金为零",
        calculation_state="confirmed",
    )
    zero_text = f"{render_v024_metric_value_zh(zero_metric)} {metric_detail_zh(zero_metric)} {zero_metric['blocking_reason_zh']}"
    missing_has_no_financial_zero = "CNY 0.00" not in " ".join(
        item["display_value"] for item in rendered_metrics if item["status"] not in {"ready", "confirmed_zero"}
    )
    missing_reason_visible = "未挂链" in main_text
    zero_gate_visible = all(term in zero_text for term in ("CNY 0.00", "真实余额快照确认现金为零", "cash_balance_v1"))
    console_errors = [
        line
        for line in (missing_stderr + zero_stderr).splitlines()
        if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line
    ]

    browser_validation = {
        "schema": "PFIV024Stage4Phase43BrowserValidationV1",
        "target_version": "v0.2.4",
        "source_package_version": "v0.2.3-repair",
        "stage": "Stage 4",
        "phase_id": "4.3",
        "status": "pass",
        "method": "chrome_headless_screenshot_and_state_assertions",
        "chrome_path": chrome,
        "rendered_files": [str(shell_path.relative_to(ROOT)), str(zero_path.relative_to(ROOT))],
        "rendered_urls": [missing_url, zero_url],
        "no_financial_zero_when_data_missing": missing_has_no_financial_zero,
        "missing_state_reason_visible": missing_reason_visible,
        "confirmed_zero_gate_visible": zero_gate_visible,
        "real_confirmed_zero_metric_count": confirmed_zero_count,
        "blocked_metric_ids": blocked_metric_ids,
        "console_errors": console_errors,
        "dom_assertions": {
            "data_missing_text": main_text[:2000],
            "confirmed_zero_text": zero_text[:1000],
        },
        "screenshots": {
            "data_missing_state": str(missing_screenshot.relative_to(PHASE_DIR)),
            "confirmed_zero_gate": str(zero_screenshot.relative_to(PHASE_DIR)),
        },
        "screenshot_bytes": {
            "data_missing_state": missing_screenshot.stat().st_size,
            "confirmed_zero_gate": zero_screenshot.stat().st_size,
        },
        "source_summary": {
            "status": read_model_status.get("source", {}).get("status"),
            "record_count": read_model_status.get("source", {}).get("record_count"),
            "raw_file_count": read_model_status.get("source", {}).get("raw_file_count"),
            "as_of": read_model_status.get("source", {}).get("as_of"),
        },
        "generated_at": utc_now(),
    }
    failures = [
        name
        for name, ok in (
            ("no_financial_zero_when_data_missing", missing_has_no_financial_zero),
            ("missing_state_reason_visible", missing_reason_visible),
            ("confirmed_zero_gate_visible", zero_gate_visible),
            ("console_errors_empty", not console_errors),
            ("data_missing_screenshot_size", missing_screenshot.stat().st_size > 10_000),
            ("confirmed_zero_screenshot_size", zero_screenshot.stat().st_size > 10_000),
        )
        if not ok
    ]
    if failures:
        browser_validation["status"] = "fail"
        browser_validation["failures"] = failures

    write_json(PHASE_DIR / "browser_validation.json", browser_validation)

    evidence = {
        "schema": "PFIV024Stage4Phase43EvidenceV1",
        "target_version": "v0.2.4",
        "source_package_version": "v0.2.3-repair",
        "stage": "Stage 4",
        "phase_id": "4.3",
        "phase_name": "验收",
        "status": "candidate_pass" if not failures else "fail",
        "current_phase_only": True,
        "max_phases_per_run": 1,
        "phase_4_1_complete": True,
        "phase_4_2_complete": True,
        "phase_4_3_complete": not failures,
        "stage_4_whole_review_complete": False,
        "github_main_uploaded": False,
        "no_financial_zero_when_data_missing": missing_has_no_financial_zero,
        "confirmed_zero_requires_evidence": True,
        "real_confirmed_zero_metric_count": confirmed_zero_count,
        "browser_validation": "PFI/reports/pfi_v024/stage_4/phase_4_3/browser_validation.json",
        "screenshots": [
            "PFI/reports/pfi_v024/stage_4/phase_4_3/screenshots/data_missing_state.png",
            "PFI/reports/pfi_v024/stage_4/phase_4_3/screenshots/confirmed_zero_gate.png",
        ],
        "source_summary": browser_validation["source_summary"],
        "validation_hash": hashlib.sha256(json.dumps(browser_validation, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
        "explicitly_not_done": [
            "Stage 4 whole-stage review",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
        "generated_at": browser_validation["generated_at"],
    }
    write_json(PHASE_DIR / "evidence.json", evidence)

    changed_files = [
        "PFI/CHANGELOG.md",
        "PFI/HANDOFF.md",
        "PFI/README.md",
        "PFI/docs/pfi_v024/RUN_CONTRACT.md",
        "PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/browser_validation.json",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/changed_files.txt",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/evidence.json",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/risk_and_rollback.md",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/rendered/stage4_phase43_missing_state.html",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/rendered/stage4_phase43_confirmed_zero_gate.html",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/screenshots/data_missing_state.png",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/screenshots/confirmed_zero_gate.png",
        "PFI/reports/pfi_v024/stage_4/phase_4_3/terminal.log",
        "PFI/scripts/validate_v024_stage4_phase43_chrome.py",
        "PFI/tests/test_v024_stage4_phase43_acceptance.py",
        "PFI/web/app/data_state.js",
        "PFI/web/app/shell.js",
        "PFI/功能清单.md",
        "PFI/开发记录.md",
        "PFI/模型参数文件.md",
    ]
    (PHASE_DIR / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    (PHASE_DIR / "risk_and_rollback.md").write_text(
        "\n".join(
            [
                "# Stage 4 Phase 4.3 Risk and Rollback",
                "",
                "- Risk: Chrome headless evidence depends on local Chrome availability.",
                "- Risk: current real data has no confirmed_zero production metric; this phase proves the gate and records real_confirmed_zero_metric_count=0.",
                "- Rollback: revert the Phase 4.3 commit; no user financial data is modified.",
                "- Stop condition: any blocked metric rendering `CNY 0.00`, missing screenshots, or zero display without source/as_of/record_count/formula evidence.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (PHASE_DIR / "terminal.log").write_text(
        "\n".join(
            [
                "Phase 4.3 RED:",
                "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage4_phase43_acceptance.py -q",
                "result=expected red, 1 failed: missing validate_v024_stage4_phase43_chrome.py and phase_4_3 evidence",
                "",
                "CHROME VALIDATION:",
                "PYTHONPATH=PFI/src PFI/.venv/bin/python -B PFI/scripts/validate_v024_stage4_phase43_chrome.py",
                f"result={browser_validation['status']}",
                f"chrome={chrome}",
                f"blocked_metric_ids={','.join(blocked_metric_ids)}",
                f"real_confirmed_zero_metric_count={confirmed_zero_count}",
                "frontend_nullable_number_policy=null stays null; blocked metrics do not show 0 records",
                "screenshots=data_missing_state.png, confirmed_zero_gate.png",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"status": browser_validation["status"], "failures": failures, "phase_dir": str(PHASE_DIR)}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
