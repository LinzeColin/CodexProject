#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P02-T048 -- A0 history QA Gate.

Verifies that the backfilled A0 history is not "just URLs" but real, readable, versioned,
point-in-time-resolvable content. Four gates, all deterministic (no network here -- the live
attachment fetches are cached by discover_attachments.py into attachment_readback.json):

  1. attachment_gate  -- >= TARGET (100) attachments are genuinely READABLE: the cached readback
                         has HTTP 200 + non-trivial bytes + recognized binary magic + a real sha256.
                         A URL that 404s or returns an HTML error page is NOT readable.
  2. revision_gate    -- run REAL official document bodies through the T026 version engine and prove
                         the revision-chain machinery is correct: idempotent re-observation makes no
                         phantom version; template/nav noise makes no version; a genuine body edit,
                         a status flip (现行有效 -> 已废止), or an attachment change each make exactly
                         one new version with a distinct content_hash and a monotonic version_no.
  3. as_of_gate       -- point-in-time resolution checked against an INDEPENDENT oracle over >=100
                         samples (incl. unsorted / 3-5-version / boundary fixtures), comparing PARSED
                         dates not lexical strings; a query never resolves to a chronologically FUTURE
                         version. Non-tautological: a deliberately broken resolver MUST be caught
                         (negative control) and a malformed observed_at MUST be rejected.
  4. gap_gate         -- over the FULL 2016+ window grid, require every ATTEMPTED cell to be explicitly
                         accounted (covered / fetch_failed / no_publications), 0 silently dropped; the
                         real T047 attempted-failures (ndrc-gov, cac-gov) MUST surface as fetch_failed;
                         and a realistic silent-hole mutation MUST be detected. Scope: detecting a
                         truly-published-but-missed month needs a ground-truth index (deferred to T056).

Ends with an aggregate acceptance pack + verdict. The implementer does NOT self-sign the task PASS;
the deterministic gate result is evidence for the independent verifier.
"""
import json, pathlib, sys, hashlib, re

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
sys.path.insert(0, str(HERE))
import version_engine as VE   # T026
import gap_detector as GD     # T043

TARGET_ATTACHMENTS = 100
TARGET_ASOF_SAMPLES = 100
# a genuinely-readable attachment must carry one of these recognized binary magics (not an HTML
# soft-404). Whitelist membership -- not mere truthiness -- so a hand-edited bogus magic can't pass.
WHITELIST_MAGIC = {"zip/ooxml", "pdf", "ole/msoffice", "wmf"}


# ----------------------------------------------------------------------------- corpus
def _source_of(d):
    if d.get("source_id"):
        return d["source_id"]
    u = d.get("url", "")
    if "stats.gov.cn" in u:
        return "stats-gov"
    if "gov.cn" in u:
        return "gov-cn-fagui"   # Wave 1 gov.cn policy/regulation A0 originals
    return "unknown"

def load_corpus():
    docs = []
    for ev in ["ADP-S4-P02-T046/wave1_backfill_docs.json",
               "ADP-S4-P02-T047/wave2_backfill_docs.json"]:
        p = V01 / "evidence" / ev
        if p.exists():
            for d in json.loads(p.read_text(encoding="utf-8")):
                if d.get("month"):
                    d = dict(d); d["source_id"] = _source_of(d)
                    docs.append(d)
    return docs


# ------------------------------------------------------------------ 1. attachment gate
def attachment_gate(readback_path):
    res = {"name": "attachment_gate", "target": TARGET_ATTACHMENTS}
    if not readback_path.exists():
        res.update(passed=False, reason="attachment_readback.json missing", readable_count=0)
        return res
    data = json.loads(readback_path.read_text(encoding="utf-8"))
    atts = data.get("attachments", [])
    # re-derive readability from the cached raw facts (do not trust a stored bool blindly):
    # readable == HTTP 200 + > 64 bytes + a recognized binary magic + a 64-hex sha256.
    def readable(a):
        return bool(a.get("http_status") == 200 and (a.get("bytes") or 0) > 64
                    and a.get("magic") in WHITELIST_MAGIC and isinstance(a.get("sha256"), str)
                    and len(a["sha256"]) == 64 and re.fullmatch(r"[0-9a-f]{64}", a["sha256"]))
    good = [a for a in atts if readable(a)]
    # distinctness: a readable attachment is a real distinct artifact only if its sha256 is unique
    distinct = {a["sha256"] for a in good}
    by_source, by_magic = {}, {}
    for a in good:
        by_source[a["source_id"]] = by_source.get(a["source_id"], 0) + 1
        by_magic[a["magic"]] = by_magic.get(a["magic"], 0) + 1
    res.update(attempted=len(atts), readable_count=len(good), distinct_sha256=len(distinct),
               by_source=by_source, by_magic=by_magic,
               passed=(len(good) >= TARGET_ATTACHMENTS and len(distinct) >= TARGET_ATTACHMENTS))
    res["reason"] = ("ok" if res["passed"]
                     else f"only {len(good)} readable / {len(distinct)} distinct < {TARGET_ATTACHMENTS}")
    return res


# -------------------------------------------------------------------- 2. revision gate
# lines the T026 engine's strip_noise removes (copyright / editorial credit / share CTA)
NAV_NOISE = "版权所有 © 中国政府网\n责任编辑：李四\n分享到 扫一扫 打开APP"

def _obs(cid, body, status="现行有效", doc_date="2020-01-01", atts=None):
    return {"canonical_id": cid, "body": body, "status": status, "doc_date": doc_date,
            "attachments": atts or []}

def revision_gate(corpus):
    res = {"name": "revision_gate", "samples": []}
    ok = True
    # source real official bodies from the corpus (fall back to fixed real-shaped text if body absent)
    bodies = []
    for d in corpus:
        b = d.get("body") or d.get("title") or (d.get("doc_number", "") + " " + d.get("canonical_id", ""))
        bodies.append((d["canonical_id"], b + "\n国务院令第" + str(d.get("doc_number", "")) + "号，现予公布。"))
    if len(bodies) < 2:
        bodies += [("ttl:sampleA", "第一条 为了规范……制定本条例。第二条 本条例自公布之日起施行。"),
                   ("ttl:sampleB", "国家统计局公布：2021年国内生产总值同比增长8.1%。")]

    cidA, bodyA = bodies[0]
    cidB, bodyB = bodies[1] if len(bodies) > 1 else bodies[0]

    # (a) idempotent: same observation x3 -> exactly one version, replay-stable
    seq = [_obs(cidA, bodyA)] * 3
    chains, actions = VE.build_chains(seq)
    acts = [a["action"] for a in actions]
    a_ok = (len(chains[cidA]) == 1 and acts == ["created_v1", "skipped_no_change", "skipped_no_change"]
            and VE.replay(seq, 3)["identical"])
    res["samples"].append({"kind": "idempotent_no_phantom", "versions": len(chains[cidA]),
                           "actions": acts, "correct": a_ok}); ok &= a_ok

    # (b) template/nav noise only -> no new version
    seq = [_obs(cidA, bodyA), _obs(cidA, bodyA + "\n" + NAV_NOISE)]
    chains, actions = VE.build_chains(seq)
    b_ok = (len(chains[cidA]) == 1 and actions[-1]["action"] == "skipped_no_change")
    res["samples"].append({"kind": "noise_only_no_version", "versions": len(chains[cidA]),
                           "last_action": actions[-1]["action"], "correct": b_ok}); ok &= b_ok

    # (c) genuine body republication -> exactly one new version, distinct content_hash, monotonic
    v1 = _obs(cidA, bodyA, doc_date="2020-01-01")
    v2 = _obs(cidA, bodyA + "\n第十条 根据2021年修订决定，增设本条。", doc_date="2021-06-01")
    chains, actions = VE.build_chains([v1, v2])
    c_ok = (len(chains[cidA]) == 2 and actions[-1]["action"] == "new_version"
            and chains[cidA][0]["content_hash"] != chains[cidA][1]["content_hash"]
            and chains[cidA][1]["version_no"] == 2)
    res["samples"].append({"kind": "substantive_body_new_version", "versions": len(chains[cidA]),
                           "distinct_hash": chains[cidA][0]["content_hash"] != chains[cidA][1]["content_hash"],
                           "correct": c_ok}); ok &= c_ok

    # (d) effectivity status flip 现行有效 -> 已废止 -> exactly one new version
    v1 = _obs(cidB, bodyB, status="现行有效", doc_date="2019-01-01")
    v2 = _obs(cidB, bodyB, status="已废止", doc_date="2023-01-01")
    chains, actions = VE.build_chains([v1, v2])
    d_ok = (len(chains[cidB]) == 2 and actions[-1]["action"] == "new_version"
            and chains[cidB][1]["status"] == "已废止")
    res["samples"].append({"kind": "status_flip_new_version", "versions": len(chains[cidB]),
                           "final_status": chains[cidB][-1]["status"], "correct": d_ok}); ok &= d_ok

    # (e) attachment change (different sha256) -> new version
    a1 = {"sha256": "a" * 64}; a2 = {"sha256": "b" * 64}
    v1 = _obs(cidB, bodyB, atts=[a1], doc_date="2020-03-01")
    v2 = _obs(cidB, bodyB, atts=[a2], doc_date="2020-09-01")
    chains, actions = VE.build_chains([v1, v2])
    e_ok = (len(chains[cidB]) == 2 and actions[-1]["action"] == "new_version")
    res["samples"].append({"kind": "attachment_change_new_version", "versions": len(chains[cidB]),
                           "correct": e_ok}); ok &= e_ok

    res["passed"] = ok
    res["reason"] = "ok" if ok else "one or more revision-chain samples incorrect"
    return res


# ----------------------------------------------------------------------- 3. as-of gate
def _parse_date(s):
    """Parse a date to a comparable (y, m, d) tuple. Returns None if NOT a well-formed, zero-padded
    YYYY-MM-DD -- a data-quality guard, since a coarse/dirty date ('2021') would make lexical string
    order disagree with chronological order and silently mis-resolve."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return (y, mo, d)

def resolve_as_of(chain_obs, query_date):
    """CHRONOLOGICALLY-correct point-in-time resolve: the observation with the greatest observed_at
    that is <= query_date, comparing PARSED dates (not lexical strings). Raises on any malformed date
    so dirty data is rejected rather than silently mis-resolved (the tautology the earlier version had)."""
    q = _parse_date(query_date)
    if q is None:
        raise ValueError(f"malformed query date {query_date!r}")
    best, best_key = None, None
    for v in chain_obs:
        pv = _parse_date(v.get("observed_at"))
        if pv is None:
            raise ValueError(f"malformed observed_at {v.get('observed_at')!r}")
        if pv <= q and (best_key is None or pv > best_key):
            best, best_key = v, pv
    return best

def _oracle_as_of(chain_obs, query_date):
    """INDEPENDENT oracle (different algorithm: filter-then-sort-then-last) to check resolve_as_of
    against, so the leak check is not the resolver validating itself."""
    q = _parse_date(query_date)
    elig = sorted((v for v in chain_obs if _parse_date(v["observed_at"]) <= q),
                  key=lambda v: _parse_date(v["observed_at"]))
    return elig[-1] if elig else None

def _broken_last_as_of(chain_obs, query_date):
    """Deliberately WRONG resolver (ignores the date, returns the newest-inserted version). Used as a
    negative control: the leak check MUST catch this one, proving the check can detect a real leak."""
    return chain_obs[-1] if chain_obs else None

def _mk_chain(cid, dated):
    """dated = list of (observed_at, version_no); returns observation dicts (intentionally unsorted)."""
    return [{"version_no": vn, "observed_at": oa,
             "content_hash": "sha256:" + hashlib.sha256((cid + oa + str(vn)).encode()).hexdigest()}
            for oa, vn in dated]

def _count_leaks(resolver, chains, query_dates):
    """A leak = the resolver returns a version whose observed_at is CHRONOLOGICALLY after the query,
    OR disagrees with the independent oracle. Checked with parsed dates, not string comparison."""
    samples, leaks, disagree, detail = 0, 0, 0, []
    for cid, obs in chains.items():
        for qd in query_dates:
            samples += 1
            r = resolver(obs, qd)
            oracle = _oracle_as_of(obs, qd)
            if r is not None and _parse_date(r["observed_at"]) > _parse_date(qd):
                leaks += 1
                detail.append({"cid": cid, "query": qd, "resolved": r["observed_at"]})
            ro = (r or {}).get("content_hash")
            oo = (oracle or {}).get("content_hash")
            if ro != oo:
                disagree += 1
    return samples, leaks, disagree, detail[:5]

def as_of_gate(corpus):
    res = {"name": "as_of_gate", "target_samples": TARGET_ASOF_SAMPLES}
    # real corpus chains: group by canonical_id, observed at the doc's month (well-formed YYYY-MM-DD)
    chains = {}
    for d in corpus:
        cid = d["canonical_id"]
        obs_at = (d.get("month") or "2020-01") + "-01"
        chains.setdefault(cid, []).append(
            {"version_no": len(chains.get(cid, [])) + 1, "observed_at": obs_at,
             "content_hash": "sha256:" + hashlib.sha256((cid + obs_at).encode()).hexdigest()})
    # adversarial fixtures: UNSORTED insertion order + 3-5 versions + boundary dates, so a correct
    # resolver must actually sort chronologically (a naive last-wins/lexical resolver would fail).
    chains["fx:unsorted3"] = _mk_chain("fx:unsorted3", [("2021-06-01", 2), ("2019-01-01", 1), ("2023-12-31", 3)])
    chains["fx:fiveVersions"] = _mk_chain("fx:fiveVersions",
        [("2016-03-15", 1), ("2018-11-30", 2), ("2020-02-29", 3), ("2022-07-01", 4), ("2025-12-01", 5)])
    chains["fx:boundary"] = _mk_chain("fx:boundary", [("2020-01-01", 1), ("2020-12-31", 2)])

    query_dates = [f"{y}-{mm}" for y in range(2016, 2027) for mm in ("01-01", "06-15", "12-31")]

    samples, leaks, disagree, detail = _count_leaks(resolve_as_of, chains, query_dates)

    # NEGATIVE CONTROL 1: the broken resolver MUST be caught (leaks>0), else the leak check is a no-op.
    _, broken_leaks, broken_disagree, _ = _count_leaks(_broken_last_as_of, chains, query_dates)
    control_catches_broken = (broken_leaks > 0 or broken_disagree > 0)

    # NEGATIVE CONTROL 2: a malformed observed_at must be REJECTED (raise), not silently mis-resolved.
    malformed_rejected = False
    try:
        resolve_as_of([{"version_no": 1, "observed_at": "2021"}], "2021-07-01")
    except ValueError:
        malformed_rejected = True

    # explicit ordering spot-check on the boundary chain (before -> None, at v1 -> v1, at v2 -> v2, future -> v2)
    b = chains["fx:boundary"]
    ordering_ok = (resolve_as_of(b, "2019-01-01") is None
                   and resolve_as_of(b, "2020-01-01")["version_no"] == 1
                   and resolve_as_of(b, "2020-12-31")["version_no"] == 2
                   and resolve_as_of(b, "2099-01-01")["version_no"] == 2)

    res.update(chains=len(chains), samples=samples, future_leakage=leaks, oracle_disagreements=disagree,
               ordering_ok=ordering_ok, control_catches_broken=control_catches_broken,
               malformed_rejected=malformed_rejected, violations=detail,
               passed=(leaks == 0 and disagree == 0 and samples >= TARGET_ASOF_SAMPLES
                       and ordering_ok and control_catches_broken and malformed_rejected))
    res["reason"] = ("ok" if res["passed"]
                     else f"leaks={leaks} disagree={disagree} samples={samples} ordering={ordering_ok} "
                          f"control_catches_broken={control_catches_broken} malformed_rejected={malformed_rejected}")
    return res


# ------------------------------------------------------------------------- 4. gap gate
# what a gap gate can and cannot prove without a ground-truth publication index:
#   - CAN: every cell the waves ATTEMPTED is explicitly accounted (covered / fetch_failed /
#     no_publications), never silently dropped; real attempted-failures are SURFACED, not hidden.
#   - CANNOT (needs external ground truth of true publications; deferred to T056 Coverage Debt):
#     detect a month the source truly published but our backfill silently missed. Such a not-yet-
#     attempted in-window month is honestly labeled not_backfilled (tracked future work), NOT covered.
# So "0 unexplained P0 gaps" here means: 0 ATTEMPTED cells are silently unaccounted, and the detector
# provably fires on a realistic silent-hole mutation (not the unreachable ghost-window control).
_ACCOUNTED = {"covered", "fetch_failed", "no_publications"}
# real attempted-but-failed A0 sources from T047 (listing links discovered, full parse deferred)
_T047_FAILED_SOURCES = ["ndrc-gov", "cac-gov"]
_WAVE_MONTH = "2026-07"

def gap_gate(corpus):
    res = {"name": "gap_gate"}
    items = [{"source_id": d["source_id"], "month": d["month"]} for d in corpus]
    sources = GD.infer_source_windows(items)   # {sid: {active_from, active_to}} for sources with docs
    covered = {(d["source_id"], d["month"]) for d in corpus}
    # register the real T047 partial-failure sources with their attempt month and mark them failed,
    # so a genuine attempted failure surfaces as fetch_failed instead of vanishing.
    for s in _T047_FAILED_SOURCES:
        sources.setdefault(s, {"active_from": _WAVE_MONTH, "active_to": _WAVE_MONTH})
    failed = {(s, _WAVE_MONTH) for s in _T047_FAILED_SOURCES}
    backfilled = set(covered)                  # cells that produced docs
    attempted = backfilled | failed            # every cell a wave actually processed

    grid_months = sorted({mo for sid, w in sources.items() for mo in GD.month_range(w["active_from"], w["active_to"])})
    grid = GD.detect(items, sources, grid_months, backfilled=backfilled, failed=failed)

    cov = GD.build_coverage(items)
    def status_of(sid, mo, bf, fl):
        w = sources[sid]
        return GD.classify(sid, mo, cov.get((sid, mo), 0), w["active_from"], w["active_to"], bf, fl)

    # (1) real corpus: every ATTEMPTED cell is explicitly accounted (no silent drop)
    silent_holes = [(s, m) for (s, m) in attempted if status_of(s, m, backfilled, failed) not in _ACCOUNTED]
    # (2) real attempted failures are SURFACED as fetch_failed (reachable positive signal, real data)
    fetch_failed_surfaced = sum(1 for (s, m) in failed if status_of(s, m, backfilled, failed) == "fetch_failed")
    # (3) POSITIVE-DETECTION CONTROL, reachable from a realistic mutation: claim a real in-window month
    #     as attempted WITHOUT recording it backfilled/failed -> the silent-hole detector must fire.
    real_src = next(iter(GD.infer_source_windows(items)))
    rw = GD.infer_source_windows(items)[real_src]
    hole_cell = next(((real_src, mo) for mo in GD.month_range(rw["active_from"], rw["active_to"])
                      if (real_src, mo) not in backfilled and (real_src, mo) not in failed
                      and cov.get((real_src, mo), 0) == 0), None)
    ctrl_attempted = attempted | ({hole_cell} if hole_cell else set())
    ctrl_silent = [(s, m) for (s, m) in ctrl_attempted if status_of(s, m, backfilled, failed) not in _ACCOUNTED]
    control_detects_silent_hole = len(ctrl_silent) > len(silent_holes)

    passed = (len(silent_holes) == 0 and fetch_failed_surfaced == len(failed)
              and control_detects_silent_hole and grid["unexplained"] == 0)
    res.update(cells=grid["cells"], months=len(grid_months), reasons=grid["reason_counts"],
               unexplained_p0=grid["unexplained"], attempted_cells=len(attempted),
               silent_holes=len(silent_holes), silent_hole_sample=silent_holes[:5],
               fetch_failed_surfaced=fetch_failed_surfaced, attempted_failures=len(failed),
               control_detects_silent_hole=control_detects_silent_hole,
               scope_note="detecting truly-published-but-missed months needs a ground-truth index (T056 Coverage Debt)",
               passed=passed)
    res["reason"] = ("ok" if passed
                     else f"silent_holes={len(silent_holes)} fetch_failed_surfaced={fetch_failed_surfaced}/"
                          f"{len(failed)} control_detects={control_detects_silent_hole} unexplained={grid['unexplained']}")
    return res


# ------------------------------------------------------------------------------- driver
def build_pack():
    corpus = load_corpus()
    readback = HERE.parent / "evidence" / "ADP-S4-P02-T048" / "attachment_readback.json"
    g1 = attachment_gate(readback)
    g2 = revision_gate(corpus)
    g3 = as_of_gate(corpus)
    g4 = gap_gate(corpus)
    gates = [g1, g2, g3, g4]
    pack = {
        "task": "ADP-S4-P02-T048",
        "acceptance": "100 attachments readable; revision-chain & as-of samples correct; 0 unexplained P0 gaps",
        "corpus_docs": len(corpus),
        "gates": gates,
        "all_passed": all(g["passed"] for g in gates),
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0,
                 "r2_bytes": 0, "r2_ops": 0, "model_calls": 0,
                 "human_maintenance": "dev-env live attachment readback (0 cloud cost)"},
        "deployment": "NOT_DEPLOYED (QA gate; production worker/cron untouched)",
    }
    return pack

if __name__ == "__main__":
    pack = build_pack()
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    sys.exit(0 if pack["all_passed"] else 1)
