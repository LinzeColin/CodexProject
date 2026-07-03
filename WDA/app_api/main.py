from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from .core import (
    DEFAULT_DATA_CORE,
    DEFAULT_RUNTIME_ROOT,
    DEFAULT_SOURCE_WORKSPACE,
    build_dashboard_payload,
    build_status,
    contact_detail,
    dashboard_html,
    initialize_runtime,
    list_update_runs,
    load_report,
    report_index,
    run_update,
    top_contacts,
)


def env_path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default))).expanduser()


def paths() -> tuple[Path, Path, Path]:
    return (
        env_path("WDA_R3_RUNTIME_ROOT", DEFAULT_RUNTIME_ROOT),
        env_path("WDA_R3_DATA_CORE", DEFAULT_DATA_CORE),
        env_path("WDA_R3_SOURCE_WORKSPACE", DEFAULT_SOURCE_WORKSPACE),
    )


app = FastAPI(title="WDA v0.2-R3 Local API", version="0.2-r3")
_update_lock = threading.Lock()


@app.on_event("startup")
def startup() -> None:
    runtime_root, data_core, source_workspace = paths()
    initialize_runtime(runtime_root, data_core, source_workspace)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    runtime_root, data_core, source_workspace = paths()
    status = build_status(data_core, source_workspace, runtime_root)
    return dashboard_html(build_dashboard_payload(status))


@app.get("/system", response_class=HTMLResponse)
def system() -> str:
    runtime_root, data_core, source_workspace = paths()
    status = build_status(data_core, source_workspace, runtime_root)
    rows = "\n".join(
        f"<tr><th>{key}</th><td>{value}</td></tr>"
        for key, value in status.items()
        if key not in {"warnings", "errors"}
    )
    alerts = "".join(f"<li>{item}</li>" for item in [*status["warnings"], *status["errors"]])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>WDA 系统状态</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:24px;line-height:1.6;color:oklch(0.22 0.025 40)}}table{{border-collapse:collapse}}th,td{{border:1px solid oklch(0.88 0.012 40);padding:8px 10px;text-align:left}}th{{background:oklch(0.965 0.006 40)}}</style>
</head><body><h1>WDA 系统状态</h1><p><a href="/">返回今日工作台</a></p><table>{rows}</table><h2>告警</h2><ul>{alerts or "<li>无</li>"}</ul></body></html>"""


@app.get("/reports/{report_id}", response_class=HTMLResponse)
def report_page(report_id: str) -> str:
    try:
        report = load_report(report_id, paths()[2])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    content = report["content"] or "该报告源文件尚未生成。"
    escaped = (
        content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{report['title']}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:24px;line-height:1.72;max-width:980px}}pre{{white-space:pre-wrap;font:inherit}}a{{color:#8b3f1d}}</style>
</head><body><p><a href="/">返回今日工作台</a></p><h1>{report['title']}</h1><p>{report['summary']}</p><pre>{escaped}</pre></body></html>"""


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return {"ok": True, "service": "WDA v0.2-R3"}


@app.get("/api/status")
def api_status() -> dict[str, Any]:
    runtime_root, data_core, source_workspace = paths()
    return build_status(data_core, source_workspace, runtime_root)


@app.get("/api/dashboard")
def api_dashboard() -> dict[str, Any]:
    runtime_root, data_core, source_workspace = paths()
    return build_dashboard_payload(build_status(data_core, source_workspace, runtime_root))


@app.post("/api/update/run")
def api_update_run(background_tasks: BackgroundTasks) -> dict[str, Any]:
    runtime_root, data_core, source_workspace = paths()
    if _update_lock.locked():
        return {"status": "already_running"}

    def locked_update() -> None:
        with _update_lock:
            run_update(runtime_root, data_core, source_workspace)

    background_tasks.add_task(locked_update)
    return {"status": "queued"}


@app.get("/api/update/runs")
def api_update_runs() -> list[dict[str, Any]]:
    return list_update_runs(paths()[0])


@app.get("/api/reports")
def api_reports() -> dict[str, Any]:
    return report_index(paths()[2])


@app.get("/api/reports/{report_id}")
def api_report(report_id: str) -> dict[str, Any]:
    try:
        return load_report(report_id, paths()[2])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/actions")
def api_actions() -> dict[str, str]:
    return {"report_id": "actions", "href": "/reports/actions"}


@app.get("/api/contacts")
def api_contacts() -> list[dict[str, Any]]:
    return top_contacts(paths()[1])


@app.get("/api/contacts/{contact_id}")
def api_contact(contact_id: str) -> dict[str, Any]:
    try:
        return contact_detail(contact_id, paths()[1])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/evidence/{evidence_id}", response_class=PlainTextResponse)
def api_evidence(evidence_id: str) -> str:
    if evidence_id != "index":
        raise HTTPException(status_code=404, detail="Only evidence index is exposed in R3.")
    return load_report("evidence", paths()[2])["content"]
