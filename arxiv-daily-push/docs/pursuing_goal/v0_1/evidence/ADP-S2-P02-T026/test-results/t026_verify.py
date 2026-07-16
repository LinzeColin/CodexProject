#!/usr/bin/env python3
"""ADP-S2-P02-T026 acceptance: version diff + template-noise filter + replay idempotency.

Acceptance (TASK_INDEX): 正文/附件/状态实质变化增版本；页脚/导航变化不增；三次重放结果一致。
Deterministic; no network/clock/random. Imports the tool under test (version_engine.py).
"""
import sys, json, pathlib
TOOLS = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1/tools")
sys.path.insert(0, str(TOOLS))
import version_engine as ve  # noqa: E402

CID = "doi:10.5555/abc"
FOOTER = "责任编辑：李四\n阅读 12345\n分享到微信\n发布于 3 分钟前\n版权所有 © 2026 某网\n京ICP备12345号"

# one canonical document rendered/updated over time
A = {"canonical_id": CID, "body": "研究发现 X 导致 Y。样本量 1000。", "status": "active",
     "attachments": [{"name": "paper.pdf", "sha256": "h1"}], "doc_date": "2026-03-01"}
# B: identical substance, only template noise added (footer/nav/share/counts/relative time)
B = {"canonical_id": CID, "body": "研究发现 X 导致 Y。样本量 1000。\n" + FOOTER, "status": "active",
     "attachments": [{"name": "paper.pdf", "sha256": "h1"}], "doc_date": "2026-03-01"}
# C: substantive BODY change (a correction to the sample size)
C = {"canonical_id": CID, "body": "研究发现 X 导致 Y。样本量已更正为 2000。\n" + FOOTER, "status": "active",
     "attachments": [{"name": "paper.pdf", "sha256": "h1"}], "doc_date": "2026-04-01"}
# D: substantive ATTACHMENT change (a supplement added), body same as C
D = {"canonical_id": CID, "body": "研究发现 X 导致 Y。样本量已更正为 2000。\n" + FOOTER, "status": "active",
     "attachments": [{"name": "paper.pdf", "sha256": "h1"}, {"name": "supp.pdf", "sha256": "h2"}], "doc_date": "2026-04-01"}
# E: substantive STATUS change (withdrawn), everything else same as D
E = {"canonical_id": CID, "body": "研究发现 X 导致 Y。样本量已更正为 2000。\n" + FOOTER, "status": "withdrawn",
     "attachments": [{"name": "paper.pdf", "sha256": "h1"}, {"name": "supp.pdf", "sha256": "h2"}], "doc_date": "2026-04-01"}
# F: exact replay of E (same substance) -> must not add a version
F = dict(E)

SEQ = [A, B, C, D, E, F]
fails = []

# --- pairwise diff assertions --------------------------------------------------------------
d_ab = ve.diff(A, B)
print("A->B (noise only):", d_ab)
if not d_ab["noise_only"] or d_ab["substantive"]:
    fails.append("A->B footer/nav noise wrongly flagged substantive")

d_bc = ve.diff(B, C)
print("B->C (body):", d_bc)
if not (d_bc["body_changed"] and d_bc["substantive"]):
    fails.append("B->C body change not detected")

d_cd = ve.diff(C, D)
print("C->D (attachment):", d_cd)
if not (d_cd["attachments_changed"] and d_cd["substantive"] and not d_cd["body_changed"]):
    fails.append("C->D attachment change not isolated")

d_de = ve.diff(D, E)
print("D->E (status):", d_de)
if not (d_de["status_changed"] and d_de["substantive"] and not d_de["body_changed"] and not d_de["attachments_changed"]):
    fails.append("D->E status change not isolated")

# --- over-strip guard: a REAL sentence that merely starts with 发布于 and contains a colon must
#     NOT be treated as a timestamp/noise line (else a real revision is silently dropped) --------
real_sentence = "发布于顶级期刊：Nature 的这项研究改变了结论。"
if ve.strip_noise(real_sentence) != "发布于顶级期刊：Nature 的这项研究改变了结论。":
    fails.append(f"over-strip: real sentence wrongly noise-stripped -> {ve.strip_noise(real_sentence)!r}")
# and the timestamp forms it must strip
for ts in ["发布于 3 分钟前", "发布于 2026-03-01 12:00", "5 小时前", "更新于 2026年3月1日"]:
    if ve.strip_noise(ts) != "":
        fails.append(f"timestamp not stripped: {ts!r} -> {ve.strip_noise(ts)!r}")
print("over-strip guard: real '发布于…：' kept, timestamps stripped:",
      ve.strip_noise(real_sentence) == real_sentence and ve.strip_noise("发布于 3 分钟前") == "")

# --- version chain assertions (only substantive changes append) ----------------------------
chains, actions = ve.build_chains(SEQ)
chain = chains[CID]
acts = [a["action"] for a in actions]
print("\nactions:", acts)
print("version chain:", [(v["version_no"], v["content_hash"][:14], v["status"]) for v in chain])
expected_acts = ["created_v1", "skipped_no_change", "new_version", "new_version", "new_version", "skipped_no_change"]
if acts != expected_acts:
    fails.append(f"action sequence {acts} != expected {expected_acts}")
if len(chain) != 4:
    fails.append(f"expected 4 versions (v1 body, v2 body, v3 attachment, v4 status), got {len(chain)}")
# footer/nav change (B) did NOT create a version between v1 and v2
if [v["version_no"] for v in chain] != [1, 2, 3, 4]:
    fails.append("version_no not a clean append-only 1..4")
# history preserved: v1 hash differs from v2 (body), v2!=v3 (attachment), v3!=v4 (status)
hashes = [v["content_hash"] for v in chain]
if len(set(hashes)) != 4:
    fails.append("version content_hashes not all distinct across substantive changes")

# --- replay idempotency: 3 replays identical -----------------------------------------------
rep = ve.replay(SEQ, times=3)
print("\nreplay:", rep)
if not rep["identical"] or rep["replays"] != 3:
    fails.append("3x replay not identical")
# stronger idempotency: re-ingesting the CURRENT tip (E) any number of times must not grow the
# chain (a genuine oscillation back to an older render WOULD be a real change, so we replay the
# tip, not an older item).
chains2, _ = ve.build_chains(SEQ + [E, E, E])
if len(chains2[CID]) != 4:
    fails.append(f"re-ingesting the current tip grew the chain to {len(chains2[CID])} (must stay 4)")
print("re-ingest current tip (E x3) -> versions:", len(chains2[CID]), "(idempotent)")

# --- verdict --------------------------------------------------------------------------------
print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
