#!/usr/bin/env python3
"""ADP V0.1 content Release Gate (ADP-S1-P03-T020).

Gates a content bundle (render payloads) against the S1-P03 acceptance:
  1. key claim evidence 100%     -- every key number/date/result is located
  2. empty section / template leak 0 -- no empty L0/L1 fact layer, no template stub
  3. P0 fact accuracy >= threshold   -- machine extraction fidelity: each payload's
     P0 fact equals the source item value (title/date), provisional pending human
On failure it blocks ONLY the content bundle (returns scope=content_bundle), not
the whole deploy.

Exit 0 => RELEASE (content bundle passes). Exit 1 => BLOCK_CONTENT_BUNDLE.

Usage:
  python3 content_release_gate.py --payloads payloads.json --items items.json \
      [--p0-threshold 0.99]
"""
import argparse, json, re, sys, pathlib

KEY_LABELS = {"日期", "DOI", "关键数字", "文号"}
DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def norm_date(s):
    if not s:
        return None
    m = DATE_ISO.search(str(s))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def gate(payloads, items, p0_threshold):
    by_id = {it["id"]: it for it in items}
    n = len(payloads)
    key_unlocated = 0
    empty_or_template = 0
    p0_faithful = 0
    p0_total = 0
    for p in payloads:
        layers = p["layers"]
        l0 = layers["L0_15s"]
        l1 = layers["L1_2min"]["facts"]
        l2 = layers.get("L2_deep", {})
        # 1. key claims located
        for c in l0["claims"] + l1:
            if c.get("label") in KEY_LABELS:
                loc = c.get("locator") or {}
                if not (loc.get("item_id") and loc.get("field")):
                    key_unlocated += 1
        # 2. empty/template leak (fact layers must be non-empty; L2 must not have a template stub if 'generated')
        if not (l0.get("text") or "").strip() or not l1:
            empty_or_template += 1
        if l2.get("status") == "generated":
            t = (l2.get("text") or "").strip()
            if not t or any(s in t.lower() for s in ["暂无", "模板", "占位", "tbd", "todo"]):
                empty_or_template += 1
        # 3. P0 fidelity: title & date facts equal the source values
        src = by_id.get(p["item_id"], {})
        title_fact = next((c["value"] for c in l1 if c.get("label") == "标题"), None)
        date_fact = next((c["value"] for c in l1 if c.get("label") == "日期"), None)
        p0_total += 1
        title_ok = (title_fact or "") == (src.get("title") or "")
        date_ok = (date_fact) == norm_date(src.get("published_at"))
        if title_ok and date_ok:
            p0_faithful += 1
    p0_accuracy = (p0_faithful / p0_total) if p0_total else 1.0
    checks = {
        "key_claim_evidence_100": key_unlocated == 0,
        "empty_or_template_leak_0": empty_or_template == 0,
        "p0_fact_accuracy_ok": p0_accuracy >= p0_threshold,
    }
    report = {"scope": "content_bundle", "sample_count": n,
              "key_unlocated": key_unlocated, "empty_or_template": empty_or_template,
              "p0_fact_accuracy": round(p0_accuracy, 4), "p0_threshold": p0_threshold,
              "baseline_status": "provisional_machine", "checks": checks}
    return all(checks.values()), report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payloads", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--p0-threshold", type=float, default=0.99)
    args = ap.parse_args()
    payloads = json.loads(pathlib.Path(args.payloads).read_text(encoding="utf-8"))
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    ok, report = gate(payloads, items, args.p0_threshold)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("RESULT:", "RELEASE" if ok else "BLOCK_CONTENT_BUNDLE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
