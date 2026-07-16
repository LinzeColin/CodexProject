#!/usr/bin/env python3
"""ADP V0.1 content defect scanner (ADP-S1-P03-T017).

Deterministically labels each item for the current content defects, so every
defect traces back to an item_id/document_id and the running build_id (never a
subjective prose description). Defect types:
  - english_direct_output : Chinese-UI item whose summary is mostly English (FACT-002)
  - duplication           : title duplicates another item in the batch
  - templating            : summary is empty/near-empty or a boilerplate stub
  - no_evidence           : factsheet has no date AND no doi AND no doc_number
  - empty_section         : missing title or summary
  - board_pollution       : board3 item not matching policy intent (FACT-003)

Usage:
  python3 scan_defects.py --items items.json --factsheets factsheets.json \
      --build-id <id> --out defects.json
"""
import argparse, json, re, sys, pathlib
from collections import Counter

DEFECTS = ["english_direct_output", "duplication", "templating", "no_evidence", "empty_section", "board_pollution"]
# board3 = China policy/law; media/non-policy topics are pollution (FACT-003)
POLICY_HINT = re.compile(r"政策|法规|通知|公告|办法|条例|规定|决定|意见|方案|国务院|部委|发改委|财政部|央行|监管|规划|令")


def ascii_ratio(s):
    if not s:
        return 0.0
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    ascii_letters = [c for c in letters if ord(c) < 128]
    return len(ascii_letters) / len(letters)


def scan(items, factsheets, build_id):
    fs_by_id = {f["item_id"]: f for f in factsheets}
    title_counts = Counter((it.get("title") or "").strip() for it in items)
    rows = []
    for it in items:
        iid = it.get("id")
        board = it.get("board_id")
        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        fs = fs_by_id.get(iid, {})
        common = fs.get("common", {})
        bext = fs.get("board_ext", {})
        labels = []
        # english direct output: summary mostly ASCII letters (English) shown in a zh UI
        if summary and ascii_ratio(summary) >= 0.85 and len(summary) >= 40:
            labels.append("english_direct_output")
        # duplication
        if title and title_counts[title] > 1:
            labels.append("duplication")
        # templating / near-empty summary
        if not summary or len(summary) < 20:
            labels.append("templating")
        # no evidence anchor
        if not common.get("date") and not common.get("doi") and not bext.get("doc_number"):
            labels.append("no_evidence")
        # empty section
        if not title or not summary:
            labels.append("empty_section")
        # board pollution: board3 (policy) item whose title/summary lacks any policy hint
        if board == "board3" and not POLICY_HINT.search(title + " " + summary):
            labels.append("board_pollution")
        rows.append({"item_id": iid, "document_id": iid, "build_id": build_id,
                     "board_id": board, "source_id": it.get("source_id"),
                     "defects": sorted(set(labels))})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--factsheets", required=True)
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    fs = json.loads(pathlib.Path(args.factsheets).read_text(encoding="utf-8"))
    rows = scan(items, fs, args.build_id)
    summary = Counter()
    for r in rows:
        for d in r["defects"]:
            summary[d] += 1
    report = {"build_id": args.build_id, "baseline_status": "provisional_machine",
              "sample_count": len(rows), "defect_counts": dict(summary),
              "items_with_any_defect": sum(1 for r in rows if r["defects"])}
    out = {"before_report": report, "rows": rows}
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
