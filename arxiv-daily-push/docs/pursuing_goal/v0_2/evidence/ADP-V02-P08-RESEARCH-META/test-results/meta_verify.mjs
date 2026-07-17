// ADP-V02-P08 (T063) acceptance. Runs the REAL metaDoi/enrichMeta/attachMeta/metaFacts extracted from
// the shipped worker_cloud.js (no retyping drift). T063's acceptance is exactly two clauses:
//   1. 预印本/期刊不混淆
//   2. 增强失败不阻塞原始论文
// Both are asserted here against the shipped code, and both have a negative control in nc_results.txt:
// an assertion that cannot fail on broken code is not evidence, it is decoration.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
// test-results -> TASK -> evidence -> v0_2 -> pursuing_goal -> docs -> arxiv-daily-push  (6 levels)
const WORKER = resolve(HERE, '../../../../../../deploy/cloudflare/worker_cloud.js');
const w = readFileSync(WORKER, 'utf8');

const S = w.indexOf('// ───────────────────────── T063 研究元数据（OpenAlex） ');
const E = w.indexOf('function factsheetHTML');
if (S < 0 || E < 0) { console.error('FAIL: could not locate the shipped T063 block'); process.exit(1); }
const helpers = `const OPENALEX_WORKS='https://api.openalex.org/works';
function nowISO(){return '2026-07-17T00:00:00.000Z';}\n`;
const mod = await import('data:text/javascript;base64,' + Buffer.from(
  helpers + w.slice(S, E) +
  '\nexport {metaDoi, metaKey, enrichMeta, attachMeta, metaFacts, META_BATCH, META_SCAN, META_RETRY_DAYS};'
).toString('base64'));

let fails = 0;
const ok = (c, msg) => { if (!c) { fails++; console.log('  FAIL ' + msg); } else console.log('  PASS ' + msg); };
// 「压根没发请求」必须表现为断言失败，而不是 new URL(null) 抛 TypeError 把整轮打断 ——
// 一崩，后面的断言就再也没机会报告了（nc5 就是这样：11 条真失败，却连最终判定都跑不到）。
// 判定要靠断言，不能靠崩溃。
const qp = (u, k) => { try { return decodeURIComponent(new URL(u).searchParams.get(k) || ''); } catch { return ''; } };

console.log('shipped constants: META_BATCH=%s META_SCAN=%s META_RETRY_DAYS=%s', mod.META_BATCH, mod.META_SCAN, mod.META_RETRY_DAYS);

console.log('\n== metadata adapters: REAL live id/url forms (taken from the production D1) ==');
// every expectation below was confirmed against the live OpenAlex API before being written here
const CASES = [
  [{ id: 'arxiv:1904.06520', url: 'https://arxiv.org/abs/1904.06520' }, '10.48550/arxiv.1904.06520'],
  [{ id: 'biorxiv:10.64898/2026.03.04.709430', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' }, '10.64898/2026.03.04.709430'],
  [{ id: 'feed:3f18', url: 'https://www.medrxiv.org/content/10.64898/2026.07.12.26357871v1?rss=1' }, '10.64898/2026.07.12.26357871'],
  [{ id: 'feed:db54', url: 'https://www.nature.com/articles/d41586-026-02188-y' }, '10.1038/d41586-026-02188-y'],
  [{ id: 'feed:2d37', url: 'https://www.nature.com/articles/s41467-026-74639-z' }, '10.1038/s41467-026-74639-z'],
  [{ id: 'feed:6da8', url: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2512275?af=R&rss=currentIssue' }, '10.1056/NEJMoa2512275'],
  [{ id: 'feed:6306', url: 'https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3003884' }, '10.1371/journal.pbio.3003884'],
  [{ id: 'feed:d801', url: 'https://www.pnas.org/doi/abs/10.1073/iti2726123?af=R' }, '10.1073/iti2726123'],
  [{ id: 'feed:8f0e', url: 'https://elifesciences.org/articles/109351' }, '10.7554/elife.109351'],
];
let adapters = 0;
for (const [it, want] of CASES) { const got = mod.metaDoi(it); if (got === want) adapters++; else console.log(`    got ${got} want ${want}`); }
ok(adapters === CASES.length, `all ${CASES.length} live source forms resolve to the right DOI`);
// NC: things with no DOI must return null -- an adapter that GUESSES is worse than one that abstains
const NO_DOI = [
  { id: 'feed:6a25', url: 'https://www.science.org/content/article/bungee-jumping-mice-may-reveal' },
  { id: 'a0:abc', url: 'https://www.ndrc.gov.cn/xxgk/zcfb/tz/202607/t20260716_1406539.html' },
  { id: 'feed:xyz', url: 'https://spectrum.ieee.org/some-story' },
  { id: '', url: '' }, { id: 'feed:q', url: 'https://example.com/10.1234' },
  // 复核 F6：PLOS 附件链接里的「DOI」是资源名，不是作品 DOI。原实现会返回
  // 10.1371/journal.pbio.3003906.PDF —— 那是猜。抽不准必须弃权。
  { id: 'feed:pdf', url: 'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3003906.PDF&type=printable' },
  { id: 'feed:xml', url: 'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3003884.XML&type=manuscript' },
];
ok(NO_DOI.every(x => mod.metaDoi(x) === null), 'NC: sources with no DOI resolve to null (abstains, does not guess)');

console.log('\n== metaKey: OpenAlex lowercases the DOI it returns -- the map key must survive that ==');
ok(mod.metaKey('https://doi.org/10.1056/nejmoa2512275') === mod.metaKey('10.1056/NEJMoa2512275'),
  'request-side NEJMoa2512275 and response-side nejmoa2512275 collapse to the same key');
ok(mod.metaKey('https://dx.doi.org/10.1038/X') === '10.1038/x', 'strips the doi.org prefix and lowercases');

// ── a REAL D1: node:sqlite running the REAL schema ───────────────────────────────────
// ★这是复核 BLOCK 的 F1★：原来的假 env 的 all() 无视 WHERE/ORDER BY/LIMIT，直接把 rows 原样吐回，
// 于是整条 SELECT 从来没被测过 —— 复核把 board_id 改成 'nope'、LIMIT 改成 999999、删掉 ORDER BY，
// 我的套件照样 PASS。这与 P07 的 NC2 是同一个病根（mock 无视它自称在测的 SQL），只隔了一轮。
// 现在用真 SQLite + 真 schema 跑真 SQL，那三种改法都必然变红（见 nc_results.txt）。
import { DatabaseSync } from 'node:sqlite';
const SCHEMA = readFileSync(resolve(HERE, '../../../../../../deploy/cloudflare/schema_cloud.sql'), 'utf8');
function mkDB(items = []) {
  const db = new DatabaseSync(':memory:');
  // 真 schema 的 cn_items 段 + 其索引（含 idx_cn_items_board_recency —— F2 就是靠它）。
  // 先去掉 -- 行注释再按 ; 切：schema 里每条 CREATE 前面都有一行中文注释，不剥掉就永远匹配不上
  // （第一版就栽在这，症状是 'no such table: cn_items'）。
  const clean = SCHEMA.split('\n').filter(l => !/^\s*--/.test(l)).join('\n');
  let made = 0;
  for (const stmt of clean.split(';')) {
    const t = stmt.trim();
    if (/^CREATE (TABLE|INDEX)/i.test(t) && /cn_items/.test(t)) { db.exec(t + ';'); made++; }
  }
  if (made < 2) { console.error('FAIL: real schema did not load (got ' + made + ' stmts) -- the fixture would be fake'); process.exit(1); }
  const ins = db.prepare('INSERT OR REPLACE INTO cn_items (id,board_id,source_id,kind,title,url,summary,published_at,fetched_at,first_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?)');
  for (const it of items) ins.run(it.id, it.board_id || 'board1', it.source_id || 's', 'paper',
    it.title || 't', it.url || '', it.summary || '', it.published_at ?? null, it.fetched_at || '2026-07-17T00:00:00Z', '2026-07-01T00:00:00Z');
  // ★ANALYZE 是这条 fixture 的关键，不是装饰★
  // 没有统计信息时，SQLite 只能走有序索引 idx_cn_items_board_recency，于是「删掉 ORDER BY 也照样有序」——
  // 我据此写下「ORDER BY 无法被覆盖」，那是**假前提**：那是 fixture 没统计信息的产物，不是查询的性质。
  // 一旦有统计信息，计划就降级成 SCAN cn_items（SCAN 与 idx_cn_items_board 都合法，planner 没有保序义务），
  // 「先补最新」当场垮成 8/50 → ORDER BY 是**承重**的。复核用这一行证伪了我的「无法覆盖」。
  db.exec('ANALYZE');
  return db;
}
// 一个尽量贴近 D1 的适配器：prepare/bind/all/run/batch，参数用 ?1 风格（node:sqlite 支持，已验证）
function mkEnv(items = []) {
  const db = mkDB(items), sql = [], written = [];
  const wrap = (q) => ({
    bind(...a) {
      const st = { _q: q, _a: a,
        all: async () => { sql.push(q); return { results: db.prepare(q).all(...a) }; },
        run: async () => { sql.push(q); db.prepare(q).run(...a); return {}; } };
      return st;
    },
    run: async () => { sql.push(q); db.exec(q); return {}; },
    _q: q, _a: [],
  });
  const selRows = [];
  return { _db: db, _sql: sql, _written: written, _selRows: selRows, DB: {
    prepare: (q) => wrap(q),
    batch: async (stmts) => stmts.map(s => {
      sql.push(s._q);
      if (/^\s*SELECT/i.test(s._q)) {
        const rs = db.prepare(s._q).all(...(s._a || []));
        // 记录候选查询真正读回了多少行 —— META_SCAN 是否承重，只能这样观测
        if (s._q.startsWith('SELECT id, url FROM cn_items')) selRows.push(rs.length);
        return { results: rs };
      }
      db.prepare(s._q).run(...(s._a || []));
      written.push({ q: s._q, a: s._a });
      return {};
    }),
  } };
}
// 读回真正落库的元数据行（不再靠窥探 bind 参数猜）
const metaRows = (env) => env._db.prepare('SELECT * FROM cn_item_meta ORDER BY item_id').all();
// 真 OpenAlex 【总是】回 meta.count（已对线上实测确认），mock 就必须也回 —— 否则 mock 比真 API 更
// 宽松，会把「未知截断状态」这条路径测成一个真实里不存在的场景。mock 不忠实 = 测的是 mock。
const OA = (results) => async () => ({ ok: true, json: async () => ({ results, meta: { count: results.length } }) });
const work = (doi, type, srcName, srcType, cited = 0, oa = 'closed') => ({
  id: 'https://openalex.org/W1', doi: 'https://doi.org/' + doi.toLowerCase(), type,
  primary_location: { source: { display_name: srcName, type: srcType } },
  cited_by_count: cited, open_access: { oa_status: oa }, publication_year: 2026, authorships: [{}, {}],
});

console.log('\n== ACCEPTANCE 1: 预印本/期刊不混淆 ==');
{
  const rows = [
    { id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' },
    { id: 'p2', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' },
    { id: 'j1', board_id: 'board2', url: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2512275' },
    { id: 'j2', board_id: 'board2', url: 'https://www.nature.com/articles/s41467-026-74639-z' },
  ];
  globalThis.fetch = OA([
    work('10.48550/arxiv.1904.06520', 'preprint', 'arXiv (Cornell University)', 'repository'),
    work('10.64898/2026.03.04.709430', 'preprint', 'bioRxiv (Cold Spring Harbor Laboratory)', 'repository'),
    work('10.1056/NEJMoa2512275', 'article', 'New England Journal of Medicine', 'journal', 2, 'green'),
    work('10.1038/s41467-026-74639-z', 'article', 'Nature Communications', 'journal', 0, 'gold'),
  ]);
  const env = mkEnv(rows), counts = { degraded: [] };
  await mod.enrichMeta(env, counts);
  const pre = new Map(metaRows(env).map(r => [r.item_id, r.is_preprint]));   // 从真库读回，不是窥探 bind 参数
  ok(pre.get('p1') === 1 && pre.get('p2') === 1, 'arXiv + bioRxiv are recorded as 预印本 (is_preprint=1)');
  ok(pre.get('j1') === 0 && pre.get('j2') === 0, 'NEJM + Nature Communications are NOT recorded as 预印本 (is_preprint=0)');
  const venue = new Map(metaRows(env).map(r => [r.item_id, r.venue]));
  ok(venue.get('j1') === 'New England Journal of Medicine' && venue.get('p1') === 'arXiv (Cornell University)',
    'the venue recorded is the one OpenAlex reports, verbatim');
  // the label a reader actually sees
  const preFacts = mod.metaFacts({ is_preprint: 1, venue: 'arXiv (Cornell University)', cited_by: 4, oa_status: 'green' });
  const jFacts = mod.metaFacts({ is_preprint: 0, venue: 'New England Journal of Medicine', cited_by: 2, oa_status: 'green' });
  ok(preFacts[0][0] === '预印本' && jFacts[0][0] === '发表于', 'the rendered label separates 预印本 from 发表于');
  ok(!JSON.stringify(preFacts.concat(jFacts)).includes('研究论文'),
    'NC: never claims 研究论文 -- OpenAlex reports Nature news as type=article too, so that label would be false');
  // a repository-hosted work whose type is NOT preprint is still a repository -> 预印本 side
  globalThis.fetch = OA([work('10.48550/arxiv.1904.06520', 'article', 'arXiv (Cornell University)', 'repository')]);
  const e2 = mkEnv([{ id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  await mod.enrichMeta(e2, { degraded: [] });
  // 复核提的健壮性 nit：条目一条都没补上时 metaRows(e2)[0] 是 undefined → TypeError 会让整轮中断，
  // 后面的断言就再也没机会报告了（nc5 就是这样）。判定要靠断言，不能靠崩溃。
  ok((metaRows(e2)[0] || {}).is_preprint === 1, 'source.type=repository alone is enough to call it 预印本 (not conflated with a journal)');
}

console.log('\n== ACCEPTANCE 2: 增强失败不阻塞原始论文 ==');
{
  const rows = [{ id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }];
  // (a) the network throws
  globalThis.fetch = async () => { throw new TypeError('network down'); };
  let counts = { degraded: [] }, threw = false;
  try { await mod.enrichMeta(mkEnv(rows), counts); } catch { threw = true; }
  ok(!threw && counts.degraded.some(d => d.startsWith('meta:')), 'fetch throwing -> enrichMeta degrades, never throws (cron survives)');
  // (b) OpenAlex returns 500
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({}) });
  counts = { degraded: [] }; threw = false;
  try { await mod.enrichMeta(mkEnv(rows), counts); } catch { threw = true; }
  ok(!threw && counts.degraded.includes('meta:http500'), 'HTTP 500 -> recorded as degraded, never throws');
  // (c) malformed JSON body
  globalThis.fetch = async () => ({ ok: true, json: async () => { throw new SyntaxError('bad json'); } });
  counts = { degraded: [] }; threw = false;
  try { await mod.enrichMeta(mkEnv(rows), counts); } catch { threw = true; }
  ok(!threw && counts.degraded.some(d => d.startsWith('meta:')), 'malformed JSON -> degrades, never throws');
  // (d) the DB itself is broken while ATTACHING -> the page must still render
  const badEnv = { DB: { prepare() { throw new Error('D1 down'); } } };
  const items = [{ id: 'p1', title: 'a real paper' }];
  let out, threw2 = false;
  try { out = await mod.attachMeta(badEnv, items); } catch { threw2 = true; }
  ok(!threw2 && out[0].title === 'a real paper' && !out[0]._meta,
    'attachMeta with a dead D1 -> returns the papers unchanged, no _meta, no throw (原文不被阻塞)');
}

console.log('\n== dedup rules: two items, one DOI ==');
{
  // the same paper arriving through two different feeds must cost ONE lookup and enrich BOTH items
  const rows = [
    { id: 'dupA', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' },
    { id: 'dupB', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430v2' },
  ];
  let calls = 0, asked = null;
  globalThis.fetch = async (u) => { calls++; asked = u; const r = [work('10.64898/2026.03.04.709430', 'preprint', 'bioRxiv', 'repository')]; return { ok: true, json: async () => ({ results: r, meta: { count: r.length } }) }; };
  const env = mkEnv(rows);
  await mod.enrichMeta(env, { degraded: [] });
  // asked 可能是 null（例如候选查询一条都没选中时根本不会发请求）—— 那时直接判失败，
  // 而不是让 new URL(null) 抛 TypeError 把整轮打断、后面的断言再也没机会报告。
  const filter = qp(asked, 'filter');
  ok(!!asked, 'a request was actually issued (otherwise nothing below is meaningful)');
  ok((filter.match(/10\.64898/g) || []).length === 1, 'the duplicated DOI is requested ONCE, not twice');
  const ids = metaRows(env).filter(r => r.found === 1).map(r => r.item_id);
  ok(ids.includes('dupA') && ids.includes('dupB'), 'the single result is broadcast back to BOTH items');
  ok(calls === 1, 'DIR-007: exactly ONE external subrequest for the whole batch');
}

console.log('\n== DIR-007: one batch, one subrequest, bounded ==');
{
  const rows = Array.from({ length: 300 }, (_, i) => ({ id: 'x' + i, board_id: i % 2 ? 'board1' : 'board2', url: `https://arxiv.org/abs/24${String(i).padStart(2, '0')}.1234${i % 10}` }));
  let calls = 0, asked = null;
  globalThis.fetch = async (u) => { calls++; asked = u; return { ok: true, json: async () => ({ results: [], meta: { count: 0 } }) }; };
  await mod.enrichMeta(mkEnv(rows), { degraded: [] });
  const filter = qp(asked, 'filter');
  const n = filter.replace('doi:', '').split('|').length;
  console.log(`  300 candidate rows -> ${calls} subrequest asking for ${n} DOIs`);
  ok(calls === 1, 'exactly 1 external subrequest per cron run (cron 20/50 -> 21/50)');
  ok(n > 1 && n <= mod.META_BATCH, `the batch is non-empty and never exceeds META_BATCH (${mod.META_BATCH})`);
}

console.log('\n== not-found bookkeeping: do not re-ask the same misses every night ==');
{
  globalThis.fetch = OA([]);   // OpenAlex knows nothing about it
  const env = mkEnv([{ id: 'ghost', board_id: 'board1', url: 'https://arxiv.org/abs/2999.99999' }]);
  await mod.enrichMeta(env, { degraded: [] });
  const row = metaRows(env).find(r => r.item_id === 'ghost');
  ok(row && row.found === 0, 'a miss is recorded (found=0) so it is not re-requested every run');
  // ★行为测试，不是拿正则去 grep SQL★（复核 F1：grep 冒充行为测试）。真跑一次：miss 之后再跑，
  // 该条目不应再被请求；把 enriched_at 推到 META_RETRY_DAYS 之前，它必须重新被请求。
  let asked2 = null;
  globalThis.fetch = async (u) => { asked2 = u; return { ok: true, json: async () => ({ results: [], meta: { count: 0 } }) }; };
  asked2 = null; await mod.enrichMeta(env, { degraded: [] });
  ok(asked2 === null, 'a fresh miss is NOT re-requested on the next run');
  env._db.prepare("UPDATE cn_item_meta SET enriched_at = '2026-01-01T00:00:00Z' WHERE item_id='ghost'").run();
  asked2 = null; await mod.enrichMeta(env, { degraded: [] });
  ok(asked2 !== null && decodeURIComponent(asked2).includes('2999.99999'), 'but it IS retried once enriched_at ages past META_RETRY_DAYS');
}

console.log('\n== F2: the LIMIT does NOT bound the scan -- the plan must use the recency index, no temp sort ==');
{
  // 复核实测：board_id IN ('board1','board2') 会放弃 idx_cn_items_board_recency 并 USE TEMP B-TREE
  // FOR ORDER BY —— 即先把整个板块排完序再 LIMIT。LIMIT 限的是返回行数，不是扫描量。
  // 先让【发货代码自己】把 cn_item_meta 建出来（用它自己的 DDL，不是我另写一份 —— 否则测的是我的表）
  const planEnv = mkEnv([]);
  globalThis.fetch = OA([]);
  await mod.enrichMeta(planEnv, { degraded: [] });
  const db = planEnv._db;
  const plan = (sql) => db.prepare('EXPLAIN QUERY PLAN ' + sql).all().map(r => r.detail).join(' | ');
  const inPlan = plan(`SELECT id, url FROM cn_items WHERE board_id IN ('board1','board2')
      AND NOT EXISTS (SELECT 1 FROM cn_item_meta m WHERE m.item_id = cn_items.id AND (m.found = 1 OR m.enriched_at >= '2026-01-01'))
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 200`);
  const eqPlan = plan(`SELECT id, url FROM cn_items WHERE board_id = 'board1'
      AND NOT EXISTS (SELECT 1 FROM cn_item_meta m WHERE m.item_id = cn_items.id AND (m.found = 1 OR m.enriched_at >= '2026-01-01'))
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 200`);
  console.log('  IN(2 boards): ' + inPlan.slice(0, 96));
  console.log('  = 1 board   : ' + eqPlan.slice(0, 96));
  ok(/TEMP B-TREE/i.test(inPlan), 'reproduces the defect: IN (2 boards) forces USE TEMP B-TREE FOR ORDER BY');
  ok(!/TEMP B-TREE/i.test(eqPlan), 'the shipped per-board query needs NO temp sort');
  ok(/idx_cn_items_board_recency/.test(eqPlan), 'the shipped per-board query uses idx_cn_items_board_recency');
  // and the shipped code really does issue per-board equality queries, not an IN
  const env = mkEnv([{ id: 'a', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  globalThis.fetch = OA([]);
  await mod.enrichMeta(env, { degraded: [] });
  const sel = env._sql.filter(q => q.startsWith('SELECT id, url FROM cn_items'));
  ok(sel.length === 2 && sel.every(q => /board_id = \?1/.test(q)) && !sel.some(q => /board_id IN/.test(q)),
    'the shipped code issues one equality query per board (board1, board2), never board_id IN (...)');
}

console.log('\n== F3: OpenAlex returns MULTIPLE works per DOI -> the winner must be deterministic ==');
{
  // 复核用真实 API 实测 arxiv:1506.01497 回 2 条，cited_by = [18240, 6274]；D1 batch 按序 = 最后一条赢
  // → 页面会把 6274 当事实，而规范记录是 18240。规则：取 cited_by 最大者，并列取 id 字典序最小者。
  const dup = (cited, id) => ({ id, doi: 'https://doi.org/10.48550/arxiv.1506.01497', type: 'preprint',
    primary_location: { source: { display_name: 'arXiv (Cornell University)', type: 'repository' } },
    cited_by_count: cited, open_access: { oa_status: 'green' }, publication_year: 2015 });
  for (const order of [[dup(18240, 'https://openalex.org/W2'), dup(6274, 'https://openalex.org/W1')],
                       [dup(6274, 'https://openalex.org/W1'), dup(18240, 'https://openalex.org/W2')]]) {
    globalThis.fetch = async () => ({ ok: true, json: async () => ({ results: order, meta: { count: order.length } }) });
    const env = mkEnv([{ id: 'w', board_id: 'board1', url: 'https://arxiv.org/abs/1506.01497' }]);
    await mod.enrichMeta(env, { degraded: [] });
    const rows = metaRows(env);
    ok(rows.length === 1 && (rows[0] || {}).cited_by === 18240,
      `duplicate works -> canonical 18240 wins regardless of response order (got ${rows[0] && rows[0].cited_by})`);
  }
  // tie on citations -> lowest OpenAlex id wins (deterministic, not "whichever arrived last")
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ results: [dup(5, 'https://openalex.org/W9'), dup(5, 'https://openalex.org/W3')], meta: { count: 2 } }) });
  const env = mkEnv([{ id: 'w', board_id: 'board1', url: 'https://arxiv.org/abs/1506.01497' }]);
  await mod.enrichMeta(env, { degraded: [] });
  ok((metaRows(env)[0] || {}).oa_id === 'https://openalex.org/W3', 'ties break on the lowest OpenAlex id (deterministic)');
}

console.log('\n== F4: a truncated response must NOT be recorded as "OpenAlex does not know this paper" ==');
{
  // 50 个 DOI 可能回 58 条 work；per-page 太小就会把真论文截掉，然后我们把自己的截断写成 found=0
  // （复核实测被截掉的是 FedAvg，5641 次引用）。而候选窗口是「最近 200 条」，一旦误判就几乎永不重试。
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ results: [], meta: { count: 58 } }) });
  const env = mkEnv([{ id: 'real', board_id: 'board1', url: 'https://arxiv.org/abs/1602.05629' }]);
  const counts = { degraded: [] };
  await mod.enrichMeta(env, counts);
  ok(metaRows(env).length === 0, 'response truncated -> writes NO found=0 row (does not blame OpenAlex for our truncation)');
  ok(counts.degraded.includes('meta:truncated'), 'the truncation is reported as a degradation instead');
  // 复核指出的残余风险：万一 OpenAlex 哪天不回 meta，就无从判断是否被截断 —— 未知必须向安全侧倒。
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ results: [] }) });   // 没有 meta
  const envU = mkEnv([{ id: 'unk', board_id: 'board1', url: 'https://arxiv.org/abs/1602.05629' }]);
  const cU = { degraded: [] };
  await mod.enrichMeta(envU, cU);
  ok(metaRows(envU).length === 0 && cU.degraded.includes('meta:truncated'),
    'meta.count missing entirely -> treated as truncated (unknown fails SAFE, no false found=0)');
  // and the request must ask for more rows than the batch can possibly need
  let asked = null;
  globalThis.fetch = async (u) => { asked = u; return { ok: true, json: async () => ({ results: [], meta: { count: 0 } }) }; };
  await mod.enrichMeta(mkEnv([{ id: 'x', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]), { degraded: [] });
  const per = Number(qp(asked, 'per-page'));
  ok(per > mod.META_BATCH, `per-page (${per}) exceeds META_BATCH (${mod.META_BATCH}) so duplicates cannot truncate the page`);
}

console.log('\n== F7: metadata rows for pruned items must not accumulate forever ==');
{
  globalThis.fetch = OA([]);
  const env = mkEnv([{ id: 'live', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  await mod.enrichMeta(env, { degraded: [] });   // 先跑一次让发货代码建表
  env._db.prepare("INSERT INTO cn_item_meta (item_id,doi,found,enriched_at) VALUES ('gone','10.1/x',1,'2026-07-01T00:00:00Z')").run();
  await mod.enrichMeta(env, { degraded: [] });
  ok(!metaRows(env).some(r => r.item_id === 'gone'), 'an orphan meta row (its cn_item was pruned) is deleted');
}

console.log('\n== the ORDER BY must actually be load-bearing: newest papers get enriched FIRST ==');
{
  // 自查：删掉 ORDER BY 时上面所有断言仍然全绿（nc7）。一个删掉也不会红的子句，就是没被测。
  // 语义是「先补最新的」：候选远多于一批时，被选中的必须是最新的那 50 条，而不是任意 50 条。
  const items = Array.from({ length: 300 }, (_, i) => ({
    id: 'n' + String(i).padStart(3, '0'), board_id: 'board1',
    // i 越大越新；DOI 唯一，便于回读到底问了哪些
    published_at: '2026-' + String(1 + (i % 12)).padStart(2, '0') + '-' + String(1 + (i % 28)).padStart(2, '0'),
    url: 'https://arxiv.org/abs/' + String(2000 + i) + '.10001',
  }));
  // 用真实的 recency 排序算出「应该被问到的最新 50 条」
  const db0 = mkDB(items);
  const want = db0.prepare(`SELECT id FROM cn_items WHERE board_id='board1'
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 50`).all().map(r => r.id);
  let asked = null;
  globalThis.fetch = async (u) => { asked = u; return { ok: true, json: async () => ({ results: [], meta: { count: 0 } }) }; };
  await mod.enrichMeta(mkEnv(items), { degraded: [] });
  const filter = qp(asked, 'filter').replace('doi:', '');
  const askedIds = filter.split('|').map(d => { const m = /arxiv\.(\d+)/.exec(d); return m ? 'n' + String(Number(m[1]) - 2000).padStart(3, '0') : null; }).filter(Boolean);
  const overlap = askedIds.filter(id => want.includes(id)).length;
  console.log(`  asked for ${askedIds.length} DOIs; ${overlap} of them are among the 50 most recent`);
  // 一条没问到时 overlap===askedIds.length 会退化成 0===0 → 印出 PASS 却什么都没断言。
  // 本文件开篇就写着「不会失败的断言不是证据，是装饰」—— 那就先钉死批量非空。
  ok(askedIds.length === 50, 'a full batch of 50 was actually requested (guards the check below from passing on an empty batch)');
  ok(overlap === askedIds.length, 'the batch is exactly the most-recent items (ORDER BY is doing real work -- nc7 proves it)');
}

console.log('\n== META_SCAN must actually bound the READ (nc6 was mislabelled 承重 in round 2) ==');
{
  // 自查+复核：我原来的 nc6 把 `LIMIT ?3` 改成 `LIMIT 999999`，留下一个没用上的绑定参数 →
  // 测试是因为**绑定参数个数不匹配**而红的，不是因为 LIMIT 语义。我看到 exit=1 就写了「承重」。
  // 那是**假的覆盖声明**，正是本项目的病根。真正的观测方式：候选远多于 META_SCAN 时，
  // 每板读回的行数必须恰好等于 META_SCAN（LIMIT 生效），而不是把整板都读回来。
  const per = mod.META_SCAN + 120;                    // 每板都超过 META_SCAN
  const items = [];
  for (const b of ['board1', 'board2'])
    for (let i = 0; i < per; i++)
      items.push({ id: b + '-' + String(i).padStart(4, '0'), board_id: b,
        published_at: '2026-07-' + String(1 + (i % 28)).padStart(2, '0'),
        url: 'https://arxiv.org/abs/' + (3000 + items.length) + '.20002' });
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ results: [], meta: { count: 0 } }) });
  const env = mkEnv(items);
  await mod.enrichMeta(env, { degraded: [] });
  console.log(`  ${per} candidates per board -> SELECT returned ${JSON.stringify(env._selRows)} rows (META_SCAN=${mod.META_SCAN})`);
  ok(env._selRows.length === 2 && env._selRows.every(n => n === mod.META_SCAN),
    'each per-board candidate query reads exactly META_SCAN rows -- the LIMIT bounds the READ');
  // 上面那条会随 META_SCAN 一起缩放（用例规模就是从常量推出来的），所以它证明「LIMIT 起作用」，
  // 但【证明不了 META_SCAN 取值合理】—— 把 META_SCAN 调成 999999 它照样绿。故另加一条守常量的 lint。
  // ★如实说明这条断言【是什么】★：它是对常量的算术校验，不是实测读取量，DB 都没参与。
  // 真实读取量另有其人兜底：KEEP_PER_BOARD=300 把 board1+board2 限在约 600 行，
  // 所以 META_SCAN=999999 其实【不会】真的烧穿 D1 预算（实际仍约 600 行/晚）——
  // 这条 lint 防的是「常量被调成离谱值」，不是在测预算。别把它读成预算实测。
  const cap = 2 * mod.META_SCAN;
  console.log(`  lint (arithmetic, no DB): 2 x META_SCAN = ${cap}; real reads are bounded by KEEP_PER_BOARD=300 -> ~600 rows/night`);
  ok(cap <= 25000, 'META_SCAN stays a sane constant (lint on the constant, NOT a measured read budget)');
}

console.log('\nACCEPTANCE = ' + (fails ? 'FAIL' : 'PASS'));
process.exit(fails ? 1 : 0);
