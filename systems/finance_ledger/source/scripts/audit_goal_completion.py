#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.reports import write_report_pdf


DEFAULT_OUTPUT_DIR = "outputs/finance_ledger_20220605_20260603"
DEFAULT_LEDGER_DB = "data/finance_ledger/finance_ledger.sqlite"
FIELDNAMES = ["requirement_id", "requirement", "status", "evidence", "detail", "next_action"]


def _exists(path: Path, *, min_bytes: int = 1) -> bool:
    return path.exists() and path.stat().st_size >= min_bytes


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_zip() -> Path | None:
    delivery = ROOT / "outputs" / "delivery"
    if not delivery.exists():
        return None
    zips = sorted(delivery.glob("economic_bleed_delivery_*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


def _display_path(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_absolute() and path.is_relative_to(ROOT) else str(path)


def _row(requirement_id: str, requirement: str, status: str, evidence: list[str], detail: str, next_action: str) -> dict[str, str]:
    return {
        "requirement_id": requirement_id,
        "requirement": requirement,
        "status": status,
        "evidence": "; ".join(evidence),
        "detail": detail,
        "next_action": next_action,
    }


def _validate_user_acceptance(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {
            "status": "needs_user_input",
            "detail": "no exported user acceptance decision file found",
            "next_action": "打开 acceptance_workbench.html 选择 A/B/C 并导出验收结果；只有全部选择 A 且 final_acceptance=A，才会关闭该项。",
        }
    try:
        payload = _read_json(path)
    except json.JSONDecodeError as exc:
        return {
            "status": "needs_user_input",
            "detail": f"user acceptance decision file is invalid JSON: {exc.msg}",
            "next_action": "重新从 acceptance_workbench.html 导出 user_acceptance_decisions.json。",
        }
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return {
            "status": "needs_user_input",
            "detail": "user acceptance decision file has no non-empty choices list",
            "next_action": "重新从 acceptance_workbench.html 导出包含 choices 的验收 JSON。",
        }
    counts = {"A": 0, "B": 0, "C": 0, "invalid": 0}
    final_choice = ""
    invalid_ids: list[str] = []
    open_items: list[str] = []
    for index, item in enumerate(choices, start=1):
        item_id = str(item.get("id") or f"row_{index}") if isinstance(item, dict) else f"row_{index}"
        choice = str(item.get("choice") or "").strip().upper() if isinstance(item, dict) else ""
        if choice in {"A", "B", "C"}:
            counts[choice] += 1
            if choice in {"B", "C"}:
                open_items.append(f"{item_id}={choice}")
        else:
            counts["invalid"] += 1
            invalid_ids.append(item_id)
        if item_id == "final_acceptance":
            final_choice = choice
    parts = [
        f"choices={len(choices)}",
        f"A={counts['A']}",
        f"B={counts['B']}",
        f"C={counts['C']}",
        f"invalid={counts['invalid']}",
        f"final_acceptance={final_choice or 'missing'}",
    ]
    if invalid_ids:
        parts.append("invalid_ids=" + ",".join(invalid_ids[:5]))
    if open_items:
        parts.append("open_items=" + ",".join(open_items[:5]))
    detail = "; ".join(parts)
    if final_choice == "A" and counts["B"] == 0 and counts["C"] == 0 and counts["invalid"] == 0:
        return {
            "status": "met",
            "detail": detail + "; strict_acceptance=true",
            "next_action": "如用户后续修改验收选择，重新导出 user_acceptance_decisions.json 并运行 finalize_delivery.py。",
        }
    return {
        "status": "needs_user_input",
        "detail": detail + "; strict_acceptance=false",
        "next_action": "将 final_acceptance 设为 A，且所有验收项均为 A；如有 B/C，按矩阵继续精修或补资料后重新验收。",
    }


def _acceptance_choices(path: Path) -> dict[str, str]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return {}
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return {}
    result: dict[str, str] = {}
    for item in choices:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "").strip()
        choice = str(item.get("choice") or "").strip().upper()
        if item_id and choice in {"A", "B", "C"}:
            result[item_id] = choice
    return result


def build_rows(output_dir: Path, ledger_db: Path, delivery_zip: Path | None = None) -> list[dict[str, str]]:
    reports = output_dir / "reports"
    audit = output_dir / "audit"
    acceptance_file = output_dir / "audit" / "user_acceptance_decisions.json"
    acceptance_choices = _acceptance_choices(acceptance_file)
    rows: list[dict[str, str]] = []

    period_reports = [
        reports / "weekly_report.pdf",
        reports / "monthly_report.pdf",
        reports / "quarterly_report.pdf",
        reports / "half_year_report.pdf",
        reports / "yearly_report.pdf",
        reports / "annual_bill_cycle_report.pdf",
    ]
    period_ok = all(_exists(path, min_bytes=20_000) for path in period_reports)
    rows.append(
        _row(
            "period_pdf_visual_reports",
            "周/月/季/半年/年/账期正式 PDF 报告且包含可视化图表",
            "met" if period_ok else "gap",
            [str(path.relative_to(output_dir)) for path in period_reports],
            "period reports present and non-empty" if period_ok else "one or more required period PDF reports missing or empty",
            "缺失时重跑 import_ledger.py 或 weekly_update.py 并检查 validate_outputs.py。",
        )
    )

    ui_pages = [
        reports / "index.html",
        reports / "operations_center.html",
        reports / "acceptance_workbench.html",
        reports / "reference_model_lab.html",
        reports / "dashboard.html",
        reports / "behavior_analysis.html",
        reports / "transaction_explorer.html",
        reports / "tag_library.html",
        reports / "review_workbench.html",
    ]
    ui_ok = all(_exists(path, min_bytes=5_000) for path in ui_pages)
    rows.append(
        _row(
            "local_interactive_ui",
            "本地 dashboard、交互 UI、开源参考工作台、标签库和复核工作台",
            "met" if ui_ok else "gap",
            [str(path.relative_to(output_dir)) for path in ui_pages],
            "9 local HTML entry points are present" if ui_ok else "one or more local HTML entry points missing",
            "缺失时重建输出并确认 REQUIRED_HTML、report_manifest 和浏览器验收列表同步。",
        )
    )

    reference_files = [
        audit / "reference_models.json",
        audit / "reference_source_log.json",
        audit / "reference_source_log.csv",
        reports / "reference_model_benchmark_report.pdf",
        reports / "reference_model_lab.html",
    ]
    reference_ok = all(_exists(path, min_bytes=20) for path in reference_files)
    rows.append(
        _row(
            "github_reference_models",
            "访问并吸收 GitHub/开源账单和个人财务模型的功能、布局和 UI 思路",
            "met" if reference_ok else "gap",
            [str(path.relative_to(output_dir)) for path in reference_files],
            "reference model audit, benchmark PDF, and interactive lab are present" if reference_ok else "reference model evidence incomplete",
            "补齐 reference_models 审计数据、PDF 对标报告和 reference_model_lab.html。",
        )
    )

    chatgpt_audit = audit / "chatgpt_reference_audit.json"
    if _exists(chatgpt_audit, min_bytes=20):
        payload = _read_json(chatgpt_audit)
        status = payload.get("status")
        gap_summary = payload.get("gap_summary", {})
        if status == "found" and not gap_summary.get("gap"):
            chatgpt_status = "met"
            detail = f"ChatGPT reference found; gap_summary={gap_summary}"
            next_action = "如用户提供新版本文件，重新运行 audit_chatgpt_reference.py 和 finalize_delivery.py。"
        elif status == "found":
            chatgpt_status = "gap"
            detail = f"ChatGPT reference found with unresolved gaps; gap_summary={gap_summary}"
            next_action = "按 chatgpt_reference_gap_matrix.csv 逐项改造后重新验收。"
        elif acceptance_choices.get("chatgpt_reference") == "A":
            chatgpt_status = "met"
            detail = f"ChatGPT reference source missing, but user accepted current reference boundary via chatgpt_reference=A; gap_summary={gap_summary}"
            next_action = "如后续提供消费系统专用 ChatGPT 对照文件，再重新运行 audit_chatgpt_reference.py 和 finalize_delivery.py。"
        else:
            chatgpt_status = "needs_user_input"
            detail = f"ChatGPT reference source missing; gap_summary={gap_summary}"
            next_action = "把 ChatGPT 版本、代码或要求文件放入 chatgpt_reference/ 或用 --input 指定后重跑。"
    else:
        chatgpt_status = "gap"
        detail = "chatgpt_reference_audit.json missing"
        next_action = "运行 scripts/audit_chatgpt_reference.py。"
    rows.append(
        _row(
            "chatgpt_reference_comparison",
            "参考 ChatGPT 版本、代码和要求文件并做逐项对照",
            chatgpt_status,
            ["audit/chatgpt_reference_audit.json", "audit/chatgpt_reference_gap_matrix.csv", "reports/chatgpt_reference_intake_report.pdf"],
            detail,
            next_action,
        )
    )

    browser_audit = audit / "browser_visual_acceptance.json"
    browser_status = "gap"
    browser_detail = "browser_visual_acceptance.json missing"
    if _exists(browser_audit, min_bytes=20):
        payload = _read_json(browser_audit)
        if payload.get("checked_count") == 18 and payload.get("failure_count") == 0:
            browser_status = "met"
            browser_detail = f"checked_count=18, failure_count=0, generated_at={payload.get('generated_at')}"
        else:
            browser_detail = f"checked_count={payload.get('checked_count')}, failure_count={payload.get('failure_count')}"
    rows.append(
        _row(
            "browser_visual_acceptance",
            "核心页面桌面/移动真实浏览器验收",
            browser_status,
            ["audit/browser_visual_acceptance.json"],
            browser_detail,
            "失败或过期时运行 finalize_delivery.py --ensure-server。",
        )
    )

    sqlite_ok = _exists(ledger_db, min_bytes=100_000) and _exists(output_dir / "data" / "consumption.sqlite", min_bytes=100_000)
    rows.append(
        _row(
            "repeatable_sqlite_project",
            "四年账单入库、共享 SQLite、脚本、测试和可重复运行工程",
            "met" if sqlite_ok else "gap",
            [str(ledger_db), "data/consumption.sqlite", "scripts/weekly_update.py", "scripts/finalize_delivery.py", "tests/"],
            "shared ledger and output SQLite databases exist" if sqlite_ok else "SQLite evidence missing",
            "重跑 import_ledger.py，并确认 data contract 与只读视图存在。",
        )
    )

    review_queue = output_dir / "review" / "manual_review_queue.csv"
    review_status = "met" if _exists(review_queue, min_bytes=20) else "gap"
    rows.append(
        _row(
            "large_review_isolation",
            "一万以上大额交易先复核，未确认前不进入生产统计",
            review_status,
            ["review/manual_review_queue.csv", "reports/review_workbench.html", "reports/manual_review_report.pdf"],
            "manual review queue and dropdown workbench are present" if review_status == "met" else "manual review queue missing",
            "用户确认后用 review_decisions_confirmed.csv 回灌并重建报告。",
        )
    )

    acceptance_result = _validate_user_acceptance(acceptance_file)
    rows.append(
        _row(
            "user_expectation_acceptance",
            "最终目标满足用户预期",
            acceptance_result["status"],
            ["reports/acceptance_workbench.html", "reports/user_acceptance_matrix_report.pdf", "audit/user_acceptance_decisions.json"],
            acceptance_result["detail"],
            acceptance_result["next_action"],
        )
    )

    latest_zip = delivery_zip if delivery_zip else _latest_zip()
    package_ok = latest_zip is not None and _exists(latest_zip, min_bytes=1_000_000)
    rows.append(
        _row(
            "delivery_package",
            "代码、报告、SQLite、审计和测试打包交付 ZIP",
            "met" if package_ok else "gap",
            [_display_path(latest_zip) if latest_zip else "outputs/delivery/*.zip"],
            f"latest_zip={latest_zip.name if latest_zip else 'missing'}" if package_ok else "delivery package missing",
            "运行 scripts/finalize_delivery.py --ensure-server --json。",
        )
    )
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    machine_total = sum(1 for row in rows if row["status"] != "needs_user_input")
    machine_met = sum(1 for row in rows if row["status"] == "met")
    return {
        "total": len(rows),
        "counts": counts,
        "machine_verifiable_total": machine_total,
        "machine_verifiable_met": machine_met,
        "machine_verifiable_pct": round(machine_met / machine_total * 100, 2) if machine_total else 0.0,
        "goal_complete": counts.get("gap", 0) == 0 and counts.get("needs_user_input", 0) == 0,
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(rows: list[dict[str, str]], summary: dict[str, Any]) -> str:
    lines = [
        "# 目标完成度机器审计报告",
        "",
        "目的：把 active goal 拆成可检查证据项，明确哪些已经由文件、测试、浏览器验收和交付包证明，哪些仍需用户输入或外部 ChatGPT 对照文件。该报告不替代用户最终验收。",
        "",
        "## 审计总览",
        "",
        "| 指标 | 当前值 |",
        "|---|---:|",
        f"| 审计项 | {summary['total']} |",
        f"| 已满足 | {summary['counts'].get('met', 0)} |",
        f"| 存在缺口 | {summary['counts'].get('gap', 0)} |",
        f"| 需要用户输入 | {summary['counts'].get('needs_user_input', 0)} |",
        f"| 机器可验证完成度 | {summary['machine_verifiable_pct']:.2f}% |",
        f"| 是否可标记总目标完成 | {'是' if summary['goal_complete'] else '否'} |",
        "| 审计策略 | evidence_required_no_subjective_completion |",
        "",
        "## 逐项矩阵",
        "",
        "| 要求 | 状态 | 证据 | 说明 | 下一步 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['requirement']} | {row['status']} | `{row['evidence']}` | {row['detail']} | {row['next_action']} |")
    lines.extend(
        [
            "",
            "## 状态口径",
            "",
            "| 状态 | 含义 |",
            "|---|---|",
            "| met | 当前工作区已有可检查证据证明该项完成。 |",
            "| gap | 当前工作区证据不足或存在明确缺口，需要继续工程改造。 |",
            "| needs_user_input | 机器无法替用户判断，或缺少外部 ChatGPT 对照文件/用户验收文件。 |",
            "",
        ]
    )
    return "\n".join(lines)


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    ledger_db = Path(args.ledger_db)
    delivery_zip = Path(args.delivery_zip) if getattr(args, "delivery_zip", "") else None
    audit_dir = output_dir / "audit"
    reports_dir = output_dir / "reports"
    rows = build_rows(output_dir, ledger_db, delivery_zip)
    summary = summarize(rows)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "rows": rows,
        "policy": "evidence_required_no_subjective_completion",
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "goal_completion_audit.json"
    csv_path = audit_dir / "goal_completion_audit.csv"
    md_path = reports_dir / "goal_completion_audit_report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(csv_path, rows)
    markdown = report_markdown(rows, summary)
    md_path.write_text(markdown, encoding="utf-8")
    write_report_pdf(markdown, md_path.with_suffix(".pdf"))
    manifest_path = audit_dir / "report_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"reports": {}}
    else:
        manifest = {"reports": {}}
    reports = manifest.setdefault("reports", {})
    reports["goal_completion_audit_md"] = str(md_path)
    reports["goal_completion_audit_pdf"] = str(md_path.with_suffix(".pdf"))
    reports["goal_completion_audit_json"] = str(json_path)
    reports["goal_completion_audit_csv"] = str(csv_path)
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "goal_complete": summary["goal_complete"],
        "summary": summary,
        "json": str(json_path),
        "csv": str(csv_path),
        "report_pdf": str(md_path.with_suffix(".pdf")),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit active goal completion against current local evidence.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-db", default=DEFAULT_LEDGER_DB)
    parser.add_argument("--delivery-zip", default="", help="Optional current delivery ZIP path to use as package evidence.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_audit(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"goal_complete: {result['goal_complete']}")
        print(f"report_pdf: {result['report_pdf']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
