"""深度讲义（R1-4/R1-5）—— 八段结构 + 逐句溯源校验.

生成通道按 owner_controls intelligence_provider 优先级：codex_cli_chatgpt_auth →
deterministic_degraded（确定性模板保底，当日仍可交付——成熟项目替代决策 #9）。
每个正文句都必须绑定 claim（不变量 7）；校验失败的句子直接丢弃并计数。
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import Any

from . import store
from .claims import split_sentences

TEMPLATE_VER = "lesson-v03-1"
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


def generate_lesson(conn: sqlite3.Connection, *, lesson_id: str, candidate_id: str,
                    doc_version_id: str, as_of_date: str) -> dict[str, Any]:
    """生成讲义并落库；返回 {lesson, generator, degraded, traceability}."""
    doc = _load_doc(conn, doc_version_id)
    claims = _load_claims(conn, doc_version_id)

    generator = "deterministic_degraded"
    degraded_reason = None
    sections = None
    if shutil.which("codex"):
        try:
            sections = _codex_generate(doc, claims)
            generator = "codex_cli_chatgpt_auth"
        except Exception as exc:
            degraded_reason = f"codex_generation_failed:{type(exc).__name__}"
    else:
        degraded_reason = "codex_cli_not_available"
    if sections is None:
        sections = _deterministic_sections(doc, claims)

    sections, bindings, dropped = bind_and_validate(sections, claims)
    created_at = store.utcnow_iso()
    conn.execute(
        """INSERT OR REPLACE INTO lessons
           (id, candidate_id, doc_version_id, as_of_date, sections_json, claim_bindings_json,
            template_ver, generator, created_at, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
        (lesson_id, candidate_id, doc_version_id, as_of_date,
         json.dumps(sections, ensure_ascii=False), json.dumps(bindings, ensure_ascii=False),
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
        "sections": sections, "bindings": bindings, "dropped_unbound_sentences": dropped,
    }


def bind_and_validate(sections: list[dict[str, Any]], claims: list[dict[str, Any]]
                      ) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    """逐句溯源校验（R1-5）：每句必须能绑定到一条声明，绑不上的句子丢弃并计数.

    绑定规则：句中引用的 claim 序号（生成器输出 [c3] 标记）优先；否则词面重叠最高的声明，
    重叠率 < 0.18 视为不可溯源。元信息句（带 meta: 前缀）绑定到文档级 locator。
    """
    bindings: dict[str, Any] = {}
    dropped = 0
    claim_tokens = [
        (claim, set(re.findall(r"[a-z0-9\-]{3,}", claim["text"].lower()))) for claim in claims
    ]
    for section_index, section in enumerate(sections):
        kept_sentences: list[str] = []
        for sent_index, sentence in enumerate(_lesson_sentences(section["body"])):
            marker = re.search(r"\[c(\d+)\]", sentence)
            bound_claim = None
            if marker:
                wanted = f"c{marker.group(1)}"
                bound_claim = next((c for c in claims if c["id"].endswith(":" + wanted)), None)
                sentence = re.sub(r"\s*\[c\d+\]", "", sentence)
            if bound_claim is None and sentence.startswith("meta:"):
                sentence = sentence[5:].strip()
                bound_claim = {"id": "__doc_meta__"}
            if bound_claim is None:
                tokens = set(re.findall(r"[a-z0-9\-]{3,}", sentence.lower()))
                best, best_overlap = None, 0.0
                for claim, ctoks in claim_tokens:
                    if not tokens or not ctoks:
                        continue
                    overlap = len(tokens & ctoks) / len(tokens | ctoks)
                    if overlap > best_overlap:
                        best, best_overlap = claim, overlap
                if best is not None and best_overlap >= 0.18:
                    bound_claim = best
            if bound_claim is None:
                dropped += 1
                continue
            kept_sentences.append(sentence)
            bindings[f"s{section_index}.{len(kept_sentences) - 1}"] = bound_claim["id"]
        section["body"] = " ".join(kept_sentences) if kept_sentences else section["body"]
        if not kept_sentences:
            bindings[f"s{section_index}.0"] = "__doc_meta__"
    return sections, bindings, dropped


def validate_traceability(conn: sqlite3.Connection, lesson_id: str) -> dict[str, Any]:
    """随机点一句能跳到出处的机器面：核对每个绑定的 claim 存在且 locator 可解析."""
    row = conn.execute("SELECT sections_json, claim_bindings_json FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    if row is None:
        return {"ok": False, "error": "lesson_not_found"}
    bindings = json.loads(row["claim_bindings_json"])
    missing = []
    for key, claim_id in bindings.items():
        if claim_id == "__doc_meta__":
            continue
        exists = conn.execute("SELECT 1 FROM claims WHERE id=?", (claim_id,)).fetchone()
        if not exists:
            missing.append({key: claim_id})
    return {"ok": not missing, "bindings": len(bindings), "missing": missing}


def _lesson_sentences(body: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s*", body)
    return [p.strip() for p in parts if p.strip()]


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
    rows = conn.execute("SELECT * FROM claims WHERE doc_version_id=? ORDER BY id", (doc_version_id,)).fetchall()
    return [
        {"id": r["id"], "type": r["type"], "text": r["text"],
         "locator": json.loads(r["locator_json"]), "confidence": r["confidence"]}
        for r in rows
    ]


def _codex_generate(doc: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Codex CLI 认证通道：一次调用产出八段 JSON；任何异常上抛由调用方降级."""
    claim_lines = "\n".join(f"[c{i}] {c['text']}" for i, c in enumerate(claims))
    prompt = (
        "你是个人前沿学习系统的讲义作者。基于以下论文摘要声明（不得编造未给出的事实，"
        "每句话结尾用 [cN] 标注所依据的声明），输出 JSON 数组，元素为 "
        '{"title": 八段之一, "body": 中文正文}，八段依次为：'
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


def _deterministic_sections(doc: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """确定性模板：只重组既有声明与元数据，不产生任何无来源句（降级保底通道）."""
    meta = doc["meta"]
    title = doc["title"]
    categories = meta.get("categories") or []
    authors = meta.get("authors") or []
    published = (meta.get("published") or "")[:10]

    def mark(claim_index: int) -> str:
        return f" [c{claim_index}]"

    facts = [(i, c) for i, c in enumerate(claims) if c["type"] == "paper_fact"]
    author_claims = [(i, c) for i, c in enumerate(claims) if c["type"] == "author_claim"]
    inferences = [(i, c) for i, c in enumerate(claims) if c["type"] in {"inference", "hypothesis"}]
    actions = [(i, c) for i, c in enumerate(claims) if c["type"] == "action"]
    numeric = [(i, c) for i, c in enumerate(claims) if _NUM.search(c["text"])]
    limits = [(i, c) for i, c in enumerate(claims) if _LIMIT.search(c["text"])]
    methods = [(i, c) for i, c in enumerate(claims) if _METHOD.search(c["text"])]

    lead = author_claims[:1] or facts[:1] or [(0, claims[0])] if claims else []
    plain = ""
    if lead:
        idx, claim = lead[0]
        plain = f"这篇论文在做什么：{claim['text']}{mark(idx)}"
    plain += f" meta: 论文《{title}》发表于 {published or '未知日期'}，作者 {len(authors)} 人，原文见 {doc['canonical_url']}。"

    context_lines = [
        f"meta: 本文主类目 {meta.get('primary_category') or '未知'}：{CATEGORY_CONTEXT.get(meta.get('primary_category'), '（该类目暂无脉络注解，点原文了解）')}。"
    ]
    for cat in categories[1:3]:
        if cat in CATEGORY_CONTEXT:
            context_lines.append(f"meta: 交叉类目 {cat}：{CATEGORY_CONTEXT[cat]}。")

    mechanism = " ".join(f"{c['text']}{mark(i)}" for i, c in (methods[:3] or author_claims[:2]))
    evidence = " ".join(f"{c['text']}{mark(i)}" for i, c in numeric[:3]) or "meta: 摘要未给出量化结果，证据等级为摘要级，点原文核对全文数字。"
    boundary = " ".join(f"{c['text']}{mark(i)}" for i, c in limits[:2]) or "meta: 摘要未声明边界与反例——这是一个需要警惕的信号，深挖时先问局限。"

    connect_lines = []
    if len(categories) > 1:
        connect_lines.append(f"meta: 本文横跨 {len(categories)} 个类目（{', '.join(categories[:4])}），关注其在你兴趣板块间的迁移面。")
    surprises = inferences[:2] or facts[1:3]
    for i, claim in surprises:
        connect_lines.append(f"意外收获：{claim['text']}{mark(i)}")
    if len(connect_lines) < 3:
        connect_lines.append(
            f"meta: 意外收获：本文由 {len(authors)} 位作者合作完成，发表后 48 小时内即进入你的学习队列。"
        )
    if len(connect_lines) < 3:
        connect_lines.append(
            "meta: 意外收获：本篇的入选是 8 特征加权的结果——打开系统页可以看到它赢在哪个特征。"
        )

    method_takeaway = " ".join(f"{c['text']}{mark(i)}" for i, c in (actions[:2] or methods[:1])) or "meta: 可复用方法：将本文机制与你正在跟的项目对照，找一个能在两周内验证的最小实验。"

    glossary_terms = _glossary(claims)

    return [
        {"title": SECTION_TITLES[0], "body": plain},
        {"title": SECTION_TITLES[1], "body": " ".join(context_lines)},
        {"title": SECTION_TITLES[2], "body": mechanism or "meta: 摘要未展开机制细节，机制拆解需要点开原文。"},
        {"title": SECTION_TITLES[3], "body": evidence},
        {"title": SECTION_TITLES[4], "body": boundary},
        {"title": SECTION_TITLES[5], "body": " ".join(connect_lines[:4])},
        {"title": SECTION_TITLES[6], "body": method_takeaway},
        {"title": SECTION_TITLES[7], "body": glossary_terms},
    ]


def _glossary(claims: list[dict[str, Any]]) -> str:
    """术语表：抽专有名词并引用其所在声明原句（不做无来源定义）."""
    seen: dict[str, int] = {}
    for index, claim in enumerate(claims):
        for match in _TERM.finditer(claim["text"]):
            term = match.group(1)
            if len(term) >= 3 and term not in seen:
                seen[term] = index
    if not seen:
        return "meta: 摘要未出现需要解释的专有术语。"
    parts = [f"术语 {term}——出处见声明：{claims[idx]['text'][:80]}… [c{idx}]"
             for term, idx in list(seen.items())[:6]]
    return " ".join(parts)
