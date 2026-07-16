#!/usr/bin/env python3
"""ADP-S3-P02-T036 acceptance: CAC (网信办) + National Data Administration adapters.

Acceptance (TASK_INDEX): 征求意见、正式文件、解读和新闻可区分；官方原文为 primary。
Deterministic (fixtures; the live cac.gov.cn classification is a separate smoke). Fixtures cover AI /
data-governance consultation, a formal regulation, an interpretation, and news.
"""
import sys, pathlib
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
T036 = V01 / "evidence" / "ADP-S3-P02-T036"
FX = T036 / "fixtures"
sys.path.insert(0, str(V01 / "tools"))
import adapter_cac_nda as A, official_connector as OC  # noqa: E402

fails = []
conn = A.CacNdaConnector("cac-gov", "listing", "https://www.cac.gov.cn/", fetcher=A.FixtureFetcher(FX) if hasattr(A, "FixtureFetcher") else None)

# reuse a simple fixture fetcher
class FF:
    def __init__(self, d): self.d = pathlib.Path(d)
    def get(self, url, fetched_at):
        import hashlib
        b = (self.d / url).read_bytes()
        return OC.FetchResult(url, 200, "text/html", b, hashlib.sha256(b).hexdigest(), fetched_at, True)
conn = A.CacNdaConnector("cac-gov", "listing", "https://www.cac.gov.cn/", fetcher=FF(FX))

CASES = [
    # fixture, expected type, expected is_primary
    ("consultation.html", "consultation", True),
    ("formal.html", "formal", True),
    ("interpretation.html", "interpretation", False),
    ("news.html", "news", False),
]

# --- 1) four types distinguishable; 2) official original is primary ------------------------
for fx, exp_type, exp_primary in CASES:
    html = (FX / fx).read_text(encoding="utf-8")
    import re, html as H
    title = H.unescape(re.search(r"<title>(.*?)</title>", html, re.S).group(1)).strip()
    dt = A.classify_doc_type(title, fx, html)
    ok = dt.doc_type == exp_type and dt.is_primary == exp_primary
    print(f"{'OK ' if ok else 'XX '}{fx}: type={dt.doc_type} primary={dt.is_primary} status={dt.consultation_status} deadline={dt.deadline}")
    if dt.doc_type != exp_type:
        fails.append(f"{fx}: type {dt.doc_type} != {exp_type}")
    if dt.is_primary != exp_primary:
        fails.append(f"{fx}: is_primary {dt.is_primary} != {exp_primary}")

# consultation status + deadline parsed
chtml = (FX / "consultation.html").read_text(encoding="utf-8")
cdt = A.classify_doc_type("关于《...（征求意见稿）》公开征求意见的通知", "consultation.html", chtml)
if cdt.consultation_status != "open":
    fails.append(f"consultation status {cdt.consultation_status} != open")
if cdt.deadline != "2026-08-10":
    fails.append(f"consultation deadline {cdt.deadline} != 2026-08-10")
print("\nconsultation status/deadline:", cdt.consultation_status, cdt.deadline)

# interpretation and news must NOT be primary (they point back to the official original)
if A.classify_doc_type("《条例》解读", "").is_primary:
    fails.append("interpretation wrongly primary")
if A.classify_doc_type("工作会议在京召开", "").is_primary:
    fails.append("news wrongly primary")

# --- 3) registry has both; nda-gov live fetch honestly reported blocked ---------------------
reg = A.build_registry(fetcher=FF(FX))
if reg.ids() != ["cac-gov", "nda-gov"]:
    fails.append(f"registry ids {reg.ids()} != cac + nda")
nda_health = reg.get("nda-gov").health()
print("registry:", reg.ids(), "| nda-gov live health ok:", nda_health.ok, "|", nda_health.note)
if nda_health.ok:
    fails.append("nda-gov health should honestly report blocked (TLS/JS-shell)")

# normalize a fixture end-to-end (doc_type in the normalized doc)
nd = conn.normalize(OC.DiscoverItem("formal.html", "", None), conn.fetch("formal.html", "x"))
if "doc_type=formal" not in nd.body_text:
    fails.append("normalize did not carry doc_type")
print("normalize formal ->", nd.body_text)

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
