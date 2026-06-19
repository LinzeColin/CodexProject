from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from .artifacts import sanitize_public_payload
from .my_bets import load_snapshot, normalize_report_date, snapshot_filename
from .preflight import capture_diagnostic_filename, public_capture_diagnostic, validate_private_position_snapshot


DEFAULT_PROFILE_NAME = "tab_chrome_profile"


def private_dir_for_output(output_dir: Path) -> Path:
    override = os.environ.get("TAB_FIFA_PRIVATE_DIR")
    if override:
        return Path(override)
    return Path(output_dir).parent / "work" / "private" / "tab_fifa"


def default_chrome_profile_dir(private_dir: Path) -> Path:
    return Path(private_dir) / DEFAULT_PROFILE_NAME


def build_private_position_bootstrap_status(
    private_dir: Path,
    report_date: str,
    chrome_profile_dir: Path | None = None,
) -> Dict[str, Any]:
    private_dir = Path(private_dir)
    report_date = normalize_report_date(report_date)
    profile_dir = Path(chrome_profile_dir) if chrome_profile_dir else default_chrome_profile_dir(private_dir)
    raw_name = f"tab_my_bets_raw_{report_date}.txt"
    snapshot_name = snapshot_filename(report_date)
    diagnostic_name = capture_diagnostic_filename(report_date)
    raw_path = private_dir / raw_name
    snapshot_path = private_dir / snapshot_name
    diagnostic_path = private_dir / diagnostic_name
    diagnostic = load_json(diagnostic_path)
    snapshot_issues = []
    if snapshot_path.exists():
        snapshot_issues = validate_private_position_snapshot(load_snapshot(snapshot_path), report_date)
    snapshot_ready = snapshot_path.exists() and not snapshot_issues
    raw_ready = raw_path.exists() and raw_path.stat().st_size > 0
    public_diagnostic = public_capture_diagnostic(diagnostic)
    status = bootstrap_status(snapshot_ready, raw_ready, public_diagnostic, bool(diagnostic))
    preflight = private_position_preflight(
        status=status,
        report_date=report_date,
        profile_exists=profile_dir.exists(),
        private_storage_exists=private_dir.exists(),
        raw_ready=raw_ready,
        snapshot_ready=snapshot_ready,
        diagnostics_exists=diagnostic_path.exists(),
        public_diagnostic=public_diagnostic,
    )
    payload = {
        "schema_version": 1,
        "report_date": report_date,
        "status": status,
        "ready": snapshot_ready,
        "profile": {
            "profile_name": profile_dir.name,
            "default_profile": profile_dir.name == DEFAULT_PROFILE_NAME,
            "exists": profile_dir.exists(),
            "private_path_required": True,
        },
        "files": {
            "raw_text_ref": f"private_raw_text_{report_date}.txt",
            "raw_text_exists": raw_path.exists(),
            "snapshot_ref": f"private_position_snapshot_{report_date}.json",
            "snapshot_exists": snapshot_path.exists(),
            "diagnostics_ref": f"private_capture_diagnostic_{report_date}.json",
            "diagnostics_exists": diagnostic_path.exists(),
        },
        "snapshot_validation": {
            "valid": snapshot_ready,
            "issue_count": len(snapshot_issues),
            "issues": snapshot_issues[:8],
        },
        "capture_diagnostic": public_diagnostic or {},
        "preflight": preflight,
        "next_action": bootstrap_next_action(status, report_date, raw_name),
    }
    return sanitize_public_payload(payload)


def bootstrap_status(snapshot_ready: bool, raw_ready: bool, diagnostic: Dict | None, has_diagnostic: bool) -> str:
    if snapshot_ready:
        return "snapshot_ready"
    if raw_ready:
        return "raw_ready_import_needed"
    auth_status = str((diagnostic or {}).get("auth_status") or "")
    if auth_status in {"access_denied", "login_required"}:
        return "profile_login_required"
    if (diagnostic or {}).get("ready") is True:
        return "capture_ready_raw_missing"
    if has_diagnostic:
        return "capture_diagnostic_not_ready"
    return "capture_not_run"


def bootstrap_next_action(status: str, report_date: str, raw_name: str) -> str:
    if status == "snapshot_ready":
        return "私有持仓快照已就绪；可以重跑日报并通过 technical preflight 后发布正式报告。"
    if status == "raw_ready_import_needed":
        return (
            "已读取私有持仓 raw text；下一步运行 "
            f"`python3 import_my_bets_snapshot.py --source <private raw text for {report_date}> --report-date {report_date}`。"
        )
    if status == "capture_ready_raw_missing":
        return "capture 诊断显示 ready 但 raw text 缺失；重新运行只读 My Bets capture 并导入快照。"
    return (
        "建立或刷新 TAB 专用已登录 profile："
        f"`TAB_FIFA_HEADLESS=0 node scripts/capture_tab_my_bets_readonly.mjs --report-date {report_date} --wait-for-login-ms 600000`。"
    )


def private_position_preflight(
    *,
    status: str,
    report_date: str,
    profile_exists: bool,
    private_storage_exists: bool,
    raw_ready: bool,
    snapshot_ready: bool,
    diagnostics_exists: bool,
    public_diagnostic: Dict | None,
) -> Dict[str, Any]:
    login_window_required = status in {"capture_not_run", "profile_login_required", "capture_diagnostic_not_ready", "capture_ready_raw_missing"}
    auth_status = str((public_diagnostic or {}).get("auth_status") or "not_checked")
    return {
        "schema_version": 1,
        "status": status,
        "report_date": report_date,
        "ready": snapshot_ready,
        "blocking_reason": private_position_blocking_reason(status, auth_status),
        "next_safe_action": private_position_next_safe_action(status),
        "can_start_bootstrap": not snapshot_ready,
        "can_import_snapshot": status == "raw_ready_import_needed",
        "can_rerun_daily_gate": snapshot_ready,
        "login_window_required": login_window_required,
        "manual_step_required": login_window_required,
        "wait_for_login_seconds": 600,
        "capture_mode": "headed_read_only_authorized_profile",
        "credential_policy": "不读取、不保存、不填写账号密码或OTP；只复用用户授权的本机 profile。",
        "automation_boundary": "只读抓取、导入私有快照、重跑报告门禁；禁止赔率点击、下注单修改和自动下注。",
        "privacy_boundary": "公开产物只展示状态、下一步和文件存在性；余额、逐笔下注、账号信息和私有路径不进入公开报告。",
        "private_storage_ready": private_storage_exists,
        "profile_ready": profile_exists,
        "raw_text_ready": raw_ready,
        "snapshot_ready": snapshot_ready,
        "diagnostics_ready": diagnostics_exists,
        "diagnostic_auth_status": auth_status,
        "diagnostic_reason": str((public_diagnostic or {}).get("reason") or ""),
        "step_statuses": [
            {"step": "private_storage", "ready": private_storage_exists, "label": "本机私有存储"},
            {"step": "authorized_profile", "ready": profile_exists and status != "profile_login_required", "label": "TAB 授权 profile"},
            {"step": "readonly_capture", "ready": raw_ready, "label": "只读持仓文本"},
            {"step": "snapshot_import", "ready": snapshot_ready, "label": "私有持仓快照"},
            {"step": "daily_gate", "ready": snapshot_ready, "label": "日报门禁可用"},
        ],
    }


def private_position_blocking_reason(status: str, auth_status: str) -> str:
    if status == "snapshot_ready":
        return "私有持仓快照已通过校验。"
    if status == "raw_ready_import_needed":
        return "只读文本已存在，但尚未导入当日私有持仓快照。"
    if status == "profile_login_required":
        return f"TAB 授权状态不可用（{auth_status or 'unknown'}），需要用户在本机窗口完成授权。"
    if status == "capture_ready_raw_missing":
        return "只读诊断显示页面可读，但当日文本未落盘，需要重新抓取。"
    if status == "capture_diagnostic_not_ready":
        return "已有诊断但读取未就绪，需要重新打开只读授权窗口。"
    return "尚未运行只读持仓读取，需要启动本地授权 profile 流程。"


def private_position_next_safe_action(status: str) -> str:
    if status == "snapshot_ready":
        return "重跑日报门禁；若公开盘口 raw 也 ready，可更新正式研究报告。"
    if status == "raw_ready_import_needed":
        return "导入当日私有快照，然后重跑日报门禁。"
    if status == "profile_login_required":
        return "点击“启动只读持仓读取”，在打开的 TAB 窗口完成授权，系统只读取持仓页文本。"
    if status == "capture_ready_raw_missing":
        return "重新启动只读持仓读取，确认当日 raw text 写入私有目录。"
    return "点击“启动只读持仓读取”，完成后系统会更新 preflight 状态。"


def report_date_from_preflight_or_latest(preflight: Dict[str, Any], latest_commit: Dict[str, Any]) -> str:
    value = str(preflight.get("report_date") or "")
    if is_report_date(value):
        return value
    for check in preflight.get("checks") or []:
        for detail in check.get("details") or []:
            diagnostic = detail.get("capture_diagnostic") if isinstance(detail, dict) else None
            value = str((diagnostic or {}).get("report_date") or "")
            if is_report_date(value):
                return value
    value = str(latest_commit.get("report_date") or "")
    return value if is_report_date(value) else ""


def is_report_date(value: str) -> bool:
    return len(value) == 8 and value.isdigit()


def load_json(path: Path) -> Dict[str, Any]:
    import json

    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
