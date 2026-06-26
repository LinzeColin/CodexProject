#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.reports import write_report_pdf


DEFAULT_OUTPUT_DIR = "outputs/finance_ledger_20220605_20260603"
DEFAULT_SCAN_DIRS = ["chatgpt_reference", "requirements"]
SUPPORTED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".html", ".py", ".js", ".ts", ".tsx", ".jsx"}
GAP_FIELDNAMES = [
    "requirement_id",
    "requirement",
    "source_hits",
    "implementation_status",
    "evidence",
    "next_action",
]
REQUIREMENT_PROBES = [
    {
        "id": "pdf_reports",
        "requirement": "正式 PDF 周/月/季/半年/年报",
        "keywords": ["pdf", "报告", "周报", "月报", "季报", "半年报", "年报"],
        "evidence": ["reports/weekly_report.pdf", "reports/monthly_report.pdf", "reports/quarterly_report.pdf", "reports/half_year_report.pdf", "reports/yearly_report.pdf"],
        "next_action": "如 ChatGPT 文件要求额外报告类型，追加到 REQUIRED_REPORTS 和报告生成链路。",
    },
    {
        "id": "visual_dashboard",
        "requirement": "可视化图表与 dashboard",
        "keywords": ["可视化", "图表", "dashboard", "仪表盘", "折线图", "环形图"],
        "evidence": ["reports/dashboard.html", "reports/visual_quality_acceptance_report.pdf"],
        "next_action": "若来源要求新的图表类型，先加入 dashboard/周期报告，再纳入浏览器验收。",
    },
    {
        "id": "local_interactive_ui",
        "requirement": "本地交互 UI 和工作台",
        "keywords": ["本地", "交互", "ui", "页面", "工作台", "layout", "界面"],
        "evidence": ["reports/index.html", "reports/operations_center.html", "reports/acceptance_workbench.html"],
        "next_action": "如果来源要求在线部署，应另建认证、权限、脱敏和备份设计。",
    },
    {
        "id": "github_reference_models",
        "requirement": "GitHub/开源参考模型吸收",
        "keywords": ["github", "开源", "参考模型", "reference", "benchmark"],
        "evidence": ["reports/reference_model_benchmark_report.pdf", "reports/reference_model_lab.html", "audit/reference_models.json"],
        "next_action": "如来源指定新项目，补充 reference_models 审计和 reference_model_lab 视图。",
    },
    {
        "id": "classification_rules",
        "requirement": "经济放血分类、主类/子类、风险标签",
        "keywords": ["分类", "主类", "子类", "风险标签", "经济放血", "消费控制"],
        "evidence": ["reports/classification_rulebook_report.pdf", "summary_by_category.csv", "summary_by_risk_tag.csv"],
        "next_action": "如来源分类口径冲突，先生成规则差异，再更新 configs/classification_rules.json 和测试。",
    },
    {
        "id": "large_review",
        "requirement": "一万以上大额复核与下拉分类",
        "keywords": ["大额", "复核", "10000", "一万", "下拉", "人工筛选"],
        "evidence": ["reports/review_workbench.html", "review/manual_review_queue.csv", "reports/manual_review_report.pdf"],
        "next_action": "如来源要求新的复核状态，扩展 review_decisions schema 并重建报告。",
    },
    {
        "id": "tag_library",
        "requirement": "标签库、可自定义筛选组合、持久保存",
        "keywords": ["标签库", "标签", "筛选组合", "自定义", "永久保存"],
        "evidence": ["reports/tag_library.html", "data/tag_library.csv", "data/tag_filter_presets.csv"],
        "next_action": "如来源要求更多内置标签，补充默认标签库并保持 SQLite 回灌。",
    },
    {
        "id": "sqlite_api",
        "requirement": "SQLite 底层数据库和只读 API",
        "keywords": ["sqlite", "数据库", "api", "底层数据库", "下游", "只读"],
        "evidence": ["data/consumption.sqlite", "reports/user_manual_report.pdf"],
        "next_action": "如来源要求远程访问，先做认证、脱敏、访问日志和备份方案。",
    },
    {
        "id": "validation_package",
        "requirement": "测试、浏览器验收和 ZIP 交付",
        "keywords": ["测试", "验收", "浏览器", "zip", "打包", "交付"],
        "evidence": ["audit/browser_visual_acceptance.json", "reports/delivery_acceptance_report.pdf"],
        "next_action": "如来源要求新入口，必须加入 validate_outputs、浏览器验收和 package manifest。",
    },
    {
        "id": "chatgpt_direct_reference",
        "requirement": "ChatGPT 版本/代码/要求文件逐项对照",
        "keywords": ["chatgpt", "gpt", "版本", "代码", "要求文件", "对照"],
        "evidence": ["audit/chatgpt_reference_audit.json", "audit/chatgpt_reference_gap_matrix.csv"],
        "next_action": "候选文件已发现时按本差距矩阵改造；未发现时保持 fail-closed，不伪造对照内容。",
    },
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_score(path: Path) -> tuple[bool, str]:
    haystack = " ".join(part.casefold() for part in path.parts)
    name = path.name.casefold()
    reasons: list[str] = []
    if "chatgpt" in haystack or "gpt" in name:
        reasons.append("filename_or_path_mentions_chatgpt")
    if "requirement" in haystack or "需求" in haystack:
        reasons.append("filename_or_path_mentions_requirements")
    if "reference" in haystack or "对照" in haystack or "版本" in haystack:
        reasons.append("filename_or_path_mentions_reference")
    return bool(reasons), "|".join(reasons)


def discover_inputs(scan_dirs: list[str], explicit_inputs: list[str]) -> list[Path]:
    candidates: list[Path] = []
    for raw in explicit_inputs:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        if path.is_dir():
            candidates.extend(child for child in path.rglob("*") if child.is_file())
        elif path.is_file():
            candidates.append(path)
    for raw in scan_dirs:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            continue
        if path.is_file():
            candidates.append(path)
        else:
            candidates.extend(child for child in path.rglob("*") if child.is_file())
    filtered: list[Path] = []
    for path in candidates:
        if path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            continue
        matched, _ = _candidate_score(path)
        if matched:
            filtered.append(path.resolve())
    return sorted(set(filtered))


def build_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        stat = path.stat()
        matched, reason = _candidate_score(path)
        rows.append(
            {
                "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
                "status": "candidate" if matched else "ignored",
                "reason": reason,
                "suffix": path.suffix,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "sha256": _sha256(path),
            }
        )
    return rows


def _read_candidate_text(path: Path, max_chars: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def build_gap_rows(paths: list[Path], output_dir: Path) -> list[dict[str, Any]]:
    combined_text = "\n".join(_read_candidate_text(path) for path in paths).casefold()
    has_source = bool(paths)
    gap_rows: list[dict[str, Any]] = []
    for probe in REQUIREMENT_PROBES:
        source_hits = sum(1 for keyword in probe["keywords"] if keyword.casefold() in combined_text) if has_source else 0
        evidence_paths = [output_dir / str(item) for item in probe["evidence"]]
        evidence_ok = all(path.exists() and path.stat().st_size > 0 for path in evidence_paths)
        if not has_source:
            status = "blocked_missing_chatgpt_source"
        elif source_hits == 0:
            status = "not_requested_by_reference"
        elif evidence_ok:
            status = "implemented"
        else:
            status = "gap"
        gap_rows.append(
            {
                "requirement_id": probe["id"],
                "requirement": probe["requirement"],
                "source_hits": source_hits,
                "implementation_status": status,
                "evidence": "; ".join(probe["evidence"]),
                "next_action": probe["next_action"],
            }
        )
    return gap_rows


def gap_summary(gap_rows: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for row in gap_rows:
        status = str(row.get("implementation_status", "unknown"))
        summary[status] = summary.get(status, 0) + 1
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or ["path", "status", "reason", "suffix", "size_bytes", "modified_at", "sha256"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(rows: list[dict[str, Any]], gap_rows: list[dict[str, Any]], *, scan_dirs: list[str], explicit_inputs: list[str]) -> str:
    status = "found" if rows else "missing"
    summary = gap_summary(gap_rows)
    lines = [
        "# ChatGPT 对照文件接入审计报告",
        "",
        "目的：把“参考 ChatGPT 的版本、代码和要求文件”从口头缺口变成可重复运行的文件接入审计和差距矩阵。该报告只记录当前工作区实际发现的候选文件，不伪造不存在的 ChatGPT 对照内容。",
        "",
        "## 审计结论",
        "",
        "| 项目 | 当前值 |",
        "|---|---|",
        f"| 状态 | {status} |",
        f"| 候选文件数 | {len(rows)} |",
        f"| 已实现命中项 | {summary.get('implemented', 0)} |",
        f"| 差距项 | {summary.get('gap', 0)} |",
        f"| 未发现来源阻塞项 | {summary.get('blocked_missing_chatgpt_source', 0)} |",
        f"| 扫描目录 | `{', '.join(scan_dirs)}` |",
        f"| 显式输入 | `{', '.join(explicit_inputs) if explicit_inputs else '未提供'}` |",
        "",
        "## 候选文件清单",
        "",
        "| 文件 | 状态 | 原因 | 大小 | SHA256 |",
        "|---|---|---|---:|---|",
    ]
    if rows:
        for row in rows:
            lines.append(f"| `{row['path']}` | {row['status']} | {row['reason']} | {row['size_bytes']} | `{str(row['sha256'])[:16]}` |")
    else:
        lines.append("| 未发现 | missing | 当前默认目录和显式输入均无 ChatGPT/对照/需求候选文件 | 0 |  |")
    lines.extend(
        [
            "",
            "## 差距矩阵",
            "",
            "| 对照项 | 来源命中 | 实现状态 | 证据 | 下一步 |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in gap_rows:
        lines.append(
            f"| {row['requirement']} | {row['source_hits']} | {row['implementation_status']} | `{row['evidence']}` | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## 接入规则",
            "",
            "| 规则 | 说明 |",
            "|---|---|",
            "| 不伪造来源 | 没有文件时只产出 missing 状态，不把用户对话或本项目代码冒充 ChatGPT 版本。 |",
            "| 可重复扫描 | 后续把 ChatGPT 版本、代码、PRD、要求文件放入 `chatgpt_reference/` 或用 `--input` 指定，再重跑本脚本。 |",
            "| 自动差距矩阵 | 候选文件存在时会按 PDF、dashboard、UI、开源参考、分类、复核、标签库、SQLite/API、验收打包等维度生成差距矩阵。 |",
            "| 可审计哈希 | 每个候选文件记录路径、大小、修改时间和 SHA256，便于后续对照版本锁定。 |",
            "| 不自动覆盖实现 | 候选文件只进入审计和差距分析；是否改代码仍通过验收工作台和最终门禁确认。 |",
            "",
            "## 后续动作",
            "",
            "| 选项 | 动作 |",
            "|---|---|",
            "| A | 如果当前开源对标和需求追踪足够，保持 ChatGPT 对照为 missing 但不阻塞工程基线。 |",
            "| B | 把 ChatGPT 版本/代码/要求文件放入 `chatgpt_reference/` 后重跑本脚本和 `scripts/finalize_delivery.py`。 |",
            "| C | 如果 ChatGPT 文件要求重构，先生成差距矩阵，再按功能模块逐项改动并重新验收。 |",
            "",
        ]
    )
    return "\n".join(lines)


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    audit_dir = output_dir / "audit"
    reports_dir = output_dir / "reports"
    paths = discover_inputs(args.scan_dir, args.input or [])
    rows = build_rows(paths)
    gap_rows = build_gap_rows(paths, output_dir)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "found" if rows else "missing",
        "candidate_count": len(rows),
        "scan_dirs": args.scan_dir,
        "inputs": args.input or [],
        "rows": rows,
        "gap_rows": gap_rows,
        "gap_summary": gap_summary(gap_rows),
        "policy": "fail_closed_no_reference_fabrication",
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "chatgpt_reference_audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(audit_dir / "chatgpt_reference_audit.csv", rows)
    write_csv(audit_dir / "chatgpt_reference_gap_matrix.csv", gap_rows, GAP_FIELDNAMES)
    markdown = report_markdown(rows, gap_rows, scan_dirs=args.scan_dir, explicit_inputs=args.input or [])
    md_path = reports_dir / "chatgpt_reference_intake_report.md"
    md_path.write_text(markdown, encoding="utf-8")
    write_report_pdf(markdown, md_path.with_suffix(".pdf"))
    manifest_path = audit_dir / "report_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"reports": {}}
    else:
        manifest = {"generated_at": datetime.now().isoformat(timespec="seconds"), "reports": {}}
    reports = manifest.setdefault("reports", {})
    reports["chatgpt_reference_intake_md"] = str(md_path)
    reports["chatgpt_reference_intake_pdf"] = str(md_path.with_suffix(".pdf"))
    reports["chatgpt_reference_gap_matrix_csv"] = str(audit_dir / "chatgpt_reference_gap_matrix.csv")
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": payload["status"],
        "candidate_count": len(rows),
        "json": str(audit_dir / "chatgpt_reference_audit.json"),
        "csv": str(audit_dir / "chatgpt_reference_audit.csv"),
        "gap_csv": str(audit_dir / "chatgpt_reference_gap_matrix.csv"),
        "report_md": str(md_path),
        "report_pdf": str(md_path.with_suffix(".pdf")),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit ChatGPT reference/version/requirements files for repeatable comparison.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-dir", nargs="*", default=DEFAULT_SCAN_DIRS, help="Directories or files to scan for ChatGPT/reference requirement artifacts.")
    parser.add_argument("--input", nargs="*", help="Explicit ChatGPT reference files or directories.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_audit(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status: {result['status']}")
        print(f"candidate_count: {result['candidate_count']}")
        print(f"report_pdf: {result['report_pdf']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
