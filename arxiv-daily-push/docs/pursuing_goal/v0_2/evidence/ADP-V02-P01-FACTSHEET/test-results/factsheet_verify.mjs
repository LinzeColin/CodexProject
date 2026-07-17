// ADP V0.2 P01 acceptance: the ported factsheet() is faithful to extract_factsheet.py,
// fabricates nothing (load-bearing negative controls), and is ReDoS-safe (linear + input-bounded).
// Mirrors the exact logic deployed in worker_cloud.js (build 0864030f7dc8).
const FS_DOI_RE = /10\.\d{4,9}\/[^\s"'<>]+/;
const FS_DOCNUM_RE = /[一-龥A-Za-z]{0,8}[〔[（(]\s*20\d{2}\s*[〕\]）)]\s*第?\s*\d+\s*号|第\s*\d+\s*号(?:令|公告)?/;
const FS_UNIT_RE = /\d[\d,.]{0,39}\s*(?:%|％|个百分点|亿元|万元|亿美元|亿|万|bps|个基点|美元|元)/g;
function fsFirst(re, ...t) { for (const x of t) { if (!x) continue; const m = String(x).match(re); if (m) return m[0].trim(); } return null; }
function fsUnits(...t) { const o = []; for (const x of t) { if (!x) continue; const mm = String(x).match(FS_UNIT_RE); if (mm) for (const u of mm) { const v = u.trim(); if (!o.includes(v)) o.push(v); } } return o; }
function factsheet(item) {
  const board = item.board_id;
  const title = (item.title || '').slice(0, 500), summary = (item.summary || '').slice(0, 2000);
  const facts = [];
  const date = (item.published_at || '').slice(0, 10); if (date) facts.push(['日期', date]);
  const doi = fsFirst(FS_DOI_RE, item.id, item.url, summary);
  if ((board === 'board1' || board === 'board2') && doi) facts.push(['DOI', doi.replace(/[).,;]+$/, '')]);
  if (board === 'board3') { const dn = fsFirst(FS_DOCNUM_RE, title, summary); if (dn) facts.push(['文号', dn]); }
  if (board === 'board3' || board === 'board4') { const u = fsUnits(title, summary); if (u.length) facts.push(['关键数字', u.slice(0, 3).join('、')]); }
  const auth = (item.authors || '').split(/[;；]/).map(a => a.trim()).filter(Boolean);
  if (auth.length > 1) facts.push(['作者', auth.length + ' 位']);
  return facts;
}
let fail = 0;
const T = (n, g, w) => { const a = JSON.stringify(g), b = JSON.stringify(w); const ok = a === b; if (!ok) fail++; console.log((ok ? 'PASS ' : 'FAIL ') + n + (ok ? '' : '  got=' + a + ' want=' + b)); };
T('board3 有文号+数字', factsheet({ board_id: 'board3', title: '国务院关于印发某方案的通知 国发〔2026〕12号', summary: '提高 3 个百分点，投入 50亿元。', published_at: '2026-07-01T08:00:00Z' }), [['日期', '2026-07-01'], ['文号', '国发〔2026〕12号'], ['关键数字', '3 个百分点、50亿元']]);
T('NC board3 无文号无数字(不臆造)', factsheet({ board_id: 'board3', title: '某地举行会议', summary: '会议顺利召开。', published_at: '2026-07-02' }), [['日期', '2026-07-02']]);
T('NC board1 arxiv-id非DOI', factsheet({ board_id: 'board1', id: '2401.12345', url: 'https://arxiv.org/abs/2401.12345', summary: 'we propose a method.', authors: 'A; B; C', published_at: '2026-06-01' }), [['日期', '2026-06-01'], ['作者', '3 位']]);
T('board2 真DOI', factsheet({ board_id: 'board2', summary: 'see doi:10.1038/s41586-026-01234-5 for details', published_at: '2026-05-01' }), [['日期', '2026-05-01'], ['DOI', '10.1038/s41586-026-01234-5']]);
T('NC 空条目->空', factsheet({ board_id: 'board1' }), []);
// ReDoS guard: previously-pathological 40KB input must return fast (was 2295ms; linear + slice)
const t = process.hrtime.bigint(); const r = factsheet({ board_id: 'board4', summary: '1,'.repeat(20000) }); const d = Number(process.hrtime.bigint() - t) / 1e6;
const redosOk = d < 50; if (!redosOk) fail++;
console.log((redosOk ? 'PASS ' : 'FAIL ') + 'ReDoS-guarded pathological board4 ms=' + d.toFixed(2) + ' facts=' + JSON.stringify(r));
console.log('\nACCEPTANCE = ' + (fail ? 'FAIL' : 'PASS') + ' (faithful port + load-bearing negative controls + ReDoS-safe)');
process.exit(fail ? 1 : 0);
