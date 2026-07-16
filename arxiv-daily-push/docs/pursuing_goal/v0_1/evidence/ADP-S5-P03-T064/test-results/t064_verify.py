#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P03-T064 acceptance: Research Set / filtering / structured comparison.

Acceptance (TASK_INDEX row 64): Golden Set 中字段可回到原文；缺失不猜；筛选可重复。
  (Golden-Set fields trace back to the source; missing fields are not guessed; filtering reproducible.)

Deterministic. Re-derives from the TOOL (research_set) + the Golden Set fixtures -- never trusts the
report. Negative controls prove discrimination: a HALLUCINATED field value (not present in the source)
must FAIL the traceability check; a guess-a-default extractor would be caught; and a filter must be a
non-trivial, deterministic subset.
"""
import copy
import importlib.util
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import research_set as RS

T064 = V01 / "evidence" / "ADP-S5-P03-T064"
spec = importlib.util.spec_from_file_location("brs", str(T064 / "build_research_set.py"))
brs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brs)

fails = []
MISSING = brs.MISSING
rset = RS.make_set("golden", brs.PAPERS)
by_id = {p["paper_id"]: p for p in rset["papers"]}
golden = {p["paper_id"]: p["golden"] for p in brs.PAPERS}

# =============================================================== 1) 字段可回到原文 (traceable) + correctness
present_fields = 0
for pid, p in by_id.items():
    # every non-missing extracted value must be byte-exact at its recorded source offset
    if not RS.traces_to_source(p):
        fails.append(f"{pid}: an extracted field does not trace byte-exact to the source")
    for field, exp in golden[pid].items():
        got = p["fields"][field]
        if exp == MISSING:
            continue
        present_fields += 1
        if got.get("value") != exp:
            fails.append(f"{pid}.{field}: extracted {got.get('value')!r} != golden {exp!r}")
        # the evidence quote must equal the value and sit at the recorded offset in the source
        ev = got.get("evidence") or {}
        if ev.get("quote") != got.get("value"):
            fails.append(f"{pid}.{field}: evidence quote != value")
        if p["text"][ev.get("offset", -1):ev.get("offset", -1) + ev.get("length", 0)] != got.get("value"):
            fails.append(f"{pid}.{field}: value not located at its source offset (not traceable)")
if present_fields < 8:
    fails.append(f"too few present fields exercised ({present_fields})")
print(f"traceability: {present_fields} present fields all byte-exact to source; all papers trace_to_source=OK")

# =============================================================== 2) 缺失不猜 (missing not guessed)
missing_checked = 0
for pid, g in golden.items():
    for field, exp in g.items():
        if exp != MISSING:
            continue
        missing_checked += 1
        got = by_id[pid]["fields"][field]
        if got.get("value") is not None or got.get("status") != "missing":
            fails.append(f"{pid}.{field}: source omits this field but extractor produced {got!r} (guessed!)")
if missing_checked < 4:
    fails.append(f"too few missing fields exercised ({missing_checked})")

# NEGATIVE CONTROL: the traceability check genuinely rejects a HALLUCINATED value. Inject a fabricated
# field value into a paper (a guess not present at the claimed offset) -> traces_to_source must be False.
halluc = copy.deepcopy(by_id["P004"])   # P004 has no extractable fields
halluc["fields"]["method"] = {"value": "使用了某种未在原文出现的方法",
                              "evidence": {"offset": 0, "length": 10, "quote": "..."}}
if RS.traces_to_source(halluc):
    fails.append("traceability check accepted a hallucinated value -> the 回到原文 guarantee is vacuous")

# NEGATIVE CONTROL: a guess-a-default extractor (fills missing with a canned value) would be caught by
# BOTH the missing-check (value != None) and traceability (value not at any source offset).
def _guessing_extract(text):
    out = RS.extract_fields(text)
    for f, v in out.items():
        if v.get("value") is None:
            v.clear(); v.update({"value": "N/A", "evidence": {"offset": 0, "length": 3, "quote": "N/A"}})
    return out
p4_guessed = {"paper_id": "P004", "text": brs.PAPERS[3]["text"], "fields": _guessing_extract(brs.PAPERS[3]["text"])}
if RS.traces_to_source(p4_guessed):
    fails.append("a guess-a-default extractor passed traceability -> control is vacuous")
print(f"缺失不猜: {missing_checked} missing fields all report status=missing; hallucination + guess-default both rejected")

# PRECISION CONTROLS: an ASCII '.' inside a decimal must NOT split the value; a trailing-'n' word must
# NOT false-match the bare n=.. statistic. Both must stay byte-exact and correct.
dec = RS.extract_fields("结果：准确率达到 92.5%。")
if dec["result"]["value"] != "准确率达到 92.5%":
    fails.append(f"decimal split by '.' boundary: {dec['result']['value']!r}")
eng = RS.extract_fields("Result: accuracy is 88.7 percent.")
if eng["result"]["value"] != "accuracy is 88.7 percent":
    fails.append(f"english decimal/sentence boundary wrong: {eng['result']['value']!r}")
falsep = RS.extract_fields("The activation function = 5 layers were used.")
if falsep["sample"].get("value") is not None:
    fails.append(f"bare n=.. false-matched a trailing-n word: {falsep['sample']!r}")
realstat = RS.extract_fields("We evaluate on n = 64 items.")
if realstat["sample"].get("value") != "n = 64":
    fails.append(f"genuine bare n=.. stat not captured: {realstat['sample']!r}")
print(f"precision: decimal '92.5%' kept whole; 'function = 5' not matched; real 'n = 64' captured")

# =============================================================== 3) 筛选可重复 (reproducible filtering)
runs = [ [q["paper_id"] for q in RS.filter_set(rset, has_field="result")["papers"]] for _ in range(3) ]
if len({tuple(r) for r in runs}) != 1:
    fails.append(f"filtering is not reproducible across runs: {runs}")
has_result = runs[0]
if has_result != sorted(has_result):
    fails.append("filter result is not in deterministic (sorted) order")
if not (0 < len(has_result) < len(rset["papers"])):
    fails.append(f"has_result filter is trivial (all or none): {has_result}")
# a different filter yields a different result (discrimination)
kw = [q["paper_id"] for q in RS.filter_set(rset, keyword="网络", field="method")["papers"]]
if kw == has_result:
    fails.append("two different filters returned identical results -> filter not actually applied")
# expected exact filter outcomes from the Golden Set
if has_result != ["P001", "P002", "P005"]:
    fails.append(f"has_result filter wrong: {has_result}")
if kw != ["P001", "P003"]:
    fails.append(f"method~网络 filter wrong: {kw}")
print(f"filtering: has_result={has_result} (3 runs identical); method~网络={kw}; non-trivial + deterministic")

# comparison table sanity: cell carries value+evidence when present, missing flag when absent
table = RS.comparison_table(rset)
for row in table["rows"]:
    for c in table["columns"]:
        cell = row[c]
        if cell["missing"] and cell["value"] is not None:
            fails.append(f"{row['paper_id']}.{c}: missing flag but has a value")
        if not cell["missing"] and not cell.get("evidence"):
            fails.append(f"{row['paper_id']}.{c}: present value without evidence locator")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
