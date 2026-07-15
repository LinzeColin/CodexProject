"""证据声明抽取（五型 + 原文定位）—— 讲义逐句溯源与 R2 检索的地基（不变量 7）.

声明类型: paper_fact / author_claim / inference / hypothesis / action。
locator: {source: 'abstract', sentence_index, char_start, char_end}，三步到原文：
声明 → locator → 摘要句 → canonical_url。
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

_HYPOTHESIS = re.compile(r"\b(assum\w+|hypothes\w+|conjectur\w+)\b", re.I)
_INFERENCE = re.compile(r"\b(may|might|could|suggest\w*|imply|implies|likely|potential\w*)\b", re.I)
_ACTION = re.compile(r"\b(should|recommend\w*|future work|call for|need to|must be)\b", re.I)
_AUTHOR = re.compile(r"\b(we|our|this (paper|work|study)|the authors?)\b", re.I)
_NUMERIC = re.compile(r"\d")


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """返回 [(char_start, char_end, sentence)]，保证定位可逆."""
    text = text.strip()
    if not text:
        return []
    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in _SENTENCE_SPLIT.finditer(text):
        end = match.start() + 1
        sentence = text[start:end].strip()
        if sentence:
            spans.append((start, end, sentence))
        start = match.end()
    tail = text[start:].strip()
    if tail:
        spans.append((start, len(text), tail))
    return spans


def classify(sentence: str) -> tuple[str, float]:
    if _HYPOTHESIS.search(sentence):
        return "hypothesis", 0.7
    if _ACTION.search(sentence):
        return "action", 0.7
    if _INFERENCE.search(sentence):
        return "inference", 0.7
    if _NUMERIC.search(sentence):  # 量化结果优先判为论文事实，即使句中有 we/our
        return "paper_fact", 0.9
    if _AUTHOR.search(sentence):
        return "author_claim", 0.85
    return "author_claim", 0.6


def extract_claims(doc_version_id: str, abstract: str) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for index, (start, end, sentence) in enumerate(split_sentences(abstract)):
        claim_type, confidence = classify(sentence)
        claims.append({
            "id": f"{doc_version_id}:c{index}",
            "doc_version_id": doc_version_id,
            "type": claim_type,
            "text": sentence,
            "locator": {"source": "abstract", "sentence_index": index,
                        "char_start": start, "char_end": end},
            "confidence": confidence,
        })
    return claims


def store_claims(conn: sqlite3.Connection, claims: list[dict[str, Any]]) -> int:
    stored = 0
    for claim in claims:
        exists = conn.execute("SELECT 1 FROM claims WHERE id=?", (claim["id"],)).fetchone()
        if exists:
            continue
        conn.execute(
            "INSERT INTO claims (id, doc_version_id, type, text, locator_json, confidence) VALUES (?, ?, ?, ?, ?, ?)",
            (claim["id"], claim["doc_version_id"], claim["type"], claim["text"],
             json.dumps(claim["locator"], ensure_ascii=False), claim["confidence"]),
        )
        try:
            conn.execute("INSERT INTO fts_claims (claim_id, text) VALUES (?, ?)", (claim["id"], claim["text"]))
        except sqlite3.OperationalError:
            pass
        stored += 1
    return stored


def resolve_claim(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    """三步到原文：声明行 + 定位 + 原文链接（证据与纠错页用）."""
    row = conn.execute(
        """SELECT c.*, v.doc_id, v.metadata_json, d.canonical_url, d.title
           FROM claims c JOIN doc_versions v ON v.id = c.doc_version_id
           JOIN documents d ON d.id = v.doc_id WHERE c.id=?""",
        (claim_id,),
    ).fetchone()
    if row is None:
        return None
    locator = json.loads(row["locator_json"])
    abstract = (json.loads(row["metadata_json"]).get("summary")) or ""
    quote = abstract[locator.get("char_start", 0):locator.get("char_end", 0)]
    return {
        "claim_id": row["id"], "type": row["type"], "text": row["text"],
        "confidence": row["confidence"], "status": row["status"],
        "locator": locator, "source_quote": quote,
        "doc_id": row["doc_id"], "doc_title": row["title"], "canonical_url": row["canonical_url"],
    }
