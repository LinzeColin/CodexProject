#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P04-T067 acceptance: Library / notes / Provenance export.

Acceptance (TASK_INDEX row 67): 导出包含原始 URL、版本、抓取时间、claim evidence 和许可提示。
  (every export contains the original URL, the version, the fetch time, the claim evidence, and a
   license notice.)

Deterministic. Re-derives from the TOOL (library_export) + fixtures -- never trusts the report.
Negative control: an under-provenanced save/export is REFUSED (so completeness is not a coincidence),
and a lax exporter that skipped the check would leak an incomplete entry.
"""
import csv
import importlib.util
import io
import json
import pathlib
import sys

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import library_export as LX

T067 = V01 / "evidence" / "ADP-S5-P04-T067"
spec = importlib.util.spec_from_file_location("blx", str(T067 / "build_library_export.py"))
blx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blx)

fails = []
lib = blx.build_library()
PF = list(LX.PROVENANCE_FIELDS)   # source_url, version, fetched_at, claim_evidence, license
if PF != ["source_url", "version", "fetched_at", "claim_evidence", "license"]:
    fails.append(f"provenance field set wrong: {PF}")

# =============================================================== 1) every format carries all provenance
# use the tool's own blank semantics so a genuine 0-valued field would not spuriously fail
blank = LX._is_blank

# JSON: each entry's provenance has all 5 non-blank fields
j = json.loads(LX.export_json(lib))
for e in j["entries"]:
    for f in PF:
        if blank(e["provenance"].get(f)):
            fails.append(f"JSON entry {e['canonical_id']} missing provenance {f}")

# CSV: a column per provenance field, every cell non-blank
rows = list(csv.DictReader(io.StringIO(LX.export_csv(lib))))
for f in PF:
    if f not in rows[0]:
        fails.append(f"CSV missing provenance column {f}")
for r in rows:
    for f in PF:
        if blank(r.get(f)):
            fails.append(f"CSV row {r.get('canonical_id')} empty provenance {f}")

# Markdown: check PER-ENTRY (a whole-string substring check would pass even if only one entry had a
# field). Re-export each entry alone and require all 5 labels+values in ITS block.
labels = {"source_url": "Source URL:", "version": "Version:", "fetched_at": "Fetched at:",
          "claim_evidence": "Claim evidence:", "license": "License:"}
for e in lib["entries"]:
    single = {"name": lib["name"], "entries": [e]}
    block = LX.export_markdown(single)
    for f in PF:
        if labels[f] not in block:
            fails.append(f"Markdown block for {e['canonical_id']} missing label {f}")
        # the value must appear on its own labeled line (first line of the value for multi-line values)
        first_line = str(e["provenance"][f]).splitlines()[0] if str(e["provenance"][f]).splitlines() else str(e["provenance"][f])
        if first_line not in block:
            fails.append(f"Markdown block for {e['canonical_id']} missing {f} value")
print(f"provenance present: JSON per-entry + CSV per-row + MD per-entry-block all carry {PF} for {len(lib['entries'])} entries")

# CSV round-trips format-hostile values (comma/quote/newline) LOSSLESSLY
tricky = next(e for e in lib["entries"] if e["canonical_id"] == "arxiv:2402.55555")
tr_row = next(r for r in rows if r["canonical_id"] == "arxiv:2402.55555")
for f in PF:
    if tr_row[f] != str(tricky["provenance"][f]):
        fails.append(f"CSV did not losslessly round-trip {f} with special chars: {tr_row[f]!r} != {tricky['provenance'][f]!r}")
print("csv integrity: comma/quote/newline values round-trip losslessly via DictReader")

# license notice explicitly present in all three formats (每种格式都含许可提示)
for fmt in ("markdown", "csv", "json"):
    text = LX.export(lib, fmt)
    if not all(str(e["provenance"]["license"]) in text for e in lib["entries"]):
        fails.append(f"{fmt} export is missing a license notice")
print("license notice present in markdown, csv, and json")

# =============================================================== 2) round-trip (JSON) keeps provenance
rt = json.loads(LX.export_json(lib))
for orig, back in zip(lib["entries"], rt["entries"]):
    if orig["provenance"] != back["provenance"]:
        fails.append(f"JSON round-trip lost/changed provenance for {orig['canonical_id']}")

# =============================================================== 3) NEGATIVE CONTROL: un-provenanced is refused
# saving an item missing license + claim_evidence must raise (never silently saved)
try:
    LX.add_to_library(LX.new_library(), blx.BAD_ITEM)
    fails.append("an item with incomplete provenance was saved (should be refused)")
except ValueError:
    pass
# and if such an entry somehow reaches export, the exporter refuses it (defense in depth)
tainted = {"name": "t", "entries": [{
    "canonical_id": "x", "title": "x", "note": None, "collection": None,
    "provenance": {"source_url": "u", "version": "v", "fetched_at": "t",
                   "claim_evidence": "e", "license": ""}}]}  # empty license
for fmt in ("markdown", "csv", "json"):
    try:
        LX.export(tainted, fmt)
        fails.append(f"{fmt} exported an entry with an empty license (provenance check not enforced)")
    except ValueError:
        pass
# provenance_complete genuinely discriminates
if LX.provenance_complete(tainted["entries"][0]):
    fails.append("provenance_complete accepted an entry with an empty license -> vacuous")
print("refusal control: incomplete provenance is refused on save AND on export (all 3 formats)")

print("\nACCEPTANCE = " + ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
