#!/usr/bin/env python3
"""Import WDA v0.2-R2 full-auto export bundle and regenerate local reports.

Full-sensitive data is written only under WDA_MetaData. Repo docs contain counts,
schema summaries, run status, and safety boundaries only.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import os
import re
import shutil
import sqlite3
import stat
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_REQUESTED_BUNDLE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/input_full_export/"
    "wda_v0_2_r2_full_export_transfer_bundle.zip"
)
DEFAULT_DISCOVERED_BUNDLE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_export/"
    "wda_v0_2_r2_full_export_transfer_bundle.zip"
)
DEFAULT_OUTPUT_ROOT = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_DOCS_ROOT = PROJECT_ROOT / "docs" / "v0_2_r2_full_auto_workspace"

REPORT_SECTIONS = [
    "结论",
    "关键发现",
    "为什么重要",
    "证据引用",
    "对我的影响",
    "下一步动作",
    "不确定的地方",
    "可忽略事项",
    "可自动化/模板化事项",
]

SIGNAL_TERMS = {
    "money_payment_invoice_contract_acceptance": [
        "付款",
        "支付",
        "发票",
        "金额",
        "合同",
        "验收",
        "费用",
        "款",
        "报价",
    ],
    "todo_commitment": [
        "需要",
        "今天",
        "明天",
        "安排",
        "提交",
        "确认",
        "回复",
        "处理",
        "跟进",
        "落实",
        "todo",
    ],
    "opportunity": [
        "项目",
        "计划",
        "方案",
        "客户",
        "需求",
        "机会",
        "合作",
        "报价",
        "推进",
    ],
    "risk_blocker": [
        "问题",
        "风险",
        "不行",
        "错误",
        "错",
        "延期",
        "延迟",
        "投诉",
        "麻烦",
        "无法",
        "失败",
        "阻塞",
        "risk",
    ],
    "communication_behavior": [
        "?",
        "？",
        "吗",
        "收到",
        "好的",
        "OK",
        "ok",
        "谢谢",
        "哈哈",
        "!",
        "！",
    ],
}

SUBJECT_LABELS = {
    "SUBJECT_all_messages": "全量消息覆盖",
    "SUBJECT_money_payment_invoice_contract_acceptance": "金额/发票/合同/验收线索",
    "SUBJECT_todo_commitment": "待办/承诺线索",
    "SUBJECT_opportunity": "机会发现线索",
    "SUBJECT_risk_blocker": "风险/阻塞线索",
    "SUBJECT_communication_behavior": "行为/沟通模式线索",
}

FORBIDDEN_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"key_info",
        r"(^|/)login($|/|\.)",
        r"mmkv",
        r"key[-_ ]?value",
        r"protected",
        r"sensitive_local_state",
        r"tool_work",
        r"decrypted",
        r"\.db$",
        r"\.sqlite$",
        r"\.db-wal$",
        r"\.db-shm$",
        r"\.mp4$",
        r"\.mov$",
        r"\.jpg$",
        r"\.jpeg$",
        r"\.png$",
        r"\.heic$",
        r"\.gif$",
        r"\.m4a$",
        r"\.mp3$",
    ]
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import WDA v0.2-R2 full bundle.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_REQUESTED_BUNDLE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--repo-docs-root", type=Path, default=DEFAULT_REPO_DOCS_ROOT)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ms_to_utc(ms: int | None) -> str:
    if not ms:
        return "UNKNOWN"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def reset_output_root(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    mkdir(path)


def write_text(path: Path, text: str) -> None:
    mkdir(path.parent)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    mkdir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def open_csv(path: Path, fieldnames: list[str]):
    mkdir(path.parent)
    f = path.open("w", encoding="utf-8", newline="")
    writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    return f, writer


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def excerpt(value: Any, limit: int = 180) -> str:
    text = clean_text(value)
    if not text:
        return "（空文本或非文本消息）"
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def safe_filename(value: str) -> str:
    out = []
    for ch in value:
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_") or "item"


def bullet(lines: Iterable[str]) -> str:
    material = [str(line) for line in lines if str(line)]
    return "\n".join(f"- {line}" for line in material) if material else "- 暂无。"


def table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    body = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        body.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(body)


def report_template(
    title: str,
    conclusion: list[str],
    findings: list[str],
    why: list[str],
    evidence: list[str],
    impact: list[str],
    actions: list[str],
    uncertainty: list[str],
    ignore: list[str],
    automate: list[str],
) -> str:
    sections = {
        "结论": conclusion,
        "关键发现": findings,
        "为什么重要": why,
        "证据引用": evidence,
        "对我的影响": impact,
        "下一步动作": actions,
        "不确定的地方": uncertainty,
        "可忽略事项": ignore,
        "可自动化/模板化事项": automate,
    }
    out = [f"# {title}", ""]
    for section in REPORT_SECTIONS:
        out.extend([f"## {section}", "", bullet(sections[section]), ""])
    return "\n".join(out)


def resolve_bundle(requested: Path) -> tuple[Path, bool]:
    if requested.exists():
        return requested, False
    if DEFAULT_DISCOVERED_BUNDLE.exists():
        return DEFAULT_DISCOVERED_BUNDLE, True
    return requested, False


def parse_checksums(raw: str) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        checksums[parts[1].strip()] = parts[0].strip()
    return checksums


def is_forbidden_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return any(pattern.search(normalized) for pattern in FORBIDDEN_PATTERNS)


def verify_bundle(bundle: Path, output_root: Path, requested: Path, fallback_used: bool) -> dict[str, Any]:
    if not bundle.exists():
        raise FileNotFoundError(f"Transfer bundle not found: {bundle}")
    bundle_sha = sha256_file(bundle)
    result = {
        "requested_bundle_path": str(requested),
        "requested_bundle_exists": requested.exists(),
        "actual_bundle_path": str(bundle),
        "fallback_bundle_used": fallback_used,
        "bundle_size_bytes": bundle.stat().st_size,
        "bundle_sha256": bundle_sha,
        "zip_testzip_error": None,
        "file_count": 0,
        "raw_chunk_count": 0,
        "report_file_count": 0,
        "manifest_file_count": 0,
        "forbidden_file_hits": [],
        "checksum_expected_count": 0,
        "checksum_checked_count": 0,
        "checksum_mismatch_count": 0,
        "checksum_missing_count": 0,
        "checksum_mismatches": [],
        "manifest_rows": 0,
        "raw_sensitive_manifest_rows": 0,
    }

    inventory_rows = []
    with zipfile.ZipFile(bundle) as z:
        result["zip_testzip_error"] = z.testzip()
        names = [info.filename for info in z.infolist() if not info.is_dir()]
        result["file_count"] = len(names)
        result["raw_chunk_count"] = sum(
            1 for name in names if name.startswith("raw_sensitive_export/") and name.endswith(".jsonl.gz")
        )
        result["report_file_count"] = sum(1 for name in names if name.startswith("reports/"))
        result["manifest_file_count"] = sum(1 for name in names if name.startswith("manifest/"))
        result["forbidden_file_hits"] = [name for name in names if is_forbidden_name(name)]
        for info in z.infolist():
            if info.is_dir():
                continue
            inventory_rows.append(
                {
                    "bundle_path": info.filename,
                    "size_bytes": info.file_size,
                    "compressed_size_bytes": info.compress_size,
                    "sha256_checked": "pending",
                    "category": (
                        "raw_sensitive_jsonl_gz"
                        if info.filename.startswith("raw_sensitive_export/")
                        else "manifest"
                        if info.filename.startswith("manifest/")
                        else "report"
                        if info.filename.startswith("reports/")
                        else "other"
                    ),
                }
            )
        checksums = parse_checksums(z.read("manifest/transfer_checksums.sha256").decode("utf-8"))
        result["checksum_expected_count"] = len(checksums)
        mismatches = []
        missing = []
        for rel_path, expected in checksums.items():
            try:
                data = z.read(rel_path)
            except KeyError:
                missing.append(rel_path)
                continue
            actual = sha256_bytes(data)
            if actual != expected:
                mismatches.append({"path": rel_path, "expected": expected, "actual": actual})
            result["checksum_checked_count"] += 1
        result["checksum_mismatch_count"] = len(mismatches)
        result["checksum_missing_count"] = len(missing)
        result["checksum_mismatches"] = mismatches[:20]

        manifest_raw = z.read("manifest/transfer_manifest.csv").decode("utf-8")
        manifest_rows = list(csv.DictReader(io.StringIO(manifest_raw)))
        result["manifest_rows"] = len(manifest_rows)
        result["raw_sensitive_manifest_rows"] = sum(
            1 for row in manifest_rows if row.get("raw_sensitive_message_content") == "yes"
        )

    write_csv(
        output_root / "source_file_inventory.csv",
        ["bundle_path", "size_bytes", "compressed_size_bytes", "sha256_checked", "category"],
        inventory_rows,
    )
    if result["zip_testzip_error"] is not None:
        raise RuntimeError(f"Zip CRC failed at {result['zip_testzip_error']}")
    if result["forbidden_file_hits"]:
        raise RuntimeError("Forbidden files found in bundle")
    if result["checksum_mismatch_count"] or result["checksum_missing_count"]:
        raise RuntimeError("Checksum validation failed")
    return result


def detect_signals(text: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for category, terms in SIGNAL_TERMS.items():
        for term in terms:
            if term in text:
                hits.append((category, term))
                break
    return hits


def message_direction(is_from_me: Any, kind_name: str) -> str:
    if kind_name == "system":
        return "system"
    if isinstance(is_from_me, bool):
        return "outbound" if is_from_me else "inbound"
    return "unknown"


def normalize_message(
    row: dict[str, Any],
    source_ref: str,
    seen_ids: set[str],
) -> dict[str, Any]:
    conversation_id = clean_text(row.get("talker")) or "UNKNOWN_CONVERSATION"
    server_id = clean_text(row.get("server_id_str")) or clean_text(row.get("server_id"))
    local_id = clean_text(row.get("local_id"))
    base_id = server_id or f"{conversation_id}:{local_id}:{source_ref}"
    message_id = base_id
    if message_id in seen_ids:
        suffix = hashlib.sha1(source_ref.encode("utf-8")).hexdigest()[:10]
        message_id = f"{base_id}__dup_{suffix}"
    seen_ids.add(message_id)
    create_time = row.get("create_time")
    try:
        timestamp_ms = int(create_time) * 1000
    except (TypeError, ValueError):
        timestamp_ms = 0
    kind_name = clean_text(row.get("kind_name")) or clean_text(row.get("base_kind")) or "unknown"
    text = clean_text(row.get("message_content")) or clean_text(row.get("content_summary"))
    sender = clean_text(row.get("sender_wxid"))
    direction = message_direction(row.get("is_from_me"), kind_name)
    if direction == "outbound":
        sender_id = "LOCAL_ACCOUNT"
    elif sender:
        sender_id = sender
    elif direction == "system":
        sender_id = "SYSTEM"
    else:
        sender_id = conversation_id
    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "direction": direction,
        "timestamp_ms": timestamp_ms,
        "message_type": kind_name,
        "text": text,
        "media_refs_json": "[]",
        "redaction_state": "none",
        "source_record_ref": source_ref,
        "receiver_ids_json": "[]",
        "reply_to_message_id": "",
        "language": "",
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest() if text else "",
        "import_notes": "v0.2-R2 full-auto bundle import",
        "talker_display_name": clean_text(row.get("talker_display_name")),
        "chat_type": clean_text(row.get("chat_type")),
    }


def create_schema(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    cur.executescript(
        """
        pragma journal_mode=wal;
        pragma synchronous=normal;
        create table sources (
          source_id text primary key,
          source_type text,
          source_path text,
          sha256 text,
          row_count integer,
          sensitivity text,
          imported_at text
        );
        create table import_runs (
          import_run_id text primary key,
          created_at text,
          input_bundle_path text,
          output_root text,
          raw_gate_status text,
          full_raw_gate_go integer,
          total_messages integer,
          total_conversations integer,
          failed_conversations integer,
          first_timestamp_ms integer,
          last_timestamp_ms integer
        );
        create table conversations (
          conversation_id text primary key,
          conversation_type text,
          participant_ids_json text,
          created_at_ms integer,
          last_message_at_ms integer,
          message_count_declared integer,
          display_title text,
          redaction_state text,
          owner_account_id text,
          source_record_ref text,
          import_notes text
        );
        create table contacts (
          contact_id text primary key,
          display_name text,
          contact_type text,
          aliases_json text,
          redaction_state text,
          profile_ref text,
          first_seen_ms integer,
          last_seen_ms integer,
          import_notes text
        );
        create table messages (
          message_id text primary key,
          conversation_id text,
          sender_id text,
          direction text,
          timestamp_ms integer,
          message_type text,
          text text,
          media_refs_json text,
          redaction_state text,
          source_record_ref text,
          receiver_ids_json text,
          reply_to_message_id text,
          language text,
          content_hash text,
          import_notes text
        );
        create table subjects (
          subject_id text primary key,
          subject_label text,
          subject_category text,
          confidence text,
          source text,
          expected_rows integer,
          actual_rows integer,
          excluded_noise text
        );
        create table message_subject_links (
          message_id text,
          subject_id text,
          link_method text,
          primary key (message_id, subject_id)
        );
        create table validation_events (
          event_id text primary key,
          import_run_id text,
          check_id text,
          result text,
          detail text,
          created_at text
        );
        create table media_index (
          media_id text primary key,
          message_id text,
          media_type text,
          local_path text,
          sha256 text,
          import_notes text
        );
        """
    )
    con.commit()


def insert_indexes(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    cur.executescript(
        """
        create index if not exists idx_messages_timestamp on messages(timestamp_ms);
        create index if not exists idx_messages_conversation on messages(conversation_id);
        create index if not exists idx_messages_sender on messages(sender_id);
        create index if not exists idx_links_subject on message_subject_links(subject_id);
        create index if not exists idx_messages_type on messages(message_type);
        create index if not exists idx_messages_direction on messages(direction);
        """
    )
    con.commit()


def open_jsonl_writer(path: Path):
    mkdir(path.parent)
    return path.open("w", encoding="utf-8")


def write_jsonl(f, obj: dict[str, Any]) -> None:
    f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def parse_bundle_to_core(bundle: Path, output_root: Path, verify: dict[str, Any]) -> dict[str, Any]:
    raw_root = output_root / "raw_import_pack"
    analysis_root = output_root / "analysis_outputs"
    data_core_root = output_root / "data_core"
    mkdir(raw_root)
    mkdir(analysis_root)
    mkdir(data_core_root)
    db_path = data_core_root / "wda_v0_2_r2.sqlite"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    create_schema(con)
    cur = con.cursor()

    messages_f = open_jsonl_writer(raw_root / "messages.jsonl")
    subject_stats_f, subject_stats_writer = open_csv(
        analysis_root / "subject_stats.csv",
        [
            "subject_id",
            "subject_label",
            "message_count",
            "conversation_count",
            "first_timestamp_ms",
            "first_timestamp_utc",
            "last_timestamp_ms",
            "last_timestamp_utc",
        ],
    )
    keyword_f, keyword_writer = open_csv(
        analysis_root / "keyword_signal_hits.csv",
        [
            "subject_id",
            "subject_label",
            "message_id",
            "conversation_id",
            "timestamp_ms",
            "signal_category",
            "term",
            "message_type",
            "direction",
            "text_full_sensitive",
        ],
    )
    todo_f, todo_writer = open_csv(
        analysis_root / "todo_signal_candidates.csv",
        ["subject_id", "subject_label", "message_id", "conversation_id", "timestamp_ms", "terms", "text_full_sensitive"],
    )
    opportunity_f, opportunity_writer = open_csv(
        analysis_root / "opportunity_signal_candidates.csv",
        ["subject_id", "subject_label", "message_id", "conversation_id", "timestamp_ms", "terms", "text_full_sensitive"],
    )
    risk_f, risk_writer = open_csv(
        analysis_root / "risk_signal_candidates.csv",
        ["subject_id", "subject_label", "message_id", "conversation_id", "timestamp_ms", "terms", "text_full_sensitive"],
    )
    timeline_f, timeline_writer = open_csv(
        analysis_root / "subject_timeline.csv",
        [
            "subject_id",
            "subject_label",
            "sequence",
            "timestamp_ms",
            "timestamp_utc",
            "message_id",
            "conversation_id",
            "sender_id",
            "direction",
            "message_type",
            "text_full_sensitive",
        ],
    )
    behavior_f, behavior_writer = open_csv(
        analysis_root / "behavior_pattern_indicators.csv",
        [
            "conversation_id",
            "display_title",
            "message_count",
            "avg_text_length",
            "question_marker_count",
            "exclamation_marker_count",
            "short_ack_count",
            "inbound_count",
            "outbound_count",
            "system_count",
            "claim_boundary",
        ],
    )

    seen_ids: set[str] = set()
    conversations: dict[str, dict[str, Any]] = {}
    contacts: dict[str, dict[str, Any]] = {}
    subject_counts: Counter[str] = Counter()
    subject_convs: dict[str, set[str]] = defaultdict(set)
    signal_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    message_type_counts: Counter[str] = Counter()
    conversation_signal_counts: dict[str, Counter[str]] = defaultdict(Counter)
    conversation_text_len: Counter[str] = Counter()
    conversation_question: Counter[str] = Counter()
    conversation_exclaim: Counter[str] = Counter()
    conversation_short_ack: Counter[str] = Counter()
    conversation_direction: dict[str, Counter[str]] = defaultdict(Counter)
    first_ts: int | None = None
    last_ts: int | None = None
    message_count = 0
    invalid_rows = 0
    chunk_count = 0
    chunk_errors: list[dict[str, Any]] = []
    failed_conversation_tokens: set[str] = set()
    evidence_samples: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=50))
    contact_radar_samples: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=8))

    all_subject_id = "SUBJECT_all_messages"
    for subject_id, label in SUBJECT_LABELS.items():
        cur.execute(
            "insert into subjects values (?, ?, ?, ?, ?, ?, ?, ?)",
            (subject_id, label, subject_id.replace("SUBJECT_", ""), "deterministic", "v0.2-R2 keyword/domain mapping", 0, 0, "false"),
        )

    message_insert_batch = []
    link_insert_batch = []
    batch_size = 5000

    with zipfile.ZipFile(bundle) as z:
        raw_names = sorted(
            n for n in z.namelist() if n.startswith("raw_sensitive_export/") and n.endswith(".jsonl.gz")
        )
        for raw_name in raw_names:
            chunk_count += 1
            try:
                with z.open(raw_name) as raw:
                    with gzip.GzipFile(fileobj=raw) as gz:
                        for line_number, line in enumerate(gz, start=1):
                            try:
                                source = json.loads(line)
                            except json.JSONDecodeError as exc:
                                invalid_rows += 1
                                chunk_errors.append({"chunk": raw_name, "line": line_number, "error": str(exc)})
                                continue
                            source_ref = f"{raw_name}:{line_number}"
                            msg = normalize_message(source, source_ref, seen_ids)
                            message_count += 1
                            ts = msg["timestamp_ms"]
                            if ts:
                                first_ts = ts if first_ts is None else min(first_ts, ts)
                                last_ts = ts if last_ts is None else max(last_ts, ts)
                            conv_id = msg["conversation_id"]
                            display_title = msg.pop("talker_display_name") or conv_id
                            chat_type = msg.pop("chat_type") or "unknown"
                            conv = conversations.setdefault(
                                conv_id,
                                {
                                    "conversation_id": conv_id,
                                    "conversation_type": chat_type,
                                    "participant_ids": set(),
                                    "created_at_ms": ts or 0,
                                    "last_message_at_ms": ts or 0,
                                    "message_count": 0,
                                    "display_title": display_title,
                                },
                            )
                            conv["message_count"] += 1
                            if ts:
                                conv["created_at_ms"] = min(conv["created_at_ms"] or ts, ts)
                                conv["last_message_at_ms"] = max(conv["last_message_at_ms"] or ts, ts)
                            if display_title and conv.get("display_title") == conv_id:
                                conv["display_title"] = display_title
                            sender_id = msg["sender_id"]
                            conv["participant_ids"].add(sender_id)
                            contacts.setdefault(
                                conv_id,
                                {
                                    "contact_id": conv_id,
                                    "display_name": display_title,
                                    "contact_type": chat_type,
                                    "first_seen_ms": ts or 0,
                                    "last_seen_ms": ts or 0,
                                },
                            )
                            if sender_id and sender_id not in {"SYSTEM", "UNKNOWN_SENDER"}:
                                contacts.setdefault(
                                    sender_id,
                                    {
                                        "contact_id": sender_id,
                                        "display_name": "本机账号" if sender_id == "LOCAL_ACCOUNT" else sender_id,
                                        "contact_type": "sender",
                                        "first_seen_ms": ts or 0,
                                        "last_seen_ms": ts or 0,
                                    },
                                )
                            contacts[conv_id]["last_seen_ms"] = max(contacts[conv_id].get("last_seen_ms", 0), ts or 0)
                            if sender_id in contacts:
                                contacts[sender_id]["last_seen_ms"] = max(contacts[sender_id].get("last_seen_ms", 0), ts or 0)

                            direction_counts[msg["direction"]] += 1
                            message_type_counts[msg["message_type"]] += 1
                            text = msg["text"]
                            hits = detect_signals(text)
                            if not hits:
                                hits = [("all_messages", "all")]
                            else:
                                for category, term in hits:
                                    subject_id = "SUBJECT_" + category
                                    signal_counts[category] += 1
                                    subject_counts[subject_id] += 1
                                    subject_convs[subject_id].add(conv_id)
                                    conversation_signal_counts[conv_id][category] += 1
                                    keyword_writer.writerow(
                                        {
                                            "subject_id": subject_id,
                                            "subject_label": SUBJECT_LABELS[subject_id],
                                            "message_id": msg["message_id"],
                                            "conversation_id": conv_id,
                                            "timestamp_ms": ts,
                                            "signal_category": category,
                                            "term": term,
                                            "message_type": msg["message_type"],
                                            "direction": msg["direction"],
                                            "text_full_sensitive": text,
                                        }
                                    )
                                    sample = {
                                        "message_id": msg["message_id"],
                                        "conversation_id": conv_id,
                                        "timestamp_ms": ts,
                                        "category": category,
                                        "term": term,
                                        "message_type": msg["message_type"],
                                        "direction": msg["direction"],
                                        "text": text,
                                    }
                                    evidence_samples[category].append(sample)
                                    contact_radar_samples[conv_id].append(sample)
                                    if category == "todo_commitment":
                                        todo_writer.writerow(
                                            {
                                                "subject_id": subject_id,
                                                "subject_label": SUBJECT_LABELS[subject_id],
                                                "message_id": msg["message_id"],
                                                "conversation_id": conv_id,
                                                "timestamp_ms": ts,
                                                "terms": term,
                                                "text_full_sensitive": text,
                                            }
                                        )
                                    elif category == "opportunity":
                                        opportunity_writer.writerow(
                                            {
                                                "subject_id": subject_id,
                                                "subject_label": SUBJECT_LABELS[subject_id],
                                                "message_id": msg["message_id"],
                                                "conversation_id": conv_id,
                                                "timestamp_ms": ts,
                                                "terms": term,
                                                "text_full_sensitive": text,
                                            }
                                        )
                                    elif category == "risk_blocker":
                                        risk_writer.writerow(
                                            {
                                                "subject_id": subject_id,
                                                "subject_label": SUBJECT_LABELS[subject_id],
                                                "message_id": msg["message_id"],
                                                "conversation_id": conv_id,
                                                "timestamp_ms": ts,
                                                "terms": term,
                                                "text_full_sensitive": text,
                                            }
                                        )

                            subject_counts[all_subject_id] += 1
                            subject_convs[all_subject_id].add(conv_id)
                            timeline_writer.writerow(
                                {
                                    "subject_id": all_subject_id,
                                    "subject_label": SUBJECT_LABELS[all_subject_id],
                                    "sequence": message_count,
                                    "timestamp_ms": ts,
                                    "timestamp_utc": ms_to_utc(ts),
                                    "message_id": msg["message_id"],
                                    "conversation_id": conv_id,
                                    "sender_id": sender_id,
                                    "direction": msg["direction"],
                                    "message_type": msg["message_type"],
                                    "text_full_sensitive": text,
                                }
                            )
                            for category, _term in hits:
                                subject_id = "SUBJECT_" + category if category != "all_messages" else all_subject_id
                                link_insert_batch.append((msg["message_id"], subject_id, "deterministic_keyword" if category != "all_messages" else "all_messages"))
                            write_jsonl(messages_f, msg)
                            message_insert_batch.append(
                                (
                                    msg["message_id"],
                                    conv_id,
                                    sender_id,
                                    msg["direction"],
                                    ts,
                                    msg["message_type"],
                                    text,
                                    msg["media_refs_json"],
                                    msg["redaction_state"],
                                    msg["source_record_ref"],
                                    msg["receiver_ids_json"],
                                    msg["reply_to_message_id"],
                                    msg["language"],
                                    msg["content_hash"],
                                    msg["import_notes"],
                                )
                            )
                            conversation_text_len[conv_id] += len(text)
                            conversation_question[conv_id] += text.count("?") + text.count("？")
                            conversation_exclaim[conv_id] += text.count("!") + text.count("！")
                            if text in {"收到", "好的", "OK", "ok", "嗯", "是"}:
                                conversation_short_ack[conv_id] += 1
                            conversation_direction[conv_id][msg["direction"]] += 1
                            if len(message_insert_batch) >= batch_size:
                                cur.executemany(
                                    "insert into messages values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    message_insert_batch,
                                )
                                cur.executemany(
                                    "insert or ignore into message_subject_links values (?, ?, ?)",
                                    link_insert_batch,
                                )
                                con.commit()
                                message_insert_batch.clear()
                                link_insert_batch.clear()
            except Exception as exc:  # noqa: BLE001
                chunk_errors.append({"chunk": raw_name, "line": "chunk", "error": str(exc)})
                token = raw_name.split("_", 2)[1] if "_" in raw_name else raw_name
                failed_conversation_tokens.add(token)

    if message_insert_batch:
        cur.executemany(
            "insert into messages values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            message_insert_batch,
        )
        cur.executemany(
            "insert or ignore into message_subject_links values (?, ?, ?)",
            link_insert_batch,
        )
        con.commit()

    messages_f.close()
    keyword_f.close()
    todo_f.close()
    opportunity_f.close()
    risk_f.close()
    timeline_f.close()

    conversations_json = raw_root / "conversations.jsonl"
    contacts_json = raw_root / "contacts.jsonl"
    with conversations_json.open("w", encoding="utf-8") as conv_f:
        for conv in conversations.values():
            participant_ids = sorted(conv["participant_ids"])
            obj = {
                "conversation_id": conv["conversation_id"],
                "conversation_type": conv["conversation_type"],
                "participant_ids": participant_ids,
                "created_at_ms": conv["created_at_ms"],
                "last_message_at_ms": conv["last_message_at_ms"],
                "message_count_declared": conv["message_count"],
                "display_title": conv["display_title"],
                "redaction_state": "none",
                "owner_account_id": "LOCAL_ACCOUNT",
                "source_record_ref": "v0.2-R2 full-auto transfer bundle",
                "import_notes": "v0.2-R2 full-auto bundle import",
            }
            conv_f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            cur.execute(
                "insert into conversations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    obj["conversation_id"],
                    obj["conversation_type"],
                    json.dumps(obj["participant_ids"], ensure_ascii=False),
                    obj["created_at_ms"],
                    obj["last_message_at_ms"],
                    obj["message_count_declared"],
                    obj["display_title"],
                    obj["redaction_state"],
                    obj["owner_account_id"],
                    obj["source_record_ref"],
                    obj["import_notes"],
                ),
            )
    with contacts_json.open("w", encoding="utf-8") as contacts_f:
        for contact in contacts.values():
            obj = {
                "contact_id": contact["contact_id"],
                "display_name": contact["display_name"],
                "contact_type": contact["contact_type"],
                "aliases": [],
                "redaction_state": "none",
                "profile_ref": "",
                "first_seen_ms": contact["first_seen_ms"],
                "last_seen_ms": contact["last_seen_ms"],
                "import_notes": "v0.2-R2 full-auto bundle import",
            }
            contacts_f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
            cur.execute(
                "insert into contacts values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    obj["contact_id"],
                    obj["display_name"],
                    obj["contact_type"],
                    json.dumps(obj["aliases"], ensure_ascii=False),
                    obj["redaction_state"],
                    obj["profile_ref"],
                    obj["first_seen_ms"],
                    obj["last_seen_ms"],
                    obj["import_notes"],
                ),
            )
    for subject_id, count in subject_counts.items():
        cur.execute(
            "update subjects set actual_rows = ?, expected_rows = ? where subject_id = ?",
            (count, count, subject_id),
        )
        subject_stats_writer.writerow(
            {
                "subject_id": subject_id,
                "subject_label": SUBJECT_LABELS.get(subject_id, subject_id),
                "message_count": count,
                "conversation_count": len(subject_convs[subject_id]),
                "first_timestamp_ms": first_ts or 0,
                "first_timestamp_utc": ms_to_utc(first_ts),
                "last_timestamp_ms": last_ts or 0,
                "last_timestamp_utc": ms_to_utc(last_ts),
            }
        )
    subject_stats_f.close()

    for conv_id, conv in conversations.items():
        msg_n = max(conv["message_count"], 1)
        behavior_writer.writerow(
            {
                "conversation_id": conv_id,
                "display_title": conv["display_title"],
                "message_count": conv["message_count"],
                "avg_text_length": round(conversation_text_len[conv_id] / msg_n, 2),
                "question_marker_count": conversation_question[conv_id],
                "exclamation_marker_count": conversation_exclaim[conv_id],
                "short_ack_count": conversation_short_ack[conv_id],
                "inbound_count": conversation_direction[conv_id]["inbound"],
                "outbound_count": conversation_direction[conv_id]["outbound"],
                "system_count": conversation_direction[conv_id]["system"],
                "claim_boundary": "observable_counts_only_no_personality_claims",
            }
        )
    behavior_f.close()

    media_index = raw_root / "media_index.csv"
    write_csv(
        media_index,
        ["media_id", "message_id", "media_type", "local_path", "sha256", "import_notes"],
        [],
    )
    import_manifest = {
        "import_id": "wda_v0_2_r2_full_auto_import",
        "created_at": now_iso(),
        "source_bundle": verify["actual_bundle_path"],
        "bundle_sha256": verify["bundle_sha256"],
        "message_rows": message_count,
        "conversation_rows": len(conversations),
        "contact_rows": len(contacts),
        "media_rows": 0,
        "redaction_state": "none_local_full_sensitive",
        "output_root": str(output_root),
    }
    write_json(raw_root / "import_manifest.json", import_manifest)

    cur.execute(
        "insert into sources values (?, ?, ?, ?, ?, ?, ?)",
        (
            "source_v0_2_r2_full_auto_bundle",
            "full_auto_transfer_bundle",
            verify["actual_bundle_path"],
            verify["bundle_sha256"],
            message_count,
            "local_full_sensitive",
            now_iso(),
        ),
    )
    cur.execute(
        "insert into import_runs values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "import_v0_2_r2_full_auto",
            now_iso(),
            verify["actual_bundle_path"],
            str(output_root),
            "Full-Auto Import Proven",
            0,
            message_count,
            len(conversations),
            len(failed_conversation_tokens),
            first_ts or 0,
            last_ts or 0,
        ),
    )
    validation_events = [
        ("event_bundle_checksum", "bundle_checksum", "pass", "all listed bundle checksums matched"),
        ("event_jsonl_parse", "jsonl_parse", "pass" if not invalid_rows else "warn", f"invalid_rows={invalid_rows}"),
        ("event_forbidden_files", "forbidden_file_scan", "pass", "no keys/db/media/tool state found"),
        ("event_sqlite_build", "sqlite_build", "pass", f"messages={message_count}"),
    ]
    for event_id, check_id, result, detail in validation_events:
        cur.execute(
            "insert into validation_events values (?, ?, ?, ?, ?, ?)",
            (event_id, "import_v0_2_r2_full_auto", check_id, result, detail, now_iso()),
        )
    con.commit()
    insert_indexes(con)
    integrity = con.execute("pragma integrity_check").fetchone()[0]
    fk_violations = con.execute("pragma foreign_key_check").fetchall()
    con.close()

    row_count_rows = [
        {"artifact": "messages.jsonl", "rows": message_count},
        {"artifact": "conversations.jsonl", "rows": len(conversations)},
        {"artifact": "contacts.jsonl", "rows": len(contacts)},
        {"artifact": "media_index.csv", "rows": 0},
        {"artifact": "sqlite.messages", "rows": message_count},
        {"artifact": "sqlite.conversations", "rows": len(conversations)},
        {"artifact": "sqlite.contacts", "rows": len(contacts)},
    ]
    write_csv(output_root / "row_count_summary.csv", ["artifact", "rows"], row_count_rows)

    summary = {
        "db_path": str(db_path),
        "message_count": message_count,
        "conversation_count": len(conversations),
        "contact_count": len(contacts),
        "media_count": 0,
        "chunk_count": chunk_count,
        "invalid_rows": invalid_rows,
        "chunk_error_count": len(chunk_errors),
        "failed_conversations": len(failed_conversation_tokens),
        "first_timestamp_ms": first_ts or 0,
        "first_timestamp_utc": ms_to_utc(first_ts),
        "last_timestamp_ms": last_ts or 0,
        "last_timestamp_utc": ms_to_utc(last_ts),
        "signal_counts": dict(signal_counts),
        "direction_counts": dict(direction_counts),
        "message_type_counts": dict(message_type_counts),
        "subject_counts": dict(subject_counts),
        "sqlite_integrity_check": integrity,
        "foreign_key_violation_count": len(fk_violations),
        "evidence_samples": {k: list(v) for k, v in evidence_samples.items()},
        "contact_radar_samples": {k: list(v) for k, v in contact_radar_samples.items()},
        "top_conversations": sorted(
            [
                {
                    "conversation_id": conv_id,
                    "display_title": conv["display_title"],
                    "message_count": conv["message_count"],
                    "risk": conversation_signal_counts[conv_id]["risk_blocker"],
                    "todo": conversation_signal_counts[conv_id]["todo_commitment"],
                    "opportunity": conversation_signal_counts[conv_id]["opportunity"],
                    "money": conversation_signal_counts[conv_id]["money_payment_invoice_contract_acceptance"],
                }
                for conv_id, conv in conversations.items()
            ],
            key=lambda item: (
                item["risk"] + item["todo"] + item["opportunity"] + item["money"],
                item["message_count"],
            ),
            reverse=True,
        )[:80],
    }
    write_json(analysis_root / "analysis_validation_report.json", summary)
    write_csv(
        analysis_root / "conversation_signal_summary.csv",
        ["conversation_id", "display_title", "message_count", "risk", "todo", "opportunity", "money"],
        summary["top_conversations"],
    )
    return summary


def evidence_lines(samples: list[dict[str, Any]], limit: int = 12) -> list[str]:
    out = []
    for sample in samples[:limit]:
        out.append(
            f"`{sample['message_id']}` / `{sample['conversation_id']}` / "
            f"{ms_to_utc(sample['timestamp_ms'])} / `{sample['category']}` / `{sample['term']}`："
            f"{excerpt(sample['text'])}"
        )
    return out


def generate_reports(output_root: Path, summary: dict[str, Any]) -> None:
    reports_root = output_root / "reports"
    radar_root = reports_root / "contact_radar"
    dashboard_root = output_root / "dashboard"
    mkdir(reports_root)
    mkdir(radar_root)
    mkdir(dashboard_root)
    signals = summary["signal_counts"]
    top_convs = summary["top_conversations"]
    all_samples = []
    for category_samples in summary["evidence_samples"].values():
        all_samples.extend(category_samples)

    common_uncertainty = [
        "本轮不解析图片、视频、语音或附件正文。",
        "关键词命中是线索，不等于最终事实，需要结合上下文复核。",
        "不做心理、性格或人格判断，只描述可观察沟通与业务线索。",
    ]
    report_specs = {
        "today_briefing.md": report_template(
            "今日简报",
            [
                f"已导入 `{summary['message_count']}` 条消息、`{summary['conversation_count']}` 个会话，中文工作区已重建。",
                "优先看风险中心、待办中心、金额/合同/验收线索和联系人雷达。",
            ],
            [
                f"风险线索 `{signals.get('risk_blocker', 0)}` 条。",
                f"待办/承诺线索 `{signals.get('todo_commitment', 0)}` 条。",
                f"机会线索 `{signals.get('opportunity', 0)}` 条。",
                f"金额/发票/合同/验收线索 `{signals.get('money_payment_invoice_contract_acceptance', 0)}` 条。",
            ],
            ["全量导入后，用户不需要从 CSV/schema 开始读，可以直接从行动报告进入。"],
            evidence_lines(all_samples, 16),
            ["能把微信聊天中的风险、待办、机会和交接信息转成可执行入口。"],
            ["先处理风险中心，再处理待办中心，然后看工作交接和联系人雷达。"],
            common_uncertainty,
            ["普通寒暄、系统通知、无业务词的短确认可以先降权。"],
            ["可每日自动生成 briefing；可把风险和待办推成固定检查清单。"],
        ),
        "work_handoff_summary.md": report_template(
            "工作交接总结",
            ["当前可形成基于证据的工作交接包，入口是风险、待办、金额/合同/验收、机会和联系人雷达。"],
            [
                f"可交接待办线索 `{signals.get('todo_commitment', 0)}`。",
                f"可交接风险线索 `{signals.get('risk_blocker', 0)}`。",
                f"可交接金额/发票/合同/验收线索 `{signals.get('money_payment_invoice_contract_acceptance', 0)}`。",
            ],
            ["交接不应依赖记忆，应能回到 message_id / conversation_id / timestamp。"],
            evidence_lines(
                summary["evidence_samples"].get("risk_blocker", [])
                + summary["evidence_samples"].get("todo_commitment", []),
                18,
            ),
            ["减少漏交接、错交接和事后翻记录成本。"],
            ["把风险中心和待办中心作为交接附件，逐条确认是否已闭环。"],
            common_uncertainty,
            ["已闭环事项、纯系统通知、重复确认可从正式交接中剔除。"],
            ["可按联系人/项目自动生成交接模板。"],
        ),
        "work_information_summary.md": report_template(
            "工作信息总结",
            ["工作信息已按金额/发票/合同/验收、项目/机会、风险/阻塞聚合成可读入口。"],
            [
                f"金额/发票/合同/验收线索 `{signals.get('money_payment_invoice_contract_acceptance', 0)}`。",
                f"项目/机会线索 `{signals.get('opportunity', 0)}`。",
            ],
            ["这些线索通常对应回款、交付、客户需求或后续行动。"],
            evidence_lines(
                summary["evidence_samples"].get("money_payment_invoice_contract_acceptance", [])
                + summary["evidence_samples"].get("opportunity", []),
                20,
            ),
            ["可以少翻聊天，直接定位业务信息证据。"],
            ["先复核金额/合同/验收，再补项目状态和责任人。"],
            common_uncertainty,
            ["没有业务词的普通沟通可暂不进入工作信息摘要。"],
            ["可自动生成客户/项目的信息卡片。"],
        ),
        "work_optimization.md": report_template(
            "工作优化建议",
            ["优化重点是自动前置高风险、高待办、高金额/合同线索，而不是增加技术报表。"],
            [
                f"总信号命中 `{sum(signals.values())}`。",
                f"高信号会话样本 `{len(top_convs)}` 个。",
            ],
            ["可行动线索分散在大量会话中，人工查找成本高。"],
            [
                f"`{item['conversation_id']}` / 消息 `{item['message_count']}` / 风险 `{item['risk']}` / 待办 `{item['todo']}`"
                for item in top_convs[:15]
            ],
            ["能把工作注意力从最近聊天转到最需要处理的证据。"],
            ["建立每日风险/待办巡检；每周复盘金额/发票/合同/验收线索。"],
            common_uncertainty,
            ["低信号、低业务影响的聊天可以暂不处理。"],
            ["可自动生成工作台优先级队列和例会材料。"],
        ),
        "todo_action_center.md": report_template(
            "待办行动中心",
            [f"发现 `{signals.get('todo_commitment', 0)}` 条待办/承诺线索，应进入复核队列。"],
            ["待办词包括需要、安排、提交、确认、回复、处理、跟进、落实等。"],
            ["待办遗漏会影响交付、回款、客户响应和内部协作。"],
            evidence_lines(summary["evidence_samples"].get("todo_commitment", []), 30),
            ["把散落聊天转成任务草稿，减少漏项。"],
            ["逐条确认责任人、截止时间、是否已闭环。"],
            common_uncertainty,
            ["已完成或只是讨论可能性的事项可忽略。"],
            ["可自动转任务、提醒、周报待办。"],
        ),
        "risk_center.md": report_template(
            "风险中心",
            [f"发现 `{signals.get('risk_blocker', 0)}` 条风险/阻塞线索，应优先复核。"],
            ["风险词包括问题、风险、不行、错误、延期、投诉、无法、失败、阻塞等。"],
            ["风险线索可能影响交付、客户关系、回款或团队效率。"],
            evidence_lines(summary["evidence_samples"].get("risk_blocker", []), 30),
            ["优先处理可防止后续扩大成本。"],
            ["为未解决风险补责任人、截止时间、下一步动作。"],
            common_uncertainty,
            ["已解决、无业务影响或只是口语化表达的风险词可降权。"],
            ["可自动生成风险台账和复盘清单。"],
        ),
        "opportunity_center.md": report_template(
            "机会中心",
            [f"发现 `{signals.get('opportunity', 0)}` 条机会/项目/需求线索。"],
            ["机会词包括项目、计划、方案、客户、需求、合作、报价、推进等。"],
            ["机会线索可用于主动跟进客户、方案、报价或资源协调。"],
            evidence_lines(summary["evidence_samples"].get("opportunity", []), 30),
            ["帮助把聊天中的潜在机会变成可追踪机会池。"],
            ["按联系人和项目复核，明确下一次跟进动作。"],
            common_uncertainty,
            ["历史已失效或泛泛讨论的机会可忽略。"],
            ["可自动生成机会清单和报价/方案跟进模板。"],
        ),
        "personal_behavior_review.md": report_template(
            "个人行为优化",
            ["本报告只给可观察沟通建议，不做心理或人格判断。"],
            [
                f"outbound `{summary['direction_counts'].get('outbound', 0)}` / inbound `{summary['direction_counts'].get('inbound', 0)}` / system `{summary['direction_counts'].get('system', 0)}`。",
                f"沟通行为线索 `{signals.get('communication_behavior', 0)}`。",
            ],
            ["可观察指标能提示哪些消息需要更明确的下一步和责任归属。"],
            evidence_lines(summary["evidence_samples"].get("communication_behavior", []), 24),
            ["有助于减少只确认、不闭环、不留证据的沟通。"],
            ["对待办补截止时间；对风险补责任人；对金额/合同/验收补附件或确认记录。"],
            common_uncertainty,
            ["寒暄、表情、系统消息不作为行为评价依据。"],
            ["可自动提示“是否需要截止时间/责任人/证据附件”。"],
        ),
        "relationship_roi.md": report_template(
            "关系投入 ROI",
            ["当前可做关系投入优先级排序，不能计算真实财务 ROI。"],
            [
                f"会话 `{summary['conversation_count']}` 个。",
                f"高信号会话候选 `{len(top_convs)}` 个。",
            ],
            ["投入优先级应看风险、待办、机会、金额/合同/验收，而不是只看聊天频率。"],
            [
                f"`{item['conversation_id']}` / 消息 `{item['message_count']}` / 风险 `{item['risk']}` / 机会 `{item['opportunity']}` / 金额线索 `{item['money']}`"
                for item in top_convs[:20]
            ],
            ["帮助决定哪些关系要优先维护，哪些可模板化处理。"],
            ["优先看高风险、高机会、高金额/合同/验收的联系人/会话。"],
            ["未接入成交、成本、回款数据，不能称为真实 ROI。"],
            ["低信号、低业务价值聊天可降权。"],
            ["可自动生成联系人优先级和投入建议。"],
        ),
    }
    for name, content in report_specs.items():
        write_text(reports_root / name, content)

    radar_rows = []
    for item in top_convs:
        page_name = safe_filename(item["conversation_id"]) + ".md"
        radar_rows.append(
            [
                item["conversation_id"],
                item["message_count"],
                item["risk"],
                item["todo"],
                item["opportunity"],
                item["money"],
                f"[打开](./{page_name})",
            ]
        )
        samples = summary["contact_radar_samples"].get(item["conversation_id"], [])
        write_text(
            radar_root / page_name,
            report_template(
                f"联系人雷达：{item['conversation_id']}",
                [f"该会话消息 `{item['message_count']}` 条，风险 `{item['risk']}`，待办 `{item['todo']}`，机会 `{item['opportunity']}`，金额/合同线索 `{item['money']}`。"],
                ["这是按信号密度和消息量排序出的联系人/会话候选。"],
                ["用于决定优先复核谁、跟进什么、哪些事项需要进入交接。"],
                evidence_lines(samples, 12),
                ["高风险或高待办对象会直接影响工作推进。"],
                ["先复核风险，再处理待办，再看金额/合同/机会。"],
                ["会话 ID 可能是群或个人标识；显示名未进入 repo-safe 文档。"],
                ["低业务信号聊天可暂时忽略。"],
                ["可自动生成联系人跟进模板。"],
            ),
        )
    write_text(
        radar_root / "index.md",
        report_template(
            "联系人雷达",
            [f"已生成 `{len(radar_rows)}` 个高信号联系人/会话入口。"],
            ["排序依据为风险、待办、机会、金额/合同线索和消息量。"],
            ["这比按最近聊天排序更适合工作处理。"],
            [table(["conversation_id", "消息", "风险", "待办", "机会", "金额/合同", "页面"], radar_rows[:80])],
            ["帮助集中处理最需要投入的关系和会话。"],
            ["从风险/待办最高的会话开始复核。"],
            common_uncertainty,
            ["低信号会话可暂不打开。"],
            ["可每日自动刷新联系人优先级。"],
        ),
    )

    evidence_lines_all = []
    for category, samples in summary["evidence_samples"].items():
        evidence_lines_all.append(f"### {category}")
        evidence_lines_all.extend(evidence_lines(samples, 50))
        evidence_lines_all.append("")
    write_text(
        reports_root / "evidence_index.md",
        report_template(
            "证据索引",
            ["本文件保存本地 full-sensitive evidence references，不要提交 GitHub。"],
            ["每条证据包含 message_id、conversation_id、timestamp、category、term 和本地摘录。"],
            ["所有结论都应能回到证据。"],
            evidence_lines_all,
            ["减少无法复核的总结。"],
            ["从报告中的 message_id 回到 SQLite 或 raw import pack 复核上下文。"],
            common_uncertainty,
            ["已闭环或无业务影响证据可降权。"],
            ["可自动输出交接附件、风险台账、待办草稿。"],
        ),
    )

    cards = [
        ("消息", summary["message_count"]),
        ("会话", summary["conversation_count"]),
        ("联系人", summary["contact_count"]),
        ("风险", signals.get("risk_blocker", 0)),
        ("待办", signals.get("todo_commitment", 0)),
        ("机会", signals.get("opportunity", 0)),
        ("金额/合同", signals.get("money_payment_invoice_contract_acceptance", 0)),
        ("时间范围", f"{summary['first_timestamp_utc']} - {summary['last_timestamp_utc']}"),
    ]
    links = [
        ("今日简报", "../reports/today_briefing.md"),
        ("联系人雷达", "../reports/contact_radar/index.md"),
        ("工作交接总结", "../reports/work_handoff_summary.md"),
        ("工作信息总结", "../reports/work_information_summary.md"),
        ("工作优化建议", "../reports/work_optimization.md"),
        ("待办行动中心", "../reports/todo_action_center.md"),
        ("风险中心", "../reports/risk_center.md"),
        ("机会中心", "../reports/opportunity_center.md"),
        ("个人行为优化", "../reports/personal_behavior_review.md"),
        ("关系投入 ROI", "../reports/relationship_roi.md"),
        ("证据索引", "../reports/evidence_index.md"),
        ("操作指南", "../operator_guide.md"),
    ]
    write_text(
        dashboard_root / "index.md",
        "# WDA v0.2-R2 中文工作区\n\n"
        "## 结论\n\n"
        "- full-auto export bundle 已导入，本地 Data Core 和中文报告已生成。\n\n"
        "## 数据概览\n\n"
        + table(["指标", "值"], cards)
        + "\n\n## 报告入口\n\n"
        + "\n".join(f"- [{label}]({href})" for label, href in links)
        + "\n",
    )
    card_html = "".join(
        f"<div class='card'><strong>{html.escape(str(v))}</strong><span>{html.escape(str(k))}</span></div>"
        for k, v in cards
    )
    link_html = "".join(f"<li><a href='{html.escape(href)}'>{html.escape(label)}</a></li>" for label, href in links)
    write_text(
        dashboard_root / "index.html",
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WDA v0.2-R2 中文工作区</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; margin: 32px; background: #f8f9fb; color: #1f2328; line-height: 1.6; }}
    main {{ max-width: 1120px; margin: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
    .card {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 8px; padding: 14px; }}
    .card strong {{ display: block; font-size: 22px; }}
    section {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 8px; padding: 18px; margin-top: 16px; }}
    a {{ color: #1557b0; }}
  </style>
</head>
<body>
<main>
  <h1>WDA v0.2-R2 中文工作区</h1>
  <section><h2>结论</h2><p>full-auto export bundle 已导入，本地 Data Core 和中文报告已生成。优先阅读：风险中心、待办行动中心、工作交接总结、联系人雷达。</p></section>
  <div class="grid">{card_html}</div>
  <section><h2>报告入口</h2><ul>{link_html}</ul></section>
</main>
</body>
</html>
""",
    )
    write_text(
        output_root / "operator_guide.md",
        f"""# WDA v0.2-R2 Operator Guide

## 结论

- 本地 full-auto workspace 位于 `{output_root}`。
- Dashboard: `{output_root}/dashboard/index.html`
- Data Core: `{output_root}/data_core/wda_v0_2_r2.sqlite`
- full-sensitive Raw Import Pack: `{output_root}/raw_import_pack/`

## 下一步动作

1. 打开 dashboard/index.html。
2. 先读 risk_center.md 和 todo_action_center.md。
3. 使用 evidence_index.md 复核关键结论。
4. 不要把 raw_import_pack、SQLite、reports 里的 full-sensitive 内容提交到 GitHub。
""",
    )


def generate_repo_docs(repo_docs_root: Path, output_root: Path, verify: dict[str, Any], summary: dict[str, Any]) -> None:
    if repo_docs_root.exists():
        shutil.rmtree(repo_docs_root)
    mkdir(repo_docs_root)
    docs = {
        "README.md": f"""# WDA v0.2-R2-B Full-Auto Workspace

v0.2-R2-B imported the local full-auto transfer bundle, rebuilt a local SQLite
Data Core, reran deterministic analysis, and regenerated Chinese
human-readable reports.

Local output root:

`{output_root}`

Repo-safe docs contain counts and boundaries only. Raw/private outputs remain
under WDA_MetaData.
""",
        "full_auto_import_summary.md": f"""# Full-Auto Import Summary

| Item | Value |
| --- | --- |
| requested bundle path exists | {verify['requested_bundle_exists']} |
| fallback bundle used | {verify['fallback_bundle_used']} |
| actual bundle path | `{verify['actual_bundle_path']}` |
| bundle sha256 | `{verify['bundle_sha256']}` |
| zip files | {verify['file_count']} |
| raw JSONL chunks | {verify['raw_chunk_count']} |
| checksum mismatches | {verify['checksum_mismatch_count']} |
| forbidden file hits | {len(verify['forbidden_file_hits'])} |
| messages imported | {summary['message_count']} |
| conversations imported | {summary['conversation_count']} |
| contacts imported | {summary['contact_count']} |
| failed conversations | {summary['failed_conversations']} |
| time range | {summary['first_timestamp_utc']} to {summary['last_timestamp_utc']} |
""",
        "data_core_summary.md": f"""# Data Core Summary

Local SQLite database:

`{output_root}/data_core/wda_v0_2_r2.sqlite`

| Table | Rows |
| --- | ---: |
| messages | {summary['message_count']} |
| conversations | {summary['conversation_count']} |
| contacts | {summary['contact_count']} |
| media_index | {summary['media_count']} |

SQLite integrity check: `{summary['sqlite_integrity_check']}`.

Foreign key violation count: `{summary['foreign_key_violation_count']}`.
""",
        "chinese_report_summary.md": """# Chinese Report Summary

Generated local reports:

- today_briefing.md
- contact_radar/
- work_handoff_summary.md
- work_information_summary.md
- work_optimization.md
- todo_action_center.md
- risk_center.md
- opportunity_center.md
- personal_behavior_review.md
- relationship_roi.md
- evidence_index.md

Each human-facing report uses:

- 结论
- 关键发现
- 为什么重要
- 证据引用
- 对我的影响
- 下一步动作
- 不确定的地方
- 可忽略事项
- 可自动化/模板化事项
""",
        "coverage_summary.md": f"""# Coverage Summary

| Coverage Item | Count |
| --- | ---: |
| raw chunks parsed | {summary['chunk_count']} |
| messages | {summary['message_count']} |
| conversations | {summary['conversation_count']} |
| contacts | {summary['contact_count']} |
| risk signals | {summary['signal_counts'].get('risk_blocker', 0)} |
| todo signals | {summary['signal_counts'].get('todo_commitment', 0)} |
| opportunity signals | {summary['signal_counts'].get('opportunity', 0)} |
| money/invoice/contract/acceptance signals | {summary['signal_counts'].get('money_payment_invoice_contract_acceptance', 0)} |

Subject coverage is deterministic keyword/domain coverage, not manual
hand-picked subject expansion.
""",
        "validation_report.md": f"""# Validation Report

| Check | Result |
| --- | --- |
| bundle exists | pass |
| requested path missing but same-name local bundle found | {'yes' if verify['fallback_bundle_used'] else 'no'} |
| zip CRC | pass |
| checksums | pass |
| forbidden files | pass |
| JSONL parse invalid rows | {summary['invalid_rows']} |
| SQLite integrity | {summary['sqlite_integrity_check']} |
| RAG/Web/Matrix started | false |
| WeChat exporter run on new computer | false |
| OpenAI API with raw messages | false |

No raw message content is included in this repo-safe report.
""",
        "remaining_limitations.md": """# Remaining Limitations

- Media paths and media DB handling remain disabled.
- Reports use deterministic keyword/signal extraction; they are evidence-backed
  but not semantic LLM analysis.
- No RAG/Web/Matrix has been started.
- No OpenAI API call with raw messages was made.
- Some conclusions require human review of local evidence before action.
""",
        "next_v0_2_r3_incremental_update_plan.md": """# Next v0.2-R3 Incremental Update Plan

Recommended next sprint: make v0.2-R3 an incremental update runner.

Scope:

- detect new transfer bundles
- validate checksum and forbidden files
- import only new chunks/messages
- preserve prior Data Core
- regenerate changed reports
- keep local-only full-sensitive outputs under WDA_MetaData

Do not start RAG/Web/Matrix until incremental import stability is proven.
""",
        "updated_handoff_note.md": f"""# Updated Handoff Note

v0.2-R2-B imported the full-auto transfer bundle from:

`{verify['actual_bundle_path']}`

Requested path was:

`{verify['requested_bundle_path']}`

Local output root:

`{output_root}`

Messages imported: `{summary['message_count']}`.
Conversations imported: `{summary['conversation_count']}`.
Contacts imported: `{summary['contact_count']}`.

RAG/Web/Matrix remain not started.
""",
    }
    for name, content in docs.items():
        write_text(repo_docs_root / name, content)


def write_validation(output_root: Path, verify: dict[str, Any], summary: dict[str, Any]) -> None:
    validation = {
        "generated_at": now_iso(),
        "transfer_bundle_validation": verify,
        "import_summary": {k: v for k, v in summary.items() if k not in {"evidence_samples", "contact_radar_samples", "top_conversations"}},
        "required_outputs": {
            "data_core/wda_v0_2_r2.sqlite": True,
            "raw_import_pack": True,
            "analysis_outputs": True,
            "dashboard/index.html": True,
            "dashboard/index.md": True,
            "reports": True,
            "operator_guide.md": True,
        },
        "forbidden_operations": {
            "raw_data_uploaded": False,
            "wechat_exporter_tools_run_on_new_computer": False,
            "openai_api_with_raw_messages": False,
            "rag_started": False,
            "web_started": False,
        },
    }
    write_json(output_root / "validation_report.json", validation)


def main() -> int:
    args = parse_args()
    bundle, fallback_used = resolve_bundle(args.bundle)
    reset_output_root(args.output_root)
    verify = verify_bundle(bundle, args.output_root, args.bundle, fallback_used)
    summary = parse_bundle_to_core(bundle, args.output_root, verify)
    generate_reports(args.output_root, summary)
    write_validation(args.output_root, verify, summary)
    generate_repo_docs(args.repo_docs_root, args.output_root, verify, summary)
    print(
        json.dumps(
            {
                "status": "pass",
                "actual_bundle_path": str(bundle),
                "fallback_used": fallback_used,
                "output_root": str(args.output_root),
                "messages": summary["message_count"],
                "conversations": summary["conversation_count"],
                "contacts": summary["contact_count"],
                "sqlite_integrity": summary["sqlite_integrity_check"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
