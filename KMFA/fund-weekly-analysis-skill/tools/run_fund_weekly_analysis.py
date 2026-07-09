#!/usr/bin/env python3
"""KMFA fund weekly analysis deterministic runner shell.

This runner does the non-LLM deterministic parts: input scan, hash manifest,
private run directory creation, and safety checks. OCR/vision extraction and Excel
creation are performed by the Codex agent under SKILL.md using the manifests and
sheet spec. The runner deliberately does not invent data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

DISALLOWED_PRODUCTION_MARKERS = ("sample", "demo", "fake", "synthetic", "模拟", "测试数据")
PRIVATE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xls", ".csv", ".pdf", ".doc", ".docx", ".zip"}
TEMPLATE_NAME = "资金与税费管理母版_真实数据预览_v2.xlsx"
PRIVATE_OCR_ROOT = Path("KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars")
OCR_GENERATION_PLAN_NAME = "screenshot_ocr_sidecar_generation_plan.csv"
XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
DRAWINGML_MAIN_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", XLSX_MAIN_NS)
ET.register_namespace("r", XLSX_REL_NS)
STRUCTURED_CSV_REQUIRED_FIELDS = {
    "date",
    "company",
    "bank",
    "account_alias",
    "liquidity_tier",
    "inflow",
    "outflow",
    "ending_balance",
    "flow_type",
}
EXPECTED_WORKBOOK_SHEETS = [
    "01_首页总览",
    "02_资金趋势预测",
    "03_三层净流余额",
    "04_税费融资风险",
    "05_公司银行矩阵",
    "06_CodexSkill流程",
    "H01_资金事实主表",
    "H02_异常任务池",
    "H03_钉钉证据索引",
    "H04_客户合同辅助",
    "H05_复审检查",
    "H06_配置规则",
]
FORMULA_ERROR_MARKERS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")
VISIBLE_SENSITIVE_PATTERNS = [
    r"(?<![\d.])\d{12,}(?![\d.])",
    "A" "KIA",
    "BEGIN [A-Z ]*" "PRIVATE",
    r"api[_-]?" "key" r"\s*[:=]",
    r"access[_-]?" "to" "ken" r"\s*[:=]",
    "pass" "word" r"\s*[:=]",
    "passwd" r"\s*[:=]",
    "密码[:：=]",
    "web" "hook" r"\s*(url)?\s*[:=]",
    "身份证[:：=]",
    "手机号[:：=]",
]
VISIBLE_SENSITIVE_PATTERN = re.compile("(" + "|".join(VISIBLE_SENSITIVE_PATTERNS) + ")", re.IGNORECASE)
OCR_DATE_PATTERN = re.compile(r"20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?")
OCR_AMOUNT_PATTERN = re.compile(r"(?:[￥¥]\s*)?[-+]?\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|(?:[￥¥]\s*)?[-+]?\d+(?:\.\d{1,2})")
AUTOMATION_CHECK_FIELDS = [
    "id",
    "name",
    "kind",
    "status",
    "rrule",
    "execution_environment",
    "cwds",
    "model",
    "reasoning_effort",
]
OCR_AMOUNT_CONTEXT_WORDS = (
    "余额",
    "金额",
    "可用",
    "收入",
    "支出",
    "付款",
    "回款",
    "保证金",
    "税",
    "借款",
    "贷款",
    "费用",
    "缴",
)
CHAT_TEXT_CONTEXT_WORDS = OCR_AMOUNT_CONTEXT_WORDS + (
    "付款请示",
    "付款",
    "收款",
    "银行",
    "账户",
    "现金",
    "票据",
    "电子汇票",
    "汇票",
    "开票",
    "税费",
    "调拨",
    "转账",
)
OCR_COMPANY_KEYWORDS = (
    "武汉开明",
    "武汉彤烨",
    "湖北开明",
    "湖北岚丹",
    "武汉信茂",
    "湖北曦月",
    "湖北工会",
)
OCR_BANK_KEYWORDS = (
    "招商银行",
    "中国银行",
    "建设银行",
    "农业银行",
    "工商银行",
    "交通银行",
    "汉口银行",
    "湖北银行",
    "中信银行",
    "民生银行",
    "平安银行",
    "光大银行",
    "浦发银行",
    "兴业银行",
    "邮储银行",
)
OCR_FACT_METRIC_RULES = (
    ("electronic_bill", ("电子汇票", "银行承兑", "承兑汇票", "票据")),
    ("bank_deposit", ("银行存款", "可用余额", "期末余额", "余额")),
    ("deposit_release", ("保证金",)),
    ("tax_payment", ("税费", "缴税", "税款")),
    ("loan", ("借款", "贷款")),
    ("payment_outflow", ("申请支付金额", "付款审批", "付款", "项目资金支出", "报销", "交易金额", "转账")),
)
OCR_LINE_CONTEXT_RADIUS = 3
CHAT_NEIGHBOR_CONTEXT_RADIUS = 2


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            yield p


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "screenshot"
    if suffix in {".xlsx", ".xls", ".csv"}:
        return "tabular_finance_source"
    if suffix == ".zip":
        return "archive"
    if suffix in {".pdf", ".doc", ".docx"}:
        return "document_evidence"
    return "other"


def iso_from_timestamp(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp).isoformat()


def macos_file_flags(path: Path) -> str:
    if sys.platform != "darwin":
        return ""
    try:
        result = subprocess.run(
            ["/usr/bin/stat", "-f", "%Sf", str(path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=2,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def unreadable_record(input_dir: Path, path: Path, error_type: str, error: str) -> dict:
    return {
        "relative_path": str(path.relative_to(input_dir)),
        "suffix": path.suffix.lower(),
        "kind": classify_file(path),
        "size_bytes": path.stat().st_size,
        "sha256": "",
        "mtime_iso": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "public_safe_to_commit": False,
        "error_type": error_type,
        "error": error,
    }


def summarize_tree(path: Path, limit: int = 5000) -> dict:
    file_count = 0
    latest_mtime: float | None = None
    for p in path.rglob("*"):
        if not p.is_file() or p.name.startswith("."):
            continue
        file_count += 1
        latest_mtime = max(latest_mtime or p.stat().st_mtime, p.stat().st_mtime)
        if file_count >= limit:
            break
    return {
        "file_count_limited": file_count,
        "file_count_limit": limit,
        "latest_file_mtime_iso": iso_from_timestamp(latest_mtime) if latest_mtime else None,
    }


def source_candidates_for(input_dir: Path) -> list[dict]:
    group_name = input_dir.name
    one_drive_root = input_dir.parent.parent if input_dir.parent.name == "DWS_Outputs" else input_dir.parent
    candidates = [
        ("dws_outputs_zip", one_drive_root / "DWS_Outputs.zip"),
        ("dws_archive_group", one_drive_root / "DWS_Archive" / group_name),
    ]
    result = []
    for kind, path in candidates:
        item = {
            "kind": kind,
            "path": str(path),
            "exists": path.exists(),
            "inspected": False,
            "note": "private source candidate; not used unless explicitly materialized into the configured input folder",
        }
        if path.exists():
            stat = path.stat()
            item.update({
                "size_bytes": stat.st_size,
                "mtime_iso": iso_from_timestamp(stat.st_mtime),
            })
            if path.is_dir():
                item.update(summarize_tree(path))
                item["inspected"] = True
            else:
                item["file_count_limited"] = None
                item["file_count_limit"] = None
                item["latest_file_mtime_iso"] = item["mtime_iso"]
        result.append(item)
    return result


def source_summary(files: list[dict]) -> dict:
    kinds = Counter(item["kind"] for item in files)
    suffixes = Counter(item["suffix"] or "<none>" for item in files)
    latest = max((item["mtime_iso"] for item in files), default=None)
    return {
        "kind_counts": dict(sorted(kinds.items())),
        "suffix_counts": dict(sorted(suffixes.items())),
        "latest_file_mtime_iso": latest,
        "real_file_count": len(files),
    }


def build_manifest(input_dir: Path, run_dir: Path, timezone: str) -> dict:
    files = []
    unreadable = []
    for p in sorted(iter_files(input_dir)):
        rel = str(p.relative_to(input_dir))
        flag_text = macos_file_flags(p)
        if "dataless" in flag_text:
            unreadable.append(unreadable_record(
                input_dir,
                p,
                "DatalessFile",
                f"macOS file flags indicate cloud-only content: {flag_text}",
            ))
            continue
        try:
            file_hash = sha256_file(p)
        except OSError as exc:
            unreadable.append(unreadable_record(input_dir, p, type(exc).__name__, str(exc)))
            continue
        files.append({
            "relative_path": rel,
            "suffix": p.suffix.lower(),
            "kind": classify_file(p),
            "size_bytes": p.stat().st_size,
            "sha256": file_hash,
            "mtime_iso": dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            "public_safe_to_commit": False if p.suffix.lower() in PRIVATE_EXTENSIONS else False,
        })
    now = dt.datetime.now(ZoneInfo(timezone))
    if unreadable:
        issue = {
            "issue_type": "SOURCE_UNREADABLE",
            "severity": "blocking",
            "observed_at": now.isoformat(),
            "action": "Make all configured DWS_Outputs/付款请示群 source files available offline/readable, then rerun. Do not generate a partial financial package.",
        }
        return {
            "project_id": "KMFA",
            "skill_name": "fund-weekly-analysis-skill",
            "run_id": run_dir.name,
            "timezone": timezone,
            "input_dir": str(input_dir),
            "generated_at": now.isoformat(),
            "status": "SOURCE_UNREADABLE",
            "generation_mode": "fail_closed_before_index_package",
            "file_count": len(files),
            "files": files,
            "unreadable_count": len(unreadable),
            "unreadable": unreadable,
            "source_summary": source_summary(files),
            "data_quality_issues": [issue],
        }
    manifest = {
        "project_id": "KMFA",
        "skill_name": "fund-weekly-analysis-skill",
        "run_id": run_dir.name,
        "timezone": timezone,
        "input_dir": str(input_dir),
        "generated_at": now.isoformat(),
        "status": "INDEXED_PENDING_EXTRACTION",
        "generation_mode": "no_hallucination_index_only",
        "file_count": len(files),
        "files": files,
        "source_summary": source_summary(files),
        "data_quality_issues": [{
            "issue_type": "PENDING_OCR_OR_REVIEW",
            "severity": "blocking_for_management_conclusion",
            "observed_at": now.isoformat(),
            "action": "Evidence was indexed from real files, but no financial amount is promoted until OCR/table extraction and review pass.",
        }],
    }
    return manifest


def evidence_rows(manifest: dict) -> list[dict]:
    rows = []
    for i, item in enumerate(manifest["files"], 1):
        if item["kind"] in {"screenshot", "archive", "document_evidence", "tabular_finance_source"}:
            rows.append({
                "evidence_id": f"FW{manifest['run_id']}-{i:05d}",
                "relative_path": item["relative_path"],
                "kind": item["kind"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "review_status": "indexed_only_pending_extraction",
            })
    return rows


def write_evidence_index_stub(manifest: dict, run_dir: Path) -> list[dict]:
    path = run_dir / "evidence_index.csv"
    rows = evidence_rows(manifest)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["evidence_id", "relative_path", "kind", "sha256", "size_bytes", "review_status"])
        w.writeheader()
        w.writerows(rows)
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict] | None = None) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def ocr_sidecar_candidates(relative_path: str) -> list[Path]:
    path = Path(relative_path)
    candidates = [
        Path(str(path) + ".ocr.txt"),
        path.with_suffix(".ocr.txt"),
    ]
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def read_text_excerpt(path: Path, limit: int = 180) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    normalized = " ".join(text.split())
    return normalized[:limit], len(text)


def text_excerpt(text: str, limit: int = 180) -> str:
    return " ".join(text.split())[:limit]


def normalize_ocr_date(value: str) -> str:
    digits = re.findall(r"\d+", value)
    if len(digits) < 3:
        return value.strip()
    year, month, day = digits[:3]
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def normalize_ocr_amount(value: str) -> str:
    cleaned = value.replace("￥", "").replace("¥", "").replace(",", "").strip()
    return money_text(money(cleaned))


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_has_finance_signal(text: str) -> bool:
    return any(word in text for word in CHAT_TEXT_CONTEXT_WORDS) or bool(OCR_DATE_PATTERN.search(text))


def safe_repo_relative_path(value: str) -> Path | None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def is_private_ocr_relative_path(path: Path) -> bool:
    try:
        path.relative_to(PRIVATE_OCR_ROOT)
    except ValueError:
        return False
    return True


def load_private_ocr_sidecars(repo_root: Path, run_dir: Path) -> dict[str, dict]:
    plan_path = run_dir / OCR_GENERATION_PLAN_NAME
    if not plan_path.exists():
        return {}
    rows: dict[str, dict] = {}
    try:
        with plan_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("apply_performed") != "true":
                    continue
                if row.get("generation_status") != "ocr_text_generated_pending_review":
                    continue
                if row.get("financial_fact_promoted") != "false":
                    continue
                private_rel = safe_repo_relative_path(row.get("ocr_text_private_relative_path", ""))
                source_rel = row.get("source_image_relative_path", "")
                if private_rel is None or not is_private_ocr_relative_path(private_rel) or not source_rel:
                    continue
                private_path = repo_root / private_rel
                if not private_path.exists() or not private_path.is_file():
                    continue
                rows.setdefault(source_rel, {
                    "private_relative_path": str(private_rel),
                    "text_sha256": row.get("text_sha256", ""),
                    "engine": row.get("engine", ""),
                })
    except OSError:
        return {}
    return rows


def resolve_ocr_text_path(repo_root: Path, input_dir: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if is_private_ocr_relative_path(path):
        return repo_root / path
    return input_dir / path


def collect_ocr_text_candidates(
    manifest: dict,
    input_dir: Path,
    repo_root: Path,
    run_dir: Path,
    evidence: list[dict],
) -> list[dict]:
    evidence_by_path = {row["relative_path"]: row for row in evidence}
    manifest_paths = {item["relative_path"]: item for item in manifest["files"]}
    private_sidecars = load_private_ocr_sidecars(repo_root, run_dir)
    rows: list[dict] = []
    for item in manifest["files"]:
        if item["kind"] != "screenshot":
            continue
        evidence_row = evidence_by_path.get(item["relative_path"])
        if evidence_row is None:
            continue
        for relative_sidecar in ocr_sidecar_candidates(item["relative_path"]):
            sidecar_key = str(relative_sidecar)
            sidecar_item = manifest_paths.get(sidecar_key)
            sidecar_path = input_dir / relative_sidecar
            if sidecar_item is None or not sidecar_path.exists():
                continue
            excerpt, text_length = read_text_excerpt(sidecar_path)
            evidence_row["review_status"] = "ocr_text_candidate_pending_review"
            rows.append({
                "ocr_candidate_id": f"OCR-{manifest['run_id']}-{len(rows) + 1:05d}",
                "evidence_id": evidence_row["evidence_id"],
                "source_image_relative_path": item["relative_path"],
                "ocr_text_relative_path": sidecar_key,
                "ocr_text_sha256": sidecar_item["sha256"],
                "text_length": str(text_length),
                "text_excerpt": excerpt,
                "extraction_status": "ocr_text_sidecar_indexed_pending_review",
                "review_status": "pending_human_review",
                "financial_fact_promoted": "false",
            })
            break
        else:
            private_sidecar = private_sidecars.get(item["relative_path"])
            if private_sidecar is None:
                continue
            sidecar_key = private_sidecar["private_relative_path"]
            sidecar_path = repo_root / sidecar_key
            excerpt, text_length = read_text_excerpt(sidecar_path)
            evidence_row["review_status"] = "ocr_text_candidate_pending_review"
            rows.append({
                "ocr_candidate_id": f"OCR-{manifest['run_id']}-{len(rows) + 1:05d}",
                "evidence_id": evidence_row["evidence_id"],
                "source_image_relative_path": item["relative_path"],
                "ocr_text_relative_path": sidecar_key,
                "ocr_text_sha256": private_sidecar["text_sha256"],
                "text_length": str(text_length),
                "text_excerpt": excerpt,
                "extraction_status": "private_ocr_text_sidecar_indexed_pending_review",
                "review_status": "pending_human_review",
                "financial_fact_promoted": "false",
            })
    return rows


def collect_screenshot_ocr_coverage(manifest: dict, repo_root: Path, run_dir: Path, evidence: list[dict]) -> list[dict]:
    manifest_paths = {item["relative_path"]: item for item in manifest["files"]}
    private_sidecars = load_private_ocr_sidecars(repo_root, run_dir)
    rows: list[dict] = []
    for row in evidence:
        if row["kind"] != "screenshot":
            continue
        sidecar_keys = [str(path) for path in ocr_sidecar_candidates(row["relative_path"])]
        present_sidecar = next((key for key in sidecar_keys if key in manifest_paths), "")
        private_sidecar = private_sidecars.get(row["relative_path"])
        if private_sidecar and not present_sidecar:
            present_sidecar = private_sidecar["private_relative_path"]
            sidecar_keys.append(present_sidecar)
        if present_sidecar:
            coverage_status = "ocr_text_sidecar_present_pending_review"
            next_action = "review_private_ocr_text_candidate" if private_sidecar else "review_ocr_text_candidate"
            review_status = "pending_human_review"
        else:
            coverage_status = "ocr_text_sidecar_missing"
            next_action = "run_ocr_or_attach_real_ocr_sidecar"
            review_status = "pending_ocr_extraction"
        rows.append({
            "ocr_coverage_id": f"OCRCOV-{manifest['run_id']}-{len(rows) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "source_image_relative_path": row["relative_path"],
            "ocr_sidecar_candidates": ";".join(sidecar_keys),
            "ocr_text_relative_path": present_sidecar,
            "ocr_coverage_status": coverage_status,
            "next_action": next_action,
            "review_status": review_status,
            "financial_fact_promoted": "false",
        })
    return rows


def extract_ocr_value_candidates(
    manifest: dict,
    input_dir: Path,
    repo_root: Path,
    ocr_text_candidates: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for candidate in ocr_text_candidates:
        text_path = resolve_ocr_text_path(repo_root, input_dir, candidate["ocr_text_relative_path"])
        text = text_path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            date_spans: list[tuple[int, int]] = []
            for match in OCR_DATE_PATTERN.finditer(line):
                date_spans.append(match.span())
                rows.append({
                    "value_candidate_id": f"OCRV-{manifest['run_id']}-{len(rows) + 1:05d}",
                    "ocr_candidate_id": candidate["ocr_candidate_id"],
                    "evidence_id": candidate["evidence_id"],
                    "source_image_relative_path": candidate["source_image_relative_path"],
                    "ocr_text_relative_path": candidate["ocr_text_relative_path"],
                    "candidate_type": "date",
                    "raw_value": match.group(0),
                    "normalized_value": normalize_ocr_date(match.group(0)),
                    "currency": "",
                    "line_number": str(line_number),
                    "line_text": line.strip()[:180],
                    "extraction_status": "ocr_value_candidate_pending_review",
                    "review_status": "pending_human_review",
                    "financial_fact_promoted": "false",
                })
            if not any(word in line for word in OCR_AMOUNT_CONTEXT_WORDS):
                continue
            for match in OCR_AMOUNT_PATTERN.finditer(line):
                if any(start <= match.start() < end for start, end in date_spans):
                    continue
                raw_value = match.group(0)
                if "." not in raw_value and "￥" not in raw_value and "¥" not in raw_value and "," not in raw_value:
                    continue
                rows.append({
                    "value_candidate_id": f"OCRV-{manifest['run_id']}-{len(rows) + 1:05d}",
                    "ocr_candidate_id": candidate["ocr_candidate_id"],
                    "evidence_id": candidate["evidence_id"],
                    "source_image_relative_path": candidate["source_image_relative_path"],
                    "ocr_text_relative_path": candidate["ocr_text_relative_path"],
                    "candidate_type": "amount",
                    "raw_value": raw_value,
                    "normalized_value": normalize_ocr_amount(raw_value),
                    "currency": "CNY",
                    "line_number": str(line_number),
                    "line_text": line.strip()[:180],
                    "extraction_status": "ocr_value_candidate_pending_review",
                    "review_status": "pending_human_review",
                    "financial_fact_promoted": "false",
                })
    return rows


def extract_ocr_company(text: str) -> str:
    return next((company for company in OCR_COMPANY_KEYWORDS if company in text), "")


def extract_ocr_bank(text: str) -> str:
    return next((bank for bank in OCR_BANK_KEYWORDS if bank in text), "")


def classify_ocr_fact_metric(text: str) -> str:
    for metric, keywords in OCR_FACT_METRIC_RULES:
        if any(keyword in text for keyword in keywords):
            return metric
    return ""


def source_path_date(relative_path: str) -> str:
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", relative_path)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def extract_ocr_business_date(line: str, source_relative_path: str) -> str:
    match = OCR_DATE_PATTERN.search(line)
    if match:
        return normalize_ocr_date(match.group(0))
    return source_path_date(source_relative_path)


def extract_ocr_financial_fact_candidates(
    manifest: dict,
    input_dir: Path,
    repo_root: Path,
    ocr_text_candidates: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for candidate in ocr_text_candidates:
        text_path = resolve_ocr_text_path(repo_root, input_dir, candidate["ocr_text_relative_path"])
        text = text_path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            normalized_line = " ".join(line.split())
            if not normalized_line:
                continue
            metric = classify_ocr_fact_metric(normalized_line)
            if not metric:
                continue
            date_spans = [match.span() for match in OCR_DATE_PATTERN.finditer(normalized_line)]
            for match in OCR_AMOUNT_PATTERN.finditer(normalized_line):
                if any(not (match.end() <= start or match.start() >= end) for start, end in date_spans):
                    continue
                raw_value = match.group(0)
                if "." not in raw_value and "￥" not in raw_value and "¥" not in raw_value and "," not in raw_value:
                    continue
                try:
                    amount = normalize_ocr_amount(raw_value)
                except (InvalidOperation, ValueError):
                    continue
                rows.append({
                    "fact_candidate_id": f"OCRFACT-{manifest['run_id']}-{len(rows) + 1:05d}",
                    "ocr_candidate_id": candidate["ocr_candidate_id"],
                    "evidence_id": candidate["evidence_id"],
                    "source_image_relative_path": candidate["source_image_relative_path"],
                    "ocr_text_relative_path": candidate["ocr_text_relative_path"],
                    "business_date": extract_ocr_business_date(normalized_line, candidate["source_image_relative_path"]),
                    "company": extract_ocr_company(normalized_line),
                    "bank": extract_ocr_bank(normalized_line),
                    "account_alias": "",
                    "candidate_metric": metric,
                    "amount": amount,
                    "currency": "CNY",
                    "line_number": str(line_number),
                    "line_text_excerpt": normalized_line[:180],
                    "extraction_status": "ocr_financial_fact_candidate_pending_review",
                    "review_status": "pending_human_review",
                    "financial_fact_promoted": "false",
                    "promotion_blocker": "human_cross_review_required",
                })
    return rows


def ocr_fact_review_authorization_relative_path(run_id: str) -> str:
    return f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json"


def load_ocr_fact_review_authorization(repo_root: Path, run_id: str) -> dict:
    relative_path = ocr_fact_review_authorization_relative_path(run_id)
    path = repo_root / relative_path
    missing = {
        "relative_path": relative_path,
        "status": "missing_authorization_manifest",
        "entries": {},
        "metadata": {},
    }
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_authorization_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_authorization_schema"}
    required = {
        "authorization_manifest_version": "1",
        "run_id": run_id,
        "authorization_scope": "ocr_financial_fact_review_validation_only",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_authorization_schema"}
    raw_entries = payload.get("fact_candidate_authorizations")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_authorization_schema"}
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_authorization_schema"}
        fact_candidate_id = entry.get("fact_candidate_id")
        candidate_metric = entry.get("candidate_metric")
        if not isinstance(fact_candidate_id, str) or not fact_candidate_id:
            return {**missing, "status": "invalid_authorization_schema"}
        if not isinstance(candidate_metric, str) or not candidate_metric:
            return {**missing, "status": "invalid_authorization_schema"}
        entries[fact_candidate_id] = {
            "candidate_metric": candidate_metric,
            "authorized": entry.get("authorized") is True,
        }
    return {
        "relative_path": relative_path,
        "status": "valid_authorization_manifest",
        "entries": entries,
        "metadata": {
            "authorization_ticket": str(payload.get("authorization_ticket", "")),
            "authorized_by": str(payload.get("authorized_by", "")),
            "authorized_at": str(payload.get("authorized_at", "")),
            "authorization_scope": str(payload.get("authorization_scope", "")),
        },
    }


def ocr_fact_review_gate_status(row: dict, authorization: dict) -> tuple[str, str, str, str]:
    auth_status = authorization["status"]
    if auth_status == "missing_authorization_manifest":
        return (
            "false",
            "missing_authorization_manifest",
            "blocked_missing_operator_authorization",
            "OCR fact review is blocked until a private operator authorization manifest exists.",
        )
    if auth_status != "valid_authorization_manifest":
        return (
            "false",
            auth_status,
            "blocked_invalid_operator_authorization",
            "OCR fact review is blocked because the operator authorization manifest is invalid.",
        )
    entry = authorization["entries"].get(row["fact_candidate_id"])
    if entry is None:
        return (
            "false",
            "fact_candidate_not_authorized",
            "blocked_missing_fact_candidate_authorization",
            "OCR fact review is blocked because this candidate is not covered by the operator authorization manifest.",
        )
    if entry["candidate_metric"] != row["candidate_metric"]:
        return (
            "true",
            "authorization_candidate_metric_mismatch",
            "blocked_authorization_metric_mismatch",
            "OCR fact review is blocked because the authorization metric does not match the candidate.",
        )
    if not entry["authorized"]:
        return (
            "true",
            "fact_candidate_authorization_not_true",
            "blocked_fact_candidate_not_authorized",
            "OCR fact review is blocked because this candidate is not explicitly authorized.",
        )
    return (
        "true",
        "valid_manifest_validation_only",
        "ready_for_review_staging_no_ledger_promotion",
        "Operator authorization manifest is valid for this row, but this runner only stages review evidence and does not write fund_ledger.csv.",
    )


def build_ocr_fact_review_apply_gate(manifest: dict, repo_root: Path, fact_candidates: list[dict]) -> list[dict]:
    rows: list[dict] = []
    authorization = load_ocr_fact_review_authorization(repo_root, manifest["run_id"])
    metadata = authorization["metadata"]
    for row in fact_candidates:
        authorization_present, validation_status, gate_status, gate_reason = ocr_fact_review_gate_status(row, authorization)
        rows.append({
            "review_gate_id": f"OCRGATE-{manifest['run_id']}-{len(rows) + 1:05d}",
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "evidence_id": row["evidence_id"],
            "amount": row["amount"],
            "currency": row["currency"],
            "operator_authorization_required": "true",
            "authorization_manifest_relative_path": authorization["relative_path"],
            "operator_authorization_present": authorization_present,
            "authorization_validation_status": validation_status,
            "authorization_ticket": metadata.get("authorization_ticket", ""),
            "authorized_by": metadata.get("authorized_by", ""),
            "authorized_at": metadata.get("authorized_at", ""),
            "authorization_scope": metadata.get("authorization_scope", ""),
            "review_gate_status": gate_status,
            "staging_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "gate_reason": gate_reason,
            "relative_path": row["ocr_text_relative_path"],
            "review_status": "pending_operator_authorization",
        })
    return rows


def build_ocr_fact_review_authorization_template(manifest: dict, review_gate_rows: list[dict]) -> dict:
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "ocr_financial_fact_review_validation_only",
        "template_status": "operator_review_required",
        "template_generated_from": "ocr_fact_review_apply_gate.csv",
        "output_authorization_manifest_relative_path": ocr_fact_review_authorization_relative_path(manifest["run_id"]),
        "authorized_by": "",
        "authorized_at": "",
        "authorization_ticket": "",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "operator_instruction": "Review each OCR fact candidate, edit authorized=true only where approved, then save a confirmed copy to output_authorization_manifest_relative_path. This template itself does not authorize, promote, or write fund_ledger.csv.",
        "fact_candidate_authorizations": [
            {
                "fact_candidate_id": row["fact_candidate_id"],
                "candidate_metric": row["candidate_metric"],
                "amount": row["amount"],
                "currency": row["currency"],
                "evidence_id": row["evidence_id"],
                "relative_path": row["relative_path"],
                "authorized": False,
                "operator_note": "",
            }
            for row in review_gate_rows
        ],
    }


def ocr_fact_review_preview_status(validation_status: str) -> tuple[str, str]:
    if validation_status == "valid_manifest_validation_only":
        return "ready_for_operator_review_no_ledger_promotion", "pending_operator_impact_review"
    if validation_status == "missing_authorization_manifest":
        return "blocked_missing_operator_authorization", "pending_operator_authorization"
    if validation_status in {"fact_candidate_not_authorized", "fact_candidate_authorization_not_true"}:
        return "blocked_fact_candidate_not_authorized", "pending_operator_authorization"
    if validation_status == "authorization_candidate_metric_mismatch":
        return "blocked_authorization_metric_mismatch", "pending_operator_authorization"
    return "blocked_invalid_operator_authorization", "pending_operator_authorization"


def build_ocr_fact_review_authorization_preview(manifest: dict, review_gate_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in review_gate_rows:
        preview_status, review_status = ocr_fact_review_preview_status(row["authorization_validation_status"])
        rows.append({
            "review_preview_id": f"OCRPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "review_gate_id": row["review_gate_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "authorization_validation_status": row["authorization_validation_status"],
            "preview_status": preview_status,
            "impact_scope": "ocr_financial_fact_candidate_review_only",
            "staging_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "relative_path": row["relative_path"],
            "review_status": review_status,
        })
    return rows


def build_ocr_fact_cross_review_summary(
    manifest: dict,
    fact_candidates: list[dict],
    review_gate_rows: list[dict],
) -> list[dict]:
    gate_by_fact_id = {row["fact_candidate_id"]: row for row in review_gate_rows}
    groups: dict[str, dict] = {}
    for row in fact_candidates:
        metric = row["candidate_metric"]
        group = groups.setdefault(metric, {
            "candidate_metric": metric,
            "candidate_count": 0,
            "candidate_amount_total": Decimal("0.00"),
            "evidence_ids": set(),
            "company_present_count": 0,
            "bank_present_count": 0,
            "operator_authorized_count": 0,
            "authorization_blocked_count": 0,
        })
        group["candidate_count"] += 1
        group["candidate_amount_total"] += Decimal(row["amount"])
        group["evidence_ids"].add(row["evidence_id"])
        if row["company"]:
            group["company_present_count"] += 1
        if row["bank"]:
            group["bank_present_count"] += 1
        gate = gate_by_fact_id.get(row["fact_candidate_id"])
        if gate and gate["authorization_validation_status"] == "valid_manifest_validation_only":
            group["operator_authorized_count"] += 1
        else:
            group["authorization_blocked_count"] += 1

    rows: list[dict] = []
    for metric in sorted(groups):
        group = groups[metric]
        candidate_count = group["candidate_count"]
        rows.append({
            "cross_review_group_id": f"OCRXREV-{manifest['run_id']}-{len(rows) + 1:05d}",
            "candidate_metric": metric,
            "candidate_count": str(candidate_count),
            "candidate_amount_total": f"{group['candidate_amount_total']:.2f}",
            "evidence_count": str(len(group["evidence_ids"])),
            "company_present_count": str(group["company_present_count"]),
            "company_missing_count": str(candidate_count - group["company_present_count"]),
            "bank_present_count": str(group["bank_present_count"]),
            "bank_missing_count": str(candidate_count - group["bank_present_count"]),
            "operator_authorized_count": str(group["operator_authorized_count"]),
            "authorization_blocked_count": str(group["authorization_blocked_count"]),
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "review_status": "pending_human_cross_review",
        })
    return rows


def build_ocr_fact_owner_review_batch_rows(manifest: dict, cross_review_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    authorization_relative_path = ocr_fact_review_authorization_relative_path(manifest["run_id"])
    for row in cross_review_rows:
        blocked_count = int(row["authorization_blocked_count"])
        owner_review_status = (
            "blocked_metric_review_required"
            if blocked_count > 0
            else "ready_for_owner_review_no_ledger_promotion"
        )
        rows.append({
            "ocr_fact_owner_review_batch_id": f"OCROWNERBATCH-{manifest['run_id']}-{len(rows) + 1:05d}",
            "cross_review_group_id": row["cross_review_group_id"],
            "candidate_metric": row["candidate_metric"],
            "source_artifact": "ocr_fact_ledger_staging_preview.csv",
            "candidate_count": row["candidate_count"],
            "candidate_amount_total": row["candidate_amount_total"],
            "evidence_count": row["evidence_count"],
            "company_missing_count": row["company_missing_count"],
            "bank_missing_count": row["bank_missing_count"],
            "operator_authorized_count": row["operator_authorized_count"],
            "authorization_blocked_count": row["authorization_blocked_count"],
            "priority": "P0" if blocked_count > 0 else "P1",
            "owner_review_status": owner_review_status,
            "owner_authorization_required": "true" if int(row["candidate_count"]) > 0 else "false",
            "authorization_manifest_relative_path": authorization_relative_path,
            "authorization_scope": "ocr_financial_fact_review_validation_only",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_owner_action": (
                "Review OCR fact candidates by metric, resolve company/bank/evidence gaps, then provide private OCR fact review authorization"
                if blocked_count > 0
                else "Keep reviewed metric batch as no-write evidence"
            ),
        })
    return rows


def build_ocr_fact_evidence_review_queue_rows(manifest: dict, staging_preview_rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str], dict] = {}
    for row in staging_preview_rows:
        key = (row["candidate_metric"], row["source_evidence_id"], row["source_ocr_text_relative_path"])
        group = groups.setdefault(key, {
            "candidate_count": 0,
            "candidate_amount_total": Decimal("0.00"),
            "company_missing_count": 0,
            "bank_missing_count": 0,
            "operator_authorized_count": 0,
            "authorization_blocked_count": 0,
        })
        group["candidate_count"] += 1
        group["candidate_amount_total"] += Decimal(row["amount"])
        if not row["company"]:
            group["company_missing_count"] += 1
        if not row["bank"]:
            group["bank_missing_count"] += 1
        if row["authorization_validation_status"] == "valid_manifest_validation_only":
            group["operator_authorized_count"] += 1
        else:
            group["authorization_blocked_count"] += 1

    rows: list[dict] = []
    authorization_relative_path = ocr_fact_review_authorization_relative_path(manifest["run_id"])
    for candidate_metric, source_evidence_id, source_ocr_text_relative_path in sorted(groups):
        group = groups[(candidate_metric, source_evidence_id, source_ocr_text_relative_path)]
        blocked_count = group["authorization_blocked_count"]
        evidence_review_status = (
            "blocked_evidence_review_required"
            if blocked_count > 0
            else "ready_for_owner_evidence_review_no_ledger_promotion"
        )
        rows.append({
            "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{manifest['run_id']}-{len(rows) + 1:05d}",
            "candidate_metric": candidate_metric,
            "source_evidence_id": source_evidence_id,
            "source_ocr_text_relative_path": source_ocr_text_relative_path,
            "candidate_count": str(group["candidate_count"]),
            "candidate_amount_total": f"{group['candidate_amount_total']:.2f}",
            "company_missing_count": str(group["company_missing_count"]),
            "bank_missing_count": str(group["bank_missing_count"]),
            "operator_authorized_count": str(group["operator_authorized_count"]),
            "authorization_blocked_count": str(blocked_count),
            "priority": "P0" if blocked_count > 0 else "P1",
            "evidence_review_status": evidence_review_status,
            "owner_authorization_required": "true" if group["candidate_count"] > 0 else "false",
            "authorization_manifest_relative_path": authorization_relative_path,
            "authorization_scope": "ocr_financial_fact_review_validation_only",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_owner_action": (
                "Review this evidence-level OCR fact group, resolve company/bank/date/amount gaps, then update candidate-level private OCR fact authorization"
                if blocked_count > 0
                else "Keep evidence group as reviewed no-write support"
            ),
        })
    return rows


def build_ocr_fact_candidate_owner_worklist_rows(
    manifest: dict,
    staging_preview_rows: list[dict],
    evidence_review_queue_rows: list[dict],
) -> list[dict]:
    evidence_queue_by_key = {
        (row["candidate_metric"], row["source_evidence_id"], row["source_ocr_text_relative_path"]): row
        for row in evidence_review_queue_rows
    }
    authorization_relative_path = ocr_fact_review_authorization_relative_path(manifest["run_id"])
    rows: list[dict] = []
    for row in staging_preview_rows:
        evidence_queue = evidence_queue_by_key.get((
            row["candidate_metric"],
            row["source_evidence_id"],
            row["source_ocr_text_relative_path"],
        ))
        ready = row["authorization_validation_status"] == "valid_manifest_validation_only"
        rows.append({
            "owner_worklist_id": f"OCROWNERWORK-{manifest['run_id']}-{len(rows) + 1:05d}",
            "ocr_fact_evidence_review_queue_id": evidence_queue["ocr_fact_evidence_review_queue_id"] if evidence_queue else "",
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "source_evidence_id": row["source_evidence_id"],
            "source_ocr_text_relative_path": row["source_ocr_text_relative_path"],
            "business_date": row["business_date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "amount": row["amount"],
            "currency": row["currency"],
            "proposed_amount_role": row["proposed_amount_role"],
            "proposed_liquidity_tier": row["proposed_liquidity_tier"],
            "proposed_flow_type": row["proposed_flow_type"],
            "authorization_validation_status": row["authorization_validation_status"],
            "staging_preview_status": row["staging_preview_status"],
            "owner_authorization_decision": "pending_owner_review",
            "owner_corrected_company": "",
            "owner_corrected_bank": "",
            "owner_note": "",
            "authorization_manifest_relative_path": authorization_relative_path,
            "authorization_scope": "ocr_financial_fact_review_validation_only",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_owner_action": (
                "Review this OCR fact candidate, fill corrected company/bank/decision externally, then update the private candidate-level OCR fact authorization manifest"
                if not ready
                else "Keep this reviewed OCR fact candidate as no-write support until a separate controlled promotion gate is authorized"
            ),
        })
    return rows


def ocr_fact_candidate_owner_decision_relative_path(run_id: str) -> str:
    return f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json"


def build_ocr_fact_candidate_owner_decision_template(manifest: dict, worklist_rows: list[dict]) -> dict:
    return {
        "decision_manifest_version": "1",
        "run_id": manifest["run_id"],
        "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
        "template_status": "owner_decision_required",
        "template_generated_from": "ocr_fact_candidate_owner_worklist.csv",
        "output_decision_manifest_relative_path": ocr_fact_candidate_owner_decision_relative_path(manifest["run_id"]),
        "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
        "allowed_owner_authorization_decisions": [
            "pending_owner_review",
            "needs_correction",
            "reject_candidate",
            "approve_for_review_authorization",
        ],
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_instruction": "Review each candidate, update owner_authorization_decision and corrected fields, then save a confirmed copy to output_decision_manifest_relative_path. This template does not authorize promotion, write fund_ledger.csv, or produce management conclusions.",
        "owner_decisions": [
            {
                "owner_worklist_id": row["owner_worklist_id"],
                "ocr_fact_evidence_review_queue_id": row["ocr_fact_evidence_review_queue_id"],
                "fact_candidate_id": row["fact_candidate_id"],
                "candidate_metric": row["candidate_metric"],
                "business_date": row["business_date"],
                "company": row["company"],
                "bank": row["bank"],
                "account_alias": row["account_alias"],
                "amount": row["amount"],
                "currency": row["currency"],
                "owner_authorization_decision": "pending_owner_review",
                "owner_corrected_company": "",
                "owner_corrected_bank": "",
                "owner_note": "",
            }
            for row in worklist_rows
        ],
    }


def load_ocr_fact_candidate_owner_decision_manifest(repo_root: Path, run_id: str) -> dict:
    relative_path = ocr_fact_candidate_owner_decision_relative_path(run_id)
    missing = {
        "relative_path": relative_path,
        "status": "missing_decision_manifest",
        "entries": {},
    }
    path = repo_root / relative_path
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_decision_manifest_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_decision_manifest_schema"}
    required = {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
        "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_decision_manifest_schema"}
    raw_entries = payload.get("owner_decisions")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_decision_manifest_schema"}
    allowed_decisions = {
        "pending_owner_review",
        "needs_correction",
        "reject_candidate",
        "approve_for_review_authorization",
    }
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_decision_manifest_schema"}
        fact_candidate_id = entry.get("fact_candidate_id")
        candidate_metric = entry.get("candidate_metric")
        owner_decision = entry.get("owner_authorization_decision")
        if not isinstance(fact_candidate_id, str) or not fact_candidate_id:
            return {**missing, "status": "invalid_decision_manifest_schema"}
        if not isinstance(candidate_metric, str) or not candidate_metric:
            return {**missing, "status": "invalid_decision_manifest_schema"}
        if owner_decision not in allowed_decisions:
            return {**missing, "status": "invalid_decision_manifest_schema"}
        entries[fact_candidate_id] = {
            "candidate_metric": candidate_metric,
            "owner_authorization_decision": owner_decision,
            "owner_corrected_company": str(entry.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(entry.get("owner_corrected_bank", "")),
            "owner_note": str(entry.get("owner_note", "")),
        }
    return {
        "relative_path": relative_path,
        "status": "valid_decision_manifest",
        "entries": entries,
    }


def ocr_fact_candidate_owner_decision_status(row: dict, decision_manifest: dict) -> tuple[str, str, dict]:
    if decision_manifest["status"] == "missing_decision_manifest":
        return (
            "missing_decision_manifest",
            "blocked_missing_owner_decision_manifest",
            {
                "owner_authorization_decision": "pending_owner_review",
                "owner_corrected_company": "",
                "owner_corrected_bank": "",
                "owner_note": "",
            },
        )
    if decision_manifest["status"] != "valid_decision_manifest":
        return (
            decision_manifest["status"],
            "blocked_invalid_owner_decision_manifest",
            {
                "owner_authorization_decision": "pending_owner_review",
                "owner_corrected_company": "",
                "owner_corrected_bank": "",
                "owner_note": "",
            },
        )
    entry = decision_manifest["entries"].get(row["fact_candidate_id"])
    if entry is None:
        return "fact_candidate_owner_decision_missing", "blocked_missing_candidate_owner_decision", {
            "owner_authorization_decision": "pending_owner_review",
            "owner_corrected_company": "",
            "owner_corrected_bank": "",
            "owner_note": "",
        }
    if entry["candidate_metric"] != row["candidate_metric"]:
        return "owner_decision_candidate_metric_mismatch", "blocked_owner_decision_metric_mismatch", entry
    owner_decision = entry["owner_authorization_decision"]
    if owner_decision == "approve_for_review_authorization":
        return "valid_owner_decision_validation_only", "ready_for_private_ocr_fact_authorization_update_no_write", entry
    if owner_decision == "reject_candidate":
        return "owner_rejected_candidate", "blocked_owner_rejected_candidate_no_write", entry
    if owner_decision == "needs_correction":
        return "owner_decision_needs_correction", "blocked_owner_decision_needs_correction", entry
    return "owner_decision_pending", "blocked_owner_decision_pending", entry


def build_ocr_fact_candidate_owner_decision_preview_rows(
    manifest: dict,
    repo_root: Path,
    worklist_rows: list[dict],
) -> list[dict]:
    decision_manifest = load_ocr_fact_candidate_owner_decision_manifest(repo_root, manifest["run_id"])
    rows: list[dict] = []
    for row in worklist_rows:
        validation_status, preview_status, decision = ocr_fact_candidate_owner_decision_status(row, decision_manifest)
        rows.append({
            "decision_preview_id": f"OCROWNERDECISION-{manifest['run_id']}-{len(rows) + 1:05d}",
            "owner_worklist_id": row["owner_worklist_id"],
            "ocr_fact_evidence_review_queue_id": row["ocr_fact_evidence_review_queue_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "decision_manifest_relative_path": decision_manifest["relative_path"],
            "decision_validation_status": validation_status,
            "decision_preview_status": preview_status,
            "owner_authorization_decision": decision["owner_authorization_decision"],
            "owner_corrected_company": decision["owner_corrected_company"],
            "owner_corrected_bank": decision["owner_corrected_bank"],
            "owner_note": decision["owner_note"],
            "authorization_manifest_relative_path": row["authorization_manifest_relative_path"],
            "authorization_scope": row["authorization_scope"],
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": (
                "Use this approved owner decision to update the private OCR fact review authorization manifest; do not promote or write ledger in this step."
                if preview_status == "ready_for_private_ocr_fact_authorization_update_no_write"
                else "Resolve owner decision status before updating private OCR fact authorization."
            ),
        })
    return rows


def build_ocr_fact_candidate_owner_decision_progress_summary_rows(
    manifest: dict,
    decision_preview_rows: list[dict],
) -> list[dict]:
    def summarize(summary_level: str, candidate_metric: str, rows: list[dict]) -> dict:
        ready_count = sum(
            1 for row in rows
            if row["decision_preview_status"] == "ready_for_private_ocr_fact_authorization_update_no_write"
        )
        missing_manifest_count = sum(
            1 for row in rows
            if row["decision_validation_status"] == "missing_decision_manifest"
        )
        pending_count = sum(
            1 for row in rows
            if row["owner_authorization_decision"] == "pending_owner_review"
        )
        approved_count = sum(
            1 for row in rows
            if row["owner_authorization_decision"] == "approve_for_review_authorization"
        )
        correction_count = sum(
            1 for row in rows
            if row["owner_authorization_decision"] == "needs_correction"
        )
        rejected_count = sum(
            1 for row in rows
            if row["owner_authorization_decision"] == "reject_candidate"
        )
        missing_company_count = sum(1 for row in rows if not row["owner_corrected_company"])
        missing_bank_count = sum(1 for row in rows if not row["owner_corrected_bank"])
        next_step = (
            "Owner decision coverage is ready for private authorization preview; keep this step no-write."
            if rows and ready_count == len(rows)
            else "Complete the private owner decision manifest before any OCR fact authorization update."
        )
        return {
            "progress_summary_id": f"OCROWNERDECISIONPROGRESS-{manifest['run_id']}-{summary_level}-{candidate_metric}",
            "summary_level": summary_level,
            "candidate_metric": candidate_metric,
            "candidate_count": str(len(rows)),
            "ready_count": str(ready_count),
            "blocking_count": str(len(rows) - ready_count),
            "missing_owner_decision_manifest_count": str(missing_manifest_count),
            "pending_owner_review_count": str(pending_count),
            "approved_for_authorization_count": str(approved_count),
            "needs_correction_count": str(correction_count),
            "rejected_count": str(rejected_count),
            "missing_company_count": str(missing_company_count),
            "missing_bank_count": str(missing_bank_count),
            "authorization_update_ready_count": str(ready_count),
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        }

    rows = [summarize("all_candidates", "ALL", decision_preview_rows)]
    for candidate_metric in sorted({row["candidate_metric"] for row in decision_preview_rows}):
        metric_rows = [row for row in decision_preview_rows if row["candidate_metric"] == candidate_metric]
        rows.append(summarize("candidate_metric", candidate_metric, metric_rows))
    return rows


def build_ocr_fact_candidate_owner_authorization_update_draft(
    manifest: dict,
    decision_preview_rows: list[dict],
) -> dict:
    approved_rows = [
        row for row in decision_preview_rows
        if row["decision_preview_status"] == "ready_for_private_ocr_fact_authorization_update_no_write"
    ]
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "ocr_financial_fact_review_validation_only",
        "draft_status": "owner_decision_approved_authorization_update_draft",
        "generated_from": "ocr_fact_candidate_owner_decision_preview.csv",
        "output_authorization_manifest_relative_path": ocr_fact_review_authorization_relative_path(manifest["run_id"]),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "operator_instruction": "Review this draft before saving it as the private OCR fact review authorization manifest. This draft is no-write and does not promote facts, write fund_ledger.csv, or produce management conclusions.",
        "fact_candidate_authorizations": [
            {
                "fact_candidate_id": row["fact_candidate_id"],
                "candidate_metric": row["candidate_metric"],
                "authorized": True,
                "owner_corrected_company": row["owner_corrected_company"],
                "owner_corrected_bank": row["owner_corrected_bank"],
                "operator_note": row["owner_note"],
                "source_decision_preview_id": row["decision_preview_id"],
            }
            for row in approved_rows
        ],
    }


def build_ocr_fact_candidate_owner_authorization_update_preview_rows(
    manifest: dict,
    decision_preview_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    authorization_relative_path = ocr_fact_review_authorization_relative_path(manifest["run_id"])
    for row in decision_preview_rows:
        approved = row["decision_preview_status"] == "ready_for_private_ocr_fact_authorization_update_no_write"
        rows.append({
            "authorization_update_preview_id": f"OCROWNERAUTHUPDATE-{manifest['run_id']}-{len(rows) + 1:05d}",
            "decision_preview_id": row["decision_preview_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "owner_authorization_decision": row["owner_authorization_decision"],
            "decision_preview_status": row["decision_preview_status"],
            "authorization_update_preview_status": (
                "ready_for_private_ocr_fact_authorization_manifest_update_no_write"
                if approved
                else "blocked_owner_decision_not_approved"
            ),
            "authorization_manifest_relative_path": authorization_relative_path,
            "authorization_update_allowed": "false",
            "draft_authorized_value": "true" if approved else "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": (
                "Review the generated authorization update draft, then save it to the private OCR fact review authorization path if owner approval is confirmed."
                if approved
                else "Resolve owner decision approval before adding this candidate to the private OCR fact review authorization draft."
            ),
        })
    return rows


def ocr_fact_proposed_ledger_role(candidate_metric: str) -> tuple[str, str, str]:
    mapping = {
        "bank_deposit": ("balance", "bank_deposit", "balance_snapshot_pending_review"),
        "electronic_bill": ("balance", "electronic_bill", "bill_balance_snapshot_pending_review"),
        "payment_outflow": ("outflow", "bank_cash", "payment_outflow_pending_review"),
        "tax_payment": ("outflow", "bank_cash", "tax_payment_pending_review"),
        "deposit_release": ("inflow", "deposit_release", "deposit_release_pending_review"),
        "loan": ("financing_or_balance_review", "loan", "loan_fact_pending_review"),
    }
    return mapping.get(candidate_metric, ("unclassified_review", "unclassified", "unclassified_pending_review"))


def ocr_fact_ledger_staging_status(gate_row: dict | None) -> str:
    if gate_row and gate_row["authorization_validation_status"] == "valid_manifest_validation_only":
        return "ready_for_ledger_staging_review_no_write"
    if not gate_row:
        return "blocked_missing_review_gate"
    if gate_row["authorization_validation_status"] in {"fact_candidate_not_authorized", "fact_candidate_authorization_not_true"}:
        return "blocked_fact_candidate_not_authorized"
    return gate_row["review_gate_status"]


def build_ocr_fact_ledger_staging_preview(
    manifest: dict,
    fact_candidates: list[dict],
    review_gate_rows: list[dict],
) -> list[dict]:
    gate_by_fact_id = {row["fact_candidate_id"]: row for row in review_gate_rows}
    rows: list[dict] = []
    for row in fact_candidates:
        gate = gate_by_fact_id.get(row["fact_candidate_id"])
        amount_role, liquidity_tier, flow_type = ocr_fact_proposed_ledger_role(row["candidate_metric"])
        rows.append({
            "staging_preview_id": f"OCRLEDGERPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "business_date": row["business_date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "amount": row["amount"],
            "currency": row["currency"],
            "proposed_amount_role": amount_role,
            "proposed_liquidity_tier": liquidity_tier,
            "proposed_flow_type": flow_type,
            "source_evidence_id": row["evidence_id"],
            "source_ocr_text_relative_path": row["ocr_text_relative_path"],
            "authorization_validation_status": gate["authorization_validation_status"] if gate else "missing_review_gate",
            "staging_preview_status": ocr_fact_ledger_staging_status(gate),
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "review_status": "pending_human_ledger_staging_review",
        })
    return rows


def build_ocr_fact_controlled_ledger_row_preview_rows(
    manifest: dict,
    staging_preview_rows: list[dict],
    decision_preview_rows: list[dict],
) -> list[dict]:
    decision_by_fact_id = {row["fact_candidate_id"]: row for row in decision_preview_rows}
    rows: list[dict] = []
    for row in staging_preview_rows:
        if row["staging_preview_status"] != "ready_for_ledger_staging_review_no_write":
            continue
        decision = decision_by_fact_id.get(row["fact_candidate_id"], {})
        decision_ready = decision.get("decision_preview_status") == "ready_for_private_ocr_fact_authorization_update_no_write"
        owner_company = str(decision.get("owner_corrected_company", "")).strip() if decision_ready else ""
        owner_bank = str(decision.get("owner_corrected_bank", "")).strip() if decision_ready else ""
        company = owner_company or row["company"]
        bank = owner_bank or row["bank"]
        amount = row["amount"]
        proposed_amount_role = row["proposed_amount_role"]
        inflow = amount if proposed_amount_role == "inflow" else ""
        outflow = amount if proposed_amount_role == "outflow" else ""
        ending_balance = amount if proposed_amount_role == "balance" else ""
        rows.append({
            "controlled_ledger_preview_id": f"OCRLEDGERROWPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "staging_preview_id": row["staging_preview_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "date": row["business_date"],
            "company": company,
            "bank": bank,
            "account_alias": row["account_alias"],
            "liquidity_tier": row["proposed_liquidity_tier"],
            "inflow": inflow,
            "outflow": outflow,
            "ending_balance": ending_balance,
            "amount": amount,
            "currency": row["currency"],
            "flow_type": row["proposed_flow_type"],
            "source_evidence_id": row["source_evidence_id"],
            "source_ocr_text_relative_path": row["source_ocr_text_relative_path"],
            "authorization_validation_status": row["authorization_validation_status"],
            "owner_decision_preview_id": decision.get("decision_preview_id", ""),
            "owner_decision_preview_status": decision.get("decision_preview_status", ""),
            "owner_correction_applied": "true" if owner_company or owner_bank else "false",
            "company_source": "owner_decision_preview" if owner_company else "ocr_fact_candidate",
            "bank_source": "owner_decision_preview" if owner_bank else "ocr_fact_candidate",
            "ledger_preview_status": "ready_for_controlled_ledger_apply_gate_no_write",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "review_status": "pending_controlled_ledger_apply_gate",
        })
    return rows


def build_ocr_fact_controlled_ledger_apply_gate_rows(
    manifest: dict,
    controlled_ledger_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for row in controlled_ledger_rows:
        missing_fields = [
            field
            for field in ("date", "company", "bank", "liquidity_tier", "currency", "flow_type")
            if not str(row.get(field, "")).strip()
        ]
        if not any(str(row.get(field, "")).strip() for field in ("inflow", "outflow", "ending_balance")):
            missing_fields.append("inflow_or_outflow_or_ending_balance")
        if row["ledger_preview_status"] != "ready_for_controlled_ledger_apply_gate_no_write":
            apply_gate_status = "blocked_ledger_preview_not_ready"
            planned_apply_count = 0
            gate_reason = "Controlled ledger row preview is not ready for the controlled ledger apply gate."
            review_status = "pending_controlled_ledger_preview_resolution"
        elif missing_fields:
            apply_gate_status = "blocked_missing_required_ledger_fields"
            planned_apply_count = 0
            gate_reason = f"Missing required ledger fields before formal ledger apply: {','.join(missing_fields)}"
            review_status = "pending_required_ledger_field_resolution"
        else:
            apply_gate_status = "ready_for_controlled_ledger_apply_no_write"
            planned_apply_count = 1
            gate_reason = (
                "Controlled ledger preview has required ledger fields, but this runner still performs no "
                "fund ledger write, no formal ledger write, and no management conclusion."
            )
            review_status = "pending_controlled_ledger_apply_review"
        rows.append({
            "controlled_ledger_apply_gate_id": f"OCRLEDGERAPPLY-{manifest['run_id']}-{len(rows) + 1:05d}",
            "controlled_ledger_preview_id": row["controlled_ledger_preview_id"],
            "staging_preview_id": row["staging_preview_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "date": row["date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "inflow": row["inflow"],
            "outflow": row["outflow"],
            "ending_balance": row["ending_balance"],
            "amount": row["amount"],
            "currency": row["currency"],
            "flow_type": row["flow_type"],
            "source_evidence_id": row["source_evidence_id"],
            "source_ocr_text_relative_path": row["source_ocr_text_relative_path"],
            "authorization_validation_status": row["authorization_validation_status"],
            "owner_decision_preview_id": row["owner_decision_preview_id"],
            "owner_decision_preview_status": row["owner_decision_preview_status"],
            "owner_correction_applied": row["owner_correction_applied"],
            "company_source": row["company_source"],
            "bank_source": row["bank_source"],
            "ledger_preview_status": row["ledger_preview_status"],
            "apply_gate_status": apply_gate_status,
            "planned_apply_count": str(planned_apply_count),
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "gate_reason": gate_reason,
            "review_status": review_status,
        })
    return rows


def build_ocr_fact_owner_decision_correction_queue_rows(
    manifest: dict,
    apply_gate_rows: list[dict],
) -> list[dict]:
    owner_field_by_missing_field = {
        "company": "owner_corrected_company",
        "bank": "owner_corrected_bank",
    }
    rows: list[dict] = []
    owner_decision_manifest_relative_path = ocr_fact_candidate_owner_decision_relative_path(manifest["run_id"])
    for row in apply_gate_rows:
        if row["apply_gate_status"] != "blocked_missing_required_ledger_fields":
            continue
        missing_required_fields = row["gate_reason"].split(":", 1)[-1].strip()
        missing_fields = [field.strip() for field in missing_required_fields.split(",") if field.strip()]
        required_owner_fields = [
            owner_field_by_missing_field.get(field, f"unsupported_owner_correction_for_{field}")
            for field in missing_fields
        ]
        rows.append({
            "correction_queue_id": f"OCROWNERFIX-{manifest['run_id']}-{len(rows) + 1:05d}",
            "controlled_ledger_apply_gate_id": row["controlled_ledger_apply_gate_id"],
            "controlled_ledger_preview_id": row["controlled_ledger_preview_id"],
            "staging_preview_id": row["staging_preview_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "missing_required_fields": ",".join(missing_fields),
            "required_owner_fields": ",".join(required_owner_fields),
            "current_date": row["date"],
            "current_company": row["company"],
            "current_bank": row["bank"],
            "current_account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "amount": row["amount"],
            "currency": row["currency"],
            "flow_type": row["flow_type"],
            "source_evidence_id": row["source_evidence_id"],
            "source_ocr_text_relative_path": row["source_ocr_text_relative_path"],
            "owner_decision_manifest_relative_path": owner_decision_manifest_relative_path,
            "owner_decision_preview_status": row["owner_decision_preview_status"],
            "owner_correction_applied": row["owner_correction_applied"],
            "correction_queue_status": "blocked_owner_correction_required",
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": (
                "Update the private owner decision manifest with the required owner-corrected fields, then rerun the no-write controlled ledger apply gate."
            ),
        })
    return rows


def build_ocr_fact_owner_decision_correction_evidence_packet_rows(
    manifest: dict,
    correction_queue_rows: list[dict],
    fact_candidates: list[dict],
    evidence_rows: list[dict],
) -> list[dict]:
    fact_by_id = {row["fact_candidate_id"]: row for row in fact_candidates}
    evidence_by_id = {row["evidence_id"]: row for row in evidence_rows}
    rows: list[dict] = []
    for row in correction_queue_rows:
        fact = fact_by_id.get(row["fact_candidate_id"], {})
        evidence = evidence_by_id.get(row["source_evidence_id"], {})
        if fact and evidence:
            packet_status = "ready_for_owner_field_review_no_write"
            next_step = "Review the real evidence context, fill owner-corrected fields externally, then save a private owner decision manifest if confirmed."
        elif not fact:
            packet_status = "blocked_missing_fact_candidate_context"
            next_step = "Rerun OCR fact candidate extraction before owner field review."
        else:
            packet_status = "blocked_missing_evidence_index_context"
            next_step = "Rerun evidence indexing before owner field review."
        decision_fragment = {
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "owner_authorization_decision": "needs_correction",
            "owner_corrected_company": row["current_company"],
            "owner_corrected_bank": row["current_bank"],
            "required_owner_fields": row["required_owner_fields"],
            "owner_note": "Review correction evidence packet before changing owner_authorization_decision to approve_for_review_authorization.",
        }
        rows.append({
            "evidence_packet_id": f"OCROWNERFIXEVID-{manifest['run_id']}-{len(rows) + 1:05d}",
            "source_correction_queue_id": row["correction_queue_id"],
            "source_controlled_ledger_apply_gate_id": row["controlled_ledger_apply_gate_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "missing_required_fields": row["missing_required_fields"],
            "required_owner_fields": row["required_owner_fields"],
            "current_date": row["current_date"],
            "current_company": row["current_company"],
            "current_bank": row["current_bank"],
            "candidate_business_date": fact.get("business_date", row["current_date"]),
            "candidate_amount": fact.get("amount", row["amount"]),
            "candidate_currency": fact.get("currency", row["currency"]),
            "candidate_line_number": fact.get("line_number", ""),
            "candidate_line_text_excerpt": fact.get("line_text_excerpt", ""),
            "source_evidence_id": row["source_evidence_id"],
            "source_evidence_relative_path": evidence.get("relative_path", ""),
            "source_image_relative_path": fact.get("source_image_relative_path", evidence.get("relative_path", "")),
            "source_ocr_text_relative_path": row["source_ocr_text_relative_path"],
            "owner_decision_manifest_relative_path": row["owner_decision_manifest_relative_path"],
            "owner_decision_json_fragment": json.dumps(decision_fragment, ensure_ascii=False, separators=(",", ":")),
            "evidence_packet_status": packet_status,
            "owner_decision_manifest_write_allowed": "false",
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        })
    return rows


def build_ocr_fact_owner_decision_correction_ocr_line_context_rows(
    manifest: dict,
    input_dir: Path,
    repo_root: Path,
    evidence_packet_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for packet in evidence_packet_rows:
        relative_path = packet.get("source_ocr_text_relative_path", "")
        target_line_number = packet.get("candidate_line_number", "")
        target_line_number_int = int(target_line_number) if target_line_number.isdigit() else 0
        text_lines: list[str] = []
        context_status = "ready_ocr_line_context_no_write"
        next_step = "Use neighboring OCR text lines as owner-review context only; do not autofill company or bank."
        if not relative_path or not target_line_number_int:
            context_status = "blocked_missing_target_ocr_line_context"
            next_step = "Rerun OCR fact extraction before owner field review; do not autofill company or bank."
        else:
            try:
                text_path = resolve_ocr_text_path(repo_root, input_dir, relative_path)
                text_lines = text_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except OSError:
                context_status = "blocked_missing_ocr_text_sidecar"
                next_step = "Restore or regenerate the OCR text sidecar before owner field review; do not autofill company or bank."
            if text_lines and (target_line_number_int < 1 or target_line_number_int > len(text_lines)):
                context_status = "blocked_target_ocr_line_out_of_range"
                next_step = "Rerun OCR fact extraction to align candidate line numbers before owner field review."
        if context_status != "ready_ocr_line_context_no_write":
            rows.append({
                "ocr_line_context_id": f"OCROWNERFIXOCRLINE-{manifest['run_id']}-{len(rows) + 1:05d}",
                "source_evidence_packet_id": packet.get("evidence_packet_id", ""),
                "source_correction_queue_id": packet.get("source_correction_queue_id", ""),
                "fact_candidate_id": packet.get("fact_candidate_id", ""),
                "candidate_metric": packet.get("candidate_metric", ""),
                "source_evidence_id": packet.get("source_evidence_id", ""),
                "source_image_relative_path": packet.get("source_image_relative_path", ""),
                "source_ocr_text_relative_path": relative_path,
                "target_ocr_line_number": target_line_number,
                "ocr_line_number": "",
                "ocr_line_offset": "",
                "ocr_line_text_excerpt": "",
                "ocr_line_context_radius": str(OCR_LINE_CONTEXT_RADIUS),
                "ocr_line_context_status": context_status,
                "owner_field_autofill_allowed": "false",
                "owner_decision_manifest_write_allowed": "false",
                "source_mutation_allowed": "false",
                "fund_ledger_write_allowed": "false",
                "formal_fund_ledger_write_allowed": "false",
                "financial_fact_promoted": "false",
                "management_conclusion_allowed": "false",
                "recommended_next_step": next_step,
            })
            continue
        for ocr_line_number in range(
            max(1, target_line_number_int - OCR_LINE_CONTEXT_RADIUS),
            min(len(text_lines), target_line_number_int + OCR_LINE_CONTEXT_RADIUS) + 1,
        ):
            rows.append({
                "ocr_line_context_id": f"OCROWNERFIXOCRLINE-{manifest['run_id']}-{len(rows) + 1:05d}",
                "source_evidence_packet_id": packet.get("evidence_packet_id", ""),
                "source_correction_queue_id": packet.get("source_correction_queue_id", ""),
                "fact_candidate_id": packet.get("fact_candidate_id", ""),
                "candidate_metric": packet.get("candidate_metric", ""),
                "source_evidence_id": packet.get("source_evidence_id", ""),
                "source_image_relative_path": packet.get("source_image_relative_path", ""),
                "source_ocr_text_relative_path": relative_path,
                "target_ocr_line_number": target_line_number,
                "ocr_line_number": str(ocr_line_number),
                "ocr_line_offset": str(ocr_line_number - target_line_number_int),
                "ocr_line_text_excerpt": text_excerpt(text_lines[ocr_line_number - 1]),
                "ocr_line_context_radius": str(OCR_LINE_CONTEXT_RADIUS),
                "ocr_line_context_status": "ready_ocr_line_context_no_write",
                "owner_field_autofill_allowed": "false",
                "owner_decision_manifest_write_allowed": "false",
                "source_mutation_allowed": "false",
                "fund_ledger_write_allowed": "false",
                "formal_fund_ledger_write_allowed": "false",
                "financial_fact_promoted": "false",
                "management_conclusion_allowed": "false",
                "recommended_next_step": next_step,
            })
    return rows


def build_ocr_fact_owner_decision_correction_draft(
    manifest: dict,
    correction_queue_rows: list[dict],
) -> dict:
    return {
        "decision_manifest_version": "1",
        "run_id": manifest["run_id"],
        "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
        "draft_status": "owner_decision_correction_manifest_draft",
        "generated_from": "ocr_fact_owner_decision_correction_queue.csv",
        "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
        "output_decision_manifest_relative_path": ocr_fact_candidate_owner_decision_relative_path(manifest["run_id"]),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "operator_instruction": (
            "Review and complete this draft before saving it as the private owner decision manifest. "
            "This draft is no-write and does not promote facts, write fund_ledger.csv, write formal_fund_ledger.csv, or produce management conclusions."
        ),
        "owner_decisions": [
            {
                "fact_candidate_id": row["fact_candidate_id"],
                "candidate_metric": row["candidate_metric"],
                "owner_authorization_decision": "needs_correction",
                "owner_corrected_company": row["current_company"],
                "owner_corrected_bank": row["current_bank"],
                "required_owner_fields": row["required_owner_fields"],
                "missing_required_fields": row["missing_required_fields"],
                "owner_note": "Complete required owner-corrected fields, then change owner_authorization_decision to approve_for_review_authorization if the candidate is approved.",
                "source_correction_queue_id": row["correction_queue_id"],
                "source_controlled_ledger_apply_gate_id": row["controlled_ledger_apply_gate_id"],
            }
            for row in correction_queue_rows
        ],
    }


def build_ocr_fact_owner_decision_correction_apply_preview_rows(
    manifest: dict,
    correction_draft: dict,
) -> list[dict]:
    rows: list[dict] = []
    output_manifest_path = correction_draft["output_decision_manifest_relative_path"]
    for decision in correction_draft["owner_decisions"]:
        required_owner_fields = [
            field.strip()
            for field in str(decision.get("required_owner_fields", "")).split(",")
            if field.strip()
        ]
        missing_owner_values = [
            field for field in required_owner_fields
            if not str(decision.get(field, "")).strip()
        ]
        if missing_owner_values:
            preview_status = "blocked_draft_still_needs_owner_values"
            manual_save_ready = "false"
            next_step = "Fill the missing owner-corrected values in the draft before saving a private owner decision manifest."
        elif decision["owner_authorization_decision"] != "approve_for_review_authorization":
            preview_status = "blocked_draft_owner_decision_not_approved"
            manual_save_ready = "false"
            next_step = "Change owner_authorization_decision to approve_for_review_authorization only after owner review confirms this candidate."
        else:
            preview_status = "ready_for_private_owner_decision_manifest_manual_save_no_write"
            manual_save_ready = "true"
            next_step = "Owner may manually save this reviewed decision to the private owner decision manifest path, then rerun validation."
        rows.append({
            "correction_apply_preview_id": f"OCROWNERFIXAPPLY-{manifest['run_id']}-{len(rows) + 1:05d}",
            "source_correction_queue_id": decision["source_correction_queue_id"],
            "source_controlled_ledger_apply_gate_id": decision["source_controlled_ledger_apply_gate_id"],
            "fact_candidate_id": decision["fact_candidate_id"],
            "candidate_metric": decision["candidate_metric"],
            "draft_owner_authorization_decision": decision["owner_authorization_decision"],
            "required_owner_fields": ",".join(required_owner_fields),
            "missing_owner_values": ",".join(missing_owner_values),
            "owner_corrected_company": decision["owner_corrected_company"],
            "owner_corrected_bank": decision["owner_corrected_bank"],
            "output_decision_manifest_relative_path": output_manifest_path,
            "correction_apply_preview_status": preview_status,
            "manual_save_ready": manual_save_ready,
            "owner_decision_manifest_write_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        })
    return rows


def build_ocr_fact_owner_decision_correction_roundtrip_audit_rows(
    manifest: dict,
    apply_gate_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for row in apply_gate_rows:
        correction_applied = row["owner_correction_applied"] == "true"
        apply_ready = row["apply_gate_status"] == "ready_for_controlled_ledger_apply_no_write"
        if correction_applied and apply_ready:
            roundtrip_status = "owner_correction_resolved_apply_gate_ready_no_write"
            next_step = "Owner correction has resolved required ledger fields; keep this as no-write evidence until a separate controlled ledger execution is authorized."
        elif correction_applied:
            roundtrip_status = "owner_correction_present_apply_gate_still_blocked"
            next_step = "Owner correction is present but the controlled ledger apply gate is still blocked; resolve remaining required ledger fields before any execution authorization."
        elif apply_ready:
            roundtrip_status = "no_owner_correction_required_apply_gate_ready_no_write"
            next_step = "No owner correction was required for this row; keep this as no-write controlled ledger readiness evidence."
        else:
            roundtrip_status = "blocked_owner_correction_required"
            next_step = "Provide missing owner-corrected fields in the private owner decision manifest, then rerun validation."
        rows.append({
            "correction_roundtrip_audit_id": f"OCROWNERFIXROUNDTRIP-{manifest['run_id']}-{len(rows) + 1:05d}",
            "controlled_ledger_apply_gate_id": row["controlled_ledger_apply_gate_id"],
            "controlled_ledger_preview_id": row["controlled_ledger_preview_id"],
            "fact_candidate_id": row["fact_candidate_id"],
            "candidate_metric": row["candidate_metric"],
            "date": row["date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "amount": row["amount"],
            "currency": row["currency"],
            "flow_type": row["flow_type"],
            "owner_decision_preview_id": row["owner_decision_preview_id"],
            "owner_decision_preview_status": row["owner_decision_preview_status"],
            "owner_correction_applied": row["owner_correction_applied"],
            "company_source": row["company_source"],
            "bank_source": row["bank_source"],
            "apply_gate_status": row["apply_gate_status"],
            "planned_apply_count": row["planned_apply_count"],
            "correction_roundtrip_status": roundtrip_status,
            "owner_decision_manifest_write_allowed": "false",
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        })
    return rows


def chat_record_source_paths(manifest: dict) -> list[str]:
    return [
        item["relative_path"]
        for item in manifest["files"]
        if item["relative_path"].replace("\\", "/").endswith("chat_records/chat_records.csv")
    ]


def manifest_source_paths(manifest: dict) -> list[str]:
    return [
        item["relative_path"]
        for item in manifest["files"]
        if item["relative_path"].replace("\\", "/").endswith("_manifest/manifest.csv")
    ]


def normalize_manifest_output_path(output_path: str, input_dir: Path) -> str:
    normalized = (output_path or "").replace("\\", "/").strip()
    if not normalized:
        return ""
    parts = [part for part in normalized.split("/") if part]
    group_name = input_dir.name
    if group_name in parts:
        group_index = len(parts) - 1 - list(reversed(parts)).index(group_name)
        return "/".join(parts[group_index + 1:])
    return "/".join(parts)


def collect_chat_text_candidates(manifest: dict, input_dir: Path, evidence: list[dict]) -> list[dict]:
    evidence_by_path = {row["relative_path"]: row for row in evidence}
    rows: list[dict] = []
    for relative_path in chat_record_source_paths(manifest):
        evidence_row = evidence_by_path.get(relative_path)
        if evidence_row is None:
            continue
        csv_path = input_dir / relative_path
        with csv_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_index, row in enumerate(reader, 2):
                for text_role in ("content", "quoted_content"):
                    raw_text = (row.get(text_role) or "").strip()
                    if not raw_text or not text_has_finance_signal(raw_text):
                        continue
                    evidence_row["review_status"] = "chat_text_candidate_pending_review"
                    rows.append({
                        "chat_text_candidate_id": f"CHAT-{manifest['run_id']}-{len(rows) + 1:05d}",
                        "evidence_id": evidence_row["evidence_id"],
                        "source_csv_relative_path": relative_path,
                        "source_row_number": str(row_index),
                        "open_message_id": row.get("open_message_id") or row.get("message_id") or "",
                        "message_time": row.get("message_time") or "",
                        "sender_name": row.get("sender_name") or "",
                        "text_role": text_role,
                        "text_sha256": text_sha256(raw_text),
                        "text_length": str(len(raw_text)),
                        "text_excerpt": text_excerpt(raw_text),
                        "extraction_status": "chat_text_indexed_pending_review",
                        "review_status": "pending_human_review",
                        "financial_fact_promoted": "false",
                        "_raw_text": raw_text,
                    })
    return rows


def extract_chat_value_candidates(manifest: dict, chat_text_candidates: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for candidate in chat_text_candidates:
        text = candidate.get("_raw_text", "")
        if not text:
            continue
        date_spans: list[tuple[int, int]] = []
        for match in OCR_DATE_PATTERN.finditer(text):
            date_spans.append(match.span())
            rows.append({
                "value_candidate_id": f"CHATV-{manifest['run_id']}-{len(rows) + 1:05d}",
                "chat_text_candidate_id": candidate["chat_text_candidate_id"],
                "evidence_id": candidate["evidence_id"],
                "source_csv_relative_path": candidate["source_csv_relative_path"],
                "source_row_number": candidate["source_row_number"],
                "candidate_type": "date",
                "raw_value": match.group(0),
                "normalized_value": normalize_ocr_date(match.group(0)),
                "currency": "",
                "text_role": candidate["text_role"],
                "line_text": text_excerpt(text),
                "extraction_status": "chat_value_candidate_pending_review",
                "review_status": "pending_human_review",
                "financial_fact_promoted": "false",
            })
        if not any(word in text for word in OCR_AMOUNT_CONTEXT_WORDS):
            continue
        for match in OCR_AMOUNT_PATTERN.finditer(text):
            if any(start <= match.start() < end for start, end in date_spans):
                continue
            raw_value = match.group(0)
            if "." not in raw_value and "￥" not in raw_value and "¥" not in raw_value and "," not in raw_value:
                continue
            rows.append({
                "value_candidate_id": f"CHATV-{manifest['run_id']}-{len(rows) + 1:05d}",
                "chat_text_candidate_id": candidate["chat_text_candidate_id"],
                "evidence_id": candidate["evidence_id"],
                "source_csv_relative_path": candidate["source_csv_relative_path"],
                "source_row_number": candidate["source_row_number"],
                "candidate_type": "amount",
                "raw_value": raw_value,
                "normalized_value": normalize_ocr_amount(raw_value),
                "currency": "CNY",
                "text_role": candidate["text_role"],
                "line_text": text_excerpt(text),
                "extraction_status": "chat_value_candidate_pending_review",
                "review_status": "pending_human_review",
                "financial_fact_promoted": "false",
            })
    return rows


def collect_manifest_resource_rows(manifest: dict, input_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for relative_path in manifest_source_paths(manifest):
        csv_path = input_dir / relative_path
        with csv_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_index, row in enumerate(reader, 2):
                message_id = row.get("message_id") or row.get("open_message_id") or ""
                if not message_id:
                    continue
                rows.append({
                    "manifest_relative_path": relative_path,
                    "manifest_row_number": str(row_index),
                    "open_message_id": message_id,
                    "message_time": row.get("message_time") or "",
                    "sender_name": row.get("sender_name") or "",
                    "msg_type": row.get("msg_type") or "",
                    "resource_type": row.get("resource_type") or "",
                    "resource_id": row.get("resource_id") or "",
                    "status": row.get("status") or "",
                    "original_filename": row.get("original_filename") or "",
                    "linked_relative_path": normalize_manifest_output_path(row.get("output_path") or "", input_dir),
                    "sha256": row.get("sha256") or "",
                })
    return rows


def collect_chat_record_context_by_message_id(manifest: dict, input_dir: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for relative_path in chat_record_source_paths(manifest):
        csv_path = input_dir / relative_path
        with csv_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_index, row in enumerate(reader, 2):
                message_id = row.get("open_message_id") or row.get("message_id") or ""
                if not message_id or message_id in rows:
                    continue
                rows[message_id] = normalize_chat_record_context_row(relative_path, row_index, row)
    return rows


def normalize_chat_record_context_row(relative_path: str, row_index: int, row: dict) -> dict:
    return {
        "chat_record_relative_path": relative_path,
        "chat_record_row_number": str(row_index),
        "open_message_id": row.get("open_message_id") or row.get("message_id") or "",
        "message_time": row.get("message_time") or "",
        "sender_name": row.get("sender_name") or "",
        "content_excerpt": text_excerpt(row.get("content") or ""),
        "quoted_sender": row.get("quoted_sender") or "",
        "quoted_content_excerpt": text_excerpt(row.get("quoted_content") or ""),
        "resource_count": row.get("resource_count") or "",
        "resource_types": row.get("resource_types") or "",
    }


def collect_chat_record_context_rows_by_path(manifest: dict, input_dir: Path) -> dict[str, list[dict]]:
    rows_by_path: dict[str, list[dict]] = {}
    for relative_path in chat_record_source_paths(manifest):
        csv_path = input_dir / relative_path
        rows: list[dict] = []
        with csv_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_index, row in enumerate(reader, 2):
                rows.append(normalize_chat_record_context_row(relative_path, row_index, row))
        rows_by_path[relative_path] = rows
    return rows_by_path


def build_ocr_fact_owner_decision_correction_chat_context_rows(
    manifest: dict,
    input_dir: Path,
    evidence_packet_rows: list[dict],
) -> list[dict]:
    resources_by_path: dict[str, list[dict]] = {}
    for resource in collect_manifest_resource_rows(manifest, input_dir):
        linked_relative_path = resource["linked_relative_path"]
        if linked_relative_path:
            resources_by_path.setdefault(linked_relative_path, []).append(resource)
    chat_by_message_id = collect_chat_record_context_by_message_id(manifest, input_dir)
    rows: list[dict] = []
    for packet in evidence_packet_rows:
        resources = resources_by_path.get(packet["source_image_relative_path"], [])
        if not resources:
            resources = [{}]
        for resource in resources:
            chat = chat_by_message_id.get(resource.get("open_message_id", ""), {})
            if resource and chat:
                context_status = "ready_chat_context_no_write"
                next_step = "Use the manifest and chat context as evidence for owner field review; do not autofill company or bank."
            elif resource:
                context_status = "ready_manifest_context_only_no_write"
                next_step = "Use the manifest context as evidence and inspect chat records manually if needed; do not autofill company or bank."
            else:
                context_status = "blocked_missing_manifest_context"
                next_step = "Rerun or repair manifest extraction before owner field review."
            rows.append({
                "chat_context_id": f"OCROWNERFIXCHAT-{manifest['run_id']}-{len(rows) + 1:05d}",
                "source_evidence_packet_id": packet["evidence_packet_id"],
                "source_correction_queue_id": packet["source_correction_queue_id"],
                "fact_candidate_id": packet["fact_candidate_id"],
                "candidate_metric": packet["candidate_metric"],
                "source_evidence_id": packet["source_evidence_id"],
                "source_image_relative_path": packet["source_image_relative_path"],
                "source_ocr_text_relative_path": packet["source_ocr_text_relative_path"],
                "open_message_id": resource.get("open_message_id", ""),
                "message_time": chat.get("message_time") or resource.get("message_time", ""),
                "sender_name": chat.get("sender_name") or resource.get("sender_name", ""),
                "manifest_relative_path": resource.get("manifest_relative_path", ""),
                "manifest_row_number": resource.get("manifest_row_number", ""),
                "resource_type": resource.get("resource_type", ""),
                "resource_id": resource.get("resource_id", ""),
                "resource_status": resource.get("status", ""),
                "chat_record_relative_path": chat.get("chat_record_relative_path", ""),
                "chat_record_row_number": chat.get("chat_record_row_number", ""),
                "chat_content_excerpt": chat.get("content_excerpt", ""),
                "quoted_sender": chat.get("quoted_sender", ""),
                "quoted_content_excerpt": chat.get("quoted_content_excerpt", ""),
                "resource_count": chat.get("resource_count", ""),
                "resource_types": chat.get("resource_types", ""),
                "context_status": context_status,
                "owner_field_autofill_allowed": "false",
                "owner_decision_manifest_write_allowed": "false",
                "source_mutation_allowed": "false",
                "fund_ledger_write_allowed": "false",
                "formal_fund_ledger_write_allowed": "false",
                "financial_fact_promoted": "false",
                "management_conclusion_allowed": "false",
                "recommended_next_step": next_step,
            })
    return rows


def build_ocr_fact_owner_decision_correction_chat_neighbor_context_rows(
    manifest: dict,
    input_dir: Path,
    chat_context_rows: list[dict],
) -> list[dict]:
    rows_by_path = collect_chat_record_context_rows_by_path(manifest, input_dir)
    rows: list[dict] = []
    for chat_context in chat_context_rows:
        relative_path = chat_context.get("chat_record_relative_path", "")
        target_row_number = chat_context.get("chat_record_row_number", "")
        target_row_number_int = int(target_row_number) if target_row_number.isdigit() else 0
        source_rows = rows_by_path.get(relative_path, [])
        source_rows_by_number = {
            int(row["chat_record_row_number"]): row
            for row in source_rows
            if row["chat_record_row_number"].isdigit()
        }
        if not relative_path or not target_row_number_int or target_row_number_int not in source_rows_by_number:
            rows.append({
                "chat_neighbor_context_id": f"OCROWNERFIXNEIGHBOR-{manifest['run_id']}-{len(rows) + 1:05d}",
                "source_chat_context_id": chat_context.get("chat_context_id", ""),
                "source_evidence_packet_id": chat_context.get("source_evidence_packet_id", ""),
                "source_correction_queue_id": chat_context.get("source_correction_queue_id", ""),
                "fact_candidate_id": chat_context.get("fact_candidate_id", ""),
                "candidate_metric": chat_context.get("candidate_metric", ""),
                "source_evidence_id": chat_context.get("source_evidence_id", ""),
                "source_image_relative_path": chat_context.get("source_image_relative_path", ""),
                "open_message_id": "",
                "chat_record_relative_path": relative_path,
                "target_chat_record_row_number": target_row_number,
                "neighbor_chat_record_row_number": "",
                "neighbor_offset": "",
                "message_time": "",
                "sender_name": "",
                "content_excerpt": "",
                "quoted_sender": "",
                "quoted_content_excerpt": "",
                "resource_count": "",
                "resource_types": "",
                "neighbor_context_radius": str(CHAT_NEIGHBOR_CONTEXT_RADIUS),
                "neighbor_context_status": "blocked_missing_target_chat_record_context",
                "owner_field_autofill_allowed": "false",
                "owner_decision_manifest_write_allowed": "false",
                "source_mutation_allowed": "false",
                "fund_ledger_write_allowed": "false",
                "formal_fund_ledger_write_allowed": "false",
                "financial_fact_promoted": "false",
                "management_conclusion_allowed": "false",
                "recommended_next_step": "Repair or inspect chat record linkage before owner field review; do not autofill company or bank.",
            })
            continue
        for neighbor_row_number in range(
            target_row_number_int - CHAT_NEIGHBOR_CONTEXT_RADIUS,
            target_row_number_int + CHAT_NEIGHBOR_CONTEXT_RADIUS + 1,
        ):
            neighbor = source_rows_by_number.get(neighbor_row_number)
            if not neighbor:
                continue
            rows.append({
                "chat_neighbor_context_id": f"OCROWNERFIXNEIGHBOR-{manifest['run_id']}-{len(rows) + 1:05d}",
                "source_chat_context_id": chat_context.get("chat_context_id", ""),
                "source_evidence_packet_id": chat_context.get("source_evidence_packet_id", ""),
                "source_correction_queue_id": chat_context.get("source_correction_queue_id", ""),
                "fact_candidate_id": chat_context.get("fact_candidate_id", ""),
                "candidate_metric": chat_context.get("candidate_metric", ""),
                "source_evidence_id": chat_context.get("source_evidence_id", ""),
                "source_image_relative_path": chat_context.get("source_image_relative_path", ""),
                "open_message_id": neighbor.get("open_message_id", ""),
                "chat_record_relative_path": relative_path,
                "target_chat_record_row_number": target_row_number,
                "neighbor_chat_record_row_number": neighbor.get("chat_record_row_number", ""),
                "neighbor_offset": str(neighbor_row_number - target_row_number_int),
                "message_time": neighbor.get("message_time", ""),
                "sender_name": neighbor.get("sender_name", ""),
                "content_excerpt": neighbor.get("content_excerpt", ""),
                "quoted_sender": neighbor.get("quoted_sender", ""),
                "quoted_content_excerpt": neighbor.get("quoted_content_excerpt", ""),
                "resource_count": neighbor.get("resource_count", ""),
                "resource_types": neighbor.get("resource_types", ""),
                "neighbor_context_radius": str(CHAT_NEIGHBOR_CONTEXT_RADIUS),
                "neighbor_context_status": "ready_neighbor_context_no_write",
                "owner_field_autofill_allowed": "false",
                "owner_decision_manifest_write_allowed": "false",
                "source_mutation_allowed": "false",
                "fund_ledger_write_allowed": "false",
                "formal_fund_ledger_write_allowed": "false",
                "financial_fact_promoted": "false",
                "management_conclusion_allowed": "false",
                "recommended_next_step": "Use neighboring chat messages as owner-review context only; do not autofill company or bank.",
            })
    return rows


def join_context_excerpts(rows: list[dict], field: str, limit: int = 500) -> str:
    excerpts = [
        row.get(field, "")
        for row in rows
        if row.get(field, "")
    ]
    return text_excerpt(" | ".join(excerpts), limit)


def build_ocr_fact_owner_decision_correction_owner_review_packet_rows(
    manifest: dict,
    evidence_packet_rows: list[dict],
    ocr_line_context_rows: list[dict],
    chat_context_rows: list[dict],
    chat_neighbor_context_rows: list[dict],
) -> list[dict]:
    ocr_by_packet: dict[str, list[dict]] = {}
    for row in ocr_line_context_rows:
        ocr_by_packet.setdefault(row.get("source_evidence_packet_id", ""), []).append(row)
    chat_by_packet: dict[str, list[dict]] = {}
    for row in chat_context_rows:
        chat_by_packet.setdefault(row.get("source_evidence_packet_id", ""), []).append(row)
    neighbor_by_packet: dict[str, list[dict]] = {}
    for row in chat_neighbor_context_rows:
        neighbor_by_packet.setdefault(row.get("source_evidence_packet_id", ""), []).append(row)
    rows: list[dict] = []
    for packet in evidence_packet_rows:
        packet_id = packet["evidence_packet_id"]
        ocr_context = ocr_by_packet.get(packet_id, [])
        chat_context = chat_by_packet.get(packet_id, [])
        neighbor_context = neighbor_by_packet.get(packet_id, [])
        ready = (
            packet["evidence_packet_status"] == "ready_for_owner_field_review_no_write"
            and any(row["ocr_line_context_status"] == "ready_ocr_line_context_no_write" for row in ocr_context)
        )
        status = "ready_for_owner_field_decision_no_write" if ready else "blocked_owner_field_context_incomplete"
        next_step = (
            "Owner must review the consolidated evidence context and fill required owner-corrected fields in the private manifest; do not autofill company or bank."
            if ready
            else "Complete missing correction evidence context before owner field decision; do not autofill company or bank."
        )
        rows.append({
            "owner_review_packet_id": f"OCROWNERFIXREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "source_evidence_packet_id": packet_id,
            "source_correction_queue_id": packet["source_correction_queue_id"],
            "fact_candidate_id": packet["fact_candidate_id"],
            "candidate_metric": packet["candidate_metric"],
            "missing_required_fields": packet["missing_required_fields"],
            "required_owner_fields": packet["required_owner_fields"],
            "current_company": packet["current_company"],
            "current_bank": packet["current_bank"],
            "candidate_business_date": packet["candidate_business_date"],
            "candidate_amount": packet["candidate_amount"],
            "candidate_currency": packet["candidate_currency"],
            "candidate_line_number": packet["candidate_line_number"],
            "candidate_line_text_excerpt": packet["candidate_line_text_excerpt"],
            "source_evidence_id": packet["source_evidence_id"],
            "source_image_relative_path": packet["source_image_relative_path"],
            "source_ocr_text_relative_path": packet["source_ocr_text_relative_path"],
            "owner_decision_manifest_relative_path": packet["owner_decision_manifest_relative_path"],
            "ocr_line_context_ready_count": str(sum(1 for row in ocr_context if row["ocr_line_context_status"] == "ready_ocr_line_context_no_write")),
            "ocr_line_context_excerpt": join_context_excerpts(ocr_context, "ocr_line_text_excerpt"),
            "chat_context_ready_count": str(sum(
                1 for row in chat_context
                if row["context_status"] in {"ready_chat_context_no_write", "ready_manifest_context_only_no_write"}
            )),
            "chat_context_excerpt": join_context_excerpts(chat_context, "chat_content_excerpt"),
            "chat_neighbor_context_ready_count": str(sum(
                1 for row in neighbor_context
                if row["neighbor_context_status"] == "ready_neighbor_context_no_write"
            )),
            "chat_neighbor_context_excerpt": join_context_excerpts(neighbor_context, "content_excerpt"),
            "owner_review_packet_status": status,
            "owner_field_autofill_allowed": "false",
            "owner_decision_manifest_write_allowed": "false",
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        })
    return rows


def build_ocr_fact_owner_decision_correction_manifest_readiness_rows(
    manifest: dict,
    repo_root: Path,
    owner_review_packet_rows: list[dict],
) -> list[dict]:
    decision_manifest = load_ocr_fact_candidate_owner_decision_manifest(repo_root, manifest["run_id"])
    rows: list[dict] = []
    for packet in owner_review_packet_rows:
        required_owner_fields = [
            field.strip()
            for field in packet.get("required_owner_fields", "").split(",")
            if field.strip()
        ]
        decision = {
            "candidate_metric": "",
            "owner_authorization_decision": "pending_owner_review",
            "owner_corrected_company": "",
            "owner_corrected_bank": "",
            "owner_note": "",
        }
        owner_decision_entry_status = decision_manifest["status"]
        missing_owner_values = list(required_owner_fields)
        if packet["owner_review_packet_status"] != "ready_for_owner_field_decision_no_write":
            manifest_readiness_status = "blocked_owner_review_packet_not_ready"
            owner_decision_entry_status = packet["owner_review_packet_status"]
            next_step = "Complete owner review packet context before validating the private owner decision manifest."
        elif decision_manifest["status"] == "missing_decision_manifest":
            manifest_readiness_status = "blocked_missing_owner_decision_manifest"
            next_step = "Save a reviewed private owner decision manifest with all required owner-corrected fields, then rerun validation."
        elif decision_manifest["status"] != "valid_decision_manifest":
            manifest_readiness_status = "blocked_invalid_owner_decision_manifest"
            next_step = "Fix the private owner decision manifest schema before rerunning validation."
        else:
            entry = decision_manifest["entries"].get(packet["fact_candidate_id"])
            if entry is None:
                manifest_readiness_status = "blocked_missing_owner_decision_entry"
                owner_decision_entry_status = "missing_owner_decision_entry"
                next_step = "Add this fact candidate to the private owner decision manifest with required owner-corrected fields."
            else:
                decision = entry
                owner_decision_entry_status = "owner_decision_entry_present"
                missing_owner_values = [
                    field for field in required_owner_fields
                    if not str(decision.get(field, "")).strip()
                ]
                if entry["candidate_metric"] != packet["candidate_metric"]:
                    manifest_readiness_status = "blocked_owner_decision_metric_mismatch"
                    next_step = "Align candidate_metric in the private owner decision manifest before rerunning validation."
                elif entry["owner_authorization_decision"] != "approve_for_review_authorization":
                    manifest_readiness_status = "blocked_owner_decision_not_approved"
                    next_step = "Set owner_authorization_decision only after owner review approves this correction."
                elif missing_owner_values:
                    manifest_readiness_status = "blocked_owner_decision_missing_required_values"
                    next_step = "Complete the missing owner-corrected values in the private owner decision manifest."
                else:
                    manifest_readiness_status = "ready_for_owner_decision_manifest_validation_no_write"
                    next_step = "Rerun validation to let the no-write apply gate confirm this owner decision; do not promote ledger in this step."
        rows.append({
            "manifest_readiness_id": f"OCROWNERFIXMANIFEST-{manifest['run_id']}-{len(rows) + 1:05d}",
            "source_owner_review_packet_id": packet["owner_review_packet_id"],
            "source_evidence_packet_id": packet["source_evidence_packet_id"],
            "fact_candidate_id": packet["fact_candidate_id"],
            "candidate_metric": packet["candidate_metric"],
            "missing_required_fields": packet["missing_required_fields"],
            "required_owner_fields": packet["required_owner_fields"],
            "decision_manifest_relative_path": decision_manifest["relative_path"],
            "decision_manifest_status": decision_manifest["status"],
            "owner_decision_entry_status": owner_decision_entry_status,
            "owner_authorization_decision": decision["owner_authorization_decision"],
            "owner_corrected_company": decision["owner_corrected_company"],
            "owner_corrected_bank": decision["owner_corrected_bank"],
            "missing_owner_values": ",".join(missing_owner_values),
            "manifest_readiness_status": manifest_readiness_status,
            "owner_decision_manifest_write_allowed": "false",
            "source_mutation_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "formal_fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_next_step": next_step,
        })
    return rows


def collect_chat_evidence_links(
    manifest: dict,
    input_dir: Path,
    evidence: list[dict],
    chat_text_candidates: list[dict],
    chat_value_candidates: list[dict],
) -> list[dict]:
    evidence_by_path = {row["relative_path"]: row for row in evidence}
    values_by_chat: dict[str, list[str]] = {}
    for value in chat_value_candidates:
        values_by_chat.setdefault(value["chat_text_candidate_id"], []).append(value["value_candidate_id"])
    resources_by_message: dict[str, list[dict]] = {}
    for resource in collect_manifest_resource_rows(manifest, input_dir):
        resources_by_message.setdefault(resource["open_message_id"], []).append(resource)

    rows: list[dict] = []
    for candidate in chat_text_candidates:
        for resource in resources_by_message.get(candidate["open_message_id"], []):
            linked_relative_path = resource["linked_relative_path"]
            linked_evidence = evidence_by_path.get(linked_relative_path)
            link_status = "linked_pending_review" if linked_evidence else "linked_evidence_missing_pending_review"
            rows.append({
                "chat_evidence_link_id": f"CHATLINK-{manifest['run_id']}-{len(rows) + 1:05d}",
                "chat_text_candidate_id": candidate["chat_text_candidate_id"],
                "chat_value_candidate_ids": ";".join(values_by_chat.get(candidate["chat_text_candidate_id"], [])),
                "open_message_id": candidate["open_message_id"],
                "source_csv_relative_path": candidate["source_csv_relative_path"],
                "source_row_number": candidate["source_row_number"],
                "manifest_relative_path": resource["manifest_relative_path"],
                "manifest_row_number": resource["manifest_row_number"],
                "resource_type": resource["resource_type"],
                "resource_id": resource["resource_id"],
                "resource_status": resource["status"],
                "linked_evidence_id": linked_evidence["evidence_id"] if linked_evidence else "",
                "linked_relative_path": linked_relative_path,
                "link_status": link_status,
                "review_status": "pending_human_review",
                "financial_fact_promoted": "false",
            })
    return rows


def collect_attachment_evidence_reconciliation(manifest: dict, input_dir: Path, evidence: list[dict]) -> list[dict]:
    evidence_by_path = {row["relative_path"]: row for row in evidence}
    rows: list[dict] = []
    for resource in collect_manifest_resource_rows(manifest, input_dir):
        linked_relative_path = resource["linked_relative_path"]
        linked_evidence = evidence_by_path.get(linked_relative_path) if linked_relative_path else None
        manifest_sha256 = resource["sha256"]
        evidence_sha256 = linked_evidence["sha256"] if linked_evidence else ""
        if not linked_relative_path:
            reconciliation_status = "manifest_output_path_missing_blocking"
        elif linked_evidence is None:
            reconciliation_status = "evidence_missing_blocking"
        elif manifest_sha256 and evidence_sha256 and manifest_sha256 != evidence_sha256:
            reconciliation_status = "evidence_hash_mismatch_blocking"
        else:
            reconciliation_status = "evidence_linked_pending_review"
        rows.append({
            "attachment_reconciliation_id": f"ATTACHREC-{manifest['run_id']}-{len(rows) + 1:05d}",
            "open_message_id": resource["open_message_id"],
            "manifest_relative_path": resource["manifest_relative_path"],
            "manifest_row_number": resource["manifest_row_number"],
            "resource_type": resource["resource_type"],
            "resource_id": resource["resource_id"],
            "resource_status": resource["status"],
            "manifest_output_path": linked_relative_path,
            "linked_evidence_id": linked_evidence["evidence_id"] if linked_evidence else "",
            "manifest_sha256": manifest_sha256,
            "evidence_sha256": evidence_sha256,
            "reconciliation_status": reconciliation_status,
            "review_status": "pending_human_review",
            "financial_fact_promoted": "false",
        })
    return rows


def attachment_remediation_for_status(reconciliation_status: str) -> tuple[str, str, str]:
    if reconciliation_status == "manifest_output_path_missing_blocking":
        return (
            "rerun_dws_attachment_download",
            "dws_attachment_download_queue",
            "Manifest resource row has no output_path; rerun or inspect the DWS attachment download for this message/resource.",
        )
    if reconciliation_status == "evidence_missing_blocking":
        return (
            "restore_or_materialize_output_file",
            "source_materialization_queue",
            "Manifest output_path has no evidence file in the indexed source tree; restore, materialize, or rerun the source archive before review.",
        )
    if reconciliation_status == "evidence_hash_mismatch_blocking":
        return (
            "quarantine_and_recollect_hash_mismatch",
            "evidence_integrity_queue",
            "Manifest SHA and indexed evidence SHA differ; quarantine the row and recollect the attachment before any fact promotion.",
        )
    return (
        "manual_attachment_reconciliation_review",
        "manual_review_queue",
        "Attachment reconciliation status is blocking and requires operator review before any fact promotion.",
    )


def build_attachment_reconciliation_remediation(manifest: dict, attachment_reconciliation_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in attachment_reconciliation_rows:
        if not row["reconciliation_status"].endswith("_blocking"):
            continue
        action_code, owner_queue, action_reason = attachment_remediation_for_status(row["reconciliation_status"])
        rows.append({
            "remediation_id": f"ATTACHFIX-{manifest['run_id']}-{len(rows) + 1:05d}",
            "attachment_reconciliation_id": row["attachment_reconciliation_id"],
            "open_message_id": row["open_message_id"],
            "blocking_status": row["reconciliation_status"],
            "resource_status": row["resource_status"],
            "action_code": action_code,
            "owner_queue": owner_queue,
            "action_reason": action_reason,
            "evidence_required": "true",
            "automation_safe": "false",
            "formal_fact_allowed": "false",
            "relative_path": row["manifest_output_path"] or f"{row['manifest_relative_path']}:{row['manifest_row_number']}",
            "review_status": "pending_operator_action",
        })
    return rows


def attachment_dry_run_status(action_code: str) -> tuple[str, str]:
    if action_code == "rerun_dws_attachment_download":
        return (
            "dws_rerun_required",
            "Dry-run only: rerun the DWS attachment download through the controlled archive workflow before evidence review.",
        )
    if action_code == "restore_or_materialize_output_file":
        return (
            "source_restore_required",
            "Dry-run only: restore or materialize the missing output file, then rerun source readiness and the fund analysis runner.",
        )
    if action_code == "quarantine_and_recollect_hash_mismatch":
        return (
            "hash_mismatch_quarantine_required",
            "Dry-run only: quarantine the mismatched evidence and recollect the attachment before any fact promotion.",
        )
    return (
        "manual_review_required",
        "Dry-run only: operator review is required before any repair or fact promotion.",
    )


def build_attachment_remediation_dry_run(manifest: dict, attachment_remediation_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in attachment_remediation_rows:
        dry_run_status, dry_run_reason = attachment_dry_run_status(row["action_code"])
        rows.append({
            "dry_run_id": f"ATTACHDRY-{manifest['run_id']}-{len(rows) + 1:05d}",
            "remediation_id": row["remediation_id"],
            "open_message_id": row["open_message_id"],
            "action_code": row["action_code"],
            "owner_queue": row["owner_queue"],
            "dry_run_status": dry_run_status,
            "dry_run_reason": dry_run_reason,
            "safe_to_apply": "false",
            "apply_performed": "false",
            "formal_fact_allowed": "false",
            "relative_path": row["relative_path"],
            "review_status": "pending_operator_action",
        })
    return rows


def attachment_source_zip_member(input_dir: Path, relative_path: str) -> str:
    zip_root = input_dir.parent.parent if input_dir.parent.name == "DWS_Outputs" else input_dir.parent
    zip_path = zip_root / "DWS_Outputs.zip"
    if not zip_path.exists() or relative_path.startswith("_manifest/manifest.csv:"):
        return ""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
    except zipfile.BadZipFile:
        return ""
    for prefix in (f"{input_dir.name}/", f"DWS_Outputs/{input_dir.name}/", ""):
        candidate = f"{prefix}{relative_path}"
        if candidate in names:
            return candidate
    return ""


def attachment_source_locator_status(action_code: str, local_exists: bool, source_zip_member: str) -> tuple[str, str]:
    if action_code == "rerun_dws_attachment_download":
        return (
            "requires_dws_attachment_rerun",
            "Manifest row has no output_path, so local or ZIP materialization cannot locate a deterministic attachment path.",
        )
    if action_code == "restore_or_materialize_output_file":
        if local_exists:
            return (
                "candidate_already_in_input_dir",
                "The missing attachment path now exists in the configured input folder; rerun reconciliation to verify evidence.",
            )
        if source_zip_member:
            return (
                "candidate_in_source_zip",
                "The missing attachment path exists in DWS_Outputs.zip and can be materialized only through an approved source repair flow.",
            )
        return (
            "candidate_not_found",
            "The missing attachment path was not found in the configured input folder or DWS_Outputs.zip.",
        )
    if action_code == "quarantine_and_recollect_hash_mismatch":
        return (
            "requires_quarantine_recollect",
            "A hash mismatch requires quarantine and recollection rather than local materialization.",
        )
    return (
        "requires_manual_review",
        "Attachment repair locator cannot determine a specific source path for this remediation action.",
    )


def build_attachment_repair_source_locator(
    manifest: dict,
    input_dir: Path,
    attachment_remediation_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for row in attachment_remediation_rows:
        relative_path = row["relative_path"]
        local_exists = False
        if not relative_path.startswith("_manifest/manifest.csv:"):
            local_exists = (input_dir / relative_path).exists()
        source_zip_member = attachment_source_zip_member(input_dir, relative_path)
        locator_status, locator_reason = attachment_source_locator_status(
            row["action_code"],
            local_exists,
            source_zip_member,
        )
        rows.append({
            "source_locator_id": f"ATTACHLOC-{manifest['run_id']}-{len(rows) + 1:05d}",
            "remediation_id": row["remediation_id"],
            "attachment_reconciliation_id": row["attachment_reconciliation_id"],
            "open_message_id": row["open_message_id"],
            "action_code": row["action_code"],
            "relative_path": relative_path,
            "local_input_exists": bool_text(local_exists),
            "source_zip_member": source_zip_member,
            "locator_status": locator_status,
            "locator_reason": locator_reason,
            "safe_to_apply": "false",
            "source_mutation_allowed": "false",
            "apply_performed": "false",
            "formal_fact_allowed": "false",
            "review_status": "pending_operator_action",
        })
    return rows


def attachment_repair_plan_for_status(dry_run_status: str) -> tuple[str, str, str]:
    if dry_run_status == "dws_rerun_required":
        return (
            "plan_only_dws_rerun_pending",
            "dws_archive_controlled_rerun",
            "Plan only: operator must run the controlled DWS attachment archive flow and then rerun source readiness.",
        )
    if dry_run_status == "source_restore_required":
        return (
            "plan_only_source_restore_pending",
            "source_materialization_plan",
            "Plan only: operator must restore or materialize the missing output file, then rerun source readiness.",
        )
    if dry_run_status == "hash_mismatch_quarantine_required":
        return (
            "plan_only_quarantine_pending",
            "evidence_quarantine_recollect_plan",
            "Plan only: operator must quarantine the mismatched evidence and recollect the attachment before review.",
        )
    return (
        "plan_only_manual_review_pending",
        "manual_review_plan",
        "Plan only: operator review is required before any repair step.",
    )


def build_attachment_repair_plan(manifest: dict, attachment_dry_run_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in attachment_dry_run_rows:
        repair_plan_status, command_family, plan_instruction = attachment_repair_plan_for_status(row["dry_run_status"])
        rows.append({
            "repair_plan_id": f"ATTACHPLAN-{manifest['run_id']}-{len(rows) + 1:05d}",
            "dry_run_id": row["dry_run_id"],
            "remediation_id": row["remediation_id"],
            "open_message_id": row["open_message_id"],
            "repair_plan_status": repair_plan_status,
            "required_command_family": command_family,
            "plan_instruction": plan_instruction,
            "operator_confirmation_required": "true",
            "source_mutation_allowed": "false",
            "apply_performed": "false",
            "formal_fact_allowed": "false",
            "relative_path": row["relative_path"],
            "review_status": "pending_operator_action",
        })
    return rows


def attachment_repair_authorization_relative_path(run_id: str) -> str:
    return f"KMFA/metadata/fund_weekly_analysis/private_runtime/attachment_repair_authorizations/{run_id}.json"


def load_attachment_repair_authorization(repo_root: Path, run_id: str) -> dict:
    relative_path = attachment_repair_authorization_relative_path(run_id)
    path = repo_root / relative_path
    missing = {
        "relative_path": relative_path,
        "status": "missing_authorization_manifest",
        "entries": {},
        "metadata": {},
    }
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_authorization_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_authorization_schema"}
    required = {
        "authorization_manifest_version": "1",
        "run_id": run_id,
        "authorization_scope": "attachment_repair_plan_validation_only",
        "source_mutation_allowed": False,
        "apply_execution_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_authorization_schema"}
    raw_entries = payload.get("repair_plan_authorizations")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_authorization_schema"}
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_authorization_schema"}
        repair_plan_id = entry.get("repair_plan_id")
        command_family = entry.get("required_command_family")
        if not isinstance(repair_plan_id, str) or not repair_plan_id:
            return {**missing, "status": "invalid_authorization_schema"}
        if not isinstance(command_family, str) or not command_family:
            return {**missing, "status": "invalid_authorization_schema"}
        entries[repair_plan_id] = {
            "required_command_family": command_family,
            "authorized": entry.get("authorized") is True,
        }
    return {
        "relative_path": relative_path,
        "status": "valid_authorization_manifest",
        "entries": entries,
        "metadata": {
            "authorization_ticket": str(payload.get("authorization_ticket", "")),
            "authorized_by": str(payload.get("authorized_by", "")),
            "authorized_at": str(payload.get("authorized_at", "")),
            "authorization_scope": str(payload.get("authorization_scope", "")),
        },
    }


def attachment_repair_gate_status(row: dict, authorization: dict) -> tuple[str, str, str, str]:
    auth_status = authorization["status"]
    if auth_status == "missing_authorization_manifest":
        return (
            "false",
            "missing_authorization_manifest",
            "blocked_missing_operator_authorization",
            "Controlled attachment repair apply is blocked until a private operator authorization manifest exists.",
        )
    if auth_status != "valid_authorization_manifest":
        return (
            "false",
            auth_status,
            "blocked_invalid_operator_authorization",
            "Controlled attachment repair apply is blocked because the operator authorization manifest is invalid.",
        )
    entry = authorization["entries"].get(row["repair_plan_id"])
    if entry is None:
        return (
            "false",
            "repair_plan_not_authorized",
            "blocked_missing_repair_plan_authorization",
            "Controlled attachment repair apply is blocked because this repair plan row is not covered by the operator authorization manifest.",
        )
    if entry["required_command_family"] != row["required_command_family"]:
        return (
            "true",
            "authorization_command_family_mismatch",
            "blocked_authorization_command_mismatch",
            "Controlled attachment repair apply is blocked because the authorization command family does not match the repair plan.",
        )
    if not entry["authorized"]:
        return (
            "true",
            "repair_plan_authorization_not_true",
            "blocked_repair_plan_not_authorized",
            "Controlled attachment repair apply is blocked because this repair plan row is not explicitly authorized.",
        )
    return (
        "true",
        "valid_manifest_validation_only",
        "blocked_apply_engine_not_enabled",
        "Operator authorization manifest is valid for this row, but this runner only validates authorization and does not execute repairs.",
    )


def build_attachment_repair_apply_gate(manifest: dict, repo_root: Path, attachment_repair_plan_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    authorization = load_attachment_repair_authorization(repo_root, manifest["run_id"])
    metadata = authorization["metadata"]
    for row in attachment_repair_plan_rows:
        authorization_present, validation_status, apply_gate_status, gate_reason = attachment_repair_gate_status(row, authorization)
        rows.append({
            "apply_gate_id": f"ATTACHGATE-{manifest['run_id']}-{len(rows) + 1:05d}",
            "repair_plan_id": row["repair_plan_id"],
            "remediation_id": row["remediation_id"],
            "open_message_id": row["open_message_id"],
            "required_command_family": row["required_command_family"],
            "operator_authorization_required": "true",
            "authorization_manifest_relative_path": authorization["relative_path"],
            "operator_authorization_present": authorization_present,
            "authorization_validation_status": validation_status,
            "authorization_ticket": metadata.get("authorization_ticket", ""),
            "authorized_by": metadata.get("authorized_by", ""),
            "authorized_at": metadata.get("authorized_at", ""),
            "authorization_scope": metadata.get("authorization_scope", ""),
            "apply_gate_status": apply_gate_status,
            "apply_allowed": "false",
            "source_mutation_allowed": "false",
            "apply_performed": "false",
            "formal_fact_allowed": "false",
            "gate_reason": gate_reason,
            "relative_path": row["relative_path"],
            "review_status": "pending_operator_authorization",
        })
    return rows


def build_attachment_repair_authorization_template(manifest: dict, attachment_apply_gate_rows: list[dict]) -> dict:
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "attachment_repair_plan_validation_only",
        "template_status": "operator_review_required",
        "template_generated_from": "attachment_repair_apply_gate.csv",
        "output_authorization_manifest_relative_path": attachment_repair_authorization_relative_path(manifest["run_id"]),
        "authorized_by": "",
        "authorized_at": "",
        "authorization_ticket": "",
        "source_mutation_allowed": False,
        "apply_execution_allowed": False,
        "operator_instruction": "Review each repair plan row, edit authorized=true only where approved, then save a confirmed copy to output_authorization_manifest_relative_path. This template itself does not authorize or execute repairs.",
        "repair_plan_authorizations": [
            {
                "repair_plan_id": row["repair_plan_id"],
                "required_command_family": row["required_command_family"],
                "open_message_id": row["open_message_id"],
                "relative_path": row["relative_path"],
                "authorized": False,
                "operator_note": "",
            }
            for row in attachment_apply_gate_rows
        ],
    }


def attachment_repair_preview_status(validation_status: str) -> tuple[str, str]:
    if validation_status == "valid_manifest_validation_only":
        return "ready_for_operator_review_no_apply", "pending_operator_impact_review"
    if validation_status == "missing_authorization_manifest":
        return "blocked_missing_operator_authorization", "pending_operator_authorization"
    if validation_status in {"repair_plan_not_authorized", "repair_plan_authorization_not_true"}:
        return "blocked_repair_plan_not_authorized", "pending_operator_authorization"
    if validation_status == "authorization_command_family_mismatch":
        return "blocked_authorization_command_mismatch", "pending_operator_authorization"
    return "blocked_invalid_operator_authorization", "pending_operator_authorization"


def build_attachment_repair_authorization_preview(manifest: dict, attachment_apply_gate_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in attachment_apply_gate_rows:
        preview_status, review_status = attachment_repair_preview_status(row["authorization_validation_status"])
        rows.append({
            "authorization_preview_id": f"ATTACHPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "apply_gate_id": row["apply_gate_id"],
            "repair_plan_id": row["repair_plan_id"],
            "open_message_id": row["open_message_id"],
            "required_command_family": row["required_command_family"],
            "authorization_validation_status": row["authorization_validation_status"],
            "preview_status": preview_status,
            "impact_scope": "attachment_evidence_repair_plan_only",
            "source_mutation_allowed": "false",
            "apply_allowed": "false",
            "apply_performed": "false",
            "formal_fact_allowed": "false",
            "relative_path": row["relative_path"],
            "review_status": review_status,
        })
    return rows


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
            if isinstance(item, dict):
                rows.append(item)
    return rows


def read_json_object(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        item = json.load(f)
    return item if isinstance(item, dict) else None


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def load_toml_object(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def automation_readiness_row(
    status: str,
    automation_id: str = "",
    automation_path: str = "",
    expected_timezone: str = "",
    rrule: str = "",
    cwd: str = "",
    schedule_ready: bool = False,
    mismatches: list[str] | None = None,
    next_action: str = "",
) -> dict:
    mismatch_fields = sorted(mismatches or [])
    return {
        "automation_readiness_id": "AUTOMATION-READINESS-001",
        "status": status,
        "automation_id": automation_id,
        "automation_path": automation_path,
        "expected_timezone": expected_timezone,
        "rrule": rrule,
        "cwd": cwd,
        "schedule_ready": bool_text(schedule_ready),
        "mismatch_count": str(len(mismatch_fields)),
        "mismatch_fields": ";".join(mismatch_fields),
        "management_conclusion_allowed": "false",
        "next_action": next_action,
    }


def build_automation_readiness_rows(repo_root: Path, automation_root: Path) -> list[dict]:
    skill_root = repo_root / "KMFA" / "fund-weekly-analysis-skill"
    contract_path = skill_root / "automation" / "codex_app_automation.contract.toml"
    if not contract_path.exists():
        return [
            automation_readiness_row(
                "CODEX_AUTOMATION_CONTRACT_MISSING",
                automation_path=str(contract_path),
                next_action="Restore tracked Codex automation contract before claiming scheduled readiness",
            )
        ]
    try:
        contract = load_toml_object(contract_path)
    except Exception:
        return [
            automation_readiness_row(
                "CODEX_AUTOMATION_CONTRACT_INVALID",
                automation_path=str(contract_path),
                next_action="Fix tracked Codex automation contract TOML before claiming scheduled readiness",
            )
        ]

    automation_id = str(contract.get("id", ""))
    expected_timezone = str(contract.get("timezone", ""))
    rrule = str(contract.get("rrule", ""))
    cwds = contract.get("cwds") if isinstance(contract.get("cwds"), list) else []
    cwd = str(cwds[0]) if cwds else ""
    automation_path = automation_root.expanduser() / automation_id / "automation.toml"
    if not automation_path.exists():
        return [
            automation_readiness_row(
                "CODEX_AUTOMATION_MISSING",
                automation_id=automation_id,
                automation_path=str(automation_path),
                expected_timezone=expected_timezone,
                rrule=rrule,
                cwd=cwd,
                next_action="Create or restore local Codex automation before claiming scheduled readiness",
            )
        ]
    try:
        live = load_toml_object(automation_path)
    except Exception:
        return [
            automation_readiness_row(
                "CODEX_AUTOMATION_INVALID",
                automation_id=automation_id,
                automation_path=str(automation_path),
                expected_timezone=expected_timezone,
                rrule=rrule,
                cwd=cwd,
                next_action="Fix local Codex automation TOML before claiming scheduled readiness",
            )
        ]

    mismatches = [
        field
        for field in AUTOMATION_CHECK_FIELDS
        if live.get(field) != contract.get(field)
    ]
    if live.get("timezone") is not None and live.get("timezone") != contract.get("timezone"):
        mismatches.append("timezone")
    prompt_file = skill_root / str(contract.get("prompt_file", ""))
    if live.get("prompt") is not None and prompt_file.exists():
        expected_prompt = prompt_file.read_text(encoding="utf-8").strip()
        if str(live["prompt"]).strip() != expected_prompt:
            mismatches.append("prompt")

    ready = (
        not mismatches
        and rrule == "FREQ=DAILY;BYHOUR=11;BYMINUTE=30"
        and expected_timezone == "Australia/Sydney"
    )
    return [
        automation_readiness_row(
            "CODEX_AUTOMATION_READY" if ready else "CODEX_AUTOMATION_MISMATCH",
            automation_id=automation_id,
            automation_path=str(automation_path),
            expected_timezone=expected_timezone,
            rrule=rrule,
            cwd=cwd,
            schedule_ready=ready,
            mismatches=mismatches,
            next_action=(
                "Keep local Codex automation schedule aligned with repo contract"
                if ready
                else "Sync local Codex automation to the tracked daily 11:30 Australia/Sydney contract"
            ),
        )
    ]


def money(value: str | None) -> Decimal:
    cleaned = (value or "").strip().replace(",", "")
    if cleaned == "":
        return Decimal("0.00")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"invalid money value: {value!r}") from exc


def money_text(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def currency_text(value: Decimal) -> str:
    amount = value.quantize(Decimal("0.01"))
    sign = "-" if amount < 0 else ""
    return f"¥{sign}{abs(amount):,.2f}"


def percent_text(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}%"


def xlsx_tag(name: str) -> str:
    return f"{{{XLSX_MAIN_NS}}}{name}"


def split_cell_ref(ref: str) -> tuple[str, int]:
    letters = "".join(ch for ch in ref if ch.isalpha())
    row_text = "".join(ch for ch in ref if ch.isdigit())
    return letters, int(row_text)


def column_index(letters: str) -> int:
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - ord("A") + 1
    return index


def column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def cell_ref(row_number: int, col_number: int) -> str:
    return f"{column_letter(col_number)}{row_number}"


def sheet_data(sheet_root: ET.Element) -> ET.Element:
    data = sheet_root.find(xlsx_tag("sheetData"))
    if data is None:
        data = ET.SubElement(sheet_root, xlsx_tag("sheetData"))
    return data


def get_or_create_row(data: ET.Element, row_number: int) -> ET.Element:
    for position, row in enumerate(list(data)):
        if row.tag != xlsx_tag("row"):
            continue
        current = int(row.attrib.get("r", "0"))
        if current == row_number:
            return row
        if current > row_number:
            new_row = ET.Element(xlsx_tag("row"), {"r": str(row_number)})
            data.insert(position, new_row)
            return new_row
    new_row = ET.SubElement(data, xlsx_tag("row"), {"r": str(row_number)})
    return new_row


def get_or_create_cell(row: ET.Element, ref: str) -> ET.Element:
    target_col, _ = split_cell_ref(ref)
    target_index = column_index(target_col)
    for position, cell in enumerate(list(row)):
        if cell.tag != xlsx_tag("c"):
            continue
        current_ref = cell.attrib.get("r", "")
        current_col, _ = split_cell_ref(current_ref) if current_ref else ("", 0)
        if current_ref == ref:
            return cell
        if current_col and column_index(current_col) > target_index:
            new_cell = ET.Element(xlsx_tag("c"), {"r": ref})
            row.insert(position, new_cell)
            return new_cell
    return ET.SubElement(row, xlsx_tag("c"), {"r": ref})


def clear_cell(cell: ET.Element) -> None:
    for attr in ("t", "cm", "vm", "ph"):
        cell.attrib.pop(attr, None)
    for child in list(cell):
        cell.remove(child)


def set_text_cell(sheet_root: ET.Element, ref: str, text: str) -> None:
    _, row_number = split_cell_ref(ref)
    row = get_or_create_row(sheet_data(sheet_root), row_number)
    cell = get_or_create_cell(row, ref)
    clear_cell(cell)
    cell.attrib["t"] = "inlineStr"
    inline = ET.SubElement(cell, xlsx_tag("is"))
    node = ET.SubElement(inline, xlsx_tag("t"))
    if text != text.strip() or "\n" in text:
        node.attrib[f"{{{XML_NS}}}space"] = "preserve"
    node.text = text


def set_number_cell(sheet_root: ET.Element, ref: str, value: Decimal | int | str) -> None:
    _, row_number = split_cell_ref(ref)
    row = get_or_create_row(sheet_data(sheet_root), row_number)
    cell = get_or_create_cell(row, ref)
    clear_cell(cell)
    node = ET.SubElement(cell, xlsx_tag("v"))
    node.text = str(value)


def clear_rows_from(sheet_root: ET.Element, start_row: int) -> None:
    data = sheet_data(sheet_root)
    for row in list(data):
        if row.tag == xlsx_tag("row") and int(row.attrib.get("r", "0")) >= start_row:
            data.remove(row)


def write_table_rows(sheet_root: ET.Element, start_row: int, rows: list[list[tuple[str, object]]]) -> None:
    for row_offset, values in enumerate(rows):
        row_number = start_row + row_offset
        for col_number, (kind, value) in enumerate(values, 1):
            if kind == "number":
                set_number_cell(sheet_root, cell_ref(row_number, col_number), value)
            else:
                set_text_cell(sheet_root, cell_ref(row_number, col_number), str(value))


def serialize_sheet(sheet_root: ET.Element) -> bytes:
    return ET.tostring(sheet_root, encoding="utf-8", xml_declaration=True)


def replace_xlsx_entries(workbook_path: Path, replacements: dict[str, bytes]) -> None:
    temp_path = workbook_path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(workbook_path, "r") as source, zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = replacements.get(info.filename)
            target.writestr(info, payload if payload is not None else source.read(info.filename))
    temp_path.replace(workbook_path)


def xml_text_values(root: ET.Element) -> list[str]:
    return [node.text or "" for node in root.iter() if node.text]


def normalize_xlsx_relationship_target(base_dir: str, target: str) -> str:
    target = target.strip()
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(base_dir, target))


def chart_title_text(chart_root: ET.Element) -> str:
    return "".join(
        node.text or ""
        for node in chart_root.findall(f".//{{{DRAWINGML_MAIN_NS}}}t")
    )


def chart_series_category_counts(chart_root: ET.Element) -> list[int]:
    counts: list[int] = []
    for series in chart_root.findall(f".//{{{CHART_NS}}}lineChart/{{{CHART_NS}}}ser"):
        point_count = series.find(
            f"{{{CHART_NS}}}cat/{{{CHART_NS}}}strLit/{{{CHART_NS}}}ptCount"
        )
        if point_count is None:
            counts.append(0)
            continue
        try:
            counts.append(int(point_count.attrib.get("val", "0")))
        except ValueError:
            counts.append(0)
    return counts


def workbook_quality_row(check_id: str, check_name: str, passed: bool, details: str) -> dict:
    return {
        "check_id": check_id,
        "check_name": check_name,
        "status": "PASS" if passed else "FAIL",
        "management_blocking": bool_text(not passed),
        "details": details,
    }


def goal_completion_audit_row(
    requirement_id: str,
    requirement: str,
    audit_status: str,
    evidence: str,
    blocking: bool,
    next_action: str,
) -> dict:
    return {
        "requirement_id": requirement_id,
        "requirement": requirement,
        "audit_status": audit_status,
        "evidence": evidence,
        "blocking": bool_text(blocking),
        "next_action": next_action,
    }


def build_goal_completion_audit_rows(cross_review: dict) -> list[dict]:
    source_ready = int(cross_review.get("source_file_count") or 0) > 0
    workbook_ready = bool(cross_review.get("excel_workbook_generated"))
    workbook_quality_clean = int(cross_review.get("workbook_quality_blocking_count") or 0) == 0
    homepage_chart_size_status = str(cross_review.get("homepage_chart_size_status") or "UNKNOWN")
    homepage_chart_semantics_status = str(cross_review.get("homepage_chart_semantics_status") or "UNKNOWN")
    visible_sensitive_text_status = str(cross_review.get("visible_sensitive_text_status") or "UNKNOWN")
    c_level_visuals_ready = (
        workbook_ready
        and homepage_chart_size_status == "PASS"
        and homepage_chart_semantics_status == "PASS"
    )
    structured_fact_count = int(cross_review.get("structured_financial_fact_count") or 0)
    metadata_signal_count = int(cross_review.get("metadata_signal_count") or 0)
    forecast_row_count = int(cross_review.get("forecast_row_count") or 0)
    cashflow_row_count = int(cross_review.get("cashflow_validation_row_count") or 0)
    internal_transfer_count = int(cross_review.get("internal_transfer_excluded_count") or 0)
    generated_amount_count = int(cross_review.get("generated_financial_amount_count") or 0)
    management_allowed = bool(cross_review.get("management_conclusion_allowed"))
    automation_ready = int(cross_review.get("automation_readiness_ready_count") or 0) > 0
    automation_status = str(cross_review.get("automation_readiness_status") or "CODEX_AUTOMATION_UNKNOWN")
    ocr_blocked = int(cross_review.get("ocr_fact_ledger_staging_preview_blocked_count") or 0)
    attachment_blocked = int(cross_review.get("attachment_reconciliation_blocking_count") or 0)

    return [
        goal_completion_audit_row(
            "source_readiness",
            "Read real DingTalk finance source folder",
            "pass" if source_ready else "blocked",
            f"source_file_count={cross_review.get('source_file_count', 0)}",
            not source_ready,
            "Restore or materialize the configured source directory" if not source_ready else "Continue extraction",
        ),
        goal_completion_audit_row(
            "native_editable_workbook",
            "Generate native editable Excel workbook from latest mother template",
            "pass" if workbook_ready and workbook_quality_clean else "blocked",
            f"workbook={cross_review.get('workbook', '')}; workbook_quality_blocking_count={cross_review.get('workbook_quality_blocking_count', 0)}",
            not (workbook_ready and workbook_quality_clean),
            "Fix workbook quality gates before any conclusion" if not workbook_quality_clean else "Keep native workbook validation enabled",
        ),
        goal_completion_audit_row(
            "c_level_visuals",
            "Keep C-level homepage visuals native and within the 18x9 inch chart limit",
            "pass" if c_level_visuals_ready else "blocked",
            (
                f"homepage_chart_size_status={homepage_chart_size_status}; "
                f"homepage_chart_semantics_status={homepage_chart_semantics_status}; "
                f"workbook_quality_blocking_count={cross_review.get('workbook_quality_blocking_count', 0)}"
            ),
            not c_level_visuals_ready,
            "Fix homepage chart size or 15/30-day semantics" if not c_level_visuals_ready else "Keep chart quality gates enabled",
        ),
        goal_completion_audit_row(
            "kmfa_metadata_transform",
            "Carry KMFA metadata signals into the workbook and review sidecars without creating financial facts",
            "pass" if metadata_signal_count > 0 else "no_metadata_signals",
            f"metadata_signal_count={metadata_signal_count}; generated_financial_amount_count={generated_amount_count}",
            False,
            "Keep metadata signals as review-only context" if metadata_signal_count > 0 else "No KMFA metadata signal rows were available in this run",
        ),
        goal_completion_audit_row(
            "company_bank_matrix",
            "Produce company-bank matrix from reviewed structured facts",
            "pass" if structured_fact_count > 0 else "pending_review",
            f"structured_financial_fact_count={structured_fact_count}",
            False,
            "Provide reviewed structured CSV rows or complete fact review" if structured_fact_count == 0 else "Review generated matrix rows",
        ),
        goal_completion_audit_row(
            "internal_transfer_netting",
            "Exclude internal transfers from operating cash flow",
            "pass" if internal_transfer_count > 0 else "pending_real_rows",
            f"internal_transfer_excluded_count={internal_transfer_count}",
            False,
            "Needs real internal_transfer rows to evidence netting" if internal_transfer_count == 0 else "Keep internal-transfer exclusion checks",
        ),
        goal_completion_audit_row(
            "operating_cashflow_validation",
            "Validate balance continuity and operating cashflow effects",
            "pass" if cashflow_row_count > 0 else "pending_real_rows",
            f"cashflow_validation_row_count={cashflow_row_count}; balance_continuity_fail_count={cross_review.get('balance_continuity_fail_count', 0)}",
            False,
            "Needs real structured ledger rows to validate cashflow" if cashflow_row_count == 0 else "Review cashflow validation rows",
        ),
        goal_completion_audit_row(
            "tax_deposit_loan_project_cost_forecast",
            "Forecast only known due-date tax/deposit/loan/project-cost items",
            "pass" if forecast_row_count > 0 else "pending_known_due_dates",
            f"forecast_row_count={forecast_row_count}",
            False,
            "Needs real due_date risk/opportunity rows" if forecast_row_count == 0 else "Review known due-date forecast rows",
        ),
        goal_completion_audit_row(
            "cross_checks",
            "Emit cross-check sidecars and block unresolved evidence issues",
            "pass" if attachment_blocked == 0 else "blocked",
            f"attachment_reconciliation_blocking_count={attachment_blocked}; workbook_quality_blocking_count={cross_review.get('workbook_quality_blocking_count', 0)}",
            attachment_blocked > 0,
            "Resolve attachment reconciliation blockers" if attachment_blocked > 0 else "Continue cross-review gates",
        ),
        goal_completion_audit_row(
            "no_hallucinated_data",
            "Do not generate hallucinated financial amounts or evidence-free forecasts",
            "pass" if generated_amount_count == 0 else "blocked",
            f"generated_financial_amount_count={generated_amount_count}",
            generated_amount_count != 0,
            "Stop and remove generated/inferred amounts" if generated_amount_count != 0 else "Keep no-hallucination gate enforced",
        ),
        goal_completion_audit_row(
            "raw_sensitive_runtime_boundary",
            "Keep raw sensitive runtime data private and out of visible management workbook surfaces",
            "pass" if visible_sensitive_text_status == "PASS" else "blocked",
            (
                "private_runtime_policy=ignored_private_runtime_only; "
                f"visible_sensitive_text_status={visible_sensitive_text_status}"
            ),
            visible_sensitive_text_status != "PASS",
            "Remove visible sensitive text before management use" if visible_sensitive_text_status != "PASS" else "Keep raw evidence in private runtime only",
        ),
        goal_completion_audit_row(
            "formal_financial_fact_promotion",
            "Promote only reviewed facts into formal financial fact layer",
            "blocked",
            f"structured_financial_fact_count={structured_fact_count}; ocr_fact_ledger_staging_preview_blocked_count={ocr_blocked}",
            True,
            "Needs explicit human/cross-review authorization before formal promotion",
        ),
        goal_completion_audit_row(
            "management_conclusion",
            "Allow C-level management conclusions only after all review gates pass",
            "pass" if management_allowed else "blocked",
            f"management_conclusion_allowed={bool_text(management_allowed)}",
            not management_allowed,
            "Keep conclusions blocked until formal facts and review gates pass" if not management_allowed else "Generate management conclusion package",
        ),
        goal_completion_audit_row(
            "automation_schedule",
            "Run under the approved local Codex automation schedule",
            "pass" if automation_ready else "external_check_required",
            f"automation_readiness_status={automation_status}; automation_readiness_ready_count={cross_review.get('automation_readiness_ready_count', 0)}",
            not automation_ready,
            "Keep Codex automation drift check green" if automation_ready else "Run check_codex_app_automation.py after code or prompt changes",
        ),
        goal_completion_audit_row(
            "github_main_runtime_contract",
            "Run through the main-only/no-branch/no-PR automation contract for skill and automation changes",
            "pass" if automation_ready else "external_check_required",
            (
                f"automation_readiness_status={automation_status}; "
                "branch_policy=main_only_no_branch_no_pr_no_worktree"
            ),
            not automation_ready,
            "Keep committing validated skill/automation changes directly to GitHub main" if automation_ready else "Restore automation readiness before claiming main sync",
        ),
    ]


def evidence_cross_review_resolution_plan_row(
    run_id: str,
    index: int,
    evidence_area: str,
    source_artifact: str,
    blocker_count: int,
    ready_count: int,
    resolution_status: str,
    required_owner_action: str,
    authorization_manifest_relative_path: str,
    next_action: str,
) -> dict:
    return {
        "evidence_resolution_plan_id": f"EVIDPLAN-{run_id}-{index:05d}",
        "evidence_area": evidence_area,
        "source_artifact": source_artifact,
        "blocker_count": str(blocker_count),
        "ready_count": str(ready_count),
        "resolution_status": resolution_status,
        "priority": "P0" if blocker_count > 0 else "P2",
        "required_owner_action": required_owner_action,
        "authorization_manifest_relative_path": authorization_manifest_relative_path,
        "automation_safe": "false",
        "source_mutation_allowed": "false",
        "fact_promotion_allowed": "false",
        "fund_ledger_write_allowed": "false",
        "management_conclusion_allowed": "false",
        "next_action": next_action,
    }


def build_evidence_cross_review_resolution_plan_rows(manifest: dict, cross_review: dict) -> list[dict]:
    run_id = manifest["run_id"]
    candidates = [
        (
            "screenshot_ocr_coverage",
            "screenshot_ocr_coverage.csv",
            int(cross_review.get("screenshot_ocr_missing_count") or 0),
            int(cross_review.get("screenshot_ocr_ready_count") or 0),
            "blocked_missing_ocr_sidecars",
            "run_or_attach_reviewed_ocr_sidecars",
            "",
            "Run bounded OCR sidecar generation or attach reviewed OCR sidecars before fact review.",
        ),
        (
            "ocr_fact_ledger_staging",
            "ocr_fact_ledger_staging_preview.csv",
            int(cross_review.get("ocr_fact_ledger_staging_preview_blocked_count") or 0),
            int(cross_review.get("ocr_fact_ledger_staging_preview_ready_count") or 0),
            "blocked_ocr_fact_owner_review_required",
            "review_ocr_fact_candidates_and_authorize_validation_only",
            ocr_fact_review_authorization_relative_path(run_id),
            "Review OCR fact candidates by metric and provide validation-only coverage before any future promotion gate.",
        ),
        (
            "chat_value_candidates",
            "chat_value_candidates.csv",
            int(cross_review.get("chat_value_candidate_count") or 0),
            0,
            "blocked_chat_value_review_required",
            "review_chat_values_and_link_to_evidence",
            fact_promotion_authorization_relative_path(run_id),
            "Review chat value candidates, link them to source evidence, then include only reviewed rows in owner authorization.",
        ),
        (
            "attachment_evidence_integrity",
            "attachment_evidence_reconciliation.csv",
            int(cross_review.get("attachment_reconciliation_blocking_count") or 0),
            int(cross_review.get("attachment_reconciliation_linked_count") or 0),
            "blocked_attachment_evidence_repair_required",
            "resolve_attachment_reconciliation_blockers",
            attachment_repair_authorization_relative_path(run_id),
            "Resolve missing attachment outputs or evidence links through the attachment repair authorization gate.",
        ),
    ]
    rows: list[dict] = []
    for candidate in candidates:
        blocker_count = candidate[2]
        if blocker_count <= 0:
            continue
        rows.append(evidence_cross_review_resolution_plan_row(run_id, len(rows) + 1, *candidate))
    return rows


def management_conclusion_gate_row(
    gate_area: str,
    gate_status: str,
    evidence: str,
    blocking: bool,
    next_action: str,
) -> dict:
    return {
        "management_gate_id": gate_area,
        "gate_area": gate_area,
        "gate_status": gate_status,
        "evidence": evidence,
        "blocking": bool_text(blocking),
        "management_conclusion_allowed": "false",
        "next_action": next_action,
    }


def management_conclusion_release_authorization_relative_path(run_id: str) -> str:
    return (
        "KMFA/metadata/fund_weekly_analysis/private_runtime/"
        f"management_conclusion_release_authorizations/{run_id}.json"
    )


def management_conclusion_release_precondition_summary(cross_review: dict) -> dict:
    source_ready = int(cross_review.get("source_file_count") or 0) > 0
    workbook_quality_blocking_count = int(cross_review.get("workbook_quality_blocking_count") or 0)
    workbook_ready = bool(cross_review.get("excel_workbook_generated")) and workbook_quality_blocking_count == 0
    fact_execution_allowed_count = int(cross_review.get("fact_promotion_execution_allowed_count") or 0)
    formalized_area_count = int(cross_review.get("fact_promotion_execution_result_formalized_area_count") or 0)
    formal_fund_ledger_row_count = int(cross_review.get("formal_fund_ledger_row_count") or 0)
    generated_amount_count = int(cross_review.get("generated_financial_amount_count") or 0)
    cashflow_row_count = int(cross_review.get("cashflow_validation_row_count") or 0)
    balance_fail_count = int(cross_review.get("balance_continuity_fail_count") or 0)
    evidence_blocking_count = sum([
        int(cross_review.get("screenshot_ocr_missing_count") or 0),
        int(cross_review.get("ocr_fact_ledger_staging_preview_blocked_count") or 0),
        int(cross_review.get("chat_value_candidate_count") or 0),
        int(cross_review.get("attachment_reconciliation_blocking_count") or 0),
    ])
    automation_ready = int(cross_review.get("automation_readiness_ready_count") or 0) > 0
    checks = {
        "source_readiness": source_ready,
        "native_workbook_quality": workbook_ready,
        "formal_fact_promotion_execution": formalized_area_count > 0 or fact_execution_allowed_count > 0,
        "formal_ledger_population": formal_fund_ledger_row_count > 0 or generated_amount_count > 0,
        "cashflow_validation": cashflow_row_count > 0 and balance_fail_count == 0,
        "evidence_cross_review": evidence_blocking_count == 0,
        "automation_schedule": automation_ready,
    }
    return {
        "pre_release_gate_count": len(checks),
        "pre_release_ready_count": sum(1 for ready in checks.values() if ready),
        "pre_release_blocking_count": sum(1 for ready in checks.values() if not ready),
        "blocking_gate_ids": [gate_id for gate_id, ready in checks.items() if not ready],
    }


def build_management_conclusion_release_authorization_template(manifest: dict, cross_review: dict) -> dict:
    summary = management_conclusion_release_precondition_summary(cross_review)
    release_authorization_id = f"MCONCRELEASE-{manifest['run_id']}-00001"
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "management_conclusion_release_validation_only",
        "template_status": "operator_review_required",
        "template_generated_from": "management_conclusion_gate.csv",
        "output_authorization_manifest_relative_path": management_conclusion_release_authorization_relative_path(
            manifest["run_id"]
        ),
        "authorized_by": "",
        "authorized_at": "",
        "authorization_ticket": "",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "operator_instruction": (
            "Review every management conclusion pre-release gate, edit authorized=true only after all gates are ready, "
            "then save a confirmed copy to output_authorization_manifest_relative_path. This template itself does not "
            "promote facts, write ledgers, mutate sources, or generate a management conclusion."
        ),
        "release_authorizations": [
            {
                "release_authorization_id": release_authorization_id,
                "pre_release_gate_count": summary["pre_release_gate_count"],
                "pre_release_ready_count": summary["pre_release_ready_count"],
                "pre_release_blocking_count": summary["pre_release_blocking_count"],
                "blocking_gate_ids": summary["blocking_gate_ids"],
                "authorization_scope": "management_conclusion_release_validation_only",
                "authorized": False,
                "authorization_note": "",
            }
        ],
    }


def load_management_conclusion_release_authorization(repo_root: Path, run_id: str) -> dict:
    relative_path = management_conclusion_release_authorization_relative_path(run_id)
    path = repo_root / relative_path
    missing = {
        "relative_path": relative_path,
        "status": "missing_release_authorization_manifest",
        "entries": {},
        "metadata": {},
    }
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_release_authorization_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_release_authorization_schema"}
    required = {
        "authorization_manifest_version": "1",
        "run_id": run_id,
        "authorization_scope": "management_conclusion_release_validation_only",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_release_authorization_schema"}
    raw_entries = payload.get("release_authorizations")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_release_authorization_schema"}
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_release_authorization_schema"}
        release_authorization_id = entry.get("release_authorization_id")
        if not isinstance(release_authorization_id, str) or not release_authorization_id:
            return {**missing, "status": "invalid_release_authorization_schema"}
        entries[release_authorization_id] = {
            "authorized": entry.get("authorized") is True,
        }
    return {
        "relative_path": relative_path,
        "status": "valid_release_authorization_manifest",
        "entries": entries,
        "metadata": {
            "authorization_ticket": str(payload.get("authorization_ticket", "")),
            "authorized_by": str(payload.get("authorized_by", "")),
            "authorized_at": str(payload.get("authorized_at", "")),
            "authorization_scope": str(payload.get("authorization_scope", "")),
        },
    }


def build_management_conclusion_release_authorization_preview(
    manifest: dict,
    repo_root: Path,
    cross_review: dict,
) -> list[dict]:
    summary = management_conclusion_release_precondition_summary(cross_review)
    authorization = load_management_conclusion_release_authorization(repo_root, manifest["run_id"])
    metadata = authorization["metadata"]
    release_authorization_id = f"MCONCRELEASE-{manifest['run_id']}-00001"
    operator_authorization_present = "false"
    validation_status = authorization["status"]
    if authorization["status"] == "valid_release_authorization_manifest":
        entry = authorization["entries"].get(release_authorization_id)
        if entry is None:
            validation_status = "release_authorization_not_found"
        elif not entry["authorized"]:
            validation_status = "release_authorization_not_true"
            operator_authorization_present = "true"
        else:
            validation_status = "valid_release_authorization_manifest"
            operator_authorization_present = "true"

    if summary["pre_release_blocking_count"] > 0:
        preview_status = "blocked_release_preconditions_not_ready"
        review_status = "pending_pre_release_gate_readiness"
        preview_reason = "Management conclusion release is blocked until all pre-release gates are ready."
    elif validation_status == "missing_release_authorization_manifest":
        preview_status = "blocked_missing_release_authorization"
        review_status = "pending_release_authorization"
        preview_reason = "Management conclusion release is blocked until a private release authorization manifest exists."
    elif validation_status != "valid_release_authorization_manifest":
        preview_status = "blocked_invalid_release_authorization"
        review_status = "pending_release_authorization"
        preview_reason = "Management conclusion release authorization is blocked because the manifest is invalid or incomplete."
    else:
        preview_status = "ready_for_management_conclusion_release_review_no_auto_conclusion"
        review_status = "pending_separate_release_run"
        preview_reason = (
            "Release authorization coverage is valid, but this runner still does not generate a management conclusion "
            "or set management_conclusion_allowed=true."
        )

    return [{
        "management_conclusion_release_preview_id": f"MCONCPREVIEW-{manifest['run_id']}-00001",
        "release_authorization_id": release_authorization_id,
        "pre_release_gate_count": str(summary["pre_release_gate_count"]),
        "pre_release_ready_count": str(summary["pre_release_ready_count"]),
        "pre_release_blocking_count": str(summary["pre_release_blocking_count"]),
        "blocking_gate_ids": "|".join(summary["blocking_gate_ids"]),
        "authorization_manifest_relative_path": authorization["relative_path"],
        "operator_authorization_present": operator_authorization_present,
        "authorization_validation_status": validation_status,
        "authorization_ticket": metadata.get("authorization_ticket", ""),
        "authorized_by": metadata.get("authorized_by", ""),
        "authorized_at": metadata.get("authorized_at", ""),
        "authorization_scope": metadata.get("authorization_scope", ""),
        "preview_status": preview_status,
        "management_conclusion_allowed": "false",
        "preview_reason": preview_reason,
        "review_status": review_status,
    }]


def build_management_conclusion_gate_rows(cross_review: dict) -> list[dict]:
    source_ready = int(cross_review.get("source_file_count") or 0) > 0
    workbook_quality_blocking_count = int(cross_review.get("workbook_quality_blocking_count") or 0)
    workbook_ready = bool(cross_review.get("excel_workbook_generated")) and workbook_quality_blocking_count == 0
    fact_execution_allowed_count = int(cross_review.get("fact_promotion_execution_allowed_count") or 0)
    fact_execution_ready_count = int(cross_review.get("fact_promotion_execution_gate_ready_count") or 0)
    fact_execution_blocked_count = int(cross_review.get("fact_promotion_execution_gate_blocked_count") or 0)
    formalized_area_count = int(cross_review.get("fact_promotion_execution_result_formalized_area_count") or 0)
    formal_fund_ledger_row_count = int(cross_review.get("formal_fund_ledger_row_count") or 0)
    generated_amount_count = int(cross_review.get("generated_financial_amount_count") or 0)
    cashflow_row_count = int(cross_review.get("cashflow_validation_row_count") or 0)
    balance_fail_count = int(cross_review.get("balance_continuity_fail_count") or 0)
    evidence_blocking_count = sum([
        int(cross_review.get("screenshot_ocr_missing_count") or 0),
        int(cross_review.get("ocr_fact_ledger_staging_preview_blocked_count") or 0),
        int(cross_review.get("chat_value_candidate_count") or 0),
        int(cross_review.get("attachment_reconciliation_blocking_count") or 0),
    ])
    automation_ready = int(cross_review.get("automation_readiness_ready_count") or 0) > 0
    automation_status = str(cross_review.get("automation_readiness_status") or "CODEX_AUTOMATION_UNKNOWN")
    release_validation_status = str(
        cross_review.get("management_conclusion_release_authorization_validation_status")
        or "missing_release_authorization_manifest"
    )
    release_preview_status = str(
        cross_review.get("management_conclusion_release_authorization_preview_status")
        or "blocked_missing_release_authorization"
    )
    release_precondition_blocking_count = int(
        cross_review.get("management_conclusion_release_precondition_blocking_count") or 0
    )

    cashflow_ready = cashflow_row_count > 0 and balance_fail_count == 0
    return [
        management_conclusion_gate_row(
            "source_readiness",
            "ready" if source_ready else "blocked_source_not_ready",
            f"source_file_count={cross_review.get('source_file_count', 0)}",
            not source_ready,
            "Restore configured source folder before management conclusion" if not source_ready else "Keep source readiness gate active",
        ),
        management_conclusion_gate_row(
            "native_workbook_quality",
            "ready" if workbook_ready else "blocked_workbook_quality",
            f"excel_workbook_generated={bool_text(bool(cross_review.get('excel_workbook_generated')))}; workbook_quality_blocking_count={workbook_quality_blocking_count}",
            not workbook_ready,
            "Fix workbook quality blockers before management conclusion" if not workbook_ready else "Keep workbook quality checks active",
        ),
        management_conclusion_gate_row(
            "formal_fact_promotion_execution",
            (
                "ready_formal_ledger_sidecar_written"
                if formalized_area_count > 0
                else ("ready" if fact_execution_allowed_count > 0 else "blocked_fact_promotion_not_executed")
            ),
            (
                f"fact_promotion_execution_allowed_count={fact_execution_allowed_count}; "
                f"fact_promotion_execution_result_formalized_area_count={formalized_area_count}; "
                f"fact_promotion_execution_gate_ready_count={fact_execution_ready_count}; "
                f"fact_promotion_execution_gate_blocked_count={fact_execution_blocked_count}"
            ),
            formalized_area_count == 0 and fact_execution_allowed_count == 0,
            "Run a separately approved controlled fact-promotion execution before management conclusion",
        ),
        management_conclusion_gate_row(
            "formal_ledger_population",
            (
                "ready_formal_ledger_sidecar"
                if formal_fund_ledger_row_count > 0
                else ("ready" if generated_amount_count > 0 else "blocked_no_formal_ledger_rows")
            ),
            f"formal_fund_ledger_row_count={formal_fund_ledger_row_count}; generated_financial_amount_count={generated_amount_count}",
            formal_fund_ledger_row_count == 0 and generated_amount_count == 0,
            "Populate formal reviewed ledger facts before management conclusion",
        ),
        management_conclusion_gate_row(
            "cashflow_validation",
            "ready" if cashflow_ready else ("blocked_balance_continuity" if balance_fail_count else "blocked_cashflow_validation_missing"),
            f"cashflow_validation_row_count={cashflow_row_count}; balance_continuity_fail_count={balance_fail_count}",
            not cashflow_ready,
            "Validate balance continuity and operating cashflow before management conclusion",
        ),
        management_conclusion_gate_row(
            "evidence_cross_review",
            "ready" if evidence_blocking_count == 0 else "blocked_unresolved_review_evidence",
            f"evidence_blocking_count={evidence_blocking_count}",
            evidence_blocking_count > 0,
            "Resolve OCR/chat/attachment review blockers before management conclusion" if evidence_blocking_count > 0 else "Keep cross-review evidence with management gate",
        ),
        management_conclusion_gate_row(
            "automation_schedule",
            "ready" if automation_ready else "external_check_required",
            f"automation_readiness_status={automation_status}; automation_readiness_ready_count={cross_review.get('automation_readiness_ready_count', 0)}",
            not automation_ready,
            "Keep Codex automation schedule readiness evidence with each run" if automation_ready else "Run check_codex_app_automation.py before claiming scheduled readiness",
        ),
        management_conclusion_gate_row(
            "management_conclusion_final_authorization",
            "blocked_management_conclusion_release_not_authorized",
            (
                "management_conclusion_allowed=false; final_owner_release_authorization=false; "
                f"release_authorization_validation_status={release_validation_status}; "
                f"release_authorization_preview_status={release_preview_status}; "
                f"pre_release_blocking_count={release_precondition_blocking_count}"
            ),
            True,
            "Approve a separate management conclusion release after all evidence, ledger, cashflow, workbook, and automation gates are ready",
        ),
    ]


OWNER_ACTION_BY_GATE = {
    "source_readiness": (
        "RESTORE_OR_MATERIALIZE_VERIFIED_SOURCE",
        "P0",
        True,
    ),
    "native_workbook_quality": (
        "FIX_NATIVE_WORKBOOK_QUALITY_BLOCKERS",
        "P0",
        True,
    ),
    "formal_fact_promotion_execution": (
        "APPROVE_CONTROLLED_FACT_PROMOTION_EXECUTION",
        "P0",
        True,
    ),
    "formal_ledger_population": (
        "POPULATE_FORMAL_REVIEWED_LEDGER_FACTS",
        "P0",
        True,
    ),
    "cashflow_validation": (
        "VALIDATE_CASHFLOW_AND_BALANCE_CONTINUITY",
        "P1",
        True,
    ),
    "evidence_cross_review": (
        "RESOLVE_EVIDENCE_CROSS_REVIEW_BLOCKERS",
        "P0",
        True,
    ),
    "automation_schedule": (
        "VERIFY_CODEX_AUTOMATION_SCHEDULE",
        "P1",
        False,
    ),
    "management_conclusion_final_authorization": (
        "APPROVE_MANAGEMENT_CONCLUSION_RELEASE",
        "P0",
        True,
    ),
}


def build_owner_action_queue_rows(management_conclusion_gate_rows: list[dict]) -> list[dict]:
    rows = []
    for gate_row in management_conclusion_gate_rows:
        if gate_row.get("blocking") != "true":
            continue
        gate_area = gate_row["gate_area"]
        action_type, priority, requires_owner_authorization = OWNER_ACTION_BY_GATE.get(
            gate_area,
            (f"RESOLVE_{gate_area.upper()}_GATE", "P1", True),
        )
        rows.append({
            "owner_action_id": f"OWNER-ACTION-{len(rows) + 1:03d}",
            "source_gate": gate_area,
            "source_gate_status": gate_row["gate_status"],
            "action_type": action_type,
            "priority": priority,
            "action_status": "external_check_required" if gate_area == "automation_schedule" else "pending_owner_action",
            "blocking": gate_row["blocking"],
            "automation_safe": "false",
            "requires_owner_authorization": bool_text(requires_owner_authorization),
            "source_mutation_allowed": "false",
            "fact_promotion_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "management_conclusion_allowed": "false",
            "evidence": gate_row["evidence"],
            "recommended_next_step": gate_row["next_action"],
        })
    return rows


def fact_promotion_review_packet_row(
    packet_id: str,
    review_area: str,
    candidate_count: int,
    ready_count: int,
    blocked_count: int,
    review_status: str,
    source_artifact: str,
    authorization_required: bool,
    next_action: str,
) -> dict:
    return {
        "review_packet_id": packet_id,
        "review_area": review_area,
        "candidate_count": str(candidate_count),
        "ready_count": str(ready_count),
        "blocked_count": str(blocked_count),
        "review_status": review_status,
        "source_artifact": source_artifact,
        "authorization_required": bool_text(authorization_required),
        "fund_ledger_write_allowed": "false",
        "financial_fact_promoted": "false",
        "next_action": next_action,
    }


def build_fact_promotion_review_packet_rows(
    manifest: dict,
    structured: dict,
    screenshot_ocr_coverage_rows: list[dict],
    ocr_fact_ledger_staging_preview_rows: list[dict],
    chat_value_candidates: list[dict],
    attachment_reconciliation_rows: list[dict],
    workbook_quality_rows: list[dict],
    goal_completion_audit_rows: list[dict],
) -> list[dict]:
    run_id = manifest["run_id"]
    structured_count = len(structured["fund_rows"])
    ocr_ready = sum(
        1 for row in ocr_fact_ledger_staging_preview_rows
        if row["staging_preview_status"] == "ready_for_ledger_staging_review_no_write"
    )
    ocr_blocked = len(ocr_fact_ledger_staging_preview_rows) - ocr_ready
    ocr_coverage_count = len(screenshot_ocr_coverage_rows)
    ocr_coverage_ready = sum(
        1 for row in screenshot_ocr_coverage_rows
        if row["ocr_coverage_status"] == "ocr_text_sidecar_present_pending_review"
    )
    ocr_coverage_missing = sum(
        1 for row in screenshot_ocr_coverage_rows
        if row["ocr_coverage_status"] == "ocr_text_sidecar_missing"
    )
    chat_count = len(chat_value_candidates)
    attachment_blocked = sum(1 for row in attachment_reconciliation_rows if row["reconciliation_status"].endswith("_blocking"))
    workbook_blocked = sum(1 for row in workbook_quality_rows if row["management_blocking"] == "true")
    goal_blocked = sum(1 for row in goal_completion_audit_rows if row["blocking"] == "true")

    return [
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00001",
            "structured_csv_facts",
            structured_count,
            structured_count,
            0,
            "pending_cross_review" if structured_count else "no_structured_rows",
            "fund_ledger.csv",
            structured_count > 0,
            "Review structured CSV source rows before formal fact promotion" if structured_count else "Provide reviewed structured CSV rows",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00002",
            "ocr_fact_ledger_staging",
            len(ocr_fact_ledger_staging_preview_rows),
            ocr_ready,
            ocr_blocked,
            "blocked_missing_operator_authorization" if ocr_blocked else ("ready_for_human_ledger_staging_review_no_write" if ocr_ready else "no_ocr_fact_candidates"),
            "ocr_fact_ledger_staging_preview.csv",
            len(ocr_fact_ledger_staging_preview_rows) > 0,
            "Review OCR ledger staging rows and provide explicit owner authorization" if ocr_fact_ledger_staging_preview_rows else "Generate OCR fact candidates first",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00003",
            "chat_value_candidates",
            chat_count,
            0,
            chat_count,
            "pending_human_review" if chat_count else "no_chat_value_candidates",
            "chat_value_candidates.csv",
            chat_count > 0,
            "Review chat value candidates and link to source evidence" if chat_count else "No chat value candidate review required",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00004",
            "attachment_evidence_integrity",
            len(attachment_reconciliation_rows),
            len(attachment_reconciliation_rows) - attachment_blocked,
            attachment_blocked,
            "blocked_evidence_integrity" if attachment_blocked else ("pass" if attachment_reconciliation_rows else "no_attachment_reconciliation_rows"),
            "attachment_evidence_reconciliation.csv",
            attachment_blocked > 0,
            "Resolve attachment evidence blockers before fact promotion" if attachment_blocked else "Keep attachment reconciliation evidence with review packet",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00005",
            "workbook_quality",
            len(workbook_quality_rows),
            len(workbook_quality_rows) - workbook_blocked,
            workbook_blocked,
            "blocked_workbook_quality" if workbook_blocked else "pass",
            "workbook_quality_checks.csv",
            workbook_blocked > 0,
            "Fix workbook quality gates before management conclusion" if workbook_blocked else "Keep workbook quality evidence with review packet",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00006",
            "goal_completion_audit",
            len(goal_completion_audit_rows),
            len(goal_completion_audit_rows) - goal_blocked,
            goal_blocked,
            "blocked_goal_requirements" if goal_blocked else "pass",
            "goal_completion_audit.csv",
            goal_blocked > 0,
            "Resolve blocking goal audit rows before completion claim" if goal_blocked else "Goal audit has no blocking rows",
        ),
        fact_promotion_review_packet_row(
            f"FPRP-{run_id}-00007",
            "screenshot_ocr_coverage",
            ocr_coverage_count,
            ocr_coverage_ready,
            ocr_coverage_missing,
            "blocked_ocr_sidecar_missing" if ocr_coverage_missing else ("pass" if ocr_coverage_count else "no_screenshot_rows"),
            "screenshot_ocr_coverage.csv",
            False,
            "Run scheduled OCR sidecar generation or attach reviewed OCR sidecars" if ocr_coverage_missing else "Keep OCR coverage evidence with review packet",
        ),
    ]


def fact_promotion_owner_review_status(row: dict) -> tuple[str, str]:
    candidate_count = int(row["candidate_count"])
    blocked_count = int(row["blocked_count"])
    ready_count = int(row["ready_count"])
    if candidate_count == 0:
        return "no_candidate_rows", "No candidate rows exist for this review area."
    if blocked_count > 0:
        return "blocked_review_required", "Review blockers must be resolved before owner authorization can support any future fact promotion execution."
    if ready_count > 0:
        return "ready_for_owner_review_no_promotion", "Rows are ready for owner review, but this batch does not promote facts or write the formal ledger."
    return "pending_owner_review", "Rows require owner review before any future controlled fact promotion execution."


def build_fact_promotion_owner_review_batch_rows(manifest: dict, review_packet_rows: list[dict]) -> list[dict]:
    authorization_path = fact_promotion_authorization_relative_path(manifest["run_id"])
    rows = []
    for row in review_packet_rows:
        owner_review_status, batch_reason = fact_promotion_owner_review_status(row)
        priority = "P0" if int(row["blocked_count"]) > 0 else ("P1" if int(row["candidate_count"]) > 0 else "P2")
        rows.append({
            "owner_review_batch_id": f"FPOWNERBATCH-{manifest['run_id']}-{len(rows) + 1:05d}",
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "candidate_count": row["candidate_count"],
            "ready_count": row["ready_count"],
            "blocked_count": row["blocked_count"],
            "priority": priority,
            "owner_review_status": owner_review_status,
            "owner_authorization_required": row["authorization_required"],
            "authorization_manifest_relative_path": authorization_path,
            "authorization_scope": "fact_promotion_review_packet_validation_only",
            "financial_fact_promotion_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "batch_reason": batch_reason,
            "recommended_owner_action": row["next_action"],
        })
    return rows


def fact_promotion_authorization_relative_path(run_id: str) -> str:
    return f"KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_authorizations/{run_id}.json"


def build_fact_promotion_authorization_template(manifest: dict, review_packet_rows: list[dict]) -> dict:
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "fact_promotion_review_packet_validation_only",
        "template_status": "operator_review_required",
        "template_generated_from": "fact_promotion_review_packet.csv",
        "output_authorization_manifest_relative_path": fact_promotion_authorization_relative_path(manifest["run_id"]),
        "authorized_by": "",
        "authorized_at": "",
        "authorization_ticket": "",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "operator_instruction": "Review each fact promotion packet row, edit authorized=true only where approved, then save a confirmed copy to output_authorization_manifest_relative_path. This template itself does not authorize, promote financial facts, write fund_ledger.csv, or unlock management conclusions.",
        "review_packet_authorizations": [
            {
                "review_packet_id": row["review_packet_id"],
                "review_area": row["review_area"],
                "candidate_count": row["candidate_count"],
                "ready_count": row["ready_count"],
                "blocked_count": row["blocked_count"],
                "review_status": row["review_status"],
                "source_artifact": row["source_artifact"],
                "authorization_required": row["authorization_required"],
                "fund_ledger_write_allowed": row["fund_ledger_write_allowed"],
                "financial_fact_promoted": row["financial_fact_promoted"],
                "next_action": row["next_action"],
                "authorized": False,
                "authorization_note": "",
            }
            for row in review_packet_rows
        ],
    }


def load_fact_promotion_authorization(repo_root: Path, run_id: str) -> dict:
    relative_path = fact_promotion_authorization_relative_path(run_id)
    path = repo_root / relative_path
    missing = {
        "relative_path": relative_path,
        "status": "missing_authorization_manifest",
        "entries": {},
        "metadata": {},
    }
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_authorization_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_authorization_schema"}
    required = {
        "authorization_manifest_version": "1",
        "run_id": run_id,
        "authorization_scope": "fact_promotion_review_packet_validation_only",
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_authorization_schema"}
    raw_entries = payload.get("review_packet_authorizations")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_authorization_schema"}
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_authorization_schema"}
        review_packet_id = entry.get("review_packet_id")
        review_area = entry.get("review_area")
        if not isinstance(review_packet_id, str) or not review_packet_id:
            return {**missing, "status": "invalid_authorization_schema"}
        if not isinstance(review_area, str) or not review_area:
            return {**missing, "status": "invalid_authorization_schema"}
        entries[review_packet_id] = {
            "review_area": review_area,
            "authorized": entry.get("authorized") is True,
        }
    return {
        "relative_path": relative_path,
        "status": "valid_authorization_manifest",
        "entries": entries,
        "metadata": {
            "authorization_ticket": str(payload.get("authorization_ticket", "")),
            "authorized_by": str(payload.get("authorized_by", "")),
            "authorized_at": str(payload.get("authorized_at", "")),
            "authorization_scope": str(payload.get("authorization_scope", "")),
        },
    }


def fact_promotion_authorization_status(row: dict, authorization: dict) -> tuple[str, str, str, str]:
    if row["authorization_required"] != "true":
        candidate_count = int(row["candidate_count"])
        ready_count = int(row["ready_count"])
        if candidate_count == 0:
            return (
                "false",
                "authorization_not_required",
                "authorization_not_required_no_candidate_facts",
                "Owner authorization is not required because this review area has no candidate facts.",
            )
        if ready_count > 0:
            return (
                "false",
                "authorization_not_required",
                "authorization_not_required_review_area_ready",
                "Owner authorization is not required for this evidence-only review area; no facts are promoted or written.",
            )
        return (
            "false",
            "authorization_not_required",
            "authorization_not_required_no_ready_facts",
            "Owner authorization is not required because this review area has no ready fact rows.",
        )
    auth_status = authorization["status"]
    if auth_status == "missing_authorization_manifest":
        return (
            "false",
            "missing_authorization_manifest",
            "blocked_missing_operator_authorization",
            "Fact promotion is blocked until a private owner authorization manifest exists.",
        )
    if auth_status != "valid_authorization_manifest":
        return (
            "false",
            auth_status,
            "blocked_invalid_operator_authorization",
            "Fact promotion authorization is blocked because the owner authorization manifest is invalid.",
        )
    entry = authorization["entries"].get(row["review_packet_id"])
    if entry is None:
        return (
            "false",
            "review_packet_not_authorized",
            "blocked_review_packet_not_authorized",
            "Fact promotion authorization is blocked because this review packet row is not covered by the owner authorization manifest.",
        )
    if entry["review_area"] != row["review_area"]:
        return (
            "true",
            "authorization_review_area_mismatch",
            "blocked_authorization_area_mismatch",
            "Fact promotion authorization is blocked because the authorization review_area does not match the review packet row.",
        )
    if not entry["authorized"]:
        return (
            "true",
            "review_packet_authorization_not_true",
            "blocked_review_packet_not_authorized",
            "Fact promotion authorization is blocked because this review packet row is not explicitly authorized.",
        )
    return (
        "true",
        "valid_manifest_validation_only",
        "ready_for_owner_review_no_fact_promotion",
        "Owner authorization manifest is valid for this review packet row, but this runner only previews authorization coverage and does not promote facts, write fund_ledger.csv, or unlock management conclusions.",
    )


def build_fact_promotion_authorization_preview(manifest: dict, repo_root: Path, review_packet_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    authorization = load_fact_promotion_authorization(repo_root, manifest["run_id"])
    metadata = authorization["metadata"]
    for row in review_packet_rows:
        authorization_present, validation_status, preview_status, preview_reason = fact_promotion_authorization_status(row, authorization)
        rows.append({
            "authorization_preview_id": f"FPPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "candidate_count": row["candidate_count"],
            "ready_count": row["ready_count"],
            "blocked_count": row["blocked_count"],
            "operator_authorization_required": row["authorization_required"],
            "authorization_manifest_relative_path": authorization["relative_path"],
            "operator_authorization_present": authorization_present,
            "authorization_validation_status": validation_status,
            "authorization_ticket": metadata.get("authorization_ticket", ""),
            "authorized_by": metadata.get("authorized_by", ""),
            "authorized_at": metadata.get("authorized_at", ""),
            "authorization_scope": metadata.get("authorization_scope", ""),
            "preview_status": preview_status,
            "financial_fact_promotion_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "preview_reason": preview_reason,
            "source_artifact": row["source_artifact"],
            "review_status": "pending_owner_authorization" if authorization_present == "false" else "pending_owner_impact_review",
        })
    return rows


def fact_promotion_execution_status(review_packet_row: dict, authorization_preview_row: dict) -> tuple[str, str, str]:
    validation_status = authorization_preview_row["authorization_validation_status"]
    if validation_status == "authorization_not_required":
        candidate_count = int(review_packet_row["candidate_count"])
        ready_count = int(review_packet_row["ready_count"])
        if candidate_count == 0:
            return (
                "not_required_no_candidate_facts",
                "no_fact_promotion_required",
                "No fact promotion execution is required because this review area has no candidate facts.",
            )
        if ready_count > 0:
            return (
                "not_required_review_area_ready",
                "review_evidence_retained_no_fact_promotion",
                "This evidence-only review area is retained for audit but does not require fact-promotion execution.",
            )
        return (
            "not_required_no_ready_facts",
            "no_fact_promotion_required",
            "No fact promotion execution is required because this review area has no ready fact rows.",
        )
    if validation_status != "valid_manifest_validation_only":
        return (
            authorization_preview_row["preview_status"],
            "pending_owner_authorization",
            "Formal fact promotion execution is blocked until the owner authorization coverage is valid.",
        )
    if int(review_packet_row["blocked_count"]) > 0:
        return (
            "blocked_unresolved_review_area",
            "pending_review_blocker_resolution",
            "Formal fact promotion execution is blocked because this review area still has blocking rows.",
        )
    if int(review_packet_row["candidate_count"]) == 0:
        return (
            "blocked_no_candidate_facts",
            "pending_candidate_generation",
            "Formal fact promotion execution is blocked because this review area has no candidate facts.",
        )
    if int(review_packet_row["ready_count"]) == 0:
        return (
            "blocked_no_ready_facts",
            "pending_ready_fact_review",
            "Formal fact promotion execution is blocked because this review area has no ready rows.",
        )
    return (
        "ready_for_controlled_fact_promotion_execution",
        "pending_controlled_execution_authorization",
        "This review area is ready for a future controlled fact-promotion execution run, but this runner does not execute promotion or write fund_ledger.csv.",
    )


def build_fact_promotion_execution_gate(
    manifest: dict,
    review_packet_rows: list[dict],
    authorization_preview_rows: list[dict],
) -> list[dict]:
    preview_by_packet_id = {row["review_packet_id"]: row for row in authorization_preview_rows}
    rows: list[dict] = []
    for row in review_packet_rows:
        preview = preview_by_packet_id[row["review_packet_id"]]
        execution_gate_status, review_status, gate_reason = fact_promotion_execution_status(row, preview)
        rows.append({
            "execution_gate_id": f"FPEXEC-{manifest['run_id']}-{len(rows) + 1:05d}",
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "candidate_count": row["candidate_count"],
            "ready_count": row["ready_count"],
            "blocked_count": row["blocked_count"],
            "authorization_validation_status": preview["authorization_validation_status"],
            "authorization_preview_status": preview["preview_status"],
            "execution_gate_status": execution_gate_status,
            "fact_promotion_execution_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "gate_reason": gate_reason,
            "source_artifact": row["source_artifact"],
            "review_status": review_status,
        })
    return rows


def build_fact_promotion_execution_dry_run_rows(manifest: dict, execution_gate_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in execution_gate_rows:
        ready_for_execution = row["execution_gate_status"] == "ready_for_controlled_fact_promotion_execution"
        dry_run_status = (
            "ready_for_controlled_execution_preview_no_write"
            if ready_for_execution
            else row["execution_gate_status"]
        )
        impact_count = int(row["ready_count"]) if ready_for_execution else 0
        rows.append({
            "dry_run_id": f"FPDRYRUN-{manifest['run_id']}-{len(rows) + 1:05d}",
            "execution_gate_id": row["execution_gate_id"],
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "candidate_count": row["candidate_count"],
            "ready_count": row["ready_count"],
            "blocked_count": row["blocked_count"],
            "execution_gate_status": row["execution_gate_status"],
            "dry_run_status": dry_run_status,
            "dry_run_impact_count": str(impact_count),
            "fact_promotion_execution_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "dry_run_reason": (
                "This row previews impact for a future separately approved controlled execution run; no facts are promoted and no ledger rows are written."
                if ready_for_execution
                else "Dry-run impact is zero because this execution gate is not ready for controlled fact promotion."
            ),
        })
    return rows


def build_fact_promotion_execution_plan_rows(manifest: dict, dry_run_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for row in dry_run_rows:
        ready_for_execution_plan = row["dry_run_status"] == "ready_for_controlled_execution_preview_no_write"
        blocked_before_plan = row["dry_run_status"].startswith("blocked_")
        if ready_for_execution_plan:
            execution_plan_status = "ready_for_owner_execution_authorization_no_write"
            required_authorization_scope = "controlled_fact_promotion_execution"
            required_owner_action = "approve_controlled_fact_promotion_execution_manifest"
            planned_impact_count = int(row["dry_run_impact_count"])
            plan_reason = (
                "This review area is ready for an owner-authorized controlled execution plan, "
                "but this runner still performs no fact promotion and no fund ledger write."
            )
        elif blocked_before_plan:
            execution_plan_status = "blocked_before_execution_plan"
            required_authorization_scope = "resolve_blockers_and_owner_authorization"
            required_owner_action = "resolve_review_blockers_before_execution"
            planned_impact_count = 0
            plan_reason = "Execution planning is blocked because the dry-run gate is blocked."
        else:
            execution_plan_status = "not_required_no_execution_plan"
            required_authorization_scope = "not_required"
            required_owner_action = "none"
            planned_impact_count = 0
            plan_reason = "Execution planning is not required for this no-op review area."
        rows.append({
            "execution_plan_id": f"FPEXECPLAN-{manifest['run_id']}-{len(rows) + 1:05d}",
            "dry_run_id": row["dry_run_id"],
            "execution_gate_id": row["execution_gate_id"],
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "candidate_count": row["candidate_count"],
            "ready_count": row["ready_count"],
            "blocked_count": row["blocked_count"],
            "dry_run_status": row["dry_run_status"],
            "dry_run_impact_count": row["dry_run_impact_count"],
            "execution_plan_status": execution_plan_status,
            "required_authorization_scope": required_authorization_scope,
            "required_owner_action": required_owner_action,
            "planned_impact_count": str(planned_impact_count),
            "source_mutation_allowed": "false",
            "fact_promotion_execution_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "plan_reason": plan_reason,
        })
    return rows


def fact_promotion_execution_authorization_relative_path(run_id: str) -> str:
    return (
        "KMFA/metadata/fund_weekly_analysis/private_runtime/"
        f"fact_promotion_execution_authorizations/{run_id}.json"
    )


def build_fact_promotion_execution_authorization_template(manifest: dict, execution_plan_rows: list[dict]) -> dict:
    return {
        "authorization_manifest_version": "1",
        "run_id": manifest["run_id"],
        "authorization_scope": "controlled_fact_promotion_execution",
        "template_status": "operator_review_required",
        "template_generated_from": "fact_promotion_execution_plan.csv",
        "output_authorization_manifest_relative_path": fact_promotion_execution_authorization_relative_path(
            manifest["run_id"]
        ),
        "authorized_by": "",
        "authorized_at": "",
        "authorization_ticket": "",
        "source_mutation_allowed": False,
        "fact_promotion_execution_allowed": False,
        "fund_ledger_write_allowed": False,
        "financial_fact_promoted": False,
        "management_conclusion_allowed": False,
        "operator_instruction": (
            "Review each execution plan row, edit authorized=true only where approved, then save a confirmed copy "
            "to output_authorization_manifest_relative_path. This template itself does not execute fact promotion, "
            "write fund_ledger.csv, mutate source files, or unlock management conclusions."
        ),
        "execution_plan_authorizations": [
            {
                "execution_plan_id": row["execution_plan_id"],
                "review_area": row["review_area"],
                "execution_plan_status": row["execution_plan_status"],
                "planned_impact_count": row["planned_impact_count"],
                "required_authorization_scope": row["required_authorization_scope"],
                "source_artifact": row["source_artifact"],
                "source_mutation_allowed": row["source_mutation_allowed"],
                "fund_ledger_write_allowed": row["fund_ledger_write_allowed"],
                "financial_fact_promoted": row["financial_fact_promoted"],
                "authorized": False,
                "authorization_note": "",
            }
            for row in execution_plan_rows
        ],
    }


def load_fact_promotion_execution_authorization(repo_root: Path, run_id: str) -> dict:
    relative_path = fact_promotion_execution_authorization_relative_path(run_id)
    path = repo_root / relative_path
    missing = {
        "relative_path": relative_path,
        "status": "missing_execution_authorization_manifest",
        "entries": {},
        "metadata": {},
    }
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {**missing, "status": "invalid_execution_authorization_json"}
    if not isinstance(payload, dict):
        return {**missing, "status": "invalid_execution_authorization_schema"}
    required = {
        "authorization_manifest_version": "1",
        "run_id": run_id,
        "authorization_scope": "controlled_fact_promotion_execution",
        "source_mutation_allowed": False,
        "fact_promotion_execution_allowed": False,
        "fund_ledger_write_allowed": False,
        "financial_fact_promoted": False,
        "management_conclusion_allowed": False,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        return {**missing, "status": "invalid_execution_authorization_schema"}
    raw_entries = payload.get("execution_plan_authorizations")
    if not isinstance(raw_entries, list):
        return {**missing, "status": "invalid_execution_authorization_schema"}
    entries = {}
    for entry in raw_entries:
        if not isinstance(entry, dict):
            return {**missing, "status": "invalid_execution_authorization_schema"}
        execution_plan_id = entry.get("execution_plan_id")
        review_area = entry.get("review_area")
        if not isinstance(execution_plan_id, str) or not execution_plan_id:
            return {**missing, "status": "invalid_execution_authorization_schema"}
        if not isinstance(review_area, str) or not review_area:
            return {**missing, "status": "invalid_execution_authorization_schema"}
        entries[execution_plan_id] = {
            "review_area": review_area,
            "authorized": entry.get("authorized") is True,
        }
    return {
        "relative_path": relative_path,
        "status": "valid_execution_authorization_manifest",
        "entries": entries,
        "metadata": {
            "authorization_ticket": str(payload.get("authorization_ticket", "")),
            "authorized_by": str(payload.get("authorized_by", "")),
            "authorized_at": str(payload.get("authorized_at", "")),
            "authorization_scope": str(payload.get("authorization_scope", "")),
        },
    }


def fact_promotion_execution_authorization_coverage_complete(
    execution_plan_rows: list[dict],
    authorization: dict,
) -> bool:
    if authorization["status"] != "valid_execution_authorization_manifest":
        return False
    required_rows = [
        row for row in execution_plan_rows
        if row["execution_plan_status"] == "ready_for_owner_execution_authorization_no_write"
    ]
    for row in required_rows:
        entry = authorization["entries"].get(row["execution_plan_id"])
        if entry is None:
            return False
        if entry["review_area"] != row["review_area"]:
            return False
        if not entry["authorized"]:
            return False
    return True


def fact_promotion_execution_authorization_status(
    row: dict,
    authorization: dict,
    complete_required_coverage: bool,
) -> tuple[str, str, str, str, str]:
    if row["execution_plan_status"] != "ready_for_owner_execution_authorization_no_write":
        if row["execution_plan_status"].startswith("blocked_"):
            return (
                "true",
                "execution_plan_not_ready",
                "blocked_execution_plan_not_ready",
                "Execution authorization cannot be accepted until this execution plan row is ready.",
                "pending_execution_plan_readiness",
            )
        return (
            "false",
            "authorization_not_required",
            "not_required_no_execution_authorization",
            "Execution authorization is not required for this no-op execution plan row.",
            "no_execution_authorization_required",
        )
    auth_status = authorization["status"]
    if auth_status == "missing_execution_authorization_manifest":
        return (
            "false",
            auth_status,
            "blocked_missing_execution_authorization",
            "Controlled fact-promotion execution is blocked until a private execution authorization manifest exists.",
            "pending_owner_execution_authorization",
        )
    if auth_status != "valid_execution_authorization_manifest":
        return (
            "false",
            auth_status,
            "blocked_invalid_execution_authorization",
            "Controlled fact-promotion execution is blocked because the execution authorization manifest is invalid.",
            "pending_owner_execution_authorization",
        )
    entry = authorization["entries"].get(row["execution_plan_id"])
    if entry is None:
        return (
            "false",
            "execution_plan_not_authorized",
            "blocked_execution_plan_not_authorized",
            "Controlled fact-promotion execution is blocked because this execution plan row is not authorized.",
            "pending_owner_execution_authorization",
        )
    if entry["review_area"] != row["review_area"]:
        return (
            "true",
            "execution_authorization_review_area_mismatch",
            "blocked_execution_authorization_area_mismatch",
            "Controlled fact-promotion execution is blocked because authorization review_area does not match the plan.",
            "pending_owner_execution_authorization",
        )
    if not entry["authorized"]:
        return (
            "true",
            "execution_plan_authorization_not_true",
            "blocked_execution_plan_not_authorized",
            "Controlled fact-promotion execution is blocked because this execution plan row is not explicitly authorized.",
            "pending_owner_execution_authorization",
        )
    if not complete_required_coverage:
        return (
            "true",
            "valid_execution_authorization_manifest_incomplete_required_coverage",
            "blocked_incomplete_execution_authorization_coverage",
            "Controlled fact-promotion execution is blocked because every ready execution plan row must be explicitly authorized before any apply gate can proceed.",
            "pending_owner_execution_authorization",
        )
    return (
        "true",
        "valid_execution_authorization_manifest",
        "ready_for_controlled_execution_run_no_write",
        "Execution authorization coverage is valid for this row, but this runner still performs no promotion or ledger write.",
        "pending_controlled_execution_impact_review",
    )


def build_fact_promotion_execution_authorization_preview(
    manifest: dict,
    repo_root: Path,
    execution_plan_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    authorization = load_fact_promotion_execution_authorization(repo_root, manifest["run_id"])
    metadata = authorization["metadata"]
    complete_required_coverage = fact_promotion_execution_authorization_coverage_complete(
        execution_plan_rows,
        authorization,
    )
    for row in execution_plan_rows:
        required, validation_status, preview_status, preview_reason, review_status = (
            fact_promotion_execution_authorization_status(row, authorization, complete_required_coverage)
        )
        rows.append({
            "execution_authorization_preview_id": f"FPEXEAUTHPREVIEW-{manifest['run_id']}-{len(rows) + 1:05d}",
            "execution_plan_id": row["execution_plan_id"],
            "dry_run_id": row["dry_run_id"],
            "execution_gate_id": row["execution_gate_id"],
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "planned_impact_count": row["planned_impact_count"],
            "execution_plan_status": row["execution_plan_status"],
            "execution_authorization_required": required,
            "authorization_manifest_relative_path": authorization["relative_path"],
            "operator_authorization_present": (
                "true" if authorization["status"] == "valid_execution_authorization_manifest" else "false"
            ),
            "authorization_validation_status": validation_status,
            "authorization_ticket": metadata.get("authorization_ticket", ""),
            "authorized_by": metadata.get("authorized_by", ""),
            "authorized_at": metadata.get("authorized_at", ""),
            "authorization_scope": metadata.get("authorization_scope", ""),
            "preview_status": preview_status,
            "source_mutation_allowed": "false",
            "fact_promotion_execution_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "preview_reason": preview_reason,
            "review_status": review_status,
        })
    return rows


def build_fact_promotion_execution_apply_gate_rows(
    manifest: dict,
    execution_authorization_preview_rows: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for row in execution_authorization_preview_rows:
        ready_for_apply = row["preview_status"] == "ready_for_controlled_execution_run_no_write"
        blocked_before_apply = row["preview_status"].startswith("blocked_")
        if ready_for_apply:
            apply_gate_status = "ready_for_controlled_execution_apply_no_write"
            planned_apply_count = int(row["planned_impact_count"])
            review_status = "pending_controlled_apply_review"
            gate_reason = (
                "Execution authorization is valid and impact is planned, but this runner still performs no "
                "fact promotion and no fund ledger write."
            )
        elif blocked_before_apply:
            apply_gate_status = "blocked_before_execution_apply"
            planned_apply_count = 0
            review_status = "pending_apply_blocker_resolution"
            gate_reason = "Execution apply is blocked because the execution authorization preview is blocked."
        else:
            apply_gate_status = "not_required_no_execution_apply"
            planned_apply_count = 0
            review_status = "no_execution_apply_required"
            gate_reason = "Execution apply is not required for this no-op authorization preview row."
        rows.append({
            "execution_apply_gate_id": f"FPEXECAPPLY-{manifest['run_id']}-{len(rows) + 1:05d}",
            "execution_authorization_preview_id": row["execution_authorization_preview_id"],
            "execution_plan_id": row["execution_plan_id"],
            "dry_run_id": row["dry_run_id"],
            "execution_gate_id": row["execution_gate_id"],
            "review_packet_id": row["review_packet_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "planned_impact_count": row["planned_impact_count"],
            "authorization_validation_status": row["authorization_validation_status"],
            "authorization_preview_status": row["preview_status"],
            "apply_gate_status": apply_gate_status,
            "planned_apply_count": str(planned_apply_count),
            "source_mutation_allowed": "false",
            "fact_promotion_execution_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "gate_reason": gate_reason,
            "review_status": review_status,
        })
    return rows


def build_fact_promotion_execution_result_rows(
    manifest: dict,
    execution_apply_gate_rows: list[dict],
    structured: dict,
) -> list[dict]:
    rows: list[dict] = []
    structured_rows = [
        row for row in structured["fund_rows"]
        if row.get("extraction_status") == "structured_csv_extracted_pending_review"
    ]
    for row in execution_apply_gate_rows:
        ready_structured_apply = (
            row["review_area"] == "structured_csv_facts"
            and row["apply_gate_status"] == "ready_for_controlled_execution_apply_no_write"
            and int(row["planned_apply_count"]) > 0
            and bool(structured_rows)
        )
        if ready_structured_apply:
            execution_result_status = "structured_csv_formal_ledger_sidecar_written"
            formal_ledger_artifact = "formal_fund_ledger.csv"
            formal_ledger_row_count = str(len(structured_rows))
            review_status = "formal_ledger_sidecar_written_pending_management_gate"
            result_reason = (
                "Structured CSV facts passed review and execution authorization gates; "
                "a formal ledger sidecar was written without mutating sources or fund_ledger.csv."
            )
        elif row["apply_gate_status"].startswith("blocked_"):
            execution_result_status = "blocked_before_formal_ledger_sidecar"
            formal_ledger_artifact = ""
            formal_ledger_row_count = "0"
            review_status = "pending_execution_result_blocker_resolution"
            result_reason = "No formal ledger sidecar is written because the execution apply gate is blocked."
        else:
            execution_result_status = "not_required_no_formal_ledger_sidecar"
            formal_ledger_artifact = ""
            formal_ledger_row_count = "0"
            review_status = "no_formal_ledger_sidecar_required"
            result_reason = "No formal ledger sidecar is required for this no-op execution apply row."
        rows.append({
            "execution_result_id": f"FPEXECRESULT-{manifest['run_id']}-{len(rows) + 1:05d}",
            "execution_apply_gate_id": row["execution_apply_gate_id"],
            "review_area": row["review_area"],
            "source_artifact": row["source_artifact"],
            "apply_gate_status": row["apply_gate_status"],
            "execution_result_status": execution_result_status,
            "planned_apply_count": row["planned_apply_count"],
            "formal_ledger_artifact": formal_ledger_artifact,
            "formal_ledger_row_count": formal_ledger_row_count,
            "source_mutation_allowed": "false",
            "fund_ledger_mutation_allowed": "false",
            "management_conclusion_allowed": "false",
            "result_reason": result_reason,
            "review_status": review_status,
        })
    return rows


def build_formal_fund_ledger_rows(manifest: dict, structured: dict, execution_result_rows: list[dict]) -> list[dict]:
    structured_formalized = any(
        row["review_area"] == "structured_csv_facts"
        and row["execution_result_status"] == "structured_csv_formal_ledger_sidecar_written"
        for row in execution_result_rows
    )
    if not structured_formalized:
        return []

    rows: list[dict] = []
    for row in structured["fund_rows"]:
        if row.get("extraction_status") != "structured_csv_extracted_pending_review":
            continue
        rows.append({
            "formal_ledger_id": f"FFL-{manifest['run_id']}-{len(rows) + 1:05d}",
            "source_ledger_id": row["ledger_id"],
            "date": row["date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "inflow": row["inflow"],
            "outflow": row["outflow"],
            "ending_balance": row["ending_balance"],
            "flow_type": row["flow_type"],
            "source_evidence_id": row["source_evidence_id"],
            "source_row_number": row["source_row_number"],
            "formal_fact_source": "structured_csv_facts",
            "formal_write_status": "structured_csv_formal_ledger_sidecar_written",
            "source_mutation_allowed": "false",
            "fund_ledger_mutation_allowed": "false",
            "management_conclusion_allowed": "false",
            "formal_review_status": "pending_management_conclusion_gate",
        })
    return rows


def write_runtime_rules_to_workbook(
    workbook_path: Path,
    manifest: dict,
    input_dir: Path,
    automation_readiness_rows: list[dict],
) -> None:
    automation = automation_readiness_rows[0] if automation_readiness_rows else {}
    schedule_ready = automation.get("schedule_ready", "false")
    schedule_rrule = automation.get("rrule", "CODEX_AUTOMATION_UNKNOWN")
    schedule_timezone = automation.get("expected_timezone", manifest.get("timezone", ""))
    rows = [
        [("A", "run_id"), ("B", manifest["run_id"]), ("C", "runtime"), ("D", "private package trace id")],
        [("A", "source_input_dir"), ("B", str(input_dir)), ("C", "source"), ("D", "read-only OneDrive input")],
        [("A", "timezone"), ("B", manifest.get("timezone", "")), ("C", "runtime"), ("D", "local scheduler timezone")],
        [("A", "schedule_rrule"), ("B", schedule_rrule), ("C", "automation"), ("D", "expected daily 11:30 Sydney")],
        [("A", "schedule_ready"), ("B", schedule_ready), ("C", "automation"), ("D", "read-only drift evidence")],
        [("A", "no_hallucinated_data_policy"), ("B", "true"), ("C", "data_policy"), ("D", "no generated financial facts without evidence")],
        [("A", "fact_promotion_execution_allowed"), ("B", "false"), ("C", "fact_promotion"), ("D", "separate owner authorization required")],
        [("A", "management_conclusion_allowed"), ("B", "false"), ("C", "management_gate"), ("D", "all rows fail closed until gates pass")],
        [("A", "fund_ledger_write_allowed"), ("B", "false"), ("C", "ledger_gate"), ("D", "no formal ledger write in this runner")],
        [("A", "private_runtime_policy"), ("B", "ignored_private_runtime_only"), ("C", "governance"), ("D", "raw files and run outputs stay out of Git")],
        [("A", "expected_schedule_timezone"), ("B", schedule_timezone), ("C", "automation"), ("D", "tracked contract comparison value")],
    ]

    with zipfile.ZipFile(workbook_path, "r") as workbook:
        sheet12 = ET.fromstring(workbook.read("xl/worksheets/sheet12.xml"))
    clear_rows_from(sheet12, 2)
    write_table_rows(sheet12, 2, rows)
    replace_xlsx_entries(workbook_path, {"xl/worksheets/sheet12.xml": serialize_sheet(sheet12)})


def collect_workbook_quality_checks(workbook_path: Path) -> list[dict]:
    rows: list[dict] = []
    ns_sheet = {"x": XLSX_MAIN_NS}
    ns_draw = {"xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}

    with zipfile.ZipFile(workbook_path, "r") as workbook:
        workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
        sheets = workbook_xml.findall(".//x:sheet", ns_sheet)
        sheet_names = [sheet.attrib["name"] for sheet in sheets]
        rows.append(workbook_quality_row(
            "WQ-SHEET-ORDER",
            "Workbook sheet order",
            sheet_names == EXPECTED_WORKBOOK_SHEETS,
            "names=" + "|".join(sheet_names),
        ))

        hidden_states = [sheet.attrib.get("state", "visible") for sheet in sheets[6:]]
        rows.append(workbook_quality_row(
            "WQ-HIDDEN-SHEETS",
            "Hidden audit and review sheets",
            len(hidden_states) == 6 and all(state == "hidden" for state in hidden_states),
            "states=" + "|".join(hidden_states),
        ))

        row2_not_blank = []
        for sheet_number in range(1, 7):
            sheet = ET.fromstring(workbook.read(f"xl/worksheets/sheet{sheet_number}.xml"))
            row = sheet.find(".//x:row[@r='2']", ns_sheet)
            values = xml_text_values(row) if row is not None else []
            if any(value.strip() for value in values):
                row2_not_blank.append(f"sheet{sheet_number}")
        rows.append(workbook_quality_row(
            "WQ-VISIBLE-ROW2-CLEARED",
            "Visible sheet row 2 cleared",
            not row2_not_blank,
            "nonblank=" + ",".join(row2_not_blank),
        ))

        chart_dimensions = []
        for name in workbook.namelist():
            if not name.startswith("xl/drawings/drawing") or not name.endswith(".xml"):
                continue
            drawing = ET.fromstring(workbook.read(name))
            for ext in drawing.findall(".//xdr:ext", ns_draw):
                width_in = int(ext.attrib.get("cx", "0")) / 914400
                height_in = int(ext.attrib.get("cy", "0")) / 914400
                chart_dimensions.append((name, width_in, height_in))
        oversized = [
            f"{name}:{width_in:.2f}x{height_in:.2f}"
            for name, width_in, height_in in chart_dimensions
            if width_in > 18 or height_in > 9
        ]
        rows.append(workbook_quality_row(
            "WQ-HOMEPAGE-CHART-SIZE",
            "Native chart size limit",
            bool(chart_dimensions) and not oversized,
            "oversized=" + ",".join(oversized) + f"; chart_extent_count={len(chart_dimensions)}",
        ))

        homepage_chart_details = []
        homepage_chart_failures = []
        expected_homepage_charts = {
            "最近15天资金余额折线图": 15,
            "最近30天资金余额折线图": 30,
        }
        drawing_rels_path = "xl/drawings/_rels/drawing1.xml.rels"
        if drawing_rels_path not in workbook.namelist():
            homepage_chart_failures.append("missing_drawing1_rels")
        else:
            rels = ET.fromstring(workbook.read(drawing_rels_path))
            chart_targets = [
                normalize_xlsx_relationship_target("xl/drawings", rel.attrib.get("Target", ""))
                for rel in rels.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
                if rel.attrib.get("Type", "").endswith("/chart")
            ]
            if len(chart_targets) != 2:
                homepage_chart_failures.append(f"chart_target_count={len(chart_targets)}")
            seen_titles = set()
            for chart_path in chart_targets:
                if chart_path not in workbook.namelist():
                    homepage_chart_failures.append(f"missing_chart={chart_path}")
                    continue
                chart = ET.fromstring(workbook.read(chart_path))
                title = chart_title_text(chart)
                counts = chart_series_category_counts(chart)
                homepage_chart_details.append(f"{title}:{','.join(str(count) for count in counts)}")
                expected_count = expected_homepage_charts.get(title)
                if expected_count is None:
                    homepage_chart_failures.append(f"unexpected_title={title}")
                    continue
                seen_titles.add(title)
                if len(counts) != 3 or any(count != expected_count for count in counts):
                    homepage_chart_failures.append(
                        f"{title}_point_counts={','.join(str(count) for count in counts)}"
                    )
            missing_titles = set(expected_homepage_charts) - seen_titles
            if missing_titles:
                homepage_chart_failures.append("missing_titles=" + "|".join(sorted(missing_titles)))
        rows.append(workbook_quality_row(
            "WQ-HOMEPAGE-CHART-SEMANTICS",
            "Homepage 15-day and 30-day line charts",
            not homepage_chart_failures,
            "charts=" + "|".join(homepage_chart_details) + "; failures=" + "|".join(homepage_chart_failures),
        ))

        formula_errors = []
        visible_sensitive_hits = []
        for sheet_number in range(1, 13):
            sheet_path = f"xl/worksheets/sheet{sheet_number}.xml"
            if sheet_path not in workbook.namelist():
                continue
            payload = workbook.read(sheet_path).decode("utf-8", errors="replace")
            for marker in FORMULA_ERROR_MARKERS:
                if marker in payload:
                    formula_errors.append(f"sheet{sheet_number}:{marker}")
            if sheet_number <= 6:
                sheet = ET.fromstring(payload)
                for text in xml_text_values(sheet):
                    if VISIBLE_SENSITIVE_PATTERN.search(text):
                        visible_sensitive_hits.append(f"sheet{sheet_number}:{text[:32]}")
        rows.append(workbook_quality_row(
            "WQ-FORMULA-ERRORS",
            "Formula error marker scan",
            not formula_errors,
            "hits=" + ",".join(formula_errors),
        ))
        rows.append(workbook_quality_row(
            "WQ-VISIBLE-SENSITIVE-TEXT",
            "Visible management sheet sensitive text scan",
            not visible_sensitive_hits,
            "hits=" + ",".join(visible_sensitive_hits[:10]),
        ))

    return rows


def metadata_formal_action_allowed(row: dict) -> bool:
    allowed_keys = (
        "formal_report_allowed",
        "formal_calculation_allowed",
        "formal_report_rerun_allowed",
        "business_decision_basis_allowed",
        "bank_operation_allowed",
        "payment_approval_allowed",
        "loan_management_action_allowed",
        "action_allowed",
    )
    return any(row.get(key) is True for key in allowed_keys)


def metadata_signal_row(
    run_id: str,
    index: int,
    signal_type: str,
    source_path_text: str,
    source_ref: str,
    stage_phase: str,
    status: str,
    severity: str,
    report_grade: str,
    formal_action_allowed: bool,
    remark: str,
) -> dict:
    return {
        "signal_id": f"META-{run_id}-{index:05d}",
        "signal_type": signal_type,
        "source_path": source_path_text,
        "source_ref": source_ref,
        "stage_phase": stage_phase,
        "status": status,
        "severity": severity,
        "report_grade": report_grade,
        "formal_action_allowed": bool_text(formal_action_allowed),
        "review_status": "kmfa_metadata_pending_review",
        "remark": remark,
    }


def collect_kmfa_metadata_signals(repo_root: Path, run_id: str) -> list[dict]:
    signals: list[dict] = []

    def rel(path: Path) -> str:
        return str(path.relative_to(repo_root))

    def add_signal(
        signal_type: str,
        path: Path,
        source_ref: str,
        stage_phase: str,
        status: str,
        report_grade: str,
        source_formal_action_allowed: bool,
        remark: str,
    ) -> None:
        formal_action_allowed = False
        severity = "blocking_for_management_conclusion"
        if source_formal_action_allowed:
            remark = f"{remark}; source_formal_action_allowed=true; s21_review_gate=false"
        signals.append(metadata_signal_row(
            run_id,
            len(signals) + 1,
            signal_type,
            rel(path),
            source_ref,
            stage_phase,
            status,
            severity,
            report_grade,
            formal_action_allowed,
            remark,
        ))

    reports_dir = repo_root / "KMFA" / "metadata" / "reports"
    lineage_dir = repo_root / "KMFA" / "metadata" / "lineage"
    quality_dir = repo_root / "KMFA" / "metadata" / "quality"

    cash_path = reports_dir / "fund_cash_pressure_signals.jsonl"
    for row in read_jsonl(cash_path):
        add_signal(
            row.get("record_type", "cash_pressure_signal"),
            cash_path,
            f"{rel(cash_path)}#{row.get('pressure_window', '')}",
            row.get("stage_phase", ""),
            row.get("pressure_level", ""),
            row.get("report_grade_visible", ""),
            metadata_formal_action_allowed(row),
            row.get("status_label", row.get("visible_window", "")),
        )

    fact_manifest_path = reports_dir / "project_cost_fact_layer_manifest.json"
    fact_manifest = read_json_object(fact_manifest_path)
    if fact_manifest:
        formal_allowed = bool((fact_manifest.get("quality_gate") or {}).get("formal_report_allowed"))
        add_signal(
            fact_manifest.get("record_type", "project_cost_fact_layer_manifest"),
            fact_manifest_path,
            rel(fact_manifest_path),
            fact_manifest.get("stage_phase", ""),
            fact_manifest.get("fact_layer_status", ""),
            "",
            formal_allowed,
            "required_metrics=" + ",".join(fact_manifest.get("required_fact_metrics", [])),
        )

    fact_records_path = lineage_dir / "project_cost_fact_records.jsonl"
    for row in read_jsonl(fact_records_path):
        add_signal(
            row.get("record_type", "project_cost_fact_record"),
            fact_records_path,
            f"{rel(fact_records_path)}#{row.get('fact_record_id', '')}",
            row.get("stage_phase", ""),
            row.get("calculation_status", ""),
            "",
            metadata_formal_action_allowed(row),
            row.get("project_entity_ref", row.get("fact_record_id", "")),
        )

    report_grade_path = reports_dir / "report_grade_runtime_records.jsonl"
    for row in read_jsonl(report_grade_path):
        add_signal(
            row.get("record_type", "report_grade_runtime_record"),
            report_grade_path,
            f"{rel(report_grade_path)}#{row.get('report_record_id', '')}",
            row.get("stage_phase", ""),
            row.get("release_permission", ""),
            row.get("computed_report_grade", ""),
            metadata_formal_action_allowed(row),
            row.get("report_record_id", ""),
        )

    reconciliation_path = quality_dir / "scope_reconciliation_records.jsonl"
    for row in read_jsonl(reconciliation_path):
        add_signal(
            row.get("record_type", "scope_reconciliation_record"),
            reconciliation_path,
            f"{rel(reconciliation_path)}#{row.get('difference_id', '')}",
            row.get("stage_phase", ""),
            row.get("resolution_status", ""),
            "",
            metadata_formal_action_allowed(row),
            row.get("impact_scope", row.get("difference_id", "")),
        )

    return signals


def balance_summary_from_fund_rows(fund_rows: list[dict], date: str | None = None) -> dict[str, Decimal]:
    latest_by_account: dict[tuple[str, str, str, str], dict] = {}
    for row in fund_rows:
        if date is not None and row["date"] != date:
            continue
        key = (row["company"], row["bank"], row["account_alias"], row["liquidity_tier"])
        current = latest_by_account.get(key)
        if current is None or (row["date"], row["source_row_number"]) >= (current["date"], current["source_row_number"]):
            latest_by_account[key] = row

    bank_cash = Decimal("0.00")
    bills = Decimal("0.00")
    total = Decimal("0.00")
    for row in latest_by_account.values():
        ending_balance = money(row["ending_balance"])
        tier = row["liquidity_tier"].upper()
        total += ending_balance
        if "T0" in tier or "BANK" in tier or "银行" in row["bank"]:
            bank_cash += ending_balance
        if "BILL" in tier or "票据" in tier or "汇票" in tier or "承兑" in tier:
            bills += ending_balance
    ratio = (bank_cash / total * Decimal("100")) if total else Decimal("0.00")
    return {
        "total_funds": total,
        "bank_cash": bank_cash,
        "bills": bills,
        "available_cash_ratio": ratio,
    }


def structured_workbook_summary(structured: dict) -> dict[str, Decimal]:
    balance = balance_summary_from_fund_rows(structured["fund_rows"])
    deposit_release = Decimal("0.00")
    due_pressure = Decimal("0.00")
    for row in structured["risk_rows"]:
        risk_type = row["risk_type"].lower()
        amount = money(row["amount"])
        if "deposit" in risk_type or "保证金" in row["risk_type"]:
            deposit_release += amount
        else:
            due_pressure += amount

    external_net = Decimal("0.00")
    internal_net = Decimal("0.00")
    for row in structured["net_flow_rows"]:
        external_net += money(row["external_inflow"]) - money(row["external_outflow"])
        internal_net += money(row["internal_transfer_net"])

    funding_gap = due_pressure - balance["bank_cash"] - deposit_release
    if funding_gap < Decimal("0.00"):
        funding_gap = Decimal("0.00")
    return {
        **balance,
        "deposit_release": deposit_release,
        "external_net": external_net,
        "internal_transfer_net": internal_net,
        "funding_gap": funding_gap,
        "due_pressure": due_pressure,
    }


def risk_row_known_movement(row: dict) -> tuple[Decimal, Decimal]:
    risk_type = row["risk_type"].lower()
    amount = money(row["amount"])
    inflow_markers = ("release", "refund", "return", "deposit_release", "可释放", "退款", "退回", "回款")
    if any(marker in risk_type for marker in inflow_markers):
        return amount, Decimal("0.00")
    return Decimal("0.00"), amount


def build_funding_forecast_rows(structured: dict) -> list[dict]:
    if not structured["fund_rows"]:
        return []

    summary = structured_workbook_summary(structured)
    grouped: dict[str, dict[str, object]] = {}
    for row in structured["risk_rows"]:
        due_date = row["due_date"]
        if not due_date:
            continue
        bucket = grouped.setdefault(due_date, {
            "known_inflow": Decimal("0.00"),
            "known_outflow": Decimal("0.00"),
            "risk_types": set(),
            "source_evidence_ids": set(),
        })
        inflow, outflow = risk_row_known_movement(row)
        bucket["known_inflow"] = bucket["known_inflow"] + inflow
        bucket["known_outflow"] = bucket["known_outflow"] + outflow
        bucket["risk_types"].add(row["risk_type"])
        bucket["source_evidence_ids"].add(row["source_evidence_id"])

    projected_bank_cash = summary["bank_cash"]
    rows = []
    for due_date, bucket in sorted(grouped.items()):
        known_inflow = bucket["known_inflow"]
        known_outflow = bucket["known_outflow"]
        projected_bank_cash += known_inflow - known_outflow
        funding_gap = Decimal("0.00")
        if projected_bank_cash < Decimal("0.00"):
            funding_gap = -projected_bank_cash
        rows.append({
            "period_date": due_date,
            "starting_bank_cash": money_text(summary["bank_cash"]),
            "known_inflow": money_text(known_inflow),
            "known_outflow": money_text(known_outflow),
            "projected_bank_cash": money_text(projected_bank_cash),
            "funding_gap": money_text(funding_gap),
            "risk_types": ",".join(sorted(bucket["risk_types"])),
            "source_evidence_ids": ",".join(sorted(bucket["source_evidence_ids"])),
            "forecast_basis": "known_due_date_structured_csv",
            "review_status": "structured_csv_forecast_pending_review",
        })
    return rows


def build_cashflow_validation_rows(structured: dict, run_id: str) -> list[dict]:
    previous_by_account: dict[tuple[str, str, str, str], Decimal] = {}
    rows = []
    ordered = sorted(
        structured["fund_rows"],
        key=lambda row: (
            row["company"],
            row["bank"],
            row["account_alias"],
            row["liquidity_tier"],
            row["date"],
            int(row["source_row_number"]),
        ),
    )
    for row in ordered:
        validation_id = f"CV-{run_id}-{len(rows) + 1:05d}"
        key = (row["company"], row["bank"], row["account_alias"], row["liquidity_tier"])
        inflow = money(row["inflow"])
        outflow = money(row["outflow"])
        actual_ending = money(row["ending_balance"])
        previous_ending = previous_by_account.get(key)
        if previous_ending is None:
            expected_ending = actual_ending
            diff = Decimal("0.00")
            validation_status = "BASELINE"
            review_status = "baseline_balance_recorded"
        else:
            expected_ending = previous_ending + inflow - outflow
            diff = actual_ending - expected_ending
            if abs(diff) <= Decimal("0.01"):
                validation_status = "PASS"
                review_status = "balance_continuity_passed_pending_review"
            else:
                validation_status = "FAIL"
                review_status = "balance_continuity_gap_pending_review"
        flow_type = row["flow_type"]
        internal_transfer_excluded = flow_type == "internal_transfer"
        operating_effect = inflow - outflow if flow_type == "operating" else Decimal("0.00")
        rows.append({
            "validation_id": validation_id,
            "ledger_id": row["ledger_id"],
            "date": row["date"],
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "previous_ending_balance": "" if previous_ending is None else money_text(previous_ending),
            "inflow": money_text(inflow),
            "outflow": money_text(outflow),
            "expected_ending_balance": money_text(expected_ending),
            "actual_ending_balance": money_text(actual_ending),
            "continuity_diff": money_text(diff),
            "flow_type": flow_type,
            "operating_cashflow_effect": money_text(operating_effect),
            "internal_transfer_excluded": bool_text(internal_transfer_excluded),
            "validation_status": validation_status,
            "review_status": review_status,
            "source_evidence_id": row["source_evidence_id"],
        })
        previous_by_account[key] = actual_ending
    return rows


def workbook_display_matrix_rows(fund_rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in fund_rows:
        key = (row["company"], row["bank"], row["account_alias"], row["liquidity_tier"])
        bucket = grouped.setdefault(key, {
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "count": 0,
            "inflow_count": 0,
            "outflow_count": 0,
            "inflow": Decimal("0.00"),
            "outflow": Decimal("0.00"),
            "tax": Decimal("0.00"),
            "deposit_net": Decimal("0.00"),
            "loan_outflow": Decimal("0.00"),
            "last_date": row["date"],
            "evidence_ids": set(),
        })
        inflow = money(row["inflow"])
        outflow = money(row["outflow"])
        bucket["count"] = int(bucket["count"]) + 1
        bucket["inflow_count"] = int(bucket["inflow_count"]) + (1 if inflow else 0)
        bucket["outflow_count"] = int(bucket["outflow_count"]) + (1 if outflow else 0)
        bucket["inflow"] = bucket["inflow"] + inflow
        bucket["outflow"] = bucket["outflow"] + outflow
        bucket["last_date"] = max(str(bucket["last_date"]), row["date"])
        bucket["evidence_ids"].add(row["source_evidence_id"])
        if row["flow_type"] == "tax":
            bucket["tax"] = bucket["tax"] + outflow
        if row["flow_type"] == "deposit":
            bucket["deposit_net"] = bucket["deposit_net"] + inflow - outflow
        if row["flow_type"] == "loan":
            bucket["loan_outflow"] = bucket["loan_outflow"] + outflow
    return [dict(row) for row in sorted(grouped.values(), key=lambda item: (item["company"], item["bank"], item["account_alias"]))]


def write_structured_facts_to_workbook(workbook_path: Path, structured: dict, evidence: list[dict], input_dir: Path, run_id: str) -> None:
    if not structured["fund_rows"]:
        return

    summary = structured_workbook_summary(structured)
    funding_forecast_rows = build_funding_forecast_rows(structured)
    cashflow_validation_rows = build_cashflow_validation_rows(structured, run_id)
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    ledger_ids_by_evidence: dict[str, list[str]] = {}
    dates_by_evidence: dict[str, set[str]] = {}
    signed_amount_by_evidence: dict[str, Decimal] = {}
    for row in structured["fund_rows"]:
        evidence_id = row["source_evidence_id"]
        ledger_ids_by_evidence.setdefault(evidence_id, []).append(row["ledger_id"])
        dates_by_evidence.setdefault(evidence_id, set()).add(row["date"])
        signed_amount_by_evidence[evidence_id] = signed_amount_by_evidence.get(evidence_id, Decimal("0.00")) + money(row["inflow"]) - money(row["outflow"])

    replacements: dict[str, bytes] = {}
    with zipfile.ZipFile(workbook_path, "r") as workbook:
        sheet1 = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        set_text_cell(sheet1, "B4", f"可用现金占比\n{percent_text(summary['available_cash_ratio'])}\nT0银行存款/期末总资金｜结构化CSV待复核")
        set_text_cell(sheet1, "E4", f"银行存款\n{currency_text(summary['bank_cash'])}\nT0可用现金｜结构化CSV待复核")
        set_text_cell(sheet1, "H4", f"票据/电子汇票\n{currency_text(summary['bills'])}\n准现金/结算工具｜结构化CSV待复核")
        set_text_cell(sheet1, "K4", f"期末总资金\n{currency_text(summary['total_funds'])}\n来自结构化CSV最新余额｜待复核")
        set_text_cell(sheet1, "B8", f"保证金可释放\n{currency_text(summary['deposit_release'])}\ndeposit风险行｜待复核")
        set_text_cell(sheet1, "E8", f"外部净流出\n{currency_text(summary['external_net'])}\n外部流入-外部流出｜待复核")
        set_text_cell(sheet1, "H8", f"内部调拨净额\n{currency_text(summary['internal_transfer_net'])}\n内部调拨行净额｜待复核")
        set_text_cell(sheet1, "K8", f"资金缺口\n{currency_text(summary['funding_gap'])}\n税费/借款压力-可用现金｜待复核")
        replacements["xl/worksheets/sheet1.xml"] = serialize_sheet(sheet1)

        sheet2 = ET.fromstring(workbook.read("xl/worksheets/sheet2.xml"))
        clear_rows_from(sheet2, 4)
        write_table_rows(sheet2, 4, [[
            ("text", "预测/到期日"),
            ("text", "已知流入"),
            ("text", "已知流出"),
            ("text", "预计T0银行存款"),
            ("text", "资金缺口"),
            ("text", "风险/机会类型"),
            ("text", "来源证据"),
            ("text", "复核状态"),
            ("text", "计算依据"),
        ]])
        forecast_table_rows = []
        for row in funding_forecast_rows:
            forecast_table_rows.append([
                ("text", row["period_date"]),
                ("number", row["known_inflow"]),
                ("number", row["known_outflow"]),
                ("number", row["projected_bank_cash"]),
                ("number", row["funding_gap"]),
                ("text", row["risk_types"]),
                ("text", row["source_evidence_ids"]),
                ("text", row["review_status"]),
                ("text", row["forecast_basis"]),
            ])
        write_table_rows(sheet2, 5, forecast_table_rows)
        replacements["xl/worksheets/sheet2.xml"] = serialize_sheet(sheet2)

        sheet3 = ET.fromstring(workbook.read("xl/worksheets/sheet3.xml"))
        clear_rows_from(sheet3, 5)
        flow_rows: list[list[tuple[str, object]]] = []
        for row in structured["net_flow_rows"]:
            day_balance = balance_summary_from_fund_rows(structured["fund_rows"], row["date"])
            external_inflow = money(row["external_inflow"])
            external_outflow = money(row["external_outflow"])
            internal_in = money(row["internal_transfer_in"])
            internal_out = money(row["internal_transfer_out"])
            account_in = external_inflow + internal_in
            account_out = external_outflow + internal_out
            external_net = external_inflow - external_outflow
            flow_rows.append([
                ("text", row["date"]),
                ("text", "structured_csv"),
                ("text", ""),
                ("number", money_text(account_in)),
                ("number", money_text(account_out)),
                ("number", money_text(account_in - account_out)),
                ("number", money_text(day_balance["total_funds"])),
                ("number", money_text(day_balance["bank_cash"])),
                ("number", money_text(day_balance["bills"])),
                ("number", money_text(day_balance["available_cash_ratio"] / Decimal("100"))),
                ("number", money_text(external_inflow)),
                ("number", money_text(external_outflow)),
                ("number", money_text(external_net)),
                ("number", row["internal_transfer_net"]),
                ("text", ""),
                ("text", "待复核"),
                ("text", "结构化CSV已写入，管理结论仍需交叉复审"),
            ])
        write_table_rows(sheet3, 5, flow_rows)
        replacements["xl/worksheets/sheet3.xml"] = serialize_sheet(sheet3)

        sheet4 = ET.fromstring(workbook.read("xl/worksheets/sheet4.xml"))
        set_text_cell(sheet4, "A4", f"税费截图金额\n{currency_text(summary['due_pressure'])}\n结构化CSV风险行｜待复核")
        set_text_cell(sheet4, "D4", f"税费版本差异\n待复核\n未生成管理结论")
        set_text_cell(sheet4, "G4", f"借款/还款应付\n{currency_text(summary['due_pressure'])}\n税费/借款压力合计｜待复核")
        set_text_cell(sheet4, "J4", f"余额不足缺口\n{currency_text(summary['funding_gap'])}\n按当前结构化事实计算｜待复核")
        clear_rows_from(sheet4, 10)
        risk_rows = []
        for row in structured["risk_rows"]:
            risk_rows.append([
                ("text", ""),
                ("number", row["amount"]),
                ("text", ""),
                ("text", row["risk_type"]),
                ("number", row["amount"]),
                ("text", ""),
                ("text", row["risk_id"]),
                ("text", ""),
                ("text", row["due_date"]),
                ("text", row["risk_type"]),
                ("number", row["amount"]),
                ("text", ""),
                ("text", ""),
                ("text", row["source_evidence_id"]),
                ("text", "结构化CSV待复核"),
            ])
        write_table_rows(sheet4, 10, risk_rows)
        replacements["xl/worksheets/sheet4.xml"] = serialize_sheet(sheet4)

        sheet5 = ET.fromstring(workbook.read("xl/worksheets/sheet5.xml"))
        clear_rows_from(sheet5, 5)
        matrix_rows = []
        for row in workbook_display_matrix_rows(structured["fund_rows"]):
            inflow = row["inflow"]
            outflow = row["outflow"]
            matrix_rows.append([
                ("text", row["company"]),
                ("text", row["bank"]),
                ("text", row["account_alias"]),
                ("text", row["liquidity_tier"]),
                ("text", "待复核"),
                ("number", row["count"]),
                ("number", row["inflow_count"]),
                ("number", row["outflow_count"]),
                ("number", money_text(inflow)),
                ("number", money_text(outflow)),
                ("number", money_text(inflow - outflow)),
                ("text", ""),
                ("number", money_text(row["tax"])),
                ("number", money_text(row["deposit_net"])),
                ("number", money_text(row["loan_outflow"])),
                ("text", row["last_date"]),
                ("number", len(row["evidence_ids"])),
                ("number", row["count"]),
                ("text", "待复核"),
                ("text", "结构化CSV已写入，需交叉复审后才能形成结论"),
            ])
        write_table_rows(sheet5, 5, matrix_rows)
        replacements["xl/worksheets/sheet5.xml"] = serialize_sheet(sheet5)

        sheet7 = ET.fromstring(workbook.read("xl/worksheets/sheet7.xml"))
        clear_rows_from(sheet7, 2)
        h01_rows = []
        for row in structured["fund_rows"]:
            inflow = money(row["inflow"])
            outflow = money(row["outflow"])
            signed = inflow - outflow
            direction = "收入" if signed > 0 else "支出" if signed < 0 else "零变动"
            amount = inflow if inflow else outflow
            evidence_row = evidence_by_id.get(row["source_evidence_id"], {})
            h01_rows.append([
                ("text", row["ledger_id"]),
                ("text", row["date"]),
                ("text", row["company"]),
                ("text", row["account_alias"]),
                ("text", direction),
                ("number", money_text(amount)),
                ("number", money_text(signed)),
                ("text", ""),
                ("text", ""),
                ("text", ""),
                ("text", row["flow_type"]),
                ("text", row["liquidity_tier"]),
                ("text", "是" if row["flow_type"] == "internal_transfer" else "否"),
                ("text", "structured_csv"),
                ("text", evidence_row.get("relative_path", "")),
                ("text", row["source_row_number"]),
                ("text", row["source_evidence_id"]),
                ("text", row["extraction_status"]),
                ("text", ""),
                ("text", f"bank={row['bank']}; ending_balance={row['ending_balance']}"),
            ])
        write_table_rows(sheet7, 2, h01_rows)
        replacements["xl/worksheets/sheet7.xml"] = serialize_sheet(sheet7)

        sheet8 = ET.fromstring(workbook.read("xl/worksheets/sheet8.xml"))
        clear_rows_from(sheet8, 4)
        h02_rows = []
        for index, row in enumerate(structured["risk_rows"], 1):
            h02_rows.append([
                ("text", f"TASK-{row['risk_id']}"),
                ("text", row["risk_type"]),
                ("text", "待复核"),
                ("number", row["amount"]),
                ("text", ""),
                ("text", row["due_date"]),
                ("text", "财务负责人"),
                ("text", "structured_csv"),
                ("text", row["source_evidence_id"]),
                ("text", "复核税费/融资/保证金风险事实后再进入管理结论"),
                ("text", "pending_review"),
                ("text", f"risk_row={index}"),
            ])
        write_table_rows(sheet8, 4, h02_rows)
        replacements["xl/worksheets/sheet8.xml"] = serialize_sheet(sheet8)

        sheet9 = ET.fromstring(workbook.read("xl/worksheets/sheet9.xml"))
        clear_rows_from(sheet9, 4)
        h03_rows = []
        for row in evidence:
            evidence_id = row["evidence_id"]
            linked_ids = ledger_ids_by_evidence.get(evidence_id, [])
            extraction_status = row["review_status"]
            h03_rows.append([
                ("text", evidence_id),
                ("text", row["relative_path"]),
                ("text", str(input_dir / row["relative_path"])),
                ("text", row["sha256"]),
                ("text", ""),
                ("text", ""),
                ("text", ""),
                ("text", row["kind"]),
                ("text", "D"),
                ("text", "private"),
                ("text", extraction_status),
                ("text", ",".join(linked_ids)),
                ("text", ",".join(sorted(dates_by_evidence.get(evidence_id, set())))),
                ("number", money_text(signed_amount_by_evidence.get(evidence_id, Decimal("0.00")))),
                ("text", extraction_status),
                ("text", "structured facts pending review" if linked_ids else "indexed only pending extraction"),
            ])
        write_table_rows(sheet9, 4, h03_rows)
        replacements["xl/worksheets/sheet9.xml"] = serialize_sheet(sheet9)

        sheet11 = ET.fromstring(workbook.read("xl/worksheets/sheet11.xml"))
        clear_rows_from(sheet11, 12)
        h05_rows = []
        for row in cashflow_validation_rows:
            is_blocking = row["validation_status"] == "FAIL"
            h05_rows.append([
                ("text", row["validation_id"]),
                ("text", "余额连续性/经营现金流验证"),
                ("text", "期末余额=上次期末余额+流入-流出；内部调拨不计入经营现金流"),
                ("text", row["validation_status"]),
                ("text", "差异进入异常任务池并阻断管理结论" if is_blocking else "待复核后可作为结构化事实"),
                ("text", "是" if is_blocking else "否"),
                ("text", f"ledger_id={row['ledger_id']}; diff={row['continuity_diff']}; operating_effect={row['operating_cashflow_effect']}; internal_transfer_excluded={row['internal_transfer_excluded']}"),
            ])
        write_table_rows(sheet11, 12, h05_rows)
        replacements["xl/worksheets/sheet11.xml"] = serialize_sheet(sheet11)

    replace_xlsx_entries(workbook_path, replacements)


def write_metadata_signals_to_workbook(workbook_path: Path, metadata_signals: list[dict], existing_h02_rows: int) -> None:
    if not metadata_signals:
        return

    replacements: dict[str, bytes] = {}
    with zipfile.ZipFile(workbook_path, "r") as workbook:
        sheet4 = ET.fromstring(workbook.read("xl/worksheets/sheet4.xml"))
        if existing_h02_rows == 0:
            set_text_cell(sheet4, "A4", f"KMFA元数据风险信号\n{len(metadata_signals)}条\npublic-safe metadata｜待复核")
            set_text_cell(sheet4, "D4", "报告等级\nD/blocked\n不可作为正式经营结论")
            set_text_cell(sheet4, "G4", "项目成本/资金压力\n待复核\n需结合真实付款请示群证据")
            set_text_cell(sheet4, "J4", "操作边界\n禁止银行/付款/贷款动作\nmetadata signal only")
        replacements["xl/worksheets/sheet4.xml"] = serialize_sheet(sheet4)

        sheet8 = ET.fromstring(workbook.read("xl/worksheets/sheet8.xml"))
        if existing_h02_rows == 0:
            clear_rows_from(sheet8, 4)
        h02_rows = []
        for row in metadata_signals:
            h02_rows.append([
                ("text", row["signal_id"]),
                ("text", row["signal_type"]),
                ("text", row["severity"]),
                ("text", ""),
                ("text", "KMFA metadata"),
                ("text", ""),
                ("text", "财务负责人"),
                ("text", row["source_ref"]),
                ("text", row["signal_id"]),
                ("text", "复核 KMFA metadata 信号并绑定真实付款请示群证据后再进入管理结论"),
                ("text", row["review_status"]),
                ("text", f"status={row['status']}; grade={row['report_grade']}; {row['remark']}"),
            ])
        write_table_rows(sheet8, 4 + existing_h02_rows, h02_rows)
        replacements["xl/worksheets/sheet8.xml"] = serialize_sheet(sheet8)

    replace_xlsx_entries(workbook_path, replacements)


def extract_structured_csv_facts(manifest: dict, input_dir: Path, evidence: list[dict]) -> dict:
    evidence_by_path = {row["relative_path"]: row["evidence_id"] for row in evidence}
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    fund_rows: list[dict] = []
    risk_rows: list[dict] = []
    source_errors: list[dict] = []

    for item in manifest["files"]:
        if item["suffix"] != ".csv":
            continue
        csv_path = input_dir / item["relative_path"]
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                fields = set(reader.fieldnames or [])
                if not STRUCTURED_CSV_REQUIRED_FIELDS.issubset(fields):
                    continue
                for row_number, row in enumerate(reader, 2):
                    inflow = money(row.get("inflow"))
                    outflow = money(row.get("outflow"))
                    ending_balance = money(row.get("ending_balance"))
                    ledger_id = f"FL-{manifest['run_id']}-{len(fund_rows) + 1:05d}"
                    evidence_id = evidence_by_path[item["relative_path"]]
                    evidence_by_id[evidence_id]["review_status"] = "structured_csv_extracted_pending_review"
                    flow_type = (row.get("flow_type") or "unclassified").strip() or "unclassified"
                    fund_rows.append({
                        "ledger_id": ledger_id,
                        "date": (row.get("date") or "").strip(),
                        "company": (row.get("company") or "").strip(),
                        "bank": (row.get("bank") or "").strip(),
                        "account_alias": (row.get("account_alias") or "").strip(),
                        "liquidity_tier": (row.get("liquidity_tier") or "").strip(),
                        "inflow": money_text(inflow),
                        "outflow": money_text(outflow),
                        "ending_balance": money_text(ending_balance),
                        "flow_type": flow_type,
                        "source_evidence_id": evidence_id,
                        "source_row_number": str(row_number),
                        "extraction_status": "structured_csv_extracted_pending_review",
                    })
                    if flow_type in {"tax", "loan", "deposit", "project_cost"}:
                        amount = outflow if outflow != Decimal("0.00") else inflow
                        risk_rows.append({
                            "risk_id": f"RISK-{manifest['run_id']}-{len(risk_rows) + 1:05d}",
                            "risk_type": (row.get("risk_type") or flow_type).strip() or flow_type,
                            "due_date": (row.get("due_date") or "").strip(),
                            "amount": money_text(amount),
                            "source_evidence_id": evidence_id,
                            "review_status": "structured_csv_extracted_pending_review",
                        })
        except (OSError, ValueError) as exc:
            source_errors.append({
                "relative_path": item["relative_path"],
                "issue_type": "STRUCTURED_CSV_PARSE_ERROR",
                "severity": "blocking_for_this_file",
                "error": str(exc),
            })

    return {
        "fund_rows": fund_rows,
        "net_flow_rows": build_net_flow_rows(fund_rows),
        "matrix_rows": build_company_bank_matrix_rows(fund_rows),
        "risk_rows": risk_rows,
        "source_errors": source_errors,
    }


def build_net_flow_rows(fund_rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict[str, Decimal]] = {}
    for row in fund_rows:
        date = row["date"]
        bucket = grouped.setdefault(date, {
            "external_inflow": Decimal("0.00"),
            "external_outflow": Decimal("0.00"),
            "internal_transfer_in": Decimal("0.00"),
            "internal_transfer_out": Decimal("0.00"),
            "unclassified_net": Decimal("0.00"),
        })
        inflow = money(row["inflow"])
        outflow = money(row["outflow"])
        if row["flow_type"] == "internal_transfer":
            bucket["internal_transfer_in"] += inflow
            bucket["internal_transfer_out"] += outflow
        else:
            bucket["external_inflow"] += inflow
            bucket["external_outflow"] += outflow
            if row["flow_type"] == "unclassified":
                bucket["unclassified_net"] += inflow - outflow
    result = []
    for date, bucket in sorted(grouped.items()):
        result.append({
            "date": date,
            "external_inflow": money_text(bucket["external_inflow"]),
            "external_outflow": money_text(bucket["external_outflow"]),
            "internal_transfer_in": money_text(bucket["internal_transfer_in"]),
            "internal_transfer_out": money_text(bucket["internal_transfer_out"]),
            "internal_transfer_net": money_text(bucket["internal_transfer_in"] - bucket["internal_transfer_out"]),
            "unclassified_net": money_text(bucket["unclassified_net"]),
            "review_status": "structured_csv_extracted_pending_review",
        })
    return result


def build_company_bank_matrix_rows(fund_rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], dict] = {}
    for row in fund_rows:
        key = (row["company"], row["bank"], row["account_alias"], row["liquidity_tier"])
        current = grouped.get(key)
        if current is None or (row["date"], row["source_row_number"]) >= (current["date"], current["source_row_number"]):
            grouped[key] = {**row, "evidence_count": (current or {}).get("evidence_count", 0) + 1}
        else:
            current["evidence_count"] += 1
    return [
        {
            "company": row["company"],
            "bank": row["bank"],
            "account_alias": row["account_alias"],
            "liquidity_tier": row["liquidity_tier"],
            "ending_balance": row["ending_balance"],
            "evidence_count": str(row["evidence_count"]),
            "review_status": "structured_csv_extracted_pending_review",
        }
        for row in sorted(grouped.values(), key=lambda item: (item["company"], item["bank"], item["account_alias"], item["liquidity_tier"]))
    ]


def write_no_hallucination_outputs(
    manifest: dict,
    run_dir: Path,
    input_dir: Path,
    repo_root: Path,
    automation_root: Path,
) -> None:
    evidence = write_evidence_index_stub(manifest, run_dir)
    screenshot_ocr_coverage_rows = collect_screenshot_ocr_coverage(manifest, repo_root, run_dir, evidence)
    ocr_text_candidates = collect_ocr_text_candidates(manifest, input_dir, repo_root, run_dir, evidence)
    ocr_value_candidates = extract_ocr_value_candidates(manifest, input_dir, repo_root, ocr_text_candidates)
    ocr_financial_fact_candidates = extract_ocr_financial_fact_candidates(manifest, input_dir, repo_root, ocr_text_candidates)
    ocr_fact_review_gate_rows = build_ocr_fact_review_apply_gate(manifest, repo_root, ocr_financial_fact_candidates)
    ocr_fact_review_authorization_template = build_ocr_fact_review_authorization_template(manifest, ocr_fact_review_gate_rows)
    ocr_fact_review_authorization_preview_rows = build_ocr_fact_review_authorization_preview(manifest, ocr_fact_review_gate_rows)
    ocr_fact_cross_review_rows = build_ocr_fact_cross_review_summary(manifest, ocr_financial_fact_candidates, ocr_fact_review_gate_rows)
    ocr_fact_owner_review_batch_rows = build_ocr_fact_owner_review_batch_rows(manifest, ocr_fact_cross_review_rows)
    ocr_fact_ledger_staging_preview_rows = build_ocr_fact_ledger_staging_preview(manifest, ocr_financial_fact_candidates, ocr_fact_review_gate_rows)
    ocr_fact_evidence_review_queue_rows = build_ocr_fact_evidence_review_queue_rows(
        manifest,
        ocr_fact_ledger_staging_preview_rows,
    )
    ocr_fact_candidate_owner_worklist_rows = build_ocr_fact_candidate_owner_worklist_rows(
        manifest,
        ocr_fact_ledger_staging_preview_rows,
        ocr_fact_evidence_review_queue_rows,
    )
    ocr_fact_candidate_owner_decision_template = build_ocr_fact_candidate_owner_decision_template(
        manifest,
        ocr_fact_candidate_owner_worklist_rows,
    )
    ocr_fact_candidate_owner_decision_preview_rows = build_ocr_fact_candidate_owner_decision_preview_rows(
        manifest,
        repo_root,
        ocr_fact_candidate_owner_worklist_rows,
    )
    ocr_fact_candidate_owner_decision_progress_summary_rows = (
        build_ocr_fact_candidate_owner_decision_progress_summary_rows(
            manifest,
            ocr_fact_candidate_owner_decision_preview_rows,
        )
    )
    ocr_fact_controlled_ledger_row_preview_rows = build_ocr_fact_controlled_ledger_row_preview_rows(
        manifest,
        ocr_fact_ledger_staging_preview_rows,
        ocr_fact_candidate_owner_decision_preview_rows,
    )
    ocr_fact_controlled_ledger_apply_gate_rows = build_ocr_fact_controlled_ledger_apply_gate_rows(
        manifest,
        ocr_fact_controlled_ledger_row_preview_rows,
    )
    ocr_fact_owner_decision_correction_queue_rows = build_ocr_fact_owner_decision_correction_queue_rows(
        manifest,
        ocr_fact_controlled_ledger_apply_gate_rows,
    )
    ocr_fact_owner_decision_correction_evidence_packet_rows = (
        build_ocr_fact_owner_decision_correction_evidence_packet_rows(
            manifest,
            ocr_fact_owner_decision_correction_queue_rows,
            ocr_financial_fact_candidates,
            evidence,
        )
    )
    ocr_fact_owner_decision_correction_ocr_line_context_rows = (
        build_ocr_fact_owner_decision_correction_ocr_line_context_rows(
            manifest,
            input_dir,
            repo_root,
            ocr_fact_owner_decision_correction_evidence_packet_rows,
        )
    )
    ocr_fact_owner_decision_correction_chat_context_rows = (
        build_ocr_fact_owner_decision_correction_chat_context_rows(
            manifest,
            input_dir,
            ocr_fact_owner_decision_correction_evidence_packet_rows,
        )
    )
    ocr_fact_owner_decision_correction_chat_neighbor_context_rows = (
        build_ocr_fact_owner_decision_correction_chat_neighbor_context_rows(
            manifest,
            input_dir,
            ocr_fact_owner_decision_correction_chat_context_rows,
        )
    )
    ocr_fact_owner_decision_correction_owner_review_packet_rows = (
        build_ocr_fact_owner_decision_correction_owner_review_packet_rows(
            manifest,
            ocr_fact_owner_decision_correction_evidence_packet_rows,
            ocr_fact_owner_decision_correction_ocr_line_context_rows,
            ocr_fact_owner_decision_correction_chat_context_rows,
            ocr_fact_owner_decision_correction_chat_neighbor_context_rows,
        )
    )
    ocr_fact_owner_decision_correction_manifest_readiness_rows = (
        build_ocr_fact_owner_decision_correction_manifest_readiness_rows(
            manifest,
            repo_root,
            ocr_fact_owner_decision_correction_owner_review_packet_rows,
        )
    )
    ocr_fact_owner_decision_correction_draft = build_ocr_fact_owner_decision_correction_draft(
        manifest,
        ocr_fact_owner_decision_correction_queue_rows,
    )
    ocr_fact_owner_decision_correction_apply_preview_rows = (
        build_ocr_fact_owner_decision_correction_apply_preview_rows(
            manifest,
            ocr_fact_owner_decision_correction_draft,
        )
    )
    ocr_fact_owner_decision_correction_roundtrip_audit_rows = (
        build_ocr_fact_owner_decision_correction_roundtrip_audit_rows(
            manifest,
            ocr_fact_controlled_ledger_apply_gate_rows,
        )
    )
    ocr_fact_candidate_owner_authorization_update_draft = build_ocr_fact_candidate_owner_authorization_update_draft(
        manifest,
        ocr_fact_candidate_owner_decision_preview_rows,
    )
    ocr_fact_candidate_owner_authorization_update_preview_rows = (
        build_ocr_fact_candidate_owner_authorization_update_preview_rows(
            manifest,
            ocr_fact_candidate_owner_decision_preview_rows,
        )
    )
    chat_text_candidates = collect_chat_text_candidates(manifest, input_dir, evidence)
    chat_value_candidates = extract_chat_value_candidates(manifest, chat_text_candidates)
    chat_evidence_links = collect_chat_evidence_links(manifest, input_dir, evidence, chat_text_candidates, chat_value_candidates)
    attachment_reconciliation_rows = collect_attachment_evidence_reconciliation(manifest, input_dir, evidence)
    attachment_remediation_rows = build_attachment_reconciliation_remediation(manifest, attachment_reconciliation_rows)
    attachment_source_locator_rows = build_attachment_repair_source_locator(manifest, input_dir, attachment_remediation_rows)
    attachment_dry_run_rows = build_attachment_remediation_dry_run(manifest, attachment_remediation_rows)
    attachment_repair_plan_rows = build_attachment_repair_plan(manifest, attachment_dry_run_rows)
    attachment_apply_gate_rows = build_attachment_repair_apply_gate(manifest, repo_root, attachment_repair_plan_rows)
    attachment_authorization_template = build_attachment_repair_authorization_template(manifest, attachment_apply_gate_rows)
    attachment_authorization_preview_rows = build_attachment_repair_authorization_preview(manifest, attachment_apply_gate_rows)
    structured = extract_structured_csv_facts(manifest, input_dir, evidence)
    funding_forecast_rows = build_funding_forecast_rows(structured)
    cashflow_validation_rows = build_cashflow_validation_rows(structured, manifest["run_id"])
    metadata_signals = collect_kmfa_metadata_signals(repo_root, manifest["run_id"])
    balance_continuity_fail_count = sum(1 for row in cashflow_validation_rows if row["validation_status"] == "FAIL")
    internal_transfer_excluded_count = sum(1 for row in cashflow_validation_rows if row["internal_transfer_excluded"] == "true")
    manifest["screenshot_ocr_coverage_count"] = len(screenshot_ocr_coverage_rows)
    manifest["screenshot_ocr_ready_count"] = sum(1 for row in screenshot_ocr_coverage_rows if row["ocr_coverage_status"] == "ocr_text_sidecar_present_pending_review")
    manifest["screenshot_ocr_missing_count"] = sum(1 for row in screenshot_ocr_coverage_rows if row["ocr_coverage_status"] == "ocr_text_sidecar_missing")
    manifest["ocr_text_candidate_count"] = len(ocr_text_candidates)
    manifest["ocr_value_candidate_count"] = len(ocr_value_candidates)
    manifest["ocr_financial_fact_candidate_count"] = len(ocr_financial_fact_candidates)
    manifest["ocr_fact_cross_review_group_count"] = len(ocr_fact_cross_review_rows)
    manifest["ocr_fact_owner_review_batch_count"] = len(ocr_fact_owner_review_batch_rows)
    manifest["ocr_fact_owner_review_batch_blocking_count"] = sum(
        1 for row in ocr_fact_owner_review_batch_rows
        if row["owner_review_status"].startswith("blocked_")
    )
    manifest["ocr_fact_evidence_review_queue_count"] = len(ocr_fact_evidence_review_queue_rows)
    manifest["ocr_fact_evidence_review_queue_blocking_count"] = sum(
        1 for row in ocr_fact_evidence_review_queue_rows
        if row["evidence_review_status"].startswith("blocked_")
    )
    manifest["ocr_fact_candidate_owner_worklist_count"] = len(ocr_fact_candidate_owner_worklist_rows)
    manifest["ocr_fact_candidate_owner_worklist_ready_count"] = sum(
        1 for row in ocr_fact_candidate_owner_worklist_rows
        if row["authorization_validation_status"] == "valid_manifest_validation_only"
    )
    manifest["ocr_fact_candidate_owner_worklist_blocking_count"] = (
        len(ocr_fact_candidate_owner_worklist_rows)
        - manifest["ocr_fact_candidate_owner_worklist_ready_count"]
    )
    manifest["ocr_fact_candidate_owner_decision_template_count"] = len(
        ocr_fact_candidate_owner_decision_template["owner_decisions"]
    )
    manifest["ocr_fact_candidate_owner_decision_preview_count"] = len(ocr_fact_candidate_owner_decision_preview_rows)
    manifest["ocr_fact_candidate_owner_decision_preview_ready_count"] = sum(
        1 for row in ocr_fact_candidate_owner_decision_preview_rows
        if row["decision_preview_status"] == "ready_for_private_ocr_fact_authorization_update_no_write"
    )
    manifest["ocr_fact_candidate_owner_decision_preview_blocking_count"] = (
        len(ocr_fact_candidate_owner_decision_preview_rows)
        - manifest["ocr_fact_candidate_owner_decision_preview_ready_count"]
    )
    manifest["ocr_fact_candidate_owner_decision_progress_summary_count"] = len(
        ocr_fact_candidate_owner_decision_progress_summary_rows
    )
    manifest["ocr_fact_candidate_owner_decision_progress_summary_candidate_count"] = len(
        ocr_fact_candidate_owner_decision_preview_rows
    )
    manifest["ocr_fact_candidate_owner_decision_progress_summary_ready_count"] = (
        manifest["ocr_fact_candidate_owner_decision_preview_ready_count"]
    )
    manifest["ocr_fact_candidate_owner_decision_progress_summary_blocking_count"] = (
        manifest["ocr_fact_candidate_owner_decision_preview_blocking_count"]
    )
    manifest["ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count"] = sum(
        1 for row in ocr_fact_candidate_owner_decision_preview_rows
        if row["decision_validation_status"] == "missing_decision_manifest"
    )
    manifest["ocr_fact_candidate_owner_authorization_update_draft_count"] = len(
        ocr_fact_candidate_owner_authorization_update_draft["fact_candidate_authorizations"]
    )
    manifest["ocr_fact_candidate_owner_authorization_update_preview_count"] = len(
        ocr_fact_candidate_owner_authorization_update_preview_rows
    )
    manifest["ocr_fact_candidate_owner_authorization_update_preview_ready_count"] = sum(
        1 for row in ocr_fact_candidate_owner_authorization_update_preview_rows
        if row["authorization_update_preview_status"] == "ready_for_private_ocr_fact_authorization_manifest_update_no_write"
    )
    manifest["ocr_fact_candidate_owner_authorization_update_preview_blocking_count"] = (
        len(ocr_fact_candidate_owner_authorization_update_preview_rows)
        - manifest["ocr_fact_candidate_owner_authorization_update_preview_ready_count"]
    )
    manifest["ocr_fact_ledger_staging_preview_count"] = len(ocr_fact_ledger_staging_preview_rows)
    manifest["ocr_fact_ledger_staging_preview_ready_count"] = sum(1 for row in ocr_fact_ledger_staging_preview_rows if row["staging_preview_status"] == "ready_for_ledger_staging_review_no_write")
    manifest["ocr_fact_ledger_staging_preview_blocked_count"] = len(ocr_fact_ledger_staging_preview_rows) - manifest["ocr_fact_ledger_staging_preview_ready_count"]
    manifest["ocr_fact_controlled_ledger_row_preview_count"] = len(ocr_fact_controlled_ledger_row_preview_rows)
    manifest["ocr_fact_controlled_ledger_row_preview_ready_count"] = len(ocr_fact_controlled_ledger_row_preview_rows)
    manifest["ocr_fact_controlled_ledger_row_preview_blocking_count"] = 0
    manifest["ocr_fact_controlled_ledger_apply_gate_count"] = len(ocr_fact_controlled_ledger_apply_gate_rows)
    manifest["ocr_fact_controlled_ledger_apply_gate_ready_count"] = sum(
        1 for row in ocr_fact_controlled_ledger_apply_gate_rows
        if row["apply_gate_status"] == "ready_for_controlled_ledger_apply_no_write"
    )
    manifest["ocr_fact_controlled_ledger_apply_gate_blocking_count"] = (
        len(ocr_fact_controlled_ledger_apply_gate_rows)
        - manifest["ocr_fact_controlled_ledger_apply_gate_ready_count"]
    )
    manifest["ocr_fact_controlled_ledger_apply_gate_planned_apply_count"] = sum(
        int(row["planned_apply_count"]) for row in ocr_fact_controlled_ledger_apply_gate_rows
    )
    manifest["ocr_fact_controlled_ledger_apply_gate_write_allowed_count"] = sum(
        1 for row in ocr_fact_controlled_ledger_apply_gate_rows
        if row["fund_ledger_write_allowed"] == "true" or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_queue_count"] = len(
        ocr_fact_owner_decision_correction_queue_rows
    )
    manifest["ocr_fact_owner_decision_correction_queue_blocking_count"] = len(
        ocr_fact_owner_decision_correction_queue_rows
    )
    manifest["ocr_fact_owner_decision_correction_queue_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_queue_rows
        if row["fund_ledger_write_allowed"] == "true" or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_evidence_packet_count"] = len(
        ocr_fact_owner_decision_correction_evidence_packet_rows
    )
    manifest["ocr_fact_owner_decision_correction_evidence_packet_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_evidence_packet_rows
        if row["evidence_packet_status"] == "ready_for_owner_field_review_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_evidence_packet_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_evidence_packet_rows)
        - manifest["ocr_fact_owner_decision_correction_evidence_packet_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_evidence_packet_rows
        if row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_ocr_line_context_count"] = len(
        ocr_fact_owner_decision_correction_ocr_line_context_rows
    )
    manifest["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_ocr_line_context_rows
        if row["ocr_line_context_status"] == "ready_ocr_line_context_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_ocr_line_context_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_ocr_line_context_rows)
        - manifest["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_ocr_line_context_rows
        if row["owner_field_autofill_allowed"] == "true"
        or row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_chat_context_count"] = len(
        ocr_fact_owner_decision_correction_chat_context_rows
    )
    manifest["ocr_fact_owner_decision_correction_chat_context_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_chat_context_rows
        if row["context_status"] in {"ready_chat_context_no_write", "ready_manifest_context_only_no_write"}
    )
    manifest["ocr_fact_owner_decision_correction_chat_context_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_chat_context_rows)
        - manifest["ocr_fact_owner_decision_correction_chat_context_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_chat_context_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_chat_context_rows
        if row["owner_field_autofill_allowed"] == "true"
        or row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_count"] = len(
        ocr_fact_owner_decision_correction_chat_neighbor_context_rows
    )
    manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_chat_neighbor_context_rows
        if row["neighbor_context_status"] == "ready_neighbor_context_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_chat_neighbor_context_rows)
        - manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_chat_neighbor_context_rows
        if row["owner_field_autofill_allowed"] == "true"
        or row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_owner_review_packet_count"] = len(
        ocr_fact_owner_decision_correction_owner_review_packet_rows
    )
    manifest["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_owner_review_packet_rows
        if row["owner_review_packet_status"] == "ready_for_owner_field_decision_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_owner_review_packet_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_owner_review_packet_rows)
        - manifest["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_owner_review_packet_rows
        if row["owner_field_autofill_allowed"] == "true"
        or row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_manifest_readiness_count"] = len(
        ocr_fact_owner_decision_correction_manifest_readiness_rows
    )
    manifest["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_manifest_readiness_rows
        if row["manifest_readiness_status"] == "ready_for_owner_decision_manifest_validation_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_manifest_readiness_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_manifest_readiness_rows)
        - manifest["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_manifest_readiness_rows
        if row["owner_decision_manifest_write_allowed"] == "true"
        or row["source_mutation_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_draft_count"] = len(
        ocr_fact_owner_decision_correction_draft["owner_decisions"]
    )
    manifest["ocr_fact_owner_decision_correction_draft_write_allowed_count"] = 0
    manifest["ocr_fact_owner_decision_correction_apply_preview_count"] = len(
        ocr_fact_owner_decision_correction_apply_preview_rows
    )
    manifest["ocr_fact_owner_decision_correction_apply_preview_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_apply_preview_rows
        if row["correction_apply_preview_status"] == "ready_for_private_owner_decision_manifest_manual_save_no_write"
    )
    manifest["ocr_fact_owner_decision_correction_apply_preview_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_apply_preview_rows)
        - manifest["ocr_fact_owner_decision_correction_apply_preview_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_apply_preview_rows
        if row["owner_decision_manifest_write_allowed"] == "true"
    )
    manifest["ocr_fact_owner_decision_correction_roundtrip_audit_count"] = len(
        ocr_fact_owner_decision_correction_roundtrip_audit_rows
    )
    manifest["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_roundtrip_audit_rows
        if row["correction_roundtrip_status"] in {
            "owner_correction_resolved_apply_gate_ready_no_write",
            "no_owner_correction_required_apply_gate_ready_no_write",
        }
    )
    manifest["ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count"] = (
        len(ocr_fact_owner_decision_correction_roundtrip_audit_rows)
        - manifest["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"]
    )
    manifest["ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count"] = sum(
        1 for row in ocr_fact_owner_decision_correction_roundtrip_audit_rows
        if row["owner_decision_manifest_write_allowed"] == "true"
        or row["fund_ledger_write_allowed"] == "true"
        or row["formal_fund_ledger_write_allowed"] == "true"
    )
    manifest["ocr_fact_review_apply_gate_count"] = len(ocr_fact_review_gate_rows)
    manifest["ocr_fact_review_authorization_present_count"] = sum(1 for row in ocr_fact_review_gate_rows if row["operator_authorization_present"] == "true")
    manifest["ocr_fact_review_authorization_valid_count"] = sum(1 for row in ocr_fact_review_gate_rows if row["authorization_validation_status"] == "valid_manifest_validation_only")
    manifest["ocr_fact_review_authorization_template_count"] = len(ocr_fact_review_authorization_template["fact_candidate_authorizations"])
    manifest["ocr_fact_review_authorization_template_authorized_count"] = sum(1 for row in ocr_fact_review_authorization_template["fact_candidate_authorizations"] if row["authorized"] is True)
    manifest["ocr_fact_review_authorization_preview_count"] = len(ocr_fact_review_authorization_preview_rows)
    manifest["ocr_fact_review_authorization_preview_ready_count"] = sum(1 for row in ocr_fact_review_authorization_preview_rows if row["preview_status"] == "ready_for_operator_review_no_ledger_promotion")
    manifest["ocr_fact_review_authorization_preview_blocked_count"] = len(ocr_fact_review_authorization_preview_rows) - manifest["ocr_fact_review_authorization_preview_ready_count"]
    manifest["chat_text_candidate_count"] = len(chat_text_candidates)
    manifest["chat_value_candidate_count"] = len(chat_value_candidates)
    manifest["chat_evidence_link_count"] = len(chat_evidence_links)
    manifest["chat_evidence_linked_count"] = sum(1 for row in chat_evidence_links if row["link_status"] == "linked_pending_review")
    manifest["attachment_reconciliation_count"] = len(attachment_reconciliation_rows)
    manifest["attachment_reconciliation_linked_count"] = sum(1 for row in attachment_reconciliation_rows if row["reconciliation_status"] == "evidence_linked_pending_review")
    manifest["attachment_reconciliation_blocking_count"] = sum(1 for row in attachment_reconciliation_rows if row["reconciliation_status"].endswith("_blocking"))
    manifest["attachment_remediation_count"] = len(attachment_remediation_rows)
    manifest["attachment_remediation_open_count"] = sum(1 for row in attachment_remediation_rows if row["review_status"] == "pending_operator_action")
    manifest["attachment_repair_source_locator_count"] = len(attachment_source_locator_rows)
    manifest["attachment_repair_source_locator_candidate_count"] = sum(
        1 for row in attachment_source_locator_rows
        if row["locator_status"] in {"candidate_already_in_input_dir", "candidate_in_source_zip"}
    )
    manifest["attachment_repair_source_locator_apply_allowed_count"] = sum(
        1 for row in attachment_source_locator_rows if row["safe_to_apply"] == "true"
    )
    manifest["attachment_remediation_dry_run_count"] = len(attachment_dry_run_rows)
    manifest["attachment_remediation_apply_allowed_count"] = sum(1 for row in attachment_dry_run_rows if row["safe_to_apply"] == "true")
    manifest["attachment_repair_plan_count"] = len(attachment_repair_plan_rows)
    manifest["attachment_repair_plan_open_count"] = sum(1 for row in attachment_repair_plan_rows if row["review_status"] == "pending_operator_action")
    manifest["attachment_repair_apply_gate_count"] = len(attachment_apply_gate_rows)
    manifest["attachment_repair_apply_blocked_count"] = sum(1 for row in attachment_apply_gate_rows if row["apply_allowed"] == "false")
    manifest["attachment_repair_authorization_present_count"] = sum(1 for row in attachment_apply_gate_rows if row["operator_authorization_present"] == "true")
    manifest["attachment_repair_authorization_valid_count"] = sum(1 for row in attachment_apply_gate_rows if row["authorization_validation_status"] == "valid_manifest_validation_only")
    manifest["attachment_repair_authorization_template_count"] = len(attachment_authorization_template["repair_plan_authorizations"])
    manifest["attachment_repair_authorization_template_authorized_count"] = sum(1 for row in attachment_authorization_template["repair_plan_authorizations"] if row["authorized"] is True)
    manifest["attachment_repair_authorization_preview_count"] = len(attachment_authorization_preview_rows)
    manifest["attachment_repair_authorization_preview_ready_count"] = sum(1 for row in attachment_authorization_preview_rows if row["preview_status"] == "ready_for_operator_review_no_apply")
    manifest["attachment_repair_authorization_preview_blocked_count"] = len(attachment_authorization_preview_rows) - manifest["attachment_repair_authorization_preview_ready_count"]
    manifest["attachment_repair_apply_allowed_count"] = sum(1 for row in attachment_apply_gate_rows if row["apply_allowed"] == "true")
    manifest["metadata_signal_count"] = len(metadata_signals)
    manifest["forecast_row_count"] = len(funding_forecast_rows)
    manifest["cashflow_validation_row_count"] = len(cashflow_validation_rows)
    manifest["balance_continuity_fail_count"] = balance_continuity_fail_count
    if structured["fund_rows"]:
        manifest["status"] = "STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW"
        manifest["structured_fact_count"] = len(structured["fund_rows"])
        manifest["data_quality_issues"] = [{
            "issue_type": "STRUCTURED_FACTS_PENDING_REVIEW",
            "severity": "blocking_for_management_conclusion",
            "observed_at": manifest["generated_at"],
            "action": "Structured CSV facts were extracted from real source files; human/cross review is still required before management conclusion.",
        }]
    write_csv(
        run_dir / "evidence_index.csv",
        ["evidence_id", "relative_path", "kind", "sha256", "size_bytes", "review_status"],
        evidence,
    )
    skill_root = Path(__file__).resolve().parents[1]
    template = skill_root / "templates" / TEMPLATE_NAME
    workbook_path = run_dir / f"资金与税费管理母版_{manifest['run_id']}.xlsx"
    shutil.copyfile(template, workbook_path)
    write_structured_facts_to_workbook(workbook_path, structured, evidence, input_dir, manifest["run_id"])
    write_metadata_signals_to_workbook(workbook_path, metadata_signals, len(structured["risk_rows"]))
    automation_readiness_rows = build_automation_readiness_rows(repo_root, automation_root)
    write_runtime_rules_to_workbook(workbook_path, manifest, input_dir, automation_readiness_rows)
    workbook_quality_rows = collect_workbook_quality_checks(workbook_path)
    workbook_quality_blocking_count = sum(1 for row in workbook_quality_rows if row["management_blocking"] == "true")
    automation_readiness_ready_count = sum(1 for row in automation_readiness_rows if row["schedule_ready"] == "true")
    automation_readiness_blocking_count = len(automation_readiness_rows) - automation_readiness_ready_count
    manifest["workbook_quality_check_count"] = len(workbook_quality_rows)
    manifest["workbook_quality_blocking_count"] = workbook_quality_blocking_count
    manifest["automation_readiness_count"] = len(automation_readiness_rows)
    manifest["automation_readiness_ready_count"] = automation_readiness_ready_count
    manifest["automation_readiness_blocking_count"] = automation_readiness_blocking_count
    manifest["automation_readiness_status"] = (
        automation_readiness_rows[0]["status"] if automation_readiness_rows else "CODEX_AUTOMATION_UNKNOWN"
    )

    write_csv(run_dir / "fund_ledger.csv", [
        "ledger_id",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "inflow",
        "outflow",
        "ending_balance",
        "flow_type",
        "source_evidence_id",
        "source_row_number",
        "extraction_status",
    ], structured["fund_rows"])
    write_csv(run_dir / "net_flow_ledger.csv", [
        "date",
        "external_inflow",
        "external_outflow",
        "internal_transfer_in",
        "internal_transfer_out",
        "internal_transfer_net",
        "unclassified_net",
        "review_status",
    ], structured["net_flow_rows"])
    write_csv(run_dir / "company_bank_matrix.csv", [
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "ending_balance",
        "evidence_count",
        "review_status",
    ], structured["matrix_rows"])
    write_csv(run_dir / "tax_loan_risk.csv", [
        "risk_id",
        "risk_type",
        "due_date",
        "amount",
        "source_evidence_id",
        "review_status",
    ], structured["risk_rows"])
    write_csv(run_dir / "funding_forecast.csv", [
        "period_date",
        "starting_bank_cash",
        "known_inflow",
        "known_outflow",
        "projected_bank_cash",
        "funding_gap",
        "risk_types",
        "source_evidence_ids",
        "forecast_basis",
        "review_status",
    ], funding_forecast_rows)
    write_csv(run_dir / "cashflow_validation.csv", [
        "validation_id",
        "ledger_id",
        "date",
        "company",
        "bank",
        "account_alias",
        "previous_ending_balance",
        "inflow",
        "outflow",
        "expected_ending_balance",
        "actual_ending_balance",
        "continuity_diff",
        "flow_type",
        "operating_cashflow_effect",
        "internal_transfer_excluded",
        "validation_status",
        "review_status",
        "source_evidence_id",
    ], cashflow_validation_rows)
    write_csv(run_dir / "screenshot_ocr_coverage.csv", [
        "ocr_coverage_id",
        "evidence_id",
        "source_image_relative_path",
        "ocr_sidecar_candidates",
        "ocr_text_relative_path",
        "ocr_coverage_status",
        "next_action",
        "review_status",
        "financial_fact_promoted",
    ], screenshot_ocr_coverage_rows)
    write_csv(run_dir / "ocr_text_candidates.csv", [
        "ocr_candidate_id",
        "evidence_id",
        "source_image_relative_path",
        "ocr_text_relative_path",
        "ocr_text_sha256",
        "text_length",
        "text_excerpt",
        "extraction_status",
        "review_status",
        "financial_fact_promoted",
    ], ocr_text_candidates)
    write_csv(run_dir / "ocr_value_candidates.csv", [
        "value_candidate_id",
        "ocr_candidate_id",
        "evidence_id",
        "source_image_relative_path",
        "ocr_text_relative_path",
        "candidate_type",
        "raw_value",
        "normalized_value",
        "currency",
        "line_number",
        "line_text",
        "extraction_status",
        "review_status",
        "financial_fact_promoted",
    ], ocr_value_candidates)
    write_csv(run_dir / "ocr_financial_fact_candidates.csv", [
        "fact_candidate_id",
        "ocr_candidate_id",
        "evidence_id",
        "source_image_relative_path",
        "ocr_text_relative_path",
        "business_date",
        "company",
        "bank",
        "account_alias",
        "candidate_metric",
        "amount",
        "currency",
        "line_number",
        "line_text_excerpt",
        "extraction_status",
        "review_status",
        "financial_fact_promoted",
        "promotion_blocker",
    ], ocr_financial_fact_candidates)
    write_csv(run_dir / "ocr_fact_cross_review.csv", [
        "cross_review_group_id",
        "candidate_metric",
        "candidate_count",
        "candidate_amount_total",
        "evidence_count",
        "company_present_count",
        "company_missing_count",
        "bank_present_count",
        "bank_missing_count",
        "operator_authorized_count",
        "authorization_blocked_count",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "review_status",
    ], ocr_fact_cross_review_rows)
    write_csv(run_dir / "ocr_fact_owner_review_batch.csv", [
        "ocr_fact_owner_review_batch_id",
        "cross_review_group_id",
        "candidate_metric",
        "source_artifact",
        "candidate_count",
        "candidate_amount_total",
        "evidence_count",
        "company_missing_count",
        "bank_missing_count",
        "operator_authorized_count",
        "authorization_blocked_count",
        "priority",
        "owner_review_status",
        "owner_authorization_required",
        "authorization_manifest_relative_path",
        "authorization_scope",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_owner_action",
    ], ocr_fact_owner_review_batch_rows)
    write_csv(run_dir / "ocr_fact_evidence_review_queue.csv", [
        "ocr_fact_evidence_review_queue_id",
        "candidate_metric",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "candidate_count",
        "candidate_amount_total",
        "company_missing_count",
        "bank_missing_count",
        "operator_authorized_count",
        "authorization_blocked_count",
        "priority",
        "evidence_review_status",
        "owner_authorization_required",
        "authorization_manifest_relative_path",
        "authorization_scope",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_owner_action",
    ], ocr_fact_evidence_review_queue_rows)
    write_csv(run_dir / "ocr_fact_candidate_owner_worklist.csv", [
        "owner_worklist_id",
        "ocr_fact_evidence_review_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "business_date",
        "company",
        "bank",
        "account_alias",
        "amount",
        "currency",
        "proposed_amount_role",
        "proposed_liquidity_tier",
        "proposed_flow_type",
        "authorization_validation_status",
        "staging_preview_status",
        "owner_authorization_decision",
        "owner_corrected_company",
        "owner_corrected_bank",
        "owner_note",
        "authorization_manifest_relative_path",
        "authorization_scope",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_owner_action",
    ], ocr_fact_candidate_owner_worklist_rows)
    (run_dir / "ocr_fact_candidate_owner_decision_template.json").write_text(
        json.dumps(ocr_fact_candidate_owner_decision_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "ocr_fact_candidate_owner_decision_preview.csv", [
        "decision_preview_id",
        "owner_worklist_id",
        "ocr_fact_evidence_review_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "decision_manifest_relative_path",
        "decision_validation_status",
        "decision_preview_status",
        "owner_authorization_decision",
        "owner_corrected_company",
        "owner_corrected_bank",
        "owner_note",
        "authorization_manifest_relative_path",
        "authorization_scope",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_candidate_owner_decision_preview_rows)
    write_csv(run_dir / "ocr_fact_candidate_owner_decision_progress_summary.csv", [
        "progress_summary_id",
        "summary_level",
        "candidate_metric",
        "candidate_count",
        "ready_count",
        "blocking_count",
        "missing_owner_decision_manifest_count",
        "pending_owner_review_count",
        "approved_for_authorization_count",
        "needs_correction_count",
        "rejected_count",
        "missing_company_count",
        "missing_bank_count",
        "authorization_update_ready_count",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_candidate_owner_decision_progress_summary_rows)
    (run_dir / "ocr_fact_candidate_owner_authorization_update_draft.json").write_text(
        json.dumps(ocr_fact_candidate_owner_authorization_update_draft, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "ocr_fact_candidate_owner_authorization_update_preview.csv", [
        "authorization_update_preview_id",
        "decision_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "owner_authorization_decision",
        "decision_preview_status",
        "authorization_update_preview_status",
        "authorization_manifest_relative_path",
        "authorization_update_allowed",
        "draft_authorized_value",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_candidate_owner_authorization_update_preview_rows)
    write_csv(run_dir / "ocr_fact_ledger_staging_preview.csv", [
        "staging_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "business_date",
        "company",
        "bank",
        "account_alias",
        "amount",
        "currency",
        "proposed_amount_role",
        "proposed_liquidity_tier",
        "proposed_flow_type",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "authorization_validation_status",
        "staging_preview_status",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "review_status",
    ], ocr_fact_ledger_staging_preview_rows)
    write_csv(run_dir / "ocr_fact_controlled_ledger_row_preview.csv", [
        "controlled_ledger_preview_id",
        "staging_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "inflow",
        "outflow",
        "ending_balance",
        "amount",
        "currency",
        "flow_type",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "authorization_validation_status",
        "owner_decision_preview_id",
        "owner_decision_preview_status",
        "owner_correction_applied",
        "company_source",
        "bank_source",
        "ledger_preview_status",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "review_status",
    ], ocr_fact_controlled_ledger_row_preview_rows)
    write_csv(run_dir / "ocr_fact_controlled_ledger_apply_gate.csv", [
        "controlled_ledger_apply_gate_id",
        "controlled_ledger_preview_id",
        "staging_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "inflow",
        "outflow",
        "ending_balance",
        "amount",
        "currency",
        "flow_type",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "authorization_validation_status",
        "owner_decision_preview_id",
        "owner_decision_preview_status",
        "owner_correction_applied",
        "company_source",
        "bank_source",
        "ledger_preview_status",
        "apply_gate_status",
        "planned_apply_count",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "gate_reason",
        "review_status",
    ], ocr_fact_controlled_ledger_apply_gate_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_queue.csv", [
        "correction_queue_id",
        "controlled_ledger_apply_gate_id",
        "controlled_ledger_preview_id",
        "staging_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "missing_required_fields",
        "required_owner_fields",
        "current_date",
        "current_company",
        "current_bank",
        "current_account_alias",
        "liquidity_tier",
        "amount",
        "currency",
        "flow_type",
        "source_evidence_id",
        "source_ocr_text_relative_path",
        "owner_decision_manifest_relative_path",
        "owner_decision_preview_status",
        "owner_correction_applied",
        "correction_queue_status",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_queue_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_evidence_packet.csv", [
        "evidence_packet_id",
        "source_correction_queue_id",
        "source_controlled_ledger_apply_gate_id",
        "fact_candidate_id",
        "candidate_metric",
        "missing_required_fields",
        "required_owner_fields",
        "current_date",
        "current_company",
        "current_bank",
        "candidate_business_date",
        "candidate_amount",
        "candidate_currency",
        "candidate_line_number",
        "candidate_line_text_excerpt",
        "source_evidence_id",
        "source_evidence_relative_path",
        "source_image_relative_path",
        "source_ocr_text_relative_path",
        "owner_decision_manifest_relative_path",
        "owner_decision_json_fragment",
        "evidence_packet_status",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_evidence_packet_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_ocr_line_context.csv", [
        "ocr_line_context_id",
        "source_evidence_packet_id",
        "source_correction_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "source_evidence_id",
        "source_image_relative_path",
        "source_ocr_text_relative_path",
        "target_ocr_line_number",
        "ocr_line_number",
        "ocr_line_offset",
        "ocr_line_text_excerpt",
        "ocr_line_context_radius",
        "ocr_line_context_status",
        "owner_field_autofill_allowed",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_ocr_line_context_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_chat_context.csv", [
        "chat_context_id",
        "source_evidence_packet_id",
        "source_correction_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "source_evidence_id",
        "source_image_relative_path",
        "source_ocr_text_relative_path",
        "open_message_id",
        "message_time",
        "sender_name",
        "manifest_relative_path",
        "manifest_row_number",
        "resource_type",
        "resource_id",
        "resource_status",
        "chat_record_relative_path",
        "chat_record_row_number",
        "chat_content_excerpt",
        "quoted_sender",
        "quoted_content_excerpt",
        "resource_count",
        "resource_types",
        "context_status",
        "owner_field_autofill_allowed",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_chat_context_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_chat_neighbor_context.csv", [
        "chat_neighbor_context_id",
        "source_chat_context_id",
        "source_evidence_packet_id",
        "source_correction_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "source_evidence_id",
        "source_image_relative_path",
        "open_message_id",
        "chat_record_relative_path",
        "target_chat_record_row_number",
        "neighbor_chat_record_row_number",
        "neighbor_offset",
        "message_time",
        "sender_name",
        "content_excerpt",
        "quoted_sender",
        "quoted_content_excerpt",
        "resource_count",
        "resource_types",
        "neighbor_context_radius",
        "neighbor_context_status",
        "owner_field_autofill_allowed",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_chat_neighbor_context_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_owner_review_packet.csv", [
        "owner_review_packet_id",
        "source_evidence_packet_id",
        "source_correction_queue_id",
        "fact_candidate_id",
        "candidate_metric",
        "missing_required_fields",
        "required_owner_fields",
        "current_company",
        "current_bank",
        "candidate_business_date",
        "candidate_amount",
        "candidate_currency",
        "candidate_line_number",
        "candidate_line_text_excerpt",
        "source_evidence_id",
        "source_image_relative_path",
        "source_ocr_text_relative_path",
        "owner_decision_manifest_relative_path",
        "ocr_line_context_ready_count",
        "ocr_line_context_excerpt",
        "chat_context_ready_count",
        "chat_context_excerpt",
        "chat_neighbor_context_ready_count",
        "chat_neighbor_context_excerpt",
        "owner_review_packet_status",
        "owner_field_autofill_allowed",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_owner_review_packet_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_manifest_readiness.csv", [
        "manifest_readiness_id",
        "source_owner_review_packet_id",
        "source_evidence_packet_id",
        "fact_candidate_id",
        "candidate_metric",
        "missing_required_fields",
        "required_owner_fields",
        "decision_manifest_relative_path",
        "decision_manifest_status",
        "owner_decision_entry_status",
        "owner_authorization_decision",
        "owner_corrected_company",
        "owner_corrected_bank",
        "missing_owner_values",
        "manifest_readiness_status",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_manifest_readiness_rows)
    (run_dir / "ocr_fact_owner_decision_correction_draft.json").write_text(
        json.dumps(ocr_fact_owner_decision_correction_draft, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "ocr_fact_owner_decision_correction_apply_preview.csv", [
        "correction_apply_preview_id",
        "source_correction_queue_id",
        "source_controlled_ledger_apply_gate_id",
        "fact_candidate_id",
        "candidate_metric",
        "draft_owner_authorization_decision",
        "required_owner_fields",
        "missing_owner_values",
        "owner_corrected_company",
        "owner_corrected_bank",
        "output_decision_manifest_relative_path",
        "correction_apply_preview_status",
        "manual_save_ready",
        "owner_decision_manifest_write_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_apply_preview_rows)
    write_csv(run_dir / "ocr_fact_owner_decision_correction_roundtrip_audit.csv", [
        "correction_roundtrip_audit_id",
        "controlled_ledger_apply_gate_id",
        "controlled_ledger_preview_id",
        "fact_candidate_id",
        "candidate_metric",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "amount",
        "currency",
        "flow_type",
        "owner_decision_preview_id",
        "owner_decision_preview_status",
        "owner_correction_applied",
        "company_source",
        "bank_source",
        "apply_gate_status",
        "planned_apply_count",
        "correction_roundtrip_status",
        "owner_decision_manifest_write_allowed",
        "source_mutation_allowed",
        "fund_ledger_write_allowed",
        "formal_fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "recommended_next_step",
    ], ocr_fact_owner_decision_correction_roundtrip_audit_rows)
    write_csv(run_dir / "ocr_fact_review_apply_gate.csv", [
        "review_gate_id",
        "fact_candidate_id",
        "candidate_metric",
        "evidence_id",
        "amount",
        "currency",
        "operator_authorization_required",
        "authorization_manifest_relative_path",
        "operator_authorization_present",
        "authorization_validation_status",
        "authorization_ticket",
        "authorized_by",
        "authorized_at",
        "authorization_scope",
        "review_gate_status",
        "staging_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "gate_reason",
        "relative_path",
        "review_status",
    ], ocr_fact_review_gate_rows)
    (run_dir / "ocr_fact_review_authorization_template.json").write_text(
        json.dumps(ocr_fact_review_authorization_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "ocr_fact_review_authorization_preview.csv", [
        "review_preview_id",
        "review_gate_id",
        "fact_candidate_id",
        "candidate_metric",
        "authorization_validation_status",
        "preview_status",
        "impact_scope",
        "staging_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "relative_path",
        "review_status",
    ], ocr_fact_review_authorization_preview_rows)
    write_csv(run_dir / "chat_text_candidates.csv", [
        "chat_text_candidate_id",
        "evidence_id",
        "source_csv_relative_path",
        "source_row_number",
        "open_message_id",
        "message_time",
        "sender_name",
        "text_role",
        "text_sha256",
        "text_length",
        "text_excerpt",
        "extraction_status",
        "review_status",
        "financial_fact_promoted",
    ], [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in chat_text_candidates
    ])
    write_csv(run_dir / "chat_value_candidates.csv", [
        "value_candidate_id",
        "chat_text_candidate_id",
        "evidence_id",
        "source_csv_relative_path",
        "source_row_number",
        "candidate_type",
        "raw_value",
        "normalized_value",
        "currency",
        "text_role",
        "line_text",
        "extraction_status",
        "review_status",
        "financial_fact_promoted",
    ], chat_value_candidates)
    write_csv(run_dir / "chat_evidence_links.csv", [
        "chat_evidence_link_id",
        "chat_text_candidate_id",
        "chat_value_candidate_ids",
        "open_message_id",
        "source_csv_relative_path",
        "source_row_number",
        "manifest_relative_path",
        "manifest_row_number",
        "resource_type",
        "resource_id",
        "resource_status",
        "linked_evidence_id",
        "linked_relative_path",
        "link_status",
        "review_status",
        "financial_fact_promoted",
    ], chat_evidence_links)
    write_csv(run_dir / "attachment_evidence_reconciliation.csv", [
        "attachment_reconciliation_id",
        "open_message_id",
        "manifest_relative_path",
        "manifest_row_number",
        "resource_type",
        "resource_id",
        "resource_status",
        "manifest_output_path",
        "linked_evidence_id",
        "manifest_sha256",
        "evidence_sha256",
        "reconciliation_status",
        "review_status",
        "financial_fact_promoted",
    ], attachment_reconciliation_rows)
    write_csv(run_dir / "attachment_reconciliation_remediation.csv", [
        "remediation_id",
        "attachment_reconciliation_id",
        "open_message_id",
        "blocking_status",
        "resource_status",
        "action_code",
        "owner_queue",
        "action_reason",
        "evidence_required",
        "automation_safe",
        "formal_fact_allowed",
        "relative_path",
        "review_status",
    ], attachment_remediation_rows)
    write_csv(run_dir / "attachment_repair_source_locator.csv", [
        "source_locator_id",
        "remediation_id",
        "attachment_reconciliation_id",
        "open_message_id",
        "action_code",
        "relative_path",
        "local_input_exists",
        "source_zip_member",
        "locator_status",
        "locator_reason",
        "safe_to_apply",
        "source_mutation_allowed",
        "apply_performed",
        "formal_fact_allowed",
        "review_status",
    ], attachment_source_locator_rows)
    write_csv(run_dir / "attachment_remediation_dry_run.csv", [
        "dry_run_id",
        "remediation_id",
        "open_message_id",
        "action_code",
        "owner_queue",
        "dry_run_status",
        "dry_run_reason",
        "safe_to_apply",
        "apply_performed",
        "formal_fact_allowed",
        "relative_path",
        "review_status",
    ], attachment_dry_run_rows)
    write_csv(run_dir / "attachment_repair_plan.csv", [
        "repair_plan_id",
        "dry_run_id",
        "remediation_id",
        "open_message_id",
        "repair_plan_status",
        "required_command_family",
        "plan_instruction",
        "operator_confirmation_required",
        "source_mutation_allowed",
        "apply_performed",
        "formal_fact_allowed",
        "relative_path",
        "review_status",
    ], attachment_repair_plan_rows)
    write_csv(run_dir / "attachment_repair_apply_gate.csv", [
        "apply_gate_id",
        "repair_plan_id",
        "remediation_id",
        "open_message_id",
        "required_command_family",
        "operator_authorization_required",
        "authorization_manifest_relative_path",
        "operator_authorization_present",
        "authorization_validation_status",
        "authorization_ticket",
        "authorized_by",
        "authorized_at",
        "authorization_scope",
        "apply_gate_status",
        "apply_allowed",
        "source_mutation_allowed",
        "apply_performed",
        "formal_fact_allowed",
        "gate_reason",
        "relative_path",
        "review_status",
    ], attachment_apply_gate_rows)
    (run_dir / "attachment_repair_authorization_template.json").write_text(
        json.dumps(attachment_authorization_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "attachment_repair_authorization_preview.csv", [
        "authorization_preview_id",
        "apply_gate_id",
        "repair_plan_id",
        "open_message_id",
        "required_command_family",
        "authorization_validation_status",
        "preview_status",
        "impact_scope",
        "source_mutation_allowed",
        "apply_allowed",
        "apply_performed",
        "formal_fact_allowed",
        "relative_path",
        "review_status",
    ], attachment_authorization_preview_rows)
    write_csv(run_dir / "workbook_quality_checks.csv", [
        "check_id",
        "check_name",
        "status",
        "management_blocking",
        "details",
    ], workbook_quality_rows)
    write_csv(run_dir / "kmfa_metadata_signals.csv", [
        "signal_id",
        "signal_type",
        "source_path",
        "source_ref",
        "stage_phase",
        "status",
        "severity",
        "report_grade",
        "formal_action_allowed",
        "review_status",
        "remark",
    ], metadata_signals)
    write_csv(run_dir / "automation_readiness.csv", [
        "automation_readiness_id",
        "status",
        "automation_id",
        "automation_path",
        "expected_timezone",
        "rrule",
        "cwd",
        "schedule_ready",
        "mismatch_count",
        "mismatch_fields",
        "management_conclusion_allowed",
        "next_action",
    ], automation_readiness_rows)
    exception_tasks = [
        {
            "task_id": f"EX-{manifest['run_id']}-{index:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "PENDING_OCR_OR_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": "Real source evidence indexed; financial facts require OCR/table extraction and review before use.",
            "relative_path": row["relative_path"],
            "review_status": "pending",
        }
        for index, row in enumerate(evidence, 1)
    ]
    for row in ocr_text_candidates:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "OCR_TEXT_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['ocr_candidate_id']} OCR text sidecar is indexed; human review is required before promoting any amount.",
            "relative_path": row["ocr_text_relative_path"],
            "review_status": "pending",
        })
    for row in screenshot_ocr_coverage_rows:
        if row["ocr_coverage_status"] != "ocr_text_sidecar_missing":
            continue
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "SCREENSHOT_OCR_MISSING",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['source_image_relative_path']} has no real OCR text sidecar; run OCR or attach a reviewed sidecar before value extraction.",
            "relative_path": row["source_image_relative_path"],
            "review_status": "pending",
        })
    for row in ocr_value_candidates:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "OCR_VALUE_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['value_candidate_id']} {row['candidate_type']} candidate requires review before fact promotion.",
            "relative_path": row["ocr_text_relative_path"],
            "review_status": "pending",
        })
    for row in ocr_financial_fact_candidates:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "OCR_FACT_CANDIDATE_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['fact_candidate_id']} {row['candidate_metric']} amount candidate requires human/cross review before fact promotion.",
            "relative_path": row["ocr_text_relative_path"],
            "review_status": "pending",
        })
    for row in chat_text_candidates:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "CHAT_TEXT_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['chat_text_candidate_id']} chat text is indexed; human review is required before promoting any amount.",
            "relative_path": f"{row['source_csv_relative_path']}:{row['source_row_number']}",
            "review_status": "pending",
        })
    for row in chat_value_candidates:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["evidence_id"],
            "task_type": "CHAT_VALUE_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['value_candidate_id']} {row['candidate_type']} candidate requires review before fact promotion.",
            "relative_path": f"{row['source_csv_relative_path']}:{row['source_row_number']}",
            "review_status": "pending",
        })
    for row in chat_evidence_links:
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["linked_evidence_id"],
            "task_type": "CHAT_EVIDENCE_LINK_PENDING_REVIEW",
            "severity": "blocking_for_financial_fact",
            "reason": f"{row['chat_evidence_link_id']} links chat candidate to source evidence; cross-review is required before fact promotion.",
            "relative_path": row["linked_relative_path"] or f"{row['manifest_relative_path']}:{row['manifest_row_number']}",
            "review_status": "pending",
        })
    for row in attachment_reconciliation_rows:
        if not row["reconciliation_status"].endswith("_blocking"):
            continue
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["linked_evidence_id"],
            "task_type": "ATTACHMENT_EVIDENCE_RECONCILIATION_FAIL",
            "severity": "blocking_for_evidence_integrity",
            "reason": f"{row['attachment_reconciliation_id']} {row['reconciliation_status']} requires source/evidence review before fact promotion.",
            "relative_path": row["manifest_output_path"] or f"{row['manifest_relative_path']}:{row['manifest_row_number']}",
            "review_status": "pending",
        })
    for row in cashflow_validation_rows:
        if row["validation_status"] != "FAIL":
            continue
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": row["source_evidence_id"],
            "task_type": "BALANCE_CONTINUITY_GAP",
            "severity": "blocking_for_management_conclusion",
            "reason": f"{row['validation_id']} continuity_diff={row['continuity_diff']} requires review; do not auto-correct.",
            "relative_path": row["ledger_id"],
            "review_status": "pending",
        })
    for row in workbook_quality_rows:
        if row["management_blocking"] != "true":
            continue
        exception_tasks.append({
            "task_id": f"EX-{manifest['run_id']}-{len(exception_tasks) + 1:05d}",
            "evidence_id": "",
            "task_type": "WORKBOOK_QUALITY_GATE_FAIL",
            "severity": "blocking_for_management_conclusion",
            "reason": f"{row['check_id']} failed: {row['details']}",
            "relative_path": workbook_path.name,
            "review_status": "pending",
        })
    write_csv(
        run_dir / "exception_tasks.csv",
        ["task_id", "evidence_id", "task_type", "severity", "reason", "relative_path", "review_status"],
        exception_tasks,
    )

    workbook_quality_by_id = {row["check_id"]: row for row in workbook_quality_rows}
    cross_review = {
        "run_id": manifest["run_id"],
        "management_conclusion_allowed": False,
        "generated_financial_amount_count": 0,
        "screenshot_ocr_coverage_count": manifest["screenshot_ocr_coverage_count"],
        "screenshot_ocr_ready_count": manifest["screenshot_ocr_ready_count"],
        "screenshot_ocr_missing_count": manifest["screenshot_ocr_missing_count"],
        "ocr_text_candidate_count": len(ocr_text_candidates),
        "ocr_value_candidate_count": len(ocr_value_candidates),
        "ocr_financial_fact_candidate_count": len(ocr_financial_fact_candidates),
        "ocr_fact_cross_review_group_count": manifest["ocr_fact_cross_review_group_count"],
        "ocr_fact_owner_review_batch_count": manifest["ocr_fact_owner_review_batch_count"],
        "ocr_fact_owner_review_batch_blocking_count": manifest["ocr_fact_owner_review_batch_blocking_count"],
        "ocr_fact_evidence_review_queue_count": manifest["ocr_fact_evidence_review_queue_count"],
        "ocr_fact_evidence_review_queue_blocking_count": manifest["ocr_fact_evidence_review_queue_blocking_count"],
        "ocr_fact_candidate_owner_worklist_count": manifest["ocr_fact_candidate_owner_worklist_count"],
        "ocr_fact_candidate_owner_worklist_ready_count": manifest["ocr_fact_candidate_owner_worklist_ready_count"],
        "ocr_fact_candidate_owner_worklist_blocking_count": manifest["ocr_fact_candidate_owner_worklist_blocking_count"],
        "ocr_fact_candidate_owner_decision_template_count": manifest["ocr_fact_candidate_owner_decision_template_count"],
        "ocr_fact_candidate_owner_decision_preview_count": manifest["ocr_fact_candidate_owner_decision_preview_count"],
        "ocr_fact_candidate_owner_decision_preview_ready_count": manifest["ocr_fact_candidate_owner_decision_preview_ready_count"],
        "ocr_fact_candidate_owner_decision_preview_blocking_count": manifest["ocr_fact_candidate_owner_decision_preview_blocking_count"],
        "ocr_fact_candidate_owner_decision_progress_summary_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_count"],
        "ocr_fact_candidate_owner_decision_progress_summary_candidate_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_candidate_count"],
        "ocr_fact_candidate_owner_decision_progress_summary_ready_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_ready_count"],
        "ocr_fact_candidate_owner_decision_progress_summary_blocking_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_blocking_count"],
        "ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count"],
        "ocr_fact_candidate_owner_authorization_update_draft_count": manifest["ocr_fact_candidate_owner_authorization_update_draft_count"],
        "ocr_fact_candidate_owner_authorization_update_preview_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_count"],
        "ocr_fact_candidate_owner_authorization_update_preview_ready_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_ready_count"],
        "ocr_fact_candidate_owner_authorization_update_preview_blocking_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_blocking_count"],
        "ocr_fact_ledger_staging_preview_count": manifest["ocr_fact_ledger_staging_preview_count"],
        "ocr_fact_ledger_staging_preview_ready_count": manifest["ocr_fact_ledger_staging_preview_ready_count"],
        "ocr_fact_ledger_staging_preview_blocked_count": manifest["ocr_fact_ledger_staging_preview_blocked_count"],
        "ocr_fact_controlled_ledger_row_preview_count": manifest["ocr_fact_controlled_ledger_row_preview_count"],
        "ocr_fact_controlled_ledger_row_preview_ready_count": manifest["ocr_fact_controlled_ledger_row_preview_ready_count"],
        "ocr_fact_controlled_ledger_row_preview_blocking_count": manifest["ocr_fact_controlled_ledger_row_preview_blocking_count"],
        "ocr_fact_controlled_ledger_apply_gate_count": manifest["ocr_fact_controlled_ledger_apply_gate_count"],
        "ocr_fact_controlled_ledger_apply_gate_ready_count": manifest["ocr_fact_controlled_ledger_apply_gate_ready_count"],
        "ocr_fact_controlled_ledger_apply_gate_blocking_count": manifest["ocr_fact_controlled_ledger_apply_gate_blocking_count"],
        "ocr_fact_controlled_ledger_apply_gate_planned_apply_count": manifest["ocr_fact_controlled_ledger_apply_gate_planned_apply_count"],
        "ocr_fact_controlled_ledger_apply_gate_write_allowed_count": manifest["ocr_fact_controlled_ledger_apply_gate_write_allowed_count"],
        "ocr_fact_owner_decision_correction_queue_count": manifest["ocr_fact_owner_decision_correction_queue_count"],
        "ocr_fact_owner_decision_correction_queue_blocking_count": manifest["ocr_fact_owner_decision_correction_queue_blocking_count"],
        "ocr_fact_owner_decision_correction_queue_write_allowed_count": manifest["ocr_fact_owner_decision_correction_queue_write_allowed_count"],
        "ocr_fact_owner_decision_correction_evidence_packet_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_count"],
        "ocr_fact_owner_decision_correction_evidence_packet_ready_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_ready_count"],
        "ocr_fact_owner_decision_correction_evidence_packet_blocking_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_blocking_count"],
        "ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count"],
        "ocr_fact_owner_decision_correction_ocr_line_context_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_count"],
        "ocr_fact_owner_decision_correction_ocr_line_context_ready_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"],
        "ocr_fact_owner_decision_correction_ocr_line_context_blocking_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_blocking_count"],
        "ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count"],
        "ocr_fact_owner_decision_correction_chat_context_count": manifest["ocr_fact_owner_decision_correction_chat_context_count"],
        "ocr_fact_owner_decision_correction_chat_context_ready_count": manifest["ocr_fact_owner_decision_correction_chat_context_ready_count"],
        "ocr_fact_owner_decision_correction_chat_context_blocking_count": manifest["ocr_fact_owner_decision_correction_chat_context_blocking_count"],
        "ocr_fact_owner_decision_correction_chat_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_chat_context_write_allowed_count"],
        "ocr_fact_owner_decision_correction_chat_neighbor_context_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_count"],
        "ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"],
        "ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count"],
        "ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count"],
        "ocr_fact_owner_decision_correction_owner_review_packet_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_count"],
        "ocr_fact_owner_decision_correction_owner_review_packet_ready_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"],
        "ocr_fact_owner_decision_correction_owner_review_packet_blocking_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_blocking_count"],
        "ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count"],
        "ocr_fact_owner_decision_correction_manifest_readiness_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_count"],
        "ocr_fact_owner_decision_correction_manifest_readiness_ready_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"],
        "ocr_fact_owner_decision_correction_manifest_readiness_blocking_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_blocking_count"],
        "ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count"],
        "ocr_fact_owner_decision_correction_draft_count": manifest["ocr_fact_owner_decision_correction_draft_count"],
        "ocr_fact_owner_decision_correction_draft_write_allowed_count": manifest["ocr_fact_owner_decision_correction_draft_write_allowed_count"],
        "ocr_fact_owner_decision_correction_apply_preview_count": manifest["ocr_fact_owner_decision_correction_apply_preview_count"],
        "ocr_fact_owner_decision_correction_apply_preview_ready_count": manifest["ocr_fact_owner_decision_correction_apply_preview_ready_count"],
        "ocr_fact_owner_decision_correction_apply_preview_blocking_count": manifest["ocr_fact_owner_decision_correction_apply_preview_blocking_count"],
        "ocr_fact_owner_decision_correction_apply_preview_write_allowed_count": manifest["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"],
        "ocr_fact_owner_decision_correction_roundtrip_audit_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_count"],
        "ocr_fact_owner_decision_correction_roundtrip_audit_ready_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"],
        "ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count"],
        "ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count"],
        "ocr_fact_review_apply_gate_count": manifest["ocr_fact_review_apply_gate_count"],
        "ocr_fact_review_authorization_present_count": manifest["ocr_fact_review_authorization_present_count"],
        "ocr_fact_review_authorization_valid_count": manifest["ocr_fact_review_authorization_valid_count"],
        "ocr_fact_review_authorization_template_count": manifest["ocr_fact_review_authorization_template_count"],
        "ocr_fact_review_authorization_template_authorized_count": manifest["ocr_fact_review_authorization_template_authorized_count"],
        "ocr_fact_review_authorization_preview_count": manifest["ocr_fact_review_authorization_preview_count"],
        "ocr_fact_review_authorization_preview_ready_count": manifest["ocr_fact_review_authorization_preview_ready_count"],
        "ocr_fact_review_authorization_preview_blocked_count": manifest["ocr_fact_review_authorization_preview_blocked_count"],
        "chat_text_candidate_count": len(chat_text_candidates),
        "chat_value_candidate_count": len(chat_value_candidates),
        "chat_evidence_link_count": len(chat_evidence_links),
        "chat_evidence_linked_count": manifest["chat_evidence_linked_count"],
        "attachment_reconciliation_count": len(attachment_reconciliation_rows),
        "attachment_reconciliation_linked_count": manifest["attachment_reconciliation_linked_count"],
        "attachment_reconciliation_blocking_count": manifest["attachment_reconciliation_blocking_count"],
        "attachment_remediation_count": len(attachment_remediation_rows),
        "attachment_remediation_open_count": manifest["attachment_remediation_open_count"],
        "attachment_repair_source_locator_count": manifest["attachment_repair_source_locator_count"],
        "attachment_repair_source_locator_candidate_count": manifest["attachment_repair_source_locator_candidate_count"],
        "attachment_repair_source_locator_apply_allowed_count": manifest["attachment_repair_source_locator_apply_allowed_count"],
        "attachment_remediation_dry_run_count": len(attachment_dry_run_rows),
        "attachment_remediation_apply_allowed_count": manifest["attachment_remediation_apply_allowed_count"],
        "attachment_repair_plan_count": len(attachment_repair_plan_rows),
        "attachment_repair_plan_open_count": manifest["attachment_repair_plan_open_count"],
        "attachment_repair_apply_gate_count": manifest["attachment_repair_apply_gate_count"],
        "attachment_repair_apply_blocked_count": manifest["attachment_repair_apply_blocked_count"],
        "attachment_repair_authorization_present_count": manifest["attachment_repair_authorization_present_count"],
        "attachment_repair_authorization_valid_count": manifest["attachment_repair_authorization_valid_count"],
        "attachment_repair_authorization_template_count": manifest["attachment_repair_authorization_template_count"],
        "attachment_repair_authorization_template_authorized_count": manifest["attachment_repair_authorization_template_authorized_count"],
        "attachment_repair_authorization_preview_count": manifest["attachment_repair_authorization_preview_count"],
        "attachment_repair_authorization_preview_ready_count": manifest["attachment_repair_authorization_preview_ready_count"],
        "attachment_repair_authorization_preview_blocked_count": manifest["attachment_repair_authorization_preview_blocked_count"],
        "attachment_repair_apply_allowed_count": manifest["attachment_repair_apply_allowed_count"],
        "structured_financial_fact_count": len(structured["fund_rows"]),
        "metadata_signal_count": len(metadata_signals),
        "forecast_row_count": len(funding_forecast_rows),
        "cashflow_validation_row_count": len(cashflow_validation_rows),
        "balance_continuity_fail_count": balance_continuity_fail_count,
        "internal_transfer_excluded_count": internal_transfer_excluded_count,
        "workbook_quality_check_count": len(workbook_quality_rows),
        "workbook_quality_blocking_count": workbook_quality_blocking_count,
        "homepage_chart_size_status": workbook_quality_by_id.get("WQ-HOMEPAGE-CHART-SIZE", {}).get("status", ""),
        "homepage_chart_semantics_status": workbook_quality_by_id.get("WQ-HOMEPAGE-CHART-SEMANTICS", {}).get("status", ""),
        "visible_sensitive_text_status": workbook_quality_by_id.get("WQ-VISIBLE-SENSITIVE-TEXT", {}).get("status", ""),
        "automation_readiness_count": len(automation_readiness_rows),
        "automation_readiness_ready_count": automation_readiness_ready_count,
        "automation_readiness_blocking_count": automation_readiness_blocking_count,
        "automation_readiness_status": automation_readiness_rows[0]["status"] if automation_readiness_rows else "CODEX_AUTOMATION_UNKNOWN",
        "automation_readiness_rrule": automation_readiness_rows[0]["rrule"] if automation_readiness_rows else "",
        "excel_workbook_generated": True,
        "workbook": workbook_path.name,
        "source_file_count": manifest["file_count"],
        "evidence_count": len(evidence),
        "status": manifest["status"],
        "reason": "No amount was generated or inferred before OCR/table extraction and review gates.",
    }
    evidence_cross_review_resolution_plan_rows = build_evidence_cross_review_resolution_plan_rows(
        manifest,
        cross_review,
    )
    evidence_cross_review_resolution_plan_blocker_count = sum(
        int(row["blocker_count"]) for row in evidence_cross_review_resolution_plan_rows
    )
    manifest["evidence_cross_review_resolution_plan_count"] = len(evidence_cross_review_resolution_plan_rows)
    manifest["evidence_cross_review_resolution_plan_blocker_count"] = (
        evidence_cross_review_resolution_plan_blocker_count
    )
    cross_review["evidence_cross_review_resolution_plan_count"] = len(evidence_cross_review_resolution_plan_rows)
    cross_review["evidence_cross_review_resolution_plan_blocker_count"] = (
        evidence_cross_review_resolution_plan_blocker_count
    )
    write_csv(run_dir / "evidence_cross_review_resolution_plan.csv", [
        "evidence_resolution_plan_id",
        "evidence_area",
        "source_artifact",
        "blocker_count",
        "ready_count",
        "resolution_status",
        "priority",
        "required_owner_action",
        "authorization_manifest_relative_path",
        "automation_safe",
        "source_mutation_allowed",
        "fact_promotion_allowed",
        "fund_ledger_write_allowed",
        "management_conclusion_allowed",
        "next_action",
    ], evidence_cross_review_resolution_plan_rows)
    goal_completion_audit_rows = build_goal_completion_audit_rows(cross_review)
    goal_completion_blocking_count = sum(1 for row in goal_completion_audit_rows if row["blocking"] == "true")
    manifest["goal_completion_audit_check_count"] = len(goal_completion_audit_rows)
    manifest["goal_completion_blocking_count"] = goal_completion_blocking_count
    cross_review["goal_completion_audit_check_count"] = len(goal_completion_audit_rows)
    cross_review["goal_completion_blocking_count"] = goal_completion_blocking_count
    write_csv(run_dir / "goal_completion_audit.csv", [
        "requirement_id",
        "requirement",
        "audit_status",
        "evidence",
        "blocking",
        "next_action",
    ], goal_completion_audit_rows)
    fact_promotion_review_packet_rows = build_fact_promotion_review_packet_rows(
        manifest,
        structured,
        screenshot_ocr_coverage_rows,
        ocr_fact_ledger_staging_preview_rows,
        chat_value_candidates,
        attachment_reconciliation_rows,
        workbook_quality_rows,
        goal_completion_audit_rows,
    )
    fact_promotion_review_blocking_count = sum(1 for row in fact_promotion_review_packet_rows if row["blocked_count"] != "0")
    fact_promotion_owner_review_batch_rows = build_fact_promotion_owner_review_batch_rows(
        manifest,
        fact_promotion_review_packet_rows,
    )
    fact_promotion_owner_review_batch_authorization_required_count = sum(
        1 for row in fact_promotion_owner_review_batch_rows
        if row["owner_authorization_required"] == "true"
    )
    fact_promotion_owner_review_batch_blocking_count = sum(
        1 for row in fact_promotion_owner_review_batch_rows
        if row["blocked_count"] != "0"
    )
    fact_promotion_authorization_template = build_fact_promotion_authorization_template(
        manifest,
        fact_promotion_review_packet_rows,
    )
    fact_promotion_authorization_template_authorized_count = sum(
        1 for row in fact_promotion_authorization_template["review_packet_authorizations"]
        if row["authorized"] is True
    )
    fact_promotion_authorization_preview_rows = build_fact_promotion_authorization_preview(
        manifest,
        repo_root,
        fact_promotion_review_packet_rows,
    )
    fact_promotion_authorization_valid_count = sum(
        1 for row in fact_promotion_authorization_preview_rows
        if row["authorization_validation_status"] == "valid_manifest_validation_only"
    )
    fact_promotion_authorization_preview_ready_count = sum(
        1 for row in fact_promotion_authorization_preview_rows
        if row["preview_status"] == "ready_for_owner_review_no_fact_promotion"
    )
    fact_promotion_authorization_preview_blocked_count = sum(
        1 for row in fact_promotion_authorization_preview_rows
        if row["preview_status"].startswith("blocked_")
    )
    fact_promotion_execution_gate_rows = build_fact_promotion_execution_gate(
        manifest,
        fact_promotion_review_packet_rows,
        fact_promotion_authorization_preview_rows,
    )
    fact_promotion_execution_gate_ready_count = sum(
        1 for row in fact_promotion_execution_gate_rows
        if row["execution_gate_status"] == "ready_for_controlled_fact_promotion_execution"
    )
    fact_promotion_execution_gate_blocked_count = sum(
        1 for row in fact_promotion_execution_gate_rows
        if row["execution_gate_status"].startswith("blocked_")
    )
    fact_promotion_execution_dry_run_rows = build_fact_promotion_execution_dry_run_rows(
        manifest,
        fact_promotion_execution_gate_rows,
    )
    fact_promotion_execution_dry_run_ready_count = sum(
        1 for row in fact_promotion_execution_dry_run_rows
        if row["dry_run_status"] == "ready_for_controlled_execution_preview_no_write"
    )
    fact_promotion_execution_dry_run_impact_count = sum(
        int(row["dry_run_impact_count"]) for row in fact_promotion_execution_dry_run_rows
    )
    fact_promotion_execution_plan_rows = build_fact_promotion_execution_plan_rows(
        manifest,
        fact_promotion_execution_dry_run_rows,
    )
    fact_promotion_execution_plan_ready_count = sum(
        1 for row in fact_promotion_execution_plan_rows
        if row["execution_plan_status"] == "ready_for_owner_execution_authorization_no_write"
    )
    fact_promotion_execution_plan_blocked_count = sum(
        1 for row in fact_promotion_execution_plan_rows
        if row["execution_plan_status"].startswith("blocked_")
    )
    fact_promotion_execution_plan_planned_impact_count = sum(
        int(row["planned_impact_count"]) for row in fact_promotion_execution_plan_rows
    )
    fact_promotion_execution_authorization_template = build_fact_promotion_execution_authorization_template(
        manifest,
        fact_promotion_execution_plan_rows,
    )
    fact_promotion_execution_authorization_template_authorized_count = sum(
        1 for row in fact_promotion_execution_authorization_template["execution_plan_authorizations"]
        if row["authorized"] is True
    )
    fact_promotion_execution_authorization_preview_rows = build_fact_promotion_execution_authorization_preview(
        manifest,
        repo_root,
        fact_promotion_execution_plan_rows,
    )
    fact_promotion_execution_authorization_preview_ready_count = sum(
        1 for row in fact_promotion_execution_authorization_preview_rows
        if row["preview_status"] == "ready_for_controlled_execution_run_no_write"
    )
    fact_promotion_execution_authorization_preview_blocked_count = sum(
        1 for row in fact_promotion_execution_authorization_preview_rows
        if row["preview_status"].startswith("blocked_")
    )
    fact_promotion_execution_apply_gate_rows = build_fact_promotion_execution_apply_gate_rows(
        manifest,
        fact_promotion_execution_authorization_preview_rows,
    )
    fact_promotion_execution_apply_gate_ready_count = sum(
        1 for row in fact_promotion_execution_apply_gate_rows
        if row["apply_gate_status"] == "ready_for_controlled_execution_apply_no_write"
    )
    fact_promotion_execution_apply_gate_blocked_count = sum(
        1 for row in fact_promotion_execution_apply_gate_rows
        if row["apply_gate_status"].startswith("blocked_")
    )
    fact_promotion_execution_apply_gate_planned_apply_count = sum(
        int(row["planned_apply_count"]) for row in fact_promotion_execution_apply_gate_rows
    )
    fact_promotion_execution_result_rows = build_fact_promotion_execution_result_rows(
        manifest,
        fact_promotion_execution_apply_gate_rows,
        structured,
    )
    formal_fund_ledger_rows = build_formal_fund_ledger_rows(
        manifest,
        structured,
        fact_promotion_execution_result_rows,
    )
    fact_promotion_execution_result_formalized_area_count = sum(
        1 for row in fact_promotion_execution_result_rows
        if row["execution_result_status"] == "structured_csv_formal_ledger_sidecar_written"
    )
    manifest["fact_promotion_review_packet_count"] = len(fact_promotion_review_packet_rows)
    manifest["fact_promotion_review_blocking_count"] = fact_promotion_review_blocking_count
    manifest["fact_promotion_owner_review_batch_count"] = len(fact_promotion_owner_review_batch_rows)
    manifest["fact_promotion_owner_review_batch_authorization_required_count"] = (
        fact_promotion_owner_review_batch_authorization_required_count
    )
    manifest["fact_promotion_owner_review_batch_blocking_count"] = fact_promotion_owner_review_batch_blocking_count
    manifest["fact_promotion_authorization_template_count"] = len(
        fact_promotion_authorization_template["review_packet_authorizations"]
    )
    manifest["fact_promotion_authorization_template_authorized_count"] = fact_promotion_authorization_template_authorized_count
    manifest["fact_promotion_authorization_present_count"] = sum(
        1 for row in fact_promotion_authorization_preview_rows
        if row["operator_authorization_present"] == "true"
    )
    manifest["fact_promotion_authorization_valid_count"] = fact_promotion_authorization_valid_count
    manifest["fact_promotion_authorization_preview_count"] = len(fact_promotion_authorization_preview_rows)
    manifest["fact_promotion_authorization_preview_ready_count"] = fact_promotion_authorization_preview_ready_count
    manifest["fact_promotion_authorization_preview_blocked_count"] = fact_promotion_authorization_preview_blocked_count
    manifest["fact_promotion_execution_gate_count"] = len(fact_promotion_execution_gate_rows)
    manifest["fact_promotion_execution_gate_ready_count"] = fact_promotion_execution_gate_ready_count
    manifest["fact_promotion_execution_gate_blocked_count"] = fact_promotion_execution_gate_blocked_count
    manifest["fact_promotion_execution_allowed_count"] = sum(
        1 for row in fact_promotion_execution_gate_rows
        if row["fact_promotion_execution_allowed"] == "true"
    )
    manifest["fact_promotion_execution_dry_run_count"] = len(fact_promotion_execution_dry_run_rows)
    manifest["fact_promotion_execution_dry_run_ready_count"] = fact_promotion_execution_dry_run_ready_count
    manifest["fact_promotion_execution_dry_run_impact_count"] = fact_promotion_execution_dry_run_impact_count
    manifest["fact_promotion_execution_dry_run_write_allowed_count"] = sum(
        1 for row in fact_promotion_execution_dry_run_rows
        if row["fund_ledger_write_allowed"] == "true"
    )
    manifest["fact_promotion_execution_plan_count"] = len(fact_promotion_execution_plan_rows)
    manifest["fact_promotion_execution_plan_ready_count"] = fact_promotion_execution_plan_ready_count
    manifest["fact_promotion_execution_plan_blocked_count"] = fact_promotion_execution_plan_blocked_count
    manifest["fact_promotion_execution_plan_planned_impact_count"] = (
        fact_promotion_execution_plan_planned_impact_count
    )
    manifest["fact_promotion_execution_plan_write_allowed_count"] = sum(
        1 for row in fact_promotion_execution_plan_rows
        if row["fund_ledger_write_allowed"] == "true"
    )
    manifest["fact_promotion_execution_authorization_template_count"] = len(
        fact_promotion_execution_authorization_template["execution_plan_authorizations"]
    )
    manifest["fact_promotion_execution_authorization_template_authorized_count"] = (
        fact_promotion_execution_authorization_template_authorized_count
    )
    manifest["fact_promotion_execution_authorization_present_count"] = sum(
        1 for row in fact_promotion_execution_authorization_preview_rows
        if row["operator_authorization_present"] == "true"
    )
    manifest["fact_promotion_execution_authorization_preview_count"] = len(
        fact_promotion_execution_authorization_preview_rows
    )
    manifest["fact_promotion_execution_authorization_preview_ready_count"] = (
        fact_promotion_execution_authorization_preview_ready_count
    )
    manifest["fact_promotion_execution_authorization_preview_blocked_count"] = (
        fact_promotion_execution_authorization_preview_blocked_count
    )
    manifest["fact_promotion_execution_authorization_write_allowed_count"] = sum(
        1 for row in fact_promotion_execution_authorization_preview_rows
        if row["fund_ledger_write_allowed"] == "true"
    )
    manifest["fact_promotion_execution_apply_gate_count"] = len(fact_promotion_execution_apply_gate_rows)
    manifest["fact_promotion_execution_apply_gate_ready_count"] = fact_promotion_execution_apply_gate_ready_count
    manifest["fact_promotion_execution_apply_gate_blocked_count"] = fact_promotion_execution_apply_gate_blocked_count
    manifest["fact_promotion_execution_apply_gate_planned_apply_count"] = (
        fact_promotion_execution_apply_gate_planned_apply_count
    )
    manifest["fact_promotion_execution_apply_gate_write_allowed_count"] = sum(
        1 for row in fact_promotion_execution_apply_gate_rows
        if row["fund_ledger_write_allowed"] == "true"
    )
    manifest["fact_promotion_execution_result_count"] = len(fact_promotion_execution_result_rows)
    manifest["fact_promotion_execution_result_formalized_area_count"] = (
        fact_promotion_execution_result_formalized_area_count
    )
    manifest["formal_fund_ledger_row_count"] = len(formal_fund_ledger_rows)
    cross_review["fact_promotion_review_packet_count"] = len(fact_promotion_review_packet_rows)
    cross_review["fact_promotion_review_blocking_count"] = fact_promotion_review_blocking_count
    cross_review["fact_promotion_owner_review_batch_count"] = len(fact_promotion_owner_review_batch_rows)
    cross_review["fact_promotion_owner_review_batch_authorization_required_count"] = (
        fact_promotion_owner_review_batch_authorization_required_count
    )
    cross_review["fact_promotion_owner_review_batch_blocking_count"] = fact_promotion_owner_review_batch_blocking_count
    cross_review["fact_promotion_authorization_template_count"] = manifest["fact_promotion_authorization_template_count"]
    cross_review["fact_promotion_authorization_template_authorized_count"] = fact_promotion_authorization_template_authorized_count
    cross_review["fact_promotion_authorization_present_count"] = manifest["fact_promotion_authorization_present_count"]
    cross_review["fact_promotion_authorization_valid_count"] = fact_promotion_authorization_valid_count
    cross_review["fact_promotion_authorization_preview_count"] = len(fact_promotion_authorization_preview_rows)
    cross_review["fact_promotion_authorization_preview_ready_count"] = fact_promotion_authorization_preview_ready_count
    cross_review["fact_promotion_authorization_preview_blocked_count"] = manifest["fact_promotion_authorization_preview_blocked_count"]
    cross_review["fact_promotion_execution_gate_count"] = len(fact_promotion_execution_gate_rows)
    cross_review["fact_promotion_execution_gate_ready_count"] = fact_promotion_execution_gate_ready_count
    cross_review["fact_promotion_execution_gate_blocked_count"] = manifest["fact_promotion_execution_gate_blocked_count"]
    cross_review["fact_promotion_execution_allowed_count"] = manifest["fact_promotion_execution_allowed_count"]
    cross_review["fact_promotion_execution_dry_run_count"] = manifest["fact_promotion_execution_dry_run_count"]
    cross_review["fact_promotion_execution_dry_run_ready_count"] = fact_promotion_execution_dry_run_ready_count
    cross_review["fact_promotion_execution_dry_run_impact_count"] = fact_promotion_execution_dry_run_impact_count
    cross_review["fact_promotion_execution_dry_run_write_allowed_count"] = manifest["fact_promotion_execution_dry_run_write_allowed_count"]
    cross_review["fact_promotion_execution_plan_count"] = manifest["fact_promotion_execution_plan_count"]
    cross_review["fact_promotion_execution_plan_ready_count"] = fact_promotion_execution_plan_ready_count
    cross_review["fact_promotion_execution_plan_blocked_count"] = fact_promotion_execution_plan_blocked_count
    cross_review["fact_promotion_execution_plan_planned_impact_count"] = (
        fact_promotion_execution_plan_planned_impact_count
    )
    cross_review["fact_promotion_execution_plan_write_allowed_count"] = (
        manifest["fact_promotion_execution_plan_write_allowed_count"]
    )
    cross_review["fact_promotion_execution_authorization_template_count"] = (
        manifest["fact_promotion_execution_authorization_template_count"]
    )
    cross_review["fact_promotion_execution_authorization_template_authorized_count"] = (
        fact_promotion_execution_authorization_template_authorized_count
    )
    cross_review["fact_promotion_execution_authorization_present_count"] = (
        manifest["fact_promotion_execution_authorization_present_count"]
    )
    cross_review["fact_promotion_execution_authorization_preview_count"] = (
        manifest["fact_promotion_execution_authorization_preview_count"]
    )
    cross_review["fact_promotion_execution_authorization_preview_ready_count"] = (
        fact_promotion_execution_authorization_preview_ready_count
    )
    cross_review["fact_promotion_execution_authorization_preview_blocked_count"] = (
        fact_promotion_execution_authorization_preview_blocked_count
    )
    cross_review["fact_promotion_execution_authorization_write_allowed_count"] = (
        manifest["fact_promotion_execution_authorization_write_allowed_count"]
    )
    cross_review["fact_promotion_execution_apply_gate_count"] = manifest["fact_promotion_execution_apply_gate_count"]
    cross_review["fact_promotion_execution_apply_gate_ready_count"] = fact_promotion_execution_apply_gate_ready_count
    cross_review["fact_promotion_execution_apply_gate_blocked_count"] = fact_promotion_execution_apply_gate_blocked_count
    cross_review["fact_promotion_execution_apply_gate_planned_apply_count"] = (
        fact_promotion_execution_apply_gate_planned_apply_count
    )
    cross_review["fact_promotion_execution_apply_gate_write_allowed_count"] = (
        manifest["fact_promotion_execution_apply_gate_write_allowed_count"]
    )
    cross_review["fact_promotion_execution_result_count"] = manifest["fact_promotion_execution_result_count"]
    cross_review["fact_promotion_execution_result_formalized_area_count"] = (
        manifest["fact_promotion_execution_result_formalized_area_count"]
    )
    cross_review["formal_fund_ledger_row_count"] = manifest["formal_fund_ledger_row_count"]
    management_conclusion_authorization_template = build_management_conclusion_release_authorization_template(
        manifest,
        cross_review,
    )
    management_conclusion_authorization_preview_rows = build_management_conclusion_release_authorization_preview(
        manifest,
        repo_root,
        cross_review,
    )
    management_conclusion_release_precondition_blocking_count = int(
        management_conclusion_authorization_preview_rows[0]["pre_release_blocking_count"]
    )
    management_conclusion_authorization_preview_ready_count = sum(
        1 for row in management_conclusion_authorization_preview_rows
        if row["preview_status"] == "ready_for_management_conclusion_release_review_no_auto_conclusion"
    )
    management_conclusion_authorization_preview_blocked_count = (
        len(management_conclusion_authorization_preview_rows)
        - management_conclusion_authorization_preview_ready_count
    )
    manifest["management_conclusion_release_authorization_template_count"] = len(
        management_conclusion_authorization_template["release_authorizations"]
    )
    manifest["management_conclusion_release_authorization_present_count"] = sum(
        1 for row in management_conclusion_authorization_preview_rows
        if row["operator_authorization_present"] == "true"
    )
    manifest["management_conclusion_release_authorization_valid_count"] = sum(
        1 for row in management_conclusion_authorization_preview_rows
        if row["authorization_validation_status"] == "valid_release_authorization_manifest"
    )
    manifest["management_conclusion_release_authorization_preview_count"] = len(
        management_conclusion_authorization_preview_rows
    )
    manifest["management_conclusion_release_authorization_preview_ready_count"] = (
        management_conclusion_authorization_preview_ready_count
    )
    manifest["management_conclusion_release_authorization_preview_blocked_count"] = (
        management_conclusion_authorization_preview_blocked_count
    )
    manifest["management_conclusion_release_precondition_blocking_count"] = (
        management_conclusion_release_precondition_blocking_count
    )
    cross_review["management_conclusion_release_authorization_template_count"] = (
        manifest["management_conclusion_release_authorization_template_count"]
    )
    cross_review["management_conclusion_release_authorization_present_count"] = (
        manifest["management_conclusion_release_authorization_present_count"]
    )
    cross_review["management_conclusion_release_authorization_valid_count"] = (
        manifest["management_conclusion_release_authorization_valid_count"]
    )
    cross_review["management_conclusion_release_authorization_preview_count"] = (
        manifest["management_conclusion_release_authorization_preview_count"]
    )
    cross_review["management_conclusion_release_authorization_preview_ready_count"] = (
        management_conclusion_authorization_preview_ready_count
    )
    cross_review["management_conclusion_release_authorization_preview_blocked_count"] = (
        management_conclusion_authorization_preview_blocked_count
    )
    cross_review["management_conclusion_release_precondition_blocking_count"] = (
        management_conclusion_release_precondition_blocking_count
    )
    cross_review["management_conclusion_release_authorization_validation_status"] = (
        management_conclusion_authorization_preview_rows[0]["authorization_validation_status"]
    )
    cross_review["management_conclusion_release_authorization_preview_status"] = (
        management_conclusion_authorization_preview_rows[0]["preview_status"]
    )
    management_conclusion_gate_rows = build_management_conclusion_gate_rows(cross_review)
    management_conclusion_gate_ready_count = sum(1 for row in management_conclusion_gate_rows if row["gate_status"] == "ready")
    owner_action_queue_rows = build_owner_action_queue_rows(management_conclusion_gate_rows)
    owner_action_queue_blocking_count = sum(1 for row in owner_action_queue_rows if row["blocking"] == "true")
    owner_action_queue_automation_safe_count = sum(1 for row in owner_action_queue_rows if row["automation_safe"] == "true")
    manifest["management_conclusion_gate_count"] = len(management_conclusion_gate_rows)
    manifest["management_conclusion_gate_ready_count"] = management_conclusion_gate_ready_count
    manifest["management_conclusion_gate_blocked_count"] = len(management_conclusion_gate_rows) - management_conclusion_gate_ready_count
    manifest["owner_action_queue_count"] = len(owner_action_queue_rows)
    manifest["owner_action_queue_blocking_count"] = owner_action_queue_blocking_count
    manifest["owner_action_queue_automation_safe_count"] = owner_action_queue_automation_safe_count
    cross_review["management_conclusion_gate_count"] = len(management_conclusion_gate_rows)
    cross_review["management_conclusion_gate_ready_count"] = management_conclusion_gate_ready_count
    cross_review["management_conclusion_gate_blocked_count"] = manifest["management_conclusion_gate_blocked_count"]
    cross_review["owner_action_queue_count"] = len(owner_action_queue_rows)
    cross_review["owner_action_queue_blocking_count"] = owner_action_queue_blocking_count
    cross_review["owner_action_queue_automation_safe_count"] = owner_action_queue_automation_safe_count
    write_csv(run_dir / "fact_promotion_review_packet.csv", [
        "review_packet_id",
        "review_area",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "review_status",
        "source_artifact",
        "authorization_required",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "next_action",
    ], fact_promotion_review_packet_rows)
    write_csv(run_dir / "fact_promotion_owner_review_batch.csv", [
        "owner_review_batch_id",
        "review_packet_id",
        "review_area",
        "source_artifact",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "priority",
        "owner_review_status",
        "owner_authorization_required",
        "authorization_manifest_relative_path",
        "authorization_scope",
        "financial_fact_promotion_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "batch_reason",
        "recommended_owner_action",
    ], fact_promotion_owner_review_batch_rows)
    (run_dir / "fact_promotion_authorization_template.json").write_text(
        json.dumps(fact_promotion_authorization_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "fact_promotion_authorization_preview.csv", [
        "authorization_preview_id",
        "review_packet_id",
        "review_area",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "operator_authorization_required",
        "authorization_manifest_relative_path",
        "operator_authorization_present",
        "authorization_validation_status",
        "authorization_ticket",
        "authorized_by",
        "authorized_at",
        "authorization_scope",
        "preview_status",
        "financial_fact_promotion_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "preview_reason",
        "source_artifact",
        "review_status",
    ], fact_promotion_authorization_preview_rows)
    write_csv(run_dir / "fact_promotion_execution_gate.csv", [
        "execution_gate_id",
        "review_packet_id",
        "review_area",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "authorization_validation_status",
        "authorization_preview_status",
        "execution_gate_status",
        "fact_promotion_execution_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "gate_reason",
        "source_artifact",
        "review_status",
    ], fact_promotion_execution_gate_rows)
    write_csv(run_dir / "fact_promotion_execution_dry_run.csv", [
        "dry_run_id",
        "execution_gate_id",
        "review_packet_id",
        "review_area",
        "source_artifact",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "execution_gate_status",
        "dry_run_status",
        "dry_run_impact_count",
        "fact_promotion_execution_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "dry_run_reason",
    ], fact_promotion_execution_dry_run_rows)
    write_csv(run_dir / "fact_promotion_execution_plan.csv", [
        "execution_plan_id",
        "dry_run_id",
        "execution_gate_id",
        "review_packet_id",
        "review_area",
        "source_artifact",
        "candidate_count",
        "ready_count",
        "blocked_count",
        "dry_run_status",
        "dry_run_impact_count",
        "execution_plan_status",
        "required_authorization_scope",
        "required_owner_action",
        "planned_impact_count",
        "source_mutation_allowed",
        "fact_promotion_execution_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "plan_reason",
    ], fact_promotion_execution_plan_rows)
    (run_dir / "fact_promotion_execution_authorization_template.json").write_text(
        json.dumps(fact_promotion_execution_authorization_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "fact_promotion_execution_authorization_preview.csv", [
        "execution_authorization_preview_id",
        "execution_plan_id",
        "dry_run_id",
        "execution_gate_id",
        "review_packet_id",
        "review_area",
        "source_artifact",
        "planned_impact_count",
        "execution_plan_status",
        "execution_authorization_required",
        "authorization_manifest_relative_path",
        "operator_authorization_present",
        "authorization_validation_status",
        "authorization_ticket",
        "authorized_by",
        "authorized_at",
        "authorization_scope",
        "preview_status",
        "source_mutation_allowed",
        "fact_promotion_execution_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "preview_reason",
        "review_status",
    ], fact_promotion_execution_authorization_preview_rows)
    write_csv(run_dir / "fact_promotion_execution_apply_gate.csv", [
        "execution_apply_gate_id",
        "execution_authorization_preview_id",
        "execution_plan_id",
        "dry_run_id",
        "execution_gate_id",
        "review_packet_id",
        "review_area",
        "source_artifact",
        "planned_impact_count",
        "authorization_validation_status",
        "authorization_preview_status",
        "apply_gate_status",
        "planned_apply_count",
        "source_mutation_allowed",
        "fact_promotion_execution_allowed",
        "fund_ledger_write_allowed",
        "financial_fact_promoted",
        "management_conclusion_allowed",
        "gate_reason",
        "review_status",
    ], fact_promotion_execution_apply_gate_rows)
    write_csv(run_dir / "fact_promotion_execution_result.csv", [
        "execution_result_id",
        "execution_apply_gate_id",
        "review_area",
        "source_artifact",
        "apply_gate_status",
        "execution_result_status",
        "planned_apply_count",
        "formal_ledger_artifact",
        "formal_ledger_row_count",
        "source_mutation_allowed",
        "fund_ledger_mutation_allowed",
        "management_conclusion_allowed",
        "result_reason",
        "review_status",
    ], fact_promotion_execution_result_rows)
    write_csv(run_dir / "formal_fund_ledger.csv", [
        "formal_ledger_id",
        "source_ledger_id",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "inflow",
        "outflow",
        "ending_balance",
        "flow_type",
        "source_evidence_id",
        "source_row_number",
        "formal_fact_source",
        "formal_write_status",
        "source_mutation_allowed",
        "fund_ledger_mutation_allowed",
        "management_conclusion_allowed",
        "formal_review_status",
    ], formal_fund_ledger_rows)
    (run_dir / "management_conclusion_authorization_template.json").write_text(
        json.dumps(management_conclusion_authorization_template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "management_conclusion_authorization_preview.csv", [
        "management_conclusion_release_preview_id",
        "release_authorization_id",
        "pre_release_gate_count",
        "pre_release_ready_count",
        "pre_release_blocking_count",
        "blocking_gate_ids",
        "authorization_manifest_relative_path",
        "operator_authorization_present",
        "authorization_validation_status",
        "authorization_ticket",
        "authorized_by",
        "authorized_at",
        "authorization_scope",
        "preview_status",
        "management_conclusion_allowed",
        "preview_reason",
        "review_status",
    ], management_conclusion_authorization_preview_rows)
    write_csv(run_dir / "management_conclusion_gate.csv", [
        "management_gate_id",
        "gate_area",
        "gate_status",
        "evidence",
        "blocking",
        "management_conclusion_allowed",
        "next_action",
    ], management_conclusion_gate_rows)
    write_csv(run_dir / "owner_action_queue.csv", [
        "owner_action_id",
        "source_gate",
        "source_gate_status",
        "action_type",
        "priority",
        "action_status",
        "blocking",
        "automation_safe",
        "requires_owner_authorization",
        "source_mutation_allowed",
        "fact_promotion_allowed",
        "fund_ledger_write_allowed",
        "management_conclusion_allowed",
        "evidence",
        "recommended_next_step",
    ], owner_action_queue_rows)
    (run_dir / "cross_review.json").write_text(json.dumps(cross_review, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "audit_log.json").write_text(
        json.dumps([
            {
                "event": "real_sources_indexed",
                "run_id": manifest["run_id"],
                "file_count": manifest["file_count"],
            },
            {
                "event": "no_hallucination_outputs_written",
                "generated_financial_amount_count": 0,
                "screenshot_ocr_coverage_count": manifest["screenshot_ocr_coverage_count"],
                "screenshot_ocr_ready_count": manifest["screenshot_ocr_ready_count"],
                "screenshot_ocr_missing_count": manifest["screenshot_ocr_missing_count"],
                "ocr_text_candidate_count": len(ocr_text_candidates),
                "ocr_value_candidate_count": len(ocr_value_candidates),
                "ocr_financial_fact_candidate_count": len(ocr_financial_fact_candidates),
                "ocr_fact_cross_review_group_count": manifest["ocr_fact_cross_review_group_count"],
                "ocr_fact_owner_review_batch_count": manifest["ocr_fact_owner_review_batch_count"],
                "ocr_fact_owner_review_batch_blocking_count": manifest["ocr_fact_owner_review_batch_blocking_count"],
                "ocr_fact_evidence_review_queue_count": manifest["ocr_fact_evidence_review_queue_count"],
                "ocr_fact_evidence_review_queue_blocking_count": manifest["ocr_fact_evidence_review_queue_blocking_count"],
                "ocr_fact_candidate_owner_worklist_count": manifest["ocr_fact_candidate_owner_worklist_count"],
                "ocr_fact_candidate_owner_worklist_ready_count": manifest["ocr_fact_candidate_owner_worklist_ready_count"],
                "ocr_fact_candidate_owner_worklist_blocking_count": manifest["ocr_fact_candidate_owner_worklist_blocking_count"],
                "ocr_fact_candidate_owner_decision_template_count": manifest["ocr_fact_candidate_owner_decision_template_count"],
                "ocr_fact_candidate_owner_decision_preview_count": manifest["ocr_fact_candidate_owner_decision_preview_count"],
                "ocr_fact_candidate_owner_decision_preview_ready_count": manifest["ocr_fact_candidate_owner_decision_preview_ready_count"],
                "ocr_fact_candidate_owner_decision_preview_blocking_count": manifest["ocr_fact_candidate_owner_decision_preview_blocking_count"],
                "ocr_fact_candidate_owner_decision_progress_summary_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_count"],
                "ocr_fact_candidate_owner_decision_progress_summary_candidate_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_candidate_count"],
                "ocr_fact_candidate_owner_decision_progress_summary_ready_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_ready_count"],
                "ocr_fact_candidate_owner_decision_progress_summary_blocking_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_blocking_count"],
                "ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count": manifest["ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count"],
                "ocr_fact_candidate_owner_authorization_update_draft_count": manifest["ocr_fact_candidate_owner_authorization_update_draft_count"],
                "ocr_fact_candidate_owner_authorization_update_preview_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_count"],
                "ocr_fact_candidate_owner_authorization_update_preview_ready_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_ready_count"],
                "ocr_fact_candidate_owner_authorization_update_preview_blocking_count": manifest["ocr_fact_candidate_owner_authorization_update_preview_blocking_count"],
                "ocr_fact_ledger_staging_preview_count": manifest["ocr_fact_ledger_staging_preview_count"],
                "ocr_fact_ledger_staging_preview_ready_count": manifest["ocr_fact_ledger_staging_preview_ready_count"],
                "ocr_fact_ledger_staging_preview_blocked_count": manifest["ocr_fact_ledger_staging_preview_blocked_count"],
                "ocr_fact_controlled_ledger_row_preview_count": manifest["ocr_fact_controlled_ledger_row_preview_count"],
                "ocr_fact_controlled_ledger_row_preview_ready_count": manifest["ocr_fact_controlled_ledger_row_preview_ready_count"],
                "ocr_fact_controlled_ledger_row_preview_blocking_count": manifest["ocr_fact_controlled_ledger_row_preview_blocking_count"],
                "ocr_fact_controlled_ledger_apply_gate_count": manifest["ocr_fact_controlled_ledger_apply_gate_count"],
                "ocr_fact_controlled_ledger_apply_gate_ready_count": manifest["ocr_fact_controlled_ledger_apply_gate_ready_count"],
                "ocr_fact_controlled_ledger_apply_gate_blocking_count": manifest["ocr_fact_controlled_ledger_apply_gate_blocking_count"],
                "ocr_fact_controlled_ledger_apply_gate_planned_apply_count": manifest["ocr_fact_controlled_ledger_apply_gate_planned_apply_count"],
                "ocr_fact_controlled_ledger_apply_gate_write_allowed_count": manifest["ocr_fact_controlled_ledger_apply_gate_write_allowed_count"],
                "ocr_fact_owner_decision_correction_queue_count": manifest["ocr_fact_owner_decision_correction_queue_count"],
                "ocr_fact_owner_decision_correction_queue_blocking_count": manifest["ocr_fact_owner_decision_correction_queue_blocking_count"],
                "ocr_fact_owner_decision_correction_queue_write_allowed_count": manifest["ocr_fact_owner_decision_correction_queue_write_allowed_count"],
                "ocr_fact_owner_decision_correction_evidence_packet_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_count"],
                "ocr_fact_owner_decision_correction_evidence_packet_ready_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_ready_count"],
                "ocr_fact_owner_decision_correction_evidence_packet_blocking_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_blocking_count"],
                "ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count": manifest["ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count"],
                "ocr_fact_owner_decision_correction_ocr_line_context_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_count"],
                "ocr_fact_owner_decision_correction_ocr_line_context_ready_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"],
                "ocr_fact_owner_decision_correction_ocr_line_context_blocking_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_blocking_count"],
                "ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count"],
                "ocr_fact_owner_decision_correction_chat_context_count": manifest["ocr_fact_owner_decision_correction_chat_context_count"],
                "ocr_fact_owner_decision_correction_chat_context_ready_count": manifest["ocr_fact_owner_decision_correction_chat_context_ready_count"],
                "ocr_fact_owner_decision_correction_chat_context_blocking_count": manifest["ocr_fact_owner_decision_correction_chat_context_blocking_count"],
                "ocr_fact_owner_decision_correction_chat_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_chat_context_write_allowed_count"],
                "ocr_fact_owner_decision_correction_chat_neighbor_context_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_count"],
                "ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"],
                "ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count"],
                "ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count": manifest["ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count"],
                "ocr_fact_owner_decision_correction_owner_review_packet_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_count"],
                "ocr_fact_owner_decision_correction_owner_review_packet_ready_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"],
                "ocr_fact_owner_decision_correction_owner_review_packet_blocking_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_blocking_count"],
                "ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count": manifest["ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count"],
                "ocr_fact_owner_decision_correction_manifest_readiness_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_count"],
                "ocr_fact_owner_decision_correction_manifest_readiness_ready_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"],
                "ocr_fact_owner_decision_correction_manifest_readiness_blocking_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_blocking_count"],
                "ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count": manifest["ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count"],
                "ocr_fact_owner_decision_correction_draft_count": manifest["ocr_fact_owner_decision_correction_draft_count"],
                "ocr_fact_owner_decision_correction_draft_write_allowed_count": manifest["ocr_fact_owner_decision_correction_draft_write_allowed_count"],
                "ocr_fact_owner_decision_correction_apply_preview_count": manifest["ocr_fact_owner_decision_correction_apply_preview_count"],
                "ocr_fact_owner_decision_correction_apply_preview_ready_count": manifest["ocr_fact_owner_decision_correction_apply_preview_ready_count"],
                "ocr_fact_owner_decision_correction_apply_preview_blocking_count": manifest["ocr_fact_owner_decision_correction_apply_preview_blocking_count"],
                "ocr_fact_owner_decision_correction_apply_preview_write_allowed_count": manifest["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"],
                "ocr_fact_owner_decision_correction_roundtrip_audit_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_count"],
                "ocr_fact_owner_decision_correction_roundtrip_audit_ready_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"],
                "ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count"],
                "ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count": manifest["ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count"],
                "ocr_fact_review_apply_gate_count": manifest["ocr_fact_review_apply_gate_count"],
                "ocr_fact_review_authorization_present_count": manifest["ocr_fact_review_authorization_present_count"],
                "ocr_fact_review_authorization_valid_count": manifest["ocr_fact_review_authorization_valid_count"],
                "ocr_fact_review_authorization_template_count": manifest["ocr_fact_review_authorization_template_count"],
                "ocr_fact_review_authorization_template_authorized_count": manifest["ocr_fact_review_authorization_template_authorized_count"],
                "ocr_fact_review_authorization_preview_count": manifest["ocr_fact_review_authorization_preview_count"],
                "ocr_fact_review_authorization_preview_ready_count": manifest["ocr_fact_review_authorization_preview_ready_count"],
                "ocr_fact_review_authorization_preview_blocked_count": manifest["ocr_fact_review_authorization_preview_blocked_count"],
                "chat_text_candidate_count": len(chat_text_candidates),
                "chat_value_candidate_count": len(chat_value_candidates),
                "chat_evidence_link_count": len(chat_evidence_links),
                "chat_evidence_linked_count": manifest["chat_evidence_linked_count"],
                "attachment_reconciliation_count": len(attachment_reconciliation_rows),
                "attachment_reconciliation_linked_count": manifest["attachment_reconciliation_linked_count"],
                "attachment_reconciliation_blocking_count": manifest["attachment_reconciliation_blocking_count"],
                "attachment_remediation_count": len(attachment_remediation_rows),
                "attachment_remediation_open_count": manifest["attachment_remediation_open_count"],
                "attachment_repair_source_locator_count": manifest["attachment_repair_source_locator_count"],
                "attachment_repair_source_locator_candidate_count": manifest["attachment_repair_source_locator_candidate_count"],
                "attachment_repair_source_locator_apply_allowed_count": manifest["attachment_repair_source_locator_apply_allowed_count"],
                "attachment_remediation_dry_run_count": len(attachment_dry_run_rows),
                "attachment_remediation_apply_allowed_count": manifest["attachment_remediation_apply_allowed_count"],
                "attachment_repair_plan_count": len(attachment_repair_plan_rows),
                "attachment_repair_plan_open_count": manifest["attachment_repair_plan_open_count"],
                "attachment_repair_apply_gate_count": manifest["attachment_repair_apply_gate_count"],
                "attachment_repair_apply_blocked_count": manifest["attachment_repair_apply_blocked_count"],
                "attachment_repair_authorization_present_count": manifest["attachment_repair_authorization_present_count"],
                "attachment_repair_authorization_valid_count": manifest["attachment_repair_authorization_valid_count"],
                "attachment_repair_authorization_template_count": manifest["attachment_repair_authorization_template_count"],
                "attachment_repair_authorization_template_authorized_count": manifest["attachment_repair_authorization_template_authorized_count"],
                "attachment_repair_authorization_preview_count": manifest["attachment_repair_authorization_preview_count"],
                "attachment_repair_authorization_preview_ready_count": manifest["attachment_repair_authorization_preview_ready_count"],
                "attachment_repair_authorization_preview_blocked_count": manifest["attachment_repair_authorization_preview_blocked_count"],
                "attachment_repair_apply_allowed_count": manifest["attachment_repair_apply_allowed_count"],
                "structured_financial_fact_count": len(structured["fund_rows"]),
                "metadata_signal_count": len(metadata_signals),
                "forecast_row_count": len(funding_forecast_rows),
                "cashflow_validation_row_count": len(cashflow_validation_rows),
                "balance_continuity_fail_count": balance_continuity_fail_count,
                "internal_transfer_excluded_count": internal_transfer_excluded_count,
                "workbook_quality_check_count": len(workbook_quality_rows),
                "workbook_quality_blocking_count": workbook_quality_blocking_count,
                "automation_readiness_count": len(automation_readiness_rows),
                "automation_readiness_ready_count": automation_readiness_ready_count,
                "automation_readiness_blocking_count": automation_readiness_blocking_count,
                "automation_readiness_status": automation_readiness_rows[0]["status"] if automation_readiness_rows else "CODEX_AUTOMATION_UNKNOWN",
                "goal_completion_audit_check_count": len(goal_completion_audit_rows),
                "goal_completion_blocking_count": goal_completion_blocking_count,
                "fact_promotion_review_packet_count": len(fact_promotion_review_packet_rows),
                "fact_promotion_review_blocking_count": fact_promotion_review_blocking_count,
                "fact_promotion_owner_review_batch_count": len(fact_promotion_owner_review_batch_rows),
                "fact_promotion_owner_review_batch_authorization_required_count": fact_promotion_owner_review_batch_authorization_required_count,
                "fact_promotion_owner_review_batch_blocking_count": fact_promotion_owner_review_batch_blocking_count,
                "fact_promotion_authorization_template_count": manifest["fact_promotion_authorization_template_count"],
                "fact_promotion_authorization_template_authorized_count": fact_promotion_authorization_template_authorized_count,
                "fact_promotion_authorization_present_count": manifest["fact_promotion_authorization_present_count"],
                "fact_promotion_authorization_valid_count": fact_promotion_authorization_valid_count,
                "fact_promotion_authorization_preview_count": len(fact_promotion_authorization_preview_rows),
                "fact_promotion_authorization_preview_ready_count": fact_promotion_authorization_preview_ready_count,
                "fact_promotion_authorization_preview_blocked_count": manifest["fact_promotion_authorization_preview_blocked_count"],
                "fact_promotion_execution_gate_count": len(fact_promotion_execution_gate_rows),
                "fact_promotion_execution_gate_ready_count": fact_promotion_execution_gate_ready_count,
                "fact_promotion_execution_gate_blocked_count": manifest["fact_promotion_execution_gate_blocked_count"],
                "fact_promotion_execution_allowed_count": manifest["fact_promotion_execution_allowed_count"],
                "fact_promotion_execution_plan_count": manifest["fact_promotion_execution_plan_count"],
                "fact_promotion_execution_plan_ready_count": fact_promotion_execution_plan_ready_count,
                "fact_promotion_execution_plan_blocked_count": fact_promotion_execution_plan_blocked_count,
                "fact_promotion_execution_plan_planned_impact_count": (
                    fact_promotion_execution_plan_planned_impact_count
                ),
                "fact_promotion_execution_plan_write_allowed_count": (
                    manifest["fact_promotion_execution_plan_write_allowed_count"]
                ),
                "fact_promotion_execution_authorization_template_count": (
                    manifest["fact_promotion_execution_authorization_template_count"]
                ),
                "fact_promotion_execution_authorization_template_authorized_count": (
                    fact_promotion_execution_authorization_template_authorized_count
                ),
                "fact_promotion_execution_authorization_preview_count": (
                    manifest["fact_promotion_execution_authorization_preview_count"]
                ),
                "fact_promotion_execution_authorization_preview_ready_count": (
                    fact_promotion_execution_authorization_preview_ready_count
                ),
                "fact_promotion_execution_authorization_preview_blocked_count": (
                    fact_promotion_execution_authorization_preview_blocked_count
                ),
                "fact_promotion_execution_authorization_write_allowed_count": (
                    manifest["fact_promotion_execution_authorization_write_allowed_count"]
                ),
                "fact_promotion_execution_apply_gate_count": manifest["fact_promotion_execution_apply_gate_count"],
                "fact_promotion_execution_apply_gate_ready_count": fact_promotion_execution_apply_gate_ready_count,
                "fact_promotion_execution_apply_gate_blocked_count": fact_promotion_execution_apply_gate_blocked_count,
                "fact_promotion_execution_apply_gate_planned_apply_count": (
                    fact_promotion_execution_apply_gate_planned_apply_count
                ),
                "fact_promotion_execution_apply_gate_write_allowed_count": (
                    manifest["fact_promotion_execution_apply_gate_write_allowed_count"]
                ),
                "management_conclusion_gate_count": len(management_conclusion_gate_rows),
                "management_conclusion_gate_ready_count": management_conclusion_gate_ready_count,
                "management_conclusion_gate_blocked_count": manifest["management_conclusion_gate_blocked_count"],
                "owner_action_queue_count": len(owner_action_queue_rows),
                "owner_action_queue_blocking_count": owner_action_queue_blocking_count,
                "owner_action_queue_automation_safe_count": owner_action_queue_automation_safe_count,
                "management_conclusion_allowed": False,
            },
        ], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "data_quality_issues.json").write_text(
        json.dumps(manifest["data_quality_issues"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_source_missing_artifacts(input_dir: Path, run_dir: Path, timezone: str) -> None:
    now = dt.datetime.now(ZoneInfo(timezone)).isoformat()
    candidates = source_candidates_for(input_dir)
    issue = {
        "issue_type": "SOURCE_MISSING",
        "severity": "blocking",
        "path": str(input_dir),
        "observed_at": now,
        "action": "Create or refresh the DWS_Outputs/付款请示群 source, or run an explicit materialization step from a verified private source candidate; do not invent data.",
    }
    manifest = {
        "project_id": "KMFA",
        "skill_name": "fund-weekly-analysis-skill",
        "run_id": run_dir.name,
        "timezone": timezone,
        "input_dir": str(input_dir),
        "generated_at": now,
        "status": "SOURCE_MISSING",
        "file_count": 0,
        "files": [],
        "source_candidates": candidates,
        "data_quality_issues": [issue],
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "data_quality_issues.json").write_text(json.dumps([issue], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "evidence_index.csv").write_text(
        "evidence_id,relative_path,kind,sha256,size_bytes,review_status\n",
        encoding="utf-8-sig",
    )
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_dir.name}\n\n"
        f"Status: SOURCE_MISSING\n\n"
        f"Missing input directory: `{input_dir}`\n\n"
        "No extraction, financial conclusion, or Excel production was performed. This is a fail-closed run.\n",
        encoding="utf-8",
    )


def write_source_unreadable_artifacts(manifest: dict, run_dir: Path) -> None:
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "data_quality_issues.json").write_text(
        json.dumps(manifest["data_quality_issues"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "evidence_index.csv").write_text(
        "evidence_id,relative_path,kind,sha256,size_bytes,review_status\n",
        encoding="utf-8-sig",
    )
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {manifest['run_id']}\n\n"
        "Status: SOURCE_UNREADABLE\n\n"
        f"Readable indexed file count: {manifest['file_count']}\n\n"
        f"Unreadable source file count: {manifest['unreadable_count']}\n\n"
        "No Excel package, extraction, financial conclusion, or forecast was produced. This is a fail-closed run.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群")
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--automation-root", default=str(Path.home() / ".codex" / "automations"))
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    timezone = ZoneInfo(args.timezone)
    input_dir = Path(args.input_dir).expanduser().resolve()
    run_id = args.run_id or dt.datetime.now(timezone).strftime("%Y%m%dT%H%M%S%z")
    run_dir = repo_root / "KMFA" / "metadata" / "fund_weekly_analysis" / "private_runtime" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        write_source_missing_artifacts(input_dir, run_dir, args.timezone)
        print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": "SOURCE_MISSING"}, ensure_ascii=False))
        return 2

    manifest = build_manifest(input_dir, run_dir, args.timezone)
    if manifest["status"] == "SOURCE_UNREADABLE":
        write_source_unreadable_artifacts(manifest, run_dir)
        print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": "SOURCE_UNREADABLE", "unreadable_count": manifest["unreadable_count"]}, ensure_ascii=False))
        return 5
    write_no_hallucination_outputs(manifest, run_dir, input_dir, repo_root, Path(args.automation_root))
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_id}\n\n"
        f"Status: {manifest['status']}\n\n"
        f"Indexed {manifest['file_count']} real source files and generated a native editable Excel workbook from the current mother template.\n\n"
        f"Structured financial fact count: {manifest.get('structured_fact_count', 0)}\n\n"
        f"Screenshot OCR coverage count: {manifest.get('screenshot_ocr_coverage_count', 0)}\n\n"
        f"Screenshot OCR ready count: {manifest.get('screenshot_ocr_ready_count', 0)}\n\n"
        f"Screenshot OCR missing count: {manifest.get('screenshot_ocr_missing_count', 0)}\n\n"
        f"OCR text candidate count: {manifest.get('ocr_text_candidate_count', 0)}\n\n"
        f"OCR value candidate count: {manifest.get('ocr_value_candidate_count', 0)}\n\n"
        f"OCR financial fact candidate count: {manifest.get('ocr_financial_fact_candidate_count', 0)}\n\n"
        f"OCR fact cross-review group count: {manifest.get('ocr_fact_cross_review_group_count', 0)}\n\n"
        f"OCR fact owner review batch count: {manifest.get('ocr_fact_owner_review_batch_count', 0)}\n\n"
        f"OCR fact owner review batch blocking count: {manifest.get('ocr_fact_owner_review_batch_blocking_count', 0)}\n\n"
        f"OCR fact evidence review queue count: {manifest.get('ocr_fact_evidence_review_queue_count', 0)}\n\n"
        f"OCR fact evidence review queue blocking count: {manifest.get('ocr_fact_evidence_review_queue_blocking_count', 0)}\n\n"
        f"OCR fact candidate owner worklist count: {manifest.get('ocr_fact_candidate_owner_worklist_count', 0)}\n\n"
        f"OCR fact candidate owner worklist ready count: {manifest.get('ocr_fact_candidate_owner_worklist_ready_count', 0)}\n\n"
        f"OCR fact candidate owner worklist blocking count: {manifest.get('ocr_fact_candidate_owner_worklist_blocking_count', 0)}\n\n"
        f"OCR fact candidate owner decision template count: {manifest.get('ocr_fact_candidate_owner_decision_template_count', 0)}\n\n"
        f"OCR fact candidate owner decision preview ready count: {manifest.get('ocr_fact_candidate_owner_decision_preview_ready_count', 0)}\n\n"
        f"OCR fact candidate owner decision preview blocking count: {manifest.get('ocr_fact_candidate_owner_decision_preview_blocking_count', 0)}\n\n"
        f"OCR fact candidate owner decision progress summary count: {manifest.get('ocr_fact_candidate_owner_decision_progress_summary_count', 0)}\n\n"
        f"OCR fact candidate owner decision progress summary candidate count: {manifest.get('ocr_fact_candidate_owner_decision_progress_summary_candidate_count', 0)}\n\n"
        f"OCR fact candidate owner decision progress summary blocking count: {manifest.get('ocr_fact_candidate_owner_decision_progress_summary_blocking_count', 0)}\n\n"
        f"OCR fact candidate owner authorization update draft count: {manifest.get('ocr_fact_candidate_owner_authorization_update_draft_count', 0)}\n\n"
        f"OCR fact candidate owner authorization update preview ready count: {manifest.get('ocr_fact_candidate_owner_authorization_update_preview_ready_count', 0)}\n\n"
        f"OCR fact candidate owner authorization update preview blocking count: {manifest.get('ocr_fact_candidate_owner_authorization_update_preview_blocking_count', 0)}\n\n"
        f"OCR fact ledger staging preview ready count: {manifest.get('ocr_fact_ledger_staging_preview_ready_count', 0)}\n\n"
        f"OCR fact ledger staging preview blocked count: {manifest.get('ocr_fact_ledger_staging_preview_blocked_count', 0)}\n\n"
        f"OCR fact controlled ledger row preview count: {manifest.get('ocr_fact_controlled_ledger_row_preview_count', 0)}\n\n"
        f"OCR fact controlled ledger row preview ready count: {manifest.get('ocr_fact_controlled_ledger_row_preview_ready_count', 0)}\n\n"
        f"OCR fact controlled ledger row preview blocking count: {manifest.get('ocr_fact_controlled_ledger_row_preview_blocking_count', 0)}\n\n"
        f"OCR fact controlled ledger apply gate ready count: {manifest.get('ocr_fact_controlled_ledger_apply_gate_ready_count', 0)}\n\n"
        f"OCR fact controlled ledger apply gate blocking count: {manifest.get('ocr_fact_controlled_ledger_apply_gate_blocking_count', 0)}\n\n"
        f"OCR fact controlled ledger apply gate planned apply count: {manifest.get('ocr_fact_controlled_ledger_apply_gate_planned_apply_count', 0)}\n\n"
        f"OCR fact controlled ledger apply gate write-allowed count: {manifest.get('ocr_fact_controlled_ledger_apply_gate_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction queue count: {manifest.get('ocr_fact_owner_decision_correction_queue_count', 0)}\n\n"
        f"OCR fact owner decision correction queue blocking count: {manifest.get('ocr_fact_owner_decision_correction_queue_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction queue write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_queue_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction evidence packet ready count: {manifest.get('ocr_fact_owner_decision_correction_evidence_packet_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction evidence packet blocking count: {manifest.get('ocr_fact_owner_decision_correction_evidence_packet_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction evidence packet write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction OCR line context ready count: {manifest.get('ocr_fact_owner_decision_correction_ocr_line_context_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction OCR line context blocking count: {manifest.get('ocr_fact_owner_decision_correction_ocr_line_context_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction OCR line context write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction chat context ready count: {manifest.get('ocr_fact_owner_decision_correction_chat_context_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction chat context blocking count: {manifest.get('ocr_fact_owner_decision_correction_chat_context_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction chat context write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_chat_context_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction chat neighbor context ready count: {manifest.get('ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction chat neighbor context blocking count: {manifest.get('ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction chat neighbor context write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction owner review packet ready count: {manifest.get('ocr_fact_owner_decision_correction_owner_review_packet_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction owner review packet blocking count: {manifest.get('ocr_fact_owner_decision_correction_owner_review_packet_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction owner review packet write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction manifest readiness count: {manifest.get('ocr_fact_owner_decision_correction_manifest_readiness_count', 0)}\n\n"
        f"OCR fact owner decision correction manifest readiness ready count: {manifest.get('ocr_fact_owner_decision_correction_manifest_readiness_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction manifest readiness blocking count: {manifest.get('ocr_fact_owner_decision_correction_manifest_readiness_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction manifest readiness write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction draft count: {manifest.get('ocr_fact_owner_decision_correction_draft_count', 0)}\n\n"
        f"OCR fact owner decision correction draft write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_draft_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction apply preview ready count: {manifest.get('ocr_fact_owner_decision_correction_apply_preview_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction apply preview blocking count: {manifest.get('ocr_fact_owner_decision_correction_apply_preview_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction apply preview write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_apply_preview_write_allowed_count', 0)}\n\n"
        f"OCR fact owner decision correction roundtrip audit ready count: {manifest.get('ocr_fact_owner_decision_correction_roundtrip_audit_ready_count', 0)}\n\n"
        f"OCR fact owner decision correction roundtrip audit blocking count: {manifest.get('ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count', 0)}\n\n"
        f"OCR fact owner decision correction roundtrip audit write-allowed count: {manifest.get('ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count', 0)}\n\n"
        f"OCR fact review authorization valid count: {manifest.get('ocr_fact_review_authorization_valid_count', 0)}\n\n"
        f"OCR fact review authorization preview ready count: {manifest.get('ocr_fact_review_authorization_preview_ready_count', 0)}\n\n"
        f"OCR fact review authorization preview blocked count: {manifest.get('ocr_fact_review_authorization_preview_blocked_count', 0)}\n\n"
        f"Chat text candidate count: {manifest.get('chat_text_candidate_count', 0)}\n\n"
        f"Chat value candidate count: {manifest.get('chat_value_candidate_count', 0)}\n\n"
        f"Chat evidence link count: {manifest.get('chat_evidence_link_count', 0)}\n\n"
        f"Chat evidence linked count: {manifest.get('chat_evidence_linked_count', 0)}\n\n"
        f"Attachment evidence reconciliation count: {manifest.get('attachment_reconciliation_count', 0)}\n\n"
        f"Attachment evidence reconciliation blocking count: {manifest.get('attachment_reconciliation_blocking_count', 0)}\n\n"
        f"Attachment remediation open count: {manifest.get('attachment_remediation_open_count', 0)}\n\n"
        f"Attachment repair source locator count: {manifest.get('attachment_repair_source_locator_count', 0)}\n\n"
        f"Attachment repair source locator candidate count: {manifest.get('attachment_repair_source_locator_candidate_count', 0)}\n\n"
        f"Attachment repair source locator apply allowed count: {manifest.get('attachment_repair_source_locator_apply_allowed_count', 0)}\n\n"
        f"Attachment remediation dry-run count: {manifest.get('attachment_remediation_dry_run_count', 0)}\n\n"
        f"Attachment repair plan open count: {manifest.get('attachment_repair_plan_open_count', 0)}\n\n"
        f"Attachment repair apply blocked count: {manifest.get('attachment_repair_apply_blocked_count', 0)}\n\n"
        f"Attachment repair authorization valid count: {manifest.get('attachment_repair_authorization_valid_count', 0)}\n\n"
        f"Attachment repair authorization template count: {manifest.get('attachment_repair_authorization_template_count', 0)}\n\n"
        f"Attachment repair authorization preview ready count: {manifest.get('attachment_repair_authorization_preview_ready_count', 0)}\n\n"
        f"Attachment repair authorization preview blocked count: {manifest.get('attachment_repair_authorization_preview_blocked_count', 0)}\n\n"
        f"KMFA metadata signal count: {manifest.get('metadata_signal_count', 0)}\n\n"
        f"Known due-date funding forecast row count: {manifest.get('forecast_row_count', 0)}\n\n"
        f"Cashflow validation row count: {manifest.get('cashflow_validation_row_count', 0)}\n\n"
        f"Balance continuity fail count: {manifest.get('balance_continuity_fail_count', 0)}\n\n"
        f"Workbook quality blocking count: {manifest.get('workbook_quality_blocking_count', 0)}\n\n"
        f"Automation readiness status: {manifest.get('automation_readiness_status', 'CODEX_AUTOMATION_UNKNOWN')}\n\n"
        f"Automation readiness ready count: {manifest.get('automation_readiness_ready_count', 0)}\n\n"
        f"Automation readiness blocking count: {manifest.get('automation_readiness_blocking_count', 0)}\n\n"
        f"Goal completion audit check count: {manifest.get('goal_completion_audit_check_count', 0)}\n\n"
        f"Goal completion blocking count: {manifest.get('goal_completion_blocking_count', 0)}\n\n"
        f"Fact promotion review packet count: {manifest.get('fact_promotion_review_packet_count', 0)}\n\n"
        f"Fact promotion review blocking count: {manifest.get('fact_promotion_review_blocking_count', 0)}\n\n"
        f"Fact promotion owner review batch count: {manifest.get('fact_promotion_owner_review_batch_count', 0)}\n\n"
        f"Fact promotion owner review batch authorization-required count: {manifest.get('fact_promotion_owner_review_batch_authorization_required_count', 0)}\n\n"
        f"Fact promotion owner review batch blocking count: {manifest.get('fact_promotion_owner_review_batch_blocking_count', 0)}\n\n"
        f"Fact promotion authorization template count: {manifest.get('fact_promotion_authorization_template_count', 0)}\n\n"
        f"Fact promotion authorization template authorized count: {manifest.get('fact_promotion_authorization_template_authorized_count', 0)}\n\n"
        f"Fact promotion authorization valid count: {manifest.get('fact_promotion_authorization_valid_count', 0)}\n\n"
        f"Fact promotion authorization preview ready count: {manifest.get('fact_promotion_authorization_preview_ready_count', 0)}\n\n"
        f"Fact promotion authorization preview blocked count: {manifest.get('fact_promotion_authorization_preview_blocked_count', 0)}\n\n"
        f"Fact promotion execution gate ready count: {manifest.get('fact_promotion_execution_gate_ready_count', 0)}\n\n"
        f"Fact promotion execution gate blocked count: {manifest.get('fact_promotion_execution_gate_blocked_count', 0)}\n\n"
        f"Fact promotion execution allowed count: {manifest.get('fact_promotion_execution_allowed_count', 0)}\n\n"
        f"Fact promotion execution plan ready count: {manifest.get('fact_promotion_execution_plan_ready_count', 0)}\n\n"
        f"Fact promotion execution plan planned impact count: {manifest.get('fact_promotion_execution_plan_planned_impact_count', 0)}\n\n"
        f"Fact promotion execution plan write-allowed count: {manifest.get('fact_promotion_execution_plan_write_allowed_count', 0)}\n\n"
        f"Fact promotion execution authorization preview ready count: {manifest.get('fact_promotion_execution_authorization_preview_ready_count', 0)}\n\n"
        f"Fact promotion execution authorization preview blocked count: {manifest.get('fact_promotion_execution_authorization_preview_blocked_count', 0)}\n\n"
        f"Fact promotion execution authorization write-allowed count: {manifest.get('fact_promotion_execution_authorization_write_allowed_count', 0)}\n\n"
        f"Fact promotion execution apply gate ready count: {manifest.get('fact_promotion_execution_apply_gate_ready_count', 0)}\n\n"
        f"Fact promotion execution apply gate planned apply count: {manifest.get('fact_promotion_execution_apply_gate_planned_apply_count', 0)}\n\n"
        f"Fact promotion execution apply gate write-allowed count: {manifest.get('fact_promotion_execution_apply_gate_write_allowed_count', 0)}\n\n"
        f"Management conclusion release authorization preview ready count: {manifest.get('management_conclusion_release_authorization_preview_ready_count', 0)}\n\n"
        f"Management conclusion release authorization preview blocked count: {manifest.get('management_conclusion_release_authorization_preview_blocked_count', 0)}\n\n"
        f"Management conclusion release precondition blocking count: {manifest.get('management_conclusion_release_precondition_blocking_count', 0)}\n\n"
        f"Management conclusion gate ready count: {manifest.get('management_conclusion_gate_ready_count', 0)}\n\n"
        f"Management conclusion gate blocked count: {manifest.get('management_conclusion_gate_blocked_count', 0)}\n\n"
        f"Owner action queue count: {manifest.get('owner_action_queue_count', 0)}\n\n"
        f"Owner action queue blocking count: {manifest.get('owner_action_queue_blocking_count', 0)}\n\n"
        f"Owner action queue automation-safe count: {manifest.get('owner_action_queue_automation_safe_count', 0)}\n\n"
        "No financial amount, management conclusion, or evidence-free forecast was generated from unreviewed OCR/table extraction. "
        "Known due-date projections remain pending review. Next step: perform OCR/table extraction, internal-transfer netting, "
        "cross-review, then promote reviewed facts only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": manifest["status"], "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
