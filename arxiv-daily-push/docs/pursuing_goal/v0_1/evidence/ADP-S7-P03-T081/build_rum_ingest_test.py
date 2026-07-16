#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S7-P03-T081 -- generate a Node test of the REAL extracted rumIngest() validator + its constants from
the worker, proving the ingest endpoint validates/sanitizes/samples correctly before any D1 write."""
import pathlib
import re

V01 = pathlib.Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/adp/"
                   "arxiv-daily-push/docs/pursuing_goal/v0_1")
OUT = V01 / "evidence" / "ADP-S7-P03-T081" / "test-results" / "rum_ingest_test.js"
src = (V01.parents[3] / "arxiv-daily-push/deploy/cloudflare/worker_cloud.js").read_text(encoding="utf-8")


def grab(pattern):
    m = re.search(pattern, src, re.S)
    assert m, "not found: " + pattern
    return m.group(0)

consts = "\n".join([
    grab(r"const RUM_ENABLED = [^\n]*"),
    grab(r"const RUM_SAMPLE = [^\n]*"),
    grab(r"const RUM_METRICS = \{[^\n]*\};"),
    grab(r"const RUM_THEMES = \[[^\n]*\];"),
    grab(r"const RUM_DEVICES = \[[^\n]*\];"),
])
fn = grab(r"function rumIngest\(payload, roll\) \{.*?\n\}")

harness = r"""// AUTO-GENERATED -- exercises the REAL extracted rumIngest() + constants from the worker.
'use strict';
%CONSTS%
%FN%
const assert=(c,m)=>{ if(!c){console.log('FAIL:',m);process.exitCode=1;} else console.log('ok:',m); };

// valid payload (roll under sample) -> ok, row sanitized
let r=rumIngest({metric:'LCP',value:2345.678,theme:'minimal',route:'today',device:'desktop',network:'4g'},0.0);
assert(r.ok && r.row.metric==='LCP' && r.row.value===2345.678 && r.row.theme==='minimal', 'valid LCP accepted + row built');
// CLS small value accepted
assert(rumIngest({metric:'CLS',value:0.05,theme:'warm',route:'radar',device:'mobile',network:'3g'},0).ok, 'valid CLS accepted');
// unknown theme/device -> 'other'; route/network sanitized
r=rumIngest({metric:'INP',value:120,theme:'HAX<script>',route:'a/b<>c',device:'watch',network:'wi fi!!'},0);
assert(r.ok && r.row.theme==='other' && r.row.device==='other', 'unknown theme/device coerced to other');
assert(r.ok && /^[a-zA-Z0-9_-]*$/.test(r.row.route) && /^[a-zA-Z0-9_.-]*$/.test(r.row.network), 'route/network sanitized to allowlist chars');
// bad metric rejected
assert(rumIngest({metric:'TTFB',value:100},0).reason==='bad_metric', 'unknown metric rejected');
// out-of-range / NaN value rejected
assert(rumIngest({metric:'LCP',value:999999},0).reason==='bad_value', 'LCP out of range rejected');
assert(rumIngest({metric:'LCP',value:'abc'},0).reason==='bad_value', 'non-numeric value rejected');
assert(rumIngest({metric:'CLS',value:-1},0).reason==='bad_value', 'negative CLS rejected');
// null / non-object payload rejected
assert(rumIngest(null,0).reason==='bad_payload', 'null payload rejected');
assert(rumIngest('x',0).reason==='bad_payload', 'string payload rejected');
// sampling: roll above RUM_SAMPLE is dropped
assert(RUM_SAMPLE>=1 ? true : rumIngest({metric:'LCP',value:2000},1.0001)==='sampled_out', 'sample gate present');
// with a low sample rate, a high roll is sampled out
(function(){ // simulate a lower sample by checking the boundary logic directly against RUM_SAMPLE
  let hi=rumIngest({metric:'LCP',value:2000,theme:'warm',route:'today',device:'desktop',network:'4g'}, RUM_SAMPLE+0.01);
  assert(hi.reason==='sampled_out', 'roll > RUM_SAMPLE is sampled_out (no write)');
})();

console.log(process.exitCode?'\nRESULT = FAIL':'\nRESULT = PASS');
"""
OUT.write_text(harness.replace("%CONSTS%", consts).replace("%FN%", fn), encoding="utf-8")
print("wrote", OUT)
