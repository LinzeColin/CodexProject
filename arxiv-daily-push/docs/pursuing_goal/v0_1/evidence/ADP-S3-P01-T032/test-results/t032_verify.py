#!/usr/bin/env python3
"""ADP-S3-P01-T032 acceptance: fixture + contract-test harness catches template drift in CI.

Acceptance (TASK_INDEX): 任一字段漂移、附件丢失或分页断裂会使相应 connector test 失败。
Deterministic; no network. Positives (normal/attachment/pagination) pass against golden JSON;
each drift type (field / attachment / pagination) is shown to FAIL the matching contract.
"""
import sys, json, pathlib, shutil, tempfile
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T032 = V01 / "evidence" / "ADP-S3-P01-T032"
FX, EXP = T032 / "fixtures", T032 / "expected"
sys.path.insert(0, str(V01 / "tools"))
import connector_contract as CC, official_connector as OC  # noqa: E402

fails = []

# --- positives: the frozen fixtures parse to the golden expected JSON -----------------------
rep = CC.run_contract(FX, EXP)
print("positive contract: all_passed =", rep["all_passed"])
for r in rep["results"]:
    print(f"  {r['fixture']}: passed={r['passed']} diffs={r['diffs']}")
if not rep["all_passed"]:
    fails.append("golden fixtures did not pass their own contract")

# --- negative 1: FIELD DRIFT -- changed.html renames the 文号 class -> doc_number lost -------
conn = CC.ReferenceOfficialConnector(FX)
normal_exp = json.loads((EXP / "normal.json").read_text(encoding="utf-8"))
drift = CC.check_doc(conn, "changed.html", normal_exp)
print("\nfield drift (changed.html vs normal expected): passed =", drift["passed"], "| diffs =", drift["diffs"])
if drift["passed"]:
    fails.append("field drift NOT caught: changed.html passed the normal contract")
if not any("doc_number" in d for d in drift["diffs"]):
    fails.append("field drift not attributed to doc_number")

# --- negative 2: ATTACHMENT LOSS -- drop one attachment from attachment.html -----------------
with tempfile.TemporaryDirectory() as td:
    tdir = pathlib.Path(td)
    for f in FX.glob("*.html"):
        shutil.copy(f, tdir / f.name)
    html = (tdir / "attachment.html").read_text(encoding="utf-8")
    html = html.replace('<a class="doc-att" href="/att/jiedu.docx">政策解读.docx</a>', "")  # lose an attachment
    (tdir / "attachment.html").write_text(html, encoding="utf-8")
    conn2 = CC.ReferenceOfficialConnector(tdir)
    att_exp = json.loads((EXP / "attachment.json").read_text(encoding="utf-8"))
    lost = CC.check_doc(conn2, "attachment.html", att_exp)
    print("attachment loss (dropped 政策解读.docx): passed =", lost["passed"], "| diffs =", lost["diffs"])
    if lost["passed"]:
        fails.append("attachment loss NOT caught")
    if not any("attachments" in d for d in lost["diffs"]):
        fails.append("attachment loss not attributed to attachments")

# --- negative 3: PAGINATION BREAK -- remove the 'next' link so page 2 is never crawled -------
with tempfile.TemporaryDirectory() as td:
    tdir = pathlib.Path(td)
    for f in FX.glob("*.html"):
        shutil.copy(f, tdir / f.name)
    html = (tdir / "pagination.html").read_text(encoding="utf-8")
    html = html.replace('<a class="next" href="?page=2">下一页</a>', "")  # break pagination
    (tdir / "pagination.html").write_text(html, encoding="utf-8")
    conn3 = CC.ReferenceOfficialConnector(tdir)
    pg_exp = json.loads((EXP / "pagination.json").read_text(encoding="utf-8"))
    broke = CC.check_pagination(conn3, pg_exp)
    print("pagination break (removed next link): passed =", broke["passed"], "| diffs =", broke["diffs"],
          "| got", len(broke["got"]), "of expected", len(pg_exp))
    if broke["passed"]:
        fails.append("pagination break NOT caught")
    if len(broke["got"]) >= len(pg_exp):
        fails.append("pagination break did not reduce discovered items")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
