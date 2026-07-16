#!/usr/bin/env python3
"""ADP V0.1 deterministic content QA + single retry + factsheet fallback (ADP-S1-P03-T019).

On a generation failure or a QA failure, prefer to say less: retry at most once,
then fall back to the fact card (L0/L1) + raw evidence (L3) and never publish
templated garbage or an unsupported 人话版.

QA checks on a render payload:
  - language     : L0/L1 (人话版) has no large unexplained English block
  - empty        : L1 has facts; L0 text non-empty
  - duplicate    : L2 text is not a duplicate of another item's L2 (batch)
  - unsupported  : every L0/L1 claim carries an evidence locator
  - template     : L2 text (if generated) is not a boilerplate stub

publish(payload, generate, seen_l2) runs generate() for L2 with <=1 retry; if it
raises or the QA fails twice, it quarantines L2 and returns the fallback payload.

Exit codes when run as a self-test: 0 = all acceptance cases pass.
"""
import argparse, json, re, sys, pathlib

TEMPLATE_STUBS = ["暂无", "模板", "todo", "tbd", "lorem", "占位"]


def ascii_ratio(s):
    letters = [c for c in (s or "") if c.isalpha()]
    return sum(1 for c in letters if ord(c) < 128) / len(letters) if letters else 0.0


def qa_check(payload, seen_l2=None):
    problems = []
    layers = payload["layers"]
    l0 = layers["L0_15s"]["text"] or ""
    facts = layers["L1_2min"]["facts"]
    l2 = layers.get("L2_deep", {})
    # language: no large English block in L0/L1 (title claim excluded)
    if len(l0) >= 120 and ascii_ratio(l0) >= 0.85:
        problems.append("language: L0 large English block")
    for f in facts:
        if f.get("label") == "标题":
            continue
        v = f.get("value") or ""
        if len(v) >= 120 and ascii_ratio(v) >= 0.85:
            problems.append("language: L1 large English block")
    # empty
    if not l0.strip():
        problems.append("empty: L0 empty")
    if not facts:
        problems.append("empty: L1 no facts")
    # unsupported: every claim has a locator
    for c in layers["L0_15s"]["claims"] + facts:
        loc = c.get("locator") or {}
        if not (loc.get("item_id") and loc.get("field")):
            problems.append(f"unsupported: claim {c.get('label')} has no locator")
    # template + duplicate (only when L2 has generated text)
    txt = (l2.get("text") or "").strip()
    if l2.get("status") == "generated":
        if not txt or any(s in txt.lower() for s in TEMPLATE_STUBS) or len(txt) < 20:
            problems.append("template: L2 boilerplate/empty stub")
        if seen_l2 is not None and txt and txt in seen_l2:
            problems.append("duplicate: L2 duplicates another item")
    return problems


def fallback(payload):
    p = json.loads(json.dumps(payload))
    p["layers"]["L2_deep"] = {"status": "quarantined_fallback",
                              "reason": "generation failed or QA failed after 1 retry; publishing fact card + raw evidence only",
                              "text": None,
                              "prompt_ref": payload["layers"]["L2_deep"].get("prompt_ref")}
    p["publish_mode"] = "fact_card_and_raw_only"
    return p


def publish(payload, generate, seen_l2=None):
    """Run generate() for L2 with <=1 retry; on failure/QA-fail twice -> fallback.
    generate() -> str (L2 text) or raises. Returns (published_payload, attempts, mode)."""
    attempts = 0
    for _ in range(2):  # initial + at most one retry
        attempts += 1
        try:
            text = generate(payload)
        except Exception:
            continue  # timeout/error -> retry (if attempts left)
        cand = json.loads(json.dumps(payload))
        cand["layers"]["L2_deep"] = {**payload["layers"]["L2_deep"], "status": "generated", "text": text}
        if not qa_check(cand, seen_l2):
            cand["publish_mode"] = "full_l0_l3"
            return cand, attempts, "full_l0_l3"
    fb = fallback(payload)
    return fb, attempts, "fact_card_and_raw_only"


def _selftest(sample_path):
    payloads = json.loads(pathlib.Path(sample_path).read_text(encoding="utf-8"))
    p = payloads[0]
    results = []
    # case A: model timeout always -> at most 1 retry (2 attempts) then fallback
    def gen_timeout(_):
        raise TimeoutError("model timeout")
    out, att, mode = publish(p, gen_timeout)
    results.append(("timeout", att <= 2 and mode == "fact_card_and_raw_only" and out["layers"]["L2_deep"]["status"] == "quarantined_fallback"))
    # case B: missing-field/template garbage -> QA fails -> fallback
    def gen_template(_):
        return "暂无"
    out, att, mode = publish(p, gen_template)
    results.append(("template_garbage", att <= 2 and mode == "fact_card_and_raw_only"))
    # case C: duplicate L2 -> fallback
    seen = {"这是一段足够长的中文深度解释内容用于测试重复检测的场景。"}
    def gen_dup(_):
        return "这是一段足够长的中文深度解释内容用于测试重复检测的场景。"
    out, att, mode = publish(p, gen_dup, seen_l2=seen)
    results.append(("duplicate", mode == "fact_card_and_raw_only"))
    # case D: good generation -> full publish, 1 attempt, no fallback
    def gen_good(_):
        return "这是一段足够长的中文深度解释，覆盖研究问题、方法与关键结果，并区分事实、解释与推断三类。"
    out, att, mode = publish(p, gen_good)
    results.append(("good_generation", att == 1 and mode == "full_l0_l3" and out["layers"]["L2_deep"]["status"] == "generated"))
    # case E: baseline payload (L2 provisional, no gen) passes QA fact-layer checks
    results.append(("baseline_qa_no_unsupported", qa_check(p) == []))
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    allok = all(ok for _, ok in results)
    print("RESULT:", "PASS" if allok else "FAIL")
    return 0 if allok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", metavar="RENDER_PAYLOAD_JSON")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(_selftest(args.selftest))
    ap.print_help()


if __name__ == "__main__":
    main()
