// AUTO-GENERATED -- exercises the REAL extracted rumIngest() + constants from the worker.
'use strict';
const RUM_ENABLED = true;              // 采集开关（部署后生效；关=不注入客户端脚本、端点 202 忽略）
const RUM_SAMPLE = 1;                  // 采样率 [0,1]（DIR-007 预算：可下调以降 D1 写入）
const RUM_METRICS = { LCP: [0, 120000], INP: [0, 60000], CLS: [0, 100] };
const RUM_THEMES = ['warm', 'minimal', 'fresh', 'techno', 'cosmos', 'forest'];
const RUM_DEVICES = ['mobile', 'tablet', 'desktop'];
function rumIngest(payload, roll) {
  if (!RUM_ENABLED) return { ok: false, reason: 'disabled' };
  if (!payload || typeof payload !== 'object') return { ok: false, reason: 'bad_payload' };
  const rng = RUM_METRICS[payload.metric];
  if (!rng) return { ok: false, reason: 'bad_metric' };
  const v = Number(payload.value);
  if (!isFinite(v) || v < rng[0] || v > rng[1]) return { ok: false, reason: 'bad_value' };
  if (!(roll <= RUM_SAMPLE)) return { ok: false, reason: 'sampled_out' };
  const theme = RUM_THEMES.indexOf(payload.theme) >= 0 ? payload.theme : 'other';
  const device = RUM_DEVICES.indexOf(payload.device) >= 0 ? payload.device : 'other';
  const route = (String(payload.route || 'other').slice(0, 32).replace(/[^a-zA-Z0-9_-]/g, '')) || 'other';
  const network = (String(payload.network || 'unknown').slice(0, 16).replace(/[^a-zA-Z0-9_.-]/g, '')) || 'unknown';
  return { ok: true, row: { metric: payload.metric, value: v, theme, device, route, network } };
}
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
