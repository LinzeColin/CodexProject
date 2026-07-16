#!/usr/bin/env python3
"""ADP V0.1 version diff + template-noise filter + idempotent replay (ADP-S2-P02-T026).

Sits on top of the CanonicalDocument identity (T024, canonicalize.py) and the
DocumentVersion append-only schema (T025, document_version.migration.sql). It decides
WHEN a new version_no should be appended to a canonical document's chain:

  - a SUBSTANTIVE change -- the body text, the attachment set, or the status -- appends
    a new version;
  - a NOISE-ONLY change -- footer, navigation, share/social widgets, engagement counts,
    dynamic "posted N minutes ago" timestamps, cookie banners, ad markers -- does NOT
    append a version (the substantive content_hash is unchanged);
  - a REPLAY of already-seen content is idempotent: re-ingesting the same items any number
    of times yields the identical version chain (same version_no assignments and hashes).

Deterministic: no network, no clock, no randomness. The content_hash is computed only over
the substantive signature, so it is stable across cosmetic re-renders of the same document.

Usage:
  python3 version_engine.py --items items.json [--replays 3] [--out report.json]
    items.json: [{ "canonical_id","body","status","attachments":[{"name","sha256"}],
                   "doc_date"?, "raw_html"? }]  (raw_html, if present, is noise-stripped
                   and appended to body before hashing; body may already be clean text)
"""
import argparse, hashlib, json, re, sys, pathlib

# --- template noise rules (line- or inline-level; documented in NOISE_RULES.md) -----------
# Each rule strips presentation chrome that is NOT the substance of the document. Rules are
# conservative: they target unambiguous boilerplate so real content is never removed.
NOISE_LINE_PATTERNS = [
    # NOTE: no \b after a CJK alternative -- CJK chars are all \w, so \b never fires between
    # two CJK chars (e.g. 分享到|微信) and the rule would silently fail to match. Anchor on
    # the leading token + .* instead.
    r"^\s*(?:版权所有|copyright|©|\(c\)).*$",              # copyright / footer
    r"^\s*(?:责任编辑|编辑|校对|审核|来源)\s*[:：].*$",    # editorial footer credits
    r"^\s*(?:京|沪|粤|浙|苏)?ICP备.*$",                    # ICP registration footer
    r"^\s*(?:分享到|扫一扫|打开APP|下载客户端|阅读原文|点击查看|查看更多|展开全文).*$",  # share/CTA
    r"^\s*(?:阅读|浏览量?|点赞|在看|评论|转发)\s*[:：]?\s*\d[\d,\.万]*\s*$",  # engagement counts
    # timestamp-shaped ONLY (leading digit + date/time chars) -- must NOT eat a real sentence that
    # merely begins with 发布于 and contains a colon (e.g. "发布于顶级期刊：Nature ...").
    r"^\s*(?:发布于|更新于|编辑于|发表于)\s*\d[\d年月日时分秒:：/\-\s]*$",  # absolute publish timestamp
    r"^\s*(?:发布于|更新于|编辑于|发表于)?\s*\d+\s*(?:秒|分钟|分|小时|时|天|周|月|年)前\s*$",  # relative "3 分钟前"
    r"^\s*(?:我们使用cookie|本网站使用cookie|接受所有cookie|隐私政策|cookie\s*settings).*$",  # consent banner
    r"^\s*(?:广告|推广|赞助内容|sponsored|advertisement)\s*$",  # ad markers
    r"^\s*(?:首页|导航|栏目|频道|menu|nav)\s*[|｜>》].*$",  # nav crumbs
]
NOISE_INLINE_PATTERNS = [
    r"[?&](?:utm_[a-z]+|spm|from|src|ref|share_token)=[^\s&]+",  # tracking query params
    r"发布于\s*\d+\s*(?:分钟|小时|天)前",                        # inline relative time
]
_LINE_RES = [re.compile(p, re.I) for p in NOISE_LINE_PATTERNS]
_INLINE_RES = [re.compile(p, re.I) for p in NOISE_INLINE_PATTERNS]


def strip_noise(text):
    """Remove template/presentation noise, then normalize whitespace. Deterministic."""
    if not text:
        return ""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if any(r.match(line) for r in _LINE_RES):
            continue
        for r in _INLINE_RES:
            line = r.sub("", line)
        line = re.sub(r"[ \t　]+", " ", line).strip()
        if line:
            out.append(line)
    return "\n".join(out)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def substantive_signature(item):
    """The version-triggering signature: normalized body + sorted attachment hashes + status.
    doc_date is recorded metadata but NOT part of the trigger (a pure date reflow is noise-like;
    a genuine republication also changes body/status). Footer/nav never reach here (stripped)."""
    body = strip_noise((item.get("body") or "") + ("\n" + item["raw_html"] if item.get("raw_html") else ""))
    attachments = sorted((a.get("sha256") or "") for a in (item.get("attachments") or []))
    status = (item.get("status") or "").strip().lower()
    return {"body_hash": _sha(body), "attachments": attachments, "status": status}


def content_hash(item):
    sig = substantive_signature(item)
    return "sha256:" + _sha(json.dumps(sig, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def diff(prev_item, new_item):
    """Explain the change between two renders of the same canonical document."""
    ps, ns = substantive_signature(prev_item), substantive_signature(new_item)
    body_changed = ps["body_hash"] != ns["body_hash"]
    att_changed = ps["attachments"] != ns["attachments"]
    status_changed = ps["status"] != ns["status"]
    substantive = body_changed or att_changed or status_changed
    return {"body_changed": body_changed, "attachments_changed": att_changed,
            "status_changed": status_changed, "substantive": substantive,
            "noise_only": (not substantive)}


def ingest(chain, item):
    """Append a version only on a substantive change. Idempotent on replay.
    `chain` = list of {version_no, content_hash, status, doc_date, attachment_keys}."""
    ch = content_hash(item)
    if not chain:
        v = {"version_no": 1, "content_hash": ch, "status": (item.get("status") or "").strip().lower(),
             "doc_date": item.get("doc_date"),
             "attachment_keys": sorted((a.get("sha256") or "") for a in (item.get("attachments") or []))}
        return chain + [v], "created_v1"
    if chain[-1]["content_hash"] == ch:
        return chain, "skipped_no_change"      # noise-only or exact replay -> no new version
    v = {"version_no": chain[-1]["version_no"] + 1, "content_hash": ch,
         "status": (item.get("status") or "").strip().lower(), "doc_date": item.get("doc_date"),
         "attachment_keys": sorted((a.get("sha256") or "") for a in (item.get("attachments") or []))}
    return chain + [v], "new_version"


def build_chains(items):
    """Run a sequence of items (each with canonical_id) through the version decision."""
    chains, actions = {}, []
    for it in items:
        cid = it["canonical_id"]
        chains[cid], act = ingest(chains.get(cid, []), it)
        actions.append({"canonical_id": cid, "action": act,
                        "version_no": chains[cid][-1]["version_no"], "content_hash": chains[cid][-1]["content_hash"]})
    return chains, actions


def _fingerprint(chains):
    """Order-independent, comparable fingerprint of the whole version state (for replay equality)."""
    return json.dumps({cid: [(v["version_no"], v["content_hash"], v["status"]) for v in ch]
                       for cid, ch in sorted(chains.items())}, ensure_ascii=False, sort_keys=True)


def replay(items, times=3):
    """Ingest the full item sequence `times` times from scratch; all runs must be identical."""
    fps = []
    for _ in range(times):
        chains, _acts = build_chains(items)
        fps.append(_fingerprint(chains))
    return {"replays": times, "identical": len(set(fps)) == 1, "fingerprint_sha": _sha(fps[0])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--replays", type=int, default=3)
    ap.add_argument("--out")
    args = ap.parse_args()
    items = json.loads(pathlib.Path(args.items).read_text(encoding="utf-8"))
    chains, actions = build_chains(items)
    rep = replay(items, args.replays)
    result = {
        "documents": {cid: ch for cid, ch in sorted(chains.items())},
        "actions": actions,
        "replay": rep,
        "summary": {"items_in": len(items), "canonical_documents": len(chains),
                    "versions_total": sum(len(c) for c in chains.values()),
                    "new_versions": sum(1 for a in actions if a["action"] == "new_version"),
                    "skipped_no_change": sum(1 for a in actions if a["action"] == "skipped_no_change"),
                    "replay_deterministic": rep["identical"]},
    }
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0 if rep["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
