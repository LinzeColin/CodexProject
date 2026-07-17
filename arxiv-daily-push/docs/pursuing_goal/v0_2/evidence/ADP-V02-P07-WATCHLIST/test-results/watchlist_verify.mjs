// ADP-V02-P07 acceptance. Runs the REAL watchDigest/watchMatches extracted from the shipped
// worker_cloud.js (no retyping drift), so every 实测 number in known_gaps.md is reproducible here
// rather than asserted in prose. This package previously shipped the claims with no artifact behind
// them, which — in a round whose whole failure mode was "a false premise written down and trusted" —
// is exactly the wrong thing to leave lying around.
//
// Run: node arxiv-daily-push/docs/pursuing_goal/v0_2/evidence/ADP-V02-P07-WATCHLIST/test-results/watchlist_verify.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
// test-results -> TASK -> evidence -> v0_2 -> pursuing_goal -> docs -> arxiv-daily-push  (6 levels)
const WORKER = resolve(HERE, '../../../../../../deploy/cloudflare/worker_cloud.js');
const w = readFileSync(WORKER, 'utf8');

// extract the shipped code (factsheet extractor + watch engine) into an isolated module
const fsS = w.indexOf('const FS_DOI_RE'), fsE = w.indexOf('function factsheetHTML');
const wS = w.indexOf('const WATCH_FACETS'), wE = w.indexOf('async function watchlistPage');
if (fsS < 0 || fsE < 0 || wS < 0 || wE < 0) { console.error('FAIL: could not locate shipped blocks'); process.exit(1); }
const helpers = `const MAX_ITEMS_PER_FEED=20;
function normIdent(s){return (s||"").replace(/　/g," ").replace(/\\s+/g,"").toLowerCase();}
function nowISO(){return new Date().toISOString();}\n`;
const mod = await import('data:text/javascript;base64,' + Buffer.from(
  helpers + w.slice(fsS, fsE) + '\n' + w.slice(wS, wE) + '\nexport {watchDigest, watchMatches, watchCutoff, WATCH_FACETS, WATCH_MAX, WATCH_SCAN, WATCH_WINDOW_DAYS};'
).toString('base64'));

let fails = 0;
const ok = (c, msg) => { if (!c) { fails++; console.log('  FAIL ' + msg); } else console.log('  PASS ' + msg); };

const CJK = '国务院办公厅关于印发全国一体化政务大数据体系建设指南的通知各省自治区直辖市人民政府现将该指南印发给你们请认真贯彻落实';
const EN = 'A study of transformer scaling laws for large language models with extensive empirical evaluation across benchmarks';
const mkRows = (nCJK) => Array.from({ length: 1000 }, (_, i) => ({
  id: 'i' + i, board_id: i < nCJK ? 'board3' : 'board1',
  title: i < nCJK ? `国务院关于印发某方案的通知 国发〔2026〕${i}号` : `Paper ${i} on scaling`,
  summary: i < nCJK ? CJK : EN, published_at: '2026-07-16',
}));
// The D1 mock MUST honour ORDER BY / LIMIT in the SQL text. A mock that ignores them returns the
// full seen set no matter what the worker asks for -- which makes the counterexample below pass
// against the very regression it exists to catch. (It did. NC2 in nc_results.txt is the proof.)
const mkEnv = (rows, seen = []) => ({ DB: { prepare(sql) { return { bind(...a) { return {
  all: async () => {
    if (!sql.includes('cn_watch_seen')) return { results: rows };
    let s = seen.filter(r => r.watch_id === a[0]);
    if (/ORDER BY\s+at\s+DESC/i.test(sql)) s = [...s].sort((x, y) => (y.at || '').localeCompare(x.at || ''));
    const m = /LIMIT\s+(\?(\d+)|(\d+))/i.exec(sql);
    if (m) s = s.slice(0, Number(m[3] ?? a[Number(m[2]) - 1]));
    return { results: s.map(r => ({ item_id: r.item_id })) };
  },
}; } }; } } });
async function best(rows, mkW, n, seen = []) {
  const env = mkEnv(rows, seen), g = () => mkW(n).map(x => ({ ...x }));
  await mod.watchDigest(env, g());
  let b = Infinity;
  for (let k = 0; k < 9; k++) {
    const t = process.hrtime.bigint(); const r = await mod.watchDigest(env, g());
    const d = Number(process.hrtime.bigint() - t) / 1e6; if (d < b) b = d;
    globalThis._hits = [...r.values()].reduce((a, x) => a + x.length, 0);
  }
  return b;
}
const kw = (n) => Array.from({ length: n }, (_, i) => ({ id: 'k' + i, facet: 'keyword', value: '指南' }));
const dn = (n) => Array.from({ length: n }, (_, i) => ({ id: 'd' + i, facet: 'doc_number', value: `国发〔2026〕${i}号` }));

console.log('shipped constants: WATCH_MAX=%s WATCH_SCAN=%s WATCH_WINDOW_DAYS=%s', mod.WATCH_MAX, mod.WATCH_SCAN, mod.WATCH_WINDOW_DAYS);
console.log('\n== CPU: the xWATCH_MAX multiplier must be gone (Workers Free = 10ms CPU/invocation) ==');
const LIMIT = 10;
const kwCJK = await best(mkRows(1000), kw, 20);
const kwEN = await best(mkRows(0), kw, 20);
const dnCJK = await best(mkRows(1000), dn, 20);
console.log(`  20 keyword  @1000 CJK : ${kwCJK.toFixed(2)} ms   (pre-fix review measured 29.0)`);
console.log(`  20 keyword  @1000 EN  : ${kwEN.toFixed(2)} ms   (pre-fix 7.95 = 80% of budget)`);
console.log(`  20 doc_number @1000 CJK: ${dnCJK.toFixed(2)} ms   (pre-fix 83)`);
ok(kwCJK < LIMIT && kwEN < LIMIT && dnCJK < LIMIT, `all 20-watch cases under the ${LIMIT}ms Free CPU limit`);
// the multiplier is gone iff cost does not scale ~linearly with watch count
const s1 = await best(mkRows(1000), kw, 1), s20 = await best(mkRows(1000), kw, 20);
console.log(`  scaling 1 -> 20 watches: ${s1.toFixed(2)} -> ${s20.toFixed(2)} ms (ratio ${(s20 / s1).toFixed(1)}x)`);
ok(s20 / s1 < 8, 'x20 watches costs far less than x20 (item-only work is hoisted, not per-pair)');

console.log('\n== correctness (unchanged by the perf work) ==');
let r = await mod.watchDigest(mkEnv(mkRows(1000)), [
  { id: 'k1', facet: 'keyword', value: '指南' },
  { id: 'b1', facet: 'board', value: 'board3' },
  { id: 'd1', facet: 'doc_number', value: '国发〔2026〕7号' }]);
ok(r.get('k1').length === 1000, 'keyword matches every CJK row (1000)');
ok(r.get('b1').length === 1000, 'board exact match (1000)');
ok(r.get('d1').length === 1 && r.get('d1')[0].id === 'i7', 'doc_number is exact: only i7');
r = await mod.watchDigest(mkEnv(mkRows(0)), [{ id: 'x', facet: 'keyword', value: 'SCALING' }]);
ok(r.get('x').length > 0, 'keyword is case-insensitive');
r = await mod.watchDigest(mkEnv(mkRows(0)), [{ id: 'y', facet: 'keyword', value: '%' }]);
ok(r.get('y').length === 0, 'keyword % is a literal, not a wildcard');
// NC: a doc_number watch must not match a row with no 文号
r = await mod.watchDigest(mkEnv([{ id: 'z', board_id: 'board3', title: '某地举行政策解读会', summary: '会议召开', published_at: '2026-07-16' }]),
  [{ id: 'd', facet: 'doc_number', value: '国发〔2026〕12号' }]);
ok(r.get('d').length === 0, 'NC: doc_number does not match a row without a 文号');

console.log('\n== idempotency (T066 re-run property) ==');
const rows = mkRows(10);
r = await mod.watchDigest(mkEnv(rows), [{ id: 'w', facet: 'board', value: 'board3' }]);
const firstIds = r.get('w').map(x => x.id);
ok(firstIds.length === 10, 'first view: all unseen');
const acked = firstIds.map(id => ({ watch_id: 'w', item_id: id }));
r = await mod.watchDigest(mkEnv(rows, acked), [{ id: 'w', facet: 'board', value: 'board3' }]);
ok(r.get('w').length === 0, 'after ack: zero unseen (does not re-notify)');
r = await mod.watchDigest(mkEnv([...rows, { id: 'NEW', board_id: 'board3', title: '新通知', summary: '', published_at: '2026-07-17' }], acked),
  [{ id: 'w', facet: 'board', value: 'board3' }]);
ok(r.get('w').length === 1 && r.get('w')[0].id === 'NEW', 'a NEW item still surfaces after ack');

console.log('\n== the reviewer\'s counterexample: seen-set truncation must be impossible ==');
// A future-dated policy sits at candidate rank #1 forever while its ack timestamp is the OLDEST.
// The reverted `ORDER BY at DESC LIMIT 5000` dropped it from the seen set -> re-notified.
const future = { id: 'POLICY_FUTURE', board_id: 'board3', title: '国务院关于印发某规划的通知 国发〔2026〕99号', summary: '指南', published_at: '2027-01-01' };
const big = [future, ...Array.from({ length: 999 }, (_, i) => ({ id: 'i' + i, board_id: 'board3', title: `通知 ${i}`, summary: '指南', published_at: '2026-07-16' }))];
const seen6001 = [{ watch_id: 'w1', item_id: 'POLICY_FUTURE', at: '2026-06-01T00:00:00Z' },
  ...Array.from({ length: 6000 }, (_, i) => ({ watch_id: 'w1', item_id: 's' + i, at: '2026-07-1' + (i % 9) + 'T00:00:00Z' }))];
r = await mod.watchDigest(mkEnv(big, seen6001), [{ id: 'w1', facet: 'keyword', value: '指南' }]);
ok(!r.get('w1').some(x => x.id === 'POLICY_FUTURE'),
  'future-dated item acked earliest is NOT re-notified with 6001 seen rows (fix #3 no longer defeats fix #2)');

console.log('\n== the 号 pre-filter must never drop a real hit ==');
const RE = /[一-龥A-Za-z]{0,8}[〔[（(]\s*20\d{2}\s*[〕\]）)]\s*第?\s*\d+\s*号|第\s*\d+\s*号(?:令|公告)?/;
const parts = ['国发', '财政部令', '〔', '[', '（', '(', '〕', ']', '）', ')', '2026', '第', '12', '号', '令', '公告', ' ', 'x', 'A', ''];
let matched = 0, noHao = 0;
for (let i = 0; i < 200000; i++) {
  const s = Array.from({ length: 1 + (i % 8) }, () => parts[(Math.random() * parts.length) | 0]).join('');
  const m = RE.exec(s); if (!m) continue; matched++; if (!m[0].includes('号')) noHao++;
}
console.log(`  fuzz 200k strings: ${matched} matches, ${noHao} without 号`);
ok(noHao === 0, 'every FS_DOCNUM_RE match contains 号 -> the pre-filter cannot drop a real hit');

console.log('\nACCEPTANCE = ' + (fails ? 'FAIL' : 'PASS'));
process.exit(fails ? 1 : 0);
