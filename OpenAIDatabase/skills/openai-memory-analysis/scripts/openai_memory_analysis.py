#!/usr/bin/env python3
"""Local-first OpenAI/ChatGPT memory analysis.

This script intentionally avoids storing full raw message text in derived
artifacts. It writes redacted memory candidates, source references, manifests,
and a rebuildable read-only index.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


UTC = timezone.utc

IMPORTANCE_HIGH = "高"
IMPORTANCE_MEDIUM = "中"
IMPORTANCE_LOW = "低"

VALIDITY_LONG = "长期"
VALIDITY_HALF_YEAR = "半年"
VALIDITY_PROJECT = "项目结束前"
VALIDITY_TEMP = "临时"

TIER_CORE = "核心画像"
TIER_MID_LONG = "一般"
TIER_SHORT = "临时"
TIER_ALIASES = {"重要中长期": TIER_MID_LONG, "一般短期": TIER_SHORT}

SENSITIVITY_RANK = {"public": 0, "private": 1, "sensitive": 2, "secret": 3}

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.I)),
    (
        "credential_assignment",
        re.compile(r"(?i)\b(password|passwd|pwd|api[_-]?key|secret|token|session|cookie)\s*[:=]\s*[^\s,;]{8,}"),
    ),
]

PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")),
]

TRIGGER_PATTERNS: dict[str, re.Pattern[str]] = {
    "answering_rule": re.compile(
        r"(默认.*回复|中文回复|以后回答|未来回答|回复格式|输出格式|每次.*输出|未来.*遵守|必须.*(验证|合同|授权|来源|测试|回滚)|不要.*(保存|回复|执行|扫描)|不应.*(保存|进入|写入)|优先.*(使用|检查|验证|读取)|少废话|可执行.*输出|证据.*来源)",
        re.I,
    ),
    "preference": re.compile(r"(偏好|请记住|记住|我希望.*(以后|每次|默认|记住)|更想要|默认.*(用|走|回复)|习惯|风格|高ROI|低Token|低上下文)", re.I),
    "decision": re.compile(r"(决定|锁定|确认.*(方案|选择|命名|授权)|命名为|以后当|作为.*(数据库|source of truth|记忆库)|授权开始|固定为|采用.*方案|删除需求|改成)", re.I),
    "project_context": re.compile(
        r"(OpenAIDatabase|Memory Vault|ChatGPT Memory|Codex|Notion Agent|Study Project|EVA[_ ]?OS|Alpha|AI-Research-System|Serenity|FIFA|QBVS|QuantLab|OpenAI.*Database|记忆数据库|记忆库|这个仓库|repo|skill|MCP)",
        re.I,
    ),
    "workflow": re.compile(r"(workflow|run contract|phase|阶段|周复盘|月复盘|ingest|增量去重|安全扫描|加密归档|测试框架|验证命令|PR流程|GitHub Actions|HANDOFF)", re.I),
    "security_boundary": re.compile(
        r"(安全扫描|安全策略|安全边界|授权边界|执行边界|隐私|secret|password|cookie|session|api key|私钥|敏感|脱敏|加密|不提交|不保存|只读|MCP|不自动登录|不抓取|不写入)",
        re.I,
    ),
    "deprecated_info": re.compile(r"(废弃|已废弃|不再|过期|替代|作废|冲突|不需要保存)", re.I),
    "temporary_or_sensitive": re.compile(
        r"(临时|一次性|今天|明天|本周|这周|下周|验证码|短信|otp|2fa|一次|暂时|退学|休学|没钱|借款|工资|账上|现金|财务紧张|催债|贷款|债务|个人借款|支付|invoice|payment)",
        re.I,
    ),
}

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？.!?])\s+|\n+|[；;]")

THEME_PROFILES: list[dict[str, Any]] = [
    {
        "name": "长期记忆数据库 / RAG / agent continuity",
        "pattern": re.compile(r"(OpenAIDatabase|长期记忆|记忆数据库|记忆库|\bRAG\b|search/fetch|MCP|personalization)", re.I),
        "meaning": "你在把聊天记录升级为可迁移、可检索、可被未来 agent 接管的长期记忆资产。",
        "do": "先把核心画像和一般候选审核成 active memory，再让未来 agent 默认先读这些资料。",
        "remember": "OpenAIDatabase 是长期记忆数据库，不是一次性报告目录。",
        "opportunity": "personal memory RAG、agent continuity、跨模型 personalization、长期项目复盘工具。",
        "growth": "减少重复解释成本，让上下文连续性变成复利资产。",
    },
    {
        "name": "Codex / agent / token / workflow 能力建设",
        "pattern": re.compile(r"(Codex|agent|token|workflow|loop|skill|side chat|CLI|offline|上下文压力)", re.I),
        "meaning": "你在系统性探索如何把 Codex 从一次性代码工具变成稳定工程与自动化执行系统。",
        "do": "沉淀 Run Contract、Task Pack、HANDOFF、验证命令和低上下文工作流。",
        "remember": "未来 Codex 协作必须高 ROI、低上下文浪费、可验证、可恢复。",
        "opportunity": "Codex skill/agent 工作流产品化、个人开发操作系统、低上下文工程交付模板。",
        "growth": "把 prompt 能力升级为工程化任务拆解、验证、交付和复盘能力。",
    },
    {
        "name": "学习系统 / Notion / Nitrosend / dashboard",
        "pattern": re.compile(r"(学习计划|Study Project|Notion|Nitrosend|dashboard|邮件|推送|PM|架构师|Architecturer)", re.I),
        "meaning": "你倾向用 GitHub/Notion/email 把学习变成可持续推进的系统，而不是零散问答。",
        "do": "把学习目标拆成项目、日课、周复盘、月复盘和自动提醒。",
        "remember": "Notion 是干净笔记本，GitHub 是 durable state，邮件推送用于维持节奏。",
        "opportunity": "学习系统模板、个人成长 OS、面向高压学习/工作人群的自动复盘工具。",
        "growth": "通过固定节奏把知识输入转成作品、项目和商业化能力。",
    },
    {
        "name": "回转窑 / 工业服务 / 动态测量调整",
        "pattern": re.compile(r"(回转窑|动态测量|工业|巡检|技术报告|点检|采购|年包|月包)", re.I),
        "meaning": "回转窑方向是你想做到行业 top 级别的垂直场景，也是 PM、架构、Codex 学习的实战载体。",
        "do": "把技术报告、巡检、动态数据报告、点检服务、材料采购支持拆成可售标准包。",
        "remember": "回转窑软件/系统可以作为 PM、架构、Codex、商业化的统一实战场景。",
        "opportunity": "工业服务标准包、动态运行数据报告系统、巡检订阅/年包、工业垂直 AI agent。",
        "growth": "用真实行业问题训练技术判断、产品设计、交付和变现能力。",
    },
    {
        "name": "金融 / 交易 / FIFA / 概率决策",
        "pattern": re.compile(r"(finance|trading|FIFA|TAB|下注|\bbet\b|概率|资金|broker|交易)", re.I),
        "meaning": "你在用概率、赔率、市场信息和模型分析训练决策系统，但需要严格安全边界。",
        "do": "把研究、回测、paper trading、真实下单授权分层，真实资金动作保持 fail-closed。",
        "remember": "金融/交易 agent 可以读取记忆和 secret_ref，但不能自动执行真实 broker/资金动作。",
        "opportunity": "概率决策工作流、体育/市场研究 agent、交易研究和风控记忆系统。",
        "growth": "训练 evidence-based decision making，避免情绪化和高风险自动化。",
    },
    {
        "name": "课程 / corporate reporting / sustainability reporting",
        "pattern": re.compile(r"(ACCT|Corporate Reporting|Sustainability|ISSB|GRI|SASB|directors'? report|remuneration|Alphabet Soup)", re.I),
        "meaning": "你有大量课程/报告框架学习需求，需要把复杂资料转成可复用笔记和考试/作业材料。",
        "do": "把课程内容沉淀成 Notion 可复制笔记、术语表、框架对比和作业素材库。",
        "remember": "课程类内容通常是项目/阶段性知识，默认进入一般或临时，不直接提升为核心画像。",
        "opportunity": "课程知识库模板、双语学习笔记、reporting framework 对比资料库。",
        "growth": "提升抽象、结构化表达和专业英文/中文转换能力。",
    },
    {
        "name": "AI 时代 / 社会影响 / 个人能力突破",
        "pattern": re.compile(r"(AI的时代|AI时代|社会|生产效率|Ultimate Goal|top1|top1%|个人能力|沟通)", re.I),
        "meaning": "你在思考 AI 普及后个人如何突破能力边界，并希望做到目标群体 top 1%。",
        "do": "把宏观思考落到可训练能力：沟通、判断、工程化、商业化、机会识别。",
        "remember": "你追求的是 ROI 最大化、个人能力成长最大化，以及在目标领域达到顶尖水平。",
        "opportunity": "AI 时代个人能力增长模型、agent-assisted learning、AI 原生工作流研究。",
        "growth": "把抽象焦虑转成可执行能力清单和作品积累。",
    },
    {
        "name": "EVA OS / 系统开发 / Task Pack",
        "pattern": re.compile(r"(EVA|Task Pack|Run Contract|PDF 报告|部署|系统|开发流程)", re.I),
        "meaning": "你偏好正式工程交付：需求、研究、Task Pack、验证、报告、ZIP/HANDOFF。",
        "do": "所有复杂项目继续走 evidence -> PRD -> Tech Spec -> Run Contract -> 验证交付。",
        "remember": "正式交付需要可运行、可验证、可维护，而不是只给方案。",
        "opportunity": "AI 原生研发流程、自动化报告系统、工程交付模板库。",
        "growth": "形成稳定的软件/系统交付方法论。",
    },
]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def from_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value), UTC)
    except (TypeError, ValueError, OSError):
        return None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix: str, text: str, length: int = 16) -> str:
    return f"{prefix}_{sha256_text(text)[:length]}"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_latest_candidate_snapshot(database_dir: Path) -> list[dict[str, Any]]:
    candidate_dir = database_dir / "data/memory/candidates"
    if not candidate_dir.exists():
        return []
    candidate_files = sorted(candidate_dir.glob("*.memory_candidates.jsonl"), key=lambda path: path.stat().st_mtime)
    for path in reversed(candidate_files):
        rows = read_jsonl(path)
        if rows:
            return rows
    return []


def load_all_candidate_snapshots(database_dir: Path) -> list[dict[str, Any]]:
    candidate_dir = database_dir / "data/memory/candidates"
    if not candidate_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(candidate_dir.glob("*.memory_candidates.jsonl"), key=lambda path: path.stat().st_mtime):
        rows.extend(read_jsonl(path))
    return rows


def append_or_merge_jsonl(path: Path, rows: list[dict[str, Any]], key_fields: list[str]) -> None:
    existing = read_jsonl(path)
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in existing + rows:
        key = tuple(row.get(k) for k in key_fields)
        merged[key] = row
    write_jsonl(path, merged.values())


def safe_zip_name(name: str) -> bool:
    p = Path(name)
    if p.is_absolute():
        return False
    return ".." not in p.parts


def redact_text(text: str) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    redacted = text

    def repl(label: str):
        def _replace(match: re.Match[str]) -> str:
            raw = match.group(0)
            digest = sha256_text(raw)[:10]
            findings.append({"type": label, "sha256_10": digest})
            return f"[REDACTED:{label}:{digest}]"

        return _replace

    for label, pattern in SECRET_PATTERNS:
        redacted = pattern.sub(repl(label), redacted)
    for label, pattern in PII_PATTERNS:
        redacted = pattern.sub(repl(label), redacted)
    return redacted, findings


def scan_text_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for label, pattern in SECRET_PATTERNS + PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            counts[label] += len(matches)
    return counts


def normalize_statement(text: str) -> str:
    text = re.sub(r"\[REDACTED:[^\]]+\]", "[redacted]", text)
    text = re.sub(r"\s+", " ", text.strip().lower())
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text[:500]


def truncate(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def flatten_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(filter(None, (flatten_content(v) for v in value)))
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("parts"), list):
            return flatten_content(value["parts"])
        if isinstance(value.get("content"), (str, list, dict)):
            return flatten_content(value["content"])
        return ""
    return ""


def iter_json_array_objects(stream: io.TextIOBase, chunk_size: int = 1024 * 1024) -> Iterable[dict[str, Any]]:
    in_array = False
    collecting = False
    in_string = False
    escape = False
    depth = 0
    buf: list[str] = []

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        for ch in chunk:
            if not in_array:
                if ch == "[":
                    in_array = True
                continue

            if not collecting:
                if ch == "{":
                    collecting = True
                    in_string = False
                    escape = False
                    depth = 1
                    buf = ["{"]
                elif ch == "]":
                    return
                continue

            buf.append(ch)
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield json.loads("".join(buf))
                    collecting = False
                    buf = []

    if collecting:
        raise ValueError("Malformed JSON array: unterminated object")


def inspect_zip(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix.lower() != ".zip":
        raise ValueError(f"Expected .zip input: {path}")

    entries: list[dict[str, Any]] = []
    unsafe_entries: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if not safe_zip_name(info.filename):
                unsafe_entries.append(info.filename)
            entries.append(
                {
                    "name": info.filename,
                    "file_size": info.file_size,
                    "compress_size": info.compress_size,
                    "is_dir": info.is_dir(),
                }
            )

    return {
        "source_filename": path.name,
        "source_path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "entry_count": len(entries),
        "entries": entries[:200],
        "entries_truncated": len(entries) > 200,
        "unsafe_entries": unsafe_entries,
        "inspected_at": isoformat(utc_now()),
    }


def copy_zip_member_to_temp(zf: zipfile.ZipFile, member: str, tmpdir: Path) -> Path:
    target = tmpdir / stable_id("nested_zip", member)
    with zf.open(member, "r") as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    return target


def is_conversations_json_name(name: str) -> bool:
    base = Path(name).name.lower()
    return base == "conversations.json" or (base.startswith("conversations-") and base.endswith(".json"))


def iter_conversations_from_export(path: Path, limit: int = 0) -> Iterable[tuple[dict[str, Any], str]]:
    yielded = 0
    with tempfile.TemporaryDirectory(prefix="oma_nested_zip_") as td:
        tmpdir = Path(td)
        with zipfile.ZipFile(path) as outer:
            for info in outer.infolist():
                if not safe_zip_name(info.filename):
                    raise ValueError(f"Unsafe ZIP entry: {info.filename}")

            direct = [i.filename for i in outer.infolist() if is_conversations_json_name(i.filename)]
            nested = [
                i.filename
                for i in outer.infolist()
                if i.filename.lower().endswith(".zip") and "conversation" in i.filename.lower()
            ]

            for member in direct:
                with outer.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8", errors="replace") as stream:
                    for obj in iter_json_array_objects(stream):
                        yield obj, f"{path.name}:{member}"
                        yielded += 1
                        if limit and yielded >= limit:
                            return

            for member in nested:
                nested_path = copy_zip_member_to_temp(outer, member, tmpdir)
                with zipfile.ZipFile(nested_path) as inner:
                    for inner_info in inner.infolist():
                        if not safe_zip_name(inner_info.filename):
                            raise ValueError(f"Unsafe nested ZIP entry: {inner_info.filename}")
                    conv_members = [i.filename for i in inner.infolist() if is_conversations_json_name(i.filename)]
                    for conv_member in conv_members:
                        with inner.open(conv_member) as raw, io.TextIOWrapper(
                            raw, encoding="utf-8", errors="replace"
                        ) as stream:
                            for obj in iter_json_array_objects(stream):
                                yield obj, f"{path.name}:{member}!{conv_member}"
                                yielded += 1
                                if limit and yielded >= limit:
                                    return


def iter_small_text_files_from_zip(path: Path, max_bytes: int = 2_000_000) -> Iterable[tuple[str, str]]:
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if not safe_zip_name(info.filename):
                raise ValueError(f"Unsafe ZIP entry: {info.filename}")
            lower = info.filename.lower()
            if info.is_dir() or info.file_size > max_bytes:
                continue
            if not lower.endswith((".md", ".txt", ".json", ".csv")):
                continue
            if any(part in lower for part in ("financial/", "payments", "invoice", "charge history")):
                continue
            with zf.open(info) as raw:
                text = raw.read(max_bytes + 1).decode("utf-8", errors="replace")
                yield info.filename, text


def extract_messages(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    mapping = conversation.get("mapping") or {}
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author") or {}
        role = author.get("role") or "unknown"
        content = message.get("content") or {}
        text = flatten_content(content)
        if not text.strip():
            continue
        created = from_timestamp(message.get("create_time")) or from_timestamp(conversation.get("create_time"))
        messages.append({"role": role, "text": text, "created_at": created, "message_id": message.get("id") or node.get("id")})
    messages.sort(key=lambda m: (m["created_at"] or datetime.min.replace(tzinfo=UTC), m.get("message_id") or ""))
    return messages


def classify_chunk(text: str) -> tuple[str, str, str, str, str]:
    categories = [name for name, pattern in TRIGGER_PATTERNS.items() if pattern.search(text)]
    temp_is_rule = bool(
        re.search(r"(不应|不要|不保存|不进入|不写入|不应进入).*?(临时|一次性|验证码|token|cookie|secret|敏感)", text, re.I)
    )
    if "temporary_or_sensitive" in categories and not temp_is_rule:
        category = "temporary_or_sensitive"
    elif "deprecated_info" in categories:
        category = "deprecated_info"
    elif "security_boundary" in categories:
        category = "security_boundary"
    elif "decision" in categories:
        category = "decision"
    elif "answering_rule" in categories:
        category = "answering_rule"
    elif "workflow" in categories:
        category = "workflow"
    elif "project_context" in categories:
        category = "project_context"
    elif "preference" in categories:
        category = "preference"
    else:
        category = "fact"

    if category in {"security_boundary", "decision", "answering_rule"}:
        importance = IMPORTANCE_HIGH
    elif category in {"workflow", "project_context", "preference", "deprecated_info"}:
        importance = IMPORTANCE_MEDIUM
    else:
        importance = IMPORTANCE_LOW

    if category == "temporary_or_sensitive":
        validity = VALIDITY_TEMP
    elif category == "project_context":
        validity = VALIDITY_PROJECT
    elif category in {"workflow", "preference"}:
        validity = VALIDITY_HALF_YEAR
    else:
        validity = VALIDITY_LONG

    trigger_score = len(categories)
    confidence = "high" if trigger_score >= 3 or importance == IMPORTANCE_HIGH else "medium" if trigger_score >= 1 else "low"

    if category == "temporary_or_sensitive":
        reason = "包含临时、一次性或敏感信息信号，应作为临时信息脱敏备份，不提升为核心画像。"
    elif category == "deprecated_info":
        reason = "包含废弃、替代或冲突修正信号，需要用于更新旧记忆。"
    elif category == "security_boundary":
        reason = "包含授权、安全或隐私边界，未来执行必须遵守。"
    elif category == "answering_rule":
        reason = "包含未来回答格式、语言或协作规则。"
    elif category == "decision":
        reason = "包含明确选择、命名、授权或锁定决策。"
    elif category == "project_context":
        reason = "包含可复用项目上下文。"
    else:
        reason = "包含可复用偏好或工作流信号。"

    return category, importance, validity, confidence, reason


def candidate_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    for raw in SENTENCE_SPLIT_RE.split(text):
        chunk = raw.strip()
        if len(chunk) < 8:
            continue
        if len(chunk) > 900:
            # Keep high-signal lines from long prompts without storing the full prompt.
            for line in chunk.splitlines():
                line = line.strip()
                if 8 <= len(line) <= 900:
                    chunks.append(line)
            continue
        chunks.append(chunk)
    return chunks


def markdown_memory_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    in_fence = False
    keep_re = re.compile(
        r"(用户偏好|用户希望|用户正在|用户明确|核心原则|不自动|不抓取|不提交|不保存|不明文|不写入|只读|人工审核|local-first|可审计|可追溯|可版本化|长期记忆|记忆库|Memory Vault|OpenAIDatabase|Codex 必须遵守)",
        re.I,
    )
    skip_re = re.compile(
        r"^(\s*#|\s*>|\s*```|\s*[{}\[\],]|\s*\"|[a-zA-Z0-9_./-]+/$|data/|src/|tests/|config/|python -m|cgmemory |test_|YYYY|memcand_|schema|properties|enum)",
        re.I,
    )
    for raw in text.splitlines():
        line = raw.strip()
        line = re.sub(r"^\s*[-*]\s+", "", line)
        if line.startswith("#") or line.startswith(">"):
            continue
        if line.endswith(("：", ":")):
            continue
        if re.match(r"^(Phase|B Phase|C Phase|Final Phase|Read-only|Final)\b", line, re.I):
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or len(line) < 12:
            continue
        if skip_re.search(line) and not keep_re.search(line):
            continue
        if keep_re.search(line):
            chunks.append(line)
    return chunks


def looks_like_code_or_config_noise(statement: str) -> bool:
    text = statement.strip()
    if re.fullmatch(r"/.+/[a-z]*", text):
        return True
    return bool(
        re.search(
            r"(console\.log\(|\bDRY_RUN\b|^\s*/\^|=>|\$\{|calendar.*\bID\b|"
            r"显式传入的\s+weights|"
            r"^\s*[-*]?\s*(const|let|var|return|if\s*\(|for\s*\(|while\s*\(|import\s+|export\s+|def\s+|class\s+))",
            text,
            re.I,
        )
    )


def make_candidate(
    *,
    chunk: str,
    source: str,
    source_kind: str,
    conversation_id: str = "",
    title: str = "",
    timestamp: datetime | None = None,
) -> dict[str, Any] | None:
    matched = [name for name, pattern in TRIGGER_PATTERNS.items() if pattern.search(chunk)]
    if not matched:
        return None
    redacted, findings = redact_text(chunk)
    statement = truncate(redacted, 420)
    if not statement or len(normalize_statement(statement)) < 8:
        return None
    if looks_like_code_or_config_noise(statement):
        category = "temporary_or_sensitive"
        importance = IMPORTANCE_LOW
        validity = VALIDITY_TEMP
        confidence = "medium"
        reason = "疑似代码、配置、日志或一次性操作片段，应低权重备份，不提升为核心画像。"
    else:
        category, importance, validity, confidence, reason = classify_chunk(statement)
    secret_types = sorted({f["type"] for f in findings if f["type"] not in {"email", "phone"}})
    secret_ref = stable_id("secretref", f"{source}:{conversation_id}:{normalize_statement(redacted)}:{','.join(secret_types)}") if secret_types else ""
    sensitivity = "secret" if secret_types else "private"
    meta_context = bool(
        re.search(
            r"(Codex|ChatGPT|OpenAIDatabase|Memory Vault|记忆数据库|记忆库|skill|MCP|Notion|Study Project|EVA|AI-Research|Serenity|FIFA|QBVS|QuantLab)",
            statement,
            re.I,
        )
    )
    if category == "temporary_or_sensitive":
        sensitivity = "sensitive" if sensitivity != "secret" else "secret"
        statement = f"短期/敏感资料已脱敏备份；redacted_source_hash={sha256_text(redacted)[:16]}。原始内容仅保留在本地加密归档引用中，不提升为核心画像。"
    elif source_kind == "openai_export" and category in {"decision", "project_context", "workflow", "deprecated_info"} and not meta_context:
        sensitivity = "sensitive"
    if category == "security_boundary" and sensitivity != "secret":
        sensitivity = "sensitive"
    date = (timestamp or utc_now()).date().isoformat()
    ident = stable_id("mem", f"{category}:{normalize_statement(statement)}")
    memory_tier = assign_memory_tier(category, validity, sensitivity, statement)
    backup_status = "backed_up_redacted_with_encrypted_raw_reference"
    if secret_ref:
        backup_status = "backed_up_redacted_secret_ref_only_with_encrypted_raw_reference"
    candidate = {
        "id": ident,
        "action": "backup",
        "date": date,
        "source": source,
        "source_kind": source_kind,
        "conversation_id": conversation_id,
        "title": truncate(title, 120),
        "category": category,
        "statement": statement,
        "importance": importance,
        "validity": validity,
        "confidence": confidence,
        "reason": reason,
        "sensitivity": sensitivity,
        "memory_tier": memory_tier,
        "backup_status": backup_status,
        "review_status": "pending",
        "evidence": [
            {
                "source": source,
                "conversation_id": conversation_id,
                "timestamp": isoformat(timestamp) if timestamp else "",
                "summary": "Matched durable-memory trigger in redacted source text.",
            }
        ],
        "security_findings": findings,
    }
    if secret_ref:
        candidate["secret_ref"] = secret_ref
        candidate["credential_policy"] = {
            "plaintext_in_git": False,
            "agent_access": "authorized_local_secret_resolver_only",
            "requires_user_authorization": True,
            "local_resolver_required": True,
            "trading_boundary": "fail_closed_for_real_broker_or_order_actions_without_current_user_approval",
        }
    return candidate


def assign_memory_tier(category: str, validity: str, sensitivity: str, statement: str) -> str:
    core_re = re.compile(r"(身份|简历|成长经历|倾向|偏好|taste|计划|规划|历史|长期目标|核心标准|默认.*回复|未来回答|协作方式)", re.I)
    if sensitivity in {"secret", "sensitive"} or validity == VALIDITY_TEMP:
        return TIER_SHORT
    if category in {"preference", "answering_rule"} or core_re.search(statement):
        return TIER_CORE
    if category in {"decision", "project_context", "workflow", "security_boundary"} or validity in {VALIDITY_LONG, VALIDITY_HALF_YEAR, VALIDITY_PROJECT}:
        return TIER_MID_LONG
    return TIER_SHORT


def merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for cand in candidates:
        key = f"{cand.get('category')}:{normalize_statement(cand.get('statement', ''))}"
        if key not in by_key:
            by_key[key] = cand
            by_key[key]["evidence_count"] = 1
            continue
        current = by_key[key]
        current["evidence"].extend(cand.get("evidence", []))
        current["evidence"] = current["evidence"][:10]
        current["evidence_count"] = current.get("evidence_count", 1) + 1
        if current["evidence_count"] >= 3 and current.get("confidence") == "medium":
            current["confidence"] = "high"
        if cand.get("importance") == IMPORTANCE_HIGH:
            current["importance"] = IMPORTANCE_HIGH
    return sorted(by_key.values(), key=lambda r: (r.get("date", ""), r.get("category", ""), r.get("id", "")))


@dataclass
class RunState:
    run_id: str
    run_dir: Path
    database_dir: Path
    input_manifests: list[dict[str, Any]] = field(default_factory=list)
    conversation_manifest: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    security_counts: Counter[str] = field(default_factory=Counter)
    archive_results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def conversation_record(conversation: dict[str, Any], messages: list[dict[str, Any]], source_ref: str, export_sha: str) -> dict[str, Any]:
    conv_id = str(conversation.get("id") or conversation.get("conversation_id") or stable_id("conv", source_ref + str(conversation.get("title", ""))))
    created = from_timestamp(conversation.get("create_time"))
    updated = from_timestamp(conversation.get("update_time")) or created
    role_counts = Counter(m["role"] for m in messages)
    content_hash = hashlib.sha256()
    for msg in messages:
        content_hash.update((msg["role"] + "\n").encode())
        content_hash.update(msg["text"].encode("utf-8", errors="ignore"))
    return {
        "conversation_id": conv_id,
        "title": truncate(str(conversation.get("title") or ""), 160),
        "created_at": isoformat(created),
        "updated_at": isoformat(updated),
        "message_count": len(messages),
        "user_message_count": role_counts.get("user", 0),
        "assistant_message_count": role_counts.get("assistant", 0),
        "content_sha256": content_hash.hexdigest(),
        "export_sha256": export_sha,
        "source_path": source_ref,
        "parsed_at": isoformat(utc_now()),
    }


def ensure_archive_key(path: Path) -> None:
    ensure_dir(path.parent)
    if not path.exists():
        path.write_text(secrets.token_urlsafe(48) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)


def encrypt_archive(input_path: Path, database_dir: Path, key_file: Path) -> dict[str, Any]:
    ensure_archive_key(key_file)
    archive_dir = ensure_dir(database_dir / "data" / "raw_encrypted" / utc_now().date().isoformat())
    source_sha = sha256_file(input_path)
    output = archive_dir / f"{input_path.name}.{source_sha[:12]}.zip.enc"
    cmd = [
        "openssl",
        "enc",
        "-aes-256-cbc",
        "-salt",
        "-pbkdf2",
        "-in",
        str(input_path),
        "-out",
        str(output),
        "-pass",
        f"file:{key_file}",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "encrypted"
        error = ""
    except subprocess.CalledProcessError as exc:
        fallback = [part for part in cmd if part != "-pbkdf2"]
        try:
            subprocess.run(fallback, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = "encrypted_without_pbkdf2"
            error = "openssl did not accept -pbkdf2; used compatibility fallback"
        except subprocess.CalledProcessError as fallback_exc:
            return {
                "source_path": str(input_path),
                "source_sha256": source_sha,
                "status": "failed",
                "error": fallback_exc.stderr.decode("utf-8", errors="replace")[:500],
            }
    result = {
        "source_path": str(input_path),
        "source_sha256": source_sha,
        "encrypted_path": str(output),
        "encrypted_sha256": sha256_file(output),
        "status": status,
        "error": error,
        "created_at": isoformat(utc_now()),
    }
    write_json(output.with_suffix(output.suffix + ".manifest.json"), result)
    return result


def process_input_zip(path: Path, state: RunState, sample_limit: int) -> None:
    manifest = inspect_zip(path)
    state.input_manifests.append(manifest)
    export_sha = manifest["sha256"]
    lower_names = [e["name"].lower() for e in manifest["entries"]]
    likely_openai_export = any("conversation" in name and name.endswith(".zip") for name in lower_names) or any(
        name.endswith("conversations.json") for name in lower_names
    )

    if likely_openai_export:
        for conversation, source_ref in iter_conversations_from_export(path, limit=sample_limit):
            messages = extract_messages(conversation)
            record = conversation_record(conversation, messages, source_ref, export_sha)
            state.conversation_manifest.append(record)
            conv_id = record["conversation_id"]
            title = record["title"]
            for msg in messages:
                text = msg["text"]
                state.security_counts.update(scan_text_counts(text))
                # User-authored messages carry the strongest signal for personal memory.
                if msg["role"] not in {"user", "tool"}:
                    continue
                for chunk in candidate_chunks(text):
                    cand = make_candidate(
                        chunk=chunk,
                        source=f"{source_ref}:conversation:{conv_id}",
                        source_kind="openai_export",
                        conversation_id=conv_id,
                        title=title,
                        timestamp=msg["created_at"],
                    )
                    if cand:
                        state.candidates.append(cand)
    else:
        for member, text in iter_small_text_files_from_zip(path):
            state.security_counts.update(scan_text_counts(text))
            for chunk in markdown_memory_chunks(text):
                cand = make_candidate(
                    chunk=chunk,
                    source=f"{path.name}:{member}",
                    source_kind="codex_pack",
                    title=member,
                    timestamp=utc_now(),
                )
                if cand:
                    state.candidates.append(cand)


def build_incremental_report(
    candidates: list[dict[str, Any]],
    active: list[dict[str, Any]],
    previous_candidates: list[dict[str, Any]] | None = None,
) -> str:
    active_keys = {normalize_statement(r.get("statement", "")): r for r in active}
    new_long = [c for c in candidates if c.get("memory_tier") in {TIER_CORE, TIER_MID_LONG}]
    safe_new_long = [c for c in new_long if c["sensitivity"] in {"public", "private"}]
    updates = [c for c in candidates if normalize_statement(c["statement"]) in active_keys]
    decisions = [c for c in candidates if c["category"] == "decision"]
    deprecated = [c for c in candidates if c["category"] == "deprecated_info"]
    rules = [c for c in candidates if c["category"] in {"answering_rule", "security_boundary"}]
    temporary = [c for c in candidates if c.get("memory_tier") == TIER_SHORT or c["sensitivity"] == "secret"]

    return "\n".join(
        [
            "# Incremental Memory Change Report",
            "",
            "本报告给用户看，重点说明记忆内容对未来决策、行动、ROI、个人成长和机会发现的影响。",
            "",
            content_conclusion_block(candidates, "本次资料"),
            "",
            previous_conclusion_comparison_block(candidates, previous_candidates, "本次资料"),
            "",
            section_memory_items("1. 新增长期记忆", new_long[:80], include_details=True),
            section_memory_items("2. 需要更新的旧记忆", updates[:80], empty="暂无；当前 active memory 为空或没有命中同义旧记忆。", include_details=True),
            section_memory_items("3. 新增决策", decisions[:80], include_details=True),
            build_delta_analysis(candidates, active),
            section_memory_items("5. 已废弃的信息", deprecated[:80], include_details=True),
            section_memory_items("6. 需要更新进 Codex 和 ChatGPT 的记忆", safe_new_long[:80], include_details=True),
            section_memory_items("7. 未来回答应遵守的规则", rules[:80], include_details=True),
            section_memory_items("8. 临时信息和敏感资料备份", temporary[:80], include_details=True),
            build_dual_agent_review(candidates, active, title="9. 双 reviewer 增量复盘"),
            "",
        ]
    )


def section_candidates(title: str, rows: list[dict[str, Any]], empty: str = "暂无。") -> str:
    lines = [f"## {title}", ""]
    if not rows:
        lines.append(empty)
        lines.append("")
        return "\n".join(lines)
    for row in rows:
        lines.append(f"- `{row['id']}` [{row['importance']}/{row['validity']}/{row['confidence']}] {row['statement']}")
        lines.append(f"  - 日期: {row['date']}; 来源: {row['source']}; 分类: {row['category']}; 原因: {row['reason']}")
    lines.append("")
    return "\n".join(lines)


def section_memory_items(
    title: str,
    rows: list[dict[str, Any]],
    empty: str = "暂无。",
    *,
    include_details: bool = False,
    limit: int | None = None,
) -> str:
    display_rows = rows[:limit] if limit is not None else rows
    lines = [f"## {title}", ""]
    if not display_rows:
        lines.append(empty)
        lines.append("")
        return "\n".join(lines)
    for row in display_rows:
        lines.append(f"- {truncate(row['statement'], 420)}")
        if include_details:
            lines.append(
                "  - "
                f"日期: {row['date']}; 来源: {truncate(row['source'], 160)}; 分类: {row['category']}; "
                f"重要性: {row['importance']}; 有效期: {row['validity']}; 置信度: {row['confidence']}; "
                f"分层: {row.get('memory_tier', '')}; 原因: {row['reason']}"
            )
    if limit is not None and len(rows) > limit:
        lines.append(f"- 另有 {len(rows) - limit} 条同类候选已写入 JSONL/Markdown 数据库。")
    lines.append("")
    return "\n".join(lines)


def compact_statement_list(rows: list[dict[str, Any]], limit: int = 12, empty: str = "暂无。") -> list[str]:
    if not rows:
        return [f"- {empty}"]
    lines = [f"- {truncate(row['statement'], 260)}" for row in rows[:limit]]
    if len(rows) > limit:
        lines.append(f"- 另有 {len(rows) - limit} 条已备份，默认通过检索按需召回。")
    return lines


def topic_theme_lines(rows: list[dict[str, Any]], empty: str = "暂无明确主题。") -> list[str]:
    if not rows:
        return [f"- {empty}"]
    matched, other = classify_theme_statements(rows)
    lines: list[str] = []
    for profile in THEME_PROFILES:
        name = profile["name"]
        statements = matched.get(name, [])
        if statements:
            lines.append(f"- {name}: {len(statements)} 条。代表内容：{truncate(statements[0], 180)}")
    if other:
        lines.append(f"- 其他待人工归类主题：{len(other)} 条。代表内容：{truncate(other[0], 180)}")
    return lines or [f"- {empty}"]


def classify_theme_statements(rows: list[dict[str, Any]]) -> tuple[dict[str, list[str]], list[str]]:
    matched: dict[str, list[str]] = {profile["name"]: [] for profile in THEME_PROFILES}
    other: list[str] = []
    for row in rows:
        statement = row.get("statement", "")
        hit = False
        for profile in THEME_PROFILES:
            if profile["pattern"].search(statement):
                matched[profile["name"]].append(statement)
                hit = True
                break
        if not hit:
            other.append(statement)
    return matched, other


def top_theme_profiles(rows: list[dict[str, Any]], limit: int = 5) -> list[tuple[dict[str, Any], int, str]]:
    matched, _ = classify_theme_statements(rows)
    ranked: list[tuple[dict[str, Any], int, str]] = []
    for profile in THEME_PROFILES:
        statements = matched.get(profile["name"], [])
        if statements:
            ranked.append((profile, len(statements), statements[0]))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]


def unique_profile_values(ranked: list[tuple[dict[str, Any], int, str]], key: str, limit: int = 6) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for profile, _, _ in ranked:
        value = profile[key]
        if value not in seen:
            values.append(value)
            seen.add(value)
        if len(values) >= limit:
            break
    return values


def content_conclusion_block(rows: list[dict[str, Any]], scope_label: str = "本次资料") -> str:
    ranked = top_theme_profiles(rows, limit=6)
    core = [c for c in rows if c.get("memory_tier") == TIER_CORE]
    decisions = [c for c in rows if c.get("category") == "decision"]
    rules = [c for c in rows if c.get("category") in {"answering_rule", "security_boundary"}]
    conflicts = [c for c in rows if c.get("category") == "deprecated_info"]

    lines = [
        f"## {scope_label}内容结论",
        "",
        "以下结论根据记忆资料内容本身生成，用来判断主题、行动、机会和成长方向；处理流程和数据库状态放在后面。",
        "",
        "### 1. 这批记忆说明的核心叙事",
        "",
    ]
    if ranked:
        for profile, count, example in ranked:
            lines.append(f"- {profile['name']}：{count} 条。结论：{profile['meaning']} 代表记忆：{truncate(example, 160)}")
    else:
        lines.append("- 暂无足够稳定的内容主题，先保留为低权重候选。")

    lines += ["", "### 2. 需要做什么", ""]
    actions = unique_profile_values(ranked, "do", limit=6)
    if core:
        actions.insert(0, "先人工审核核心画像，避免把短期噪音当成长期身份。")
    if decisions:
        actions.append("把明确决策写入 Decision Log，后续默认执行，减少重复确认。")
    lines.extend([f"- {item}" for item in actions[:7]] or ["- 暂无明确行动；先继续收集和人工审核。"])

    lines += ["", "### 3. 需要记得做什么", ""]
    remembers = unique_profile_values(ranked, "remember", limit=6)
    if rules:
        remembers.append("未来助手必须先遵守已记录的回答规则、安全边界和授权边界。")
    lines.extend([f"- {item}" for item in remembers[:7]] or ["- 暂无可提升为长期记忆的稳定规则。"])

    lines += ["", "### 4. 建议做什么", ""]
    lines += [
        "- 把内容主题分为：立即行动、长期能力建设、潜在业务/投资机会、只需低权重保留四类。",
        "- 对高频主题建立 Project Index；对明确选择建立 Decision Log；对成长目标建立 Timeline。",
        "- 每次周/月复盘都先看内容结论，再看数据库状态。",
    ]

    lines += ["", "### 5. 潜在发展 / 投资 / 业务机会", ""]
    opportunities = unique_profile_values(ranked, "opportunity", limit=6)
    lines.extend([f"- {item}" for item in opportunities] or ["- 暂无足够明确的机会信号。"])

    lines += ["", "### 6. 个人能力成长信号", ""]
    growth = unique_profile_values(ranked, "growth", limit=6)
    lines.extend([f"- {item}" for item in growth] or ["- 暂无足够明确的能力成长信号。"])

    if conflicts:
        lines += ["", "### 7. 需要谨慎对待的信息", ""]
        lines.append("- 存在冲突/过时候选，必须先人工确认替换关系，避免让旧信息继续影响判断。")
    return "\n".join(lines)


def theme_count_map(rows: list[dict[str, Any]]) -> dict[str, int]:
    matched, other = classify_theme_statements(rows)
    counts = {name: len(statements) for name, statements in matched.items() if statements}
    if other:
        counts["其他待人工归类主题"] = len(other)
    return counts


def previous_conclusion_comparison_block(
    current_rows: list[dict[str, Any]],
    previous_rows: list[dict[str, Any]] | None,
    scope_label: str = "本次资料",
) -> str:
    lines = [f"## {scope_label}与上一轮结论对比", ""]
    if not previous_rows:
        lines += [
            "- 未找到上一轮候选基线；本轮作为后续对比的 baseline。",
            "- 下一轮起必须对比主题变化、决策变化、规则变化、机会变化和短期噪音变化。",
            "",
        ]
        return "\n".join(lines)

    current_counts = theme_count_map(current_rows)
    previous_counts = theme_count_map(previous_rows)
    current_keys = set(current_counts)
    previous_keys = set(previous_counts)
    added = sorted(current_keys - previous_keys)
    removed = sorted(previous_keys - current_keys)
    strengthened = sorted(
        (key for key in current_keys & previous_keys if current_counts[key] > previous_counts[key]),
        key=lambda key: current_counts[key] - previous_counts[key],
        reverse=True,
    )
    weakened = sorted(
        (key for key in current_keys & previous_keys if current_counts[key] < previous_counts[key]),
        key=lambda key: previous_counts[key] - current_counts[key],
        reverse=True,
    )

    previous_statements = {normalize_statement(row.get("statement", "")) for row in previous_rows}
    new_decisions = [
        row
        for row in current_rows
        if row.get("category") == "decision" and normalize_statement(row.get("statement", "")) not in previous_statements
    ]
    new_rules = [
        row
        for row in current_rows
        if row.get("category") in {"answering_rule", "security_boundary"}
        and normalize_statement(row.get("statement", "")) not in previous_statements
    ]
    current_short = sum(1 for row in current_rows if row.get("memory_tier") == TIER_SHORT or row.get("sensitivity") == "secret")
    previous_short = sum(1 for row in previous_rows if row.get("memory_tier") == TIER_SHORT or row.get("sensitivity") == "secret")

    lines.append(f"- 上一轮候选 {len(previous_rows)} 条；本轮候选 {len(current_rows)} 条。")
    if added:
        lines.append("- 新增主题：" + "；".join(f"{name}（{current_counts[name]} 条）" for name in added[:6]))
    else:
        lines.append("- 新增主题：暂无明显新增主题，主要是在既有方向上继续加深。")
    if strengthened:
        lines.append(
            "- 明显增强主题："
            + "；".join(
                f"{name}（{previous_counts[name]} -> {current_counts[name]}）" for name in strengthened[:6]
            )
        )
    if weakened:
        lines.append(
            "- 本轮少出现主题："
            + "；".join(f"{name}（{previous_counts[name]} -> {current_counts[name]}）" for name in weakened[:6])
        )
    if removed:
        lines.append("- 本轮未继续出现主题：" + "；".join(f"{name}（上轮 {previous_counts[name]} 条）" for name in removed[:6]))
    lines.append(f"- 新增决策候选：{len(new_decisions)} 条；新增规则/边界候选：{len(new_rules)} 条。")
    lines.append(f"- 临时/敏感候选变化：{previous_short} -> {current_short}。")
    lines.append("- 结论更新：报告必须把这些变化转成用户可执行的行动、要记住的上下文、机会判断和风险提醒，而不是只列数据库状态。")
    lines.append("")
    return "\n".join(lines)


def build_delta_analysis(candidates: list[dict[str, Any]], active: list[dict[str, Any]]) -> str:
    core = [c for c in candidates if c.get("memory_tier") == TIER_CORE]
    mid_long = [c for c in candidates if c.get("memory_tier") == TIER_MID_LONG]
    short = [c for c in candidates if c.get("memory_tier") == TIER_SHORT]
    projects = [c for c in candidates if c["category"] == "project_context"]
    workflows = [c for c in candidates if c["category"] == "workflow"]
    rules = [c for c in candidates if c["category"] in {"answering_rule", "security_boundary"}]
    secret_refs = [c for c in candidates if c.get("secret_ref")]
    lines = [
        "## 4. 分析增量变化",
        "",
        f"- 本次共形成 {len(candidates)} 条候选：核心画像 {len(core)} 条，一般 {len(mid_long)} 条，临时 {len(short)} 条。",
        f"- 相比现有 active memory：当前 active {len(active)} 条；本轮重点仍是把候选整理成可长期使用的 active memory。",
    ]
    if projects:
        lines.append(f"- 新主题集中在项目/长期上下文：{len(projects)} 条，适合沉淀到 Project Index 和未来 RAG。")
    if workflows:
        lines.append(f"- 工作流/执行体系出现 {len(workflows)} 条，说明重复解释成本较高，应优先固化为标准流程。")
    if rules:
        lines.append(f"- 回答规则/安全边界出现 {len(rules)} 条，未来 agent 应优先读取并遵守。")
    if secret_refs:
        lines.append(f"- 检测到 {len(secret_refs)} 条 secret_ref 需求；已保存红线和授权入口，但未保存明文 secret。")
    lines += [
        "- 新机会：把记忆数据库从聊天记录归档升级为 personal RAG、agent continuity、项目复盘和个人能力增长系统。",
        "- 新风险：如果不人工去噪，短期/敏感记录会拉低 personalization 质量；如果上传明文 secret，会扩大金融和交易风险。",
        "",
    ]
    return "\n".join(lines)


def build_weekly_report(
    candidates: list[dict[str, Any]],
    week_start: datetime,
    previous_candidates: list[dict[str, Any]] | None = None,
) -> str:
    week_end = week_start + timedelta(days=7)

    def in_week(c: dict[str, Any]) -> bool:
        try:
            d = datetime.fromisoformat(c["date"]).replace(tzinfo=UTC)
            return week_start.date() <= d.date() < week_end.date()
        except ValueError:
            return False

    weekly = [c for c in candidates if in_week(c)]
    if not weekly:
        weekly = candidates[:80]
    decisions = [c for c in weekly if c["category"] == "decision"]
    rules = [c for c in weekly if c["category"] in {"answering_rule", "security_boundary"}]
    preferences = [c for c in weekly if c["category"] == "preference"]
    projects = [c for c in weekly if c["category"] == "project_context"]
    workflows = [c for c in weekly if c["category"] == "workflow"]
    conflicts = [c for c in weekly if c["category"] == "deprecated_info"]
    temp = [c for c in weekly if c.get("memory_tier") == TIER_SHORT or c["sensitivity"] == "secret"]
    safe_context = [c for c in weekly if c["validity"] != VALIDITY_TEMP and c["sensitivity"] in {"public", "private"}]

    return "\n".join(
        [
            f"# Weekly Memory Pack - {week_start.date().isoformat()}",
            "",
            "本周复盘面向用户决策、ROI、个人能力成长和机会发现，不是 agent 维护日志。",
            "",
            content_conclusion_block(weekly, "本周资料"),
            "",
            previous_conclusion_comparison_block(weekly, previous_candidates, "本周资料"),
            "",
            "## 1. 本周核心事件",
            "",
            *weekly_core_event_lines(weekly, projects, workflows, rules, temp),
            "",
            "## 2. 本周重要决策",
            "",
            *compact_statement_list(decisions, 12, "暂无明确新决策。"),
            "",
            "## 3. 本周反复出现的问题",
            "",
            *weekly_repeated_problem_lines(workflows, conflicts, temp),
            "",
            "## 4. 本周新偏好",
            "",
            *compact_statement_list(preferences, 12, "暂无明确新偏好。"),
            "",
            "## 5. 本周项目进展",
            "",
            *topic_theme_lines(projects, "暂无明确项目进展。"),
            "",
            "## 6. 本周需要 ChatGPT 未来记住的上下文",
            "",
            compact_context_pack(safe_context[:40]),
            "",
            "## 7. 本周临时信息和敏感资料备份",
            "",
            f"- 本周临时/敏感资料 {len(temp)} 条，已保留脱敏摘要和本地加密归档引用。",
            "- 使用方式：默认低权重召回，不进入核心画像；只有未来任务明确相关时再通过 search/fetch 或人工审核调用。",
            "",
            "## 8. 与旧记忆冲突的地方",
            "",
            *compact_statement_list(conflicts, 12, "暂无明确冲突；仍需人工审核候选质量。"),
            "",
            "## 9. 下周行动清单",
            "",
            "- 高 ROI / 高信心：先审核核心画像和一般候选，生成第一版可用 `active_memory`。",
            "- 高 ROI / 中信心：建立 Project Index、Decision Log、Timeline，让未来 agent 快速接管项目上下文。",
            "- 中 ROI / 高信心：把 weekly/monthly 复盘作为个人成长和机会发现仪表盘，而不是只做数据库维护。",
            "- 中 ROI / 中信心：为 finance/trading agent 建立 `secret_ref` 到本地 secret resolver 的授权流程，真实交易继续 fail-closed。",
            "",
            build_dual_agent_review(weekly, [], title="10. 双 reviewer 周复盘补充"),
            "",
        ]
    )


def weekly_core_event_lines(
    weekly: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    temp: list[dict[str, Any]],
) -> list[str]:
    lines = [
        f"- 本周处理/识别到 {len(weekly)} 条记忆候选，其中项目上下文 {len(projects)} 条、工作流 {len(workflows)} 条、规则/边界 {len(rules)} 条、临时/敏感 {len(temp)} 条。",
    ]
    if projects:
        lines.append("- 核心变化：长期记忆数据库和项目续接上下文继续成为高价值主题，应进入 Project Index。")
    if workflows:
        lines.append("- 执行变化：工作流、复盘、归档、RAG/search/fetch 等内容反复出现，说明值得固化为可复用流程。")
    if rules:
        lines.append("- 协作变化：未来回答规则和安全边界需要成为每个 agent 的启动上下文。")
    if temp:
        lines.append("- 资料处理变化：短期/敏感内容不删除，但降权、脱敏、加密引用，避免污染长期画像。")
    return lines


def weekly_repeated_problem_lines(
    workflows: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    temp: list[dict[str, Any]],
) -> list[str]:
    lines = []
    if workflows:
        lines.append("- 反复问题：同类执行标准需要多次解释，说明 active memory 和标准 workflow 还不够成型。")
    if conflicts:
        lines.append("- 反复问题：存在旧认知/新认知冲突，需要用 Decision Log 和 Deprecated Memory 明确替换关系。")
    if len(temp) > 20:
        lines.append("- 反复问题：短期/敏感资料数量较多，需要避免直接提升为核心画像，防止长期记忆噪音。")
    if not lines:
        lines.append("- 暂无明显重复问题；下一步重点是人工审核候选质量。")
    return lines


def build_monthly_report(
    candidates: list[dict[str, Any]],
    month: str,
    previous_candidates: list[dict[str, Any]] | None = None,
) -> str:
    month_rows = [c for c in candidates if c.get("date", "").startswith(month)] or candidates[:120]
    active_like = [c for c in month_rows if c.get("memory_tier") in {TIER_CORE, TIER_MID_LONG} and c["sensitivity"] in {"public", "private"}]
    core = [c for c in month_rows if c.get("memory_tier") == TIER_CORE]
    mid_long = [c for c in month_rows if c.get("memory_tier") == TIER_MID_LONG]
    short = [c for c in month_rows if c.get("memory_tier") == TIER_SHORT]
    deprecated = [c for c in month_rows if c["category"] == "deprecated_info"]
    decisions = [c for c in month_rows if c["category"] == "decision"]
    projects = [c for c in month_rows if c["category"] == "project_context"]
    timeline = sorted(month_rows, key=lambda c: (c.get("date", ""), c.get("id", "")))[:80]
    return "\n".join(
        [
            f"# Monthly Memory Pack - {month}",
            "",
            "本月复盘面向用户的长期画像、能力成长、项目组合、机会地图和决策质量，不是 agent 维护日志。",
            "",
            content_conclusion_block(month_rows, "本月资料"),
            "",
            previous_conclusion_comparison_block(month_rows, previous_candidates, "本月资料"),
            "",
            "## 1. Core Profile Memories",
            "",
            *compact_statement_list(core, 40, "暂无足够明确的核心画像候选。"),
            "",
            "## 2. Important Mid/Long-term Memories",
            "",
            *topic_theme_lines(mid_long, "暂无一般候选。"),
            "",
            "## 3. Temporary Memories",
            "",
            f"- 本月临时/敏感/低确定性资料 {len(short)} 条，已脱敏备份并保留本地加密原文引用。",
            "- 未来使用方式：不默认进入 personalization；仅在相关项目、金融/交易、学习或安全边界任务中按需召回。",
            "",
            "## 4. Deprecated/Conflicting Memories",
            "",
            *compact_statement_list(deprecated, 20, "暂无明确冲突；请继续通过人工审核确认旧记忆替换关系。"),
            "",
            "## 5. Updated Profile",
            "",
            *monthly_profile_lines(core, active_like),
            "",
            "## 6. Updated Project Index",
            "",
            *topic_theme_lines(projects, "暂无明确项目索引更新。"),
            "",
            "## 7. Updated Decision Log",
            "",
            *compact_statement_list(decisions, 30, "暂无明确新增决策。"),
            "",
            "## 8. Updated Timeline",
            "",
            *timeline_lines(timeline, 50),
            "",
            "## 9. 适合上传到 ChatGPT Project 的 compact context pack",
            "",
            compact_context_pack(active_like[:40]),
            "",
            build_dual_agent_review(month_rows, [], title="10. 双 reviewer 月复盘补充"),
            "",
        ]
    )


def monthly_profile_lines(core: list[dict[str, Any]], active_like: list[dict[str, Any]]) -> list[str]:
    if not core and not active_like:
        return ["- 暂无足够明确的 profile 更新。"]
    lines = [
        f"- 本月可用于画像/长期上下文的候选共 {len(active_like)} 条，其中核心画像 {len(core)} 条。",
        "- 用户长期偏好应继续围绕：高 ROI、可执行、低上下文浪费、真实验证、长期记忆续接、个人能力增长和机会发现。",
    ]
    if core:
        lines.extend(compact_statement_list(core, 12))
    return lines


def timeline_lines(rows: list[dict[str, Any]], limit: int = 40) -> list[str]:
    if not rows:
        return ["- 暂无可用时间线。"]
    lines = [f"- {row['date']}: {truncate(row['statement'], 260)}" for row in rows[:limit]]
    if len(rows) > limit:
        lines.append(f"- 另有 {len(rows) - limit} 条时间线事件已写入数据库。")
    return lines


def compact_context_pack(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "暂无可上传 compact context。"
    lines = ["以下为 pending 候选的脱敏 compact context，上传前仍需人工审核："]
    for row in rows:
        lines.append(f"- [{row['category']}/{row['importance']}/{row['validity']}] {truncate(row['statement'], 320)}")
    return "\n".join(lines)


def build_dual_agent_review(candidates: list[dict[str, Any]], active: list[dict[str, Any]], title: str = "Dual Reviewer Memory Analysis") -> str:
    core = [c for c in candidates if c.get("memory_tier") == TIER_CORE]
    mid_long = [c for c in candidates if c.get("memory_tier") == TIER_MID_LONG]
    short = [c for c in candidates if c.get("memory_tier") == TIER_SHORT]
    projects = [c for c in candidates if c.get("category") == "project_context"]
    workflows = [c for c in candidates if c.get("category") == "workflow"]
    rules = [c for c in candidates if c.get("category") in {"answering_rule", "security_boundary"}]
    decisions = [c for c in candidates if c.get("category") == "decision"]
    conflicts = [c for c in candidates if c.get("category") == "deprecated_info"]
    secret_refs = [c for c in candidates if c.get("secret_ref")]

    lines = [
        f"## {title}",
        "",
        "### Reviewer A - 战略 / 机会 / ROI 视角",
        "",
        f"- 最高价值资产不是原始聊天记录，而是可检索、可迁移、可被 agent 接管的三层记忆库；本轮核心画像 {len(core)} 条、一般 {len(mid_long)} 条，应该优先转成 active memory。",
    ]
    if projects or workflows:
        lines.append("- 机会角度：OpenAIDatabase 可以从个人备份扩展为 personal RAG、agent continuity、项目复盘、学习系统和能力增长 OS。")
    if secret_refs:
        lines.append("- 金融/交易角度：finance/trading agent 需要知道凭证存在和授权边界，但不能依赖 GitHub 明文 secret；应建设 `secret_ref -> local resolver -> user approval` 的闭环。")
    if decisions:
        lines.append(f"- 决策角度：本轮出现 {len(decisions)} 条决策候选，应进入 Decision Log，减少未来重复确认成本。")
    lines += [
        "- 投资/业务角度：长期记忆、跨 agent personalization、垂直行业 agent、金融/交易安全授权层，都是可继续验证的高杠杆方向。",
        "- 个人成长角度：每周看重复问题，每月看画像/项目/机会地图，比单纯保存对话更能提高 ROI。",
        "",
        "### Reviewer B - 执行 / 质量 / 遗漏 视角",
        "",
        f"- 数据质量重点：本轮临时 {len(short)} 条，必须备份但默认降权，避免短期噪音污染长期画像。",
        f"- 规则质量重点：本轮规则/边界 {len(rules)} 条，需要同步到 README、AGENTS、skill 和 future context pack。",
    ]
    if conflicts:
        lines.append(f"- 冲突处理：发现 {len(conflicts)} 条过时/冲突候选，需要在 Deprecated/Conflicting Memory 中写清替换关系。")
    if not active:
        lines.append("- 最大遗漏：active memory 仍需要人工审核成正式版；没有 active memory，未来 agent 只能使用 pending 候选，置信度和可用性会下降。")
    lines += [
        "- 安全遗漏检查：不能为了金融/交易 agent 方便而把 API key、broker token、session、private key 或 `.env` 明文上传 GitHub。",
        "- 可继续优化：生成 Project Index、Decision Log、Timeline、Personalization Pack，并为 search/fetch 加上更明确的召回权重。",
        "",
        "### 两次复盘合并后的默认建议",
        "",
        "- 第一优先级：审核核心画像和一般候选，生成第一版 active memory。",
        "- 第二优先级：把项目、决策、时间线和机会主题结构化，供未来 agent/RAG 使用。",
        "- 第三优先级：建立 secret_ref 授权流程，支持 finance/trading agent，但真实交易继续 fail-closed。",
        "",
    ]
    return "\n".join(lines)


def build_context_pack(candidates: list[dict[str, Any]], title: str) -> str:
    usable = [c for c in candidates if c.get("memory_tier") in {TIER_CORE, TIER_MID_LONG} and c["sensitivity"] in {"public", "private"}]
    return "\n".join(
        [
            f"# {title}",
            "",
            "注意：以下内容由本地脚本生成，默认仍为 pending，需要人工审核后再写入长期记忆。",
            "",
            compact_context_pack(usable[:120]),
            "",
        ]
    )


def build_human_memory_review(
    candidates: list[dict[str, Any]],
    active: list[dict[str, Any]],
    previous_candidates: list[dict[str, Any]] | None = None,
) -> str:
    core = [c for c in candidates if c.get("memory_tier") == TIER_CORE]
    mid_long = [c for c in candidates if c.get("memory_tier") == TIER_MID_LONG]
    short = [c for c in candidates if c.get("memory_tier") == TIER_SHORT]
    sensitive = [c for c in candidates if c.get("sensitivity") not in {"public", "private"}]
    rules = [c for c in candidates if c.get("category") in {"security_boundary", "answering_rule"}]
    decisions = [c for c in candidates if c.get("category") == "decision"]
    workflows = [c for c in candidates if c.get("category") == "workflow"]
    projects = [c for c in candidates if c.get("category") == "project_context"]
    conflicts = [c for c in candidates if c.get("category") == "deprecated_info"]

    lines = [
        "# Human Memory Review",
        "",
        "本报告面向用户决策、ROI、个人成长和机会发现。所有资料都已处理为可备份记忆候选；短期/敏感内容保留脱敏摘要和本地加密原文引用，不删除历史。",
        "",
        content_conclusion_block(candidates, "本次资料"),
        "",
        previous_conclusion_comparison_block(candidates, previous_candidates, "本次资料"),
        "",
        "## 1. 本次资料里的主要话题",
        "",
    ]
    topic_lines = []
    if projects:
        topic_lines.append(f"- 记忆数据库和项目上下文：{len(projects)} 条。重点是 OpenAIDatabase、ChatGPT/Codex 记忆、只读检索和长期续接。")
    if workflows:
        topic_lines.append(f"- 工作流和执行体系：{len(workflows)} 条。重点是阶段推进、归档、解析、复盘、RAG/search/fetch。")
    if rules:
        topic_lines.append(f"- 安全边界和未来协作规则：{len(rules)} 条。重点是不自动登录、不抓 UI、不写 ChatGPT Memory、只读 MCP。")
    if short:
        topic_lines.append(f"- 临时/敏感资料：{len(short)} 条。已提炼为脱敏摘要并保留加密归档引用，不提升为核心画像。")
    lines.extend(topic_lines or ["- 暂无高信号主题。"])

    lines += ["", "## 2. 三层记忆分级", ""]
    lines += [
        f"- 核心画像：{len(core)} 条。身份、简历、成长经历、倾向、偏好、Taste、计划、规划、历史等最根本信息。",
        f"- 一般：{len(mid_long)} 条。项目、决策、长期工作流、阶段性目标、稳定约束。",
        f"- 临时：{len(short)} 条。具体事件、敏感细节、短期上下文、低确定性内容；保留脱敏摘要和加密原文引用。",
    ]

    lines += ["", "## 3. 需要记得做什么", ""]
    lines += [
        "- 把 OpenAIDatabase 当作长期记忆数据库，而不是一次性报告目录。",
        "- 所有新资料都要经过提取、脱敏、分层、备份、索引，不能简单丢弃。",
        "- 把核心画像和一般记忆提供给未来 agent 做 personalization 和 RAG。",
        "- 临时资料保留为低权重检索资料，只在相关任务中召回。",
    ]

    lines += ["", "## 4. 建议做什么", ""]
    lines += [
        "- 先人工审核核心画像和一般候选，建立第一版 `active_memory.jsonl`。",
        "- 为每条 active memory 增加 `tier`、`source`、`use_when`、`do_not_use_for` 字段。",
        "- 以月为单位维护 Project Index、Decision Log、Timeline，避免记忆变成碎片。",
        "- 给未来 agent 一个固定入口：先读 README、AGENTS、USER_REQUIREMENTS、active memory，再 search/fetch。",
    ]

    lines += ["", "## 5. 本次需要写入 personalization / core memory 的内容", ""]
    if core:
        for row in core[:20]:
            lines.append(f"- {truncate(row['statement'], 300)}")
    else:
        lines.append("- 本轮没有足够明确的身份/简历/成长经历/Taste/长期偏好类核心画像候选。")

    lines += ["", "## 6. 本次一般记忆", ""]
    if mid_long:
        lines.extend(topic_theme_lines(mid_long))
    else:
        lines.append("- 暂无一般候选。")

    lines += ["", "## 7. 本次临时信息怎么处理", ""]
    if short:
        lines += [
            f"- 本次共有 {len(short)} 条临时/敏感资料。",
            "- 处理方式：不删除、不丢弃；保存脱敏摘要，原文只通过本地加密归档引用保留。",
            "- 使用方式：默认不进入 personalization；只有当未来任务明确相关时，通过 RAG/search 低权重召回。",
        ]
    else:
        lines.append("- 暂无临时候选。")

    lines += ["", "## 8. 新增决策", ""]
    if decisions:
        for row in decisions[:20]:
            lines.append(f"- {row['statement']}")
    else:
        lines.append("- 暂无明确新增决策。")

    lines += ["", "## 9. 冲突、过时或需要纠错的信息", ""]
    if conflicts:
        for row in conflicts[:10]:
            lines.append(f"- 待人工确认：{row['statement']}")
    else:
        lines.append("- 暂无明确冲突。")

    lines += ["", "## 10. 未来回答应遵守的规则", ""]
    if rules:
        for row in rules[:20]:
            lines.append(f"- {row['statement']}")
    else:
        lines.append("- 继续遵守本地优先、人工审核、敏感信息不外发、不自动写入 ChatGPT Memory。")

    lines += ["", "## 11. ROI 最大化建议", ""]
    lines += [
        "- 所有历史都备份，但只有核心画像和一般进入高权重 personalization/RAG。",
        "- 把重复解释成本最高的内容优先沉淀为 active memory。",
        "- 对敏感业务/财务/个人压力信息保留脱敏摘要和加密引用，不让原文污染长期身份叙事。",
        "- 优先建设 search/fetch、Project Index、Decision Log、Timeline，因为这些能让未来 agent 更快接管。",
    ]

    lines += ["", "## 12. 个人能力成长建议", ""]
    lines += [
        "- 建立固定复盘节奏：每周看模式和行动，每月更新画像、项目索引和决策日志。",
        "- 用记忆数据库追踪反复出现的问题，而不是只保存聊天记录。",
        "- 把机会分成：短期可执行、长期能力建设、需要外部资源验证三类。",
        "- 对高压力或高敏话题，只提炼行动和风险，不把情绪原文变成长期身份叙事。",
    ]

    lines += ["", "## 13. 潜在发展 / 投资机会", ""]
    lines += [
        "- 个人记忆数据库产品化：把 ChatGPT/Codex export 变成可审计、可检索、可迁移的长期记忆资产。",
        "- AI agent continuity 基础设施：面向多 agent 接管、RAG、personalization、项目复盘和学习系统。",
        "- 个人能力增长 OS：用长期记忆识别重复问题、能力缺口、机会主题和下一步行动。",
        "- 数据安全工具链：本地加密归档、敏感内容分层、只读检索、人工审核 gate。",
    ]

    lines += ["", "## 14. 本次处理质量", ""]
    lines += [
        f"- 总候选：{len(candidates)}。",
        f"- 核心画像：{len(core)}。",
        f"- 一般：{len(mid_long)}。",
        f"- 临时：{len(short)}。",
        f"- 敏感/需谨慎使用：{len(sensitive)}。",
    ]

    lines += ["", build_dual_agent_review(candidates, active, title="15. 双 reviewer 复盘补充")]

    return "\n".join(lines) + "\n"


def build_candidates_markdown(candidates: list[dict[str, Any]]) -> str:
    lines = ["# Memory Update Candidates", ""]
    if not candidates:
        lines += ["暂无候选。", ""]
        return "\n".join(lines)
    for cand in candidates:
        lines += [
            f"## Candidate: {cand['id']}",
            "",
            f"- Action: {cand['action']}",
            f"- Date: {cand['date']}",
            f"- Source: {cand['source']}",
            f"- Category: {cand['category']}",
            f"- Importance: {cand['importance']}",
            f"- Validity: {cand['validity']}",
            f"- Memory tier: {cand.get('memory_tier', '')}",
            f"- Backup status: {cand.get('backup_status', '')}",
            f"- Confidence: {cand['confidence']}",
            f"- Sensitivity: {cand['sensitivity']}",
            f"- Review status: {cand['review_status']}",
            f"- Reason: {cand['reason']}",
        ]
        if cand.get("secret_ref"):
            lines += [
                f"- Secret ref: {cand['secret_ref']}",
                "- Secret policy: plaintext is not stored in GitHub; authorized local resolver required.",
            ]
        lines += [
            "",
            "### Proposed memory",
            "",
            cand["statement"],
            "",
            "### Reviewer decision",
            "",
            "- [ ] Accept",
            "- [ ] Edit",
            "- [ ] Reject",
            "",
        ]
    return "\n".join(lines)


def load_curation_overrides(database_dir: Path | None) -> dict[str, dict[str, Any]]:
    if database_dir is None:
        return {}
    path = database_dir / "data/memory/curation/core_profile_review.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    overrides = data.get("overrides", {})
    return overrides if isinstance(overrides, dict) else {}


def apply_curation_override(row: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> bool:
    override = overrides.get(row.get("id", ""))
    if not override:
        return False
    original_statement = row.get("statement", "")
    for field in ["statement", "category", "importance", "validity", "confidence", "reason", "memory_tier", "sensitivity", "backup_status"]:
        if field in override:
            row[field] = override[field]
    row["curation_status"] = override.get("status", "reviewed")
    row["curation_reason"] = override.get("review_reason", "")
    if original_statement and original_statement != row.get("statement", ""):
        row["original_statement_hash"] = sha256_text(original_statement)[:16]
    return True


def retrieval_weight(row: dict[str, Any]) -> str:
    tier = normalized_memory_tier(row)
    if tier == TIER_CORE:
        return "high"
    if tier == TIER_MID_LONG:
        return "medium"
    return "low"


def normalized_memory_tier(row: dict[str, Any]) -> str:
    if looks_like_code_or_config_noise(row.get("statement", "")):
        return TIER_SHORT
    tier = TIER_ALIASES.get(row.get("memory_tier"), row.get("memory_tier"))
    if tier in {TIER_CORE, TIER_MID_LONG, TIER_SHORT}:
        return tier
    return assign_memory_tier(
        row.get("category", "fact"),
        row.get("validity", VALIDITY_TEMP),
        row.get("sensitivity", "private"),
        row.get("statement", ""),
    )


def active_use_when(row: dict[str, Any]) -> str:
    tier = row.get("memory_tier")
    if tier == TIER_CORE:
        return "Use as high-weight personalization, durable preference, identity/profile context, or default collaboration rule."
    if tier == TIER_MID_LONG:
        return "Use when the task touches this project, workflow, decision, opportunity, or reusable context."
    return "Use only when directly relevant to the current task or retrieved by search/fetch; keep low-weight."


def active_do_not_use_for(row: dict[str, Any]) -> str:
    if row.get("sensitivity") == "secret" or row.get("secret_ref"):
        return "Do not expose plaintext secrets or perform broker/payment/protected actions without explicit current user approval."
    if row.get("memory_tier") == TIER_SHORT:
        return "Do not treat as stable identity, default preference, or high-weight personalization without renewed evidence."
    return "Do not overgeneralize beyond the cited source and validity period."


def build_active_memory_rows(candidates: list[dict[str, Any]], run_id: str, database_dir: Path | None = None) -> list[dict[str, Any]]:
    activated_at = isoformat(utc_now())
    curation_overrides = load_curation_overrides(database_dir)
    rows: list[dict[str, Any]] = []
    for row in candidates:
        active = dict(row)
        active["memory_tier"] = normalized_memory_tier(active)
        if active["memory_tier"] == TIER_SHORT and looks_like_code_or_config_noise(active.get("statement", "")):
            active["category"] = "temporary_or_sensitive"
            active["importance"] = IMPORTANCE_LOW
            active["validity"] = VALIDITY_TEMP
            active["reason"] = "疑似代码、配置、日志或一次性操作片段，应低权重备份，不提升为核心画像。"
        apply_curation_override(active, curation_overrides)
        active.setdefault("backup_status", "backed_up_as_redacted_summary")
        active["status"] = "active"
        active["review_status"] = "active_auto_promoted_from_full_flow"
        active["activation_mode"] = "user_authorized_full_flow"
        active["activated_at"] = activated_at
        active["activation_run_id"] = run_id
        active["retrieval_weight"] = retrieval_weight(active)
        active["use_when"] = active_use_when(active)
        active["do_not_use_for"] = active_do_not_use_for(active)
        rows.append(active)
    rows.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}.get(r["retrieval_weight"], 3), r.get("date", ""), r.get("id", "")))
    return rows


def build_active_memory_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Active Memory",
        "",
        "Generated from the full memory-analysis flow. All three tiers are backed up; retrieval weight controls personalization strength.",
        "",
    ]
    for tier in [TIER_CORE, TIER_MID_LONG, TIER_SHORT]:
        tier_rows = [row for row in rows if row.get("memory_tier") == tier]
        lines += [f"## {tier}", "", f"- Count: {len(tier_rows)}", ""]
        for row in tier_rows[:80]:
            lines.append(f"- [{row.get('retrieval_weight')}/{row.get('importance')}/{row.get('validity')}] {truncate(row.get('statement', ''), 300)}")
        if len(tier_rows) > 80:
            lines.append(f"- 另有 {len(tier_rows) - 80} 条已写入 `active_memory.jsonl`。")
        lines.append("")
    return "\n".join(lines)


def build_core_profile_markdown(rows: list[dict[str, Any]], overrides: dict[str, dict[str, Any]]) -> str:
    core_rows = [row for row in rows if row.get("memory_tier") == TIER_CORE]
    demoted_ids = {mid for mid, override in overrides.items() if override.get("memory_tier") == TIER_MID_LONG}
    demoted_rows = [row for row in rows if row.get("id") in demoted_ids]
    lines = [
        "# Curated Core Profile",
        "",
        "这是给未来 ChatGPT/Codex/agent 优先读取的高权重 personalization 摘要。项目阶段性信息和具体 workflow 仍保留在 active memory，但不默认当作核心画像。",
        "",
        "## High-weight Core Personalization",
        "",
    ]
    for row in core_rows:
        lines.append(f"- {row.get('statement', '')}")
        lines.append(f"  - importance: {row.get('importance')}; validity: {row.get('validity')}; confidence: {row.get('confidence')}; id: {row.get('id')}")
    if not core_rows:
        lines.append("- 暂无已审核核心画像。")
    lines += [
        "",
        "## Important Mid/Long-term Context Demoted From Core",
        "",
    ]
    for row in demoted_rows:
        lines.append(f"- {row.get('statement', '')}")
        lines.append(f"  - reason: {row.get('curation_reason') or row.get('reason')}; id: {row.get('id')}")
    if not demoted_rows:
        lines.append("- 暂无。")
    lines += [
        "",
        "## Agent Use Rules",
        "",
        "- 先用 High-weight Core Personalization 适配默认回答方式和协作标准。",
        "- 只有任务触及具体项目、学习计划、Nitrosend、回转窑、Notion 或相关 workflow 时，再召回 Important Mid/Long-term Context。",
        "- 不要把临时、敏感资料、日志、代码片段、一次性命令当作稳定人格画像。",
        "",
    ]
    return "\n".join(lines)


def build_project_index(candidates: list[dict[str, Any]]) -> str:
    matched, other = classify_theme_statements(candidates)
    lines = ["# Project Index", "", "用于让未来 agent 快速理解项目组合、长期主题、下一步动作和机会方向。", ""]
    for profile in THEME_PROFILES:
        statements = matched.get(profile["name"], [])
        if not statements:
            continue
        lines += [
            f"## {profile['name']}",
            "",
            f"- 记录数：{len(statements)}",
            f"- 核心含义：{profile['meaning']}",
            f"- 下一步：{profile['do']}",
            f"- 需要记住：{profile['remember']}",
            f"- 机会方向：{profile['opportunity']}",
            f"- 能力成长：{profile['growth']}",
            f"- 代表记录：{truncate(statements[0], 260)}",
            "",
        ]
    if other:
        lines += [
            "## 其他待人工归类主题",
            "",
            f"- 记录数：{len(other)}",
            f"- 代表记录：{truncate(other[0], 260)}",
            "- 下一步：后续复盘时继续去噪、合并、归类。",
            "",
        ]
    return "\n".join(lines)


def build_decision_log(candidates: list[dict[str, Any]]) -> str:
    decisions = [row for row in candidates if row.get("category") == "decision"]
    lines = ["# Decision Log", "", "记录已识别的用户决策、默认执行策略和未来影响。低置信或语义不完整项仍需人工确认。", ""]
    if not decisions:
        return "\n".join(lines + ["暂无明确决策。", ""])
    for row in sorted(decisions, key=lambda r: (r.get("date", ""), r.get("id", ""))):
        lines += [
            f"## {row.get('date')} - {truncate(row.get('statement', ''), 90)}",
            "",
            f"- 决策：{truncate(row.get('statement', ''), 500)}",
            f"- 来源：{truncate(row.get('source', ''), 220)}",
            f"- 重要性：{row.get('importance')}；有效期：{row.get('validity')}；置信度：{row.get('confidence')}",
            "- 默认影响：未来相关任务优先按该决策执行；如出现更新决策，以更新后的记录为准。",
            "",
        ]
    return "\n".join(lines)


def build_timeline(candidates: list[dict[str, Any]]) -> str:
    rows = sorted(candidates, key=lambda r: (r.get("date", ""), r.get("id", "")))
    lines = ["# Timeline", "", "按日期记录关键记忆，用于恢复上下文、发现主题演变和做周/月复盘。", ""]
    for row in rows:
        lines.append(f"- {row.get('date')}: [{row.get('memory_tier')}/{row.get('category')}] {truncate(row.get('statement', ''), 320)}")
    lines.append("")
    return "\n".join(lines)


def extract_brief_review_lines(report: str, max_lines: int = 50) -> list[str]:
    keep_prefixes = (
        "## 本周资料内容结论",
        "## 本周资料与上一轮结论对比",
        "## 1. 本周核心事件",
        "## 2. 本周重要决策",
        "## 3. 本周反复出现的问题",
        "## 9. 下周行动清单",
        "## 本月资料内容结论",
        "## 本月资料与上一轮结论对比",
        "## 1. Core Profile Memories",
        "## 2. Important Mid/Long-term Memories",
        "## 5. Updated Profile",
        "## 6. Updated Project Index",
        "## 7. Updated Decision Log",
        "## 9. 适合上传到 ChatGPT Project 的 compact context pack",
    )
    lines: list[str] = []
    include = False
    for line in report.splitlines():
        if line.startswith("## "):
            include = any(line.startswith(prefix) for prefix in keep_prefixes)
        if include and (line.startswith("## ") or line.startswith("- ")):
            lines.append(line)
        if len(lines) >= max_lines:
            lines.append("- 其余细节已进入 GitHub 备份和 RAG 数据库。")
            break
    return lines or ["- 暂无可摘要内容。"]


def build_chat_report(
    candidates: list[dict[str, Any]],
    active: list[dict[str, Any]],
    previous_candidates: list[dict[str, Any]] | None,
    week_start: datetime,
    month: str,
) -> str:
    core = [c for c in candidates if c.get("memory_tier") == TIER_CORE]
    mid_long = [c for c in candidates if c.get("memory_tier") == TIER_MID_LONG]
    short = [c for c in candidates if c.get("memory_tier") == TIER_SHORT]
    decisions = [c for c in candidates if c.get("category") == "decision"]
    rules = [c for c in candidates if c.get("category") in {"answering_rule", "security_boundary"}]
    weekly_report = build_weekly_report(candidates, week_start, previous_candidates)
    monthly_report = build_monthly_report(candidates, month, previous_candidates)
    lines = [
        "# 本轮聊天框输出报告",
        "",
        "这份报告用于直接输出到聊天框；仓库中的 Markdown/JSONL/SQLite 是 GitHub 备份和 RAG 数据库。",
        "",
        content_conclusion_block(candidates, "本次资料"),
        "",
        previous_conclusion_comparison_block(candidates, previous_candidates, "本次资料"),
        "",
        "## 本次增量与记忆更新",
        "",
        f"- 本轮候选：{len(candidates)} 条；核心画像 {len(core)} 条、一般 {len(mid_long)} 条、临时低权重 {len(short)} 条。",
        f"- 数据库 active memory 总数：{len(active)} 条，已从所有候选快照去重汇总并分配 retrieval_weight。",
        f"- 新增决策候选：{len(decisions)} 条；未来应进入 Decision Log 并减少重复确认。",
        f"- 未来回答规则/安全边界：{len(rules)} 条；未来 agent 应优先读取并遵守。",
        "- 已生成 active_memory、Project Index、Decision Log、Timeline、weekly/monthly/context packs，并重建 SQLite search/fetch 索引。",
        "",
        "## 周复盘",
        "",
        *extract_brief_review_lines(weekly_report, max_lines=42),
        "",
        "## 月复盘",
        "",
        *extract_brief_review_lines(monthly_report, max_lines=48),
        "",
        "## 双 reviewer 合并结论",
        "",
        "- 战略/机会：最高价值不是原始聊天，而是可迁移、可检索、可被未来 agent 接管的三层记忆库；最值得继续做的是 personal RAG、agent continuity、个人能力增长 OS、垂直行业/金融风控 agent。",
        "- 执行/质量：最大短板是 active memory 需要持续去噪，项目/决策/时间线需要长期维护；短期敏感信息只能低权重召回，不能污染核心画像。",
        "- 默认下一步：每次运行都直接在聊天框输出报告，并把 durable 数据推到 GitHub。",
        "",
    ]
    return "\n".join(lines)


def ensure_repo_baseline(database_dir: Path) -> None:
    for rel in [
        "data/memory/active",
        "data/memory/candidates",
        "data/memory/curation",
        "data/memory/secret_refs",
        "data/memory/deprecated",
        "data/derived/weekly",
        "data/derived/monthly",
        "data/derived/human_reviews",
        "data/derived/incremental",
        "data/derived/context_packs",
        "data/derived/chat_reports",
        "data/derived/profile",
        "data/derived/project_index",
        "data/derived/decision_log",
        "data/derived/timeline",
        "data/processed/conversations",
        "data/processed/indexes",
        "data/raw_encrypted",
        ".local_keys",
    ]:
        ensure_dir(database_dir / rel)
    active_jsonl = database_dir / "data/memory/active/active_memory.jsonl"
    active_md = database_dir / "data/memory/active/active_memory.md"
    if not active_jsonl.exists():
        active_jsonl.write_text("", encoding="utf-8")
    if not active_md.exists():
        active_md.write_text("# Active Memory\n\nNo accepted active memories yet.\n", encoding="utf-8")


def build_sqlite_index(database_dir: Path, records: list[dict[str, Any]]) -> Path:
    index_path = database_dir / "data/processed/indexes/memory_index.sqlite"
    ensure_dir(index_path.parent)
    with sqlite3.connect(index_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
              id TEXT PRIMARY KEY,
              statement TEXT NOT NULL,
              category TEXT,
              status TEXT,
              importance TEXT,
              validity TEXT,
              confidence TEXT,
              sensitivity TEXT,
              date TEXT,
              source TEXT,
              record_json TEXT NOT NULL
            )
            """
        )
        con.execute("DELETE FROM memory")
        for row in records:
            if row.get("sensitivity") == "secret":
                continue
            con.execute(
                """
                INSERT OR REPLACE INTO memory
                (id, statement, category, status, importance, validity, confidence, sensitivity, date, source, record_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("id"),
                    row.get("statement"),
                    row.get("category"),
                    row.get("review_status") or row.get("status"),
                    row.get("importance"),
                    row.get("validity"),
                    row.get("confidence"),
                    row.get("sensitivity"),
                    row.get("date"),
                    row.get("source"),
                    json.dumps(row, ensure_ascii=False, sort_keys=True),
                ),
            )
        con.commit()
    return index_path


def load_index_records(database_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((database_dir / "data/memory/candidates").glob("*.jsonl")):
        records.extend(read_jsonl(path))
    active = database_dir / "data/memory/active/active_memory.jsonl"
    records.extend(read_jsonl(active))
    dedup: dict[str, dict[str, Any]] = {}
    for row in records:
        if row.get("id"):
            dedup[row["id"]] = row
    return list(dedup.values())


def query_index(database_dir: Path, query: str, limit: int = 10, sensitivity_max: str = "sensitive") -> list[dict[str, Any]]:
    index_path = database_dir / "data/processed/indexes/memory_index.sqlite"
    if not index_path.exists():
        build_sqlite_index(database_dir, load_index_records(database_dir))
    max_rank = SENSITIVITY_RANK.get(sensitivity_max, 2)
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    where = ["sensitivity != 'secret'"]
    params: list[Any] = []
    if terms:
        term_clauses = []
        for term in terms:
            term_clauses.append("(statement LIKE ? OR category LIKE ? OR source LIKE ?)")
            like = f"%{term}%"
            params.extend([like, like, like])
        where.append("(" + " AND ".join(term_clauses) + ")")
    sql = f"SELECT record_json FROM memory WHERE {' AND '.join(where)} ORDER BY date DESC, importance ASC LIMIT ?"
    params.append(limit * 5)
    rows: list[dict[str, Any]] = []
    with sqlite3.connect(index_path) as con:
        for (record_json,) in con.execute(sql, params):
            row = json.loads(record_json)
            if SENSITIVITY_RANK.get(row.get("sensitivity", "private"), 1) <= max_rank:
                rows.append(compact_search_result(row))
            if len(rows) >= limit:
                break
    return rows


def fetch_index(database_dir: Path, ident: str) -> dict[str, Any]:
    index_path = database_dir / "data/processed/indexes/memory_index.sqlite"
    if not index_path.exists():
        build_sqlite_index(database_dir, load_index_records(database_dir))
    with sqlite3.connect(index_path) as con:
        row = con.execute("SELECT record_json FROM memory WHERE id = ?", (ident,)).fetchone()
    if not row:
        return {"error": "not_found", "id": ident}
    record = json.loads(row[0])
    if record.get("sensitivity") == "secret":
        return {"error": "redacted_secret", "id": ident}
    return record


def compact_search_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "summary": row.get("statement"),
        "category": row.get("category"),
        "date": row.get("date"),
        "importance": row.get("importance"),
        "validity": row.get("validity"),
        "confidence": row.get("confidence"),
        "sensitivity": row.get("sensitivity"),
        "status": row.get("review_status") or row.get("status"),
        "source": row.get("source"),
    }


def extract_secret_refs(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cand in candidates:
        if not cand.get("secret_ref"):
            continue
        rows.append(
            {
                "secret_ref": cand.get("secret_ref"),
                "memory_id": cand.get("id"),
                "date": cand.get("date"),
                "source": cand.get("source"),
                "source_kind": cand.get("source_kind"),
                "category": cand.get("category"),
                "summary": "Credential or high-risk secret was detected and redacted. Plaintext is not stored in GitHub.",
                "sensitivity": cand.get("sensitivity"),
                "security_finding_types": sorted({f.get("type", "") for f in cand.get("security_findings", []) if f.get("type")}),
                "credential_policy": cand.get("credential_policy", {}),
                "agent_instruction": "Use this reference only to request authorized local secret access; fail closed for broker, trading, payment, or other protected actions without current user approval.",
            }
        )
    return rows


def write_run_outputs(state: RunState, week_start: datetime, month: str) -> dict[str, str]:
    ensure_repo_baseline(state.database_dir)
    merged_candidates = merge_candidates(state.candidates)
    state.candidates = merged_candidates
    active = read_jsonl(state.database_dir / "data/memory/active/active_memory.jsonl")
    previous_candidates = load_latest_candidate_snapshot(state.database_dir)
    secret_refs = extract_secret_refs(merged_candidates)
    all_known_candidates = merge_candidates(load_all_candidate_snapshots(state.database_dir) + merged_candidates)
    curation_overrides = load_curation_overrides(state.database_dir)
    active_rows = build_active_memory_rows(all_known_candidates, state.run_id, state.database_dir)
    run_manifest = {
        "run_id": state.run_id,
        "generated_at": isoformat(utc_now()),
        "database_dir": str(state.database_dir),
        "input_count": len(state.input_manifests),
        "conversation_count": len(state.conversation_manifest),
        "candidate_count": len(merged_candidates),
        "active_memory_count": len(active_rows),
        "previous_candidate_count": len(previous_candidates),
        "security_counts": dict(state.security_counts),
        "archive_results": state.archive_results,
        "errors": state.errors,
    }
    paths = {
        "run_manifest": state.run_dir / "run_manifest.json",
        "input_manifests": state.run_dir / "input_manifests.json",
        "conversation_manifest": state.run_dir / "conversation_manifest.jsonl",
        "security_scan": state.run_dir / "security_scan.json",
        "candidates_jsonl": state.run_dir / "memory_candidates.jsonl",
        "candidates_md": state.run_dir / "memory_candidates.md",
        "incremental": state.run_dir / "incremental_change_report.md",
        "weekly": state.run_dir / "weekly_memory_pack.md",
        "monthly": state.run_dir / "monthly_memory_pack.md",
        "chatgpt_pack": state.run_dir / "chatgpt_project_context_pack.md",
        "codex_pack": state.run_dir / "codex_memory_update_pack.md",
        "human_review": state.run_dir / "human_memory_review.md",
        "dual_review": state.run_dir / "dual_agent_review.md",
        "active_memory_jsonl": state.run_dir / "active_memory.jsonl",
        "active_memory_md": state.run_dir / "active_memory.md",
        "core_profile_md": state.run_dir / "CORE_PROFILE.md",
        "project_index": state.run_dir / "PROJECT_INDEX.md",
        "decision_log": state.run_dir / "DECISION_LOG.md",
        "timeline": state.run_dir / "TIMELINE.md",
        "chat_report": state.run_dir / "chat_report.md",
        "secret_refs": state.run_dir / "secret_refs.jsonl",
    }
    write_json(paths["run_manifest"], run_manifest)
    write_json(paths["input_manifests"], state.input_manifests)
    write_json(paths["security_scan"], {"counts": dict(state.security_counts), "generated_at": isoformat(utc_now())})
    write_jsonl(paths["conversation_manifest"], state.conversation_manifest)
    write_jsonl(paths["candidates_jsonl"], merged_candidates)
    paths["candidates_md"].write_text(build_candidates_markdown(merged_candidates), encoding="utf-8")
    incremental_report = build_incremental_report(merged_candidates, active, previous_candidates)
    weekly_report = build_weekly_report(merged_candidates, week_start, previous_candidates)
    monthly_report = build_monthly_report(merged_candidates, month, previous_candidates)
    human_review = build_human_memory_review(merged_candidates, active, previous_candidates)
    paths["incremental"].write_text(incremental_report, encoding="utf-8")
    paths["weekly"].write_text(weekly_report, encoding="utf-8")
    paths["monthly"].write_text(monthly_report, encoding="utf-8")
    paths["chatgpt_pack"].write_text(build_context_pack(merged_candidates, "ChatGPT Project Compact Context Pack"), encoding="utf-8")
    paths["codex_pack"].write_text(build_context_pack(merged_candidates, "Codex Memory Update Pack"), encoding="utf-8")
    paths["human_review"].write_text(human_review, encoding="utf-8")
    paths["dual_review"].write_text(build_dual_agent_review(merged_candidates, active), encoding="utf-8")
    write_jsonl(paths["active_memory_jsonl"], active_rows)
    paths["active_memory_md"].write_text(build_active_memory_markdown(active_rows), encoding="utf-8")
    paths["core_profile_md"].write_text(build_core_profile_markdown(active_rows, curation_overrides), encoding="utf-8")
    paths["project_index"].write_text(build_project_index(merged_candidates), encoding="utf-8")
    paths["decision_log"].write_text(build_decision_log(merged_candidates), encoding="utf-8")
    paths["timeline"].write_text(build_timeline(merged_candidates), encoding="utf-8")
    chat_report = build_chat_report(merged_candidates, active_rows, previous_candidates, week_start, month)
    paths["chat_report"].write_text(chat_report, encoding="utf-8")
    write_jsonl(paths["secret_refs"], secret_refs)

    candidate_base = f"{state.run_id}.memory_candidates"
    report_base = state.run_id
    append_or_merge_jsonl(
        state.database_dir / "data/processed/conversations/conversation_manifest.jsonl",
        state.conversation_manifest,
        ["conversation_id", "content_sha256"],
    )
    write_jsonl(state.database_dir / "data/memory/candidates" / f"{candidate_base}.jsonl", merged_candidates)
    (state.database_dir / "data/memory/candidates" / f"{candidate_base}.md").write_text(
        build_candidates_markdown(merged_candidates), encoding="utf-8"
    )
    write_jsonl(state.database_dir / "data/memory/active/active_memory.jsonl", active_rows)
    (state.database_dir / "data/memory/active/active_memory.md").write_text(
        build_active_memory_markdown(active_rows), encoding="utf-8"
    )
    (state.database_dir / "data/derived/profile/CORE_PROFILE.md").write_text(
        build_core_profile_markdown(active_rows, curation_overrides), encoding="utf-8"
    )
    (state.database_dir / "data/derived/weekly" / f"{week_start.date().isoformat()}.weekly_memory_pack.md").write_text(
        weekly_report, encoding="utf-8"
    )
    (state.database_dir / "data/derived/monthly" / f"{month}.monthly_memory_pack.md").write_text(
        monthly_report, encoding="utf-8"
    )
    (state.database_dir / "data/derived/human_reviews" / f"{report_base}.human_memory_review.md").write_text(
        human_review, encoding="utf-8"
    )
    (state.database_dir / "data/derived/human_reviews" / f"{report_base}.dual_agent_review.md").write_text(
        build_dual_agent_review(merged_candidates, active), encoding="utf-8"
    )
    (state.database_dir / "data/derived/incremental" / f"{report_base}.incremental_change_report.md").write_text(
        incremental_report, encoding="utf-8"
    )
    (state.database_dir / "data/derived/context_packs" / f"{report_base}.chatgpt_project_context_pack.md").write_text(
        build_context_pack(merged_candidates, "ChatGPT Project Compact Context Pack"), encoding="utf-8"
    )
    (state.database_dir / "data/derived/context_packs" / f"{report_base}.codex_memory_update_pack.md").write_text(
        build_context_pack(merged_candidates, "Codex Memory Update Pack"), encoding="utf-8"
    )
    (state.database_dir / "data/derived/chat_reports" / f"{report_base}.chat_report.md").write_text(
        chat_report, encoding="utf-8"
    )
    (state.database_dir / "data/derived/project_index/PROJECT_INDEX.md").write_text(
        build_project_index(merged_candidates), encoding="utf-8"
    )
    (state.database_dir / "data/derived/decision_log/DECISION_LOG.md").write_text(
        build_decision_log(merged_candidates), encoding="utf-8"
    )
    (state.database_dir / "data/derived/timeline/TIMELINE.md").write_text(
        build_timeline(merged_candidates), encoding="utf-8"
    )
    write_jsonl(state.database_dir / "data/memory/secret_refs" / f"{report_base}.secret_refs.jsonl", secret_refs)
    build_sqlite_index(state.database_dir, load_index_records(state.database_dir))
    return {name: str(path) for name, path in paths.items()}


def run_analysis(args: argparse.Namespace) -> int:
    database_dir = Path(args.database_dir).resolve()
    out_root = ensure_dir(Path(args.out_dir).resolve())
    run_id = "run_" + utc_now().strftime("%Y%m%dT%H%M%SZ")
    run_dir = ensure_dir(out_root / run_id)
    state = RunState(run_id=run_id, run_dir=run_dir, database_dir=database_dir)
    ensure_repo_baseline(database_dir)

    inputs = [Path(p).expanduser().resolve() for p in args.inputs]
    if args.archive:
        key_file = Path(args.archive_key_file).expanduser().resolve() if args.archive_key_file else database_dir / ".local_keys/openai_memory_analysis.key"
        for input_path in inputs:
            state.archive_results.append(encrypt_archive(input_path, database_dir, key_file))

    for input_path in inputs:
        try:
            process_input_zip(input_path, state, sample_limit=args.sample_limit)
        except Exception as exc:  # keep processing other inputs while recording evidence.
            state.errors.append(f"{input_path}: {type(exc).__name__}: {exc}")
            raise

    week_start = datetime.fromisoformat(args.week_start).replace(tzinfo=UTC) if args.week_start else default_week_start()
    month = args.month or utc_now().strftime("%Y-%m")
    paths = write_run_outputs(state, week_start, month)
    chat_report_path = Path(paths["chat_report"])
    if chat_report_path.exists():
        print(chat_report_path.read_text(encoding="utf-8"))
    print(json.dumps({"status": "ok", "run_id": run_id, "paths": paths}, ensure_ascii=False, indent=2))
    return 0


def run_refresh_from_candidates(args: argparse.Namespace) -> int:
    database_dir = Path(args.database_dir).resolve()
    out_root = ensure_dir(Path(args.out_dir).resolve())
    candidate_path = Path(args.candidate_jsonl).resolve() if args.candidate_jsonl else None
    if candidate_path is None:
        candidate_dir = database_dir / "data/memory/candidates"
        candidates = sorted(candidate_dir.glob("*.memory_candidates.jsonl"), key=lambda path: path.stat().st_mtime)
        if not candidates:
            raise FileNotFoundError(f"No candidate snapshots found in {candidate_dir}")
        candidate_path = candidates[-1]
    rows = read_jsonl(candidate_path)
    if not rows:
        raise ValueError(f"Candidate snapshot is empty: {candidate_path}")
    run_id = "run_" + utc_now().strftime("%Y%m%dT%H%M%SZ")
    run_dir = ensure_dir(out_root / run_id)
    state = RunState(run_id=run_id, run_dir=run_dir, database_dir=database_dir)
    state.candidates = rows
    state.errors.append(f"refresh-from-candidates: rebuilt durable outputs from {candidate_path}; raw export ZIP was not re-read.")
    week_start = datetime.fromisoformat(args.week_start).replace(tzinfo=UTC) if args.week_start else default_week_start()
    month = args.month or utc_now().strftime("%Y-%m")
    paths = write_run_outputs(state, week_start, month)
    chat_report_path = Path(paths["chat_report"])
    if chat_report_path.exists():
        print(chat_report_path.read_text(encoding="utf-8"))
    print(json.dumps({"status": "ok", "run_id": run_id, "source_candidate_jsonl": str(candidate_path), "paths": paths}, ensure_ascii=False, indent=2))
    return 0


def default_week_start() -> datetime:
    now = utc_now()
    start = now - timedelta(days=now.weekday())
    return datetime(start.year, start.month, start.day, tzinfo=UTC)


def run_inspect(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(Path(args.out_dir).resolve())
    manifests = []
    for raw in args.inputs:
        path = Path(raw).expanduser().resolve()
        manifests.append(inspect_zip(path))
    write_json(out_dir / "inspect_manifest.json", {"generated_at": isoformat(utc_now()), "inputs": manifests})
    print(json.dumps({"status": "ok", "manifest": str(out_dir / "inspect_manifest.json")}, ensure_ascii=False, indent=2))
    return 0


def run_search(args: argparse.Namespace) -> int:
    results = query_index(Path(args.database_dir).resolve(), args.query, args.limit, args.sensitivity_max)
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


def run_fetch(args: argparse.Namespace) -> int:
    result = fetch_index(Path(args.database_dir).resolve(), args.id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def serve_mcp(args: argparse.Namespace) -> int:
    database_dir = Path(args.database_dir).resolve()

    def respond(req: dict[str, Any], result: Any = None, error: Any = None) -> None:
        payload = {"jsonrpc": "2.0", "id": req.get("id")}
        if error is not None:
            payload["error"] = error
        else:
            payload["result"] = result
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        method = req.get("method")
        params = req.get("params") or {}
        if method == "initialize":
            respond(req, {"protocolVersion": "2024-11-05", "serverInfo": {"name": "openai-memory-analysis", "version": "0.1.0"}})
        elif method == "tools/list":
            respond(
                req,
                {
                    "tools": [
                        {
                            "name": "search",
                            "description": "Search redacted active and pending memory records.",
                            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}},
                        },
                        {
                            "name": "fetch",
                            "description": "Fetch one redacted memory record by id.",
                            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
                        },
                    ]
                },
            )
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name == "search":
                respond(req, {"content": [{"type": "text", "text": json.dumps(query_index(database_dir, arguments.get("query", ""), int(arguments.get("limit", 10))), ensure_ascii=False)}]})
            elif name == "fetch":
                respond(req, {"content": [{"type": "text", "text": json.dumps(fetch_index(database_dir, arguments.get("id", "")), ensure_ascii=False)}]})
            else:
                respond(req, error={"code": -32601, "message": "Unknown read-only tool"})
        else:
            respond(req, error={"code": -32601, "message": "Unknown method"})
    return 0


def create_fixture_export(path: Path) -> None:
    conversations = [
        {
            "id": "conv_pref",
            "title": "Codex preference",
            "create_time": 1781481600,
            "update_time": 1781485200,
            "mapping": {
                "m1": {
                    "id": "m1",
                    "message": {
                        "id": "msg1",
                        "author": {"role": "user"},
                        "create_time": 1781481600,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "以后默认中文回复；复杂任务必须给执行合同、验证命令、风险与回滚；不要保存临时验证码。"
                            ],
                        },
                    },
                }
            },
        },
        {
            "id": "conv_decision",
            "title": "Memory skill decision",
            "create_time": 1781568000,
            "update_time": 1781569000,
            "mapping": {
                "m1": {
                    "id": "m1",
                    "message": {
                        "id": "msg2",
                        "author": {"role": "user"},
                        "create_time": 1781568000,
                        "content": {
                            "content_type": "text",
                            "parts": ["决定命名为 openai-memory-analysis，并把 OpenAIDatabase 作为记忆数据库。"],
                        },
                    },
                }
            },
        },
    ]
    with tempfile.TemporaryDirectory(prefix="oma_fixture_") as td:
        inner_path = Path(td) / "chatgpt-conversations.zip"
        with zipfile.ZipFile(inner_path, "w", zipfile.ZIP_DEFLATED) as inner:
            inner.writestr("conversations.json", json.dumps(conversations, ensure_ascii=False))
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as outer:
            outer.write(inner_path, "User Online Activity/Conversations__fixture.zip")
            outer.writestr("report.html", "<html>fixture</html>")


def create_fixture_pack(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "pack/README.md",
            "未来回答应遵守严格本地优先、安全扫描、候选记忆 pending 审核。不要保存一次性 token 或 cookie。",
        )


def run_self_test(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(Path(args.out_dir).resolve())
    db_dir = ensure_dir(out_dir / "OpenAIDatabase")
    export_zip = out_dir / "fixture-openai-export.zip"
    pack_zip = out_dir / "fixture-codex-pack.zip"
    create_fixture_export(export_zip)
    create_fixture_pack(pack_zip)
    ns = argparse.Namespace(
        inputs=[str(export_zip), str(pack_zip)],
        database_dir=str(db_dir),
        out_dir=str(out_dir / "runs"),
        sample_limit=0,
        archive=True,
        archive_key_file=str(db_dir / ".local_keys/openai_memory_analysis.key"),
        week_start="2026-06-15",
        month="2026-06",
    )
    rc = run_analysis(ns)
    records = load_index_records(db_dir)
    assert rc == 0
    assert records, "expected memory records"
    assert any(r.get("category") == "decision" for r in records)
    search_results = query_index(db_dir, "OpenAIDatabase", limit=5)
    assert search_results, "expected search result"
    fetched = fetch_index(db_dir, search_results[0]["id"])
    assert fetched.get("id") == search_results[0]["id"]
    all_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in (out_dir / "runs").rglob("*.md"))
    assert "验证码" in all_text
    print(json.dumps({"status": "PASS", "out_dir": str(out_dir), "records": len(records)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze OpenAI/ChatGPT/Codex exports into a redacted memory vault.")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Inspect ZIP inputs without parsing message content.")
    inspect_p.add_argument("--inputs", nargs="+", required=True)
    inspect_p.add_argument("--out-dir", required=True)
    inspect_p.set_defaults(func=run_inspect)

    run_p = sub.add_parser("run", help="Run local memory analysis.")
    run_p.add_argument("--inputs", nargs="+", required=True)
    run_p.add_argument("--database-dir", required=True)
    run_p.add_argument("--out-dir", required=True)
    run_p.add_argument("--sample-limit", type=int, default=0, help="Limit parsed conversations for smoke tests. 0 means full.")
    run_p.add_argument("--archive", action="store_true", help="Encrypt raw ZIP inputs into data/raw_encrypted.")
    run_p.add_argument("--archive-key-file", default="")
    run_p.add_argument("--week-start", default="", help="YYYY-MM-DD. Defaults to current UTC week start.")
    run_p.add_argument("--month", default="", help="YYYY-MM. Defaults to current UTC month.")
    run_p.set_defaults(func=run_analysis)

    refresh_p = sub.add_parser(
        "refresh-from-candidates",
        help="Rebuild active memory, reports, indexes, and chat report from a backed-up candidate JSONL snapshot.",
    )
    refresh_p.add_argument("--database-dir", required=True)
    refresh_p.add_argument("--out-dir", required=True)
    refresh_p.add_argument("--candidate-jsonl", default="", help="Defaults to the latest data/memory/candidates/*.memory_candidates.jsonl.")
    refresh_p.add_argument("--week-start", default="", help="YYYY-MM-DD. Defaults to current UTC week start.")
    refresh_p.add_argument("--month", default="", help="YYYY-MM. Defaults to current UTC month.")
    refresh_p.set_defaults(func=run_refresh_from_candidates)

    search_p = sub.add_parser("search", help="Read-only search over active and pending memory records.")
    search_p.add_argument("--database-dir", required=True)
    search_p.add_argument("--query", required=True)
    search_p.add_argument("--limit", type=int, default=10)
    search_p.add_argument("--sensitivity-max", default="sensitive", choices=["public", "private", "sensitive"])
    search_p.set_defaults(func=run_search)

    fetch_p = sub.add_parser("fetch", help="Read-only fetch by memory id.")
    fetch_p.add_argument("--database-dir", required=True)
    fetch_p.add_argument("--id", required=True)
    fetch_p.set_defaults(func=run_fetch)

    mcp_p = sub.add_parser("serve-mcp", help="Serve read-only JSON-RPC search/fetch tools over stdio.")
    mcp_p.add_argument("--database-dir", required=True)
    mcp_p.set_defaults(func=serve_mcp)

    self_p = sub.add_parser("self-test", help="Run deterministic local self-test with synthetic fixtures.")
    self_p.add_argument("--out-dir", required=True)
    self_p.set_defaults(func=run_self_test)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
