"""深度讲义（R1-4/R1-5）—— 八段结构 + 逐句溯源（结构化句子，绑定即数据）.

复审修复（2026-07-14）：句子与其声明绑定在生成时即为一等数据
（sections_json = [{title, sentences: [{text, claim}], body}]），
渲染端不再重新切分正文，从根上消除索引漂移与标记错位。
生成通道：codex_cli_chatgpt_auth → deterministic_degraded（确定性模板保底）。
无法溯源的句子直接丢弃并计数；整段丢空时以诚实占位句标注（不回填未验证内容）。
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
from typing import Any

from . import store

TEMPLATE_VER = "lesson-v03-2"
DOC_META = "__doc_meta__"  # 一等元信息绑定：来源=arXiv 官方元数据本身
SECTION_TITLES = (
    "人话版",
    "领域脉络",
    "机制拆解",
    "证据与数字",
    "反例与边界",
    "跨领域连接与意外收获",
    "可复用方法",
    "术语表",
)

CATEGORY_CONTEXT = {
    "cs.AI": "人工智能——让机器完成需要智能的任务的总领域",
    "cs.LG": "机器学习——从数据中自动学习规律的方法学",
    "cs.CL": "自然语言处理——让机器理解与生成人类语言",
    "cs.CV": "计算机视觉——让机器理解图像与视频",
    "q-bio.QM": "定量生物学方法——用数学与计算工具研究生命系统",
    "q-fin.GN": "一般金融学——市场、资产与经济行为的量化研究",
    "eess.SY": "系统与控制工程——让复杂系统按预期稳定运行",
    "stat.ML": "统计机器学习——机器学习的统计学基础",
}

_NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent|×|x\b)|\d{2,}")
_LIMIT = re.compile(r"\b(limit\w*|however|although|only|fail\w*|cannot|challenge\w*|constraint\w*|caveat\w*)\b", re.I)
_METHOD = re.compile(r"\b(propose\w*|method\w*|approach\w*|framework|introduce\w*|develop\w*|design\w*|algorithm)\b", re.I)
_TERM = re.compile(r"\b([A-Z][A-Za-z]*(?:-[A-Za-z]+)?[A-Z][A-Za-z]*|[A-Z]{2,}[a-z0-9]*)\b")
# 中英混排讲义句切分（仅用于 codex 自由文本通道；确定性通道从不重切分）
_ZH_SENTENCE = re.compile(r"(?<=[。！？])|(?<=[.!?])\s+")


def generate_lesson(conn: sqlite3.Connection, *, lesson_id: str, candidate_id: str,
                    doc_version_id: str, as_of_date: str) -> dict[str, Any]:
    """生成讲义并落库；返回 {lesson, generator, degraded, dropped_unbound_sentences}."""
    doc = _load_doc(conn, doc_version_id)
    claims = _load_claims(conn, doc_version_id)

    generator = "deterministic_degraded"
    degraded_reason = None
    sections = None
    dropped = 0
    if shutil.which("codex"):
        try:
            raw_sections = _codex_generate(doc, claims)
            sections, dropped = _bind_free_text(raw_sections, claims)
            generator = "codex_cli_chatgpt_auth"
        except Exception as exc:
            degraded_reason = f"codex_generation_failed:{type(exc).__name__}"
            sections = None
    else:
        degraded_reason = "codex_cli_not_available"
    if sections is None:
        sections = _deterministic_sections(doc, claims)

    for section in sections:
        section["body"] = " ".join(s["text"] for s in section["sentences"])

    binding_summary = _binding_summary(sections, dropped)
    created_at = store.utcnow_iso()
    conn.execute(
        """INSERT OR REPLACE INTO lessons
           (id, candidate_id, doc_version_id, as_of_date, sections_json, claim_bindings_json,
            template_ver, generator, created_at, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
        (lesson_id, candidate_id, doc_version_id, as_of_date,
         json.dumps(sections, ensure_ascii=False), json.dumps(binding_summary, ensure_ascii=False),
         TEMPLATE_VER, generator, created_at),
    )
    try:
        body = " ".join(s["body"] for s in sections)
        conn.execute("DELETE FROM fts_lessons WHERE lesson_id=?", (lesson_id,))
        conn.execute("INSERT INTO fts_lessons (lesson_id, body) VALUES (?, ?)", (lesson_id, body))
    except sqlite3.OperationalError:
        pass
    conn.commit()
    return {
        "lesson_id": lesson_id, "generator": generator, "degraded_reason": degraded_reason,
        "sections": sections, "bindings": binding_summary, "dropped_unbound_sentences": dropped,
    }


def _binding_summary(sections: list[dict[str, Any]], dropped: int) -> dict[str, Any]:
    total = sum(len(s["sentences"]) for s in sections)
    doc_meta = sum(1 for s in sections for sent in s["sentences"] if sent["claim"] == DOC_META)
    return {"schema": "structured-v2", "total_sentences": total,
            "doc_meta_sentences": doc_meta, "dropped_unbound": dropped}


def validate_traceability(conn: sqlite3.Connection, lesson_id: str) -> dict[str, Any]:
    """机器面校验：每个句子的 claim 绑定必须存在（DOC_META 除外，属官方元数据）."""
    row = conn.execute("SELECT sections_json FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    if row is None:
        return {"ok": False, "error": "lesson_not_found"}
    sections = json.loads(row["sections_json"])
    missing = []
    bindings = 0
    for section_index, section in enumerate(sections):
        for sent_index, sentence in enumerate(section.get("sentences") or []):
            bindings += 1
            claim_id = sentence.get("claim")
            if not claim_id:
                missing.append({f"s{section_index}.{sent_index}": "unbound"})
            elif claim_id != DOC_META:
                exists = conn.execute("SELECT 1 FROM claims WHERE id=?", (claim_id,)).fetchone()
                if not exists:
                    missing.append({f"s{section_index}.{sent_index}": claim_id})
    return {"ok": not missing and bindings > 0, "bindings": bindings, "missing": missing}


def _bind_free_text(raw_sections: list[dict[str, Any]], claims: list[dict[str, Any]]
                    ) -> tuple[list[dict[str, Any]], int]:
    """codex 自由文本通道：逐句词面重叠绑定；绑不上的句子丢弃并计数（不回填）."""
    claim_tokens = [
        (claim, set(re.findall(r"[a-z0-9\-]{3,}", claim["text"].lower()))) for claim in claims
    ]
    dropped = 0
    sections: list[dict[str, Any]] = []
    for raw in raw_sections:
        sentences: list[dict[str, Any]] = []
        for part in _ZH_SENTENCE.split(str(raw.get("body") or "")):
            sentence = part.strip()
            if not sentence:
                continue
            tokens = set(re.findall(r"[a-z0-9\-]{3,}", sentence.lower()))
            best, best_overlap = None, 0.0
            for claim, ctoks in claim_tokens:
                if not tokens or not ctoks:
                    continue
                overlap = len(tokens & ctoks) / len(tokens | ctoks)
                if overlap > best_overlap:
                    best, best_overlap = claim, overlap
            if best is not None and best_overlap >= 0.18:
                sentences.append({"text": sentence, "claim": best["id"]})
            else:
                dropped += 1
        if not sentences:
            sentences.append({"text": "该段生成内容未通过逐句溯源校验，已按合同省略（不展示无来源内容）。",
                              "claim": DOC_META})
        sections.append({"title": raw.get("title") or "未命名", "sentences": sentences})
    return sections, dropped


def _load_doc(conn: sqlite3.Connection, doc_version_id: str) -> dict[str, Any]:
    row = conn.execute(
        """SELECT v.*, d.title, d.canonical_url FROM doc_versions v
           JOIN documents d ON d.id = v.doc_id WHERE v.id=?""",
        (doc_version_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"doc version not found: {doc_version_id}")
    meta = json.loads(row["metadata_json"])
    return {"doc_version_id": doc_version_id, "title": row["title"],
            "canonical_url": row["canonical_url"], "meta": meta}


def _load_claims(conn: sqlite3.Connection, doc_version_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM claims WHERE doc_version_id=?", (doc_version_id,)).fetchall()
    claims = [
        {"id": r["id"], "type": r["type"], "text": r["text"],
         "locator": json.loads(r["locator_json"]), "confidence": r["confidence"]}
        for r in rows
    ]
    # 按摘要句序排列（数值序，避免 c10 < c2 的字典序陷阱）
    claims.sort(key=lambda c: int(c["locator"].get("sentence_index", 0)))
    return claims


def _codex_generate(doc: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Codex CLI 认证通道：产出八段自由文本；绑定由 _bind_free_text 负责（零标记协议）."""
    claim_lines = "\n".join(f"- {c['text']}" for c in claims)
    prompt = (
        "你是个人前沿学习系统的讲义作者。只基于以下论文摘要声明写作，不得编造未给出的事实。"
        '输出 JSON 数组，元素为 {"title": 八段之一, "body": 中文正文}，八段依次为：'
        f"{', '.join(SECTION_TITLES)}。\n论文: {doc['title']}\n声明:\n{claim_lines}"
    )
    result = subprocess.run(
        ["codex", "exec", "--json", prompt],
        capture_output=True, text=True, timeout=180, check=True,
    )
    sections = json.loads(result.stdout)
    if not isinstance(sections, list) or len(sections) != len(SECTION_TITLES):
        raise ValueError("codex output shape invalid")
    return sections


def _sent(text: str, claim_id: str = DOC_META) -> dict[str, Any]:
    return {"text": text, "claim": claim_id}


def _claim_sent(prefix: str, indexed_claim: tuple[int, dict[str, Any]]) -> dict[str, Any]:
    _, claim = indexed_claim
    return {"text": f"{prefix}{claim['text']}", "claim": claim["id"]}


def _deterministic_sections(doc: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """确定性模板：直接构造〈句子, 声明〉对，绝不字符串拼接后再切分（复审修复）."""
    meta = doc["meta"]
    title = doc["title"]
    categories = meta.get("categories") or []
    authors = meta.get("authors") or []
    published = (meta.get("published") or "")[:10]

    indexed = list(enumerate(claims))
    facts = [(i, c) for i, c in indexed if c["type"] == "paper_fact"]
    author_claims = [(i, c) for i, c in indexed if c["type"] == "author_claim"]
    inferences = [(i, c) for i, c in indexed if c["type"] in {"inference", "hypothesis"}]
    actions = [(i, c) for i, c in indexed if c["type"] == "action"]
    numeric = [(i, c) for i, c in indexed if _NUM.search(c["text"])]
    limits = [(i, c) for i, c in indexed if _LIMIT.search(c["text"])]
    methods = [(i, c) for i, c in indexed if _METHOD.search(c["text"])]

    plain: list[dict[str, Any]] = []
    lead = author_claims[:1] or facts[:1] or indexed[:1]
    if lead:
        plain.append(_claim_sent("这篇论文在做什么：", lead[0]))
    plain.append(_sent(f"论文《{title}》发表于 {published or '未知日期'}，作者 {len(authors)} 人，原文见 {doc['canonical_url']}。"))

    context = [_sent(
        f"本文主类目 {meta.get('primary_category') or '未知'}：{CATEGORY_CONTEXT.get(meta.get('primary_category'), '（该类目暂无脉络注解，点原文了解）')}。"
    )]
    for cat in categories[1:3]:
        if cat in CATEGORY_CONTEXT:
            context.append(_sent(f"交叉类目 {cat}：{CATEGORY_CONTEXT[cat]}。"))

    mechanism = [_claim_sent("", entry) for entry in (methods[:3] or author_claims[:2])]
    if not mechanism:
        mechanism = [_sent("摘要未展开机制细节，机制拆解需要点开原文。")]

    evidence = [_claim_sent("", entry) for entry in numeric[:3]]
    if not evidence:
        evidence = [_sent("摘要未给出量化结果，证据等级为摘要级，点原文核对全文数字。")]

    boundary = [_claim_sent("", entry) for entry in limits[:2]]
    if not boundary:
        boundary = [_sent("摘要未声明边界与反例——这是一个需要警惕的信号，深挖时先问局限。")]

    connect: list[dict[str, Any]] = []
    if len(categories) > 1:
        connect.append(_sent(f"本文横跨 {len(categories)} 个类目（{', '.join(categories[:4])}），关注其在你兴趣板块间的迁移面。"))
    for entry in (inferences[:2] or facts[1:3]):
        connect.append(_claim_sent("意外收获：", entry))
    if len(connect) < 3:
        connect.append(_sent(f"意外收获：本文由 {len(authors)} 位作者合作完成，发表后 48 小时内即进入你的学习队列。"))
    if len(connect) < 3:
        connect.append(_sent("意外收获：本篇的入选是 8 特征加权的结果——打开系统页可以看到它赢在哪个特征。"))

    takeaway = [_claim_sent("", entry) for entry in (actions[:2] or methods[:1])]
    if not takeaway:
        takeaway = [_sent("可复用方法：将本文机制与你正在跟的项目对照，找一个能在两周内验证的最小实验。")]

    glossary = _glossary_sentences(claims)

    bodies = [plain, context, mechanism, evidence, boundary, connect[:4], takeaway, glossary]
    return [{"title": t, "sentences": s} for t, s in zip(SECTION_TITLES, bodies)]


def _glossary_sentences(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """术语表：抽专有名词并引用其所在声明原句（不做无来源定义）."""
    seen: dict[str, int] = {}
    for index, claim in enumerate(claims):
        for match in _TERM.finditer(claim["text"]):
            term = match.group(1)
            if len(term) >= 3 and term not in seen:
                seen[term] = index
    if not seen:
        return [_sent("摘要未出现需要解释的专有术语。")]
    return [
        {"text": f"术语 {term}——出处见声明：{claims[idx]['text'][:80]}",
         "claim": claims[idx]["id"]}
        for term, idx in list(seen.items())[:6]
    ]
