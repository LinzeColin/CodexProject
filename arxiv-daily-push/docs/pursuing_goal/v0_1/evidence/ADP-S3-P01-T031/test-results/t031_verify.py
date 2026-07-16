#!/usr/bin/env python3
"""ADP-S3-P01-T031 acceptance: minimal Official Connector Interface / SDK.

Acceptance (TASK_INDEX): 无业务 UI、图谱或新平台耦合；一个 mock connector 全链路通过。
Deterministic + CI-safe: the full chain runs on a MockConnector; HttpFetcher (the real GET used by
A0 adapters) is exercised against a LOCAL loopback HTTP server -- no external network in CI. The live
gov.cn fetch (Owner: real fetch at the kernel stage) is a separate evidence smoke, not this test.
"""
import sys, pathlib, hashlib, threading, http.server, dataclasses
V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/arxiv-daily-push/docs/pursuing_goal/v0_1")
sys.path.insert(0, str(V01 / "tools"))
import official_connector as OC  # noqa: E402

FETCHED_AT = "2026-07-17T00:00:00+10:00"
fails = []

# --- reference MockConnector: the full chain must pass with no UI/graph/platform coupling ----
class MockOfficialConnector(OC.OfficialConnector):
    source_id = "mock-a0"
    authority_level = "A0"
    _CANNED = {
        "https://mock.gov.cn/doc/1": (b"<html><h1>\xe5\x9b\xbd\xe5\x8a\xa1\xe9\x99\xa2\xe5\x85\xb3\xe4\xba\x8e\xe6\x94\xbf\xe7\xad\x96</h1>"
                                      b"\xe5\x9b\xbd\xe5\x8f\x91\xe3\x80\x942026\xe3\x80\x951\xe5\x8f\xb7 2026-01-05 \xe7\x8e\xb0\xe8\xa1\x8c\xe6\x9c\x89\xe6\x95\x88"
                                      b"<a href='/att/1.pdf'>\xe9\x99\x84\xe4\xbb\xb6</a></html>"),
        "https://mock.gov.cn/doc/2": (b"<html><h1>\xe6\xb3\x95\xe8\xa7\x84</h1>\xe4\xb8\xad\xe5\x8d\x8e\xe4\xba\xba\xe6\xb0\x91"
                                      b"\xe5\x85\xb1\xe5\x92\x8c\xe5\x9b\xbd 2026-02-10 \xe7\x8e\xb0\xe8\xa1\x8c\xe6\x9c\x89\xe6\x95\x88</html>"),
    }
    def discover(self, cursor):
        return [OC.DiscoverItem("https://mock.gov.cn/doc/1", "国务院政策", "2026-01-05"),
                OC.DiscoverItem("https://mock.gov.cn/doc/2", "法规", "2026-02-10")]
    def fetch(self, url, fetched_at):
        b = self._CANNED[url]
        return OC.FetchResult(url, 200, "text/html", b, hashlib.sha256(b).hexdigest(), fetched_at, True)
    def verify(self, item, fetched):
        official = fetched.url.split("/")[2].endswith(".gov.cn")
        return OC.VerifyResult(official, "A0" if official else "unofficial", official,
                               ("official .gov.cn domain",) if official else ("non-official domain",))
    def normalize(self, item, fetched):
        text = fetched.body.decode("utf-8", "ignore")
        docnum = "国发〔2026〕1号" if "1号" in text else None
        return OC.NormalizedDoc(self.source_id, item.url, item.title, docnum, item.hint_date,
                                "现行有效" if "现行有效" in text else None,
                                "A0", text, canonical_hint="ttl:" + hashlib.sha256(item.title.encode()).hexdigest()[:16])
    def attachments(self, fetched):
        return [OC.Attachment("https://mock.gov.cn/att/1.pdf", "pdf")] if b"1.pdf" in fetched.body else []
    def cursor(self, docs):
        dates = [d.doc_date for d in docs if d.doc_date]
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=max(dates) if dates else None)
    def health(self):
        return OC.HealthResult(True, "mock reachable", "canned fixture")

reg = OC.AdapterRegistry()
reg.register(MockOfficialConnector())
trace = OC.run_chain(reg.get("mock-a0"), OC.Cursor(), FETCHED_AT)

print("registry ids:", reg.ids())
print("chain: health.ok", trace["health"].ok, "| discovered", trace["discovered"],
      "| docs", len(trace["docs"]), "| cursor_after", trace["cursor_after"])
for d in trace["docs"]:
    print(f"  doc {d.doc_id}: A={d.authority_level} num={d.doc_number} date={d.doc_date} status={d.status} atts={len(d.attachments)}")

# full chain assertions
if not trace["health"].ok:
    fails.append("health not ok")
if trace["discovered"] != 2 or len(trace["docs"]) != 2:
    fails.append("discover/normalize did not produce all docs")
if not all(v.is_official and v.authority_level == "A0" for v in trace["verifies"]):
    fails.append("verify did not mark official A0")
if not all(d.authority_level == "A0" and d.title for d in trace["docs"]):
    fails.append("normalize missing authority/title")
if trace["docs"][0].doc_number is None or trace["docs"][0].doc_date is None:
    fails.append("doc_number/doc_date not extracted for doc 1")
if len(trace["docs"][0].attachments) != 1:
    fails.append("attachments not extracted for doc 1")
if trace["cursor_after"].last_date != "2026-02-10":
    fails.append(f"cursor not advanced to latest date, got {trace['cursor_after'].last_date}")
# registry rejects duplicate source_id
try:
    reg.register(MockOfficialConnector()); fails.append("registry accepted duplicate source_id")
except ValueError:
    pass
# no new-platform coupling: SDK imports stdlib only
import official_connector as _oc
src = (V01 / "tools" / "official_connector.py").read_text()
for banned in ("import requests", "import flask", "import django", "networkx", "neo4j", "fastapi"):
    if banned in src:
        fails.append(f"SDK couples to a new platform: {banned}")

# --- HttpFetcher: a REAL GET, verified against a local loopback server (deterministic) -------
PAYLOAD = b"<html>official test payload \xe5\xae\x98\xe6\x96\xb9</html>"
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(PAYLOAD)
    def log_message(self, *a):
        pass
srv = http.server.HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.handle_request, daemon=True).start()
port = srv.server_address[1]
fr = OC.HttpFetcher(timeout=5).get(f"http://127.0.0.1:{port}/doc", FETCHED_AT)
print(f"\nHttpFetcher real GET: status={fr.status} ok={fr.ok} bytes={len(fr.body)} sha={fr.sha256[:12]}")
if not (fr.ok and fr.status == 200 and fr.body == PAYLOAD and fr.sha256 == hashlib.sha256(PAYLOAD).hexdigest()):
    fails.append("HttpFetcher real GET did not return the exact payload / hash")

print("\n" + ("ACCEPTANCE = PASS" if not fails else "ACCEPTANCE = FAIL"))
for f in fails:
    print("  FAIL:", f)
sys.exit(0 if not fails else 1)
