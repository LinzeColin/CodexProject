from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import DATA_DIR, PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.storage import atomic_write_json, atomic_write_text


DATA_TRUST_STATUSES = {
    "RAW_IMPORTED",
    "PARSED_CANDIDATE",
    "NEEDS_REVIEW",
    "USER_CONFIRMED",
    "RECONCILED",
    "ARCHIVED",
    "REJECTED",
}


@dataclass(frozen=True)
class PFIOSDataTrustRecord:
    record_id: str
    source_group: str
    source_path: str
    source_type: str
    trust_status: str
    evidence_classification: str
    decision_grade: str
    user_confirmation_required: bool
    issue: str
    next_action: str
    size_bytes: int
    modified_at: str
    content_hash: str

    def to_row(self) -> dict[str, object]:
        return asdict(self)


def build_data_trust_audit(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    max_independent_runs: int = 30,
) -> dict[str, Any]:
    root = Path(project_root)
    reports = Path(report_root)
    generated_as_of = as_of or datetime.now().date().isoformat()
    records: list[PFIOSDataTrustRecord] = []
    records.extend(_project_records(root))
    records.extend(_data_provider_records(root))
    records.extend(_strategy_records(root))
    records.extend(_holding_records(root))
    records.extend(_research_bus_records(root))
    records.extend(_validation_queue_records(root))
    records.extend(_independent_validation_records(root, max_runs=max_independent_runs))
    records.extend(_cache_records(root))
    records.extend(_raw_processed_records(root))
    records.extend(_experiment_records(root))
    records.extend(_report_catalog_records(root, reports))

    status_counts = Counter(record.trust_status for record in records)
    decision_counts = Counter(record.decision_grade for record in records)
    evidence_counts = Counter(record.evidence_classification for record in records)
    review_count = sum(1 for record in records if record.trust_status == "NEEDS_REVIEW")
    rejected_count = sum(1 for record in records if record.trust_status == "REJECTED")
    audit_status = "Blocked" if rejected_count else "Review" if review_count else "Pass"
    return {
        "schema": "PFIOSDataTrustAuditV1",
        "system": "PFIOS",
        "as_of": generated_as_of,
        "run_id": _stable_id("quantLabDataTrust", generated_as_of, str(root.resolve())),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_status": audit_status,
        "record_count": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "review_count": review_count,
        "rejected_count": rejected_count,
        "assumptions": [
            "This audit is read-only and only classifies local PFIOS files.",
            "It does not refresh data providers, open Streamlit, start Moomoo OpenD, or mutate holdings.",
            "Video/OCR/candidate files remain candidate evidence until confirmed by the user or reconciled against official exports.",
            "Actionable means usable inside the research evidence chain; it is not live-trading approval.",
        ],
        "records": [record.to_row() for record in records],
    }


def write_data_trust_audit(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    audit = build_data_trust_audit(as_of=as_of, project_root=root, report_root=report_root)
    target = Path(output_dir) if output_dir else root / "data" / "systemAudit"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(audit["as_of"]))
    stem = f"PFIOSDataTrustAudit_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    _write_records_csv(csv_path, audit["records"])
    markdown = _audit_markdown(audit)
    atomic_write_text(markdown_path, markdown)
    _write_simple_pdf(pdf_path, audit)
    audit["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
    }
    atomic_write_json(json_path, audit)
    return audit


def _project_records(root: Path) -> list[PFIOSDataTrustRecord]:
    records = [
        _required_path_record(root / "AGENTS.md", root, "Project Control", "policy", "项目规则文件存在。", "继续按项目规则执行每轮单目标升级。"),
        _required_path_record(root / "HANDOFF.md", root, "Project Control", "handoff", "交接文件存在。", "每轮开始先核对 HANDOFF 与当前真实文件是否一致。"),
        _required_path_record(root / "README.md", root, "Project Control", "documentation", "README 存在。", "保持 README 与新增系统层同步。"),
        _required_path_record(root / "pyproject.toml", root, "Project Control", "build_config", "Python 项目配置存在。", "保持依赖、测试路径和包配置可复现。"),
    ]
    for path, source_type, next_action in [
        (root / "PLANS.md", "delivery_plan", "如进入跨系统交付阶段，补充当前执行计划和验收顺序。"),
        (root / "CODEX_TASK_PACK.md", "task_pack", "如需要交给其它 agent 执行，补充低上下文任务包。"),
        (root / "CODEX_PROMPTS.md", "prompt_pack", "如需要复用提示词，补充提示词与输入输出边界。"),
        (root / "docs" / "DataSources.md", "data_source_documentation", "继续维护数据源真实性、权限和失效边界。"),
        (root / "docs" / "RiskAndLimits.md", "risk_documentation", "继续维护研究边界、非实盘边界和风险口径。"),
        (root / "docs" / "ResearchBus.md", "interop_documentation", "继续维护跨系统互通 schema 与审计入口。"),
    ]:
        records.append(_advisory_path_record(path, root, "Project Control", source_type, next_action))
    return records


def _data_provider_records(root: Path) -> list[PFIOSDataTrustRecord]:
    provider_dir = root / "src" / "pfi_os" / "data" / "providers"
    provider_files = [
        ("base.py", "Provider 抽象基类存在。", "所有数据源必须通过统一接口返回可验证行情。"),
        ("factory.py", "Provider 工厂存在。", "数据源选择和默认优先级必须通过工厂显式管理。"),
        ("moomoo_provider.py", "Moomoo Provider 存在。", "真实行情优先检查 OpenD、权限、市场、周期和错误状态。"),
        ("yahoo_finance.py", "Yahoo Finance Provider 存在。", "作为公开备选源时必须标记延迟和复权口径。"),
        ("akshare_provider.py", "AKShare Provider 存在。", "A 股公开源需要记录调用时间、复权口径和失败对象。"),
        ("tushare_provider.py", "TuShare Provider 存在。", "需要 token 时只能读取本地环境变量，禁止写入报告。"),
        ("alpha_vantage.py", "Alpha Vantage Provider 存在。", "需要 key 和频率限制时必须进入数据源状态记录。"),
        ("polygon_provider.py", "Polygon Provider 存在。", "需要 key 和美股权限时必须进入数据源状态记录。"),
        ("csv_provider.py", "CSV Provider 存在。", "用户导入文件只能作为来源明确的候选或确认数据。"),
        ("sample_provider.py", "Sample Provider 存在。", "Sample 仅用于演示和测试，不得作为真实研究证据。"),
    ]
    records = [
        _required_path_record(provider_dir / filename, root, "Data Providers", "python", issue, next_action)
        for filename, issue, next_action in provider_files
    ]
    records.append(_required_path_record(root / "src" / "pfi_os" / "data" / "quality.py", root, "Data Providers", "python", "数据质量检查模块存在。", "回测结论前必须结合缺口、重复值、异常价格和覆盖率检查。"))
    records.append(_required_path_record(root / "src" / "pfi_os" / "data" / "validation.py", root, "Data Providers", "python", "数据校验模块存在。", "真实研究前必须运行跨源校验或记录缺失原因。"))
    records.append(_required_path_record(root / "docs" / "DataSources.md", root, "Data Providers", "documentation", "数据源文档存在。", "保持 Moomoo、Yahoo、AKShare、TuShare、Polygon、Alpha Vantage 的权限和延迟说明。"))
    return records


def _strategy_records(root: Path) -> list[PFIOSDataTrustRecord]:
    strategy_root = root / "src" / "pfi_os" / "strategies"
    records: list[PFIOSDataTrustRecord] = [
        _required_path_record(strategy_root / "base.py", root, "Strategy Library", "python", "策略基类存在。", "所有策略必须输出非负持仓权重并保留 metadata。"),
        _required_path_record(strategy_root / "profiles.py", root, "Strategy Library", "python", "策略画像模块存在。", "策略收益来源、失效环境和研究假设必须进入画像。"),
        _required_path_record(strategy_root / "templates.py", root, "Strategy Library", "python", "策略模板模块存在。", "新增策略必须走模板、质量检查、烟雾测试和确认流程。"),
    ]
    builtin_paths = [
        strategy_root / "behavioral" / "alipay.py",
        strategy_root / "trend" / "ma_crossover.py",
        strategy_root / "trend" / "breakout.py",
        strategy_root / "mean_reversion" / "rsi_reversion.py",
        strategy_root / "mean_reversion" / "bollinger_reversion.py",
        strategy_root / "momentum" / "momentum_rotation.py",
    ]
    for path in builtin_paths:
        records.append(_required_path_record(path, root, "Built-in Strategies", "python", f"内置策略文件存在：{path.stem}。", "内置策略可编辑但必须保留版本、参数、假设和确认记录。"))

    approvals_dir = root / "data" / "approvals"
    approval_files = sorted(approvals_dir.glob("*.json")) if approvals_dir.exists() else []
    if not approval_files:
        records.append(_path_record(approvals_dir, root, "Strategy Approvals", "directory", "NEEDS_REVIEW", "FACT", "Watch", "策略确认目录缺失或暂无确认记录。", "策略变更用于正式回测前应生成确认记录。", user_confirmation_required=True))
    for path in approval_files[:50]:
        records.append(_json_record(path, root, "Strategy Approvals", expected_type=dict, status_if_valid="USER_CONFIRMED", issue_if_valid="策略确认记录可读。", next_action="确认记录只能证明变更已确认，不证明策略有效。"))
    for path in approval_files[50:]:
        records.append(_path_record(path, root, "Strategy Approvals", "json", "ARCHIVED", "FACT", "Observe", "较早策略确认记录已归档到审计索引。", "需要复盘时再按策略编号精查。"))
    return records


def _holding_records(root: Path) -> list[PFIOSDataTrustRecord]:
    holdings_dir = root / "data" / "holdings"
    book_json = holdings_dir / "HoldingsBook.json"
    book_csv = holdings_dir / "HoldingsBook.csv"
    history = holdings_dir / "HoldingsImportHistory.json"
    records: list[PFIOSDataTrustRecord] = []
    paired = book_json.exists() and book_csv.exists() and book_json.stat().st_size > 0 and book_csv.stat().st_size > 0
    records.append(_json_record(book_json, root, "Holdings", expected_type=dict, status_if_valid="RECONCILED" if paired else "NEEDS_REVIEW", issue_if_valid="持仓簿 JSON 与 CSV 已成对存在。" if paired else "持仓簿缺少 JSON/CSV 成对文件。", next_action="继续用持仓质量检查和用户确认来复核来源。"))
    records.append(_csv_record(book_csv, root, "Holdings", status_if_valid="RECONCILED" if paired else "NEEDS_REVIEW", issue_if_valid="持仓簿 CSV 与 JSON 已成对存在。" if paired else "持仓簿 CSV 缺少对应 JSON 或为空。", next_action="检查持仓总市值、权重和更新时间。"))
    history_payload = _load_json(history)
    if history_payload.exists and history_payload.valid and isinstance(history_payload.payload, dict) and isinstance(history_payload.payload.get("history"), list):
        records.append(_path_record(history, root, "Holdings", "json", "RECONCILED", "FACT", "Actionable", "持仓同步历史为当前 schema。", "继续保留同步历史，异常导入进入复核队列。"))
    elif history_payload.exists and history_payload.valid:
        records.append(_path_record(history, root, "Holdings", "json", "NEEDS_REVIEW", "FACT", "Watch", "持仓同步历史 JSON 可读但 schema 不符合 PFIOSHoldingsImportHistoryV1。", "保留文件，人工确认是否需要迁移旧历史结构。", user_confirmation_required=True))
    else:
        records.append(_missing_or_rejected_record(history, root, "Holdings", "持仓同步历史缺失或 JSON 损坏。", "先修复 HoldingsImportHistory.json，再用于同步审计。"))
    imports_dir = holdings_dir / "imports"
    for path in sorted(imports_dir.glob("*.csv")) if imports_dir.exists() else []:
        name = path.name.lower()
        if "confirmed" in name:
            records.append(_csv_record(path, root, "Holdings Imports", status_if_valid="USER_CONFIRMED", issue_if_valid="用户或行研系统确认的持仓候选。", next_action="写入正式持仓前仍需确认代码、市场、金额和更新时间。"))
        elif "trade" in name or "position" in name or "candidate" in name:
            records.append(_csv_record(path, root, "Holdings Imports", status_if_valid="PARSED_CANDIDATE", issue_if_valid="视频/OCR/候选导入文件，只能作为候选证据。", next_action="需要用户确认或官方导出文件交叉验证。", user_confirmation_required=True))
        else:
            records.append(_csv_record(path, root, "Holdings Imports", status_if_valid="RAW_IMPORTED", issue_if_valid="持仓导入辅助文件已读取。", next_action="确认是否需要纳入正式持仓。"))
    for lock_path in sorted(holdings_dir.glob("*.lock")):
        lock_status, lock_issue = _lock_file_status(lock_path)
        records.append(_path_record(lock_path, root, "Holdings", "lock", lock_status, "OBSERVATION", _decision_for_status(lock_status), lock_issue, "确认没有运行中的持仓同步后再判断是否清理。", user_confirmation_required=lock_status == "NEEDS_REVIEW"))
    return records


def _research_bus_records(root: Path) -> list[PFIOSDataTrustRecord]:
    bus_dir = root / "data" / "researchBus"
    records = [
        _json_record(bus_dir / "ResearchBusInteropAudit.json", root, "ResearchBus", expected_type=dict, status_if_valid=_research_bus_status(bus_dir / "ResearchBusInteropAudit.json"), issue_if_valid="ResearchBus 互通审计文件可读。", next_action="若状态不是 Pass，先处理互通审计失败项。"),
        _json_record(bus_dir / "ResearchBusSnapshot.json", root, "ResearchBus", expected_type=dict, status_if_valid="RECONCILED", issue_if_valid="ResearchBus 快照可读。", next_action="继续用快照暴露跨系统状态，不复制敏感原始数据。"),
    ]
    sqlite_path = bus_dir / "ResearchBus.sqlite"
    status = "RECONCILED" if sqlite_path.exists() and sqlite_path.stat().st_size > 0 else "NEEDS_REVIEW"
    records.append(_path_record(sqlite_path, root, "ResearchBus", "sqlite", status, "FACT", "Actionable" if status == "RECONCILED" else "Watch", "ResearchBus SQLite 主库存在。" if status == "RECONCILED" else "ResearchBus SQLite 主库缺失或为空。", "运行互通审计确认 schema 和表计数。"))
    for path in sorted(bus_dir.glob("*SourceLog_*.json")):
        records.append(_json_record(path, root, "Research Source Logs", expected_type=dict, status_if_valid="RAW_IMPORTED", issue_if_valid="公开研究或盘感来源日志可读。", next_action="用于后续 Evidence Classification，不直接提升为结论。"))
    return records


def _validation_queue_records(root: Path) -> list[PFIOSDataTrustRecord]:
    queue_dir = root / "data" / "validationQueue"
    tasks = queue_dir / "ValidationTasks.json"
    payload = _load_json(tasks)
    if payload.exists and payload.valid and isinstance(payload.payload, list) and payload.payload:
        status = "PARSED_CANDIDATE"
        issue = f"验证任务队列可读，任务数 {len(payload.payload)}。"
    elif payload.exists and payload.valid:
        status = "NEEDS_REVIEW"
        issue = "验证任务队列为空或格式不是非空 list。"
    else:
        status = "REJECTED" if payload.exists else "NEEDS_REVIEW"
        issue = "验证任务队列缺失或 JSON 损坏。"
    records = [_path_record(tasks, root, "Validation Queue", "json", status, "FACT", _decision_for_status(status), issue, "不要把待验证任务当成已验证结论；先跑回测或独立验证。", user_confirmation_required=status == "NEEDS_REVIEW")]
    for lock_path in sorted(queue_dir.glob("*.lock")):
        lock_status, lock_issue = _lock_file_status(lock_path)
        records.append(_path_record(lock_path, root, "Validation Queue", "lock", lock_status, "OBSERVATION", _decision_for_status(lock_status), lock_issue, "确认没有运行中的同步或写入流程后再处理。", user_confirmation_required=lock_status == "NEEDS_REVIEW"))
    return records


def _independent_validation_records(root: Path, *, max_runs: int) -> list[PFIOSDataTrustRecord]:
    run_dir = root / "data" / "independentValidation"
    paths = sorted(run_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True) if run_dir.exists() else []
    records: list[PFIOSDataTrustRecord] = []
    if not paths:
        return [_path_record(run_dir, root, "Independent Validation", "directory", "NEEDS_REVIEW", "FACT", "Watch", "独立验证目录缺失或没有运行记录。", "生成或同步独立验证运行记录后再用于证据链。")]
    for index, path in enumerate(paths[:max_runs]):
        payload = _load_json(path)
        if not payload.valid:
            records.append(_path_record(path, root, "Independent Validation", "json", "REJECTED", "FACT", "Reject", "独立验证运行 JSON 损坏。", "修复或隔离该运行记录。"))
            continue
        run_status = str(payload.payload.get("status", "")) if isinstance(payload.payload, dict) else ""
        mode = str(payload.payload.get("mode", "")) if isinstance(payload.payload, dict) else ""
        if run_status.lower() in {"failed", "error", "blocked"}:
            status = "REJECTED"
            issue = f"独立验证运行状态为 {run_status}。"
        elif run_status.lower() in {"planned"} or mode.lower() == "dry_run":
            status = "PARSED_CANDIDATE"
            issue = f"独立验证为 {run_status or mode}，只代表计划或候选验证。"
        elif run_status.lower() == "completed":
            status = "RECONCILED"
            issue = "独立验证运行完成，仍需结合数据源和假设审计。"
        else:
            status = "NEEDS_REVIEW"
            issue = f"独立验证运行状态不明确：{run_status or 'missing'}。"
        records.append(_path_record(path, root, "Independent Validation", "json", status, "FACT", _decision_for_status(status), issue, "保留 run_id、分片、假设和输出路径；不要把 dry_run 当作真实执行完成。"))
    for path in paths[max_runs:]:
        records.append(_path_record(path, root, "Independent Validation", "json", "ARCHIVED", "FACT", "Observe", "较早独立验证运行已归档到审计索引。", "需要复盘时再按 run_id 精查。"))
    return records


def _cache_records(root: Path) -> list[PFIOSDataTrustRecord]:
    cache_dir = root / "data" / "cache"
    records = []
    for path in sorted(cache_dir.glob("*")) if cache_dir.exists() else []:
        if not path.is_file() or path.name == ".gitkeep":
            continue
        if path.suffix.lower() == ".log":
            records.append(_path_record(path, root, "Runtime Cache", "log", "ARCHIVED", "OBSERVATION", "Observe", "运行日志，不应作为研究结论证据。", "只在排查启动/停止问题时查看；不要进入投资证据链。"))
        elif path.suffix.lower() == ".pid":
            pid_status, pid_issue = _pid_file_status(path)
            records.append(_path_record(path, root, "Runtime Cache", "pid", pid_status, "OBSERVATION", _decision_for_status(pid_status), pid_issue, "只在排查启动/停止问题时查看；不要进入投资证据链。", user_confirmation_required=pid_status == "NEEDS_REVIEW"))
    return records


def _raw_processed_records(root: Path) -> list[PFIOSDataTrustRecord]:
    records: list[PFIOSDataTrustRecord] = []
    for group, subdir, status in [("Raw Data", root / "data" / "raw", "RAW_IMPORTED"), ("Processed Data", root / "data" / "processed", "PARSED_CANDIDATE")]:
        paths = [path for path in subdir.rglob("*") if path.is_file() and path.name != ".gitkeep"] if subdir.exists() else []
        if not paths:
            records.append(_path_record(subdir, root, group, "directory", "ARCHIVED", "FACT", "Observe", f"{group} 目录暂无正式数据文件。", "这不是错误；真实数据会由数据源下载或导入流程写入。"))
        for path in paths[:100]:
            records.append(_path_record(path, root, group, path.suffix.lower().lstrip(".") or "file", status, "FACT", _decision_for_status(status), "本地行情或加工数据文件已索引。", "进入回测前仍需运行数据质量检查和多源校验。"))
    return records


def _experiment_records(root: Path) -> list[PFIOSDataTrustRecord]:
    experiment_root = root / "data" / "results" / "experiments"
    if not experiment_root.exists():
        return [_path_record(experiment_root, root, "Experiments", "directory", "NEEDS_REVIEW", "FACT", "Watch", "参数扫描和实验记录目录缺失。", "运行参数扫描或实验后应生成 summary.csv、runs.json 和稳定性验证文件。")]
    experiment_dirs = [path for path in sorted(experiment_root.iterdir()) if path.is_dir()]
    if not experiment_dirs:
        return [_path_record(experiment_root, root, "Experiments", "directory", "ARCHIVED", "FACT", "Observe", "参数扫描和实验目录暂无运行记录。", "这不是错误；生成实验后会进入审计索引。")]

    records: list[PFIOSDataTrustRecord] = []
    for experiment_dir in experiment_dirs[:40]:
        summary = experiment_dir / "summary.csv"
        runs = experiment_dir / "runs.json"
        has_summary = summary.exists() and summary.stat().st_size > 0
        has_runs = runs.exists() and runs.stat().st_size > 0
        if has_summary and has_runs:
            status = "RECONCILED"
            issue = "实验 summary.csv 与 runs.json 成对存在。"
            next_action = "继续检查样本外验证、walk-forward、成本压力测试和参数稳定性。"
        else:
            status = "NEEDS_REVIEW"
            issue = "实验缺少 summary.csv 或 runs.json。"
            next_action = "不要把不完整实验当成可用证据；先补齐实验元数据。"
        records.append(_path_record(experiment_dir, root, "Experiments", "directory", status, "FACT", _decision_for_status(status), issue, next_action, user_confirmation_required=status == "NEEDS_REVIEW"))
        records.append(_csv_record(summary, root, "Experiment Summary", status_if_valid=status, issue_if_valid="实验摘要 CSV 可读。", next_action=next_action))
        records.append(_json_record(runs, root, "Experiment Runs", expected_type=list, status_if_valid=status, issue_if_valid="实验 runs.json 可读。", next_action=next_action))
        for validation_file in ["stability.json", "train_test_validation.json", "walk_forward_validation.json"]:
            path = experiment_dir / validation_file
            if path.exists():
                records.append(_json_record(path, root, "Experiment Validation", expected_type=dict, status_if_valid="RECONCILED", issue_if_valid=f"{validation_file} 可读。", next_action="验证文件只是研究证据的一部分，仍需结合数据质量和风险门禁。"))
            else:
                records.append(_path_record(path, root, "Experiment Validation", "json", "NEEDS_REVIEW", "FACT", "Watch", f"实验缺少 {validation_file}。", "参数扫描结果进入研究结论前应补充稳定性、样本外或 walk-forward 验证。", user_confirmation_required=True))
    for experiment_dir in experiment_dirs[40:]:
        records.append(_path_record(experiment_dir, root, "Experiments", "directory", "ARCHIVED", "FACT", "Observe", "较早实验已归档到审计索引。", "需要复盘时再按实验名精查。"))
    return records


def _report_catalog_records(root: Path, report_root: Path) -> list[PFIOSDataTrustRecord]:
    if not report_root.exists():
        return [_path_record(report_root, root, "Report Catalog", "directory", "NEEDS_REVIEW", "FACT", "Watch", "报告目录不存在。", "运行回测或报告导出后应生成报告目录。")]
    report_files = [path for path in report_root.rglob("*") if path.is_file() and path.suffix.lower() in {".docx", ".json", ".csv", ".md", ".pdf"}]
    status = "RECONCILED" if report_files else "NEEDS_REVIEW"
    issue = f"报告目录可读，已索引 {len(report_files)} 个报告或元数据文件。" if report_files else "报告目录可读但没有报告或元数据文件。"
    return [_path_record(report_root, root, "Report Catalog", "directory", status, "FACT", _decision_for_status(status), issue, "报告结论必须同时引用数据质量、多源校验、成本假设和风险门禁。")]


def _json_record(path: Path, root: Path, group: str, *, expected_type: type | tuple[type, ...] | None, status_if_valid: str, issue_if_valid: str, next_action: str) -> PFIOSDataTrustRecord:
    payload = _load_json(path)
    if not payload.exists:
        return _path_record(path, root, group, "json", "NEEDS_REVIEW", "FACT", "Watch", "文件缺失。", next_action, user_confirmation_required=True)
    if not payload.valid:
        return _path_record(path, root, group, "json", "REJECTED", "FACT", "Reject", f"JSON 损坏：{payload.error}", "修复或隔离损坏文件，禁止作为研究证据。")
    if expected_type is not None and not isinstance(payload.payload, expected_type):
        return _path_record(path, root, group, "json", "NEEDS_REVIEW", "FACT", "Watch", f"JSON 类型不符合预期：{type(payload.payload).__name__}。", next_action, user_confirmation_required=True)
    return _path_record(path, root, group, "json", status_if_valid, "FACT", _decision_for_status(status_if_valid), issue_if_valid, next_action)


def _csv_record(path: Path, root: Path, group: str, *, status_if_valid: str, issue_if_valid: str, next_action: str, user_confirmation_required: bool = False) -> PFIOSDataTrustRecord:
    if not path.exists():
        return _path_record(path, root, group, "csv", "NEEDS_REVIEW", "FACT", "Watch", "CSV 文件缺失。", next_action, user_confirmation_required=True)
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
    except UnicodeDecodeError:
        return _path_record(path, root, group, "csv", "REJECTED", "FACT", "Reject", "CSV 编码不可读。", "修复编码后再进入数据链。")
    if not rows or len(rows) < 2:
        return _path_record(path, root, group, "csv", "NEEDS_REVIEW", "FACT", "Watch", "CSV 没有数据行。", next_action, user_confirmation_required=True)
    return _path_record(path, root, group, "csv", status_if_valid, "FACT", _decision_for_status(status_if_valid), issue_if_valid, next_action, user_confirmation_required=user_confirmation_required)


@dataclass(frozen=True)
class _JsonLoadResult:
    exists: bool
    valid: bool
    payload: Any = None
    error: str = ""


def _load_json(path: Path) -> _JsonLoadResult:
    if not path.exists():
        return _JsonLoadResult(False, False)
    try:
        return _JsonLoadResult(True, True, json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:
        return _JsonLoadResult(True, False, error=str(exc))


def _research_bus_status(path: Path) -> str:
    payload = _load_json(path)
    if payload.exists and payload.valid and isinstance(payload.payload, dict):
        return "RECONCILED" if str(payload.payload.get("status", "")).lower() == "pass" else "NEEDS_REVIEW"
    return "NEEDS_REVIEW"


def _missing_or_rejected_record(path: Path, root: Path, group: str, issue: str, next_action: str) -> PFIOSDataTrustRecord:
    status = "REJECTED" if path.exists() else "NEEDS_REVIEW"
    return _path_record(path, root, group, path.suffix.lower().lstrip(".") or "file", status, "FACT", _decision_for_status(status), issue, next_action, user_confirmation_required=status == "NEEDS_REVIEW")


def _path_record(
    path: Path,
    root: Path,
    group: str,
    source_type: str,
    status: str,
    evidence: str,
    decision: str,
    issue: str,
    next_action: str,
    *,
    user_confirmation_required: bool = False,
) -> PFIOSDataTrustRecord:
    if status not in DATA_TRUST_STATUSES:
        raise ValueError(f"Unknown data trust status: {status}")
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    modified_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""
    content_hash = _file_hash(path) if path.exists() and path.is_file() else ""
    rel_path = _relative_path(path, root)
    return PFIOSDataTrustRecord(
        record_id=_stable_id("quantLabDataTrustRecord", group, rel_path, modified_at, str(size)),
        source_group=group,
        source_path=rel_path,
        source_type=source_type,
        trust_status=status,
        evidence_classification=evidence,
        decision_grade=decision,
        user_confirmation_required=user_confirmation_required or status in {"NEEDS_REVIEW", "PARSED_CANDIDATE"},
        issue=issue,
        next_action=next_action,
        size_bytes=size,
        modified_at=modified_at,
        content_hash=content_hash,
    )


def _required_path_record(path: Path, root: Path, group: str, source_type: str, issue: str, next_action: str) -> PFIOSDataTrustRecord:
    if path.exists():
        return _path_record(path, root, group, source_type, "RECONCILED", "FACT", "Actionable", issue, next_action)
    return _path_record(path, root, group, source_type, "NEEDS_REVIEW", "FACT", "Watch", f"必需文件缺失：{path.name}。", next_action, user_confirmation_required=True)


def _advisory_path_record(path: Path, root: Path, group: str, source_type: str, next_action: str) -> PFIOSDataTrustRecord:
    if path.exists():
        return _path_record(path, root, group, source_type, "RECONCILED", "FACT", "Actionable", f"建议控制文件存在：{path.name}。", next_action)
    return _path_record(path, root, group, source_type, "NEEDS_REVIEW", "FACT", "Watch", f"建议控制文件缺失：{path.name}。", next_action, user_confirmation_required=True)


def _decision_for_status(status: str) -> str:
    if status == "REJECTED":
        return "Reject"
    if status in {"NEEDS_REVIEW", "PARSED_CANDIDATE", "RAW_IMPORTED"}:
        return "Watch"
    if status == "ARCHIVED":
        return "Observe"
    return "Actionable"


def _pid_file_status(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_text(encoding="utf-8").strip()
        pid = int(raw)
    except Exception:
        return "NEEDS_REVIEW", "PID 文件不可解析，可能是运行残留。"
    if pid <= 0:
        return "NEEDS_REVIEW", "PID 文件内容无效，可能是运行残留。"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "ARCHIVED", "PID 文件对应进程不存在，按旧运行残留归档。"
    except PermissionError:
        return "NEEDS_REVIEW", "PID 文件对应进程存在但当前用户无权限确认详情。"

    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            cmdline = proc_cmdline.read_text(encoding="utf-8", errors="ignore").replace("\x00", " ").lower()
        except OSError:
            cmdline = ""
        if "pfi_os" in cmdline or "streamlit_app.py" in cmdline or "streamlit" in cmdline:
            return "NEEDS_REVIEW", "PID 文件对应 PFIOS/Streamlit 相关进程仍存在，需要确认是否为当前服务。"
        return "ARCHIVED", "PID 文件对应进程存在但不是 PFIOS/Streamlit，按旧运行残留归档。"

    return "NEEDS_REVIEW", "PID 文件对应进程仍存在，需要确认是否为当前 PFIOS 服务。"


def _lock_file_status(path: Path) -> tuple[str, str]:
    try:
        stat = path.stat()
    except OSError:
        return "NEEDS_REVIEW", "锁文件状态无法读取。"
    age_seconds = max(0.0, datetime.now().timestamp() - stat.st_mtime)
    if stat.st_size == 0 and age_seconds >= 3600:
        return "ARCHIVED", "空锁文件已超过 1 小时，按旧运行残留归档。"
    return "NEEDS_REVIEW", "存在近期或非空锁文件，可能是正常运行残留或正在写入。"


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _date_stamp(as_of: str) -> str:
    parsed = datetime.fromisoformat(as_of)
    return parsed.strftime("%d%m%Y")


def _audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        f"# PFIOS Data Trust Audit {audit['as_of']}",
        "",
        "## Summary",
        f"- System: {audit['system']}",
        f"- Run ID: {audit['run_id']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Records: {audit['record_count']}",
        f"- Review Count: {audit['review_count']}",
        f"- Rejected Count: {audit['rejected_count']}",
        "",
        "## Status Counts",
        _markdown_table([{"status": key, "count": value} for key, value in audit["status_counts"].items()], ["status", "count"]),
        "",
        "## High Priority Records",
        _markdown_table(
            [row for row in audit["records"] if row["trust_status"] in {"NEEDS_REVIEW", "REJECTED"}][:30],
            ["trust_status", "decision_grade", "source_group", "source_path", "issue", "next_action"],
        ),
        "",
        "## Assumptions",
        *[f"- {item}" for item in audit["assumptions"]],
    ]
    return "\n".join(lines)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "None"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        values = [str(row.get(column, "")).replace("\n", " ").replace("|", "/") for column in columns]
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *body])


def _write_records_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(PFIOSDataTrustRecord.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _write_simple_pdf(path: Path, audit: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"PFIOS Data Trust Audit {audit['as_of']}",
        f"Run ID: {audit['run_id']}",
        f"Generated At: {audit['generated_at']}",
        f"Audit Status: {audit['audit_status']}",
        f"Records: {audit['record_count']}",
        f"Review Count: {audit['review_count']}",
        f"Rejected Count: {audit['rejected_count']}",
        "",
        "Status Counts:",
        *[f"- {key}: {value}" for key, value in audit["status_counts"].items()],
        "",
        "Key rule: candidate, video, OCR, stale cache, and weak evidence must not be promoted.",
    ]
    content = ["BT", "/F1 12 Tf", "72 760 Td", "14 TL"]
    for line in lines[:52]:
        content.append(f"({_pdf_escape(_pdf_ascii(line))}) Tj")
        content.append("T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    _write_pdf_objects(path, objects)


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    path.write_bytes(bytes(content))


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
