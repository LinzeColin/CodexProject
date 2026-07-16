#!/usr/bin/env python3
"""ADP V0.1 deterministic Factsheet extractor (ADP-S1-P03-T016).

Extracts stable facts (date / DOI / 文号 / 单位 / authors / agency) from a raw
item BEFORE any generated text. Missing fields are null, never fabricated. Output
conforms to schemas/factsheet.schema.json and is deterministic (no timestamps,
no randomness) so re-running on the same input is byte-identical.

Usage:
  python3 extract_factsheet.py --items items.json --out factsheets.json
  (items.json = list of D1 cn_items rows: id/board_id/source_id/kind/title/url/
   summary/categories/authors/published_at)
"""
import argparse, json, re, sys, pathlib

EXTRACTOR_VERSION = "adp.factsheet_extractor.v0_1"

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+")
# Chinese official document number 文号, e.g. 国发〔2026〕12号 / 财政部令[2026]3号 / 第12号
DOCNUM_RE = re.compile(r"[一-龥A-Za-z]{0,8}[〔\[（(]\s*20\d{2}\s*[〕\]）)]\s*第?\s*\d+\s*号"
                       r"|第\s*\d+\s*号(?:令|公告)?")
# number + unit tokens
UNIT_RE = re.compile(r"\d[\d,.]*\s*(?:%|％|个百分点|亿元|万元|亿美元|亿|万|bps|个基点|美元|元)")
DATE_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def norm_date(published_at):
    if not published_at:
        return None
    m = DATE_ISO_RE.search(str(published_at))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def extract_doi(*texts):
    for t in texts:
        if not t:
            continue
        m = DOI_RE.search(str(t))
        if m:
            return m.group(0).rstrip(").,;")
    return None


def extract_docnum(*texts):
    for t in texts:
        if not t:
            continue
        m = DOCNUM_RE.search(str(t))
        if m:
            return m.group(0).strip()
    return None


def extract_units(*texts):
    found = []
    for t in texts:
        if not t:
            continue
        for m in UNIT_RE.finditer(str(t)):
            tok = m.group(0).strip()
            if tok not in found:
                found.append(tok)
    return found or None


def split_authors(authors):
    if not authors:
        return None
    parts = [a.strip() for a in re.split(r"[;；]", str(authors)) if a.strip()]
    return parts or None


def factsheet(item):
    board = item.get("board_id")
    title = item.get("title") or None
    url = item.get("url") or None
    summary = item.get("summary") or ""
    doi = extract_doi(item.get("id"), url, summary)
    common = {
        "title": title, "url": url, "date": norm_date(item.get("published_at")),
        "authors": split_authors(item.get("authors")), "doi": doi,
        "categories": item.get("categories") or None,
    }
    board_ext = {"doc_number": None, "agency": None, "venue": None, "units": None}
    if board == "board3":
        board_ext["doc_number"] = extract_docnum(title, summary)
        board_ext["units"] = extract_units(title, summary)
    elif board == "board4":
        board_ext["units"] = extract_units(title, summary)
    elif board == "board2":
        board_ext["venue"] = item.get("source_id") or None
    # P0 fields: item_id/board_id/source_id/title/url/date + board doi(1,2) / doc_number(3)
    p0 = {"title": title is not None, "url": url is not None, "date": common["date"] is not None}
    if board in ("board1", "board2"):
        p0["doi"] = doi is not None
    if board == "board3":
        p0["doc_number"] = board_ext["doc_number"] is not None
    return {
        "item_id": item.get("id"), "board_id": board, "source_id": item.get("source_id"),
        "extractor_version": EXTRACTOR_VERSION, "baseline_status": "provisional_machine",
        "common": common, "board_ext": board_ext, "p0_present": p0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    sheets = [factsheet(it) for it in items]
    out = json.dumps(sheets, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(out + "\n", encoding="utf-8")
    print(f"extracted {len(sheets)} factsheets")


if __name__ == "__main__":
    main()
