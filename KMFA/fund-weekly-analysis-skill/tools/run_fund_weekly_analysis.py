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
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

DISALLOWED_PRODUCTION_MARKERS = ("sample", "demo", "fake", "synthetic", "模拟", "测试数据")
PRIVATE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xls", ".csv", ".pdf", ".doc", ".docx", ".zip"}
TEMPLATE_NAME = "资金与税费管理母版_真实数据预览_v2.xlsx"
XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
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


def collect_ocr_text_candidates(manifest: dict, input_dir: Path, evidence: list[dict]) -> list[dict]:
    evidence_by_path = {row["relative_path"]: row for row in evidence}
    manifest_paths = {item["relative_path"]: item for item in manifest["files"]}
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
    return rows


def extract_ocr_value_candidates(manifest: dict, input_dir: Path, ocr_text_candidates: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for candidate in ocr_text_candidates:
        text_path = input_dir / candidate["ocr_text_relative_path"]
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
                    "resource_type": row.get("resource_type") or "",
                    "resource_id": row.get("resource_id") or "",
                    "status": row.get("status") or "",
                    "linked_relative_path": normalize_manifest_output_path(row.get("output_path") or "", input_dir),
                    "sha256": row.get("sha256") or "",
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


def workbook_quality_row(check_id: str, check_name: str, passed: bool, details: str) -> dict:
    return {
        "check_id": check_id,
        "check_name": check_name,
        "status": "PASS" if passed else "FAIL",
        "management_blocking": bool_text(not passed),
        "details": details,
    }


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
                    if flow_type in {"tax", "loan", "deposit"}:
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


def write_no_hallucination_outputs(manifest: dict, run_dir: Path, input_dir: Path, repo_root: Path) -> None:
    evidence = write_evidence_index_stub(manifest, run_dir)
    ocr_text_candidates = collect_ocr_text_candidates(manifest, input_dir, evidence)
    ocr_value_candidates = extract_ocr_value_candidates(manifest, input_dir, ocr_text_candidates)
    chat_text_candidates = collect_chat_text_candidates(manifest, input_dir, evidence)
    chat_value_candidates = extract_chat_value_candidates(manifest, chat_text_candidates)
    chat_evidence_links = collect_chat_evidence_links(manifest, input_dir, evidence, chat_text_candidates, chat_value_candidates)
    attachment_reconciliation_rows = collect_attachment_evidence_reconciliation(manifest, input_dir, evidence)
    structured = extract_structured_csv_facts(manifest, input_dir, evidence)
    funding_forecast_rows = build_funding_forecast_rows(structured)
    cashflow_validation_rows = build_cashflow_validation_rows(structured, manifest["run_id"])
    metadata_signals = collect_kmfa_metadata_signals(repo_root, manifest["run_id"])
    balance_continuity_fail_count = sum(1 for row in cashflow_validation_rows if row["validation_status"] == "FAIL")
    internal_transfer_excluded_count = sum(1 for row in cashflow_validation_rows if row["internal_transfer_excluded"] == "true")
    manifest["ocr_text_candidate_count"] = len(ocr_text_candidates)
    manifest["ocr_value_candidate_count"] = len(ocr_value_candidates)
    manifest["chat_text_candidate_count"] = len(chat_text_candidates)
    manifest["chat_value_candidate_count"] = len(chat_value_candidates)
    manifest["chat_evidence_link_count"] = len(chat_evidence_links)
    manifest["chat_evidence_linked_count"] = sum(1 for row in chat_evidence_links if row["link_status"] == "linked_pending_review")
    manifest["attachment_reconciliation_count"] = len(attachment_reconciliation_rows)
    manifest["attachment_reconciliation_linked_count"] = sum(1 for row in attachment_reconciliation_rows if row["reconciliation_status"] == "evidence_linked_pending_review")
    manifest["attachment_reconciliation_blocking_count"] = sum(1 for row in attachment_reconciliation_rows if row["reconciliation_status"].endswith("_blocking"))
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
    workbook_quality_rows = collect_workbook_quality_checks(workbook_path)
    workbook_quality_blocking_count = sum(1 for row in workbook_quality_rows if row["management_blocking"] == "true")
    manifest["workbook_quality_check_count"] = len(workbook_quality_rows)
    manifest["workbook_quality_blocking_count"] = workbook_quality_blocking_count

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

    cross_review = {
        "run_id": manifest["run_id"],
        "management_conclusion_allowed": False,
        "generated_financial_amount_count": 0,
        "ocr_text_candidate_count": len(ocr_text_candidates),
        "ocr_value_candidate_count": len(ocr_value_candidates),
        "chat_text_candidate_count": len(chat_text_candidates),
        "chat_value_candidate_count": len(chat_value_candidates),
        "chat_evidence_link_count": len(chat_evidence_links),
        "chat_evidence_linked_count": manifest["chat_evidence_linked_count"],
        "attachment_reconciliation_count": len(attachment_reconciliation_rows),
        "attachment_reconciliation_linked_count": manifest["attachment_reconciliation_linked_count"],
        "attachment_reconciliation_blocking_count": manifest["attachment_reconciliation_blocking_count"],
        "structured_financial_fact_count": len(structured["fund_rows"]),
        "metadata_signal_count": len(metadata_signals),
        "forecast_row_count": len(funding_forecast_rows),
        "cashflow_validation_row_count": len(cashflow_validation_rows),
        "balance_continuity_fail_count": balance_continuity_fail_count,
        "internal_transfer_excluded_count": internal_transfer_excluded_count,
        "workbook_quality_check_count": len(workbook_quality_rows),
        "workbook_quality_blocking_count": workbook_quality_blocking_count,
        "excel_workbook_generated": True,
        "workbook": workbook_path.name,
        "source_file_count": manifest["file_count"],
        "evidence_count": len(evidence),
        "status": manifest["status"],
        "reason": "No amount was generated or inferred before OCR/table extraction and review gates.",
    }
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
                "ocr_text_candidate_count": len(ocr_text_candidates),
                "ocr_value_candidate_count": len(ocr_value_candidates),
                "chat_text_candidate_count": len(chat_text_candidates),
                "chat_value_candidate_count": len(chat_value_candidates),
                "chat_evidence_link_count": len(chat_evidence_links),
                "chat_evidence_linked_count": manifest["chat_evidence_linked_count"],
                "attachment_reconciliation_count": len(attachment_reconciliation_rows),
                "attachment_reconciliation_linked_count": manifest["attachment_reconciliation_linked_count"],
                "attachment_reconciliation_blocking_count": manifest["attachment_reconciliation_blocking_count"],
                "structured_financial_fact_count": len(structured["fund_rows"]),
                "metadata_signal_count": len(metadata_signals),
                "forecast_row_count": len(funding_forecast_rows),
                "cashflow_validation_row_count": len(cashflow_validation_rows),
                "balance_continuity_fail_count": balance_continuity_fail_count,
                "internal_transfer_excluded_count": internal_transfer_excluded_count,
                "workbook_quality_check_count": len(workbook_quality_rows),
                "workbook_quality_blocking_count": workbook_quality_blocking_count,
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
    write_no_hallucination_outputs(manifest, run_dir, input_dir, repo_root)
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_id}\n\n"
        f"Status: {manifest['status']}\n\n"
        f"Indexed {manifest['file_count']} real source files and generated a native editable Excel workbook from the current mother template.\n\n"
        f"Structured financial fact count: {manifest.get('structured_fact_count', 0)}\n\n"
        f"OCR text candidate count: {manifest.get('ocr_text_candidate_count', 0)}\n\n"
        f"OCR value candidate count: {manifest.get('ocr_value_candidate_count', 0)}\n\n"
        f"Chat text candidate count: {manifest.get('chat_text_candidate_count', 0)}\n\n"
        f"Chat value candidate count: {manifest.get('chat_value_candidate_count', 0)}\n\n"
        f"Chat evidence link count: {manifest.get('chat_evidence_link_count', 0)}\n\n"
        f"Chat evidence linked count: {manifest.get('chat_evidence_linked_count', 0)}\n\n"
        f"Attachment evidence reconciliation count: {manifest.get('attachment_reconciliation_count', 0)}\n\n"
        f"Attachment evidence reconciliation blocking count: {manifest.get('attachment_reconciliation_blocking_count', 0)}\n\n"
        f"KMFA metadata signal count: {manifest.get('metadata_signal_count', 0)}\n\n"
        f"Known due-date funding forecast row count: {manifest.get('forecast_row_count', 0)}\n\n"
        f"Cashflow validation row count: {manifest.get('cashflow_validation_row_count', 0)}\n\n"
        f"Balance continuity fail count: {manifest.get('balance_continuity_fail_count', 0)}\n\n"
        f"Workbook quality blocking count: {manifest.get('workbook_quality_blocking_count', 0)}\n\n"
        "No financial amount, management conclusion, or evidence-free forecast was generated from unreviewed OCR/table extraction. "
        "Known due-date projections remain pending review. Next step: perform OCR/table extraction, internal-transfer netting, "
        "cross-review, then promote reviewed facts only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": manifest["status"], "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
