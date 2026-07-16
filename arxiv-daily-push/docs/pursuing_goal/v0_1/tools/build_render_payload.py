#!/usr/bin/env python3
"""ADP V0.1 L0-L3 人话版 render payload builder (ADP-S1-P03-T018).

Deterministically builds the four-layer render payload from an item + its
factsheet. The fact layers (L0 15s, L1 2min) are Chinese fact statements with an
evidence locator on every key number/date/result; the raw English abstract is
placed ONLY in L3, explicitly labeled 原始证据, never as unexplained content in
L0/L1. L2 (deep explanation) is a contract slot marked provisional_pending_model
(requires the model; the Owner directive keeps it provisional). Distinguishes
fact / interpretation / inference (L0/L1 are fact-only; interpretation/inference
belong to L2).

Usage:
  python3 build_render_payload.py --items items.json --factsheets fs.json \
      --build-id <id> --out payloads.json
"""
import argparse, json, sys, pathlib

BOARD_LABEL = {"board1": "研究前沿", "board2": "顶级期刊", "board3": "中国政策法规",
               "board4": "美国科技金融", "board5": "跨板块总览"}


def claim(label, value, item_id, field, ctype="fact"):
    return {"label": label, "value": value, "claim_type": ctype,
            "locator": {"item_id": item_id, "field": field}}


def build(item, fs):
    iid = item.get("id")
    board = item.get("board_id")
    common = fs.get("common", {})
    bext = fs.get("board_ext", {})
    date = common.get("date")
    src = item.get("source_id")
    title = common.get("title")

    # L0: one-line Chinese fact summary (source · board · date). Title shown as a labeled title, not a paragraph.
    l0_bits = [f"来源 {src}", f"板块 {BOARD_LABEL.get(board, board)}"]
    if date:
        l0_bits.append(f"日期 {date}")
    l0_text = " · ".join(l0_bits) + "。"
    l0_claims = [claim("来源", src, iid, "source_id"),
                 claim("板块", BOARD_LABEL.get(board, board), iid, "board_id")]
    if date:
        l0_claims.append(claim("日期", date, iid, "common.date"))

    # L1: structured Chinese facts, each with a locator (key numbers/dates/results 100% located)
    facts = [claim("标题", title, iid, "common.title"),
             claim("来源", src, iid, "source_id"),
             claim("板块", BOARD_LABEL.get(board, board), iid, "board_id")]
    if date:
        facts.append(claim("日期", date, iid, "common.date"))
    if common.get("doi"):
        facts.append(claim("DOI", common["doi"], iid, "common.doi"))
    if common.get("authors"):
        facts.append(claim("作者", "; ".join(common["authors"][:6]), iid, "common.authors"))
    if common.get("categories"):
        facts.append(claim("分类", common["categories"], iid, "common.categories"))
    if bext.get("doc_number"):
        facts.append(claim("文号", bext["doc_number"], iid, "board_ext.doc_number"))
    if bext.get("units"):
        facts.append(claim("关键数字", "、".join(bext["units"][:8]), iid, "board_ext.units"))

    # L3: raw evidence -- the (possibly English) abstract goes here, explicitly labeled
    l3 = {"label": "原始证据（未加工原文，可能为英文）", "raw_title": item.get("title"),
          "raw_abstract": item.get("summary") or None, "url": common.get("url"), "doi": common.get("doi")}

    l2 = {"status": "provisional_pending_model",
          "prompt_ref": f"BOARD_PROMPTS.md#{board}",
          "text": None,
          "claim_types_required": ["fact", "interpretation", "inference"]}

    return {"item_id": iid, "build_id": None, "board_id": board,
            "baseline_status": "provisional_machine",
            "layers": {"L0_15s": {"text": l0_text, "claims": l0_claims},
                       "L1_2min": {"facts": facts},
                       "L2_deep": l2, "L3_evidence": l3}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--factsheets", required=True)
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    fs = {f["item_id"]: f for f in json.loads(pathlib.Path(args.factsheets).read_text(encoding="utf-8"))}
    payloads = []
    for it in items:
        p = build(it, fs.get(it.get("id"), {}))
        p["build_id"] = args.build_id
        payloads.append(p)
    out = json.dumps(payloads, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(out + "\n", encoding="utf-8")
    print(f"built {len(payloads)} render payloads")


if __name__ == "__main__":
    main()
