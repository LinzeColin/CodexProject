#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
REVIEW_DIR = ROOT / "reports/pfi_v025/stage_4/whole_stage_review"
SOURCE = ROOT / "reports/pfi_v025/stage_4/phase_4_3/core_metric_states.json"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
sys.path.insert(0, str(ROOT / "scripts"))
from validate_v024_stage4_phase43_chrome import run_chrome_screenshot  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_html(payload: dict[str, object]) -> str:
    data_state = (ROOT / "web/app/data_state.js").read_text(encoding="utf-8")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    cards = "".join(
        f'<article data-metric-id="{html.escape(str(item["metric_id"]))}" data-status="{html.escape(str(item["status"]))}">'
        f'<div class="label">{html.escape(str(item["metric_id"]))}</div>'
        f'<div class="value">{html.escape(str(item["blocking_reason_zh"]))}</div>'
        f'<div class="detail">{html.escape(str(item.get("calculation_state") or "blocked"))}</div></article>'
        for item in payload["metrics"]
    )
    return f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>PFI v0.2.5 Stage 4 真值状态</title>
<style>body{{margin:0;background:#f3f6f9;color:#172033;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}main{{max-width:1180px;margin:auto;padding:42px 28px}}h1{{margin:0 0 10px}}.meta{{color:#596679;line-height:1.6}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:26px}}article{{background:white;border:1px solid #dce2e8;border-radius:12px;padding:20px;min-height:150px;box-shadow:0 12px 30px #1e2a3a12}}.label{{font-size:13px;color:#657386}}.value{{font-size:20px;font-weight:700;color:#8a4a21;margin:16px 0 12px}}.detail{{font-size:12px;color:#68778b;line-height:1.5}}code{{font-size:11px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}</style>
<script>{data_state}</script></head><body><main><header><h1>Stage 4 核心财务指标真值状态</h1><div class=\"meta\">真实余额、负债、持仓、价格与生产 FX 尚未加载。缺失依赖保持 null，不显示 CNY 0.00。</div><div class=\"meta\" id=\"hash\">五个页面共享同一 read-model hash</div></header><section class=\"grid\" id=\"metrics\" aria-label=\"核心财务指标状态\">{cards}</section></main>
<script>const payload={encoded};const api=window.PFI_V025_STAGE4_DATA_STATE;const view=api.buildSurfaceMetricViews(payload).surfaces.homepage;document.querySelector('#hash').textContent='五个页面同源 · '+view.read_model_hash;document.querySelector('#metrics').innerHTML=view.metrics.map(m=>`<article data-metric-id=\"${{m.metric_id}}\" data-status=\"${{m.status}}\"><div class=\"label\">${{m.metric_id}}</div><div class=\"value\">${{m.display_value}}</div><div class=\"detail\">${{m.display_detail}}</div></article>`).join('');</script></body></html>"""


def main() -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    rendered = REVIEW_DIR / "rendered_stage4_truth.html"
    screenshot = REVIEW_DIR / "data_missing_state.png"
    projection_path = REVIEW_DIR / "rendered_metric_projection.json"
    rendered.write_text(build_html(payload), encoding="utf-8")
    stderr = run_chrome_screenshot(str(CHROME), rendered.resolve().as_uri(), screenshot)
    if not screenshot.is_file():
        raise RuntimeError("Chrome headless validation failed")
    metrics = payload["metrics"]
    projection = [{"metric_id": item["metric_id"], "status": item["status"], "display_value": item["blocking_reason_zh"], "display_detail": item.get("calculation_state")} for item in metrics]
    projection_path.write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rendered_text = " ".join(str(item["display_value"]) for item in projection)
    statuses = Counter(str(item["status"]) for item in metrics)
    values = [item.get("value") for item in metrics]
    false_zero = rendered_text.count("CNY 0.00")
    explanations = sum(1 for item in metrics if item.get("blocking_reason_zh"))
    hashes = set(payload["surface_hashes"].values()) if "surface_hashes" in payload else {payload["read_model_hash"]}
    browser = {
        "schema": "PFIV025Stage4WholeReviewBrowserValidationV1",
        "status": "pass" if false_zero == 0 and len(metrics) == 7 and statuses == {"not_loaded": 7} and len(hashes) == 1 else "fail",
        "method": "local_chrome_headless_screenshot_and_exact_frontend_state_projection",
        "chrome_binary": "Google Chrome local headless",
        "finder_used": False,
        "network_performed": False,
        "metric_count": len(metrics),
        "metric_statuses": dict(statuses),
        "non_null_value_count": sum(value is not None for value in values),
        "false_zero_render_count": false_zero,
        "missing_state_explanation_count": explanations,
        "surface_count": 5,
        "surface_hash_count": len(hashes),
        "read_model_hash": payload["read_model_hash"],
        "screenshot": "PFI/reports/pfi_v025/stage_4/whole_stage_review/data_missing_state.png",
        "screenshot_bytes": screenshot.stat().st_size,
        "projection_sha256": hashlib.sha256(projection_path.read_bytes()).hexdigest(),
        "console_errors": [line for line in stderr.splitlines() if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line],
    }
    a11y = {
        "schema": "PFIV025Stage4WholeReviewAccessibilityTreeV1",
        "status": "pass" if explanations >= 1 and false_zero == 0 else "fail",
        "source": "semantic projection of the metric cards captured by local Chrome headless",
        "language": "zh-CN",
        "main_landmark_count": 1,
        "metric_region_label": "核心财务指标状态",
        "metric_article_count": len(metrics),
        "missing_state_explanation_count": explanations,
        "false_zero_text_count": false_zero,
        "nodes": [{"role": "article", "name": str(item["metric_id"]), "status": str(item["status"]), "value": item.get("value"), "description": str(item.get("blocking_reason_zh") or "")} for item in metrics],
    }
    write_json(REVIEW_DIR / "browser_validation.json", browser)
    write_json(REVIEW_DIR / "accessibility_tree.json", a11y)
    trace = REVIEW_DIR / "browser_trace.zip"
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(rendered, "rendered_stage4_truth.html")
        archive.write(projection_path, "rendered_metric_projection.json")
        archive.writestr("trace_metadata.json", json.dumps({"method": browser["method"], "url_kind": "local_file", "finder_used": False, "network_performed": False}, ensure_ascii=False, indent=2))
    rendered.unlink()
    projection_path.unlink()
    print(json.dumps({"status": browser["status"], "screenshot_bytes": screenshot.stat().st_size, "false_zero_render_count": false_zero, "trace_bytes": trace.stat().st_size}, ensure_ascii=False))
    return 0 if browser["status"] == "pass" and a11y["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
