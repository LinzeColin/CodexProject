#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P02-T062 -- version timeline / as-of / old-vs-new comparison API.

The user-facing read layer over the version chain (T026 version_engine: substantive-change
detection + template-noise filter) and the as-of resolver (T056 coverage_asof: parsed-date,
never-future point-in-time query). It lets a user SEE:

  * version_timeline(renders) -- the ordered chain of SUBSTANTIVE versions of one canonical
    document (noise-only re-renders never create a timeline entry), each with the noise-stripped
    body snapshot that was in force at that version;
  * diff_payload(old_render, new_render) -- a LOCATABLE line-level old-vs-new diff: every change
    is classified add / delete / modify with its line position and its exact text, computed over
    the noise-stripped body so TEMPLATE NOISE IS NEVER SHOWN as a change; a noise-only re-render
    yields an empty diff (changed == False);
  * as_of(timeline, query_date) -- the version in force as of a date, by PARSED date, never a
    chronologically future version (delegates to the T056 resolver semantics);
  * replay_version(timeline, version_no) -- reconstruct the exact noise-stripped body of an OLD
    version deterministically; replaying any version any number of times is identical (idempotent).

Deterministic; no network, no clock, no randomness, no production side effects. Reuses
version_engine and coverage_asof rather than re-implementing noise rules or the as-of resolver.
"""
import difflib
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import version_engine as VE      # T026: strip_noise, substantive_signature, content_hash, diff, ingest
import coverage_asof as CA       # T056: _parse_date, as_of_query, _oracle_as_of


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _clean_body(render):
    """The substantive, noise-stripped body of a render -- the SAME text version_engine hashes.
    raw_html (if present) is appended before stripping, exactly as substantive_signature does."""
    body = (render.get("body") or "") + ("\n" + render["raw_html"] if render.get("raw_html") else "")
    return VE.strip_noise(body)


def _lines(text):
    return text.split("\n") if text else []


# ------------------------------------------------------------------ 1. version timeline
def version_timeline(renders):
    """Fold a chronological sequence of renders of ONE canonical document into its substantive
    version timeline. A render that changes only template noise does NOT add a version; its
    stored body is the last substantive body. Each timeline entry carries the noise-stripped body
    snapshot so an old version can be shown/replayed later.

    renders: [{canonical_id, body|raw_html, status?, attachments?, doc_date?, observed_at?}] in
    chronological order. observed_at (a YYYY-MM-DD string) drives as_of; defaults to doc_date."""
    chain, timeline = [], []
    for r in renders:
        prev_hash = chain[-1]["content_hash"] if chain else None
        chain, action = VE.ingest(chain, r)
        if action == "skipped_no_change":
            continue                       # noise-only re-render or exact replay: no timeline entry
        v = chain[-1]
        timeline.append({
            "version_no": v["version_no"],
            "content_hash": v["content_hash"],
            "status": v["status"],
            "doc_date": v.get("doc_date"),
            "observed_at": r.get("observed_at") or r.get("doc_date"),
            "body": _clean_body(r),        # noise-stripped snapshot in force at this version
            "attachment_keys": v["attachment_keys"],
            "prev_content_hash": prev_hash,
        })
    return timeline


# ------------------------------------------------------------------ 2. locatable old-vs-new diff
def diff_payload(old_render, new_render):
    """Locatable line-level diff between two renders, computed over the NOISE-STRIPPED body so
    template chrome never appears as a change. Returns per-change {op, old_line, new_line, text}
    where op in {add, delete, modify}. changed==False for a noise-only (substantive-equal) render."""
    old_body, new_body = _clean_body(old_render), _clean_body(new_render)
    old_lines, new_lines = _lines(old_body), _lines(new_body)
    changes = []
    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            # pair old/new lines positionally; surplus on either side becomes pure delete/add
            span = max(i2 - i1, j2 - j1)
            for k in range(span):
                oi, nj = i1 + k, j1 + k
                if oi < i2 and nj < j2:
                    changes.append({"op": "modify", "old_line": oi + 1, "new_line": nj + 1,
                                    "old_text": old_lines[oi], "new_text": new_lines[nj]})
                elif oi < i2:
                    changes.append({"op": "delete", "old_line": oi + 1, "new_line": None,
                                    "old_text": old_lines[oi], "new_text": None})
                else:
                    changes.append({"op": "add", "old_line": None, "new_line": nj + 1,
                                    "old_text": None, "new_text": new_lines[nj]})
        elif tag == "delete":
            for oi in range(i1, i2):
                changes.append({"op": "delete", "old_line": oi + 1, "new_line": None,
                                "old_text": old_lines[oi], "new_text": None})
        elif tag == "insert":
            for nj in range(j1, j2):
                changes.append({"op": "add", "old_line": None, "new_line": nj + 1,
                                "old_text": None, "new_text": new_lines[nj]})
    # status / attachment changes come from the substantive signature (never from chrome)
    sig_diff = VE.diff(old_render, new_render)
    counts = {"add": sum(c["op"] == "add" for c in changes),
              "delete": sum(c["op"] == "delete" for c in changes),
              "modify": sum(c["op"] == "modify" for c in changes)}
    changed = bool(changes) or sig_diff["status_changed"] or sig_diff["attachments_changed"]
    return {
        "changed": changed,
        "noise_only": not changed,
        "line_changes": changes,
        "counts": counts,
        "status_change": {"from": VE.substantive_signature(old_render)["status"],
                          "to": VE.substantive_signature(new_render)["status"]} if sig_diff["status_changed"] else None,
        "attachments_changed": sig_diff["attachments_changed"],
    }


# ------------------------------------------------------------------ 3. as-of (never future)
def as_of(timeline, query_date):
    """Version in force as of query_date, by PARSED date -- never a future version. Delegates to the
    T056 resolver (which raises on a malformed date and returns None before the first version)."""
    obs = [{"observed_at": v["observed_at"], "version_ref": v["version_no"], "_v": v} for v in timeline]
    hit = CA.as_of_query(obs, query_date)
    return hit["_v"] if hit else None


# ------------------------------------------------------------------ 4. replay an old version
def replay_version(timeline, version_no):
    """Deterministically reconstruct the noise-stripped body + metadata of an OLD version. Pure
    function of the timeline entry, so replaying any version any number of times is identical."""
    for v in timeline:
        if v["version_no"] == version_no:
            return {"version_no": v["version_no"], "body": v["body"], "status": v["status"],
                    "content_hash": v["content_hash"], "body_sha": "sha256:" + _sha(v["body"]),
                    "attachment_keys": v["attachment_keys"]}
    raise KeyError(f"version {version_no} not in timeline")


def replay_is_idempotent(timeline, version_no, times=3):
    reps = [replay_version(timeline, version_no) for _ in range(times)]
    shas = {r["body_sha"] for r in reps}
    return {"version_no": version_no, "times": times, "identical": len(shas) == 1,
            "body_sha": reps[0]["body_sha"]}
